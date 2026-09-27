#!/usr/bin/env python
"""Georeference the scans of a chart series by the graticule printed on them.

    .venv/Scripts/python scripts/rectify_charts.py SERIES [SHEET ...] [--workers N] [--force]
    .venv/Scripts/python scripts/rectify_charts.py SERIES --review DIR
    .venv/Scripts/python scripts/rectify_charts.py SERIES --apply READINGS.json

SERIES is a scanned series from chart_series.py (``onc``, ``tpc``): library
scans of paper charts, with no georeferencing in them. Each is registered by its
graticule (``graticule.py``) and written as a GeoTIFF in the chart's own
projection to ``source/SERIES/rectified/``, which the later stages read like any
other series' downloads.

**What has to be reviewed is the sheet index**, ``scripts/SERIES_sheets.json``.
The graticule says where a scan's lines are and how many there are; it cannot
say which is which, because a graticule looks the same one interval along. That
comes from the labels printed at the sheet's corner, and they have to be read.
The published indexes do not serve: they gave TPC E-2A as starting at 1 52' W,
and the sheet says 1. So:

1. ``--review DIR`` surveys every scan and draws the corner of each -- the end
   parallel and the end meridian of its graticule, marked, with the labels
   beside them -- six to a page, and writes ``readings.json`` with what the
   index would have said, for comparison.
2. Someone reads the labels and fills the readings in.
3. ``--apply READINGS.json`` writes them into the sheet index, which is
   committed. A sheet is rectified only once it has a reading, unless
   ``--trust-index`` says its nominal limits will do.

**The scans are not rigid**: a scanner's feed slips, and a sheet can be 3.5%
longer at one end than the other. So a scan is not given an affine but warped,
through a thin-plate spline tied down at every crossing of a meridian and a
parallel -- a hundred or two to a sheet. Crossings that disagree with a smooth
surface through the rest are left out first; a spline passes through every
point it is given, the wrong ones included.

**The map area is the graticule's**, written as limits in degrees to
``rectified/areas.json``: from the first line of each family to the last, or to
the neatline where one was found outside them. A sheet is printed past its
neatline to overlap its neighbours, and that overlap is given up beyond the last
graticule line; the neighbour has it.
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
from osgeo import gdal, osr
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graticule  # noqa: E402
from chart_series import SERIES, series  # noqa: E402

gdal.UseExceptions()
Image.MAX_IMAGE_PIXELS = None        # these are scans of whole sheets

SCRIPT = "rectify_charts.py"
AREAS = "areas.json"
REPORT = "report.json"

# The rectified rasters are intermediates of scans that were JPEGs to begin
# with; lossless copies of them would be ten times the size for nothing.
CREATION = ["COMPRESS=JPEG", "JPEG_QUALITY=92", "PHOTOMETRIC=YCBCR", "TILED=YES",
            "BIGTIFF=IF_SAFER"]
# How far inside its limits a sheet's map area is drawn, in pixels of the scan:
# the limit is a ruled line, and the line is not map.
INSET = 4.0
# A crossing further than this from a smooth surface through the others, in
# pixels, was measured on the wrong line.
OUTLIER = 8.0
# Review pages: cells across and down, and the size of a cell in scan pixels.
PAGE = (2, 3)
CELL = (1000, 500)


def load_index(chart_series) -> dict:
    path = chart_series.sheet_index
    if not path.is_file():
        raise SystemExit(f"{chart_series.name} has no sheet index at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def crs_for(band, longitude: float) -> str:
    """The projection of a sheet in the latitude band ``band``: Lambert
    conformal conic with its standard parallels 1 degree 20 minutes inside the
    band, which is printed on the sheets. The central meridian is the sheet's
    own; any would do, and this one keeps north up."""
    south, north = band
    return (f"+proj=lcc +lat_1={south + 4 / 3:.6f} +lat_2={north - 4 / 3:.6f} "
            f"+lat_0={(south + north) / 2:.6f} +lon_0={longitude:.6f} +datum=WGS84 +units=m "
            "+no_defs")


def reading_of(entry) -> graticule.Reading | None:
    read = entry.get("read")
    if not read:
        return None
    return graticule.Reading(read["parallel_end"], float(read["parallel"]),
                             read["meridian_end"], float(read["meridian"]))


def sheet_for(stem: str, entry: dict, index: dict) -> graticule.Sheet:
    """What is known of a sheet before its scan is looked at."""
    south, north = entry["band"]
    read = entry.get("read")
    if read:
        longitude, latitude = float(read["meridian"]), float(read["parallel"])
    elif entry.get("limits_from"):
        longitude = (entry["west"] + entry["east"]) / 2
        latitude = (entry["south"] + entry["north"]) / 2
    else:
        # Only the row is known. A TPC is a quarter of its ONC: A and B the
        # northern half of the band, C and D the southern.
        longitude = 0.0
        quarter = stem[-1] if stem[-1] in "abcd" and "-" in stem else ""
        latitude = {"a": north - 2, "b": north - 2, "c": south + 2, "d": south + 2}.get(
            quarter, (south + north) / 2)
    limits = ({side: entry[side] for side in ("west", "south", "east", "north")}
              if entry.get("limits_from") else {})
    return graticule.Sheet(name=stem, crs=crs_for(entry["band"], longitude),
                           interval=index["interval"], pixel_size=index["pixel_size"],
                           middle=(longitude, latitude), **limits)


def read_scan(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


# -- rectifying -------------------------------------------------------------

def consistent(control: np.ndarray, project) -> np.ndarray:
    """The control points that lie on one smooth surface.

    A cubic in the projected coordinates is fitted to the columns and to the
    rows, the points furthest from it are dropped and it is fitted again. What
    a scanner does to a sheet is smooth -- a stretch that comes and goes over
    hundreds of pixels -- so a point several pixels from the surface is a
    crossing measured on the wrong line, not a kink in the paper.
    """
    projected = project(control[:, 2:4])
    centre = projected.mean(axis=0)
    scale = np.ptp(projected, axis=0).max() / 2
    u, v = ((projected - centre) / scale).T
    design = np.stack([u ** i * v ** j for i in range(4) for j in range(4 - i)], axis=1)
    kept = np.ones(len(control), bool)
    for _ in range(6):
        if kept.sum() < design.shape[1] + 4:
            break
        misfit = np.zeros(len(control))
        for axis in (0, 1):
            solution, *_ = np.linalg.lstsq(design[kept], control[kept, axis], rcond=None)
            misfit = np.hypot(misfit, design @ solution - control[:, axis])
        again = misfit <= max(OUTLIER, 3.0 * np.sqrt(np.mean(misfit[kept] ** 2)))
        if (again == kept).all():
            break
        kept = again
    return kept


def limits_of(registration: graticule.Registration) -> dict:
    """A sheet's map area as limits in degrees: its graticule's end lines, or
    the neatline where one was found outside them, drawn in by INSET."""
    size = registration.pixel_size
    metres = INSET * (np.nanmean(size) if np.isfinite(size).any() else 100.0)
    lat = float(np.mean([line.value for line in registration.parallels]))
    d_lat = metres / 111_000.0
    d_lon = d_lat / max(0.1, math.cos(math.radians(lat)))
    meridians = [line.value for line in registration.meridians]
    parallels = [line.value for line in registration.parallels]
    found = registration.neatlines
    return {
        "west": round(min(min(meridians), found.get("west", math.inf)) + d_lon, 5),
        "east": round(max(max(meridians), found.get("east", -math.inf)) - d_lon, 5),
        "south": round(min(min(parallels), found.get("south", math.inf)) + d_lat, 5),
        "north": round(max(max(parallels), found.get("north", -math.inf)) - d_lat, 5),
    }


def rectify(scan: Path, out: Path, registration: graticule.Registration, limits: dict) -> dict:
    """Warp a scan into its projection through its control points."""
    sheet = registration.sheet
    project = graticule.Projector(sheet.crs)
    control = registration.control
    kept = consistent(control, project)
    control = control[kept]
    projected = project(control[:, 2:4])
    gcps = [gdal.GCP(float(x), float(y), 0.0, float(column), float(row))
            for (column, row), (x, y) in zip(control[:, :2], projected)]
    srs = osr.SpatialReference()
    srs.SetFromUserInput(sheet.crs)

    # The output covers the map area and a little more, square to the projection.
    edge = []
    for t in np.linspace(0, 1, 60):
        lon = limits["west"] + t * (limits["east"] - limits["west"])
        lat = limits["south"] + t * (limits["north"] - limits["south"])
        edge += [(lon, limits["south"]), (lon, limits["north"]),
                 (limits["west"], lat), (limits["east"], lat)]
    corners = project(edge)
    pixel = float(np.nanmean(registration.pixel_size))
    pad = 12 * pixel
    bounds = (corners[:, 0].min() - pad, corners[:, 1].min() - pad,
              corners[:, 0].max() + pad, corners[:, 1].max() + pad)

    source = gdal.Translate("", str(scan), format="VRT", GCPs=gcps, outputSRS=srs.ExportToWkt())
    part = out.with_name(out.name + ".part.tif")
    gdal.Warp(str(part), source, format="GTiff", tps=True, dstSRS=srs.ExportToWkt(),
              xRes=pixel, yRes=pixel, outputBounds=bounds, resampleAlg="cubic",
              dstNodata=None, creationOptions=CREATION, multithread=True)
    part.replace(out)
    return {"control": int(len(control)), "dropped": int((~kept).sum()), "pixel": round(pixel, 3)}


def work(task):
    """Register and rectify one sheet. Returns ``(stem, outcome)``; never raises."""
    stem, scan, out, entry, index, trust_index = task
    started = time.monotonic()
    try:
        reading = reading_of(entry)
        if reading is None and not trust_index:
            return stem, {"skipped": "no reading; run --review, read the labels, and --apply"}
        sheet = sheet_for(stem, entry, index)
        registration = graticule.register(read_scan(Path(scan)), sheet, reading)
        if len(registration.control) < 9:
            return stem, {"failed": "; ".join(registration.problems)}
        limits = limits_of(registration)
        done = rectify(Path(scan), Path(out), registration, limits)
        return stem, {
            **done, "limits": limits, "labelled_by": list(registration.labelled_by),
            "distortion_rms": round(registration.distortion_rms, 1),
            "distortion_max": round(registration.distortion_max, 1),
            "rotation": round(registration.rotation, 3),
            "problems": registration.problems,
            "seconds": round(time.monotonic() - started),
        }
    except Exception as exc:                       # one bad scan must not stop the rest
        return stem, {"failed": f"{type(exc).__name__}: {exc}"}


# -- review -----------------------------------------------------------------

def corner(found: graticule.Survey):
    """Which end of each family to read, and the scan window that shows both
    end lines and the labels printed beside them.

    An end with a margin beyond it is chosen over one the map runs off, because
    a sheet's labels are printed in its margin: south over north, west over
    east, if both have one.
    """
    def has_margin(side):
        return side in found.neatline or found.stops[side][1] >= graticule.MARGIN

    parallel_end = "south" if has_margin("south") or not has_margin("north") else "north"
    meridian_end = "west" if has_margin("west") or not has_margin("east") else "east"
    parallel = found.end_line(parallel_end)
    meridian = found.end_line(meridian_end)
    at = graticule.crossing(parallel, meridian)
    if at is None:
        row = parallel.at(found.along_x)
        at = (meridian.at(row), row)
    x, y = at
    width, height = CELL
    # The labels are printed in the margin, beside where the two end lines
    # meet: below and to the left of a south-western corner. So the corner sits
    # off-centre in the window, with the larger part of it given to the margin.
    left = x - (0.4 if meridian_end == "west" else 0.6) * width
    top = y - (0.45 if parallel_end == "south" else 0.55) * height
    left = int(max(0, min(found.width - width, left)))
    top = int(max(0, min(found.height - height, top)))
    return parallel_end, meridian_end, (left, top, left + width, top + height)


def draw_cell(rgb: np.ndarray, found: graticule.Survey, caption: str):
    parallel_end, meridian_end, window = corner(found)
    left, top, right, bottom = window
    cell = Image.fromarray(np.ascontiguousarray(rgb[top:bottom, left:right])).convert("RGBA")
    marks = Image.new("RGBA", cell.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(marks)
    parallel = found.end_line(parallel_end)
    meridian = found.end_line(meridian_end)
    # Drawn over the lines themselves, thin and see-through, and only inside
    # the map, so that no label is covered.
    draw.line([(a - left, b - top) for a, b in zip(parallel.along, parallel.across)],
              fill=(255, 0, 0, 130), width=5)
    draw.line([(b - left, a - top) for a, b in zip(meridian.along, meridian.across)],
              fill=(0, 90, 255, 130), width=5)
    cell = Image.alpha_composite(cell, marks).convert("RGB")
    draw = ImageDraw.Draw(cell)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    box = draw.textbbox((0, 0), caption, font=font)
    draw.rectangle((0, 0, box[2] + 16, box[3] + 12), fill=(255, 255, 160))
    draw.text((8, 4), caption, fill=(0, 0, 0), font=font)
    return cell, parallel_end, meridian_end


def survey_one(task):
    stem, scan, entry, index = task
    try:
        sheet = sheet_for(stem, entry, index)
        rgb = read_scan(Path(scan))
        found = graticule.survey(rgb, sheet)
        nominal = ""
        if entry.get("limits_from"):
            nominal = (f"  index ({entry['limits_from']}): W {entry['west']:g}  S {entry['south']:g}"
                       f"  E {entry['east']:g}  N {entry['north']:g}")
        cell, parallel_end, meridian_end = draw_cell(
            rgb, found, f"{entry.get('title', stem)}  [{stem}]{nominal}")
        return stem, {
            "parallel_end": parallel_end, "parallel": None,
            "meridian_end": meridian_end, "meridian": None,
            "parallels": len(found.parallels), "meridians": len(found.meridians),
            "neatline": {side: round(value, 2) for side, value in found.neatline.items()},
        }, cell
    except Exception as exc:
        return stem, {"failed": f"{type(exc).__name__}: {exc}"}, None


def review(chart_series, index, scans, out_dir: Path, workers: int) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = [(stem, str(path), index["sheets"][stem], index) for stem, path in scans]
    readings, cells = {}, []
    started = time.monotonic()
    with mp.get_context("spawn").Pool(workers) as pool:
        for done, (stem, outcome, cell) in enumerate(pool.imap(survey_one, tasks), 1):
            readings[stem] = outcome
            if cell is not None:
                cells.append((stem, cell))
            if done % 20 == 0 or done == len(tasks):
                print(f"  surveyed {done}/{len(tasks)}, "
                      f"{(time.monotonic() - started) / 60:.1f} min", flush=True)
    across, down = PAGE
    per_page = across * down
    for page in range(0, len(cells), per_page):
        sheet = Image.new("RGB", (across * CELL[0], down * CELL[1]), "white")
        for i, (stem, cell) in enumerate(cells[page:page + per_page]):
            sheet.paste(cell, ((i % across) * CELL[0], (i // across) * CELL[1]))
            readings[stem]["page"] = page // per_page
        sheet.save(out_dir / f"corners-{page // per_page:03d}.jpg", quality=88)
    (out_dir / "readings.json").write_text(json.dumps(readings, indent=1) + "\n",
                                           encoding="utf-8", newline="\n")
    failed = [stem for stem, outcome in readings.items() if "failed" in outcome]
    print(f"wrote {math.ceil(len(cells) / per_page)} pages and readings.json to {out_dir}")
    if failed:
        print(f"{len(failed)} scan(s) could not be surveyed: {', '.join(failed[:20])}"
              + (" ..." if len(failed) > 20 else ""))
    return 0


def apply_readings(chart_series, index, path: Path) -> int:
    readings = json.loads(path.read_text(encoding="utf-8"))
    applied = 0
    for stem, read in readings.items():
        if stem not in index["sheets"]:
            raise SystemExit(f"{stem} is not a sheet of {chart_series.name}")
        if read.get("parallel") is None or read.get("meridian") is None:
            continue
        entry = index["sheets"][stem]
        entry["read"] = {"parallel_end": read["parallel_end"], "parallel": float(read["parallel"]),
                         "meridian_end": read["meridian_end"], "meridian": float(read["meridian"])}
        if "crown" in read:
            entry["crown"] = bool(read["crown"])
        applied += 1
    chart_series.sheet_index.write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8",
                                        newline="\n")
    print(f"{applied} reading(s) written to {chart_series.sheet_index}")
    return 0


# -- main -------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", choices=sorted(n for n, s in SERIES.items() if s.scan_suffix))
    ap.add_argument("sheets", nargs="*", help="sheets to do, by file stem (default: all)")
    ap.add_argument("--workers", type=int, default=8,
                    help="scans worked on at once; each holds its scan several times over "
                         "in memory, about 2 GB (default: %(default)s)")
    ap.add_argument("--force", action="store_true", help="redo sheets that are up to date")
    ap.add_argument("--review", type=Path, metavar="DIR",
                    help="draw every sheet's corner into DIR for its labels to be read")
    ap.add_argument("--apply", type=Path, metavar="READINGS",
                    help="write the readings in this file into the sheet index")
    ap.add_argument("--trust-index", action="store_true",
                    help="label sheets that have no reading from their nominal limits. The "
                         "indexes are not to be relied on; this is for a trial")
    args = ap.parse_args(argv)
    chart_series = series(args.series)
    index = load_index(chart_series)
    if args.apply:
        return apply_readings(chart_series, index, args.apply)

    in_dir = chart_series.input_directory(SCRIPT)
    out_dir = chart_series.rectified_directory
    scans = sorted((p.stem, p) for p in in_dir.glob(f"*{chart_series.scan_suffix}")
                   if chart_series.wants_tif(f"{p.stem}.tif") and p.stem in index["sheets"])
    unknown = sorted(p.stem for p in in_dir.glob(f"*{chart_series.scan_suffix}")
                     if p.stem not in index["sheets"])
    if unknown:
        print(f"not in the sheet index, and left alone: {', '.join(unknown)}")
    if args.sheets:
        scans = [(stem, path) for stem, path in scans if stem in args.sheets]
    if not scans:
        raise SystemExit(f"no scans in {in_dir}; run scripts/fetch_charts.py "
                         f"{chart_series.name} first")
    if args.review:
        return review(chart_series, index, scans, args.review, args.workers)

    out_dir.mkdir(parents=True, exist_ok=True)
    report_path, areas_path = out_dir / REPORT, out_dir / AREAS
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    tasks = []
    for stem, scan in scans:
        out = out_dir / f"{stem}.tif"
        current = (out.is_file() and out.stat().st_mtime >= scan.stat().st_mtime
                   and report.get(stem, {}).get("read") == index["sheets"][stem].get("read")
                   and "limits" in report.get(stem, {}))
        if args.force or not current:
            tasks.append((stem, str(scan), str(out), index["sheets"][stem], index,
                          args.trust_index))
    print(f"{len(tasks)} of {len(scans)} sheet(s) to rectify -> {out_dir}", flush=True)

    started = time.monotonic()
    with mp.get_context("spawn").Pool(max(1, min(args.workers, len(tasks) or 1))) as pool:
        for done, (stem, outcome) in enumerate(pool.imap_unordered(work, tasks), 1):
            outcome["read"] = index["sheets"][stem].get("read")
            report[stem] = outcome
            state = ("skipped: " + outcome["skipped"] if "skipped" in outcome
                     else "FAILED: " + outcome["failed"] if "failed" in outcome
                     else f"{outcome['control']} control points, scanner distortion "
                          f"{outcome['distortion_rms']} px rms"
                          + (f"; {'; '.join(outcome['problems'])}" if outcome["problems"] else ""))
            print(f"  [{done}/{len(tasks)}] {stem}: {state}", flush=True)
            if done % 10 == 0:
                report_path.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                                       encoding="utf-8", newline="\n")

    report_path.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                           encoding="utf-8", newline="\n")
    areas = {f"{stem}.tif": {"limits": outcome["limits"]}
             for stem, outcome in sorted(report.items())
             if "limits" in outcome and (out_dir / f"{stem}.tif").is_file()}
    areas_path.write_text(json.dumps(areas, indent=1) + "\n", encoding="utf-8", newline="\n")
    failed = sorted(stem for stem, outcome in report.items() if "failed" in outcome)
    skipped = sorted(stem for stem, outcome in report.items() if "skipped" in outcome)
    print(f"{len(areas)} sheet(s) rectified, {len(skipped)} without a reading, "
          f"{len(failed)} failed, in {(time.monotonic() - started) / 60:.1f} min")
    if failed:
        print("failed: " + ", ".join(failed), file=sys.stderr)
    # Sheets that could not be done are reported, not fatal: the series is a
    # gap filler, and the sheets that did register are worth having.
    return 0


if __name__ == "__main__":
    sys.exit(main())
