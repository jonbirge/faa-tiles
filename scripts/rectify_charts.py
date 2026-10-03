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
   ``--imprints`` draws the part of each sheet that says who produced it as
   well: the series were a joint production, and a sheet with a British,
   Australian or Canadian imprint is Crown copyright.
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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import graticule  # noqa: E402
from cesiumtiles.core import lean_workers  # noqa: E402
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
# The part of a scan that says who made the sheet: this much of it, from this
# far left of and below the south-west corner of the map. Measured on ONC J-25
# and R-8, whose titles are 1,500 px wide with the imprint in the 500 px below.
IMPRINT = (1500, 750)
IMPRINT_FROM = (-200, 40)
# Looked for in the corners of the paper instead: this much of the foot of the
# sheet, from this far in from its sides as a share of its width.
PAPER_FOOT = 1000
PAPER_INSET = 0.04


def load_index(chart_series) -> dict:
    path = chart_series.sheet_index
    if not path.is_file():
        raise SystemExit(f"{chart_series.name} has no sheet index at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# Bands reaching past this latitude are drawn on a polar stereographic
# projection, true to scale at the latitude their sheets give.
POLAR = 84.0
POLAR_TRUE_SCALE = 81 + 3 / 60


def crs_for(band, longitude: float) -> str:
    """The projection of a sheet in the latitude band ``band``: Lambert
    conformal conic with its standard parallels 1 degree 20 minutes inside the
    band, which is printed on the sheets ("Standard Parallels 73 20 and 78 40"
    on the row from 72 to 80). The central meridian is the sheet's own; any
    would do, and this one keeps north up.

    The row nearest a pole is not a cone: its sheets say "Polar Stereographic
    Projection, Scale 1:1,000,000 at 81 03".
    """
    south, north = band
    if max(abs(south), abs(north)) > POLAR:
        pole = 90 if north > 0 else -90
        return (f"+proj=stere +lat_0={pole} +lat_ts={math.copysign(POLAR_TRUE_SCALE, pole):.6f} "
                f"+lon_0={longitude:.6f} +datum=WGS84 +units=m +no_defs")
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


def _value_at(lines, along: float, across: float) -> float:
    """The longitude at a pixel, from the meridians either side of it -- or
    the latitude, from the parallels. ``lines`` are labelled lines of one
    family; ``along`` and ``across`` are the pixel in their terms. Past the end
    lines it carries on as the last two were going."""
    at = sorted((line.at(along), line.value) for line in lines)
    places = np.array([p for p, _ in at])
    values = np.array([v for _, v in at])
    if across < places[0]:
        places, values = places[:2], values[:2]
    elif across > places[-1]:
        places, values = places[-2:], values[-2:]
    else:
        return float(np.interp(across, places, values))
    return float(values[0] + (across - places[0]) * (values[1] - values[0])
                 / (places[1] - places[0]))


def _steady(x, y):
    """A line through points some of which are wild: the middle one of the
    slopes between every two, and of what is left over."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 4 or np.ptp(x) == 0:
        return 0.0, float(np.median(y))
    i, j = np.triu_indices(len(x), 1)
    apart = x[j] != x[i]
    slope = float(np.median((y[j] - y[i])[apart] / (x[j] - x[i])[apart]))
    return slope, float(np.median(y - slope * x))


def limits_of(registration: graticule.Registration) -> dict:
    """A sheet's map area as limits in degrees: the largest box of meridians
    and parallels that is map all over.

    On a side the map runs off the scan, that is the last line of the
    graticule. On a side with a margin it is where the lines crossing that
    side stop, which need not be on a line of the graticule, or the same all
    the way along: an ONC is a rectangle on the paper, ruled straight up from
    its south-west corner, and the meridian through that corner leans away
    into the map, so that the sheet reaches a quarter of a degree further west
    at its north edge than at its south. The box has to stop at the corner
    meridian. What is west of it is a wedge of map at one end and of paper at
    the other, and the sheet next door has the map.

    Where the lines stop is measured a line at a time. Mostly they stop on a
    line of the graticule, and the middle one of them says which: that is the
    limit, and a line lost under type that stops early does not move it. Where
    they do not, a steady line is put through the stops; a stop well off it
    is a line that was lost early; and the limit is the furthest in of the
    stops that are left and of the line read at the box's far corners, drawn
    in to the next line of the graticule. Drawn in, because an edge that is
    not on a line is a ruled border, and the sheets of these series are laid
    out on the graticule with their borders outside it: ONC B-2's west edge
    follows the 42nd meridian up from the south-west corner and then a rule
    to 30 E at the north, its stops read 40.6 at 73 N and westward from
    there, and the box has to stop at 42, where the sheet next door begins.
    What is drawn in is the overlap.
    """
    found = registration.survey
    size = registration.pixel_size
    pixel = float(np.nanmean(size)) if np.isfinite(size).any() else 100.0
    lat = float(np.mean([line.value for line in registration.parallels]))
    per_lat = pixel / 111_000.0
    per_lon = per_lat / max(0.1, math.cos(math.radians(lat)))
    interval = registration.sheet.interval
    meridians, parallels = registration.meridians, registration.parallels
    half = found.coarse / 2

    def margin(side):
        return side in found.neatline or found.stops[side][1] >= graticule.MARGIN

    def stops(side):
        """Where each line that crosses ``side`` stops there, as ``(pixel
        along the line, value where it stops)``."""
        crossing, across = ((parallels, meridians) if side in ("west", "east")
                            else (meridians, parallels))
        out = []
        for line in crossing:
            along = (line.along[0] - half if side in ("west", "north")
                     else line.along[-1] + half)
            out.append((along, _value_at(across, line.at(along), along)))
        return out

    def limit(side, low, high):
        """The limit on ``side`` of a box reaching from ``low`` to ``high``
        the other way."""
        lines = meridians if side in ("west", "east") else parallels
        inward = 1 if side in ("west", "south") else -1
        end = min(line.value for line in lines) if inward > 0 else max(
            line.value for line in lines)
        per = per_lon if side in ("west", "east") else per_lat
        if not margin(side):
            return end + inward * INSET * per
        stopped = stops(side)
        usual = float(np.median([where for _, where in stopped]))
        nearest = round(usual / interval) * interval
        if abs(usual - nearest) <= graticule.ON_THE_LINE * interval:
            return nearest + inward * INSET * per
        values = np.array([line.value for line in
                           (parallels if side in ("west", "east") else meridians)])
        wheres = np.array([where for _, where in stopped])
        slope, offset = _steady(values, wheres)
        off = wheres - (slope * values + offset)
        scatter = max(3 * float(np.median(np.abs(off - np.median(off)))), 2 * half * per)
        kept = list(wheres[np.abs(off) <= scatter]) + [slope * low + offset,
                                                        slope * high + offset]
        edge = float(max(kept) if inward > 0 else min(kept))
        nearest = round(edge / interval) * interval
        if abs(edge - nearest) <= graticule.ON_THE_LINE * interval:
            return nearest + inward * INSET * per
        drawn_in = (math.ceil if inward > 0 else math.floor)(edge / interval) * interval
        return drawn_in + inward * INSET * per

    lats = [line.value for line in parallels]
    lons = [line.value for line in meridians]
    south, north = limit("south", min(lons), max(lons)), limit("north", min(lons), max(lons))
    west = limit("west", max(south, min(lats)), min(north, max(lats)))
    east = limit("east", max(south, min(lats)), min(north, max(lats)))
    # Again, now that it is known how far east and west the box goes.
    south = limit("south", max(west, min(lons)), min(east, max(lons)))
    north = limit("north", max(west, min(lons)), min(east, max(lons)))
    return {"west": round(west, 5), "east": round(east, 5),
            "south": round(south, 5), "north": round(north, 5)}


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
        # Surveyed as the review surveyed it, before there was a reading.
        unread = sheet_for(stem, {k: v for k, v in entry.items() if k != "read"}, index)
        registration = graticule.register(read_scan(Path(scan)), sheet, reading,
                                          surveyed_as=unread)
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


def corner(found: graticule.Survey, avoid: dict | None = None) -> Corner:
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

    ``avoid`` names lines not to mark, as ``{"parallel": [(column, row), ...],
    "meridian": [...]}``: the lines through those pixels. It is for a second
    look at a sheet whose marked line turned out to have no label to read --
    the rule of a diagram in the margin, taken for a meridian -- and gets the
    next line in marked instead.
    """
    avoid = avoid or {}
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

    def choose(lines, side, reach, apart, avoided):
        """Which line, counted from the end, and where it stops."""
        allowed = [k for k, line in enumerate(lines)
                   if not any(abs(line.at(along) - across) < 0.3 * apart
                              for along, across in avoided)] or [0]
        if side is None:
            return allowed[0], None
        ends = [end_of(lines[k], side, found.coarse) for k in allowed[:3]]
        usual = float(np.median([along for along, _ in ends]))
        i = next((i for i, (along, _) in enumerate(ends) if abs(along - usual) <= reach / 2),
                 int(np.argmin([abs(along - usual) for along, _ in ends])))
        return allowed[i], ends[i]

    i, parallel_meets = choose(parallels, label_side[0], reach[0], reach[1],
                               [(column, row) for column, row in avoid.get("parallel", ())])
    j, meridian_meets = choose(meridians, label_side[1], reach[1], reach[0],
                               [(row, column) for column, row in avoid.get("meridian", ())])
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


def imprint_window(found: graticule.Survey):
    """The window of the scan under the south-west corner of the map, where
    these sheets print their title and, under it, who produced them; None if
    the map runs off the scan to the south and there is no margin to print in.

    The corner is where the southernmost parallel stops to the west: the
    middle one of where the three southernmost do, since a line may be lost
    before it gets there or followed on past.
    """
    if found.stops["south"][1] < graticule.MARGIN and "south" not in found.neatline:
        return None
    southern = [line for line, _ in found.parallels][::-1][:3]
    column = float(np.median([end_of(line, "west", found.coarse)[0] for line in southern]))
    row = southern[0].at(column)
    width, height = IMPRINT
    left = int(max(0, min(found.width - width, column + IMPRINT_FROM[0])))
    top = int(max(0, min(found.height - height, row + IMPRINT_FROM[1])))
    return left, top, left + width, top + height


def paper_windows(width: int, height: int):
    """The bottom corners of the paper, left and right: where to look for a
    title and imprint that are not under the corner of the map. The sheets of
    the polar rows have theirs at the foot of the legend, well clear of a map
    whose corner is half way up the sheet, and the oldest have it on the
    right."""
    wide, tall = min(IMPRINT[0], width // 2), min(PAPER_FOOT, height)
    top = height - tall
    inset = min(int(PAPER_INSET * width), width // 2 - wide)
    return ((inset, top, inset + wide, height),
            (width - inset - wide, top, width - inset, height))


def imprint_view(rgb: np.ndarray, found: graticule.Survey, where: str):
    """The part of a scan to read its imprint off, or None if there is none to
    show: under the corner of the map, or the bottom corners of the paper side
    by side."""
    if where == "paper":
        windows = paper_windows(found.width, found.height)
    else:
        windows = [w for w in (imprint_window(found),) if w is not None]
    if not windows:
        return None
    views = [Image.fromarray(np.ascontiguousarray(rgb[top:bottom, left:right]))
             for left, top, right, bottom in windows]
    view = Image.new("RGB", (sum(v.width for v in views), max(v.height for v in views)),
                     (255, 255, 160))
    across = 0
    for v in views:
        view.paste(v, (across, 0))
        across += v.width
    return view


def captioned(view: Image.Image, caption: str) -> Image.Image:
    """A view of a scan under a strip that says which sheet it is of. Under,
    not over: a caption drawn on the view covered what was to be read."""
    cell = Image.new("RGB", (view.width, view.height + CAPTION), (255, 255, 160))
    cell.paste(view, (0, CAPTION))
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    ImageDraw.Draw(cell).text((8, 4), caption, fill=(0, 0, 0), font=font)
    return cell


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


def draw_cell(rgb: np.ndarray, found: graticule.Survey, caption: str, avoid=None):
    shown = corner(found, avoid)
    views = Image.new("RGB", CELL, (255, 255, 160))
    for i, window in enumerate(shown.windows):
        views.paste(draw_panel(rgb, found, shown, window), (i * PANEL[0], 0))
    ImageDraw.Draw(views).line([(PANEL[0], 0), (PANEL[0], CELL[1])], fill=(255, 255, 160),
                               width=6)
    return captioned(views, caption), shown


def _spacing(family, reference):
    """Pixels from one line of a family to the next, in the middle of the scan."""
    at = [(line.at(reference), number) for line, number in family]
    return round(float(np.median([(b[0] - a[0]) / (b[1] - a[1]) for a, b in zip(at, at[1:])])), 1)


def survey_one(task):
    """Survey one scan for the review and keep what was found beside the
    pages: its views as images, and what was measured as ``surveyed/STEM.json``.
    Kept sheet by sheet, by the process that did the work, so that a review
    that is stopped -- 270 scans at 2 GB apiece is a long time for nothing else
    on the machine to want the memory -- has lost only the sheets in hand."""
    stem, scan, entry, index, imprints, out_dir, avoid = task
    out_dir = Path(out_dir)
    try:
        sheet = sheet_for(stem, entry, index)
        rgb = read_scan(Path(scan))
        found = graticule.survey(rgb, sheet)
        imprint = imprint_view(rgb, found, imprints) if imprints else None
        if imprint is not None:
            captioned(imprint, f"{entry.get('title', stem)}  [{stem}]").save(
                out_dir / "imprints" / f"{stem}.jpg", quality=95)
        nominal = ""
        if entry.get("limits_from"):
            nominal = (f"  index ({entry['limits_from']}): W {entry['west']:g}  S {entry['south']:g}"
                       f"  E {entry['east']:g}  N {entry['north']:g}")
        cell, shown = draw_cell(rgb, found, f"{entry.get('title', stem)}  [{stem}]{nominal}",
                                avoid)
        cell.save(out_dir / "cells" / f"{stem}.jpg", quality=95)
        outcome = {
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
            "imprint": imprint is not None,
        }
    except Exception as exc:
        outcome = {"failed": f"{type(exc).__name__}: {exc}"}
    # Last, and whole or not at all: this file is what says the sheet is done.
    kept = out_dir / "surveyed" / f"{stem}.json"
    partial = kept.with_suffix(".part")
    partial.write_text(json.dumps(outcome) + "\n", encoding="utf-8", newline="\n")
    partial.replace(kept)
    return stem, outcome


def pages(cells, out_dir: Path, name: str, readings: dict, key: str) -> int:
    """Lay cells out six to a page and write the pages; note in ``readings``
    which page each sheet is on. ``cells`` is ``(stem, image file)``. Returns
    how many pages there were."""
    across, down = PAGE
    per_page = across * down
    for stale in out_dir.glob(f"{name}-*.jpg"):
        stale.unlink()
    for first in range(0, len(cells), per_page):
        number = first // per_page
        here = [(stem, Image.open(path)) for stem, path in cells[first:first + per_page]]
        wide, tall = here[0][1].size
        page = Image.new("RGB", (across * wide, down * tall), "white")
        for i, (stem, cell) in enumerate(here):
            page.paste(cell, ((i % across) * wide, (i // across) * tall))
            readings[stem][key] = number
        page.save(out_dir / f"{name}-{number:03d}.jpg", quality=88)
    return math.ceil(len(cells) / per_page)


def review(chart_series, index, scans, out_dir: Path, workers: int,
           imprints: str = "", force: bool = False, avoid: dict | None = None) -> int:
    for directory in (out_dir, out_dir / "cells", out_dir / "imprints", out_dir / "surveyed"):
        directory.mkdir(parents=True, exist_ok=True)

    def kept(stem, scan):
        """What an earlier run found of a sheet, if its scan has not changed
        since and it looked for what this run is looking for."""
        path = out_dir / "surveyed" / f"{stem}.json"
        if force or not path.is_file() or path.stat().st_mtime < scan.stat().st_mtime:
            return None
        outcome = json.loads(path.read_text(encoding="utf-8"))
        if "failed" in outcome:
            return outcome
        if imprints and "imprint" not in outcome:
            return None
        return outcome if (out_dir / "cells" / f"{stem}.jpg").is_file() else None

    readings = {stem: kept(stem, scan) for stem, scan in scans}
    tasks = [(stem, str(scan), index["sheets"][stem], index, imprints, str(out_dir),
              (avoid or {}).get(stem))
             for stem, scan in scans if readings[stem] is None]
    print(f"{len(tasks)} of {len(scans)} sheet(s) to survey", flush=True)
    started = time.monotonic()
    if tasks:
        with mp.get_context("spawn").Pool(max(1, min(workers, len(tasks)))) as pool:
            for done, (stem, outcome) in enumerate(pool.imap_unordered(survey_one, tasks), 1):
                readings[stem] = outcome
                if done % 20 == 0 or done == len(tasks):
                    print(f"  surveyed {done}/{len(tasks)}, "
                          f"{(time.monotonic() - started) / 60:.1f} min", flush=True)

    surveyed = [stem for stem, _ in scans if "failed" not in readings[stem]]
    written = pages([(stem, out_dir / "cells" / f"{stem}.jpg") for stem in surveyed],
                    out_dir, "corners", readings, "page")
    imprinted = [(stem, out_dir / "imprints" / f"{stem}.jpg") for stem in surveyed
                 if imprints and readings[stem].get("imprint")]
    if imprinted:
        print(f"wrote {pages(imprinted, out_dir, 'imprint', readings, 'imprint_page')} pages of "
              f"imprints")
    (out_dir / "readings.json").write_text(json.dumps(readings, indent=1) + "\n",
                                           encoding="utf-8", newline="\n")
    failed = [stem for stem, outcome in readings.items() if "failed" in outcome]
    print(f"wrote {written} pages and readings.json to {out_dir}")
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
        # Who the sheet says produced it, where that was read too: what the
        # flag rests on.
        for key in ("producer", "imprint"):
            if read.get(key):
                entry[key] = read[key]
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
                         "in memory, about 1.1 GB (default: %(default)s)")
    ap.add_argument("--force", action="store_true",
                    help="redo sheets that are up to date, or with --review, already surveyed")
    ap.add_argument("--review", type=Path, metavar="DIR",
                    help="draw every sheet's corner into DIR for its labels to be read")
    ap.add_argument("--imprints", nargs="?", const="corner", default="",
                    choices=("corner", "paper"),
                    help="with --review, draw the part of every sheet that says who produced "
                         "it as well: a sheet produced outside the US is under other terms. "
                         "It is looked for under the south-west corner of the map, or with "
                         "'paper' in the bottom corners of the sheet, which is where it is on "
                         "the sheets the first does not find it on")
    ap.add_argument("--avoid", type=Path, metavar="LINES",
                    help="with --review, lines not to mark, as JSON: {sheet: {\"parallel\": "
                         "[[column, row], ...], \"meridian\": [...]}}, each the line through "
                         "that pixel of the scan. For a second look at sheets whose marked "
                         "line had no label to read")
    ap.add_argument("--apply", type=Path, metavar="READINGS",
                    help="write the readings in this file into the sheet index")
    ap.add_argument("--trust-index", action="store_true",
                    help="label sheets that have no reading from their nominal limits. The "
                         "indexes are not to be relied on; this is for a trial")
    args = ap.parse_args(argv)
    chart_series = series(args.series)
    index = load_index(chart_series)
    lean_workers()
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
        avoid = json.loads(args.avoid.read_text(encoding="utf-8")) if args.avoid else None
        return review(chart_series, index, scans, args.review, args.workers, args.imprints,
                      args.force, avoid)

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
