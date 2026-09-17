"""Mosaics of several overlapping rasters, against small synthetic sheets."""

from __future__ import annotations

import json
import math

import numpy as np
import pytest
import rasterio
from PIL import Image
from rasterio.crs import CRS
from rasterio.transform import from_bounds

from cesiumtiles.mosaic import (
    MapArea,
    MosaicSource,
    Polygon,
    build_mosaic,
    covering_arc,
    plan_tiles,
    prepare_sources,
)

RED = (220, 30, 30)
BLUE = (30, 60, 220)
MAX_ZOOM = 8


def _solid(path, bounds, color, *, crs="EPSG:4326", size=256, palette=False):
    west, south, east, north = bounds
    profile = {
        "driver": "GTiff", "width": size, "height": size, "dtype": "uint8",
        "crs": CRS.from_string(crs), "transform": from_bounds(west, south, east, north, size, size),
    }
    if palette:
        with rasterio.open(path, "w", count=1, **profile) as dst:
            dst.write(np.zeros((1, size, size), np.uint8))
            dst.write_colormap(1, {0: (*color, 255), 1: (0, 0, 0, 255)})
    else:
        with rasterio.open(path, "w", count=3, **profile) as dst:
            dst.write(np.stack([np.full((size, size), c, np.uint8) for c in color]))
    return path


def _pixel(out, lon, lat, z=MAX_ZOOM):
    """RGBA of the tile pixel covering ``lon, lat``, or None if no tile there."""
    n = 2 ** z
    fx = (lon + 180.0) / 360.0 * n
    fy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    x, y = int(fx), int(fy)
    path = out / "tiles" / str(z) / str(x) / f"{y}.webp"
    if not path.exists():
        return None
    img = Image.open(path).convert("RGBA")
    return img.getpixel((int((fx - x) * 256), int((fy - y) * 256)))


def _close(rgba, rgb, tol=6):
    return rgba is not None and rgba[3] == 255 and all(abs(a - b) <= tol for a, b in zip(rgba, rgb))


@pytest.fixture(scope="module")
def scene(tmp_path_factory):
    """Two overlapping sheets. ``a_red`` sorts first, so ``b_blue`` is on top.

    ``a_red`` is a palette sheet with a west limit; ``b_blue`` has a hole cut in
    it, through which the red sheet beneath should show.
    """
    root = tmp_path_factory.mktemp("mosaic")
    red = _solid(root / "a_red.tif", (-106.0, 39.0, -104.0, 41.0), RED, palette=True)
    blue = _solid(root / "b_blue.tif", (-105.0, 39.0, -103.0, 41.0), BLUE)
    sources = [
        MosaicSource(red, MapArea.from_dict({"limits": {"west": -105.8}})),
        MosaicSource(blue, MapArea.from_dict({"exclude": [
            {"lonlat": [[-104.9, 39.8], [-104.1, 39.8], [-104.1, 40.6], [-104.9, 40.6]]},
        ]})),
    ]
    out = root / "out"
    result = build_mosaic(sources, out, min_zoom=5, max_zoom=MAX_ZOOM, lossless=True, workers=2, quiet=True)
    return out, result


def test_later_source_is_painted_on_top(scene):
    out, _ = scene
    assert _close(_pixel(out, -105.5, 39.5), RED)     # red only
    assert _close(_pixel(out, -104.5, 39.3), BLUE)    # overlap, outside the hole
    assert _close(_pixel(out, -103.5, 39.5), BLUE)    # blue only


def test_excluded_polygon_shows_the_sheet_beneath(scene):
    out, _ = scene
    assert _close(_pixel(out, -104.5, 40.2), RED)


def test_limits_clip_the_sheet(scene):
    out, _ = scene
    pixel = _pixel(out, -105.95, 40.0)
    assert pixel is None or pixel[3] == 0
    assert _close(_pixel(out, -105.6, 40.0), RED)


def test_palette_is_expanded_before_resampling(scene):
    # Resampling palette indices directly would blend 0 and 1 into index noise;
    # the sheet interior must come out as exactly the palette colour.
    out, _ = scene
    assert _close(_pixel(out, -105.3, 40.8), RED, tol=0)


def test_every_zoom_is_present_and_counted_from_disk(scene):
    out, result = scene
    assert sorted(result.per_zoom) == list(range(5, MAX_ZOOM + 1))
    on_disk = sum(1 for _ in (out / "tiles").rglob("*.webp"))
    assert result.tile_count == on_disk
    assert not list((out / "tiles").rglob("*.part"))
    # Build intermediates (masks) are cleaned away.
    assert sorted(p.name for p in out.iterdir()) == ["metadata.json", "tiles"]


def test_parents_are_built_from_children(scene):
    out, result = scene
    top = result.max_zoom
    children = {(int(p.parent.name), int(p.stem)) for p in (out / "tiles" / str(top)).rglob("*.webp")}
    parents = {(int(p.parent.name), int(p.stem)) for p in (out / "tiles" / str(top - 1)).rglob("*.webp")}
    assert parents == {(x // 2, y // 2) for x, y in children}
    assert _close(_pixel(out, -105.5, 39.5, z=top - 1), RED)


def test_metadata_describes_the_mosaic(scene):
    out, result = scene
    meta = json.loads((out / "metadata.json").read_text())
    assert meta["sources"] == ["a_red.tif", "b_blue.tif"]
    assert meta["maxzoom"] == MAX_ZOOM and meta["minzoom"] == 5
    assert meta["url_template"] == "tiles/{z}/{x}/{y}.webp"
    west, south, east, north = meta["data_bounds"]
    assert west == pytest.approx(-105.8, abs=0.01)   # the limit, not the image edge
    assert east == pytest.approx(-103.0, abs=0.01)
    assert meta["tiles"] == result.tile_count


def test_missing_polygon_frame_is_rejected():
    with pytest.raises(ValueError):
        Polygon(((0, 0), (1, 0), (1, 1)), frame="page")


def test_manifest_form_round_trips():
    area = MapArea.from_dict({
        "limits": {"south": 32.0},
        "include": [{"pixel": [[0, 0], [10, 0], [10, 10]]}],
        "exclude": [{"lonlat": [[1, 1], [2, 1], [2, 2]]}],
        "manual": True,   # manifest bookkeeping keys are ignored
    })
    assert area.limits.south == 32.0 and area.limits.west is None
    assert area.include[0].frame == "pixel"
    assert area.exclude[0].frame == "lonlat"
    assert not area.is_whole_image


def test_pixel_scale_scales_only_pixel_polygons():
    """Manifests are recorded against the downloaded GeoTIFFs; ifr-low tiles
    rasters drawn from the PDFs at twice that, so its pixel polygons double."""
    spec = {
        "limits": {"south": 32.0},
        "include": [{"pixel": [[0, 0], [10, 0], [10, 20]]}],
        "exclude": [{"lonlat": [[1, 1], [2, 1], [2, 2]]}],
    }
    area = MapArea.from_dict(spec, 2)
    assert area.include[0].points == ((0.0, 0.0), (20.0, 0.0), (20.0, 40.0))
    # Ground coordinates are ground coordinates at any resolution.
    assert area.exclude[0].points == ((1.0, 1.0), (2.0, 1.0), (2.0, 2.0))
    assert area.limits.south == 32.0
    assert MapArea.from_dict(spec).include[0].points == ((0.0, 0.0), (10.0, 0.0), (10.0, 20.0))


# -- the antimeridian --------------------------------------------------


def test_covering_arc():
    assert covering_arc([(-106, -104), (-105, -103)]) == (-106, -103)
    # Two clusters either side of 180: the short way round crosses it.
    assert covering_arc([(170, 178), (-178, -170)]) == (170, -170)
    # An unwrapped interval running past 180 is the same thing.
    assert covering_arc([(175, 185)]) == (175, -175)
    assert covering_arc([(-180, 0), (0, 180)]) == (-180, 180)


def test_sheet_across_the_antimeridian(tmp_path):
    lcc = "+proj=lcc +lat_1=50 +lat_2=55 +lat_0=52 +lon_0=180 +datum=WGS84 +units=m +no_defs"
    sheet = _solid(tmp_path / "aleutians.tif", (-300_000, -150_000, 300_000, 150_000), BLUE, crs=lcc)

    [prepared] = prepare_sources([MosaicSource(sheet)])
    z = 6
    plan = plan_tiles([prepared], z)
    columns = {x for x, _ in plan}
    # Tiles on both sides of the seam, both drawn from the one sheet.
    assert 0 in columns and (1 << z) - 1 in columns
    # The sheet's centre is 180 itself, so which side counts as "unwrapped" is
    # arbitrary; what matters is that one side needs a whole-world offset.
    wraps = {wrap for contributors in plan.values() for _, wrap in contributors}
    assert len(wraps) == 2 and 0 in wraps

    out = tmp_path / "out"
    build_mosaic([MosaicSource(sheet)], out, min_zoom=z, max_zoom=z, lossless=True, workers=2, quiet=True)
    assert _close(_pixel(out, 179.5, 52.0, z=z), BLUE)
    assert _close(_pixel(out, -179.5, 52.0, z=z), BLUE)
    west, _, east, _ = json.loads((out / "metadata.json").read_text())["data_bounds"]
    assert west > 0 > east   # crosses 180, as Cesium rectangles express it
