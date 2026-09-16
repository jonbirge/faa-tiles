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

The data: the FAA U.S. VFR Wall Planning Chart. `vfr_geotiff_original.tif` is
palette-indexed but georeferenced; `vfr_wall_planning.tif` is RGB but has no geo
metadata; `vfr_wall_planning_geo.tif` is the `geotransfer` output combining them
and is the input to all tiling. The sectional series lives in `sectionals/`
(57 GeoTIFFs, 3.2 GB, from `scripts/fetch_sectionals.py`).

## Environment

- Windows 11, **Python 3.14.7**, venv at `.venv/`. 24 cores, NVIDIA GPU
  (Windows reports an RTX 5070 Ti Laptop; the user has said 4070 Ti — reconcile
  before picking a CUDA build, since Blackwell needs cu128 and Ada does not).
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
.venv/Scripts/python -m pytest                        # 139 tests, ~45s
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
- **Windows `SO_REUSEADDR` lets a second server hijack a bound port** (opposite
  of POSIX). `serve.py` sets `allow_reuse_address` only on non-Windows for this
  reason — don't "simplify" it back to `True`.

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
  `level / maxzoom` (hue 212 + 173*f, HSL, 50% alpha) so it re-scales for any
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

Not tied to its own tileset. The **Source** box takes a tileset directory
(resolved through that directory's `metadata.json`, whose `url_template` is
relative to *it*, not to the page) or a raw `{z}/{x}/{y}` template (used as
given, with the form controls supplying scheme/zooms/tile size). There is no
title heading — the user asked for it gone; the document `<title>` stays.

- `window.tilesetMetadata` is **reassigned in `rebuild()`**, not captured once at
  startup. It went stale after a source change and reported the original
  tileset's values, which is confusing when debugging.
- Cross-origin servers that omit `Timing-Allow-Origin` report all three
  Resource Timing sizes as zero. Those are counted as `opaque` and the byte
  totals shown as `n/a (cross-origin)`, never as zero.

## Sectional mosaic

`fetch_sectionals.py` -> `detect_sectional_areas.py` -> `build_sectional_tileset.py`.
Decided with the user, with measurements: **z12** (the "finest pixel" rule gives
z13, driven only by the 1:250k Honolulu inset, at 4x the tiles), **WebP q90**,
**overlaps by file name, later on top** (an acknowledged placeholder), map areas
**detected once, reviewed, committed** as `scripts/sectional_areas.json`, and
lower zooms **box-filtered from children**.

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
  `west > east`, which Cesium rectangles accept as-is.
- **Palette sheets are RGB-expanded before warping**, or resampling blends
  indices. A test guards it.

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
- **The Phoenix GeoTIFF has a blank white row through its map** near 35.6 N.
  That is the FAA's file, not the mask; it shows because Phoenix sorts after Las
  Vegas. A better overlap rule is the fix, not a mask.

## Repo hygiene

- Git repo on `master`, no remote. The user commits to `master` directly; there
  is no PR workflow here. `.gitignore` excludes `.venv/`, `*.tif`, `*.psd`,
  `sources/`, `tileset/`, `tileset-*/`, which keeps `.git` at ~130 KB.
- **Line endings are LF everywhere**, enforced by `.gitattributes`
  (`* text=auto eol=lf`), which overrides the user's global `core.autocrlf=true`.
  When writing files from Python, use `write_text(..., newline="\n")` or the
  Write tool: plain `Path.write_text` on Windows emits CRLF, which is how a
  content-free "modified" `requirements-dev.txt` appeared.
- The source rasters are large (62 MB, 250 MB, and a 1.2 GB PSD in `sources/`).
  Never `cat`/`Read` them, and don't let them into a commit.
- `tileset/` (~280 MB) is build output; regenerate rather than preserve. It
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
  `tileset/` should persist. (An earlier `tileset-colorado/` demo outlived its
  usefulness and had to be cleaned up by hand.) `tileset-sectionals/` (~8 GB) is
  the other real product and is expected to persist too.
