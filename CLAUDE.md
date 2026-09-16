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
  plus a generated viewer and a local preview server.

The data: the FAA U.S. VFR Wall Planning Chart. `vfr_geotiff_original.tif` is
palette-indexed but georeferenced; `vfr_wall_planning.tif` is RGB but has no geo
metadata; `vfr_wall_planning_geo.tif` is the `geotransfer` output combining them
and is the input to all tiling.

## Environment

- Windows 11, **Python 3.14.4**, venv at `.venv/`. 24 cores.
- Use `pwsh.exe` not `powershell.exe` (see the user's global CLAUDE.md).
- `.venv/Scripts/python.exe` — note `Scripts/`, not `bin/`.

```bash
.venv/Scripts/python -m pytest                        # 115 tests, ~30s
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

2. **GDAL comes from a non-PyPI index.** PyPI's `GDAL` is sdist-only on Windows
   for *every* Python version, so `requirements.txt` carries
   `--extra-index-url https://gisidx.github.io/gwi` (cgohlke/geospatial-wheels).
   This yields **GDAL 3.13.3**. Without that index, `pip install -r` will try to
   build GDAL from source and fail.

3. **`osgeo.gdal` and `rasterio` coexist fine** in one venv, in either import
   order, each using its own bundled GDAL (3.13.3 and 3.12.4 respectively).

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
   Full pyramid is 5,577 tiles / 285 MB, built in ~62s.

## Gotchas that have already bitten

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
- **Windows `SO_REUSEADDR` lets a second server hijack a bound port** (opposite
  of POSIX). `serve.py` sets `allow_reuse_address` only on non-Windows for this
  reason — don't "simplify" it back to `True`.

## Design notes

- `scheme.py` implements both tile grids itself rather than depending on
  `mercantile` at runtime; `mercantile` is a **dev-only** dependency used as an
  independent oracle in `tests/test_scheme.py`, so agreement is evidence.
- `TilesetResult` counts and bounds are read back **off disk** after a build,
  never assumed from the request — GDAL skips tiles that miss the source's
  curved footprint, so requested ≠ produced.
- Reported `bounds` in `metadata.json` snap **outward to whole tiles**, because
  that is what Cesium's imagery `rectangle` needs. `data_bounds` holds the
  unsnapped extent. A test asserting a crop shrinks `bounds` on a given side
  will fail if the crop lands inside the same edge tile — compare area instead.
- Cropping uses a warp **cutline**, so it is pixel-exact (verified: alpha 0
  outside the boundary, 255 inside, at the right column) rather than snapped.
- The viewer fetches `metadata.json` at runtime with the generation-time copy as
  a `file://` fallback, so re-tiling needs no HTML change. It uses **no Cesium
  Ion token**: our tiles are the base layer and terrain is the default ellipsoid.

## Repo hygiene

- Not a git repo yet. `.gitignore` already excludes `.venv/`, `*.tif`, `*.psd`,
  `sources/`, `tileset/`, `tileset-*/`.
- The source rasters are large (62 MB, 250 MB, and a 1.2 GB PSD in `sources/`).
  Never `cat`/`Read` them, and don't let them into a commit.
- `tileset/` (285 MB) and `tileset-colorado/` (8 MB) are build output; regenerate
  rather than preserve.
