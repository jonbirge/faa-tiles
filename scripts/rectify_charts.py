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

1. ``--review DIR`` surveys every scan and marks a parallel in red and a
   meridian in blue, shows each where it meets the edge of the map and its
   label is printed, six sheets to a page, and writes ``readings.json`` with
   the pixel of each scan where its two marked lines cross.
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
from typing import NamedTuple

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
# Review pages: cells across and down, the size of a cell in scan pixels, and
# the height of the strip above each that names the sheet. Above, not over: a
# caption drawn on the cell covered the very label it was there to have read.
PAGE = (2, 3)
CELL = (1000, 500)
CAPTION = 40
# A cell is two views side by side: the parallel's label, then the meridian's.
PANEL = (CELL[0] // 2, CELL[1])


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
    return graticule.Reading(float(read["column"]), float(read["row"]),
                             float(read["parallel"]), float(read["meridian"]))


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

class Corner(NamedTuple):
    """The two lines marked for reading: where they cross in the scan, the
    window of the scan in which each one's label is looked for (the parallel's,
    then the meridian's), the end of each family they were counted from and how
    many lines in from it."""

    parallel: graticule.Line
    meridian: graticule.Line
    at: tuple[float, float]
    windows: tuple[tuple[int, int, int, int], tuple[int, int, int, int]]
    ends: tuple[str, str]
    steps: tuple[int, int]
    # Where each line stops at the edge of the map, ``(column, row)``, or None
    # for one whose ends both run off the scan.
    meets: tuple


def end_of(line: graticule.Line, side: str, coarse: int) -> tuple[float, float]:
    """Where a traced line stops on ``side``, as ``(along, across)`` of the
    line. A chain's end mark is the middle of the last strip the line filled;
    the line itself went on about half a strip."""
    if side in ("west", "north"):
        along = line.along[0] - coarse / 2
    else:
        along = line.along[-1] + coarse / 2
    return float(along), line.at(along)


def corner(found: graticule.Survey) -> Corner:
    """The two lines to read, where they cross, and where to look for the label
    of each.

    A line's label is printed in the margin where the line meets the edge of
    the map, so that is what is shown: the parallel where it stops to the west,
    or to the east if the map runs off the scan to the west, and the meridian
    where it stops to the south, or the north. The first round of reading
    showed one window about where the two lines cross, which is the same place
    only if the edge of the map is a meridian. On an ONC it is not: the map is
    a rectangle on the paper, its west edge is ruled straight up from the
    south-west corner, and north of the equator the meridian through that
    corner leans away from it into the map.

    The lines are the end ones, south and west for choice, unless one stops
    half an interval from where the next two in do, short or past. A line is
    lost under type before it reaches the edge, and on ONC L-3 one was followed
    out of the map along a line of the notes printed beside it.
    """
    def has_margin(side):
        return side in found.neatline or found.stops[side][1] >= graticule.MARGIN

    def first_with_margin(sides):
        return next((side for side in sides if has_margin(side)), None)

    parallel_end = first_with_margin(("south", "north")) or "south"
    meridian_end = first_with_margin(("west", "east")) or "west"
    # The side a parallel's label is on is the end the meridians are counted
    # from, and the other way about.
    label_side = (first_with_margin(("west", "east")), first_with_margin(("south", "north")))
    parallels = [line for line, _ in found.parallels]
    meridians = [line for line, _ in found.meridians]
    if parallel_end == "south":
        parallels = parallels[::-1]
    if meridian_end == "east":
        meridians = meridians[::-1]
    reach = (_spacing(found.meridians, found.along_y), _spacing(found.parallels, found.along_x))

    def choose(lines, side, reach):
        if side is None:
            return 0, None
        ends = [end_of(line, side, found.coarse) for line in lines[:3]]
        usual = float(np.median([along for along, _ in ends]))
        i = next((i for i, (along, _) in enumerate(ends) if abs(along - usual) <= reach / 2),
                 int(np.argmin([abs(along - usual) for along, _ in ends])))
        return i, ends[i]

    i, parallel_meets = choose(parallels, label_side[0], reach[0])
    j, meridian_meets = choose(meridians, label_side[1], reach[1])
    parallel, meridian = parallels[i], meridians[j]
    # Where the two cross, or would if they were traced that far.
    column = float(meridian.across.mean())
    for _ in range(6):
        row = parallel.at(column)
        column = meridian.at(row)
    at = (float(column), float(row))

    def window(centre):
        width, height = PANEL
        left = int(max(0, min(found.width - width, centre[0] - width / 2)))
        top = int(max(0, min(found.height - height, centre[1] - height / 2)))
        return left, top, left + width, top + height

    meets = (parallel_meets,
             None if meridian_meets is None else (meridian_meets[1], meridian_meets[0]))
    return Corner(parallel, meridian, at,
                  (window(meets[0] or at), window(meets[1] or at)),
                  (parallel_end, meridian_end), (i, j), meets)


def draw_panel(rgb: np.ndarray, found: graticule.Survey, shown: Corner, window):
    """A window of the scan with the two lines marked over it, each as far as
    it was traced: not on across the margin, where its label is."""
    left, top, right, bottom = window
    view = Image.fromarray(np.ascontiguousarray(rgb[top:bottom, left:right])).convert("RGBA")
    marks = Image.new("RGBA", view.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(marks)
    half = found.coarse / 2
    # Drawn over the lines themselves, thin and see-through, so that nothing
    # printed is covered.
    for line, low, high, colour, as_point in (
            (shown.parallel, left, right, (255, 0, 0, 130), lambda a, b: (a - left, b - top)),
            (shown.meridian, top, bottom, (0, 90, 255, 130), lambda a, b: (b - left, a - top))):
        start, stop = max(low, line.along[0] - half), min(high, line.along[-1] + half)
        if stop - start < 2:
            continue
        along = np.linspace(start, stop, max(2, int((stop - start) / 8)))
        draw.line([as_point(a, line.at(a)) for a in along], fill=colour, width=5)
    return Image.alpha_composite(view, marks).convert("RGB")


def draw_cell(rgb: np.ndarray, found: graticule.Survey, caption: str):
    shown = corner(found)
    cell = Image.new("RGB", (CELL[0], CELL[1] + CAPTION), (255, 255, 160))
    for i, window in enumerate(shown.windows):
        cell.paste(draw_panel(rgb, found, shown, window), (i * PANEL[0], CAPTION))
    draw = ImageDraw.Draw(cell)
    draw.line([(PANEL[0], CAPTION), (PANEL[0], CELL[1] + CAPTION)], fill=(255, 255, 160), width=6)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    draw.text((8, 4), caption, fill=(0, 0, 0), font=font)
    return cell, shown


def _spacing(family, reference):
    """Pixels from one line of a family to the next, in the middle of the scan."""
    at = [(line.at(reference), number) for line, number in family]
    return round(float(np.median([(b[0] - a[0]) / (b[1] - a[1]) for a, b in zip(at, at[1:])])), 1)


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
        cell, shown = draw_cell(rgb, found, f"{entry.get('title', stem)}  [{stem}]{nominal}")
        return stem, {
            "column": round(shown.at[0], 1), "row": round(shown.at[1], 1),
            "parallel": None, "meridian": None,
            # For whoever compares a reading with the index: which lines these
            # are, as the survey counted them. Nothing downstream relies on it.
            "parallel_from": [shown.ends[0], shown.steps[0]],
            "meridian_from": [shown.ends[1], shown.steps[1]],
            "parallels": len(found.parallels), "meridians": len(found.meridians),
            "spacing": [_spacing(found.parallels, found.along_x),
                        _spacing(found.meridians, found.along_y)],
            "ink": [round(float(np.median([line.ink for line, _ in family])))
                    for family in (found.parallels, found.meridians)],
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
    tall = CELL[1] + CAPTION
    for page in range(0, len(cells), per_page):
        sheet = Image.new("RGB", (across * CELL[0], down * tall), "white")
        for i, (stem, cell) in enumerate(cells[page:page + per_page]):
            sheet.paste(cell, ((i % across) * CELL[0], (i // across) * tall))
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
        entry["read"] = {"column": float(read["column"]), "row": float(read["row"]),
                         "parallel": float(read["parallel"]),
                         "meridian": float(read["meridian"])}
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
