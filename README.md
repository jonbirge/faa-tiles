# faa-tiles

Turn the FAA's published aeronautical charts into static `z/x/y` tile pyramids
you can drape on a Cesium globe, plus the tooling to keep them current.

Four tilesets are built here today. Each is a different product, and each is
built by one command:

| Tileset | Chart | Sheets | Zooms | Tiles | Size |
| --- | --- | --- | --- | --- | --- |
| `tileset-sectionals` | VFR sectionals | 55 | z0–z12 | 508,529 | 5.30 GB |
| `tileset-sectionals-tac` | the same, with terminal area charts over them | 55 + 34 | z0–z12 + sparse z13 | — | — |
| `tileset-ifr-low` | IFR enroute low, CONUS | 37 | z0–z13 | 953,205 | 3.05 GB |
| `tileset-planning` | U.S. VFR wall planning chart | 1 | z0–z11 | 98,014 | 441 MB |

Underneath are two installable packages:

| Package | Job |
| --- | --- |
| `cesiumtiles` | Cut a GeoTIFF into a tile pyramid; mosaic a whole chart series into one; serve and test the result |
| `geotransfer` | Copy CRS and transform from one GeoTIFF onto a plain TIFF of identical size |

---

## Quick start

From a fresh clone, with Python 3.14 (Windows, Linux or macOS):

```bash
python scripts/setup_repo.py
```

That creates `.venv`, installs everything — including GDAL and PyTorch, which
come from their own package indexes — checks the imports load, and makes
`source/`. Then build whichever products you want and open the tester:

```bash
.venv/Scripts/python scripts/build_sectionals.py       # VFR sectionals            z12
.venv/Scripts/python scripts/build_sectionals_tac.py   # + terminal area charts    z12 + z13 detail
.venv/Scripts/python scripts/build_ifr_low.py          # IFR enroute low           z13, lossless
.venv/Scripts/python scripts/build_wall_planning.py    # VFR wall planning chart   z11
.venv/Scripts/cesiumtiles-serve .                      # http://127.0.0.1:8000/
```

On Linux and macOS the venv interpreter is `.venv/bin/python`.

**Budget disk and time first.** These are big jobs, and most of the cost is in
preparing the sheets rather than in tiling them. Measured on an i7-14700KF with
an RTX 4070 SUPER, writing to a local SSD:

| Product | Download | Intermediates | Prepare | Tile |
| --- | --- | --- | --- | --- |
| sectionals | 3.2 GB | ~48 GB upsampled | 52 min (GPU) | 26 min |
| sectionals + TACs | + 678 MB | + ~12 GB | ~+15 min | ~35–50 min |
| IFR low | 130 MB of PDFs | 5.2 GB rendered + healed | ~100 min | 31 min |
| wall planning | manual drop-in | ~2 GB | 1 min (GPU) | 3 min |

Without an NVIDIA GPU the upsampling stages run on the CPU at about 1/35 the
speed — hours rather than minutes. The IFR product does not upsample at all, so
it is GPU-free.

Every download and every intermediate lives under `source/`, so deleting that
one directory reclaims all of it. Tilesets are written at the top level.

---

## How a chart series is built

A "series" is one FAA product: the sectionals, the terminal area charts, the
IFR low enroute charts. `scripts/chart_series.py` describes each one in a single
place — where it is published, which zips and files to keep, what preparation it
needs, how deep to tile it — and every stage looks the series up there. Adding a
product means adding a `Series`, not copying scripts.

```
fetch_charts.py  ->  detect_*_areas.py  ->  (prepare)  ->  build_chart_tileset.py
   source/NAME       scripts/NAME_areas.json              tileset-NAME
```

**1. Fetch.** `fetch_charts.py SERIES` lists the product's index, picks the
current edition — the newest `MM-DD-YYYY` directory *that is not in the future*,
because the FAA posts the next edition early — and runs a team of downloaders
over that edition's zips. Only the files the series wants are extracted; a TAC
zip, for instance, also carries that city's Flyway Planning chart and sometimes
an airspace graphic, none of which are map.

**2. Find each sheet's map area.** A published chart is a map inside furniture:
a paper collar with a legend panel and notes, or a drawn frame with grid ticks
outside it. Georeferenced along with the map, that furniture would land on the
globe as if it were terrain. Each sheet's map area is detected once per edition
into `scripts/<series>_areas.json`, **reviewed by a human, and committed** — so
a routine build does not re-detect, and `--detect` is an explicit request.

The area is a pixel polygon, not a lon/lat rectangle: insets printed over the
map, tilted island sheets and Alaskan legend panels are none of them
rectangular in any geographic frame. It becomes a mask the warp reads as alpha.

Two detectors, because the two kinds of sheet are different problems:

- `detect_sectional_areas.py` (sectionals, TACs) walks in from each image edge
  until the paper collar ends, fits a line to the west and east edges and a
  quadratic to the north and south — meridians are straight in a conic
  projection, parallels bow — then moves the fit inward past its worst reading.
- `detect_ifr_areas.py` (IFR) measures the heavy frame rule instead. An IFR
  chart's map is mostly white paper, so there is no collar edge to find; what
  there is, is a 6–10 px black rule around the map where legend tables use 1–5 px
  ones.

Both write contact sheets with every outline drawn (`--sheet DIR`), and both
print a per-edge paper check. Trust the numbers over the thumbnails: a clean
contact sheet once hid leftover collar on 49 of 57 sheets.

**3. Prepare.** Optional stages, each writing a directory the next one reads:

- `render_pdfs.py` — for a series published as true vector PDFs, draw the sheets
  from the vector geometry instead of tiling the FAA's rasters. This is
  rendering, not upsampling: every pixel comes from the drawing.
- `upsample_charts.py` — for a series with no vector source, super-resolve each
  sheet 2x with Real-CUGAN.
- `heal_frames.py` — for sheets that abut rather than overlap, paint over the
  frame rule so neighbours join without a seam.

**4. Mosaic.** `build_chart_tileset.py SERIES` warps every sheet into one
pyramid. It does not use `gdal raster tile`: each max-zoom tile warps only the
sheets that actually reach it, compositing front-to-back so it stops as soon as
the tile is opaque, and the lower zooms are box-filtered from their children a
level at a time. Measured at 388 tiles/s at z12, 14 KB a tile. (Warping the low
zooms from the sheets instead was tried: a z8 tile reads a 16x source window and
managed 13 tiles/s.)

The `build_*.py` wrappers at the top of `scripts/` just run these stages in
order for one product, so what a wrapper does is exactly what you would get
typing the stages by hand. They take `--no-fetch`, `--detect` and `--resume`,
and pass anything else through to `build_chart_tileset.py`.

### Options worth knowing

| Option | Meaning |
| --- | --- |
| `--max-zoom N` | Override the series' depth. |
| `--detail-zoom N` / `--no-detail` | The sparse extra level (see the composite below). |
| `--[no-]lossless` | Override the series' WebP mode; lossy quality is `--quality`. |
| `--warp cpu\|gpu` | Which backend resamples the max-zoom tiles. Default `cpu`. |
| `--resampling` | Warp kernel, default `cubic`. |
| `--warp-tolerance PIXELS` | Let the warp approximate the projection, like `gdalwarp -et`. Default 0, exact. |
| `--[no-]reverse-order` | Paint order where sheets overlap. |
| `--only NAME ...` | Build from a few sheets, by file-name prefix. |
| `--resume` / `--overwrite` | Keep existing tiles, or replace the tileset. |

---

## The four products

### VFR sectionals — `tileset-sectionals`

55 sheets covering the U.S. including Alaska, Hawaii and the Aleutians, each in
its own Lambert Conformal Conic, overlapping its neighbours at the edges.

```bash
.venv/Scripts/python scripts/build_sectionals.py
```

- **Upsampled 2x with Real-CUGAN** (denoise3x weights) before tiling. The FAA's
  sectional rasters staircase at any zoom and, unlike the IFR charts, there is
  no vector source to fall back on — the sectional PDFs wrap the very same
  rasters. Whole sheets are upsampled rather than just their map areas, so the
  reviewed manifests differ from the raster by a scale and no offset. This is
  the expensive stage: ~900 MB per sheet, ~48 GB in total, 52 min on the GPU.
- **z12, WebP q90.** The median lower-48 sheet is 42.3 m/px, native z11.5, so
  the 2x upsample reaches z12.5 and a z12 tile still minifies. z13 would be 1.4x
  finer than even the upsampled sheets, for 4x the tiles.
- **Guam and American Samoa are excluded**, by choice. Both inset GeoTIFFs ship
  inside `Hawaiian_Islands.zip` alongside sheets that are kept, so the exclusion
  is per file, not per zip.
- **Three sheets are hand-traced:** Hawaiian Islands and Honolulu, which are not
  a map in a collar at all, and Los Angeles, whose legend panel and LA Basin
  inset leave an L-shaped map area that any fitted edge cuts short.
- 508,529 tiles / 5.30 GB, built 2026-09-18.

### Sectionals with terminal area charts — `tileset-sectionals-tac`

The same mosaic with each **VFR Terminal Area Chart** laid over it where one is
published: 34 sheets from 30 zips, because Anchorage/Fairbanks,
Denver/Colorado Springs, Seattle/Portland and Tampa/Orlando each ship two.

```bash
.venv/Scripts/python scripts/build_sectionals_tac.py
```

- **A composite is layers, not a copy.** `sectionals-tac` owns no sheets: it
  names the `sectionals` and `tac` series and the order they paint in. Each
  layer keeps its own downloads, its own preparation stages and its own reviewed
  manifest, so building the composite after `tileset-sectionals` costs only the
  TACs. Paint order runs layer by layer — every sectional is below every TAC,
  whatever the file names — which is what "inserted where available" means.
- **The TACs get the same 2x Real-CUGAN pass**, with the same weights, so the
  two layers meet on equal terms where one is drawn over the other.
- **z12, plus a sparse z13 detail level.** A TAC is 1:250,000 at 300 dpi —
  21.17 m/px, exactly half the sectionals' pitch — so it holds one more level
  than the sheets around it. Tiling the whole mosaic at z13 would quadruple it
  (~2 M tiles, ~21 GB) to magnify the 96% that is sectional. Instead the pyramid
  stops at z12 and one extra level holds **only the tiles a TAC reaches** — tens
  of thousands, against half a million below. Cesium falls back to the stretched
  z12 parent everywhere that level is absent, exactly as it already does over
  ocean.
- Every source paints into a kept detail tile, not just the TACs, so a TAC's
  edge sits on magnified sectional rather than on a hard transparent boundary a
  tile wide. The detail level feeds nothing below it: the overview cascade still
  starts at z12, and `metadata.json` carries `fullzoom` beside `maxzoom` to say
  where full coverage stops.
- `--no-detail` builds a plain uniform pyramid instead; `--detail-zoom N` moves
  the level.

### IFR enroute low — `tileset-ifr-low`

The CONUS low enroute charts, L-01 to L-36. Alaska, Pacific and area charts are
out of scope, and so are the inset TIFFs some zips carry. L-06 is published as
two halves, `ENR_L06N` and `ENR_L06S`, which makes 37 sheets.

```bash
.venv/Scripts/python scripts/build_ifr_low.py
```

- **Drawn from the FAA's vector PDFs, not its GeoTIFFs.** The published GeoTIFFs
  are badly rasterised — every edge staircases, and no amount of super-resolution
  recovers what the rasteriser threw away. The same charts ship as true vector
  PDFs, which `render_pdfs.py` draws at 4x the GeoTIFF's 400 dpi. Each pixel
  comes from the vector geometry, so type and line work antialias properly.
  About 160 s a sheet, 5.2 GB of renders.
  Rendering runs in 8192 px blocks: pdfium silently stops drawing past ~32767 px,
  and a 48000 px sheet loses its right third with no error of any kind.
- **The PDFs carry no georeferencing** — their own metadata says so, offering
  only four bounding corners. `detect_pdf_windows.py` registers each GeoTIFF
  against its PDF once per edition and commits the affine, CRS and page window
  as `scripts/ifr_low_pdf.json`. `ENR_L06.pdf` is a single page holding both
  panels, which is why a *window* is recorded rather than the page assumed.
  After that only the PDFs are downloaded (130 MB against 386 MB of GeoTIFFs);
  `build_ifr_low.py --detect` fetches the GeoTIFFs and re-derives both
  manifests, which is the only thing they are still needed for.
- **Seams are healed, not cropped.** Neighbouring IFR charts do not overlap:
  they meet at their frame rules, and under a rule neither sheet has map.
  Cropping inside the rules left a 1–3 km dark gap along every shared edge.
  Instead each map area runs to its rule's outer edge and `heal_frames.py`
  writes a copy of the sheet with the rule painted over by repeating the nearest
  clean row or column outward — ~12 px, roughly 0.5–1 km, each sheet filling its
  own half. That closed 31 of 32 seams; L-29/L-30 keeps a straight ~450 m sliver
  where the FAA's two georeferenced sheets simply do not meet.
- **z13, lossless WebP.** IFR charts are thin linework and small type on white,
  which lossy compression softens. The 4x renders resolve past z14, so z13 tiles
  are genuine vector detail.
- Overlaps paint in *reverse* file-name order, so the lower-numbered chart is on
  top.
- 953,205 tiles / 3.05 GB, tiled in 31 min at 608 tiles/s.

### U.S. VFR wall planning chart — `tileset-planning`

The single-sheet case, and the worked example of the library.

```bash
.venv/Scripts/python scripts/build_wall_planning.py
```

**There is no automated download.** The FAA product page's "Planning Set" link
(`visual/<edition>/All_Files/Planning.zip`) returns 404 for every edition, so
the source files are dropped into `source/wall-planning/` by hand. The wrapper
checks for them and says what it needs: either the already-georeferenced chart,
or the FAA's palette-indexed GeoTIFF (which carries the georeferencing) plus a
full-colour RGB render of the same sheet at the same pixel size (which has the
better pixels and no geo metadata). `geotransfer` marries those two.

Then `build_vfr_tileset.py` crops to the neatline, upsamples 2x with Real-CUGAN
and tiles to z11 — 98,014 tiles / 441 MB in 3.2 min. Useful variants:

```bash
scripts/build_vfr_tileset.py --dry-run                     # plan without writing tiles
scripts/build_vfr_tileset.py --no-upsample                 # tile at the native z9
scripts/build_vfr_tileset.py --max-zoom 7 --out tileset-draft
scripts/build_vfr_tileset.py --detect-neatline             # re-measure for a new edition
```

**Trimming to the neatline** is worth understanding, because it is what
`cesiumtiles --bbox-crs source` exists for. A printed sheet carries a white
margin, a heavy border and a "Nautical Miles" scale bar, all georeferenced. The
crop has to be expressed in the chart's own Lambert Conformal Conic, because a
neatline is a rectangle *there* and not in lon/lat — this sheet's corners differ
by 8.3° of longitude between NW and SW, so a lon/lat box leaves white wedges.
And it has to be **inscribed** in the map rather than circumscribed about it:
the neatline is not square to the pixel grid (its top edge runs from row 272 on
the left to row 200 on the right), so any box containing the whole map also
contains slices of border and paper. `--detect-neatline` re-measures it from the
image: a chromatic bounding box first, since margins are white and only the map
is coloured, then each edge shrunk until it holds no run of paper-white or
neatline-black longer than 150 px, map ink being broken up at that scale.

---

## The tile tester

`cesiumtiles-serve` renders a Cesium viewer at `/` and serves the tilesets
beneath the directory you point it at. A tileset on disk is **data only** —
`tiles/` and `metadata.json`, no HTML — so one tester can sit above several and
switch between them.

```bash
.venv/Scripts/cesiumtiles-serve .          # find every tileset below the cwd
.venv/Scripts/cesiumtiles-serve tileset-ifr-low
```

Open <http://127.0.0.1:8000/>. It uses no Cesium Ion token: our tiles are the
base layer and terrain is the plain ellipsoid. The page reads `metadata.json` at
runtime, so re-tiling needs no change to the HTML, and it exposes
`window.viewer` and `window.tileTracker` for the dev console.

| Option | Meaning |
| --- | --- |
| `-p`, `--port N` | Port to listen on (default 8000). |
| `--host ADDR` | Bind address; default `127.0.0.1`, use `0.0.0.0` for the LAN. |
| `--no-cors` | Omit `Access-Control-Allow-Origin`. |
| `--open` | Open the viewer once the server is up. |

A preview server is included at all because `python -m http.server` sends no
CORS headers, which blocks the tiles the moment a Cesium app on another origin
tries to read them. This one also sends correct MIME types, `no-cache` for
`metadata.json`, and logs only failed requests rather than every one of a
million tiles. It answers `/tilesets.json` with what it found, which is what
fills the tester's Source menu.

### Choosing a source

The **Source** control is a menu. It lists the tilesets the server can see — the
served directory itself if it holds a `metadata.json`, and each immediate
subdirectory that does — then any URLs connected this session, then **Connect to
URL...**, which opens a dialog for anything else:

- a **tileset directory** URL, read through its `metadata.json`, so scheme,
  zooms, extent and tile size all come across; or
- a raw **`{z}/{x}/{y}` template**, used as given, with the scheme and tile size
  taken from the dialog.

A URL that loads joins the menu for the session; one that fails keeps the dialog
open with the reason, and leaves the current tileset in place.

**Switching sources leaves the camera where it is**, so two tilesets can be
compared at a fixed viewpoint — flip between them and only the imagery changes.
If the new tileset does not cover where you are looking, the panel says so and
**Fly to extent** takes you there.

A remote server must allow cross-origin requests. If it also omits
`Timing-Allow-Origin` the browser withholds transfer sizes, and the panel
reports network bytes as `n/a (cross-origin)` rather than pretending they are
zero; tile counts still work.

### Diagnostics

- **On screen** — imagery tiles the globe is drawing, by zoom level, with the
  x/y range at each, how many are still loading, and the camera altitude.
- **Downloaded** — tiles fetched, bytes over the wire, average tile size, tiles
  served from cache, and the most recent tile requested. Traffic is read from
  Resource Timing rather than by patching Cesium.

**Reset counters & cache** zeroes the counters *and* forces the next load to be
genuinely cold. Script cannot clear the browser's HTTP cache, so it rebuilds the
imagery layer against a fresh query string, which misses both Cesium's in-memory
cache and the browser's. Without that, pressing reset and flying around would
replay local copies and report almost no traffic. (Measured: a warm load reports
0 downloaded / 37 cached / 10.8 KB; after a reset, 34 downloaded / 0 cached /
2.51 MB.)

A cache hit is not simply "zero bytes transferred" — browsers may report a fixed
~300-byte header placeholder with a full body size and a 200 status. The panel
classifies by whether `transferSize` is smaller than `encodedBodySize`, which is
what actually indicates the body never crossed the wire.

**Show tile grid** overlays each tile's boundary, coloured by level on a
continuous deep-blue-to-almost-red ramp computed from `level / maxzoom`, so
pointing the tester at a shallower or deeper source re-scales it rather than
running off the end of a fixed list. The swatches beside the levels in *On
screen* name them outright, so identity never rests on the colour. The overlay
is drawn on canvas rather than fetched, so it does not disturb the counters.

### Rendering controls

These matter when comparing tilesets, because two of Cesium's defaults flatter
or penalise them misleadingly:

| control | what it does |
| --- | --- |
| `max SSE` | `globe.maximumScreenSpaceError`, default **2**. How aggressively the globe refines; 1 roughly doubles the tiles on screen. |
| `scale` | Cesium defaults `useBrowserRecommendedResolution` to true, which **ignores the display's pixel ratio**: on a 1.5x screen the globe renders at two thirds of the panel's sharpness. This turns that off and sets `resolutionScale`; above 1 it supersamples. |
| `magnify` | Texture magnification past the deepest zoom. Cesium's default is `LINEAR`, so every tile is bilinearly smeared once you pass max zoom — which reads as the *tileset* being soft when it is not. `nearest` keeps pixels honest. |
| `MSAA` | `scene.msaaSamples`, default none here. Affects geometry edges, including the globe silhouette, more than imagery. |

When judging an upsampler, set `magnify` to `nearest` and `scale` to your
display's pixel ratio first — otherwise you are partly grading Cesium's bilinear
filter.

---

## `cesiumtiles` — single-raster tilesets

For one georeferenced raster, as opposed to a series:

```bash
.venv/Scripts/cesiumtiles chart.tif ./tileset
.venv/Scripts/cesiumtiles chart.tif ./colorado --bbox -109.06 36.99 -102.04 41.00
.venv/Scripts/cesiumtiles chart.tif ./small --format webp --lossy --quality 95
```

```python
from cesiumtiles import build_tileset

result = build_tileset("chart.tif", "./tileset")
print(result.summary())
```

Output layout:

```
tileset/
  tiles/{z}/{x}/{y}.webp    the pyramid
  metadata.json             bounds, zooms, counts, url template
```

Tiling is delegated to GDAL's `gdal raster tile`, which since GDAL 3.11 is the
maintained reference implementation (`gdal2tiles` is deprecated in favour of it
from 3.13). This package supplies what that algorithm does not: geographic bbox
cropping, zoom defaults derived from the source resolution, and Cesium metadata
and a viewer — GDAL emits Leaflet, OpenLayers, MapML and STAC front ends, but
not Cesium. Counts and bounds are read back off disk after the run rather than
assumed from the request.

| Option | Meaning |
| --- | --- |
| `--bbox W S E N` | Crop before tiling. Applied as a warp cutline, so it is pixel-exact rather than snapped to tile edges. |
| `--bbox-crs CRS` | The frame those numbers are in; `source` means the raster's own CRS, which is what a neatline is rectangular in. |
| `--scheme mercator\|geographic` | `mercator` (default) is EPSG:3857 WebMercatorQuad, the standard slippy grid and zero-config for Cesium's `UrlTemplateImageryProvider`. `geographic` is EPSG:4326 WorldCRS84Quad. |
| `--min-zoom` / `--max-zoom` | Override the automatic range. |
| `--format webp\|png\|jpeg` | Default `webp`. |
| `--lossy` / `--quality N` | Lossy WebP, roughly 4x smaller, but it can ring around hairline linework and type. |
| `--resampling` / `--overview-resampling` | GDAL kernels for the warp and the overview cascade; `cubic` and `lanczos`. |
| `--skip-blank` | Omit fully transparent tiles. Smaller, but the viewer will generate 404s. |
| `--threads` | Worker count, or `ALL_CPUS` (default). |
| `--resume` / `-f`, `--overwrite` | Write only missing tiles; replace a non-empty directory. |
| `--title` / `-q`, `--quiet` | Name recorded in metadata; suppress the progress bar. |

**Zoom defaults.** `--max-zoom` lands where tile pixels match the source's own
resolution, so no detail is discarded and none invented; `--min-zoom` is 0, so
Cesium always has a complete pyramid to descend. Every tile in the covered
rectangle is written, including the fully transparent ones along a conic
projection's curved edges — blank tiles cost almost nothing and keeping them
means Cesium never requests a URL that 404s.

**Reported bounds** in `metadata.json` snap outward to whole tiles, because that
is the tile coverage; `data_bounds` holds the true unsnapped extent, and is what
an imagery rectangle must be given.

### Format sizes

Measured on real chart tiles, extrapolated to a 7,190-tile pyramid of the wall
planning chart:

| Format | KB/tile | Full tileset |
| --- | --- | --- |
| PNG | 66.4 | ~370 MB |
| WebP lossless (default) | 49.9 | **285 MB** |
| WebP q95 | 11.4 | ~64 MB |
| WebP q90 | 8.6 | ~48 MB |

Lossless is the default for single rasters, and the IFR series; the sectionals
and TACs use q90, reviewed on the real charts.

---

## `geotransfer` — georeferencing transfer

```bash
.venv/Scripts/geotransfer reference.tif image.tif out.tif
```

```python
from geotransfer import copy_geo_metadata

copy_geo_metadata(
    "vfr_geotiff_original.tif",   # has the CRS + transform
    "vfr_wall_planning.tif",      # has the pixels
    "vfr_wall_planning_geo.tif",  # gets both
)
```

The image file is duplicated byte for byte and only the GeoTIFF header tags are
rewritten. Nothing is decoded, resampled or recompressed, so band count, colour
interpretation, compression and predictor all survive exactly — a 250 MB chart
takes well under a second.

It copies the CRS, the affine transform (or GCPs and RPCs, if the reference is
georeferenced that way) and the `AREA_OR_POINT` pixel-convention tag. The
reference's colour table, band structure and nodata are **not** copied; those
belong to the image file.

| Option | Meaning |
| --- | --- |
| `-f`, `--overwrite` | Replace `output` if it exists. |
| `--no-strict-size` | Allow inputs of different pixel dimensions (checking is on by default). |
| `--copy-nodata` | Also copy the reference's nodata value. |

---

## Two warp backends

`build_chart_tileset.py --warp cpu|gpu`. Both are kept and tested; `cpu` is the
default.

- **`cpu`** warps each max-zoom tile with `gdal.Warp`, in worker processes.
- **`gpu`** evaluates the projection in torch, prefilters isotropically and
  samples on the card, one source sheet at a time in paint order. Tiles that
  only one sheet touches finish on the device; seam tiles accumulate as
  premultiplied partials in a fixed pool of device slots and composite once,
  when their last sheet has painted.

The filter is isotropic, and that is correct rather than a shortcut: LCC and Web
Mercator are both conformal, so an output pixel's footprint is a circle (axis
ratio measured at 1.004, including a sheet rotated 90°). Anisotropic filtering
was planned and dropped on that measurement — which also means the GPU does not
produce visibly better tiles. Its case is speed, and only sometimes:

- Two IFR sheets, z0–z13: CPU 2.0 min, GPU 0.7 min.
- All 37 IFR sheets, z0–z13: CPU 31.2 min, GPU 28.8 min. With every sheet
  bordering others, the seam traffic dominates, and GPU tiles also compress 8.6%
  worse under the same encoder.

Output agrees closely but not exactly: 97.7% of z13 pixels identical, p99
difference 4, the outliers being 1 px shifts of mask and sheet edges.

**Accuracy-for-speed knobs**, meant for trials rather than for a chart being
kept. `--warp-tolerance PIXELS` lets the warp approximate the projection, in
source pixels, like `gdalwarp -et`. On the CPU that is where the time is:
measured on a synthetic hairline sheet, `0.125` builds the max zoom **1.7x
faster** and moves 8% of pixels, by up to the full range; looser costs more
accuracy for no more speed. On the GPU the geometry is already approximated to
~1,000x inside that tolerance for ~1% of a batch, so the knob does nothing
there — its lever is `--resampling bilinear` instead of cubic, worth ~1.8x on
the sampler and noticeably smaller tiles.

Tiles are decoded and encoded with **imagecodecs**, not GDAL. Opening a 256 px
WebP as a GDAL dataset costs more than decoding it and serialises threads:
GDAL managed 720 tiles/s on one thread and *fell* to 940/s on 22, where
`imagecodecs.webp_decode` does 6,300/s on one and ~18,700/s on 22, pixel for
pixel identical. Encoding is ~28% faster with byte-identical output, since both
call the same libwebp.

---

## Public site

`www/index.html` is the page deployed beside the tilesets on a real server: one
button per tileset floating over a full-window globe, Cesium's 3D/2D/Columbus
picker, and nothing else. Switching never moves the camera, so charts compare in
place. Under the charts is Esri's Light Gray Canvas.

It is standalone rather than generated by `viewer.py`, and it cannot scan its
own folder, so it reads a `tilesets.json` written on the server by
`www/update_tilesets.sh` — same format `cesiumtiles-serve` answers with — and
falls back to the server's directory listing where there is one.

---

## Installing by hand

```bash
py -3 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pip install -e .
```

Runtime only: `-r requirements.txt`.

**Two dependencies come from their own indexes**, both already in
`requirements.txt`:

- **GDAL.** PyPI's `GDAL` is source-only on Windows for every Python version, so
  `--extra-index-url https://gisidx.github.io/gwi` points at Christoph Gohlke's
  [geospatial-wheels](https://github.com/cgohlke/geospatial-wheels), which
  publishes real `cp314` win_amd64 binaries. That gives **GDAL 3.13.3** — newer
  than the 3.8.4 Ubuntu 24.04's apt provides, so there is no advantage to
  building this under WSL. `osgeo.gdal` and `rasterio` coexist in one venv, each
  using its own GDAL build.
- **PyTorch.** `--extra-index-url https://download.pytorch.org/whl/cu126` for
  CUDA builds. cu126 is right for an Ada card (sm_89); cu128 is for Blackwell.
  On a machine with no NVIDIA GPU, swap that index for `.../whl/cpu` —
  `upsample.py` falls back by itself, it is only slow.

Model weights for the upsampler download on first use, into `source/models/`.

---

## Tests

```bash
.venv/Scripts/python -m pytest      # 235 tests, ~70 s
```

Everything runs against small synthetic rasters built in a temp directory; none
of it needs the chart files. The tile arithmetic in `cesiumtiles.scheme` is
checked against [mercantile](https://github.com/mapbox/mercantile), a separate
implementation of the same grid, so agreement is evidence rather than tautology.
Mosaic tests build the same LCC scenes on **both** warp backends and require
them to agree.

---

## Still open

- **Overlap order is a placeholder.** Sheets are painted in file-name order
  (reversed for IFR), which is arbitrary, and it shows: the FAA's Phoenix
  GeoTIFF has a blank white row through its map near 35.6 N, and Phoenix sorts
  after Las Vegas, so it paints over good Las Vegas map. Preferring the sheet
  whose own map area is further from its edge would fix that and most seam
  artefacts generally.
- **Empty ocean returns 404s.** Tiles are written only where a sheet has map, so
  a client requests and fails tiles over the gaps inside the extent. The tester
  no longer warns about these, but the requests still happen.
- **Nothing is scheduled.** The FAA republishes on a 56-day cycle, which wants a
  job that fetches the new edition, skips products whose edition has not moved,
  re-runs detection and stops for a human to review the manifests before
  rebuilding.
- **A better upsampler, maybe.** Real-CUGAN won the first round, but it is a
  1.28 M-parameter CNN with a receptive field of a few tens of pixels. 15 of the
  42 architectures `spandrel` recognises are attention-based and
  `scripts/upsample.py` loads any of them unchanged (`--model weights.pth`), so
  trying DAT, HAT, ATD, DRCT or SwinIR is a weights download. Prefer weights
  tuned for line art over the usual natural-image training; a model trained on
  photographs reaches for texture this artwork does not have. Measure line
  continuity on thin airways, not just sharpness: Real-ESRGAN was found to cut
  line continuity 18–23% against waifu2x at 3x, and a model that breaks thin
  lines is disqualified whatever else it does.
- **Diffusion upsamplers are probably the wrong tool** and were considered.
  They *sample*, so tiles would differ run to run, and their advantage is
  inventing plausible texture — skin, foliage, fabric. A chart has no texture to
  invent, only flat fills, hard edges and type. The first round already hinted
  at this: the winner was the smallest model tried, and the one that synthesised
  most lost.

### Why a learned upsampler at all

The chart content is a *rasterised vector drawing* — piecewise-constant regions
meeting at step edges — not a bandlimited sampling of a continuous field. Every
GDAL kernel except `near` is a linear filter, so each bandlimits edges by
construction and rings on them. Measured on a 256x256 Denver crop holding flat
fills, magenta airways, type and relief together, upsampling 2x, where "ringing"
counts output pixels straying outside the range of the four source pixels they
sit between:

| kernel | ringing | worst excursion | sharpness |
| --- | --- | --- | --- |
| near | 0.00% | 0 | 8.18 |
| bilinear | 0.00% | 0 | 7.00 |
| cubic | 5.24% | 21 | 8.28 |
| cubicspline | 2.86% | 23 | 6.12 |
| lanczos | 10.85% | 32 | 8.90 |

No kernel gives both zero ringing and sharp edges, and none can; `near` avoids
ringing only by aliasing instead. So the answer had to come from outside that
family — a model trained on line art, which is the closest well-studied analogue
to cartographic artwork. Edge-directed interpolation assumes natural images,
pixel-art scalers assume aliased input from a small palette (chart type and
hairlines are antialiased, and the relief is continuous tone), and vectorising
destroys the relief.

One cheap win came out of the same measurement and applies everywhere: the
tiling warp used to default to `lanczos`, which rang worst. Every pipeline now
warps with `cubic`, which halves the ringing at nearly the same sharpness.
`scripts/upsample_test.py` is the harness.

---

## Layout

```
pyproject.toml              packaging + pytest config
requirements.txt            runtime deps (GDAL and PyTorch indexes)
requirements-dev.txt        runtime + test deps
scripts/
    setup_repo.py           fresh clone -> working venv
    build_sectionals.py     one wrapper per product: fetch, prepare, tile
    build_sectionals_tac.py
    build_ifr_low.py
    build_wall_planning.py
    build_vfr_tileset.py    the single-chart pipeline the last one drives
    pipeline.py             what the wrappers share: run stages in order
    chart_series.py         each FAA chart series, described once
    layout.py               where everything lives (source/, models, ...)
    fetch_charts.py         download a series' current edition (+ fetch_chart.py worker)
    detect_sectional_areas.py   map areas for sectionals and TACs -> *_areas.json
    detect_ifr_areas.py     map areas and frame rules for IFR sheets
    detect_pdf_windows.py   register each PDF against its GeoTIFF -> *_pdf.json
    render_pdfs.py          draw sheets from vector PDFs
    upsample_charts.py      2x super-resolution over a series
    upsample.py             the upsampler itself, block by block
    heal_frames.py          paint over frame rules so sheets join
    *_areas.json            reviewed, committed map areas
source/                     every download and intermediate (gitignored)
src/geotransfer/
    core.py                 copy_geo_metadata / read_georeference
    cli.py
src/cesiumtiles/
    scheme.py               XYZ grid maths for both tiling schemes
    core.py                 build_tileset: one raster
    mosaic.py               build_mosaic: many overlapping sheets, masked
    gpumosaic.py            the GPU backend's top level and pyramid
    gpuwarp.py              projection and sampling in torch
    viewer.html             the tile tester page (plain HTML - edit this)
    viewer.py               fills in its four placeholders
    serve.py                local preview server (CORS, tile MIME types)
    cli.py
www/
    index.html              the public site: one button per tileset
    update_tilesets.sh      writes tilesets.json beside it
tests/                      235 tests, all on synthetic rasters
CLAUDE.md                   orientation notes, gotchas and measurements
```

`CLAUDE.md` is worth reading before changing anything: it records the decisions
that were settled with measurements, and the mistakes that have already been
made twice.
