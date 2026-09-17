#!/usr/bin/env python
"""Build the Cesium tileset for the FAA U.S. VFR Wall Planning Chart.

This is both the reproduction recipe for the published tileset and a worked
example of the library. Run it from the repo root:

    .venv/Scripts/python scripts/build_vfr_tileset.py

Useful variants:

    # See what would happen without writing 280 MB of tiles.
    .venv/Scripts/python scripts/build_vfr_tileset.py --dry-run

    # Lossless tiles, roughly 4x the size. The default is WebP q95, which was
    # reviewed on the real chart and showed no discernible ringing.
    .venv/Scripts/python scripts/build_vfr_tileset.py --lossless

    # Skip the model entirely and tile the chart at its native z9.
    .venv/Scripts/python scripts/build_vfr_tileset.py --no-upsample

    # Quick iteration: stop at zoom 7 (about 90 seconds of work, not 60).
    .venv/Scripts/python scripts/build_vfr_tileset.py --max-zoom 7 --out tileset-draft

    # New chart edition? Re-measure the neatline instead of trusting the constant.
    .venv/Scripts/python scripts/build_vfr_tileset.py --detect-neatline

The pipeline has three stages. Stage 1 is skipped if its output already exists.

  1. geotransfer  Copy the CRS and transform from the FAA's palette-indexed
                  GeoTIFF onto the full-colour RGB render, which has the better
                  pixels but no georeferencing.
  2. neatline     Work out where the map graphic actually ends, so the printed
                  margin, border and scale bar do not get pasted onto the globe.
  3. upsample     Double the resolution with Real-CUGAN, which raises the
                  native zoom from z9 to z10. Chosen over APISR and waifu2x on
                  a side-by-side of all three over the whole chart.
  4. cesiumtiles  Cut the result into a z/x/y pyramid.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cesiumtiles import build_tileset  # noqa: E402
from geotransfer import copy_geo_metadata  # noqa: E402
from upsample import DEFAULT_MODEL, load_model, upsample_raster  # noqa: E402

# --------------------------------------------------------------------------
# Inputs. Both come from the FAA's VFR Wall Planning Chart product; the RGB
# render is the one worth looking at, the GeoTIFF is the one that knows where
# it is.
# --------------------------------------------------------------------------
from layout import WALL_PLANNING  # noqa: E402

GEO_REFERENCE = WALL_PLANNING / "vfr_geotiff_original.tif"   # palette-indexed, georeferenced
RGB_IMAGE = WALL_PLANNING / "vfr_wall_planning.tif"          # full colour, no geo metadata
COMBINED = WALL_PLANNING / "vfr_wall_planning_geo.tif"       # stage 1 output

# --------------------------------------------------------------------------
# Where the map graphic ends and the printed furniture begins. Outside it are a
# white paper margin, a heavy black neatline, and a "Nautical Miles" scale bar.
# All of it is georeferenced, so without this crop it gets painted onto the
# globe as if it were terrain.
#
# These numbers are in the chart's OWN CRS (a custom Lambert Conformal Conic, in
# metres), not lon/lat: the sheet's corners differ by 8.3 degrees of longitude
# between NW and SW, so a lon/lat box would leave white wedges in the corners.
#
# The box is INSCRIBED in the map, not circumscribed about it. The neatline is
# not aligned to the pixel grid -- its top edge runs from row 272 on the left to
# row 200 on the right -- so any axis-aligned box that contains the whole map
# also contains slices of border and paper. Trimming to the inscribed box costs
# about 1.8% of the area and is what keeps the edges clean.
#
# Measured from the 2025 edition with --detect-neatline: pixel box
# (472, 296)-(18096, 10992) of 18509 x 11441, i.e. margins of 472 left, 296 top,
# 413 right, 449 bottom. Keeps 89.0% of the sheet. Re-running --detect-neatline
# reproduces these numbers exactly.
# --------------------------------------------------------------------------
NEATLINE_LCC = (-2065471.156, -1353550.704, 2560432.418, 1453780.3)  # W, S, E, N

TITLE = "U.S. VFR Wall Planning Chart"
DEFAULT_OUT = REPO / "tileset-planning"
UPSAMPLED_DIR = WALL_PLANNING / "upsampled"


def detect_neatline(source: Path, run_limit: int = 150, step: int = 8, decimation: int = 8):
    """Re-measure the crop from the image. Returns (W, S, E, N) in the source CRS.

    Two stages, because two different things have to be distinguished.

    First, find roughly where the map is: the paper margin is pure white and the
    scale-bar panel is white with black type, so only the map itself is
    chromatic (blue ocean, green and tan terrain). Saturation separates map from
    furniture without having to recognise any of the furniture.

    That bounding box still catches border and paper, because the neatline is
    not square to the pixel grid. So second, shrink each edge until it is clean,
    judged on the thing that really tells furniture from map: a long
    uninterrupted run of paper-white or of neatline-black. Map ink is broken up
    at that scale by coastlines, symbols and type, so a run of ``run_limit``
    pixels of either is border, not content.
    """
    import numpy as np
    from osgeo import gdal

    gdal.UseExceptions()
    ds = gdal.Open(str(source))
    width, height = ds.RasterXSize, ds.RasterYSize

    # -- stage 1: chromatic bounding box, from a cheap decimated read ---
    small = ds.ReadAsArray(buf_xsize=width // decimation, buf_ysize=height // decimation)
    a = small.astype(np.int16)
    mask = (a.max(axis=0) - a.min(axis=0)) > 10
    rows = np.where(mask.mean(axis=1) > 0.25)[0]
    cols = np.where(mask.mean(axis=0) > 0.25)[0]
    if not len(rows) or not len(cols):
        raise SystemExit("no chromatic content found; is this the right image?")
    left, top = int(cols[0] * decimation), int(rows[0] * decimation)
    right, bottom = int((cols[-1] + 1) * decimation), int((rows[-1] + 1) * decimation)
    print(f"  chromatic box   : ({left}, {top})-({right}, {bottom})")

    # -- stage 2: shrink until every edge is free of paper and neatline -
    def longest_run(flags):
        if not flags.any():
            return 0
        padded = np.concatenate(([False], flags, [False]))
        edges = np.flatnonzero(padded[1:] != padded[:-1])
        return int((edges[1::2] - edges[::2]).max())

    def worst_run(x, y, xsize, ysize):
        strip = ds.ReadAsArray(x, y, xsize, ysize).astype(np.int16)
        paper = (strip.min(axis=0) > 245).ravel()
        ink = (strip.max(axis=0) < 100).ravel()
        return max(longest_run(paper), longest_run(ink))

    for _ in range(200):
        sides = {
            "top": worst_run(left, top, right - left, 1),
            "bottom": worst_run(left, bottom - 1, right - left, 1),
            "left": worst_run(left, top, 1, bottom - top),
            "right": worst_run(right - 1, top, 1, bottom - top),
        }
        dirty = [s for s, run in sides.items() if run > run_limit]
        if not dirty:
            break
        if "top" in dirty:
            top += step
        if "bottom" in dirty:
            bottom -= step
        if "left" in dirty:
            left += step
        if "right" in dirty:
            right -= step
    else:
        raise SystemExit("crop did not converge; check run_limit")

    print(f"  inscribed box   : ({left}, {top})-({right}, {bottom}) of {width} x {height}")
    print(f"  margins dropped : left {left}, top {top}, right {width - right}, "
          f"bottom {height - bottom}")
    print(f"  keeps {(right - left) * (bottom - top) / (width * height) * 100:.1f}% of the sheet")

    gt = ds.GetGeoTransform()
    return (round(float(gt[0] + left * gt[1]), 3), round(float(gt[3] + bottom * gt[5]), 3),
            round(float(gt[0] + right * gt[1]), 3), round(float(gt[3] + top * gt[5]), 3))


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--out", type=Path, default=DEFAULT_OUT,
                   help="output directory (default: %(default)s)")
    p.add_argument("--detect-neatline", action="store_true",
                   help="re-measure the crop from the image instead of using the "
                        "stored constant; do this for a new chart edition")
    p.add_argument("--no-crop", action="store_true",
                   help="tile the whole sheet, printed margin and scale bar included")
    p.add_argument("--no-upsample", action="store_true",
                   help="tile the chart at its native resolution, skipping the "
                        "super-resolution stage and topping out at z9")
    p.add_argument("--model", default=str(DEFAULT_MODEL),
                   help="upsampling weights, or 'waifu2x' (default: Real-CUGAN)")
    p.add_argument("--keep-upsampled", action="store_true",
                   help="keep the intermediate GeoTIFF; it is ~1 GB and nothing "
                        "downstream needs it")
    p.add_argument("--lossless", action="store_true",
                   help="lossless WebP, roughly 4x the size. The default is q95, "
                        "which was reviewed on the real chart and showed no "
                        "discernible ringing even on hairlines and type")
    p.add_argument("--quality", type=int, default=95,
                   help="lossy WebP quality, 1-100 (default: %(default)s). "
                        "Below about 90 the linework starts to suffer")
    p.add_argument("--format", dest="tile_format", default="webp",
                   choices=["webp", "png", "jpeg"],
                   help="webp is ~25%% smaller than png at the same fidelity; "
                        "jpeg has no alpha so the chart edges would go black "
                        "(default: %(default)s)")
    p.add_argument("--scheme", default="mercator", choices=["mercator", "geographic"],
                   help="mercator is the standard slippy-map grid and needs no "
                        "config in Cesium; geographic matches Cesium's native "
                        "globe tiling and yields ~20%% fewer tiles but needs an "
                        "explicit GeographicTilingScheme (default: %(default)s)")
    p.add_argument("--min-zoom", type=int, default=0,
                   help="0 gives Cesium a complete pyramid to descend (default: %(default)s)")
    p.add_argument("--max-zoom", type=int, default=None,
                   help="default is automatic: the level where tile pixels match "
                        "the chart's own resolution, which is z9 here. Higher just "
                        "magnifies; lower throws detail away")
    p.add_argument("--threads", default="ALL_CPUS",
                   help="parallel workers (default: %(default)s). Expect ~3.8x on "
                        "24 cores; the sequential overview cascade caps it")
    p.add_argument("--skip-blank", action="store_true",
                   help="omit fully transparent tiles. Saves ~600 tiles but they "
                        "are only a few hundred bytes each, and their absence "
                        "makes the viewer emit 404s")
    p.add_argument("--dry-run", action="store_true",
                   help="print the plan and exit without writing tiles")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    # -- stage 1: georeference the RGB render -----------------------------
    print("[1/4] georeferencing")
    if COMBINED.exists():
        print(f"  {COMBINED.name} already exists, reusing it")
    else:
        for required in (GEO_REFERENCE, RGB_IMAGE):
            if not required.exists():
                print(f"  error: missing input {required}", file=sys.stderr)
                return 1
        # Duplicates the RGB file and rewrites only its GeoTIFF header tags, so
        # the pixels are untouched and it takes well under a second.
        copy_geo_metadata(GEO_REFERENCE, RGB_IMAGE, COMBINED)
        print(f"  wrote {COMBINED.name}")

    # -- stage 2: decide the crop -----------------------------------------
    print("[2/4] neatline")
    if args.no_crop:
        bbox = None
        print("  cropping disabled; the printed margin will be tiled too")
    elif args.detect_neatline:
        bbox = detect_neatline(COMBINED)
        print(f"  measured: {tuple(round(v, 3) for v in bbox)}")
    else:
        bbox = NEATLINE_LCC
        print(f"  using stored constant: {bbox}")

    # -- stage 3: upsample -------------------------------------------------
    print("[3/4] upsampling")
    if args.dry_run:
        print("  --dry-run: stopping here")
        print(f"    output   {args.out}")
        print(f"    format   {args.tile_format}"
              f"{' lossless' if args.lossless else ' lossy q' + str(args.quality)}")
        print(f"    upsample {'off' if args.no_upsample else args.model}")
        print(f"    scheme   {args.scheme}")
        print(f"    zooms    {args.min_zoom}..{args.max_zoom or 'auto'}")
        print(f"    bbox     {bbox if bbox else 'none (whole sheet)'}")
        return 0

    # The crop is applied by whichever stage reads the source first, so it is
    # only ever done once.
    if args.no_upsample:
        tiling_source, tiling_bbox = COMBINED, bbox
        print("  skipped; tiling at native resolution")
    else:
        tiling_source = UPSAMPLED_DIR / f"{args.out.name}.tif"
        upsample_raster(COMBINED, tiling_source, load_model(args.model, args.threads
                                                            if isinstance(args.threads, int) else 0),
                        bbox=bbox)
        tiling_bbox = None

    # -- stage 4: tile -----------------------------------------------------
    print("[4/4] tiling")
    result = build_tileset(
        tiling_source,
        args.out,
        bbox=tiling_bbox,
        # The neatline is a rectangle in the chart's own projection, not in
        # lon/lat, so the crop has to be expressed there.
        bbox_crs="source",
        scheme=args.scheme,
        min_zoom=args.min_zoom,
        max_zoom=args.max_zoom,
        tile_format=args.tile_format,
        lossless=args.lossless,
        quality=args.quality,
        # lanczos on both the warp and the overview cascade. The alternatives
        # GDAL offers (bilinear, cubic, average, mode, ...) are all available,
        # but lanczos keeps hairline symbology sharpest.
        resampling="lanczos",
        overview_resampling="lanczos",
        threads=args.threads,
        skip_blank=args.skip_blank,
        overwrite=True,
        title=TITLE,
        quiet=False,
    )

    print()
    # The intermediate is ~1 GB and nothing downstream reads it.
    if not args.no_upsample and not args.keep_upsampled:
        tiling_source.unlink(missing_ok=True)

    print(result.summary())
    print()
    print(f"preview it with:  .venv/Scripts/cesiumtiles-serve {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
