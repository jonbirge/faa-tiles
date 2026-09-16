#!/usr/bin/env python
"""Build the Cesium tileset for the FAA U.S. VFR Wall Planning Chart.

This is both the reproduction recipe for the published tileset and a worked
example of the library. Run it from the repo root:

    .venv/Scripts/python scripts/build_vfr_tileset.py

Useful variants:

    # See what would happen without writing 280 MB of tiles.
    .venv/Scripts/python scripts/build_vfr_tileset.py --dry-run

    # A quarter of the size, at the cost of some ringing on fine linework.
    .venv/Scripts/python scripts/build_vfr_tileset.py --lossy

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
  3. cesiumtiles  Cut the cropped chart into a z/x/y pyramid plus a viewer.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from cesiumtiles import build_tileset  # noqa: E402
from geotransfer import copy_geo_metadata  # noqa: E402

# --------------------------------------------------------------------------
# Inputs. Both come from the FAA's VFR Wall Planning Chart product; the RGB
# render is the one worth looking at, the GeoTIFF is the one that knows where
# it is.
# --------------------------------------------------------------------------
GEO_REFERENCE = REPO / "vfr_geotiff_original.tif"      # palette-indexed, georeferenced
RGB_IMAGE = REPO / "vfr_wall_planning.tif"             # full colour, no geo metadata
COMBINED = REPO / "vfr_wall_planning_geo.tif"          # stage 1 output

# --------------------------------------------------------------------------
# The neatline: the rectangle where the map graphic ends and the printed
# furniture begins. Outside it are a white margin, a heavy black border, and a
# "Nautical Miles" scale bar -- all georeferenced, so without this crop they get
# painted onto the globe as if they were terrain.
#
# These numbers are in the chart's OWN CRS (a custom Lambert Conformal Conic,
# metres), not lon/lat, because that is the frame the neatline is a true
# rectangle in. Its corners differ by 8.3 degrees of longitude between NW and SW,
# so a lon/lat box would leave white wedges in the corners.
#
# Measured from the 2025 edition with --detect-neatline: pixel box
# (422, 221)-(18148, 11070) of 18509 x 11441, i.e. margins of 422 left, 221 top,
# 361 right, 371 bottom. Keeps 90.8% of the image area.
# --------------------------------------------------------------------------
NEATLINE_LCC = (-2078595.031, -1374023.013, 2574081.248, 1473465.213)  # W, S, E, N

TITLE = "U.S. VFR Wall Planning Chart"
DEFAULT_OUT = REPO / "tileset"


def detect_neatline(source: Path, threshold: float = 0.25, decimation: int = 8):
    """Re-measure the neatline by finding where chromatic content lives.

    The margin is pure white and the scale-bar panel is white with black text
    and rules; only the map itself is chromatic (blue ocean, green and tan
    terrain). Counting pixels with real saturation therefore separates map from
    furniture without needing to recognise any of the furniture.

    Returns (west, south, east, north) in the source's own CRS.
    """
    import numpy as np
    from osgeo import gdal

    gdal.UseExceptions()
    ds = gdal.Open(str(source))
    width, height = ds.RasterXSize, ds.RasterYSize

    def chromatic(block):
        a = block.astype(np.int16)
        return (a.max(axis=0) - a.min(axis=0)) > 10

    # Pass 1: a decimated read to find the box approximately.
    small = ds.ReadAsArray(buf_xsize=width // decimation, buf_ysize=height // decimation)
    mask = chromatic(small)
    rows = np.where(mask.mean(axis=1) > threshold)[0]
    cols = np.where(mask.mean(axis=0) > threshold)[0]
    if not len(rows) or not len(cols):
        raise SystemExit("no chromatic content found; is this the right image?")
    box = [cols[0] * decimation, rows[0] * decimation,
           (cols[-1] + 1) * decimation, (rows[-1] + 1) * decimation]

    # Pass 2: full-resolution strips around each edge, for exact pixels.
    pad = decimation * 64

    def edge(axis: int, guess: int, take_last: bool) -> int:
        lo = max(0, guess - pad)
        hi = min(width if axis else height, guess + pad)
        if axis:  # vertical edge: scan columns
            arr = ds.ReadAsArray(lo, box[1], hi - lo, box[3] - box[1])
            frac = chromatic(arr).mean(axis=0)
        else:  # horizontal edge: scan rows
            arr = ds.ReadAsArray(box[0], lo, box[2] - box[0], hi - lo)
            frac = chromatic(arr).mean(axis=1)
        hits = np.where(frac > threshold)[0]
        return lo + (hits[-1] + 1 if take_last else hits[0])

    left = edge(1, box[0], False)
    right = edge(1, box[2], True)
    top = edge(0, box[1], False)
    bottom = edge(0, box[3], True)

    print(f"  neatline pixels : ({left}, {top})-({right}, {bottom}) of {width} x {height}")
    print(f"  margins dropped : left {left}, top {top}, right {width - right}, "
          f"bottom {height - bottom}")

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
    p.add_argument("--lossy", action="store_true",
                   help="lossy WebP: roughly a quarter the size, but lossy "
                        "compression rings around hairlines and text, which is "
                        "most of what an aeronautical chart is made of")
    p.add_argument("--quality", type=int, default=95,
                   help="quality for --lossy, 1-100 (default: %(default)s). "
                        "95 is visually close; below about 90 the linework suffers")
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
    print("[1/3] georeferencing")
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
    print("[2/3] neatline")
    if args.no_crop:
        bbox = None
        print("  cropping disabled; the printed margin will be tiled too")
    elif args.detect_neatline:
        bbox = detect_neatline(COMBINED)
        print(f"  measured: {tuple(round(v, 3) for v in bbox)}")
    else:
        bbox = NEATLINE_LCC
        print(f"  using stored constant: {bbox}")

    # -- stage 3: tile -----------------------------------------------------
    print("[3/3] tiling")
    if args.dry_run:
        print("  --dry-run: stopping here")
        print(f"    output   {args.out}")
        print(f"    format   {args.tile_format}"
              f"{' lossy q' + str(args.quality) if args.lossy else ' lossless'}")
        print(f"    scheme   {args.scheme}")
        print(f"    zooms    {args.min_zoom}..{args.max_zoom or 'auto'}")
        print(f"    bbox     {bbox if bbox else 'none (whole sheet)'}")
        return 0

    result = build_tileset(
        COMBINED,
        args.out,
        bbox=bbox,
        # The neatline is a rectangle in the chart's own projection, not in
        # lon/lat, so the crop has to be expressed there.
        bbox_crs="source",
        scheme=args.scheme,
        min_zoom=args.min_zoom,
        max_zoom=args.max_zoom,
        tile_format=args.tile_format,
        lossless=not args.lossy,
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
    print(result.summary())
    print()
    print(f"preview it with:  .venv/Scripts/cesiumtiles-serve {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
