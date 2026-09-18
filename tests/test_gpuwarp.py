"""The GPU warp's projection math, checked against PROJ.

The whole point of evaluating the projection per pixel is to avoid GDAL's
polynomial approximation, so these assert agreement with PROJ far tighter than
any pixel: a z13 tile is about 14.7 m across a pixel, and we hold millimetres.
If this drifts, every tile moves.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import torch
from osgeo import osr

from cesiumtiles.gpuwarp import (
    LambertConformalConic,
    footprint_scale,
    mercator_to_lonlat,
    prefilter,
    warp_block,
)

osr.UseExceptions()

# The FAA IFR enroute sheets: one CRS across all 37.
US_IFR = LambertConformalConic(
    standard_parallel_1=45.0,
    standard_parallel_2=33.0,
    latitude_of_origin=39.0,
    central_meridian=-95.0,
)


def _srs(epsg: int) -> osr.SpatialReference:
    s = osr.SpatialReference()
    s.ImportFromEPSG(epsg)
    s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return s


def _lcc_srs(lcc: LambertConformalConic) -> osr.SpatialReference:
    s = osr.SpatialReference()
    s.SetProjCS("test")
    s.SetWellKnownGeogCS("WGS84")
    s.SetLCC(lcc.standard_parallel_1, lcc.standard_parallel_2,
             lcc.latitude_of_origin, lcc.central_meridian,
             lcc.false_easting, lcc.false_northing)
    s.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return s


def test_lcc_matches_proj_across_conus():
    rng = np.random.default_rng(3)
    lon = rng.uniform(-125.0, -65.0, 2000)
    lat = rng.uniform(24.0, 50.0, 2000)
    transform = osr.CoordinateTransformation(_srs(4326), _lcc_srs(US_IFR))
    truth = np.array([transform.TransformPoint(float(a), float(b))[:2]
                      for a, b in zip(lon, lat)])
    x, y = US_IFR.forward(torch.tensor(lon, dtype=torch.float64),
                          torch.tensor(lat, dtype=torch.float64))
    assert np.abs(x.numpy() - truth[:, 0]).max() < 1e-3   # millimetre
    assert np.abs(y.numpy() - truth[:, 1]).max() < 1e-3


def test_lcc_is_exact_on_its_own_origin():
    """At the central meridian and origin latitude the projection is the
    identity on the false origin, whatever the ellipsoid does elsewhere."""
    x, y = US_IFR.forward(torch.tensor([US_IFR.central_meridian], dtype=torch.float64),
                          torch.tensor([US_IFR.latitude_of_origin], dtype=torch.float64))
    assert abs(float(x)) < 1e-6
    assert abs(float(y)) < 1e-6


def test_lcc_wraps_longitude_the_short_way():
    """A sheet reached from the far side of the antimeridian must not swing the
    cone the long way round; the longitude difference wraps to +/-180."""
    near = US_IFR.forward(torch.tensor([-179.0], dtype=torch.float64),
                          torch.tensor([40.0], dtype=torch.float64))
    same = US_IFR.forward(torch.tensor([181.0], dtype=torch.float64),
                          torch.tensor([40.0], dtype=torch.float64))
    assert abs(float(near[0]) - float(same[0])) < 1e-6
    assert abs(float(near[1]) - float(same[1])) < 1e-6


def test_mercator_inverse_matches_proj():
    rng = np.random.default_rng(5)
    x = rng.uniform(-14e6, -7e6, 2000)
    y = rng.uniform(2.5e6, 6.5e6, 2000)
    transform = osr.CoordinateTransformation(_srs(3857), _srs(4326))
    truth = np.array([transform.TransformPoint(float(a), float(b))[:2]
                      for a, b in zip(x, y)])
    lon, lat = mercator_to_lonlat(torch.tensor(x, dtype=torch.float64),
                                  torch.tensor(y, dtype=torch.float64))
    assert np.abs(lon.numpy() - truth[:, 0]).max() < 1e-9
    assert np.abs(lat.numpy() - truth[:, 1]).max() < 1e-9


def test_from_wkt_reads_the_parameters():
    lcc = LambertConformalConic.from_wkt(_lcc_srs(US_IFR).ExportToWkt())
    assert lcc.standard_parallel_1 == pytest.approx(45.0)
    assert lcc.standard_parallel_2 == pytest.approx(33.0)
    assert lcc.latitude_of_origin == pytest.approx(39.0)
    assert lcc.central_meridian == pytest.approx(-95.0)


def test_from_wkt_refuses_a_projection_it_does_not_implement():
    mercator = _srs(3857)
    with pytest.raises(ValueError):
        LambertConformalConic.from_wkt(mercator.ExportToWkt())


def _identity_coords(size: int) -> torch.Tensor:
    """Coordinates that map each destination pixel to the same source pixel.

    Geotransform pixel space is edge-based, so pixel j's centre is at j + 0.5.
    """
    axis = torch.arange(size, dtype=torch.float64) + 0.5
    rows, columns = torch.meshgrid(axis, axis, indexing="ij")
    return torch.stack((columns, rows), dim=-1)


def test_identity_warp_returns_the_source_untouched():
    """Guards the grid convention. Normalising as if the coordinates were
    integer indices shifts everything half a pixel, which looks like a
    georeferencing fault rather than an off-by-one."""
    source = torch.rand(4, 32, 32)
    out = warp_block(source, (0, 0), _identity_coords(32), scale=1.0)
    assert torch.equal(out, source)


def test_a_half_pixel_shift_is_not_the_identity():
    """The converse, so the test above cannot pass by accident."""
    source = torch.rand(4, 32, 32)
    out = warp_block(source, (0, 0), _identity_coords(32) + 0.5, scale=1.0)
    assert (out - source).abs().max() > 0.1


def test_window_origin_cancels():
    """Coordinates are in full-raster space; the window's origin is subtracted."""
    source = torch.rand(4, 32, 32)
    coords = _identity_coords(32)[6:26, 6:26]
    out = warp_block(source[:, 4:28, 4:28], (4, 4), coords, scale=1.0)
    assert torch.allclose(out, source[:, 6:26, 6:26], atol=1e-5)


def test_prefilter_preserves_a_flat_field():
    """The kernel is normalised, so minifying a constant changes nothing. If it
    did, every large flat area of a chart would shift in tone."""
    flat = torch.full((4, 64, 64), 0.7)
    for scale in (1.0, 1.5, 2.0, 4.0):
        assert (prefilter(flat, scale) - 0.7).abs().max() < 1e-6


def test_prefilter_is_a_no_op_when_not_minifying():
    source = torch.rand(4, 16, 16)
    assert prefilter(source, 1.0) is source
    assert prefilter(source, 0.5) is source


def test_prefilter_actually_blurs_when_minifying():
    """An impulse must spread, or there is no band-limiting and z13 would alias."""
    impulse = torch.zeros(1, 33, 33)
    impulse[0, 16, 16] = 1.0
    out = prefilter(impulse, 2.0)
    assert out[0, 16, 16] < 0.9          # energy left the centre
    assert out[0, 16, 17] > 0.01         # and landed next door
    assert abs(float(out.sum()) - 1.0) < 1e-5   # none of it was lost


def test_footprint_scale_reads_a_known_minification():
    assert footprint_scale(_identity_coords(16) * 2.0) == pytest.approx(2.0, abs=1e-6)
    assert footprint_scale(_identity_coords(16)) == pytest.approx(1.0, abs=1e-6)


def test_the_warp_is_isotropic_here():
    """The reason there is no anisotropic filtering: LCC and Web Mercator are
    both conformal, so an output pixel's footprint is a circle. Measured over
    the real sheets the axis ratio is 1.004, including one rotated 90 degrees.
    If this ever fails, the filter needs revisiting."""
    # A z13-sized destination step near the middle of the IFR coverage.
    west, north = -10_000_000.0, 4_800_000.0
    step = 2 * 20037508.342789244 / (1 << 13) / 256
    x = torch.tensor([west, west + step, west], dtype=torch.float64)
    y = torch.tensor([north, north, north - step], dtype=torch.float64)
    lon, lat = mercator_to_lonlat(x, y)
    east_m, north_m = US_IFR.forward(lon, lat)
    jacobian = np.array([[float(east_m[1] - east_m[0]), float(east_m[2] - east_m[0])],
                         [float(north_m[1] - north_m[0]), float(north_m[2] - north_m[0])]])
    singular = np.linalg.svd(jacobian, compute_uv=False)
    assert singular.max() / singular.min() < 1.02


def test_eccentricity_matches_the_ellipsoid():
    """GRS80 by default, which is what the charts are on. WGS84's flattening
    differs in the 9th digit (298.257223563), so do not swap the constants."""
    assert US_IFR.inverse_flattening == 298.257222101          # GRS80
    assert US_IFR.eccentricity == pytest.approx(0.0818191910428, abs=1e-12)
    assert US_IFR.eccentricity == pytest.approx(
        math.sqrt(2 / 298.257222101 - (1 / 298.257222101) ** 2))
    # The two ellipsoids agree to ~2e-10 in eccentricity, i.e. under a
    # millimetre on the ground -- far below a z13 pixel, so either is fine.
    wgs84 = math.sqrt(2 / 298.257223563 - (1 / 298.257223563) ** 2)
    assert abs(US_IFR.eccentricity - wgs84) < 1e-9


def test_mip_factor_leaves_the_prefilter_a_residual_under_two():
    """Power-of-two read, with the prefilter doing only the last factor of <2."""
    from cesiumtiles.gpuwarp import mip_factor
    assert mip_factor(0.8) == 1
    assert mip_factor(1.0) == 1
    assert mip_factor(1.9) == 1
    assert mip_factor(2.0) == 2
    assert mip_factor(5.1) == 4
    assert mip_factor(8.0) == 8
    for scale in (1.0, 1.3, 2.5, 3.9, 5.1, 17.0):
        assert 1.0 <= scale / mip_factor(scale) < 2.0 or scale < 1.0


def test_an_oversized_window_raises_instead_of_allocating(monkeypatch, tmp_path):
    """The first GPU build read a full-resolution 10k px window per block at
    z11, ~8 GB per worker, and took the machine down. The ceiling must raise."""
    from osgeo import gdal
    from cesiumtiles import gpuwarp

    path = str(tmp_path / "sheet.tif")
    ds = gdal.GetDriverByName("GTiff").Create(path, 512, 512, 4, gdal.GDT_Byte)
    ds.SetGeoTransform((0.0, 100.0, 0.0, 400000.0, 0.0, -100.0))
    ds.SetProjection(_lcc_srs(US_IFR).ExportToWkt())
    ds.FlushCache()
    # A block centred on the sheet, found through PROJ rather than guessed.
    to_mercator = osr.CoordinateTransformation(_lcc_srs(US_IFR), _srs(3857))
    mx, my, _ = to_mercator.TransformPoint(25_600.0, 374_400.0)
    monkeypatch.setattr(gpuwarp, "MAX_WINDOW_PIXELS", 16)
    with pytest.raises(gpuwarp.WindowTooLarge):
        gpuwarp.warp_dataset_block(ds, US_IFR, mx - 10_000.0, my + 10_000.0,
                                   20_000.0, 64, "cpu")


def test_integer_pyramid_average_matches_the_cpu_cascade():
    """The GPU pyramid reduces each child on its own, in integers. It must give
    what the CPU cascade's premultiplied float average gives, including where
    alpha is partial and where a child is missing (all zeros)."""
    from cesiumtiles.gpumosaic import _average_parents

    rng = np.random.default_rng(11)
    children = rng.integers(0, 256, (3, 2, 2, 256, 256, 4), dtype=np.uint8)
    children[0, ..., 3] = 255                        # opaque
    children[1, ..., 3] = rng.choice([0, 128, 255], size=children[1, ..., 3].shape)
    children[2, 1, 1] = 0                            # a missing child

    parents, alive = _average_parents(children, "cpu")

    # The CPU cascade, as _render_parent does it: premultiply, mean, _finish.
    canvas = np.zeros((3, 512, 512, 4), np.float32)
    for dy in (0, 1):
        for dx in (0, 1):
            px = children[:, dy, dx].astype(np.float32)
            a = px[..., 3:4] / 255.0
            canvas[:, dy * 256:(dy + 1) * 256, dx * 256:(dx + 1) * 256, :3] = px[..., :3] * a
            canvas[:, dy * 256:(dy + 1) * 256, dx * 256:(dx + 1) * 256, 3:] = a
    small = canvas.reshape(3, 256, 2, 256, 2, 4).mean(axis=(2, 4))
    alpha8 = np.clip(np.rint(small[..., 3] * 255.0), 0, 255)
    safe = np.where(small[..., 3] > 0, small[..., 3], 1.0)
    colour8 = np.clip(np.rint(small[..., :3] / safe[..., None]), 0, 255)
    expected = np.concatenate([colour8, alpha8[..., None]], axis=-1)

    diff = np.abs(parents.astype(int) - expected.astype(int))
    # Identical but for float rounding exactly at .5 boundaries.
    assert diff.max() <= 1
    assert (diff > 0).mean() < 0.01
    assert alive.tolist() == [True, True, True]


def test_encode_webp_is_lossless_and_drops_alpha_when_opaque():
    import imagecodecs
    from cesiumtiles.core import encode_webp

    rng = np.random.default_rng(12)
    rgba = rng.integers(0, 256, (256, 256, 4), dtype=np.uint8)
    back = imagecodecs.webp_decode(encode_webp(rgba, True, 90))
    assert back.shape == (256, 256, 4)
    visible = rgba[..., 3] > 0
    assert np.array_equal(back[visible], rgba[visible])

    rgba[..., 3] = 255
    back = imagecodecs.webp_decode(encode_webp(rgba, True, 90))
    assert back.shape == (256, 256, 3)               # opaque tiles are stored RGB
    assert np.array_equal(back, rgba[..., :3])
