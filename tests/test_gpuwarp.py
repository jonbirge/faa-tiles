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

from cesiumtiles.gpuwarp import LambertConformalConic, mercator_to_lonlat

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
