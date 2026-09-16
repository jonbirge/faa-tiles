"""End-to-end tileset builds against small synthetic rasters."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from PIL import Image
from rasterio.crs import CRS
from rasterio.transform import from_bounds

from cesiumtiles import TileBuildError, build_tileset
from cesiumtiles.scheme import WEB_MERCATOR

# A small patch of Colorado, in lon/lat.
WEST, SOUTH, EAST, NORTH = -106.0, 39.0, -104.0, 40.5


def _write_source(path, *, bounds=(WEST, SOUTH, EAST, NORTH), size=512, crs="EPSG:4326", georeferenced=True):
    west, south, east, north = bounds
    rng = np.random.default_rng(1)
    # A gradient plus noise: downsampling artefacts would show up as banding.
    ramp = np.linspace(0, 255, size, dtype="float32")
    data = np.stack([
        np.broadcast_to(ramp, (size, size)),
        np.broadcast_to(ramp[:, None], (size, size)),
        rng.integers(0, 256, (size, size)),
    ]).astype("uint8")

    profile = {
        "driver": "GTiff", "width": size, "height": size, "count": 3,
        "dtype": "uint8", "compress": "lzw",
    }
    if georeferenced:
        profile["crs"] = CRS.from_string(crs)
        profile["transform"] = from_bounds(west, south, east, north, size, size)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data)
    return path


@pytest.fixture
def source(tmp_path):
    return _write_source(tmp_path / "source.tif")


def test_builds_a_full_pyramid(tmp_path, source):
    out = tmp_path / "tiles_out"
    result = build_tileset(source, out, quiet=True)

    assert result.min_zoom == 0
    assert result.max_zoom == result.native_zoom
    assert result.tile_count == sum(result.per_zoom.values())
    assert result.total_bytes > 0
    # Every level between min and max must be present, or Cesium sees holes.
    assert sorted(result.per_zoom) == list(range(result.min_zoom, result.max_zoom + 1))
    assert result.per_zoom[result.min_zoom] <= result.per_zoom[result.max_zoom]


def test_tiles_land_at_the_documented_paths(tmp_path, source):
    out = tmp_path / "tiles_out"
    result = build_tileset(source, out, quiet=True)

    meta = json.loads((out / "metadata.json").read_text())
    assert meta["url_template"] == "tiles/{z}/{x}/{y}.webp"
    assert meta["convention"] == "xyz"
    assert meta["crs"] == "EPSG:3857"

    for z, x, y in [(result.max_zoom, *next(iter(_any_tile(out, result.max_zoom))))]:
        assert (out / "tiles" / str(z) / str(x) / f"{y}.webp").is_file()


def _any_tile(out, z):
    z_dir = out / "tiles" / str(z)
    for x_dir in z_dir.iterdir():
        for tile in x_dir.iterdir():
            yield int(x_dir.name), int(tile.stem)
            return


def test_tiles_are_256px_rgba(tmp_path, source):
    out = tmp_path / "tiles_out"
    result = build_tileset(source, out, quiet=True)
    x, y = next(iter(_any_tile(out, result.max_zoom)))
    img = Image.open(out / "tiles" / str(result.max_zoom) / str(x) / f"{y}.webp")
    assert img.size == (256, 256)
    assert img.convert("RGBA").getchannel("A").getextrema()[1] == 255


def test_viewer_and_metadata_are_written(tmp_path, source):
    out = tmp_path / "tiles_out"
    build_tileset(source, out, quiet=True, title="Test Chart")

    html = (out / "index.html").read_text(encoding="utf-8")
    assert "UrlTemplateImageryProvider" in html
    assert "WebMercatorTilingScheme" in html
    assert "Test Chart" in html
    # The baked-in fallback must be real JSON, not a placeholder.
    assert '"maxzoom"' in html

    meta = json.loads((out / "metadata.json").read_text())
    assert meta["name"] == "Test Chart"
    assert meta["minzoom"] <= meta["maxzoom"]


def test_reported_bounds_cover_the_source(tmp_path, source):
    out = tmp_path / "tiles_out"
    result = build_tileset(source, out, quiet=True)
    west, south, east, north = result.bounds_lonlat
    # Tile edges snap outward to the grid, so coverage is a superset.
    assert west <= WEST + 1e-6
    assert south <= SOUTH + 1e-6
    assert east >= EAST - 1e-6
    assert north >= NORTH - 1e-6


# -- cropping ----------------------------------------------------------


def _area(bounds):
    west, south, east, north = bounds
    return (east - west) * (north - south)


def test_bbox_shrinks_the_covered_extent(tmp_path, source):
    full = build_tileset(source, tmp_path / "full", quiet=True)
    half = build_tileset(
        source, tmp_path / "half", bbox=(-105.5, 39.25, -104.5, 40.0), quiet=True
    )
    assert half.tile_count < full.tile_count
    # Reported bounds snap outward to tile edges, so a crop landing inside the
    # same edge tile leaves that side unchanged; the covered area must still shrink.
    assert _area(half.bounds_lonlat) < _area(full.bounds_lonlat)
    assert half.bounds_lonlat[0] >= full.bounds_lonlat[0]
    assert half.bounds_lonlat[2] <= full.bounds_lonlat[2]


def test_bbox_makes_pixels_outside_it_transparent(tmp_path, source):
    bbox = (-105.5, 39.25, -104.5, 40.0)
    result = build_tileset(source, tmp_path / "crop", bbox=bbox, quiet=True)

    # Find the tile straddling the western crop edge and check across it.
    import mercantile

    edge_x, mid_y = mercantile.xy(bbox[0], (bbox[1] + bbox[3]) / 2)
    z = result.max_zoom
    rng = WEB_MERCATOR.tile_range(z, (edge_x - 1, mid_y - 1, edge_x + 1, mid_y + 1))
    tile = result.tile_dir / str(z) / str(rng.x_min) / f"{rng.y_min}.webp"
    assert tile.is_file()

    alpha = np.array(Image.open(tile).convert("RGBA"))[:, :, 3]
    west, _, east, _ = WEB_MERCATOR.tile_bounds(z, rng.x_min, rng.y_min)
    col = int((edge_x - west) / (east - west) * 256)
    assert 4 < col < 252, "crop edge should fall inside this tile"
    assert alpha[:, : col - 2].max() == 0, "pixels west of the crop must be transparent"
    assert alpha[:, col + 2 :].min() == 255, "pixels east of the crop must be opaque"


def test_bbox_accepts_a_projected_crs(tmp_path, source):
    import mercantile

    west, south = mercantile.xy(-105.5, 39.25)
    east, north = mercantile.xy(-104.5, 40.0)
    projected = build_tileset(
        source, tmp_path / "proj", bbox=(west, south, east, north),
        bbox_crs="EPSG:3857", quiet=True,
    )
    geographic = build_tileset(
        source, tmp_path / "geo", bbox=(-105.5, 39.25, -104.5, 40.0), quiet=True
    )
    assert projected.tile_count == geographic.tile_count
    assert projected.bounds_lonlat == pytest.approx(geographic.bounds_lonlat, abs=1e-6)


def test_bbox_outside_the_source_is_rejected(tmp_path, source):
    with pytest.raises(TileBuildError, match="does not overlap"):
        build_tileset(source, tmp_path / "nope", bbox=(10.0, 10.0, 11.0, 11.0), quiet=True)


def test_inverted_bbox_is_rejected(tmp_path, source):
    with pytest.raises(ValueError, match="west, south, east, north"):
        build_tileset(source, tmp_path / "nope", bbox=(-104.0, 39.0, -106.0, 40.5), quiet=True)


# -- options and failure modes -----------------------------------------


def test_max_zoom_override_is_respected(tmp_path, source):
    result = build_tileset(source, tmp_path / "shallow", max_zoom=5, min_zoom=2, quiet=True)
    assert result.max_zoom == 5
    assert result.min_zoom == 2
    assert sorted(result.per_zoom) == [2, 3, 4, 5]


def test_geographic_scheme_uses_the_4326_grid(tmp_path, source):
    result = build_tileset(source, tmp_path / "geo", scheme="geographic", quiet=True)
    assert result.crs == "EPSG:4326"
    meta = json.loads((result.output_dir / "metadata.json").read_text())
    assert meta["scheme"] == "geographic"
    assert "GeographicTilingScheme" in (result.output_dir / "index.html").read_text(encoding="utf-8")


def test_png_format(tmp_path, source):
    result = build_tileset(source, tmp_path / "png", tile_format="png", quiet=True)
    x, y = next(iter(_any_tile(result.output_dir, result.max_zoom)))
    assert (result.tile_dir / str(result.max_zoom) / str(x) / f"{y}.png").is_file()


def test_lossy_webp_is_smaller_than_lossless(tmp_path, source):
    big = build_tileset(source, tmp_path / "lossless", quiet=True)
    small = build_tileset(source, tmp_path / "lossy", lossless=False, quality=80, quiet=True)
    assert small.total_bytes < big.total_bytes


def test_ungeoreferenced_source_is_rejected(tmp_path):
    plain = _write_source(tmp_path / "plain.tif", georeferenced=False)
    with pytest.raises(TileBuildError, match="no CRS"):
        build_tileset(plain, tmp_path / "out", quiet=True)


def test_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_tileset(tmp_path / "absent.tif", tmp_path / "out", quiet=True)


def test_unknown_scheme_and_format(tmp_path, source):
    with pytest.raises(ValueError, match="scheme must be"):
        build_tileset(source, tmp_path / "a", scheme="utm", quiet=True)
    with pytest.raises(ValueError, match="tile_format must be"):
        build_tileset(source, tmp_path / "b", tile_format="gif", quiet=True)


def test_min_zoom_above_max_zoom_is_rejected(tmp_path, source):
    with pytest.raises(ValueError, match="exceeds max_zoom"):
        build_tileset(source, tmp_path / "out", min_zoom=8, max_zoom=4, quiet=True)


def test_refuses_to_clobber_a_populated_directory(tmp_path, source):
    out = tmp_path / "out"
    build_tileset(source, out, quiet=True)
    with pytest.raises(FileExistsError):
        build_tileset(source, out, quiet=True)
    build_tileset(source, out, overwrite=True, quiet=True)


# -- parallelism regressions -------------------------------------------


def test_boolean_flags_are_omitted_when_false(tmp_path, source, monkeypatch):
    """gdal.Run enables any boolean key that is present, whatever its value.

    Passing skip-blank=False therefore used to *enable* skipping, silently
    contradicting the default and leaving holes the viewer would 404 on.
    """
    from osgeo import gdal

    seen = {}
    real = gdal.Run

    def spy(*args, **kwargs):
        seen.update(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(gdal, "Run", spy)
    build_tileset(source, tmp_path / "out", quiet=False, max_zoom=4)

    assert "skip-blank" not in seen
    assert "resume" not in seen
    assert "quiet" not in seen
    assert seen["add-alpha"] is True


def test_boolean_flags_are_passed_when_true(tmp_path, source, monkeypatch):
    from osgeo import gdal

    seen = {}
    real = gdal.Run

    def spy(*args, **kwargs):
        seen.update(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(gdal, "Run", spy)
    build_tileset(source, tmp_path / "out", skip_blank=True, quiet=True, max_zoom=4)

    assert seen["skip-blank"] is True
    assert seen["quiet"] is True


def test_cropped_input_is_a_real_file_not_an_anonymous_dataset(tmp_path, source, monkeypatch):
    """A crop must be tileable in parallel.

    gdal raster tile spawns child processes for large jobs, so its input has to
    be openable by name from another process. An in-memory or anonymous dataset
    fails outright on a big job and quietly drops to one thread on a small one.
    """
    from osgeo import gdal

    seen = {}
    real = gdal.Run

    def spy(*args, **kwargs):
        seen.update(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(gdal, "Run", spy)
    build_tileset(source, tmp_path / "out", bbox=(-105.5, 39.25, -104.5, 40.0), quiet=True)

    handed_over = seen["input"]
    assert isinstance(handed_over, str), "input must be a path, not a dataset object"
    assert handed_over.endswith(".vrt")
    # It must have been a real on-disk file, and cleaned up afterwards.
    assert not handed_over.startswith("/vsimem"), "a /vsimem path is invisible to child processes"
    assert not Path(handed_over).exists(), "scratch VRT should be removed after the build"


def test_uncropped_input_is_also_a_path(tmp_path, source, monkeypatch):
    from osgeo import gdal

    seen = {}
    real = gdal.Run
    monkeypatch.setattr(gdal, "Run", lambda *a, **k: (seen.update(k), real(*a, **k))[1])
    build_tileset(source, tmp_path / "out", quiet=True, max_zoom=4)
    assert seen["input"] == str(Path(source).resolve())


def test_bbox_crs_source_uses_the_rasters_own_frame(tmp_path, source):
    """A map neatline is a rectangle in the chart's projection, not in lon/lat.

    For a source that is already EPSG:4326 the two spellings must agree exactly;
    the point of "source" is that it also works when the CRS has no EPSG code,
    as with the FAA chart's custom Lambert Conformal Conic.
    """
    explicit = build_tileset(
        source, tmp_path / "explicit", bbox=(-105.5, 39.25, -104.5, 40.0),
        bbox_crs="EPSG:4326", quiet=True,
    )
    from_source = build_tileset(
        source, tmp_path / "from_source", bbox=(-105.5, 39.25, -104.5, 40.0),
        bbox_crs="source", quiet=True,
    )
    assert from_source.tile_count == explicit.tile_count
    assert from_source.bounds_lonlat == pytest.approx(explicit.bounds_lonlat, abs=1e-9)


def test_bbox_crs_source_is_case_insensitive(tmp_path, source):
    result = build_tileset(
        source, tmp_path / "out", bbox=(-105.5, 39.25, -104.5, 40.0),
        bbox_crs="SOURCE", quiet=True,
    )
    assert result.tile_count > 0


def test_viewer_rectangle_uses_the_unsnapped_extent(tmp_path, source):
    """Cesium crashes if the imagery rectangle sits exactly on a tile boundary.

    `bounds` is snapped outward to whole tiles for tile-coverage purposes, so an
    edge coincides exactly with an imagery tile edge. Cesium's
    _createTileImagerySkeletons then computes an empty intersection and passes
    undefined into rectangleToNativeRectangle, throwing "can't access property
    west" from inside the render loop. The viewer must use `data_bounds`.
    """
    result = build_tileset(source, tmp_path / "out", quiet=True)
    meta = json.loads((result.output_dir / "metadata.json").read_text())

    assert "data_bounds" in meta, "the viewer depends on this key"
    dw, ds, de, dn = meta["data_bounds"]
    bw, bs, be, bn = meta["bounds"]
    # The true extent must sit inside the tile-snapped coverage, or the viewer
    # would clip away imagery that exists.
    assert bw <= dw and bs <= ds and be >= de and bn >= dn

    html = (result.output_dir / "index.html").read_text(encoding="utf-8")
    assert "extentOf" in html
    assert "meta.data_bounds" in html
    # The rectangle must not be built straight from the snapped bounds.
    assert "const [w, s, e, n] = meta.bounds;" not in html


def test_viewer_includes_the_diagnostics_panel(tmp_path, source):
    """The panel reports visible tiles and download traffic, with a reset."""
    result = build_tileset(source, tmp_path / "out", quiet=True)
    html = (result.output_dir / "index.html").read_text(encoding="utf-8")

    # Visible-tile readout, from Cesium's render list.
    assert "visibleTiles" in html
    assert "_tilesToRender" in html
    # Traffic accounting, from Resource Timing.
    assert "PerformanceObserver" in html
    assert "encodedBodySize" in html
    assert "transferSize" in html
    # Reset must clear the counters *and* force a cold reload, which needs a
    # cache-busting token; without it the next load replays the browser cache.
    assert 'id="reset"' in html
    assert "bust = Date.now()" in html
    assert "removeAll()" in html


def test_viewer_cache_classification_compares_wire_to_body(tmp_path, source):
    """A cache hit can report a ~300 byte header placeholder with a 200 status.

    Treating any non-zero transferSize as a download therefore miscounts a fully
    cached load as a full download. The test pins the comparison that actually
    distinguishes them.
    """
    result = build_tileset(source, tmp_path / "out", quiet=True)
    html = (result.output_dir / "index.html").read_text(encoding="utf-8")
    assert "wire < body" in html


def test_viewer_is_a_general_tile_tester(tmp_path, source):
    """The page must load any tileset, not just the one it was generated for."""
    result = build_tileset(source, tmp_path / "out", quiet=True)
    html = (result.output_dir / "index.html").read_text(encoding="utf-8")

    assert 'id="source"' in html and 'id="load"' in html
    for control in ('id="scheme"', 'id="minzoom"', 'id="maxzoom"', 'id="tilesize"'):
        assert control in html
    # A directory is resolved through its metadata.json; a raw template is used
    # as given, with the form supplying what the metadata would have.
    assert "resolveSource" in html
    assert 'spec.indexOf("{z}")' in html
    assert "metadata.json" in html
    # Cross-origin tile servers withhold Resource Timing sizes; those must be
    # reported as unavailable rather than silently counted as zero bytes.
    assert "opaque" in html
    assert "cross-origin" in html


def test_viewer_has_no_title_heading(tmp_path, source):
    result = build_tileset(source, tmp_path / "out", quiet=True, title="Test Chart")
    html = (result.output_dir / "index.html").read_text(encoding="utf-8")
    assert "<h1" not in html
    # The document title still carries the name, for the browser tab.
    assert "<title>Test Chart</title>" in html


def test_grid_ramps_blue_to_orange_across_the_zoom_range(tmp_path, source):
    """Blue at z0 through to orange at maxzoom, scaled to the tileset loaded.

    The ramp is computed from level/maxzoom rather than baked in, so pointing
    the tester at a source with a different depth re-scales it instead of
    running off the end of a fixed list.
    """
    result = build_tileset(source, tmp_path / "out", quiet=True)
    html = (result.output_dir / "index.html").read_text(encoding="utf-8")
    assert "GRID_HUE_START" in html and "GRID_HUE_SPAN" in html
    assert "level / span" in html
    # Borders are half transparent, per the requested look.
    assert "GRID_ALPHA = 0.5" in html
    assert "gridColor(level, meta.maxzoom, GRID_ALPHA)" in html
