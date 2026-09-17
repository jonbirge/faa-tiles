#!/usr/bin/env python
"""Mosaic every sheet of an FAA chart series into one Cesium tileset.

    .venv/Scripts/python scripts/build_chart_tileset.py SERIES [--out DIR] [options]

SERIES is a name from chart_series.py (``sectionals``, ``ifr-low``). Stages,
each its own script so it can be rerun alone:

  1. fetch_charts.py SERIES      download the current edition's GeoTIFFs into
                                 source/SERIES
  2. detect_*_areas.py           find each sheet's map area into
                                 scripts/SERIES_areas.json; rerun and review
                                 for every new edition.
                                   sectionals: detect_sectional_areas.py
                                   ifr-low:    detect_ifr_areas.py
  3. this script                 mosaic the sheets into z/x/y tiles

Overlaps are resolved by file name: sheets are painted in lexicographic order,
so where two overlap, the one later in the alphabet is on top. ``--reverse-order``
paints in reverse, putting the earliest name on top; each series sets its own
default (on for ``ifr-low``), and ``--no-reverse-order`` overrides it. Either way
it is a placeholder for a smarter rule, not a considered choice.

Tiles are lossy WebP q90 unless the series sets ``lossless`` (``ifr-low`` does);
``--[no-]lossless`` overrides it.

Max zoom is z12 for both series. For sectionals, only the 1:250,000 Honolulu
inset would ask for z13, which quadruples the tileset; for IFR low charts, the
finest sheets (the 32 m/px coastal ones) land at about z12.0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cesiumtiles.mosaic import MapArea, MosaicSource, build_mosaic  # noqa: E402
from chart_series import SERIES, series  # noqa: E402

MAX_ZOOM = 12
QUALITY = 90  # lossy WebP where a series is not lossless: large tilesets, and q90 keeps type legible


def sources(chart_series, directory: Path, manifest: dict) -> list[MosaicSource]:
    # The series' patterns and exclusions apply here too: they are not normally
    # downloaded, but an older download may have left unwanted sheets behind.
    charts = sorted(p for p in directory.glob("*.tif") if chart_series.wants_tif(p.name))
    if not charts:
        raise SystemExit(
            f"no GeoTIFFs in {directory}; run scripts/fetch_charts.py {chart_series.name} first")
    missing = [p.name for p in charts if p.name not in manifest]
    if missing:
        raise SystemExit(
            "no map area recorded for: " + ", ".join(missing)
            + "\ndetect and review map areas first (see this script's docstring)"
        )
    return [MosaicSource(p, MapArea.from_dict(manifest[p.name])) for p in charts]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", choices=sorted(SERIES))
    ap.add_argument("--out", type=Path, help="output tileset (default: tileset-SERIES)")
    ap.add_argument("--charts", type=Path,
                    help="directory of GeoTIFFs (default: source/SERIES, or its healed/ "
                         "subdirectory for a series that heals frames)")
    ap.add_argument("--max-zoom", type=int, default=MAX_ZOOM)
    ap.add_argument("--min-zoom", type=int, default=0)
    ap.add_argument("--quality", type=int, default=QUALITY, help="lossy WebP quality (default: %(default)s)")
    ap.add_argument("--lossless", action=argparse.BooleanOptionalAction, default=None,
                    help="lossless WebP tiles (default: the series' setting)")
    ap.add_argument("--workers", type=int, default=None, help="render processes (default: all cores)")
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="build from just these charts (file name prefixes)")
    ap.add_argument("--reverse-order", action=argparse.BooleanOptionalAction, default=None,
                    help="paint sheets in reverse file-name order, so the earliest name is on "
                         "top where sheets overlap (default: the series' setting)")
    ap.add_argument("--resume", action="store_true", help="keep tiles already written")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing tileset")
    args = ap.parse_args(argv)
    chart_series = series(args.series)
    out = args.out or chart_series.tileset

    manifest = json.loads(chart_series.manifest.read_text(encoding="utf-8"))
    directory = args.charts or chart_series.build_directory
    if chart_series.heal_frames and not args.charts:
        raw = sorted(p.name for p in chart_series.directory.glob("*.tif") if chart_series.wants_tif(p.name))
        stale = [n for n in raw if not (directory / n).is_file()
                 or (directory / n).stat().st_mtime < (chart_series.directory / n).stat().st_mtime]
        if stale:
            raise SystemExit(f"{len(stale)} sheet(s) not healed or out of date, e.g. {stale[0]}; "
                             f"run scripts/heal_frames.py {chart_series.name} first")
    chosen = sources(chart_series, directory, manifest)
    if args.only:
        chosen = [s for s in chosen if any(Path(s.path).name.startswith(n) for n in args.only)]
        if not chosen:
            raise SystemExit(f"--only matched no charts: {args.only}")
    reverse = chart_series.reverse_order if args.reverse_order is None else args.reverse_order
    if reverse:
        chosen.reverse()
    print(f"paint order: {'reverse ' if reverse else ''}file name, "
          f"{Path(chosen[-1].path).name} on top", flush=True)

    lossless = chart_series.lossless if args.lossless is None else args.lossless
    print(f"tiles: WebP {'lossless' if lossless else f'q{args.quality}'}", flush=True)

    result = build_mosaic(
        chosen, out,
        min_zoom=args.min_zoom, max_zoom=args.max_zoom, quality=args.quality, lossless=lossless,
        workers=args.workers, resume=args.resume, overwrite=args.overwrite,
        title=chart_series.title,
    )
    print(result.summary())
    print(f"preview it with:  .venv/Scripts/cesiumtiles-serve {out.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
