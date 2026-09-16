#!/usr/bin/env python
"""Find each IFR enroute chart's map frame and write it to the area manifest.

    .venv/Scripts/python scripts/detect_ifr_areas.py [SERIES] [--sheet DIR] [CHART ...]

SERIES defaults to ``ifr-low``. The sectional detector does not work here: it
finds the map where the paper collar ends, and an IFR chart's map is itself
mostly white paper.

What IFR charts do have is a drawn frame. Every sheet encloses its map in a
heavy black rule, ~8 px wide, top, bottom, left and right, with the lettered
grid ticks and legend panels outside it. Legend tables are ruled too, but with
1-2 px lines. So each side of the map is the one run of fully dark, *thick*
rows (or columns) across the middle of the sheet, and the map area is the
rectangle just inside them. That is a measurement, not a fit.

Some sheets carry a second framed panel beside the main map -- L-23 has a
"Wilmington - Bimini Inset" strip down its left side, at its own scale and so
not georeferenced with the sheet. Consecutive thick rules bound panels, so on
each axis the widest panel is taken as the map and the rest are reported as
dropped. A sheet with fewer than two thick rules on an axis is reported and left
out of the manifest rather than guessed at.

The map area is written to ``scripts/<series>_areas.json`` as that chart's
``include``. Hand-authored keys are never touched: ``exclude`` polygons, and
``"manual": true``, which skips the chart. ``--sheet DIR`` writes contact sheets
with each map area outlined, for review.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from osgeo import gdal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart_series import series  # noqa: E402

gdal.UseExceptions()

DARK = 110          # every channel below this counts as ink
FULL = 0.9          # fraction of the middle of the sheet a frame rule must cover
                    # (L-34's right rule is crossed by something and reads 0.94)
THICK = 6           # pixels; frame rules are 6-10 (L-12 has 6), legend column rules 5, table rules 1-2
MIDDLE = (0.3, 0.7) # the span a rule is measured across, clear of corners
INSET = 12          # pixels moved inside the rule, past its anti-aliased edge


def _ink(dataset) -> np.ndarray:
    mask = None
    for b in range(1, min(3, dataset.RasterCount) + 1):
        band = dataset.GetRasterBand(b).ReadAsArray() < DARK
        mask = band if mask is None else (mask & band)
    return mask


def _thick_rules(fraction: np.ndarray) -> list[tuple[int, int]]:
    """(first, last) index of every run of fully dark lines at least THICK wide."""
    idx = np.nonzero(fraction >= FULL)[0]
    runs = []
    for i in idx:
        if runs and i - runs[-1][1] <= 1:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    return [(a, b) for a, b in runs if b - a + 1 >= THICK]


def detect(path: Path) -> tuple[list[list[int]] | None, str]:
    """The map frame's interior as a pixel polygon, or None and the reason."""
    dataset = gdal.Open(str(path))
    ink = _ink(dataset)
    height, width = ink.shape
    lo, hi = MIDDLE
    rows = _thick_rules(ink[:, int(width * lo):int(width * hi)].mean(axis=1))
    cols = _thick_rules(ink[int(height * lo):int(height * hi), :].mean(axis=0))
    if len(rows) < 2 or len(cols) < 2:
        return None, f"no frame: {len(rows)} thick horizontal and {len(cols)} thick vertical rules"
    (top, bottom), dropped_rows = _widest_panel(rows)
    (left, right), dropped_cols = _widest_panel(cols)
    x0, y0, x1, y1 = left + 1 + INSET, top + 1 + INSET, right - INSET, bottom - INSET
    report = (f"frame x {left}..{right}, y {top}..{bottom}; map {x1 - x0}x{y1 - y0} px "
              f"({100 * (x1 - x0) * (y1 - y0) / (width * height):.0f}% of sheet)")
    dropped = [f"x {a}..{b}" for a, b in dropped_cols] + [f"y {a}..{b}" for a, b in dropped_rows]
    if dropped:
        report += "; dropped framed panel(s) " + ", ".join(dropped)
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], report


def _widest_panel(rules):
    """The widest gap between consecutive rules, as (inner edge, inner edge),
    and every other gap wide enough to be a panel rather than a doubled rule."""
    gaps = [(int(a[1]), int(b[0])) for a, b in zip(rules, rules[1:])]
    widest = max(gaps, key=lambda g: g[1] - g[0])
    others = [g for g in gaps if g != widest and g[1] - g[0] > 1000]
    return widest, others


def contact_sheets(chart_series, manifest: dict, out_dir: Path, width: int = 400, per_sheet: int = 20) -> None:
    from PIL import Image, ImageDraw

    out_dir.mkdir(parents=True, exist_ok=True)
    names = sorted(manifest)
    for sheet in range(0, len(names), per_sheet):
        thumbs = []
        for name in names[sheet:sheet + per_sheet]:
            dataset = gdal.Open(str(chart_series.directory / name))
            scale = width / dataset.RasterXSize
            small = gdal.Translate("", dataset, format="MEM", width=width, resampleAlg="average")
            image = Image.fromarray(small.ReadAsArray()[:3].transpose(1, 2, 0))
            draw = ImageDraw.Draw(image)
            for polygon in manifest[name].get("include", []):
                points = [(x * scale, y * scale) for x, y in polygon["pixel"]]
                draw.line(points + points[:1], fill=(255, 0, 255), width=2)
            for polygon in manifest[name].get("exclude", []):
                points = [(x * scale, y * scale) for x, y in polygon["pixel"]]
                draw.line(points + points[:1], fill=(255, 140, 0), width=2)
            draw.text((4, 4), name, fill=(255, 0, 0))
            thumbs.append(image)
        cols = 4
        cell = max(t.height for t in thumbs)
        canvas = Image.new("RGB", (width * cols, cell * ((len(thumbs) + cols - 1) // cols)), (80, 80, 80))
        for i, thumb in enumerate(thumbs):
            canvas.paste(thumb, ((i % cols) * width, (i // cols) * cell))
        target = out_dir / f"{chart_series.name}-areas-{sheet // per_sheet}.png"
        canvas.save(target)
        print(f"wrote {target}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", nargs="?", default="ifr-low")
    ap.add_argument("charts", nargs="*", help="chart file names to detect (default: all)")
    ap.add_argument("--sheet", type=Path, help="write review contact sheets into this directory")
    ap.add_argument("--no-detect", action="store_true", help="only draw contact sheets")
    args = ap.parse_args(argv)
    chart_series = series(args.series)

    path = chart_series.manifest
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    names = args.charts or sorted(p.name for p in chart_series.directory.glob("*.tif")
                                  if chart_series.wants_tif(p.name))

    failed = 0
    if not args.no_detect:
        for name in names:
            entry = manifest.setdefault(name, {})
            if entry.get("manual"):
                print(f"{name}: manual, skipped")
                continue
            points, report = detect(chart_series.directory / name)
            if points is None:
                failed += 1
                entry.pop("include", None)
                print(f"!! {name}: {report}", flush=True)
            else:
                entry["include"] = [{"pixel": points}]
                print(f"{'??' if 'dropped' in report else '  '} {name}: {report}", flush=True)
        ordered = {k: manifest[k] for k in sorted(manifest) if manifest[k]}
        path.write_text(json.dumps(ordered, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {path}; {failed} chart(s) need a look")

    if args.sheet:
        contact_sheets(chart_series, {k: v for k, v in manifest.items() if v}, args.sheet)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
