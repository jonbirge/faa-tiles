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

## Quick start

From a fresh clone, with Python 3.14 (Windows, Linux or macOS):

```bash
python scripts/setup_repo.py
```

That creates `.venv`, installs everything (including GDAL and CPU PyTorch from
their own package indexes) and checks the imports. Then build whichever
tilesets you want and open the tester:

```bash
.venv/Scripts/python scripts/build_sectionals.py      # VFR sectionals   ~7 min, ~2.1 GB (z11)
.venv/Scripts/python scripts/build_ifr_low.py         # IFR low enroute ~28 min, ~1.4 GB (z12, lossless)
.venv/Scripts/python scripts/build_wall_planning.py   # VFR wall planning chart (see below)
.venv/Scripts/cesiumtiles-serve .                     # http://127.0.0.1:8000/
```

(On Linux and macOS the venv interpreter is `.venv/bin/python`.)

Each wrapper runs its stages as separate scripts, in order: download, then any
preparation the series needs (the IFR charts are rendered from vector PDFs and
their frame seams healed), then build. The chart wrappers accept `--no-fetch`,
`--resume`, `--detect` (redo the reviewed manifests, which for the IFR charts
also downloads the GeoTIFFs they are derived from) and any
`build_chart_tileset.py` option. The wall planning
chart has **no automated download** — the FAA's "Planning Set" link was dead —
so put its files in `source/wall-planning/` by hand first; `--help` lists them.
Its wrapper then georeferences, crops to the neatline, upsamples 2x with
Real-CUGAN and tiles.

**Everything downloaded lives in `source/`**: chart GeoTIFFs, model weights,
third-party checkouts and the intermediates made from them, in one subfolder
each. Delete `source/` to reclaim all of it. Tilesets (`tileset-*`) stay at the
top level, where the tester finds them.

## Setup by hand

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
The **Source** menu lists every tileset the server can see: the served directory
itself if it holds a `metadata.json`, and each immediate subdirectory that does
(one level deep, not recursive). Picking one loads it. The server rescans on
every page load, so a tileset built while it runs appears after a reload.

Below a separator, **Connect to URL...** opens a dialog for anything else:

- a **tileset directory** URL, read through its `metadata.json`, so scheme,
  zooms, extent and size all come across automatically; or
- a raw **`{z}/{x}/{y}` URL template**, used as given, with the scheme and tile
  size taken from the dialog and a z0-18 range assumed.

A URL that loads is added to the menu for the rest of the session; one that
fails keeps the dialog open with the reason.

Swapping sources **leaves the camera where it is**, so two tilesets can be
compared at a fixed viewpoint — flip between `./tileset` and `./tileset-lossy`
and only the imagery changes. If the new tileset does not cover where you are
looking, the panel says so and **Fly to extent** takes you there.

To compare local tilesets, serve their common parent:
`.venv/Scripts/cesiumtiles-serve .`. The server finds the tilesets beneath it,
opens the first, and lists the rest in the menu. The tester is always at `/`,
whichever directory you serve.

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
only failed requests rather than every one of thousands of tiles. It also
answers `/tilesets.json` with the tilesets it found, which is what fills the
tester's menu; on any other server the menu falls back to the tileset the page
opened with.

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
| `--resampling` / `--overview-resampling` | GDAL kernels for the warp and the overview cascade; `cubic` and `lanczos` by default. |
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

### Upsample the source before tiling — *done*

> Implemented: `build_vfr_tileset.py` stage 3 upsamples 2x with Real-CUGAN,
> raising the native zoom to z10. `--no-upsample` skips it. What follows is the
> reasoning, kept because it is the argument for the choice.

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

**A cheap win independent of all this — *done*:** the tiling warp defaulted to
`lanczos`, which measured worst for ringing. For the reprojection step, which
resamples at roughly 1:1, `cubic` halves the ringing at nearly the same
sharpness, so every pipeline now warps with `cubic` (single-chart tiling, the
chart-series mosaic, and the wall planning build).

### Tile the VFR sectional set — *done*

The sectional series is 55 sheets that overlap at their edges, each in its own
Lambert Conformal Conic, each inside a printed collar. Three scripts build it:

```bash
.venv/Scripts/python scripts/fetch_charts.py sectionals          # current edition -> source/sectionals
.venv/Scripts/python scripts/detect_sectional_areas.py --sheet review/
.venv/Scripts/python scripts/build_chart_tileset.py sectionals   # -> ./tileset-sectionals
```

- **Fetching** picks the newest edition directory that is not in the future
  (the FAA posts the next one early) and runs `WORKERS` downloaders at once.
  Each series in `scripts/chart_series.py` says which zips and GeoTIFFs it
  wants; anything else is not extracted, and the build skips it too. The
  sectional series excludes the Guam (Mariana Islands) and American Samoa
  insets, which ship in `Hawaiian_Islands.zip` alongside sheets we keep.
- **Map areas** live in `scripts/sectionals_areas.json`, one pixel polygon per
  sheet. They are detected (walk in from each edge until the paper collar
  ends, fit a line or arc, move inward past the worst reading) and then
  reviewed; the script prints how much paper is left just inside each edge and
  writes contact sheets with every outline drawn. Enlarged insets printed over
  the map are hand-authored `exclude` boxes. Three sheets are hand-traced: the
  two that are not a map in a collar (Hawaiian Islands, Honolulu), and Los
  Angeles, whose legend panel and LA Basin inset leave an L-shaped map area that
  a fitted edge cuts short.
  Rerun and review for each edition.
- **The mosaic** is `cesiumtiles.mosaic`, not `gdal raster tile`: every z12
  tile warps just the sheets that reach it, with each sheet's map area burnt
  into a mask the warp reads as alpha, and composites them. Lower zooms are
  box-filtered from their children, a level at a time, fully parallel. Sheets
  crossing 180 degrees are handled.
- **Choices:** max zoom z12 (only the 1:250k Honolulu inset would use z13, at 4x
  the tiles), WebP q90, and overlaps resolved by file name — later on top.

Still open:

- **Overlap order is a placeholder.** It already shows: the FAA's Phoenix
  GeoTIFF has a blank white row running through its map near 35.6 N, and
  Phoenix sorts after Las Vegas, so it is drawn on top of good Las Vegas map.
  Preferring the sheet whose own map area is further from its edge would fix
  this and most seam artefacts generally.
- **Empty ocean returns 404s.** Tiles are only written where a sheet has map,
  so Cesium requests (and fails) tiles over the gaps inside the extent. The
  tester no longer warns about these, but the requests still happen.
- **No upsampling** yet; the wall chart's Real-CUGAN stage is not in this path.

### Tile the IFR low enroute set — *done*

The CONUS low enroute charts, L-01 to L-36, build the same way:

```bash
.venv/Scripts/python scripts/fetch_charts.py ifr-low          # -> source/ifr-low/pdf
.venv/Scripts/python scripts/render_pdfs.py ifr-low           # -> source/ifr-low/rendered
.venv/Scripts/python scripts/heal_frames.py ifr-low           # -> source/ifr-low/healed
.venv/Scripts/python scripts/build_chart_tileset.py ifr-low   # -> ./tileset-ifr-low
```

- **Scope:** only `ENR_L01`-`ENR_L36`. Alaska, Pacific and area charts are left
  out, and so are the inset TIFFs some zips carry. L-06 is published as two
  halves, `ENR_L06N` and `ENR_L06S`, so the series has 37 sheets.
- **The sheets are drawn from the FAA's vector PDFs, not its GeoTIFFs.** The
  published GeoTIFFs are badly rasterised — every edge staircases, and no
  amount of super-resolution recovers what the rasteriser threw away. The same
  charts are also published as true vector PDFs, which `render_pdfs.py` draws
  at 2x the GeoTIFF's 400 dpi. That is *rendering*, not upsampling: each pixel
  comes from the vector geometry, so type and line work antialias properly.
  A sheet takes about 35 s, and all 37 render in 6.4 minutes on 6 workers.
  **Rendering is done in 8192 px blocks**, not whole sheets: pdfium stops
  drawing past ~32767 px without any error, and a 48000 px sheet silently loses
  its right third (see CLAUDE.md).
- **The PDFs are not georeferenced** — their own metadata says so, offering
  only four bounding corners. So `detect_pdf_windows.py` registers each
  GeoTIFF against its PDF once per edition and commits the result as
  `scripts/ifr_low_pdf.json`: the affine, the CRS, and which box of which page
  the sheet is. `ENR_L06.pdf` is a single page holding both panels that ship as
  `ENR_L06N` and `ENR_L06S`, which is why a window is recorded rather than
  assumed. After that only the PDFs are downloaded (~130 MB against 386 MB of
  GeoTIFFs); `build_ifr_low.py --detect` fetches the GeoTIFFs and re-derives
  both manifests, which is the only thing they are still needed for.
- **Map areas are found differently.** An IFR chart's map is mostly white, so
  the sectional detector's "walk in until the paper ends" has nothing to find.
  Instead every sheet frames its map with a heavy black rule, 6-10 px, while
  legend tables use 1-5 px rules; the map is the rectangle just inside the
  thick rules on each axis. Where a sheet frames a second panel beside the map
  (L-23's Wilmington-Bimini inset strip), the widest panel is the map and the
  other is reported and dropped.
- **Seams are healed, not cropped.** Neighbouring IFR charts do not overlap:
  they meet at their frame rules, and under a rule neither sheet has map.
  Cropping inside the rules left a 1-3 km dark gap along every shared edge.
  Instead the map area runs to each rule's outer edge, and `heal_frames.py`
  writes a copy of each sheet with the rule painted over by repeating the
  nearest clean row or column outward (~12 px, ~0.5-1 km per side), which the
  build tiles. That closed 31 of 32 seams; L-29/L-30 still has a straight
  ~450 m sliver where the FAA's two georeferenced sheets simply do not meet.
- **Same engine** as the sectionals, at **z12** and **lossless WebP**: IFR
  charts are thin linework and small type on white, which lossy q90 softens.
  The 2x renders reach z13 natively; z12 is where the current build stops.
  `build_chart_tileset.py --[no-]lossless` overrides a series' default. Overlaps are
  painted in *reverse* file-name order, so the lower-numbered chart is on top;
  `build_chart_tileset.py --[no-]reverse-order` overrides a series' default.

### Automate fetching and building every current FAA chart

The FAA republishes on a **56-day cycle**, so this should be a scheduled job
rather than something run by hand:

- Fetch the current edition list, download the VFR and IFR products, and unpack
  the GeoTIFFs (or the vector PDFs, for the IFR charts). *Done for sectionals
  and IFR low* (`scripts/fetch_charts.py`). The reviewed manifests are tied to
  an edition, so a scheduled job has to re-detect and someone has to look.
- Detect each sheet's neatline, upsample, mosaic where a series overlaps, and
  tile — the pipeline above, driven by a manifest rather than constants.
- Track edition dates so an unchanged chart is skipped instead of rebuilt.
- Plan for the storage: the full VFR sectional set alone is tens of GB of source
  before any tiling.

`scripts/build_vfr_tileset.py` is the single-chart case of this and is already
parameterised the right way; the generalisation is a manifest of charts plus a
download stage, with `--detect-neatline` doing the per-edition measurement so
new editions do not inherit stale constants.

### Try a transformer upsampler

Real-CUGAN won the first round, but it is a small CNN — 1.28 M parameters, 26
convolutions, a receptive field of a few tens of pixels. The obvious next step is
a model that can see further along a line before deciding what it is.

**Attention-based architectures are the interesting tier**, and they are already
drop-in: **15 of the 42 architectures `spandrel` recognises are attention-based**,
and `scripts/upsample.py` loads any of them unchanged. Trying one is
`--model path/to/weights.pth`, nothing else. Worth a look, roughly in order:

| model | why |
| --- | --- |
| **DAT** (Dual Aggregation Transformer) | Aggregates across both spatial and channel dimensions; strong 2x results and several line-art-tuned weights exist. |
| **HAT** (Hybrid Attention Transformer) | Combines channel attention with window self-attention, which activates more input pixels than SwinIR. Big, but this is a batch job. |
| **ATD** (Adaptive Token Dictionary, CVPR 2024) | Learns a token dictionary rather than attending over a fixed window; good quality per parameter. |
| **DRCT** | Addresses the information bottleneck that limits SwinIR-style networks; a strong recent baseline. |
| **SwinIR** / **Swin2SR** | The reference transformer SR. Not the strongest any more, but the most line-art-tuned weights exist for it, so it is the easiest honest comparison. |
| **SeemoRe**, **MoESR**, **SPAN**, **OmniSR**, **PLKSR** | Efficiency-oriented. Include them: the first round was won by the *smallest* model tried, so more capacity is not obviously the answer. |

All are a **single deterministic forward pass**, like the CNNs — same input, same
output, reproducible tiles. Weights tuned for illustration and line art (rather
than the usual DIV2K natural-image training) are on
[OpenModelDB](https://openmodeldb.info); a model trained on photographs will
reach for texture this artwork does not have.

**What to measure.** `scripts/upsample_test.py` has the ringing and sharpness
harness. Two more signals proved useful in the first round and are worth
formalising: **line continuity** on thin airways and boundaries, which is the
property that separates these models on line art and the one that disqualifies a
model outright; and **lossless WebP size as a proxy for local complexity** — with
tile count held constant, APISR's output was 30% larger than Real-CUGAN's, which
correctly predicted it was synthesising more high-frequency content than the
source justified.

### Diffusion upsamplers — probably the wrong tool

**StableSR**, **SeeSR**, **SUPIR**, **DiffBIR**, and the one-step distillations
(**OSEDiff**, **ResShift**, **CCSR**, **AdcSR**) are the genuinely generative
tier, and two things argue against them here.

They **sample**, so they are not reproducible: the literature reports noticeable
instability across noise samples for StableSR, PASD, SeeSR, SUPIR and AddSR, with
CCSR existing specifically to address it. Tiles that differ run to run are a poor
fit for a chart, and it is also the regime where the worry about invented detail
actually bites — unlike a deterministic 2x convolution, where it does not.

And their advantage is inventing plausible *texture*: skin, foliage, fabric. A
chart has no texture to invent, only flat fills, hard edges and type. The first
round already hinted at this — the winner was the smallest model, and the one
that synthesised most lost.

Worth revisiting only if a transformer plateaus and the remaining gap is clearly
reconstruction rather than invention.

## Tests

```bash
.venv/Scripts/python -m pytest
```

145 tests, all against small synthetic rasters built in a temp directory — none
need the chart files. The tile arithmetic in `cesiumtiles.scheme` is checked
against [mercantile](https://github.com/mapbox/mercantile), a separate
implementation of the same grid, so agreement is evidence rather than tautology.

## Layout

```
pyproject.toml            packaging + pytest config
requirements.txt          runtime deps (incl. the GDAL wheel index)
requirements-dev.txt      runtime + test deps
scripts/
    setup_repo.py         fresh clone -> working venv
    build_sectionals.py   wrappers: download + build one product each
    build_ifr_low.py
    build_wall_planning.py
    pipeline.py           what the wrappers share: run stages in order
    layout.py             where everything lives (source/, models, ...)
    chart_series.py       each FAA chart series, described once
    fetch_charts.py       download a series' current edition (+ fetch_chart.py worker)
    detect_*_areas.py     find each sheet's map area -> *_areas.json (reviewed, committed)
    build_chart_tileset.py  mosaic a series into tiles
    build_vfr_tileset.py  the wall planning chart pipeline
    upsample.py           2x super-resolution
source/                   every download and intermediate (gitignored)
src/geotransfer/
    core.py               copy_geo_metadata / read_georeference
    cli.py
src/cesiumtiles/
    scheme.py             XYZ grid maths for both tiling schemes
    core.py               build_tileset
    mosaic.py             build_mosaic: many overlapping sheets, masked
    viewer.html           the tile tester page (plain HTML - edit this)
    viewer.py             fills in its placeholders
    serve.py              local preview server (CORS, tile MIME types)
    cli.py
tests/
    test_core.py          georeferencing transfer
    test_scheme.py        tile maths vs mercantile
    test_tiles.py         end-to-end tileset builds
    test_mosaic.py        mosaics: overlap order, masks, antimeridian
    test_serve.py         preview server behaviour
.claude/
    launch.json           dev-server definitions for the browser pane
CLAUDE.md                 orientation notes for Claude Code
```
