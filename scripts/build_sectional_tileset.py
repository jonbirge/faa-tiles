#!/usr/bin/env python
"""Mosaic every FAA VFR sectional into one Cesium tileset.

    .venv/Scripts/python scripts/build_sectional_tileset.py [--out DIR] [options]

Stages, each its own script so it can be rerun alone:

  1. fetch_sectionals.py         download the current edition's GeoTIFFs into
                                 ./sectionals
  2. detect_sectional_areas.py   find each sheet's map area (and hand-authored
                                 inset cut-outs) into sectional_areas.json;
                                 rerun and review for every new edition
  3. this script                 mosaic the sheets into z/x/y tiles

Overlaps are resolved by file name: sheets are painted in lexicographic order,
so where two overlap, the one later in the alphabet is on top. That is a
placeholder for a smarter rule, not a considered choice.

Max zoom is z12. The finest sheet (the 1:250,000 Honolulu inset, 21 m/px) would
ask for z13, which quadruples the tileset for one small inset; everything else
reaches its native resolution by z12 (the lower 48 at ~z11.6, Alaska ~z11).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from cesiumtiles.mosaic import MapArea, MosaicSource, build_mosaic  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_sectionals import EXCLUDE  # noqa: E402

SECTIONALS = REPO / "sectionals"
MANIFEST = Path(__file__).resolve().parent / "sectional_areas.json"
OUTPUT = REPO / "tileset-sectionals"

MAX_ZOOM = 12
QUALITY = 90  # lossy WebP: these tilesets are large, and q90 keeps chart type legible


def sources(sectionals: Path, manifest: dict) -> list[MosaicSource]:
    # Excluded charts are not normally downloaded, but an older download may
    # have left them behind; they must not reach the tileset either way.
    charts = sorted(p for p in sectionals.glob("*.tif") if p.name not in EXCLUDE)
    if not charts:
        raise SystemExit(f"no GeoTIFFs in {sectionals}; run scripts/fetch_sectionals.py first")
    missing = [p.name for p in charts if p.name not in manifest]
    if missing:
        raise SystemExit(
            "no map area recorded for: " + ", ".join(missing)
            + "\nrun scripts/detect_sectional_areas.py and review its contact sheets first"
        )
    return [MosaicSource(p, MapArea.from_dict(manifest[p.name])) for p in charts]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUTPUT, help=f"output tileset (default {OUTPUT.name})")
    ap.add_argument("--sectionals", type=Path, default=SECTIONALS, help="directory of sectional GeoTIFFs")
    ap.add_argument("--max-zoom", type=int, default=MAX_ZOOM)
    ap.add_argument("--min-zoom", type=int, default=0)
    ap.add_argument("--quality", type=int, default=QUALITY)
    ap.add_argument("--workers", type=int, default=None, help="render processes (default: all cores)")
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="build from just these charts (name prefixes, e.g. Denver Albuquerque)")
    ap.add_argument("--resume", action="store_true", help="keep tiles already written")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing tileset")
    args = ap.parse_args(argv)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    chosen = sources(args.sectionals, manifest)
    if args.only:
        chosen = [s for s in chosen if any(Path(s.path).name.startswith(n) for n in args.only)]
        if not chosen:
            raise SystemExit(f"--only matched no charts: {args.only}")

    result = build_mosaic(
        chosen, args.out,
        min_zoom=args.min_zoom, max_zoom=args.max_zoom, quality=args.quality,
        workers=args.workers, resume=args.resume, overwrite=args.overwrite,
        title="FAA VFR Sectionals",
    )
    print(result.summary())
    print(f"preview it with:  .venv/Scripts/cesiumtiles-serve {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
