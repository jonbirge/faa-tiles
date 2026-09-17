#!/usr/bin/env python
"""Paint over each sheet's frame rule, so edge-to-edge charts join without a seam.

    .venv/Scripts/python scripts/heal_frames.py SERIES [--workers N] [--force] [CHART ...]

IFR enroute charts do not overlap their neighbours; they meet at a heavy black
frame rule, and under that rule neither sheet has any map. Tiled as they are,
every shared edge becomes a black line, or a gap if the rule is cropped away.

For each sheet this writes a copy under ``source/<series>/healed/`` in which the
band between the rule's outer edge and the clean map just inside it is replaced
by repeating that clean row or column outward -- a line crossing the edge
carries straight on through, flat fills stay flat. Everything else is copied
unchanged, and only the healed strips are rewritten. The band is ~10-20 px,
roughly 0.5-1 km, per side; where two sheets meet, each fills its own half.

The frame comes from the manifest's ``frame`` entry (detect_ifr_areas.py).
A healed copy newer than its sheet is skipped unless ``--force``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from osgeo import gdal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart_series import SERIES, series  # noqa: E402

gdal.UseExceptions()

CREATION = ["COMPRESS=DEFLATE", "PREDICTOR=2", "TILED=YES", "BIGTIFF=IF_SAFER", "NUM_THREADS=2"]


def heal(source: str, target: str, frame: dict) -> str:
    gdal.UseExceptions()
    started = time.monotonic()
    src = gdal.Open(source)
    part = target + ".part"
    out = gdal.GetDriverByName("GTiff").CreateCopy(part, src, options=CREATION)
    width, height = out.RasterXSize, out.RasterYSize

    ox0, oy0, ox1, oy1 = frame["outer"]
    cx0, cy0, cx1, cy1 = frame["clean"]
    if not (0 <= ox0 < cx0 < cx1 < ox1 <= width and 0 <= oy0 < cy0 < cy1 < oy1 <= height):
        raise ValueError(f"implausible frame {frame} for a {width}x{height} sheet")

    for b in range(1, out.RasterCount + 1):
        band = out.GetRasterBand(b)
        # Columns first, across the full frame height, then rows across the full
        # frame width: the row pass copies rows whose ends were already filled,
        # so the corners come out filled too.
        rows = oy1 - oy0
        left = band.ReadAsArray(cx0, oy0, 1, rows)
        band.WriteArray(np.repeat(left, cx0 - ox0, axis=1), ox0, oy0)
        right = band.ReadAsArray(cx1 - 1, oy0, 1, rows)
        band.WriteArray(np.repeat(right, ox1 - cx1, axis=1), cx1, oy0)

        cols = ox1 - ox0
        top = band.ReadAsArray(ox0, cy0, cols, 1)
        band.WriteArray(np.repeat(top, cy0 - oy0, axis=0), ox0, oy0)
        bottom = band.ReadAsArray(ox0, cy1 - 1, cols, 1)
        band.WriteArray(np.repeat(bottom, oy1 - cy1, axis=0), ox0, cy1)
    out.FlushCache()
    del out, src
    Path(part).replace(target)
    return (f"{Path(target).name}: healed {cx0 - ox0}/{ox1 - cx1} px left/right, "
            f"{cy0 - oy0}/{oy1 - cy1} px top/bottom ({time.monotonic() - started:.0f}s)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", choices=sorted(SERIES))
    ap.add_argument("charts", nargs="*", help="chart file names (default: all)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--force", action="store_true", help="rewrite copies that are up to date")
    args = ap.parse_args(argv)
    chart_series = series(args.series)

    manifest = json.loads(chart_series.manifest.read_text(encoding="utf-8"))
    names = args.charts or sorted(p.name for p in chart_series.directory.glob("*.tif")
                                  if chart_series.wants_tif(p.name))
    missing = [n for n in names if "frame" not in manifest.get(n, {})]
    if missing:
        raise SystemExit(f"no frame recorded for {', '.join(missing)}; "
                         f"run detect_ifr_areas.py {chart_series.name} and review it first")

    out_dir = chart_series.healed_directory
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = []
    for name in names:
        source, target = chart_series.directory / name, out_dir / name
        if (not args.force and target.is_file()
                and target.stat().st_mtime >= source.stat().st_mtime
                and target.stat().st_mtime >= chart_series.manifest.stat().st_mtime):
            continue
        todo.append((str(source), str(target), manifest[name]["frame"]))
    print(f"{len(todo)} of {len(names)} sheet(s) to heal -> {out_dir}", flush=True)

    with ProcessPoolExecutor(args.workers) as pool:
        for line in pool.map(heal, *zip(*todo)) if todo else ():
            print("  " + line, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
