"""Warp chart sheets into Web Mercator tiles on the GPU.

An alternative to ``gdal.Warp`` for the max-zoom tiles, selected with
``build_chart_tileset.py --warp gpu`` (the default; ``--warp cpu`` keeps GDAL).
What it does differently:

* **The projection is exact.** It is evaluated per output pixel in closed form,
  where gdal.Warp fits a polynomial over the destination and pays about 4x in
  the kernel to be exact instead (see ``mosaic.ERROR_THRESHOLD``).
* **Resampling is prefilter-then-reconstruct**: a power-of-two mip read, a
  Gaussian that band-limits the remainder to the output's Nyquist limit, then
  bicubic. GDAL widens a separable cubic along the source axes, which
  approximates both steps at once.

The filter is isotropic, and that is correct rather than a shortcut: see the
note above ``source_pixels``. It was first planned as EWA/anisotropic, until the
footprints measured circular.

It is written in PyTorch rather than CUDA C or OpenGL, deliberately:

* torch is already a dependency (the sectional upsampler), already the CUDA
  build, and has wheels wherever we run.
* It needs no display: no X, no EGL, no GL context. A headless Linux box with
  an NVIDIA card runs it as-is, and it falls back to CPU where there is no GPU.
* The filter is *ours*, so the same input gives the same tiles on any machine,
  unlike hardware texture filtering, which varies by vendor and driver.

Memory is the constraint to respect. See ``MAX_WINDOW_PIXELS`` for what
happened without a bound, and ``limit_memory`` for the second guard.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn.functional as F

__all__ = [
    "LambertConformalConic", "WindowTooLarge", "best_device", "footprint_scale",
    "limit_memory", "mercator_to_lonlat", "mip_factor", "prefilter",
    "source_pixels", "source_pixels_batch", "supports", "warp_block", "warp_dataset_block",
]


def best_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def limit_memory(device: str, share: float) -> None:
    """Cap this process's CUDA allocations at ``share`` of the card.

    Past the cap torch raises ``OutOfMemoryError``. Without it, the Windows
    driver's default is to spill CUDA allocations into shared *system* memory,
    so a runaway block exhausts RAM for the whole machine instead of failing one
    process -- which is how the first GPU test build crashed the computer.
    """
    if device.startswith("cuda") and torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(share)


# -- projections -------------------------------------------------------------
#
# Formulas are Snyder, *Map Projections -- A Working Manual* (USGS PP 1395),
# ellipsoidal Lambert Conformal Conic with two standard parallels, pp. 107-109.

@dataclass(frozen=True)
class LambertConformalConic:
    """An ellipsoidal LCC 2SP, as the FAA charts use it."""

    standard_parallel_1: float
    standard_parallel_2: float
    latitude_of_origin: float
    central_meridian: float
    false_easting: float = 0.0
    false_northing: float = 0.0
    semi_major: float = 6378137.0
    inverse_flattening: float = 298.257222101

    @classmethod
    def from_wkt(cls, wkt: str) -> "LambertConformalConic":
        from osgeo import osr

        srs = osr.SpatialReference(wkt)
        name = srs.GetAttrValue("PROJECTION")
        if name != "Lambert_Conformal_Conic_2SP":
            raise ValueError(f"expected Lambert_Conformal_Conic_2SP, got {name!r}")
        return cls(
            standard_parallel_1=srs.GetProjParm("standard_parallel_1"),
            standard_parallel_2=srs.GetProjParm("standard_parallel_2"),
            latitude_of_origin=srs.GetProjParm("latitude_of_origin"),
            central_meridian=srs.GetProjParm("central_meridian"),
            false_easting=srs.GetProjParm("false_easting"),
            false_northing=srs.GetProjParm("false_northing"),
            semi_major=srs.GetSemiMajor(),
            inverse_flattening=srs.GetInvFlattening(),
        )

    @property
    def eccentricity(self) -> float:
        f = 1.0 / self.inverse_flattening
        return math.sqrt(2 * f - f * f)

    def _constants(self) -> tuple[float, float, float]:
        """``(n, F, rho0)``, which depend only on the projection, not the point."""
        e = self.eccentricity

        def m(lat_deg: float) -> float:
            lat = math.radians(lat_deg)
            return math.cos(lat) / math.sqrt(1.0 - (e * math.sin(lat)) ** 2)

        def t(lat_deg: float) -> float:
            lat = math.radians(lat_deg)
            s = e * math.sin(lat)
            return (math.tan(math.pi / 4 - lat / 2)
                    / ((1.0 - s) / (1.0 + s)) ** (e / 2))

        m1, m2 = m(self.standard_parallel_1), m(self.standard_parallel_2)
        t1, t2 = t(self.standard_parallel_1), t(self.standard_parallel_2)
        if abs(self.standard_parallel_1 - self.standard_parallel_2) < 1e-12:
            n = math.sin(math.radians(self.standard_parallel_1))
        else:
            n = (math.log(m1) - math.log(m2)) / (math.log(t1) - math.log(t2))
        big_f = m1 / (n * t1 ** n)
        rho0 = self.semi_major * big_f * t(self.latitude_of_origin) ** n
        return n, big_f, rho0

    def forward(self, lon: torch.Tensor, lat: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Longitude/latitude in degrees to projected metres, elementwise."""
        n, big_f, rho0 = self._constants()
        e = self.eccentricity
        lat_rad = torch.deg2rad(lat)
        s = e * torch.sin(lat_rad)
        t = (torch.tan(math.pi / 4 - lat_rad / 2)
             / ((1.0 - s) / (1.0 + s)) ** (e / 2))
        rho = self.semi_major * big_f * t ** n
        # Longitude difference wrapped to +/-180, so a sheet near the
        # antimeridian does not swing the cone the long way round.
        delta = torch.remainder(lon - self.central_meridian + 180.0, 360.0) - 180.0
        theta = n * torch.deg2rad(delta)
        return (self.false_easting + rho * torch.sin(theta),
                self.false_northing + rho0 - rho * torch.cos(theta))


# EPSG:3857 is spherical Mercator on a sphere of the ellipsoid's semi-major
# axis; that is the definition, not an approximation of it.
MERCATOR_RADIUS = 6378137.0


def mercator_to_lonlat(x: torch.Tensor, y: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Web Mercator metres to longitude/latitude in degrees, elementwise."""
    lon = torch.rad2deg(x / MERCATOR_RADIUS)
    lat = torch.rad2deg(2.0 * torch.atan(torch.exp(y / MERCATOR_RADIUS)) - math.pi / 2)
    return lon, lat


# -- resampling --------------------------------------------------------------
#
# The filter here is *isotropic*, deliberately. An output pixel's footprint in
# the source is in general an ellipse, and 3D renderers go to great lengths
# (anisotropic filtering, EWA) to gather over it. Here it is a circle: Lambert
# Conformal Conic and Web Mercator are both conformal, so each maps
# infinitesimal circles to circles, and composing them does too. Measured over
# the IFR sheets, including one rotated a full 90 degrees, the ratio of the
# footprint's axes is 1.004 -- rotation does not break this, because a rotation
# is exactly what conformality allows. So an isotropic prefilter is not an
# approximation of the right answer, it *is* the right answer, and an
# anisotropic one would be machinery for a case that does not arise.
#
# Resampling is then the textbook two steps: prefilter the source to the output
# 's Nyquist limit, then reconstruct at the sample points. GDAL instead widens a
# separable cubic along the source axes, which approximates both at once.


def source_pixels(lcc: "LambertConformalConic", inverse_geotransform, west: float,
                  north: float, span: float, size: int, device: str,
                  dtype: torch.dtype = torch.float64) -> torch.Tensor:
    """Source pixel coordinates for every pixel of a Mercator block.

    ``west``/``north`` are the block's top-left corner and ``span`` its side, in
    Mercator metres; ``size`` is its side in pixels. Returns ``(size, size, 2)``
    of ``(column, row)`` in the *full* source raster's pixel space.

    Evaluated at every pixel, in double precision: this is the step GDAL
    approximates with a polynomial, and the whole reason that approximation
    costs it 4x to avoid.
    """
    step = span / size
    centres = (torch.arange(size, device=device, dtype=dtype) + 0.5) * step
    x = west + centres
    y = north - centres
    grid_y, grid_x = torch.meshgrid(y, x, indexing="ij")
    lon, lat = mercator_to_lonlat(grid_x, grid_y)
    east_m, north_m = lcc.forward(lon, lat)
    a, b, c, d, e, f = (float(v) for v in inverse_geotransform)
    column = a + b * east_m + c * north_m
    row = d + e * east_m + f * north_m
    return torch.stack((column, row), dim=-1)


def source_pixels_batch(lcc: "LambertConformalConic", inverse_geotransform,
                        wests: torch.Tensor, norths: torch.Tensor, span: float,
                        size: int, dtype: torch.dtype = torch.float64) -> torch.Tensor:
    """:func:`source_pixels` for many same-sized blocks at once.

    ``wests`` and ``norths`` are ``(B,)`` on the target device. Returns
    ``(B, size, size, 2)``. One call per batch rather than per tile is what lets
    the GPU be busy: a single 256 px tile is far too little work to launch.
    """
    device = wests.device
    step = span / size
    centres = (torch.arange(size, device=device, dtype=dtype) + 0.5) * step
    x = wests.to(dtype)[:, None, None] + centres[None, None, :]
    y = norths.to(dtype)[:, None, None] - centres[None, :, None]
    x, y = torch.broadcast_tensors(x, y)
    lon, lat = mercator_to_lonlat(x, y)
    east_m, north_m = lcc.forward(lon, lat)
    a, b, c, d, e, f = (float(v) for v in inverse_geotransform)
    return torch.stack((a + b * east_m + c * north_m, d + e * east_m + f * north_m), dim=-1)


def footprint_scale(coords: torch.Tensor) -> float:
    """Source pixels per destination pixel, from the coordinate field itself.

    Differencing what was already computed avoids re-deriving the Jacobian, and
    it is the true local scale rather than a nominal one. The footprint is
    circular (see above), so a single number describes it; this takes the larger
    axis, which is the one that decides aliasing.
    """
    dx = coords[:, 1:, :] - coords[:, :-1, :]      # step along destination x
    dy = coords[1:, :, :] - coords[:-1, :, :]      # step along destination y
    return float(max(dx.norm(dim=-1).median(), dy.norm(dim=-1).median()))


def prefilter(source: torch.Tensor, scale: float) -> torch.Tensor:
    """Band-limit ``source`` so ``scale``-fold minification cannot alias.

    A separable Gaussian, because the footprint is circular and a Gaussian is
    the only separable kernel that is also radially symmetric. Its width is set
    so the source's new cut-off matches the output's Nyquist limit; below 1:1
    there is nothing to remove and the source is returned untouched.
    """
    if scale <= 1.0:
        return source
    sigma = 0.5 * math.sqrt(scale * scale - 1.0)
    radius = max(1, int(math.ceil(3.0 * sigma)))
    taps = torch.arange(-radius, radius + 1, device=source.device, dtype=source.dtype)
    kernel = torch.exp(-0.5 * (taps / sigma) ** 2)
    kernel = kernel / kernel.sum()
    bands = source.shape[0]
    horizontal = kernel.view(1, 1, 1, -1).expand(bands, 1, 1, -1)
    vertical = kernel.view(1, 1, -1, 1).expand(bands, 1, -1, 1)
    out = source.unsqueeze(0)
    out = F.conv2d(F.pad(out, (radius, radius, 0, 0), mode="replicate"),
                   horizontal, groups=bands)
    out = F.conv2d(F.pad(out, (0, 0, radius, radius), mode="replicate"),
                   vertical, groups=bands)
    return out.squeeze(0)


def warp_block(source: torch.Tensor, origin: tuple[int, int], coords: torch.Tensor,
               scale: float | None = None) -> torch.Tensor:
    """Resample a source window onto a destination block.

    ``source`` is ``(bands, height, width)`` float32 with colour already
    premultiplied by alpha -- sampling straight colour would drag the colour of
    transparent pixels in across the sheet's edge. ``origin`` is the window's
    top-left in full-raster pixels, and ``coords`` comes from
    :func:`source_pixels` in that same full-raster space.
    """
    if scale is None:
        scale = footprint_scale(coords)
    filtered = prefilter(source, scale)

    height, width = source.shape[-2:]
    local = coords - torch.tensor(origin, device=coords.device, dtype=coords.dtype)
    # A geotransform's pixel space is edge-based: (0, 0) is the raster's corner
    # and pixel j's centre is at j + 0.5. align_corners=False puts -1 and +1 on
    # those same outer edges, so this is a plain rescale. Treating the
    # coordinates as integer indices instead (the +1 convention) shifts
    # everything half a pixel, which an identity warp catches immediately.
    size = torch.tensor([width, height], device=coords.device, dtype=coords.dtype)
    grid = 2.0 * local / size - 1.0
    sampled = F.grid_sample(
        filtered.unsqueeze(0), grid.unsqueeze(0).to(filtered.dtype),
        mode="bicubic", padding_mode="zeros", align_corners=False,
    ).squeeze(0)
    # bicubic overshoots; premultiplied colour must stay within its own alpha.
    return sampled.clamp_(min=0.0)


# Enough source pixels around the window for the prefilter's tails and the
# bicubic's 4x4 support, in *mip-level* pixels. Generous: reading a few extra
# rows costs nothing next to decompressing the window at all.
WINDOW_MARGIN = 12

# Hard ceiling on the window one block may read, in mip-level pixels. With the
# mip selection below a block needs about (2 x its own size)^2, so this is
# several times what any real block asks for; it exists so a bug raises here
# instead of allocating tens of GB. That is not hypothetical: before mip
# selection a z11 block read a 10,400 px window at full resolution, ~8 GB per
# worker once filtered, and on Windows the driver spilled the overflow into
# system RAM rather than failing -- it took the machine down.
MAX_WINDOW_PIXELS = 48 * 1024 * 1024

# Full-resolution source pixels read and reduced per step while building a mip
# level, so the full-resolution window never exists in memory at once. Bounded
# in pixels, not rows: a fixed row count scales with the window's width, and at
# z10 a 2048-row strip was ~700 MB of float32 before premultiplying.
STRIP_PIXELS = 8 * 1024 * 1024


class WindowTooLarge(RuntimeError):
    """A block asked for more source than MAX_WINDOW_PIXELS allows."""


def supports(projection_wkt: str) -> bool:
    """Whether this module can warp from ``projection_wkt``."""
    try:
        LambertConformalConic.from_wkt(projection_wkt)
    except Exception:
        return False
    return True


def mip_factor(scale: float) -> int:
    """The power-of-two reduction to read the source at for ``scale``.

    Chosen so the residual scale left for the prefilter stays in [1, 2): the
    prefilter does the fine band-limiting, the box reduction does the bulk.
    Reading at full resolution and prefiltering alone is correct but wasteful at
    low zooms -- at z11 a block minifies ~5x, so 96% of what is read is
    averaged away.
    """
    if scale < 2.0:
        return 1
    return 1 << int(math.floor(math.log2(scale)))


def _read_premultiplied(dataset, x0: int, y0: int, width: int, height: int,
                        factor: int, device: str) -> torch.Tensor:
    """Read a window as premultiplied RGBA float32, box-reduced by ``factor``.

    Premultiplied *before* reducing: averaging straight colour with alpha
    alongside would drag the colour of masked-out collar in across the map's
    edge. Read in strips so the full-resolution window never exists at once.
    ``width`` and ``height`` must be multiples of ``factor``.
    """
    bands = dataset.RasterCount
    out_h, out_w = height // factor, width // factor
    result = torch.empty((4, out_h, out_w), device=device, dtype=torch.float32)
    strip = max(factor, (STRIP_PIXELS // max(1, width) // factor) * factor)
    for row in range(0, height, strip):
        rows = min(strip, height - row)
        raw = dataset.ReadAsArray(x0, y0 + row, width, rows)
        if raw.ndim == 2:
            raw = raw[None]
        pixels = torch.as_tensor(raw, device=device).to(torch.float32).div_(255.0)
        del raw
        if bands >= 4:
            rgb, alpha = pixels[:3], pixels[3:4]
        else:
            rgb = pixels[:3] if pixels.shape[0] == 3 else pixels[:1].expand(3, -1, -1)
            alpha = torch.ones_like(rgb[:1])
        premultiplied = torch.cat((rgb * alpha, alpha), dim=0)
        del pixels, rgb, alpha
        if factor > 1:
            premultiplied = F.avg_pool2d(premultiplied.unsqueeze(0), factor).squeeze(0)
        r0 = row // factor
        result[:, r0:r0 + premultiplied.shape[1]] = premultiplied
        del premultiplied
    return result


def warp_dataset_block(dataset, lcc: "LambertConformalConic", west: float, north: float,
                       span: float, size: int, device: str) -> torch.Tensor | None:
    """Resample one Mercator block out of an open GDAL dataset.

    Returns ``(4, size, size)`` float32 with colour premultiplied by alpha, on
    ``device``, or ``None`` when the block does not touch the source at all.
    The dataset is expected to carry an alpha band (the map-area mask); without
    one every pixel counts as opaque.

    Reads the source at a power-of-two mip level matched to the block's
    minification (see :func:`mip_factor`), then prefilters the remainder and
    reconstructs with bicubic, so the memory a block needs is bounded by its own
    size rather than by how far out the zoom is.
    """
    from osgeo import gdal

    inverse = gdal.InvGeoTransform(dataset.GetGeoTransform())
    coords = source_pixels(lcc, inverse, west, north, span, size, device)
    scale = footprint_scale(coords)
    factor = mip_factor(scale)

    width, height = dataset.RasterXSize, dataset.RasterYSize
    low = coords.amin(dim=(0, 1))
    high = coords.amax(dim=(0, 1))
    margin = WINDOW_MARGIN * factor
    x0 = max(0, int(math.floor(float(low[0]))) - margin)
    y0 = max(0, int(math.floor(float(low[1]))) - margin)
    x1 = min(width, int(math.ceil(float(high[0]))) + margin)
    y1 = min(height, int(math.ceil(float(high[1]))) + margin)
    if x1 <= x0 or y1 <= y0:
        return None
    # Snap the window to the mip grid so each reduced pixel covers exactly
    # `factor` source pixels; trim rather than overrun the raster's edge.
    x0, y0 = x0 - x0 % factor, y0 - y0 % factor
    x1 = x0 + ((x1 - x0) // factor) * factor
    y1 = y0 + ((y1 - y0) // factor) * factor
    if x1 <= x0 or y1 <= y0:
        return None
    reduced = ((x1 - x0) // factor) * ((y1 - y0) // factor)
    if reduced > MAX_WINDOW_PIXELS:
        raise WindowTooLarge(
            f"block needs a {(x1 - x0) // factor}x{(y1 - y0) // factor} window at 1/{factor} "
            f"(scale {scale:.2f}); refusing rather than exhausting memory")

    source = _read_premultiplied(dataset, x0, y0, x1 - x0, y1 - y0, factor, device)
    # Coordinates into the reduced level: same edge-based convention, scaled.
    level_coords = coords / factor
    del coords
    return warp_block(source, (x0 // factor, y0 // factor), level_coords,
                      scale=scale / factor)
