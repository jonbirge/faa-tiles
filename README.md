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
```

A tileset is **data only** - no viewer is written into it. The tile tester is
served by `cesiumtiles-serve`, which can therefore sit above several tilesets and
switch between them.

The tester reads `metadata.json` at runtime, so re-tiling with different bounds
or zooms needs no change to the HTML. It exposes `window.viewer` and
`window.tileTracker` for poking at the scene from the dev console.

It also carries a diagnostics panel:

- **On screen** — how many imagery tiles the globe is drawing, broken down by
  zoom level with the x/y range at each, how many are still loading, and the
  camera altitude.
- **Downloaded** — tiles fetched, bytes over the wire, average tile size, tiles
  served from cache, and the most recent tile requested.

The **Rendering** section controls how Cesium draws the tiles, which matters when
comparing tilesets because two of its defaults flatter or penalise them
misleadingly:

| control | what it does |
| --- | --- |
| `max SSE` | `globe.maximumScreenSpaceError`, default **2**. How aggressively the globe refines. Lower fetches deeper tiles sooner — 1 roughly doubles the tiles on screen. |
| `scale` | Cesium defaults `useBrowserRecommendedResolution` to true, which **ignores the display's pixel ratio**: on a 1.5x screen the globe renders at two thirds of the panel's sharpness. This turns that off and sets `resolutionScale`; above 1 it supersamples. |
| `magnify` | Texture magnification past the deepest zoom. Cesium's default is `LINEAR`, so every tile is bilinearly smeared once you pass max zoom — which reads as the *tileset* being soft when it is not. `nearest` keeps pixels hard and honest. |
| `MSAA` | `scene.msaaSamples`. Affects geometry edges, including the globe silhouette, more than imagery. |

When judging an upsampler, set `magnify` to `nearest` and `scale` to your display's
pixel ratio first — otherwise you are partly grading Cesium's bilinear filter.

**Show tile grid** overlays each tile's boundary as a semi-transparent border,
coloured by zoom level, with matching swatches beside the levels in the *On
screen* list. The overlay is drawn on canvas rather than fetched, so it does not
disturb the traffic counters.

The border is a continuous ramp: **deep blue at z0 through to almost-red at the
maximum zoom**, drawn at 50% transparency over a faint dark hairline that keeps
it visible where the imagery beneath is pale. The colour is computed from
`level / maxzoom`, so pointing the tester at a shallower or deeper source
re-scales the ramp rather than running off the end of a fixed list. The hue
travels the short way round, through purple and red, which keeps it clear of the
greens and yellows the terrain shading uses.

One caveat worth knowing: on a smooth ramp, *adjacent* levels are the least
distinguishable, and adjacent levels are exactly what Cesium renders together.
The swatches in the *On screen* list name the levels outright, so identity never
rests on the colour alone.

### Pointing it at other tiles

The viewer is a general tile tester, not tied to the tileset it ships beside.
The **Source** box takes either:

- a **tileset directory** — `.`, `../other-tileset`, or an absolute URL — which
  is read through its `metadata.json`, so scheme, zooms, extent and size all
  come across automatically; or
- a raw **`{z}/{x}/{y}` URL template**, used as given, with the scheme, tile size
  and zoom range taken from the controls beside it.

Swapping sources **leaves the camera where it is**, so two tilesets can be
compared at a fixed viewpoint — flip between `./tileset` and `./tileset-lossy`
and only the imagery changes. If the new tileset does not cover where you are
looking, the panel says so and **Fly to extent** takes you there.

To compare local tilesets, serve their common parent:
`.venv/Scripts/cesiumtiles-serve .`. The server finds the tilesets beneath it and
opens the first; load the others by name. The tester is always at `/`, whichever
directory you serve.

A remote server must allow cross-origin requests. If it also omits
`Timing-Allow-Origin`, the browser withholds transfer sizes, and the panel
reports network bytes as `n/a (cross-origin)` rather than pretending they are
zero — tile counts still work.

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
.venv/Scripts/cesiumtiles-serve
```

It serves the working directory by default and finds the tilesets beneath it, so
they are addressed as `./tileset`, `./other` and so on, and several can be
compared in one session.

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

Under Claude Code, `.claude/launch.json` defines `tileset` on port 8000 so the
browser pane can start it directly.

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

Tilesets are large; treat any you make this way as scratch and delete them when
you are done.

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

Lossless is the default, but **q95 was reviewed on the real chart and showed no
discernible ringing** — including on hairline symbology and type, which is where
it would show first. `tileset-lossy` is that build: same 6,372 tiles at
**72.3 MB against 280.4 MB**, a 3.9x saving. Worth considering as the default if
serving cost matters more than exactness.

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

## Planned work

Four things worth building next, roughly in dependency order. Each notes what
already exists to build on.

### Upsample the source before tiling

The chart's native resolution runs out at **z9** — 262 m/px in Lambert Conformal
Conic, which is where `--max-zoom`'s auto-detection lands. Past that Cesium
magnifies the top level and the linework goes soft. Upsampling the GeoTIFF 2x
before tiling would put a genuine z10 in the pyramid, with hairlines and type
resampled smoothly rather than stretched.

Worth being honest about what this buys: classical upsampling (lanczos, cubic,
Lanczos-3 in `gdal.Warp`) **adds no information**. It makes magnification look
clean instead of blocky, which matters a lot for chart symbology, but it does not
recover detail the scan never had. The costs are concrete: 4x the pixels (212 Mpx
→ 850 Mpx), roughly 4x the tiles at the new top level (~4,700 → ~19,000), and a
source file that no longer fits comfortably in memory, so the warp wants to stay
a VRT rather than being materialised.

`build_vfr_tileset.py` is the place for it — a stage between the crop and the
tiling, with the neatline detection running on the original rather than the
upsampled copy.

**Which kernel.** The usual signal-processing framing does not fit this artwork.
Sinc-family reconstruction assumes the raster is a bandlimited sampling of a
continuous field; a chart is a *rasterised vector drawing* — piecewise-constant
regions meeting at step edges, which have unbounded bandwidth. A sinc kernel
therefore overshoots on both sides of every edge, which is the halo. Measured on
a 256x256 Denver crop (flat fills, magenta airways, type and relief together),
upsampling 2x, where "ringing" counts output pixels straying outside the range of
the four source pixels they sit between:

| kernel | ringing | worst excursion | sharpness |
| --- | --- | --- | --- |
| near | 0.00% | 0 | 8.18 |
| bilinear | 0.00% | 0 | 7.00 |
| cubic | 5.24% | 21 | 8.28 |
| cubicspline | 2.86% | 23 | 6.12 |
| lanczos | 10.85% | 32 | 8.90 |

No GDAL kernel gives both zero ringing and sharp edges, and none can: **every
one of them except `near` is a linear filter**, so each bandlimits edges by
construction and the ringing is the Gibbs overshoot that follows. `near` avoids
it only by aliasing instead. Choosing among them is choosing among options that
share the defect, so the answer has to come from outside that family.

**Ruled out, and why:**

- **Edge-directed interpolation** (NEDI, DCCI, ICBI, EGII) — non-linear and
  genuinely edge-aware, but built for *natural* images: smooth gradients
  interrupted by edges. The literature is lukewarm even there, with NEDI often
  scoring below plain bicubic, since edge direction is hard to estimate from the
  low-resolution data. Our prior is stronger and different — piecewise-constant
  regions — and these methods do not exploit it.
- **Pixel-art scalers** (hqx, xBR/xBRZ, Super-xBR, scale2x) — the closest match
  to the premise, non-linear, and they produce clean diagonals with neither blur
  nor ringing. The blocker is that they assume **aliased** input from a small
  palette. This chart is antialiased on type and hairlines, and its shaded relief
  is continuous tone; both would be quantised into something worse than they
  started. Right family, wrong source.
- **Vectorise and re-rasterise** (potrace, or Kopf & Lischinski's *Depixelizing
  Pixel Art*) — theoretically correct for the flat-region part, since the chart
  was vector before it was raster, and the palette-indexed original hands you the
  quantisation. But it destroys the shaded relief and can distort small type.

**Recommended: a learned model trained on line art.** That content class — flat
regions, hard antialiased lines, limited palette — is the closest well-studied
analogue to cartographic artwork, and unlike the pixel-art scalers these handle
antialiased input natively. In order of interest:

1. **waifu2x (cunet)** — the most conservative, and the one measurement in the
   literature that bears directly on charts favours it: Real-ESRGAN was found to
   reduce **line continuity by 18–23% against waifu2x at 3x**. Continuity is what
   an airway, a boundary or a road *is*; a model that breaks thin lines is
   disqualifying regardless of how sharp the result looks.
2. **Real-CUGAN** — anime-trained with 2x/3x/4x and, usefully here, tunable
   enhancement strength (five weights at 2x). The right setting for this job is
   the weakest one that still cleans artifacts.
3. **APISR** (CVPR 2024) — current state of the art on this content class at only
   1.03M parameters, so cheap to evaluate.

**All three are trained on anime, not maps**, and two differences matter enough
to test before committing: charts carry **dense small type**, which anime does
not, so glyph deformation needs checking; and the **shaded relief** is continuous
tone that an illustration model may posterise into bands. Evaluate on a crop
holding type, hairlines and relief together, and measure rather than eyeball —
`scripts/upsample_test.py` already has the ringing and sharpness harness, and
wants a line-continuity check adding to it.

**The chart is not uniformly piecewise-constant**, and that is probably the most
useful thing to know before starting. The shaded relief is genuine continuous
tone, where lanczos is the *right* kernel; the linework, fills and type are
piecewise-constant, where it rings. The strongest approach is likely to segment
the two — the palette-indexed original is a natural source for that mask — and
resample each with what suits it.

**A cheap win independent of all this:** the tiling warp currently defaults to
`lanczos`, which measured worst for ringing. For the reprojection step, which
resamples at roughly 1:1, `cubic` halves the ringing at nearly the same
sharpness. Worth testing as the default.

### Tile the VFR sectional set

The wall planning chart is one sheet. The sectional series is ~50 sheets that
**overlap at their edges**, so this is a mosaicking problem rather than a bigger
version of the current one:

- Each sheet needs its own neatline crop first, or the printed margins land in
  the middle of the mosaic. `detect_neatline` in `build_vfr_tileset.py` already
  does this per sheet and should generalise, though the run-length threshold is
  tuned to this chart's furniture and will want re-checking.
- Sheets carry **different Lambert Conformal Conic parameters** — standard
  parallels chosen per sheet — so they cannot simply be stacked. They have to be
  warped to a common frame, which `gdal.Warp` will do into a VRT mosaic.
- Overlaps need a resolution order. GDAL's VRT mosaic takes the last-listed
  source, so sheet ordering becomes a deliberate choice rather than an accident.
- The combined pyramid will be far deeper: sectionals are 1:500,000 against the
  wall chart's much smaller scale, so expect a native zoom around z12–13 and tile
  counts in the hundreds of thousands.

`cesiumtiles` itself needs no change for this — it already accepts any
georeferenced raster, and a VRT mosaic is one. The work is in assembling the VRT.

### Automate fetching and building every current FAA chart

The FAA republishes on a **56-day cycle**, so this should be a scheduled job
rather than something run by hand:

- Fetch the current edition list, download the VFR and IFR products, and unpack
  the GeoTIFFs.
- Detect each sheet's neatline, upsample, mosaic where a series overlaps, and
  tile — the pipeline above, driven by a manifest rather than constants.
- Track edition dates so an unchanged chart is skipped instead of rebuilt.
- Plan for the storage: the full VFR sectional set alone is tens of GB of source
  before any tiling.

`scripts/build_vfr_tileset.py` is the single-chart case of this and is already
parameterised the right way; the generalisation is a manifest of charts plus a
download stage, with `--detect-neatline` doing the per-edition measurement so
new editions do not inherit stale constants.

### Generative upsampling

Learned super-resolution in place of the lanczos stage.

This is the strongest option for the artwork, and for a reason classical kernels
cannot match: a linear filter has no way to tell an artifact from signal. Scan
noise, ragged antialiasing on a one-pixel airway, the stair-stepping where a
diagonal boundary was rasterised — to `lanczos` these are all just data to be
interpolated, and it faithfully magnifies them. A model trained on flat-colour
line art has seen what a clean edge is supposed to look like and reconstructs
one, which is exactly the cleanup this source needs.

The hallucination worry that attaches to generative upscaling belongs to a
different regime than this one. At 2x or 4x each output pixel is tightly
conditioned on a small, well-defined source neighbourhood, leaving little room
to insert content that was not already there; and the text on this chart is
already legible at source resolution, so the model is sharpening glyphs rather
than reading and re-setting them. The risk of invented detail is real at large
upscale factors, or with a strongly generative prior asked to fill in what was
never sampled — neither describes doubling the resolution of a legible chart.

Ordinary quality control still applies, and costs nothing: keep the source tiles
alongside the upsampled ones so any pixel can be compared against what was
published. That is worth doing for *any* upsampling method, classical included,
not as a special precaution against models.

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
    viewer.html           the tile tester page (plain HTML - edit this)
    viewer.py             fills in its placeholders
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
