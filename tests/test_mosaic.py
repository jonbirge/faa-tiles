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


@pytest.mark.parametrize("backend", ["gpu", "cpu"])
def test_sheet_across_the_antimeridian(tmp_path, backend):
    """Run on both warp backends. The sheet is LCC, which the GPU path
    implements, so this is the test that makes the GPU branch actually run --
    the other synthetic sheets are not LCC and fall back to GDAL either way."""
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
    build_mosaic([MosaicSource(sheet)], out, min_zoom=z, max_zoom=z, lossless=True, workers=2,
                 quiet=True, backend=backend)
    assert _close(_pixel(out, 179.5, 52.0, z=z), BLUE)
    assert _close(_pixel(out, -179.5, 52.0, z=z), BLUE)
    west, _, east, _ = json.loads((out / "metadata.json").read_text())["data_bounds"]
    assert west > 0 > east   # crosses 180, as Cesium rectangles express it


# -- both warp backends on LCC sheets ------------------------------------

LCC_US = ("+proj=lcc +lat_1=45 +lat_2=33 +lat_0=39 +lon_0=-95 "
          "+datum=WGS84 +units=m +no_defs")


@pytest.fixture(scope="module", params=["gpu", "cpu"])
def lcc_scene(request, tmp_path_factory):
    """The overlap scene again, but on LCC sheets, so the GPU backend actually
    runs rather than falling back to GDAL. Red is a palette sheet beneath; blue
    sits on top with a square hole cut out of it in lon/lat."""
    root = tmp_path_factory.mktemp(f"lcc-{request.param}")
    red = _solid(root / "a_red.tif", (-200_000, -100_000, 0, 100_000), RED,
                 crs=LCC_US, palette=True)
    blue = _solid(root / "b_blue.tif", (-100_000, -100_000, 100_000, 100_000), BLUE,
                  crs=LCC_US)
    sources = [
        MosaicSource(red),
        MosaicSource(blue, MapArea.from_dict({"exclude": [
            {"lonlat": [[-95.9, 38.7], [-95.3, 38.7], [-95.3, 39.3], [-95.9, 39.3]]},
        ]})),
    ]
    out = root / "out"
    build_mosaic(sources, out, min_zoom=MAX_ZOOM, max_zoom=MAX_ZOOM, lossless=True,
                 workers=2, quiet=True, backend=request.param)
    return out


def test_lcc_overlap_on_both_backends(lcc_scene):
    assert _close(_pixel(lcc_scene, -97.0, 39.0), RED)       # red only
    assert _close(_pixel(lcc_scene, -94.3, 39.0), BLUE)      # blue only
    assert _close(_pixel(lcc_scene, -95.1, 38.4), BLUE)      # overlap: blue on top
    assert _close(_pixel(lcc_scene, -95.6, 39.0), RED)       # through the hole


def test_lcc_palette_is_exact_on_both_backends(lcc_scene):
    """Deep inside a flat sheet the prefilter and bicubic must change nothing --
    a colour shift here would tint every flat area of a chart."""
    assert _close(_pixel(lcc_scene, -96.8, 39.3), RED, tol=1)
    assert _close(_pixel(lcc_scene, -94.0, 39.3), BLUE, tol=1)


# -- seam tiles, and the knobs that trade accuracy for speed ----------------

def _lcc_overlap_sources(root):
    """Two overlapping LCC sheets, as the module fixture builds them: enough of
    the overlap is shared that a good share of the tiles are seam tiles."""
    root.mkdir(parents=True, exist_ok=True)
    red = _solid(root / "a_red.tif", (-200_000, -100_000, 0, 100_000), RED, crs=LCC_US)
    blue = _solid(root / "b_blue.tif", (-100_000, -100_000, 100_000, 100_000), BLUE,
                  crs=LCC_US)
    return [MosaicSource(red), MosaicSource(blue)]


def _tiles(out):
    return {p.relative_to(out).as_posix(): p.read_bytes()
            for p in sorted((out / "tiles").rglob("*.webp"))}


def test_seam_tiles_are_the_same_whether_they_fit_on_the_device(tmp_path, monkeypatch):
    """The GPU backend composites a seam tile's sheets on the device, in a pool
    of preallocated slots, and falls back to host RAM once the slots run out.
    Both routes must produce the same tiles: on the full IFR series the live set
    peaked at 19,796 partials, far past any sane device budget, so the spill is
    a normal path and not an emergency."""
    from cesiumtiles import gpumosaic

    sources = _lcc_overlap_sources(tmp_path / "src")
    plan = plan_tiles(prepare_sources(sources), MAX_ZOOM)
    assert sum(1 for c in plan.values() if len(c) > 1), "no seam tiles to composite"

    built = {}
    # Ample, one slot (so a batch gathers from the device and the spill at once),
    # and none at all.
    for name, budget in (("device", gpumosaic.SEAM_DEVICE_BYTES), ("mixed", 512 * 1024),
                         ("spilled", 0)):
        monkeypatch.setattr(gpumosaic, "SEAM_DEVICE_BYTES", budget)
        out = tmp_path / name
        build_mosaic(sources, out, min_zoom=MAX_ZOOM, max_zoom=MAX_ZOOM, lossless=True,
                     quiet=True, backend="gpu")
        built[name] = _tiles(out)

    assert built["device"], "the scene produced no tiles"
    assert built["device"] == built["mixed"] == built["spilled"]


def test_seam_pool_holds_one_accumulator_per_tile_within_its_budget():
    from cesiumtiles.gpumosaic import seam_slots

    assert seam_slots(10, budget=1 << 30) == 10          # the plan, not the budget
    assert seam_slots(1_000_000, budget=2 * 2**30) == 4096   # 512 KB each
    assert seam_slots(1_000_000, budget=0) == 0          # everything spills


def test_warp_tolerance_reaches_gdal_warp(tmp_path, monkeypatch):
    """The CPU backend's tolerance is gdal.Warp's errorThreshold, and 0 (exact)
    is the default -- any non-zero threshold moves chart hairlines."""
    from cesiumtiles import mosaic

    seen = {}

    def fake_warp(_dest, _source, **kwargs):
        seen.update(kwargs)
        raise AssertionError("stop here; the call itself is what is under test")

    prepared = prepare_sources([MosaicSource(
        _solid(tmp_path / "red.tif", (-100_000, -100_000, 0, 0), RED, crs=LCC_US))])
    monkeypatch.setattr(mosaic.gdal, "Warp", fake_warp)
    mosaic._init_worker(prepared, tmp_path, ".webp", [], "cubic", False, 16, 0.25)
    with pytest.raises(AssertionError):
        mosaic._warp_layer(0, 0.0, 0.0, 1000.0, 256)
    assert seen["errorThreshold"] == 0.25
    assert seen["resampleAlg"] == "cubic"

    mosaic._init_worker(prepared, tmp_path, ".webp", [], "cubic", False, 16)
    with pytest.raises(AssertionError):
        mosaic._warp_layer(0, 0.0, 0.0, 1000.0, 256)
    assert seen["errorThreshold"] == mosaic.ERROR_THRESHOLD == 0.0


def test_gpu_backend_accepts_a_cheaper_reconstruction_filter(tmp_path):
    """--resampling bilinear on the GPU is a sampler choice, not a broken one:
    the source is already prefiltered to the output's Nyquist limit, so flat
    colour must still come through flat."""
    out = tmp_path / "bilinear"
    build_mosaic(_lcc_overlap_sources(tmp_path / "src"), out,
                 min_zoom=MAX_ZOOM, max_zoom=MAX_ZOOM, lossless=True, quiet=True,
                 backend="gpu", resampling="bilinear", tolerance=0.125)
    assert _close(_pixel(out, -97.0, 39.0), RED, tol=1)
    assert _close(_pixel(out, -94.3, 39.0), BLUE, tol=1)


# -- the detail level -------------------------------------------------------
#
# A series can mix scales: VFR sectionals at 1:500,000 with terminal area charts
# at 1:250,000 over the busy airports. Tiling everything at the finer sheets'
# zoom quadruples the mosaic to magnify the coarse 96% of it, so the pyramid
# stops where the coarse sheets stop and one sparse level past it holds the fine
# ones. A client falls back to the stretched parent where that level is absent.

DETAIL_TOP = 8
DETAIL_LEVEL = 9
WIDE = (-110.0, 35.0, -100.0, 45.0)
FINE = (-105.0, 39.5, -104.5, 40.0)


def _detail_scene(root, *, detail):
    root.mkdir(parents=True, exist_ok=True)
    wide = _solid(root / "a_wide.tif", WIDE, RED)
    fine = _solid(root / "b_fine.tif", FINE, BLUE)
    sources = [MosaicSource(wide), MosaicSource(fine, detail=True)]
    out = root / "out"
    result = build_mosaic(sources, out, min_zoom=6, max_zoom=DETAIL_TOP,
                          detail_zoom=DETAIL_LEVEL if detail else None,
                          lossless=True, workers=2, quiet=True)
    return out, result


@pytest.fixture(scope="module")
def detail_scene(tmp_path_factory):
    """A wide coarse sheet with one small sheet marked ``detail`` inside it."""
    return _detail_scene(tmp_path_factory.mktemp("detail"), detail=True)


def test_the_detail_level_exists_only_where_a_detail_source_reaches(detail_scene):
    out, result = detail_scene
    assert result.max_zoom == DETAIL_LEVEL
    # Inside the fine sheet the detail level is drawn, and drawn from it.
    assert _close(_pixel(out, -104.75, 39.75, z=DETAIL_LEVEL), BLUE)
    # Far from it there is no tile at all, so a client draws the z8 parent.
    assert _pixel(out, -108.0, 37.0, z=DETAIL_LEVEL) is None
    assert _close(_pixel(out, -108.0, 37.0, z=DETAIL_TOP), RED)
    # Sparse means sparse: a full level would be four tiles per z8 tile.
    assert result.per_zoom[DETAIL_LEVEL] < result.per_zoom[DETAIL_TOP]


def test_the_detail_level_paints_the_coarse_sheet_under_the_fine_one(detail_scene):
    """A kept tile gets every source, not only the detail ones, so the fine
    sheet's edge sits on the magnified sheet beneath instead of on a hard
    transparent boundary a tile wide."""
    out, _ = detail_scene
    # Same z9 tile as the fine sheet's west edge, just outside the sheet.
    assert _close(_pixel(out, -105.05, 39.75, z=DETAIL_LEVEL), RED)


def test_the_detail_level_feeds_nothing_below_it(tmp_path):
    """The overview cascade starts at max_zoom, the deepest level that covers
    the whole mosaic -- so every tile below is byte for byte what a build
    without a detail level produces."""
    with_detail, _ = _detail_scene(tmp_path / "with", detail=True)
    without, plain = _detail_scene(tmp_path / "without", detail=False)
    assert plain.max_zoom == DETAIL_TOP
    for z in range(6, DETAIL_TOP + 1):
        a = sorted((p.relative_to(with_detail), p.read_bytes()) for p in
                   (with_detail / "tiles" / str(z)).rglob("*.webp"))
        b = sorted((p.relative_to(without), p.read_bytes()) for p in
                   (without / "tiles" / str(z)).rglob("*.webp"))
        assert a == b, f"z{z} differs"


def test_metadata_reports_the_detail_level_and_the_full_coverage(detail_scene):
    """``bounds`` must describe the chart, not the terminal area: read off the
    sparse top level it would frame a single city."""
    out, result = detail_scene
    metadata = json.loads((out / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["maxzoom"] == DETAIL_LEVEL
    assert metadata["fullzoom"] == DETAIL_TOP
    west, south, east, north = metadata["bounds"]
    assert west <= WIDE[0] and south <= WIDE[1] and east >= WIDE[2] and north >= WIDE[3]


def test_a_detail_level_must_be_past_max_zoom_and_have_a_source(tmp_path):
    wide = _solid(tmp_path / "a_wide.tif", WIDE, RED)
    fine = _solid(tmp_path / "b_fine.tif", FINE, BLUE)
    with pytest.raises(ValueError, match="past max_zoom"):
        build_mosaic([MosaicSource(wide), MosaicSource(fine, detail=True)], tmp_path / "a",
                     max_zoom=DETAIL_TOP, detail_zoom=DETAIL_TOP, workers=1, quiet=True)
    with pytest.raises(ValueError, match="no source is marked detail"):
        build_mosaic([MosaicSource(wide), MosaicSource(fine)], tmp_path / "b",
                     max_zoom=DETAIL_TOP, detail_zoom=DETAIL_LEVEL, workers=1, quiet=True)
