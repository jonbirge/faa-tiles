"""Tile arithmetic, checked against mercantile as an independent oracle.

mercantile is a dev-only dependency: it implements the XYZ Web Mercator grid
separately, so agreeing with it is meaningful evidence rather than a tautology.
"""

from __future__ import annotations

import mercantile
import pytest

from cesiumtiles.scheme import GEOGRAPHIC, WEB_MERCATOR, TilingScheme

SAMPLE_TILES = [
    (0, 0, 0),
    (1, 0, 0),
    (1, 1, 1),
    (5, 9, 12),
    (9, 105, 194),
    (12, 3412, 1598),
    (14, 4823, 6160),
]


@pytest.mark.parametrize("z,x,y", SAMPLE_TILES)
def test_tile_bounds_match_mercantile(z, x, y):
    ours = WEB_MERCATOR.tile_bounds(z, x, y)
    theirs = mercantile.xy_bounds(x, y, z)
    assert ours == pytest.approx((theirs.left, theirs.bottom, theirs.right, theirs.top), abs=1e-6)


@pytest.mark.parametrize("z", [0, 1, 4, 9, 14])
def test_grid_dimensions_match_mercantile(z):
    # mercantile's world is square and starts as a single tile at z0.
    assert WEB_MERCATOR.columns(z) == 2**z
    assert WEB_MERCATOR.rows(z) == 2**z
    assert WEB_MERCATOR.resolution(z) == pytest.approx(
        (mercantile.xy_bounds(0, 0, z).right - mercantile.xy_bounds(0, 0, z).left) / 256
    )


@pytest.mark.parametrize(
    "bbox",
    [
        (-106.0, 39.0, -104.0, 40.5),
        (-129.9179, 21.5505, -64.1381, 51.7469),
        (-0.5, -0.5, 0.5, 0.5),
        (170.0, -45.0, 179.0, -40.0),
    ],
)
@pytest.mark.parametrize("z", [4, 8, 11])
def test_tile_range_matches_mercantile(bbox, z):
    west, south, east, north = bbox
    expected = list(mercantile.tiles(west, south, east, north, [z]))

    left, top = mercantile.xy(west, north)
    right, bottom = mercantile.xy(east, south)
    ours = WEB_MERCATOR.tile_range(z, (left, bottom, right, top))

    assert ours.x_min == min(t.x for t in expected)
    assert ours.x_max == max(t.x for t in expected)
    assert ours.y_min == min(t.y for t in expected)
    assert ours.y_max == max(t.y for t in expected)
    assert ours.count == len(expected)
    assert sorted(ours) == sorted((t.x, t.y) for t in expected)


def test_tile_range_does_not_spill_across_an_exact_edge():
    # Bounds that are exactly one tile wide must select exactly one tile.
    bounds = WEB_MERCATOR.tile_bounds(6, 20, 30)
    r = WEB_MERCATOR.tile_range(6, bounds)
    assert (r.x_min, r.x_max, r.y_min, r.y_max) == (20, 20, 30, 30)
    assert r.count == 1


def test_tile_range_spanning_two_tiles():
    west, south, east, north = WEB_MERCATOR.tile_bounds(6, 20, 30)
    span = east - west
    r = WEB_MERCATOR.tile_range(6, (west, south, east + span * 0.5, north))
    assert (r.x_min, r.x_max) == (20, 21)


def test_tile_range_clamps_to_the_world():
    r = WEB_MERCATOR.tile_range(3, WEB_MERCATOR.clamp_bounds((-1e9, -1e9, 1e9, 1e9)))
    assert (r.x_min, r.x_max, r.y_min, r.y_max) == (0, 7, 0, 7)


def test_rejects_degenerate_bounds():
    with pytest.raises(ValueError, match="degenerate"):
        WEB_MERCATOR.tile_range(3, (10.0, 10.0, 10.0, 20.0))


def test_clamp_rejects_disjoint_bounds():
    with pytest.raises(ValueError, match="do not intersect"):
        GEOGRAPHIC.clamp_bounds((200.0, 10.0, 210.0, 20.0))


# -- geographic scheme -------------------------------------------------


def test_geographic_is_two_by_one_at_zoom_zero():
    # Cesium's GeographicTilingScheme, and OGC WorldCRS84Quad, both start with
    # two square tiles side by side.
    assert (GEOGRAPHIC.columns(0), GEOGRAPHIC.rows(0)) == (2, 1)
    assert GEOGRAPHIC.tile_bounds(0, 0, 0) == (-180.0, -90.0, 0.0, 90.0)
    assert GEOGRAPHIC.tile_bounds(0, 1, 0) == (0.0, -90.0, 180.0, 90.0)


def test_geographic_tiles_stay_square():
    for z in (0, 3, 7):
        span_x, span_y = GEOGRAPHIC.tile_span(z)
        assert span_x == pytest.approx(span_y)


# -- zoom selection ----------------------------------------------------


@pytest.mark.parametrize("scheme", [WEB_MERCATOR, GEOGRAPHIC])
@pytest.mark.parametrize("z", range(0, 15))
def test_zoom_for_resolution_round_trips(scheme: TilingScheme, z: int):
    assert scheme.zoom_for_resolution(scheme.resolution(z)) == z


def test_zoom_for_resolution_rounds_up_to_preserve_detail():
    # Halfway between two levels we must take the finer one, never the coarser,
    # or the tiles would throw away source detail.
    between = (WEB_MERCATOR.resolution(9) + WEB_MERCATOR.resolution(10)) / 2
    assert WEB_MERCATOR.zoom_for_resolution(between) == 10


def test_zoom_for_the_faa_chart():
    # The VFR wall planning chart warps to ~329.77 m/px in EPSG:3857; GDAL's own
    # auto-detection independently picks z9 for it.
    assert WEB_MERCATOR.zoom_for_resolution(329.772) == 9
    assert GEOGRAPHIC.zoom_for_resolution(0.00281645) == 8


def test_zoom_for_resolution_rejects_nonsense():
    with pytest.raises(ValueError, match="positive"):
        WEB_MERCATOR.zoom_for_resolution(0)


# -- y-axis convention -------------------------------------------------


@pytest.mark.parametrize("z,x,y", SAMPLE_TILES)
def test_flip_y_is_its_own_inverse(z, x, y):
    assert WEB_MERCATOR.flip_y(z, WEB_MERCATOR.flip_y(z, y)) == y


@pytest.mark.parametrize("z,x,y", SAMPLE_TILES)
def test_flip_y_matches_mercantile_tms(z, x, y):
    # XYZ counts rows from the north, TMS from the south.
    assert WEB_MERCATOR.flip_y(z, y) == (2**z - 1 - y)


def test_north_west_tile_is_y_zero():
    _, _, _, north = WEB_MERCATOR.tile_bounds(4, 0, 0)
    assert north == pytest.approx(WEB_MERCATOR.north)
