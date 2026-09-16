# faa-tiles

Two tools for getting FAA chart rasters onto a Cesium globe.

| Package | Job |
| --- | --- |
| `geotransfer` | Copy georeferencing from a GeoTIFF onto a plain TIFF of identical size |
| `cesiumtiles` | Cut a GeoTIFF into a static `z/x/y` tile pyramid, with a Cesium viewer |

The motivating case: the FAA publishes the U.S. VFR Wall Planning Chart as a
georeferenced but palette-indexed GeoTIFF. A full-colour RGB render of the same
chart at the same resolution has the better pixels but no geo metadata.
`geotransfer` marries the two; `cesiumtiles` then serves the result.

## Reproducing the chart tileset

```bash
.venv/Scripts/python scripts/build_vfr_tileset.py
```

That script is the recipe for the published tileset and a worked example of the
library: georeference the RGB render, crop to the map neatline, tile. It is
commented with the options worth reaching for — `--lossy`, `--max-zoom`,
`--scheme`, `--skip-blank` — and `--dry-run` prints the plan without writing
280 MB. Result: **6,372 tiles, 280.4 MB, ~64 s** on 24 cores.

## Setup

```bash
py -3 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pip install -e .
```

Runtime-only install: `-r requirements.txt`.

### About the GDAL dependency

`cesiumtiles` needs GDAL's Python bindings (`osgeo`) for the `gdal raster tile`
algorithm. **PyPI's `GDAL` package is source-only on Windows for every Python
version**, so `requirements.txt` points at Christoph Gohlke's
[geospatial-wheels](https://github.com/cgohlke/geospatial-wheels) index, which
publishes real `cp314` win_amd64 binaries:

```
--extra-index-url https://gisidx.github.io/gwi
```

This gives GDAL **3.13.3** — newer than the 3.8.4 that Ubuntu 24.04's apt
provides, so there is no advantage to building this under WSL. `osgeo.gdal` and
`rasterio` coexist in one venv, each using its own GDAL build.

---

## `cesiumtiles` — static tile pyramids

```bash
.venv/Scripts/cesiumtiles vfr_wall_planning_geo.tif ./tileset
```

```python
from cesiumtiles import build_tileset

result = build_tileset("vfr_wall_planning_geo.tif", "./tileset")
print(result.summary())
```

Output layout:

```
tileset/
  tiles/{z}/{x}/{y}.webp    the pyramid
  metadata.json             bounds, zooms, counts, url template
  index.html                a working Cesium viewer
```

The viewer reads `metadata.json` at runtime, so re-tiling with different bounds
or zooms needs no change to the HTML. It exposes `window.viewer` and
`window.tileTracker` for poking at the scene from the dev console.

It also carries a diagnostics panel:

- **On screen** — how many imagery tiles the globe is drawing, broken down by
  zoom level with the x/y range at each, how many are still loading, and the
  camera altitude.
- **Downloaded** — tiles fetched, bytes over the wire, average tile size, tiles
  served from cache, and the most recent tile requested.

**Reset counters & cache** zeroes the counters *and* forces the next load to be
genuinely cold. Script cannot clear the browser's HTTP cache, so it rebuilds the
imagery layer against a fresh query string, which misses both Cesium's in-memory
tile cache and the browser's. Without that, pressing reset and flying around
would just replay local copies and report almost no traffic.

Note that a cache hit is not simply "zero bytes transferred": browsers may report
a fixed ~300-byte header placeholder with a full body size and a 200 status. The
panel classifies by whether `transferSize` is smaller than `encodedBodySize`,
which is what actually indicates the body never crossed the wire.

### Previewing a tileset

The tiles are plain static files, so any web server will do. A preview server is
included because `python -m http.server` sends no CORS headers, which blocks the
tiles the moment a Cesium app on a different origin or port tries to read them.

```bash
.venv/Scripts/cesiumtiles-serve tileset
```

Then open <http://127.0.0.1:8000/>. `Ctrl-C` stops it. Equivalent forms:

```bash
.venv/Scripts/python -m cesiumtiles.serve tileset --port 8000
```

```python
from cesiumtiles import serve_tileset

server = serve_tileset("tileset", port=8000, background=True)
...
server.shutdown()
```

| Option | Meaning |
| --- | --- |
| `-p`, `--port N` | Port to listen on (default 8000). |
| `--host ADDR` | Bind address. Default `127.0.0.1`; use `0.0.0.0` to expose on the LAN. |
| `--no-cors` | Omit `Access-Control-Allow-Origin`. |
| `--open` | Open the viewer in a browser once the server is up. |

It serves correct MIME types for `.webp`/`.png`/`.jpg`, sends `no-cache` for
`index.html` and `metadata.json` so a re-tile is visible on reload, and logs
only failed requests rather than every one of thousands of tiles.

Under Claude Code, `.claude/launch.json` defines `tileset` (port 8000) and
`tileset-colorado` (port 8001) so the browser pane can start either directly.

### Choosing the zoom range

`--max-zoom` defaults to the level at which tile pixels match the source's own
resolution, so no detail is discarded and none is invented. For the VFR wall
planning chart (262 m/px in Lambert Conformal Conic) that lands at **z9**;
zooming past it in Cesium just magnifies the top level, which is expected.

`--min-zoom` defaults to 0 so Cesium always has a complete pyramid to descend.

Every tile in the covered rectangle is written by default, including the fully
transparent ones along the chart's curved Lambert Conformal Conic edges — 6,552
for the chart cropped to its neatline (7,190 for the whole uncropped sheet). Blank tiles cost almost nothing (the pyramid is 285.0 MB
either way), and keeping them means Cesium never requests a URL that 404s.
`--skip-blank` drops the count to 5,577 if you would rather have the smaller
tree and can tolerate the misses.

### Cropping

`--bbox WEST SOUTH EAST NORTH` crops before tiling, in lon/lat degrees by
default. The crop is exact: it is applied as a warp cutline, so pixels outside
the rectangle become transparent rather than being merely clipped to the
nearest tile edge.

```bash
.venv/Scripts/cesiumtiles chart.tif ./colorado --bbox -109.06 36.99 -102.04 41.00
```

Use `--bbox-crs` to give the rectangle in some other frame, e.g.
`--bbox-crs EPSG:3857` with metre coordinates, or **`--bbox-crs source`** for the
raster's own CRS. Note that the *reported* bounds in `metadata.json` snap outward
to whole tiles, since that is what Cesium needs for its imagery rectangle.

#### Trimming to a map's neatline

A printed chart carries a margin, a border and a scale bar, and they are
georeferenced along with the map — so without a crop they get pasted onto the
globe as if they were terrain. Cropping them off is what `--bbox-crs source` is
for, because **a neatline is a rectangle in the projection the chart was drawn
in, not in lon/lat**. On the VFR wall planning chart the sheet's corners
differ by 8.3 degrees of longitude between NW and SW, so a lon/lat box would
leave white wedges in the corners.

The crop also has to be **inscribed** in the map rather than circumscribed about
it. The neatline is not square to the pixel grid — its top edge runs from row 272
on the left of the sheet to row 200 on the right — so any axis-aligned box
containing the whole map also contains slices of border and paper. Trimming to
the inscribed box costs about 1.8% of the area and is what actually keeps the
edges clean.

```bash
.venv/Scripts/cesiumtiles vfr_wall_planning_geo.tif ./tileset     --bbox-crs source --bbox -2065471.156 -1353550.704 2560432.418 1453780.3
```

`scripts/build_vfr_tileset.py` does this for you, and can re-measure the
neatline from the image with `--detect-neatline` when a new chart edition comes
out.

### Options

| Option | Meaning |
| --- | --- |
| `--scheme mercator\|geographic` | `mercator` (default) is EPSG:3857 WebMercatorQuad — the standard slippy-map grid, and zero-config for Cesium's `UrlTemplateImageryProvider`. `geographic` is EPSG:4326 WorldCRS84Quad, matching Cesium's native globe tiling. |
| `--format webp\|png\|jpeg` | Default `webp`. |
| `--lossy` / `--quality N` | Lossy webp. Roughly 4x smaller, but can ring around hairline linework and text. |
| `--min-zoom` / `--max-zoom` | Override the automatic range. |
| `--resampling` / `--overview-resampling` | GDAL kernels; both default to `lanczos`. |
| `--skip-blank` | Omit fully transparent tiles. Smaller, but the viewer will generate 404s for them. |
| `--threads` | Worker count, or `ALL_CPUS` (default). |
| `--resume` | Write only missing tiles. |
| `-f`, `--overwrite` | Replace a non-empty output directory. |

### Format sizes

Measured on real chart tiles, extrapolated to the full 7,190-tile pyramid:

| Format | KB/tile | Full tileset |
| --- | --- | --- |
| PNG | 66.4 | ~370 MB |
| WebP lossless (default) | 49.9 | **285 MB** |
| WebP q95 | 11.4 | ~64 MB |
| WebP q90 | 8.6 | ~48 MB |

### Parallelism

Tiling runs in parallel: GDAL spawns worker processes, each taking a range of
tiles. Measured on a 24-core machine over a 2,455-tile western-US crop:

| Threads | Wall time | Speed-up |
| --- | --- | --- |
| 1 | 135.1 s | 1.0x |
| 4 | 64.4 s | 2.1x |
| 8 | 47.6 s | 2.8x |
| `ALL_CPUS` (24) | 35.3 s | 3.8x |

Scaling flattens well before 24 cores because only the top zoom parallelises
well. Splitting that same job by level: **z9 alone is 12.8 s for 1,804 tiles**
(141 tiles/s), while **z0-z8 is 25.9 s for 651 tiles** (25 tiles/s). The
overview cascade is inherently sequential — each level is built from the one
below — so it dominates wall time and caps the overall speed-up.

Converting the source to a tiled COG with overviews does **not** help (34.6 s
vs 36.0 s measured); the stripped source layout is not the bottleneck.

### How it works

Tiling is delegated to GDAL's `gdal raster tile`, which since GDAL 3.11 is the
maintained reference implementation — `gdal2tiles` is deprecated in favour of
it from 3.13. This package supplies what that algorithm does not: geographic
bbox cropping, zoom defaults derived from the source resolution, and Cesium
metadata and a viewer (GDAL emits Leaflet, OpenLayers, MapML and STAC front
ends, but not Cesium).

Counts and bounds in `TilesetResult` are read back off disk after the run
rather than assumed from the request.

---

## `geotransfer` — georeferencing transfer

```python
from geotransfer import copy_geo_metadata

copy_geo_metadata(
    "vfr_geotiff_original.tif",   # has the CRS + transform
    "vfr_wall_planning.tif",      # has the pixels
    "vfr_wall_planning_geo.tif",  # gets both
)
```

```bash
.venv/Scripts/geotransfer vfr_geotiff_original.tif vfr_wall_planning.tif out.tif
```

The image file is duplicated byte-for-byte and only the GeoTIFF header tags are
rewritten. Nothing is decoded, resampled or recompressed, so band count, colour
interpretation, compression and predictor all survive exactly — a 250 MB chart
takes well under a second.

Copies CRS, affine transform (or GCPs and RPCs, if the reference is
georeferenced that way) and the `AREA_OR_POINT` pixel-convention tag. The
reference's colour table, band structure and nodata are **not** copied; those
belong to the image file.

| Option | Meaning |
| --- | --- |
| `overwrite` / `-f` | Replace `output` if it exists. |
| `strict_size` / `--no-strict-size` | Size checking is on by default. |
| `copy_nodata` / `--copy-nodata` | Also copy the reference's nodata value. |

---

## Tests

```bash
.venv/Scripts/python -m pytest
```

115 tests, all against small synthetic rasters built in a temp directory — none
need the chart files. The tile arithmetic in `cesiumtiles.scheme` is checked
against [mercantile](https://github.com/mapbox/mercantile), a separate
implementation of the same grid, so agreement is evidence rather than tautology.

## Layout

```
pyproject.toml            packaging + pytest config
requirements.txt          runtime deps (incl. the GDAL wheel index)
requirements-dev.txt      runtime + test deps
src/geotransfer/
    core.py               copy_geo_metadata / read_georeference
    cli.py
src/cesiumtiles/
    scheme.py             XYZ grid maths for both tiling schemes
    core.py               build_tileset
    viewer.py             Cesium viewer generation
    serve.py              local preview server (CORS, tile MIME types)
    cli.py
tests/
    test_core.py          georeferencing transfer
    test_scheme.py        tile maths vs mercantile
    test_tiles.py         end-to-end tileset builds
    test_serve.py         preview server behaviour
.claude/
    launch.json           dev-server definitions for the browser pane
CLAUDE.md                 orientation notes for Claude Code
```
