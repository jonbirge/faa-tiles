"""Warp chart sheets into Web Mercator tiles on the GPU, with EWA filtering.

Why this exists, given ``gdal.Warp`` already works: GDAL's warp applies a
*separable* kernel along the source's own axes. That is right for an
axis-aligned scale, but the true footprint of an output pixel in a rotated,
reprojected source is a tilted ellipse, and GDAL cannot express one. Half the
IFR sheets carry rotation in their geotransform and ENR_L24 is rotated a full
90 degrees, so this is not a corner case. Elliptically-weighted averaging (EWA)
gathers over that ellipse properly, which is what 3D hardware has always done
for textures under perspective.

It is written in PyTorch rather than CUDA C or OpenGL, deliberately:

* torch is already a dependency (the sectional upsampler), already the CUDA
  build, and has wheels wherever we run.
* It needs no display: no X, no EGL, no GL context. A headless Linux box with
  an NVIDIA card runs it as-is, and it falls back to CPU where there is no GPU.
* The filter is *ours*, so the same input gives the same tiles on any machine.
  Hardware anisotropic filtering is an approximation whose quality varies by
  vendor and driver generation, which is a poor property for a pipeline that
  reruns every 56 days and is compared against previous editions.

The projection is evaluated per output pixel in closed form, so there is no
transformer approximation of the kind that costs GDAL a 4x penalty to avoid
(see ``mosaic.ERROR_THRESHOLD``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch

__all__ = ["LambertConformalConic", "mercator_to_lonlat", "best_device"]


def best_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


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
