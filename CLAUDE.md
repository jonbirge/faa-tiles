# CLAUDE.md

Orientation notes for Claude Code. Read `README.md` for user-facing docs; this
file records the things that are non-obvious, already-decided, or easy to get
wrong a second time.

## What this is

Two packages under `src/`, one venv, one test suite.

- **`geotransfer`** — copies CRS/transform from a GeoTIFF onto a same-size plain
  TIFF by duplicating the file and rewriting only its header tags. No pixel
  decode, no recompression.
- **`cesiumtiles`** — cuts a GeoTIFF into a static `z/x/y` pyramid for Cesium,
  plus a generated viewer and a local preview server. `cesiumtiles.mosaic`
  does the same for a *series* of overlapping sheets (the VFR sectionals).

**Everything downloaded or derived from downloads lives under `source/`** (the
user asked for this, so the lot can be deleted in one go): `source/sectionals/`
(55 GeoTIFFs), `source/tac/` (34 terminal area charts from 30 zips) and
`source/ifr-low/pdf/` (36 vector PDFs) and `source/ifr-high/pdf/` (12) from
`scripts/fetch_charts.py SERIES`, then `source/ifr-low/rendered/` (37 sheets
drawn from those PDFs), `source/ifr-low/healed/` (frame-healed copies, both
below) and `source/ifr-high/rendered/` (12 sheets, not healed -- see below),
`source/models/` (upsampler weights), `source/vendor/nunif`, and
`source/wall-planning/`. Paths come from `scripts/layout.py`; use it rather than
building paths from `REPO`. Tilesets stay at the top level.

The first chart was the FAA U.S. VFR Wall Planning Chart, in
`source/wall-planning/`: `vfr_geotiff_original.tif` is palette-indexed but
georeferenced; `vfr_wall_planning.tif` is RGB but has no geo metadata;
`vfr_wall_planning_geo.tif` is the `geotransfer` output combining them and is
the input to tiling. Only the combined file is on disk now. **It has no
automated download**: the FAA product page's "Planning Set" link
(`visual/<edition>/All_Files/Planning.zip`) was 404 for every edition, so the
user chose a manual drop-in; `build_wall_planning.py` checks for the files.

**Wrappers, one per product** (the user asked for these over running stages by
hand): `build_sectionals.py`, `build_sectionals_tac.py`, `build_ifr_low.py`,
`build_ifr_high.py`, `build_wall_planning.py`, all thin, running stage scripts through
`pipeline.py`. The chart wrappers do **not**
re-detect map areas unless `--detect` is passed, because the manifests are
reviewed and committed. `scripts/setup_repo.py` takes a fresh clone to a working
venv; it has been run against an existing venv, not from a truly fresh clone.

## Environment

- Windows 11, **Python 3.14.7**, venv at `.venv/`. An **i7-14700KF: 20 physical
  cores, 28 logical** -- 8 hyperthreaded P-cores plus 12 E-cores, so thread
  scaling is uneven and "24 cores" (the old note) was wrong -- and an
  **RTX 4070 SUPER, 12 GB** — `nvidia-smi` settles the earlier confusion
  between a "5070 Ti Laptop" and a "4070 Ti". It is Ada (sm_89), so **cu126**,
  not cu128: cu128 is for Blackwell and trails a torch release besides.
  `requirements.txt` carries that index, and `upsample.py:best_device()` falls
  back to CPU where CUDA is absent.
- **`pip install "torch>=2.14"` will not move you off a CPU build.** pip reads
  `2.14.0+cpu` as satisfying it and reports "already satisfied". Pin the exact
  local version, `torch==2.14.0+cu126`, to switch.
- **Windows is not a limitation here, and assuming it is has been wrong twice.**
  GDAL bindings install from the cgohlke index; PyTorch has `cp314` win_amd64
  wheels including CUDA ones. Check before claiming a platform blocks something.
  The user has Linux and macOS available too, so pick on merit, not portability.
- Use `pwsh.exe` not `powershell.exe` (see the user's global CLAUDE.md).
- `.venv/Scripts/python.exe` — note `Scripts/`, not `bin/`.
- **Every dependency that stays goes in `requirements.txt` (or
  `requirements-dev.txt`) in the same change that starts using it.** Do not just
  `pip install` it into the venv and move on. torch, torchvision and spandrel
  were installed for the upsampler that way and never recorded; when the base
  interpreter vanished and the venv had to be rebuilt, they were only recovered
  by reading package names out of the dead venv's `site-packages`. The venv is
  disposable; the requirements files are the record. If a package needs a
  non-PyPI index or a specific build (CPU vs CUDA), record that too.

**The user tests in their own browser, continuously, while you work.** They are
the live verification loop. Make the change, say what to look at, stop. Do not
stage a browser-pane reproduction to confirm something renders — they will see it
first. Reserve the pane for what they cannot easily observe: numeric
measurements, instrumented counters, palette validation, or chasing a specific
failure they reported.

**Do not run the full test suite on your own initiative.** Not before a commit,
not after a refactor, not "because it touched a lot of files". *Offering* is
welcome — say when you think a full run is worth it and let the user call it.
Running one test by node id to check a specific thing is fine. What is not fine
is a full run after every small change; this was asked for repeatedly before it
stuck.

**Not running the suite is not the same as not maintaining it.** The suite must
stay green and current, and keeping it that way is part of every change:

- When a change alters behaviour a test asserts, update that test **in the same
  change**, deliberately, without waiting for a run to reveal it. Grep `tests/`
  for the ids, names, strings or numbers you touched. The "Tighten the tester
  panel" commit removed the min/max zoom inputs and left
  `test_viewer_is_a_general_tile_tester` still asserting them; it failed on the
  user's next run.
- New behaviour gets a test, and a fixed bug gets a regression test, as the
  gotchas below already have.
- Fix a failing test by deciding which side is wrong: the code or the test. Never
  delete or loosen an assertion just to get back to green.
- Keep the test count and runtime quoted below accurate when they change.

```bash
.venv/Scripts/python -m pytest                        # 235 tests, ~70s
.venv/Scripts/cesiumtiles SOURCE OUT [--bbox W S E N] # build a tileset
.venv/Scripts/cesiumtiles-serve tileset               # preview on :8000
```

## Settled decisions — do not re-litigate these

These were investigated with measurements, not assumptions. Re-deriving them
costs a lot of context for no gain.

1. **GDAL's `gdal raster tile` is the tiling engine.** Since GDAL 3.11 it is the
   maintained reference implementation, and `gdal2tiles` is deprecated in favour
   of it from 3.13. `cesiumtiles` is a thin wrapper adding only what it lacks:
   geographic bbox cropping, resolution-derived zoom defaults, and Cesium
   metadata/viewer (GDAL emits Leaflet/OpenLayers/MapML/STAC, not Cesium).
   **Except for chart series**, which `cesiumtiles.mosaic` renders itself (see
   *Sectional mosaic* below); the user laid out that per-tile design.

2. **GDAL comes from a non-PyPI index.** PyPI's `GDAL` is sdist-only on Windows
   for *every* Python version, so `requirements.txt` carries
   `--extra-index-url https://gisidx.github.io/gwi` (cgohlke/geospatial-wheels).
   This yields **GDAL 3.13.3**. Without that index, `pip install -r` will try to
   build GDAL from source and fail.

3. **`osgeo.gdal` and `rasterio` coexist fine** in one venv, in either import
   order, each using its own bundled GDAL (rasterio 1.5.1 currently bundles 3.13.3 too).

4. **WSL is not an improvement.** Ubuntu 24.04's apt ships GDAL 3.8.4 — five
   minor versions *behind* what we have on Windows. There is no Linux-only tool
   in this space. (Also `/mnt/e` via the 9p bridge is ~20x slower for the many
   small file writes tiling produces.)

5. **Tiling choices the user made:** Web Mercator (EPSG:3857, `WebMercatorQuad`)
   and WebP **lossless**. Lossy q95 is ~4x smaller and available via `--lossy`,
   but lossless was chosen deliberately because chart hairlines and text ring
   under lossy compression.

6. **Max zoom for this chart is 9.** Native 262.48 m/px in LCC warps to ~329.8 m
   in Mercator, which lands at zoom 8.89 → z9. Computed independently by
   `scheme.zoom_for_resolution()` and by GDAL's own auto-detection; they agree.
   Full pyramid is **7,190 tiles / 285 MB**, built in ~56s on 24 cores.
   (5,577 is the count *with* `--skip-blank`; don't quote that as the default.)

7. **Parallelism is real but caps at ~3.8x on 24 cores.** Measured on a
   2,455-tile crop: 1 thread 135.1s, 4 threads 64.4s, 8 threads 47.6s, ALL_CPUS
   35.3s. Only the top zoom parallelises well — z9 alone runs at 141 tiles/s
   while z0-z8 manages 25 tiles/s, because the overview cascade is inherently
   sequential. **Converting the source to a tiled COG does not help** (34.6s vs
   36.0s); the stripped source layout is not the bottleneck, so don't spend time
   on that idea again.

8. **The chart is cropped to its neatline.** The printed sheet has a white
   margin, a heavy border and a "Nautical Miles" scale bar, all georeferenced,
   which would otherwise land on the globe as if they were map. The crop is
   `NEATLINE_LCC` in `scripts/build_vfr_tileset.py`: pixel box
   (472, 296)-(18096, 10992) of 18509 x 11441, keeping 89.0% of the area.
   The box is **inscribed** in the map, not circumscribed: the neatline is not
   square to the pixel grid (top edge row 272 on the left, row 200 on the
   right), so a containing box always catches border and paper. An earlier
   circumscribed crop looked right in the middle and left neatline at the edges.
   **It must be expressed in the source CRS** (`--bbox-crs source`) because the
   neatline is a rectangle in the chart's Lambert Conformal Conic, not in
   lon/lat — its corners differ by 8.3 deg of longitude NW vs SW. Cropped build
   is 6,372 tiles / 280.4 MB; uncropped is 7,190 / 285.0 MB.
   `--detect-neatline` re-measures it for a new chart edition and reproduces
   these numbers exactly: a chromatic bounding box first (margins are white, the
   scale-bar panel is white with black type, only the map is coloured), then
   shrink each edge until it holds no run of paper-white or neatline-black
   longer than 150 px. Map ink is broken up at that scale, so a long run of
   either is furniture.

## Gotchas that have already bitten

- **`gdal.Run` enables any boolean key that is present, whatever its value.**
  Passing `skip-blank=False` *enables* skipping. Flags we do not want must be
  omitted from the options dict entirely. This shipped as a bug once and
  silently changed the tile count; `tests/test_tiles.py` now guards it.
- **`gdal raster tile` spawns child `gdal.exe` processes** for large jobs, each
  handling a tile range. Its input must therefore be openable *by name from
  another process*: an anonymous `gdal.Warp("", ...)` dataset raises
  "Source dataset cannot be cloned", and a `/vsimem/` path is invisible to the
  child. Cropping writes a real temp `.vrt` for this reason — do not "optimise"
  it back to an in-memory dataset. Small jobs hide the problem by not spawning
  at all.

- **Writing large Python files via Bash heredocs fails here.** A `cat > f <<'EOF'`
  with a few hundred lines of Python silently produced no file and a bash syntax
  error. Use the `Write` tool for anything non-trivial.
- **Testing the Cesium viewer in the browser pane needs manual render pumping.**
  The pane throttles `requestAnimationFrame`, so Cesium's tile load queue stalls
  and *zero* tile requests appear — which looks exactly like a broken provider.
  It is not. Loop `viewer.scene.render()` with small `await` delays until
  `viewer.scene.globe.tilesLoaded` is true, then screenshot. The generated page
  exposes `window.viewer` for this.
- **`wsl.exe` from Git Bash mangles `/mnt/...` paths.** Prefix the command with
  `MSYS_NO_PATHCONV=1`.
- **The Cesium imagery rectangle must be `data_bounds`, never `bounds`.**
  `bounds` is snapped outward to whole tiles, so an edge coincides exactly with
  an imagery tile edge; Cesium's `_createTileImagerySkeletons` then computes an
  empty intersection and passes `undefined` into `rectangleToNativeRectangle`,
  throwing *"can't access property west"* from inside the render loop while
  panning the chart border. Measured: snapped edges caused ~60 bad calls, the
  unsnapped extent caused 0. `viewer.py` has `extentOf()` for this; a test
  guards it.
- **pdfium silently stops drawing past ~32767 px.** It rasterises through AGG,
  whose cell coordinates overflow there. Ask for a wider bitmap and it returns
  the full size you asked for, fills it white, draws the page frame -- and omits
  the interior beyond the limit. Nothing raises, no dimension is wrong, and the
  frame at the page edge still reads as ink, so a "last drawn column" probe says
  everything is fine. A whole IFR sheet at 2x is 48000 px wide and lost its
  right third; it looked like a georeferencing fault, and was misdiagnosed as
  one twice. Measured on ENR_L27: 31868 px complete, 35324 px starts dropping,
  47900 px empty past ~32000; the right half rendered *alone* is complete.
  `render_pdfs.py` renders in `BLOCK` (8192 px) squares for this, and
  `tests/test_render_pdfs.py` guards the size. When checking a render for
  missing content, measure **interior** ink by region, never a single extent.
- **Windows `SO_REUSEADDR` lets a second server hijack a bound port** (opposite
  of POSIX). `serve.py` sets `allow_reuse_address` only on non-Windows for this
  reason — don't "simplify" it back to `True`.
- **`build_mosaic`'s CPU pool defaults to `os.cpu_count()`, and 28 workers do
  not fit in this box's 32 GB.** The first `sectionals-tac` build died seconds
  into the z13 detail pass with `numpy ... Unable to allocate 48.0 MiB for an
  array with shape (3, 2048, 2048)` -- the *first* allocation each worker makes.
  Each worker holds a 256 MB GDAL cache plus ~250 MB of block buffers (48 MB
  premultiplied colour, 16 MB alpha, ~145 MB transient inside `_warp_layer`), so
  28 of them want roughly 14 GB before any pixels move, on top of the parent's
  plans. Measured with `--workers 16`, the same build peaked at **44.2 GB of
  commit charge** (the page file grew; the limit was 41.5 GB at rest) and
  finished. So: pass `--workers` on a big mosaic, and note the failure is an
  *ordinary* MemoryError from numpy, not a GDAL message -- nothing points at the
  pool. The detail level renders first (`_build_cpu`), so a crash there costs no
  max-zoom work. The same class of problem already narrowed the mask pool
  (`MASK_WORKERS`, `MASK_CACHE_MB`); the render pool has no such cap yet.

## Design notes

- `scheme.py` implements both tile grids itself rather than depending on
  `mercantile` at runtime; `mercantile` is a **dev-only** dependency used as an
  independent oracle in `tests/test_scheme.py`, so agreement is evidence.
- `TilesetResult` counts and bounds are read back **off disk** after a build,
  never assumed from the request. Requested != produced in both directions:
  `--skip-blank` omits tiles, and GDAL decides for itself which tiles a source
  reaches.
- Reported `bounds` in `metadata.json` snap **outward to whole tiles**: that is
  the tile coverage. `data_bounds` holds the true unsnapped extent, and is what
  the viewer's imagery rectangle must use (see the gotcha above). A test asserting a crop shrinks `bounds` on a given side
  will fail if the crop lands inside the same edge tile — compare area instead.
- `_reproject_bounds` densifies rectangle edges rather than transforming four
  corners. It matters: the chart's LCC top edge bows to 51.23 N at its midpoint
  while its highest corner is only 48.34 N, so corner-only reprojection would
  clip a 2.9-degree band off the top.
- Cropping uses a warp **cutline**, so it is pixel-exact (verified: alpha 0
  outside the boundary, 255 inside, at the right column) rather than snapped.
- The viewer fetches `metadata.json` at runtime with the generation-time copy as
  a `file://` fallback, so re-tiling needs no HTML change. It uses **no Cesium
  Ion token**: our tiles are the base layer and terrain is the default ellipsoid.

## Viewer diagnostics

The generated viewer has an **On screen** panel (visible imagery tiles by level,
with x/y ranges, plus camera altitude) and a **Downloaded** panel (tiles, network
bytes, average tile size, cache hits), with a reset button.

- Visible tiles come from `viewer.scene.globe._surface._tilesToRender`, walking
  `tile.data.imagery`. Those are **private** Cesium fields, so `visibleTiles()`
  is wrapped in try/catch and degrades to "unavailable" on a Cesium upgrade.
- Traffic comes from **Resource Timing**, not from patching Cesium.
- **Distinguishing a cache hit from a download is not obvious.** A cache hit can
  report `transferSize: 300` (a fixed header placeholder) with a full
  `encodedBodySize` and a **200** status — not 0, and not 304. The reliable test
  is `transferSize < encodedBodySize`: if so, the body never crossed the wire.
  An earlier version keyed on `transferSize === 0` and then on a 304 status, and
  both miscounted a fully cached load as a full download.
- **The tile-grid overlay is a `TileCoordinatesImageryProvider` with
  `requestImage` overridden** to stroke only the tile edge (no fill, no label —
  the user asked for a border only). It is a second imagery layer, so
  `visibleTiles()` filters on `tile.imageryLayer === baseLayer` or every tally
  doubles. Canvas-drawn, so it never touches the traffic counters.
- **Grid colour is a continuous deep-blue -> almost-red ramp**, computed from
  `level / maxzoom` (OKLCH, hue 264 -> 29, chroma 0.25, 75% opaque -- the user
  asked for 25% transparency and more saturation) so it re-scales for any
  source. The user asked for exactly this after an earlier alternating-hue
  version. Worth remembering rather than re-deriving: a smooth ramp separates
  *adjacent* levels least, and adjacent levels are what Cesium renders together
  -- measured with the `dataviz` validator, one hue over ten steps gives
  ΔL 0.047 and a smooth two-hue ramp gives protan ΔE 0.6. The legend naming each
  level is what carries identity. This is a deliberate, stated preference; do not
  "fix" it back to an alternating scheme.
- **Reset also busts the cache**, because script cannot clear the browser's HTTP
  cache. It rebuilds the imagery layer against a fresh `?r=<timestamp>`, which
  misses both Cesium's in-memory cache and the browser's. Verified: warm load
  reports 0 downloaded / 37 cached / 10.8 KB, and after reset 34 downloaded /
  0 cached / 2.51 MB.

## The viewer is a general tile tester

Not tied to its own tileset. The **Source** control is a **menu**, not a text
box (the user asked for this): local tilesets from the server's one-level scan,
then URLs connected this session, then a disabled separator and **Connect to
URL...**, which opens a `<dialog>`. The dialog takes a tileset directory URL
(resolved through its `metadata.json`, whose `url_template` is relative to *it*,
not to the page) or a raw `{z}/{x}/{y}` template, with scheme and tile size for
the template chosen in the dialog. There is no title heading — the user asked
for it gone; the document `<title>` stays.

- **The menu comes from `/tilesets.json`**, served by `cesiumtiles-serve` from
  `list_tilesets()`: the root if it holds `metadata.json`, then immediate
  subdirectories that do, in name order, rescanned per request. A browser page
  cannot list a directory itself. On another server (or a saved copy) the fetch
  fails and the menu falls back to `INITIAL_SOURCE` alone.
- **The menu is re-rendered, never patched** (`renderMenu()`), and re-selects
  `meta.source_spec`. Choosing "Connect to URL..." puts the selection back on
  the current source before the dialog opens, and a failed load leaves the
  current tileset in place, so the menu never shows a source that is not loaded.
- **MSAA defaults to none** (the user's call); the option reads "none", not
  "off".
- **Magnification is per imagery layer; the other rendering controls are not.**
  `maximumScreenSpaceError`, `resolutionScale` and `msaaSamples` live on the
  viewer or scene and survive a source change, but `magnificationFilter` is set
  on each `ImageryLayer`, and `relayer()` builds a new one. It used to be
  applied only from `applyRendering()`, so switching tilesets silently dropped
  "magnify" back to Cesium's LINEAR while the menu still read "nearest" -- the
  user spotted it. `relayer()` now calls `applyMagnification()`, which covers
  the grid toggle too; a test guards it.
- `window.tilesetMetadata` is **reassigned in `rebuild()`**, not captured once at
  startup. It went stale after a source change and reported the original
  tileset's values, which is confusing when debugging.
- Cross-origin servers that omit `Timing-Allow-Origin` report all three
  Resource Timing sizes as zero. Those are counted as `opaque` and the byte
  totals shown as `n/a (cross-origin)`, never as zero.

## Chart series mosaics

`fetch_charts.py SERIES` -> the series' detectors -> (`render_pdfs.py`) ->
(`heal_frames.py`) -> `build_chart_tileset.py SERIES`.
**`scripts/chart_series.py` is the one place a series is described**: its index
URL, which zips and files it wants (regexes), exclusions, download directory,
**which script detects its map areas** (`detector`), manifests
(`scripts/<series>_areas.json`, `<series>_pdf.json`) and tileset directory. Add
a series there, not by copying scripts. `pipeline.py` reads `detector` off the
series, so the wrappers no longer name a detection script and
`detect_sectional_areas.py` now takes a series argument like the IFR one.

**A composite series is layers, not sheets.** `sectionals-tac` has a `layers`
list and nothing else of its own: each layer stays the series it is, with its
own downloads, stages and reviewed manifest, and the composite only fixes the
paint order (every sheet of one layer below every sheet of the next) and which
layers earn the detail level. A composite raises rather than returning a
`directory` or `manifest`, so a stage cannot quietly write into a directory
nothing else reads. Building it after `tileset-sectionals` costs only the TACs.

**The manifests are always in downloaded-GeoTIFF pixel space.** A series that
renders PDFs tiles rasters drawn at `pdf_scale` times that, so pixel polygons
and frame bands are scaled by `Series.pixel_scale` at the point of use --
`MapArea.from_dict(spec, pixel_scale)` and `heal_frames.py`. Do not rescale the
manifests themselves; they are the reviewed record.

The sectionals came first, and the notes below are mostly theirs.
Decided with the user, with measurements: **z12** at first (the "finest pixel"
rule gives z13, driven only by the 1:250k Honolulu inset, at 4x the tiles), then
**z11 for both series** as a trial, and now **IFR z13, sectionals z12, wall
planning z11** (the user's call). Each is where its prepared source stops
holding detail: IFR renders from vector at 4x reach z14; the sectionals are
42.3 m/px (native z11.5), z12.5 upsampled, so z13 would be 1.4x finer than even
the upsampled sheets for ~4x the tiles; the planning chart is native ~z9.9
upsampled, z11 being one level past by choice. **Match max_zoom to the
prepared source's resolution** -- the IFR sheets went a build at z13 from 2x
renders, magnifying, before that was noticed. The z12 sectionals were built on
2026-09-18: **508,529 tiles / 5.30 GB** (the estimate was ~8.5 GB), 52.0 min
upsampling on the GPU plus 26.3 min tiling on the CPU warp.
**WebP q90**,
**overlaps by file name, later on top** (an acknowledged placeholder), map areas
**detected once, reviewed, committed** as `scripts/sectionals_areas.json`, and
lower zooms **box-filtered from children**. **Guam and Samoa are excluded**
(the user's call): the series' `exclude` names the Mariana and Samoan Islands
inset GeoTIFFs, which are not extracted and which the build also skips. Exclusion is per GeoTIFF, not per zip, because both ship inside
`Hawaiian_Islands.zip` with Hawaiian Islands and Honolulu.

- **Per tile, not VRT + `gdal raster tile`.** Each z12 tile warps only the sheets
  that reach it, composited front-to-back ("under") so it stops once opaque.
  Measured 388 tiles/s at z12 on 24 cores, 14 KB/tile. Do not warp lower zooms
  from the sheets: a z8 tile reads a 16x source window and ran at 13 tiles/s.
- **Map areas are masks, not clip rectangles.** Each sheet's area becomes a Byte
  mask attached to its VRT as an alpha band, which the warp honours. A lon/lat
  rectangle was tried first and cannot express enlarged insets printed over the
  map, the tilted/L-shaped island sheets, or Alaskan legend panels.
- **Sheets are re-based from NAD83 to WGS84** (`_wgs84_based`). Otherwise PROJ
  picks different datum operations in different tiles and warns of seams. The
  datums differ by ~2 m, under a z12 pixel.
- **Antimeridian:** footprints are unwrapped around each sheet's centre meridian
  and warped with a whole-world x offset. `metadata.json` bounds then have
  `west > east`. The camera and `Rectangle.contains` accept that, but
  **`UrlTemplateImageryProvider` does not**: it intersects the rectangle with
  the tiling scheme and keeps only west..180. The first full build showed only
  a few Pacific tiles around Guam and a tile-failure note, because this was
  claimed from the Cesium API rather than checked in the viewer. The viewer now
  gives the imagery the full longitude band (`imageryExtentOf`, edges 1e-5 deg
  inside +/-180) and the camera the true extent (`viewRectangle`). It also no
  longer warns on 404s from a metadata-described tileset, since a mosaic has
  no tiles over ocean by design.
- **Palette sheets are RGB-expanded before warping**, or resampling blends
  indices. A test guards it.

**Terminal area charts (`tac`) and the `sectionals-tac` composite.** 30 zips
from `visual/<edition>/tac-files/` yield **34 sheets**, because
Anchorage/Fairbanks, Denver/Colorado Springs, Seattle/Portland and
Tampa/Orlando each ship two -- compare sheet counts against zip counts here
too. The `tif_pattern` keeps `* TAC.tif` and nothing else: a zip also carries
that city's Flyway Planning chart (`Denver FLY.tif`), sometimes an airspace
graphic (`Anchorage Graphic.tif`) or `New York TAC VFR Planning Charts.tif`,
none of which are map. 678 MB downloaded.

- **A TAC is 1:250,000 at 300 dpi: 21.1679 m/px**, read off the world files --
  exactly half the sectionals' 42.3. Measured through
  `prepare_sources`, 32 of the 34 downloaded sheets already report native
  **z13** and the two Alaskan ones z12; upsampled 2x they reach past it. Same
  Real-CUGAN denoise3x weights as the sectionals, so the two layers meet on
  equal terms.
- **z12 with a sparse z13 detail level, not z13 everywhere** (the user's call).
  A uniform z13 would be ~2 M tiles / ~21 GB to magnify the 96% that is
  sectional -- the trade already rejected for `tileset-sectionals`. Instead
  `build_mosaic(detail_zoom=)` plans one level past `max_zoom` from
  `plan_detail_tiles`, keeping only tiles a source marked `detail` reaches:
  tens of thousands of tiles, not two million. Cesium falls back to the
  stretched z12 parent where the level is absent, exactly as it already does
  over ocean.
- **Every source paints into a kept detail tile, not just the detail ones**, so
  a TAC's edge sits on the magnified sectional rather than on a hard
  transparent boundary a tile wide.
- **The detail level feeds nothing below it.** The overview cascade still
  starts at `max_zoom`; so does the coverage read-back, because a sparse top
  level's columns describe one city, not the chart. `metadata.json` carries
  `fullzoom` beside `maxzoom` to say where the full coverage stops.
- **The TACs paint on top at every level** (the user's call), which is what
  "inserted where available" means -- not only at the finest one.
- **Los Angeles TAC is hand-traced and `manual`**, like the LA sectional and
  for the same reason: its west band fit spanned 4676-6326 px (every other
  sheet's worst side spans under 90) and the fitted slant silently dropped a
  wedge of the Pacific. Its neatline is a drawn rule, measured at west
  4669, east 14878, north 103, south 5890, each >99.8% dark across the full
  span of the opposite pair; the manifest is that rectangle inset 12 px.
  **The paper check did not catch it** -- it never catches map cut off, only
  collar left in (it flags 0 of 34 sheets). The per-side band spread the
  detector prints is what catches it.

Detection lessons, each learnt from a wrong outline:

- **Neatlines are not one kind of line.** West/east are meridians (straight in
  LCC) and get line fits; north/south may be parallels (arcs) or straight, and
  get quadratics. Denver's south edge bows 0.045 deg across the sheet.
- **Measure a side only between the two sides across it**, and never extrapolate
  a fit past its last band; corner bands run along the perpendicular collar and
  produced wild arcs.
- **Paper is `min(RGB) >= 250`, sampled not averaged.** Collar paper is 255;
  Canada's tint is 232-242 and read as paper at 235, cutting 16% off Montreal.
  Averaging smears notes-panel type into grey that reads as map.
- **The map must start *at* the detected edge** (48 px of non-paper), not merely
  somewhere in the next 600 px: a scale-bar line under the neatline passed the
  long-run test and left ~100 px of collar on nearly every sheet. The contact
  sheets did not show it; the per-edge paper check the script now prints did.
- Every image edge is trimmed 40 px for ragged paper margins too thin to fit.
- **Trust the numbers, not the thumbnails.** A clean contact sheet hid collar on
  49 of 57 sheets. After the fixes only Anchorage east is flagged (27%); a crop
  showed a ragged paper margin, now trimmed, and pale map behind it, but the
  figure was not chased further.
- **The paper check only catches collar left in, never map cut off.** Los
  Angeles's west edge fitted a slant (its legend panel sits above map that steps
  out to column ~605, with the LA Basin inset below), which passed the check at
  2% and silently dropped a wedge of ocean off Big Sur. The user spotted it.
  Los Angeles is now hand-traced and `manual`. When a sheet's collar is not a
  plain band on each side, trace it rather than tune the fitter.
- **IFR low (`ifr-low`) is CONUS L-01 to L-36 only, no insets** (the user's
  call). L-06 ships as two halves, `ENR_L06N`/`ENR_L06S`, which the first
  pattern missed: the fetch reported 36 ok while one zip extracted nothing.
  Compare sheet counts against zip counts after a fetch.
- **IFR low paints in reverse file-name order** (`reverse_order=True` in its
  series, the user's call after seeing overlap artefacts), so L-01 is on top of
  L-02 and so on. `build_chart_tileset.py --[no-]reverse-order` overrides a
  series' default. Still a placeholder for a real overlap rule.
- **All pipelines warp with `cubic`**, not `lanczos` (the user's call, on the
  earlier measurement that lanczos rang most and cubic halved it at nearly the
  same sharpness): `build_tileset`, the CLI, `build_mosaic` and the wall chart
  build. Overview cascades are untouched.
- **The IFR sheets are rendered from the FAA's vector PDFs, not upsampled.**
  This is the settled answer to the staircasing, and supersedes the
  super-resolution experiments below. The published GeoTIFFs are badly
  rasterised at source, so no upsampler can recover the edges; the same charts
  ship as true vector PDFs (`DELUS<odd>.zip`, two sheets each), which
  `render_pdfs.py` draws at `pdf_scale` times their 400 dpi. **Do not call
  this upsampling and do not add an upsampler to this path** -- every pixel
  comes from the vector geometry. Measured at 4x: ~161 s/sheet, and 5.2 GB of
  renders.
- **`pdf_scale` is tied to `max_zoom` and must be revisited with it.** A z13
  tile is ~14.7 m/px where these sheets sit. At `pdf_scale=2` the source is
  23.15 m/px, so the warp *magnified* 1.58x and the tiles were finer than the
  source feeding them -- an oversight when z12 became z13. At 4x the source is
  11.58 m/px and the warp minifies (0.79x), which is the regime GDAL's kernel
  widening handles properly. **Raising it does not invalidate existing renders
  by mtime**, so `render_pdfs.py` also compares each render's pixel size
  against `window x scale`; without that every sheet is silently kept at the
  old resolution.
- **Those PDFs carry no georeferencing** (their `.htm` metadata says so, giving
  only four bounding corners), so `detect_pdf_windows.py` registers each
  GeoTIFF against its PDF once per edition and commits the affine, CRS and page
  window as `scripts/ifr_low_pdf.json`. **`ENR_L06.pdf` is one 24000x8000 page
  holding both panels** that ship as `ENR_L06N` (at x=2000) and `ENR_L06S` (at
  x=16000), each with its own affine -- which is why a window is registered
  rather than the page assumed. Registration is ink-profile correlation at 1/8
  scale, then a +/-16 px search on five full-resolution probes whose offsets
  must agree; expect matches around 0.89-0.92.
- **A routine ifr-low build downloads only the PDFs** (`fetches_tifs` is false
  when `pdf_scale` is set), ~130 MB against 386 MB of GeoTIFFs. The GeoTIFFs
  are an input to re-detection alone: `build_ifr_low.py --detect` passes
  `fetch_charts.py --tifs` and reruns both detectors.
- **The sectionals are upsampled 2x with Real-CUGAN denoise3x**
  (`upsample_charts.py`, `upsample_model`/`upsample_scale` in the series). The
  user compared it against a plain build of the same three sheets at the same
  zoom and kept it. There is no vector escape here as there is for the IFR
  charts: the sectional PDFs wrap the very same rasters.
  **Whole sheets are upsampled, not their map areas.** Cropping first would be
  faster but puts an offset as well as a scale between the reviewed manifests
  and the raster, and `pixel_scale` is deliberately only a scale.
  It is not cheap in disk: ~900 MB per upsampled sheet, so ~48 GB for all 55.
- **Run the upsampler on the GPU.** Measured on the 4070 SUPER: **80.2
  blocks/s against 2.3 on CPU**, a 35x difference — about 35 min for the
  sectionals' ~171k blocks instead of ~14 h. `load_model(..., device=)` and
  `best_device()` handle it; the old CPU figure is why Real-CUGAN was shelved
  for the IFR sheets before the PDFs turned up.
- **Real-CUGAN over the IFR sheets was tried and shelved** before the PDFs were
  found; it did not remove the staircasing anyway, because that is baked into
  the FAA raster. Do not revive it there. `upsample.py` crops with `window=`
  and scales all four geotransform terms, which rotated sheets need.
- **The wall planning chart now uses the denoise3x Real-CUGAN weights** (the
  user asked to try them); earlier builds used no-denoise.
- **IFR low tiles are lossless WebP** (`lossless=True` in its series, the user's
  call); sectionals stay lossy q90. `build_chart_tileset.py --[no-]lossless`
  overrides the series default.
- **IFR map areas come from the frame rule, not the collar.** The map is mostly
  white, so `detect_sectional_areas.py` cannot work on them. The frame is a
  fully dark run 6-10 px thick across the middle of the sheet (L-12's is 6;
  legend column rules are 5), and L-34's right rule reads only 0.94 dark
  because something crosses it. L-23 frames a Wilmington-Bimini inset strip
  beside its map; the widest framed panel is taken and the other dropped.
- **IFR *low* sheets abut; they do not overlap, and the frame rule is the seam.**
  (The high charts do overlap -- see below -- so this is a property of the low
  set, not of IFR charts.)
  Cropping inside the rule (the first build) left dark 1-3 km gaps along all 32
  shared edges; the user saw them as black lines. Growing the outline showed the
  seams only close at the rule's *outer* edge, so there is no map under the rule
  on either sheet. The user chose healing: the manifest records `frame.outer`
  and `frame.clean` per sheet, `include` runs to `outer`, and `heal_frames.py`
  writes `source/ifr-low/healed/` copies with the band repeated from the clean
  row/column outward. `heal_frames=True` in the series makes the build read the
  healed copies and refuse stale ones. Result: 31 of 32 seams closed. **L-29/L-30
  keeps a straight ~450 m transparent sliver** (the W79 meridian lines up across
  it), so the FAA's two georeferenced sheets just do not meet there; closing it
  would need a bleed past the frame, which would overpaint real map elsewhere.
  The healed build ran 17.6 min, against ~9 min for the unhealed one.
- **IFR high (`ifr-high`) is the low pipeline at half the scale**, on the same
  scripts: CONUS H-01 to H-12 (not AKH, CB or the oceanic charts), 12 GeoTIFF
  zips and 6 PDF zips (`DEHUS1,3,..,11`, two sheets each -- 12 sheets from 6
  zips, so check the counts). `build_ifr_high.py`.
- **The high sheets are 24000x8000 at 92.60 m/px**, measured off the downloads:
  exactly half the low charts' 46.30, this being the smaller-scale chart. So
  `pdf_scale=4` gives 23.15 m/px and **z12** minifies it 0.79x -- the same ratio
  ifr-low gets from 4x at z13. z13 here would magnify 1.58x, which is the
  mistake ifr-low made from 2x renders. Keep the pair in step.
- **The high sheets overlap; they do not abut.** Measured on the 2026-09-03
  edition with `prepare_sources` footprints, east-west neighbours share 15-31%
  of a sheet (H-07/H-08 31.1%, H-05/H-10 25.1%) and H-10/H-12 share 48.7%;
  north-south neighbours 3-4%. **Do not heal these**, and do not conclude
  anything from lon/lat bounding boxes: those suggested H-01/H-03 overlap 27
  degrees of longitude, and a pixel probe put the shared points outside H-01
  entirely -- the sheets are conic rectangles, not lon/lat ones.
  `heal_frames=False`, and `detect_ifr_areas.py` reads that flag to write
  `include` from `frame.clean` rather than `frame.outer`, so each rule is
  cropped away and the sheet beneath shows through instead of being crossed by
  a black line.
- **The high crop was checked at a seam, not just in aggregate.** H-08 sorts
  after H-07 and paints over it, so H-08's west crop edge lands mid-map on
  H-07. At that edge (lon -90.13) the z12 tiles have **no full-height dark
  column and min alpha 255** -- no leaked rule, no gap. The nearest dark line is
  444 px away and is an ARTCC boundary over the Gulf. A whole-tileset scan is
  not enough on its own: 3.7% of ifr-high z12 tiles hold a full-tile dark run,
  but so do 3.3% of *healed* ifr-low's, so that statistic measures map content
  (grid lines, boundaries), not artefacts. Use ifr-low as the control.
- **H-12 is the odd high sheet**: 78.71 m/px rather than 92.60, and its
  geotransform is rotated 61 degrees -- a tall eastern-seaboard chart in a
  landscape image. Being the finest and sorting last, plain file-name order puts
  it on top, so `ifr-high` sets `reverse_order=False` where `ifr-low` sets True.
  A placeholder, like every overlap rule here.
- **The Phoenix GeoTIFF has a blank white row through its map** near 35.6 N.
  That is the FAA's file, not the mask; it shows because Phoenix sorts after Las
  Vegas. A better overlap rule is the fix, not a mask.

## GPU backend (`--warp gpu`)

`build_chart_tileset.py --warp gpu|cpu`, default **cpu** since the full IFR
trial (below; it was gpu before); both are kept and
tested (the user's call). Built after a comparison showed the *first* GPU design
lost to the CPU, and the user laid out the architecture that works:

- **Max zoom (`gpumosaic.render_top`), one source sheet at a time**, in paint
  order, bottom first, in the main process. Every tile the sheet touches is
  mapped to a source footprint in one batched pass; tiles are grouped into
  overlapping **chunks** (a sheet is up to 3.07 Gpx -- 9.2 GB uint8, ~49 GB
  float32 -- against 12 GB of VRAM), each decoded once on threads, uploaded
  premultiplied, prefiltered once, and sampled in batches of 128. Single-sheet
  tiles finish on the GPU; seam tiles wait as partials until their last sheet,
  then composite and encode **once**.
- **Seam tiles composite on the device** (`gpumosaic._SeamPool`), after the full
  IFR trial found the single dispatcher thread doing it in numpy -- busy 1,014 s
  of a 1,464 s z13 pass, up to 19,796 partials live. One premultiplied float16
  accumulator per tile ("under" is associative, so a running composite is
  enough), in **preallocated slots** so a gather or a store is one
  `index_select` rather than a launch per tile, and the card's share is fixed
  rather than growing with the live set. `SEAM_DEVICE_BYTES` (2 GiB, ~4,000
  tiles) bounds it; past that tiles spill to `_Partials` (host RAM, then disk)
  as before -- at 19,796 live they will, so the spill is a normal path, but it
  is now a *transfer*, not a composite. A test builds the same overlapping LCC
  scene with the pool ample, one slot and none, and the tiles must come out
  byte-identical.
- **Pyramid (`gpumosaic.render_overviews`)**: children decoded on threads with
  **imagecodecs** (see below), the premultiplied 2x2 average batched on the GPU. That
  average, not the codecs, was 60% of a parent's cost in numpy.
- **Encoding is on 22 threads in-process** (`mosaic.write_tile`), no pickling.
- **Lossless WebP uses `METHOD=2`** (`core.LOSSLESS_WEBP`): in lossless mode
  METHOD only sets effort, round trips are bit-exact (tested), and it encodes
  2x as fast as GDAL's default at no size cost. It helps both backends.
- **Measured, L-27 + L-28 (60k tiles, z0-z13):** CPU 2.0 min, GPU 1.0 min. z13
  alone: CPU 557 tiles/s, GPU ~1,200-1,290. Output matches: 98% of z13 pixels
  identical, p99 difference 2, tile counts equal at every level.
- **The filter is isotropic, and that is correct**, not a shortcut: LCC and Web
  Mercator are both conformal, so an output pixel's footprint is a circle (axis
  ratio 1.004 measured, including a sheet rotated 90 degrees). EWA/anisotropic
  filtering was planned and dropped on that measurement. For the same reason
  **the GPU does not produce visibly better tiles**; its case is speed.
- `render_top` prints a per-stage timing line (decode wait, prefilter, sample,
  hand-off, blocked-on-encoders). Use it before optimising anything. The first
  profile showed the stages running in turn, not together.

Things that have already bitten here:

- **The first GPU test build crashed the machine.** It read full-resolution
  source windows regardless of minification -- ~8 GB per worker at z11 -- and
  the Windows driver **spills CUDA allocations into system RAM** instead of
  failing. Now: mip-level reads, `MAX_WINDOW_PIXELS`/`MAX_CHUNK_PIXELS` raise
  before allocating, and `gpuwarp.limit_memory` caps the process so an overrun
  raises `OutOfMemoryError`. Probe one block's peak memory in one process
  before any parallel GPU run.
- **Colour scale:** the GPU works in 0..1, the CPU composite in 0..255. Mixing
  them rendered every GPU tile near-black. The antimeridian test caught it --
  the only LCC synthetic sheet, so the only one that ran the GPU path. Mosaic
  tests now include LCC scenes run on **both** backends; keep it that way.
- **Grid convention:** geotransform pixel space is edge-based (pixel j's centre
  at j + 0.5), so `grid_sample` normalisation is `2u/W - 1`, not
  `(2u + 1)/W - 1`. The identity-warp test guards it.
- **Checking a WebP round trip**: an early check read tiles back in a way that
  made every tile "differ". GDAL and Pillow in fact decode our tiles
  identically (3,000 checked). Test the checker against a known-good control.

- **Decoding tiles uses imagecodecs, not GDAL.** Opening a 256 px WebP as a
  GDAL dataset costs far more than decoding it and serialises threads (GIL or
  GDAL's own open-path locks): GDAL decoded 720/s on 1 thread and *fell* to
  940/s on 22; processes reached ~4,400/s. `imagecodecs.webp_decode` on the
  file's bytes does 6,300/s on 1 thread and ~18,700/s on 22, pixel-identical.
  That took the pyramid from 536 to 865 tiles/s. **Encoding was measured the
  same way and is *not* lock-bound** -- threads beat processes.
- **Mosaic tiles are encoded with imagecodecs too** (`core.encode_webp`,
  used by both backends through `mosaic.write_pixels`): ~28% faster than
  GDAL's driver, and the output is unchanged -- lossless decodes exactly, and
  lossy q90 is **byte-identical** to GDAL's (150 of 150 sectional tiles), as
  both call the same libwebp. It removed z13's encoder bound (32 -> 27 s on
  two sheets, encoders never blocking). `build_tileset` still uses GDAL.
- **Per-item Python overhead is what the GIL actually costs here**, not the
  codecs. Decoding children through paths, per-child tasks and an extra copy
  was ~150 us of GIL time per child; one task per parent and
  `webp_decode(..., hasalpha=True, out=...)` straight into the batch buffer
  brought the real function to ~4,400 parents/s.
- **Windows Defender slows reading freshly written files about 2x** (it scans
  on first open): 7,600/s read+decode fresh vs 15,900/s on a second read. The
  pyramid reads every tile the level above wrote seconds earlier, so this is
  about half its decode wait. Changing Defender is the user's call, not ours;
  an exclusion for the tileset output directories is the suggested fix.
- Measure threads against processes before blaming the GIL. It was wrongly
  blamed for encoding here, and the real lock was specific to opening files.

Two IFR sheets, z0-z13: **CPU 2.0 min, GPU 0.7 min** (built on E:, under the exclusion).

**Where it stops -- and a measurement mistake worth not repeating.**

- **Build and benchmark on E:, never on C:.** Every comparison build up to the
  Defender test wrote into Claude's scratch directory on C:, which is NTFS, not
  the Dev Drive, and writes small files at ~2,500-4,500/s against ~14,000/s on
  E:. That produced "the dispatcher is blocked on encoders 11 s" and, from it,
  a wrong conclusion that z13 was CPU-bound on encoding. Built onto E: the
  encoders are never blocked. Scratch builds now go in `.bench/` inside the repo
  (git-ignored), which is on the Dev Drive and under its Defender exclusion.
- **z13 is paced by the main thread's GPU-side work** -- chunk upload and
  prefilter, sampling -- not by encoding.
- **Encoder worker processes were built, measured and reverted.** Shared-memory
  tile slots, 24 processes: no gain (z13 25.4 s against 24.8 with threads,
  pyramid 885 against 888 tiles/s). Their isolated benchmark wrote to E:, so
  that verdict stands. Do not rebuild them expecting a win.
- **Benchmark encoding on real, varied tiles.** One tile encoded repeatedly ran
  at 454/s against 283/s for real ones.
- **Windows Defender scans every freshly written tile on its first open, and it
  is expensive**: logged with typeperf, `MsMpEng` used ~15.6 cores while 60k
  fresh tiles were read on E: (~2.9 ms of CPU per tile, about what encoding one
  costs), and 0.5 cores on a second read. **The Dev Drive's performance mode
  does not remove this** -- it defers scans ("open now, scan later"), it does not
  skip them; only an exclusion does. The user excluded the whole repo folder.
  Measured on two sheets: the pyramid went from 941 to 1,625 tiles/s (its
  decode wait 8.3 -> 2.6 s), z13 was unchanged (its tiles are not read back),
  and the build from 0.8 to 0.7 min. Note `source/` (FAA downloads) is now
  unscanned too, by the user's choice.
- **`(Get-MpPreference).PerformanceModeStatus`** reads 1 on this machine while
  the Security app shows Dev Drive protection on and `fsutil devdrv query E:`
  says trusted. Microsoft documents 0=enable/1=disable only for the Intune
  value; do not assume the PowerShell number means the same. The Security app's
  *See volumes* screen is the documented check. Tamper Protection is on, so
  `Set-MpPreference` changes from PowerShell silently do nothing.
- **Profile with torch.profiler before optimising the GPU side.** Stage timers
  and isolated microbenchmarks both misled here: a random sampling grid made
  bicubic look 17x its real cost, and a microbenchmark called downloads cheap
  when the profiler showed pageable copies taking half the main thread.
- The remaining lever is a trade-off, not a win: lossless effort 25 instead of
  75 encodes ~14% faster for ~8% larger tiles.

**Full IFR trial (2026-09-18), and why the default went back to cpu.** All 37
sheets, z0-z13, GPU: **28.8 min** against the CPU build's 31.2 (which predates
the imagecodecs encoder, so not a fair baseline). z13 took 24.4 min, and its
main thread spent 794 s in hand-off to the **single dispatcher thread**
compositing seam partials (up to 19,796 held at once) -- two sheets have
almost no seams, which is why the two-sheet benchmark showed 2x. Output:
97.7% of z13 pixels identical, p99 4; the 255-level outliers are 1 px shifts
of mask/sheet edges, and the GPU writes 9 more z13 edge tiles. GPU tiles
compress **8.6% worse** under the same encoder (the pixels, not the encoder).
The user set cpu as default; next steps are in a GitHub issue.

**Trading accuracy for speed (`--warp-tolerance`, `--resampling`).** Both
backends take both knobs; the defaults (exact, cubic) are unchanged and are what
a chart being kept should be built with.

- **`--warp-tolerance` is in source pixels on both backends**, the unit
  gdalwarp's `-et` uses. On the CPU it is gdal.Warp's `errorThreshold`
  (`mosaic.ERROR_THRESHOLD`, default 0); on the GPU it widens the lattice the
  projection is evaluated on exactly (`gpuwarp.lattice_step`).
- **On the GPU it is already free, so the knob does nothing there by default.**
  `LATTICE_STEP = 16` costs 1.2e-4 source px -- ~1,000x inside GDAL's own 0.125
  default, and below the ~5e-4 px float32 rounds the grid to anyway -- for ~1%
  of a batch. So `lattice_step` **caps at LATTICE_STEP** unless a caller passes
  its own `cap`, and loosening the tolerance past that buys nothing while
  losing accuracy. The GPU's lever is the reconstruction filter, not the
  geometry: `--resampling bilinear` instead of cubic. Do not re-derive this by
  widening the lattice and finding no gain.
- **On the CPU the tolerance is where the time is**, because the exact
  transformer is what costs ~4x in the kernel. Measured on a 4096 px synthetic
  LCC sheet of dense hairlines, tiled at its native z11 (441 tiles, 4 cores, so
  relative figures only): exact 4.7 s, **tolerance 0.125 2.8 s (1.7x)**, 0.5
  2.8 s, 2.0 2.8 s. **The win saturates at 0.125** -- once it is fitting a
  polynomial at all the tolerance barely matters -- while the damage keeps
  growing: 8.4% of pixels differ at 0.125, 11.4% at 0.5, 16.5% at 2.0, worst
  255/255 throughout. So 0.125 is the only loosening worth having, and nothing
  above it ever is.
- **`--resampling bilinear` is the GPU's lever, and it also shrinks tiles.**
  On the same sheet through the torch sampler (on this box's CPU, so indicative
  of the filter's relative cost only): bilinear **1.8x** cubic's time, nearest
  3.0x. Lossless tiles came out 2.01 MB against cubic's 3.38, and nearest's
  0.31 MB -- because interpolation *invents* intermediate values, and the more
  distinct values a tile holds the worse it compresses. That is very likely the
  same mechanism behind the GPU's 8.6% compression gap (issue step 5), and it
  points at the prefilter/reconstruction pair rather than at the encoder.
- Run-to-run variance on that box was ~25% on identical work, so treat anything
  under ~1.3x there as noise. The tolerance knob on the GPU backend produced
  **0.00% differing pixels** -- exactly as the cap intends.

## Public site (`www/`)

`www/index.html` is the page the user deploys as `index.html` beside their
tilesets: one button per tileset floating over a full-window globe, plus Cesium's 3D/2D/Columbus
picker, and nothing else (the user's call). **Switching never moves the camera**
-- no zoom to extents; it starts over CONUS via Cesium's default view -- so
charts compare in place. Under the
charts is Esri's Light Gray Canvas (public `services.arcgisonline.com` tiles).
The tile tester's rendering defaults (the user's call, for performance):
`useBrowserRecommendedResolution = false` so it renders at the display's full
pixel ratio, SSE 2, and **MSAA off** -- Cesium's own default is 4x, which on a
full-DPR framebuffer made the site sluggish and does nothing for draped imagery. It is standalone, not generated by `viewer.py`; keep its Cesium
version in step with `CESIUM_VERSION` (a test checks). **It cannot scan its
folder by itself**: it reads `tilesets.json` (written on the server by
`www/update_tilesets.sh`, same format as `cesiumtiles-serve`; it only checks
`metadata.json` exists, and the page reads the names itself), falling back to
the server's directory listing -- which most servers stop giving once
`index.html` exists, and the page detects getting itself back. Both routes
were checked against the real tilesets.

## Repo hygiene

- Git repo on `master`, pushed to the **public** GitHub repo `jonbirge/faa-tiles` (`origin`); anything committed is published once pushed. The user commits to `master` directly; there
  is no PR workflow here. `.gitignore` excludes `.venv/`, `*.tif`, `*.psd`,
  `source/`, `tileset/`, `tileset-*/`, which keeps `.git` at ~130 KB.
- **Line endings are LF everywhere**, enforced by `.gitattributes`
  (`* text=auto eol=lf`), which overrides the user's global `core.autocrlf=true`.
  When writing files from Python, use `write_text(..., newline="\n")` or the
  Write tool: plain `Path.write_text` on Windows emits CRLF, which is how a
  content-free "modified" `requirements-dev.txt` appeared.
- The source rasters under `source/` are large (3.2 GB of sectionals, 386 MB of
  IFR charts, a 250 MB wall chart). Never `cat`/`Read` them, and don't let them
  into a commit.
- `tileset-planning/` (**98,014 tiles / 440.6 MB at z11**, built in 3.2 min) is
  build output; regenerate rather than preserve. It was ~180 MB at the
  auto-detected z10; `build_wall_planning.py` now asks for **z11** (the user's
  call, one level past the z10 the 2x upsample reaches) and for the
  **denoise3x** weights, which the wrapper used to leave to
  `build_vfr_tileset.py`'s no-denoise default — so re-running it quietly built
  a different chart from the one on disk. Its upsample measured **45.7
  blocks/s** on the GPU against 2.3 on CPU: 1.1 min rather than ~21. It
  holds `tiles/` and `metadata.json` only - **no index.html**. The tile tester is
  rendered by `cesiumtiles-serve` and served from memory at `/`.
- **The tester page is `src/cesiumtiles/viewer.html`** - plain HTML, edit it
  directly. `viewer.py` only substitutes four placeholders (`__CESIUM__`,
  `__TITLE__`, `__METADATA__`, `__SOURCE__`). It used to be a Python string,
  which forced double-escaping (a literal backslash-backslash-d to mean the
  regex `\d`) and made edits error-prone.
  The server re-renders **per request**, so editing the HTML and reloading the
  browser shows the change with no restart. It ships as package data via
  `[tool.setuptools.package-data]`.
- **Do not leave extra tilesets lying around.** The user asked for this: build a
  scratch tileset if a test needs one, then delete it in the same turn. Only
  `tileset-planning/` should persist. (An earlier `tileset-colorado/` demo outlived its
  usefulness and had to be cleaned up by hand.) `tileset-sectionals/` (**5.30 GB, 508,529 tiles at
  z12**, upsampled 2x, WebP q90) and `tileset-ifr-low/` (**3.05 GB, 953,205 tiles at
  z13**, lossless, from 4x PDF renders, 31.2 min at 608 tiles/s) are
  the other real products and are expected to persist too.
  `tileset-ifr-high/` is **1.07 GB, 313,057 tiles at z12** (lossless, from 4x PDF
  renders, 14.3 min at 373 tiles/s, built 2026-09-20); the whole product takes
  about half an hour end to end, the cheapest of the four series.
  `tileset-sectionals-tac/` joined them on 2026-09-20: **5.93 GB, 568,218 tiles**,
  z0-z12 full plus a sparse z13 of 58,872 tiles over the 34 TACs (against 380,238
  at z12), tiled in 26.5 min. `tileset-ifr-high/` is the fifth product.
