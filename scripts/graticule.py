"""Register a scanned chart by the graticule printed on it.

A scan of a paper chart carries no georeferencing, but it carries something
better than four corner ticks: a graticule, ruled across the whole map at a
known spacing in a known projection. This module finds it, which is how the US
military ONC and TPC sheets -- 920 scans, none georeferenced -- get onto the
globe (``georeference_charts.py``).

**The scans are not rigid copies of the paper.** Sheets this size are fed
through a scanner, and the feed slips: on one sample the parallels are 682 px
apart at the top of the scan and 706 px at the bottom, a 3.5% stretch that no
projection explains and no affine can follow. A first version fitted one
similarity to the whole graticule and lost half of that sheet. So nothing here
assumes the scan has one scale. Each printed line is traced where it is, and
the scan is tied down at every place two of them cross:

1. **Trace.** The scan is cut into strips across the lines. In each strip a
   graticule line is a thin dark mark at one place, there in most of the
   strip's width, where type and symbols are dark in a little of it. Marks are
   linked from strip to strip into chains; a chain that runs most of the way
   across the map is a printed line.
2. **Pick.** The graticule is the set of chains that are evenly spaced, at
   about the spacing the sheet's scale gives. Neatlines that fall between
   graticule lines, the rules of the sheet's border and scale bars are long
   lines too, and are left out by not fitting the rhythm.
3. **Label.** A graticule looks the same one interval along, so which line is
   which has to come from the paper. The lines of one family stop at the
   neatline: where the meridians end short of the edge of the scan, and a
   ruled line runs across their ends, that is the sheet's southern (or
   northern) limit, and the parallel there is known. A sheet is printed past
   its neatline on some sides, usually north and east, to overlap its
   neighbours; there the lines run off the paper and say nothing. A sheet with
   no neatline on either side of an axis cannot be labelled and is reported.
4. **Tie.** Every crossing of a labelled meridian and a labelled parallel is a
   control point: a place in the scan with a known longitude and latitude.

What is known about a sheet beforehand is a :class:`Sheet`: its projection, its
nominal neatline, the graticule spacing, and its pixel size to within several
percent. Nothing here reads a label off the sheet, so a nominal neatline that
is wrong by a whole interval gives a confident, wrong registration. The index
the bounds come from has to be right; ``georeference_charts.py`` cross-checks
it between neighbouring sheets.

numpy and GDAL only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from osgeo import osr

osr.UseExceptions()

# A mark is looked for in cells FINE pixels across the line and ``coarse``
# along it. Across: a line leaning a few degrees has to stay in one cell over
# the cell's length. Along: long enough that type, which is dark for a few
# pixels, is dark in the minority of a cell against a line that is dark
# throughout. ``coarse`` is chosen per sheet from how far its lines lean.
FINE = 6
COARSE = 32
MIN_COARSE = 12
# Thin-line darkness is clipped here, so heavy black type cannot outweigh a
# hairline by being blacker.
RESPONSE_CEILING = 120.0
# Window for the local mean that "thin" is measured against, pixels each side.
BACKGROUND = 15
# A cell holds a mark if its response is at least this, of RESPONSE_CEILING.
MARK = 38.0

# Linking marks into chains: how far a mark may be from where the chain was
# heading, pixels, and how many strips a chain may miss and carry on.
LINK_REACH = 5.0
LINK_GAP = 10
# The steepest a line may lean against its own axis, as a tangent. Scans are
# square to within a degree or two; the rest is the projection's convergence.
MAX_LEAN = 0.30
# A chain is a printed line if it spans this much of the scan along its length
# and has marks in this much of its span.
MIN_SPAN = 0.35
MIN_FILL = 0.5

# How far the spacing between graticule lines may be from what the sheet's
# stated scale gives, and how far it may change from one interval to the next.
SPACING_TOLERANCE = 0.10
SPACING_DRIFT = 0.045
# Lines that stop this far short of the edge of the scan, in pixels, may stop
# at a neatline; lines that run closer run off the scan.
MARGIN = 90.0
# Where lines stop is known to about a strip. Within this many intervals of a
# graticule line, they stop at that line and it is the neatline.
ON_THE_LINE = 0.15
# Further out than that the neatline is a ruled line of its own, which must
# have been traced within this many intervals of where the lines stop.
RULE_REACH = 0.12
# How far a neatline may be measured from the sheet's nominal limit, in
# intervals. The limits in the index are not the sheet's to the minute -- ONC
# J-24's southern limit is given as 15 40' for a corner of the sheet that dips
# below its neatline at 16 -- but past half an interval the graticule would be
# labelled one line out.
NEATLINE_TOLERANCE = 0.45
# A traced line is smooth. Marks further than this from a cubic through the
# line's marks, in pixels, are some other line it strayed on to.
STRAY = 5.0
# A crossing is kept if both lines have marks within this many pixels of it.
CROSSING_SUPPORT = 260.0


def _wgs84() -> osr.SpatialReference:
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


@dataclass(frozen=True)
class Sheet:
    """What is known about a scanned sheet before it is looked at."""

    name: str
    # The chart's projection, as PROJ or WKT. Its false origin is immaterial.
    crs: str
    # The nominal neatline, degrees.
    west: float
    south: float
    east: float
    north: float
    # Graticule spacing, degrees.
    interval: float
    # Metres per pixel, right to within SPACING_TOLERANCE.
    pixel_size: float


@dataclass
class Line:
    """One printed line, traced. ``along`` runs with the line -- x for a
    parallel, y for a meridian -- and ``across`` is where the line is."""

    along: np.ndarray
    across: np.ndarray
    # Degrees, once the line is labelled.
    value: float | None = None

    def at(self, along: float) -> float:
        """Where the line is at ``along``: between its marks by interpolation,
        past its ends by carrying on as its last few marks were heading."""
        if along < self.along[0] or along > self.along[-1]:
            end = slice(0, 8) if along < self.along[0] else slice(-8, None)
            if len(self.along[end]) >= 2:
                slope, offset = np.polyfit(self.along[end], self.across[end], 1)
                return float(slope * along + offset)
        return float(np.interp(along, self.along, self.across))

    def covers(self, along: float) -> bool:
        return self.along[0] <= along <= self.along[-1]

    def support(self, along: float) -> float:
        """Distance from ``along`` to the nearest mark."""
        return float(np.abs(self.along - along).min())


@dataclass
class Registration:
    """A sheet with its graticule found.

    ``control`` is rows of ``(column, row, longitude, latitude)``, one for each
    place a labelled meridian crosses a labelled parallel.
    """

    sheet: Sheet
    control: np.ndarray
    meridians: list
    parallels: list
    # The sides whose margin settled the labels, e.g. ("west", "south"), and
    # where each of those neatlines was measured to be, degrees. Coarse -- a
    # line's end is known to a strip -- but independent of the sheet's index.
    labelled_by: tuple[str, ...]
    neatlines: dict
    # The affine nearest the control points, projected metres to pixels, and
    # how far the control points are from it: what the scanner did.
    affine: np.ndarray
    distortion_rms: float
    distortion_max: float
    problems: list = field(default_factory=list)

    @property
    def pixel_size(self) -> tuple[float, float]:
        a = self.affine
        if not a.any():
            return float("nan"), float("nan")
        return 1 / math.hypot(a[0, 0], a[1, 0]), 1 / math.hypot(a[0, 1], a[1, 1])

    @property
    def rotation(self) -> float:
        """Degrees the scan is turned from the projection's north-up."""
        return math.degrees(math.atan2(-self.affine[1, 0], self.affine[0, 0]))

    @property
    def ok(self) -> bool:
        return not self.problems


class Projector:
    """Lon/lat to a sheet's projected metres."""

    def __init__(self, crs: str):
        srs = osr.SpatialReference()
        srs.SetFromUserInput(crs)
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        self.transform = osr.CoordinateTransformation(_wgs84(), srs)

    def __call__(self, lonlat) -> np.ndarray:
        points = np.asarray(lonlat, float).reshape(-1, 2)
        return np.array(self.transform.TransformPoints(points.tolist()))[:, :2]


def expected(sheet: Sheet) -> dict:
    """What the sheet's projection and stated scale say of its graticule:
    the spacing of its parallels and of its meridians in pixels, at the middle
    of the sheet, and the furthest its lines lean from the scan's axes."""
    project = Projector(sheet.crs)
    lon = (sheet.west + sheet.east) / 2
    lat = (sheet.south + sheet.north) / 2
    step = sheet.interval
    centre, north, east = project([(lon, lat), (lon, lat + step), (lon + step, lat)])
    rows = float(np.hypot(*(north - centre))) / sheet.pixel_size
    columns = float(np.hypot(*(east - centre))) / sheet.pixel_size
    # A parallel leans most at the sheet's east and west edges, by the
    # convergence there; a meridian by the same angle. A scan may be a degree
    # or two out of square on top of that.
    corner, along = project([(sheet.east, lat), (sheet.east, lat + step)])
    lean = abs(math.atan2(along[0] - corner[0], along[1] - corner[1]))
    return {"parallel": rows, "meridian": columns, "lean": math.tan(lean) + 0.035}


# -- image responses --------------------------------------------------------

def darkness(rgb: np.ndarray) -> np.ndarray:
    """How black each pixel is, 0..255. A graticule is printed in black, which
    is dark in every channel; the blue military grid beside it is not."""
    if rgb.ndim == 2:
        return (255 - rgb).astype(np.float32)
    return (255 - rgb[:, :, :3].max(axis=2)).astype(np.float32)


def thin(dark: np.ndarray) -> np.ndarray:
    """Darkness above the local mean: thin dark features, not dark areas."""
    k = BACKGROUND
    padded = np.pad(dark, k, mode="edge").astype(np.float64)
    integral = np.pad(padded.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    n = 2 * k + 1
    total = integral[n:, n:] - integral[:-n, n:] - integral[n:, :-n] + integral[:-n, :-n]
    return np.clip(dark - total / (n * n), 0, None).astype(np.float32)


def strips(response: np.ndarray, coarse: int) -> np.ndarray:
    """The response to near-horizontal lines, as ``(rows / FINE, strips)``.

    Each cell is two FINE rows deep and steps by one, so a line that drifts
    across a row boundary within a strip is still whole in one of them. Within
    a cell the response is the greatest down each column and the median across
    the columns: there in most of the strip's width, or not a line.
    """
    t = np.minimum(response, RESPONSE_CEILING)
    height, width = t.shape
    rows, columns = height // FINE, width // coarse
    cells = t[:rows * FINE, :columns * coarse].reshape(rows, FINE, columns, coarse).max(axis=1)
    deep = np.maximum(cells[:-1], cells[1:])
    return np.median(deep, axis=2)


def marks(dark: np.ndarray, response: np.ndarray, coarse: int):
    """Where thin dark near-horizontal marks are, strip by strip.

    Returns a list, one entry a strip, of ``(across, slope)`` arrays: the row
    each mark is at, to a fraction of a pixel, and how it leans there, as rows
    per column. Both are measured on the two halves of the strip separately.
    """
    found = strips(response, coarse)
    rows, columns = found.shape
    height = dark.shape[0]
    half = coarse // 2
    out = []
    for c in range(columns):
        profile = found[:, c]
        peak = (profile >= MARK)
        peak[1:] &= profile[1:] >= profile[:-1]
        peak[:-1] &= profile[:-1] > profile[1:]
        peak[2:] &= profile[2:] >= profile[:-2]
        peak[:-2] &= profile[:-2] >= profile[2:]
        here = []
        for r in np.flatnonzero(peak):
            top = max(0, r * FINE - FINE)
            bottom = min(height, r * FINE + 3 * FINE)
            window = dark[top:bottom, c * coarse:(c + 1) * coarse]
            centres = []
            for part in (window[:, :half], window[:, half:]):
                line = np.median(part, axis=1)
                weight = np.clip(line - np.median(line), 0, None)
                k = int(np.argmax(weight))
                lo, hi = max(0, k - 3), min(len(weight), k + 4)
                total = weight[lo:hi].sum()
                if total <= 0:
                    centres = None
                    break
                centres.append(top + float((np.arange(lo, hi) * weight[lo:hi]).sum() / total))
            if centres is None or abs(centres[1] - centres[0]) > MAX_LEAN * half + 2:
                continue
            here.append(((centres[0] + centres[1]) / 2, (centres[1] - centres[0]) / half))
        out.append(np.array(here, float).reshape(-1, 2))
    return out


def chains(found, coarse: int, extent: int) -> list[Line]:
    """Link marks from strip to strip into printed lines.

    ``found`` is :func:`marks`; ``extent`` is the scan's size along the lines,
    against which a chain is long or not.
    """
    open_chains: list[dict] = []
    closed: list[dict] = []
    for c, here in enumerate(found):
        centre = c * coarse + coarse / 2
        taken = np.zeros(len(here), bool)
        # Longest chains choose first: a printed line keeps its marks from a
        # stray chain that happens to pass nearby.
        for chain in sorted(open_chains, key=lambda ch: -len(ch["along"])):
            gap = c - chain["strip"]
            predicted = chain["across"][-1] + chain["slope"] * (centre - chain["along"][-1])
            reach = LINK_REACH + 1.5 * (gap - 1)
            best, distance = None, reach
            for i, (across, _slope) in enumerate(here):
                if not taken[i] and abs(across - predicted) <= distance:
                    best, distance = i, abs(across - predicted)
            if best is None:
                continue
            taken[best] = True
            chain["along"].append(centre)
            chain["across"].append(here[best, 0])
            chain["strip"] = c
            n = min(len(chain["along"]), 8)
            if n >= 3:
                chain["slope"] = float(np.polyfit(chain["along"][-n:], chain["across"][-n:], 1)[0])
            else:
                chain["slope"] = 0.5 * (chain["slope"] + here[best, 1])
        for i, (across, slope) in enumerate(here):
            if not taken[i]:
                open_chains.append({"along": [centre], "across": [across], "strip": c,
                                    "slope": float(slope)})
        still = []
        for chain in open_chains:
            (still if c - chain["strip"] <= LINK_GAP else closed).append(chain)
        open_chains = still
    closed += open_chains

    lines = []
    for chain in closed:
        along = np.array(chain["along"])
        span = along[-1] - along[0]
        if span < MIN_SPAN * extent:
            continue
        if len(along) < MIN_FILL * (span / coarse + 1):
            continue
        lines.append(Line(along, np.array(chain["across"])))
    return lines


def smooth_part(line: Line, coarse: int, extent: int) -> Line | None:
    """The line without the marks it strayed for, or None if too little is left.

    A chain follows whatever is darkest where it expects the line, and where
    the line is hidden it can take up another -- an airway, a boundary -- and
    follow that away. A printed graticule line is smooth: a cubic through its
    marks fits them to a pixel or two, scanner and all. Marks far from the
    cubic are dropped and it is fitted again, and the longest run of marks
    that remains is the line.
    """
    along, across = line.along, line.across
    centre, scale = along.mean(), max(1.0, np.ptp(along) / 2)
    unit = (along - centre) / scale
    kept = np.ones(len(along), bool)
    for _ in range(6):
        if kept.sum() < 8:
            return None
        fitted = np.polyval(np.polyfit(unit[kept], across[kept], 3), unit)
        residual = np.abs(fitted - across)
        # Drop the worst first: a stray stretch drags the cubic towards itself.
        limit = max(STRAY, np.percentile(residual[kept], 90))
        again = residual <= limit
        if (again == kept).all() and limit <= STRAY:
            break
        kept = again if limit <= STRAY else kept & (residual < limit)
    # The longest run of kept marks with no gap longer than chains allows.
    best, start = (0, 0), None
    for i in range(len(along) + 1):
        good = i < len(along) and kept[i]
        if good and start is None:
            start = i
        if start is not None and (not good or i == len(along)):
            if i - start > best[1] - best[0]:
                best = (start, i)
            start = None
    chosen = np.zeros(len(along), bool)
    chosen[best[0]:best[1]] = True
    # Marks either side of a short gap belong to the same line.
    chosen = kept & (np.abs(np.arange(len(along)) - np.clip(np.arange(len(along)),
                                                            best[0], best[1] - 1)) <= LINK_GAP)
    if chosen.sum() < 8 or np.ptp(along[chosen]) < MIN_SPAN * extent:
        return None
    return Line(along[chosen], across[chosen])


def trace(dark: np.ndarray, coarse: int) -> list[Line]:
    """The long near-horizontal printed lines of a scan."""
    extent = dark.shape[1]
    lines = chains(marks(dark, thin(dark), coarse), coarse, extent)
    return [kept for kept in (smooth_part(line, coarse, extent) for line in lines)
            if kept is not None]


# -- picking the graticule --------------------------------------------------

def rhythm(positions, step: float):
    """The largest evenly spaced subset of ``positions``.

    ``positions`` are where lines cross a reference, in order. Returns
    ``[(index into positions, interval number)]``: consecutive members are one
    interval apart, or two where a line between them was not traced. The
    spacing must be within SPACING_TOLERANCE of ``step`` and may change by no
    more than SPACING_DRIFT from one interval to the next -- a scanner's
    stretch comes on gradually, and a line that is not of the graticule breaks
    the rhythm.
    """
    n = len(positions)
    if n < 2:
        return []
    # best[(j, k)]: the longest run ending with the link j -> k, as
    # (members, -roughness, previous link, intervals in the link, spacing).
    best: dict[tuple[int, int], tuple] = {}
    for k in range(n):
        for j in range(k):
            gap = positions[k] - positions[j]
            for skipped in (1, 2):
                per = gap / skipped
                if abs(per / step - 1) > SPACING_TOLERANCE:
                    continue
                entry = (2, 0.0, None, skipped, per)
                for i in range(j):
                    before = best.get((i, j))
                    if before is None:
                        continue
                    drift = abs(per - before[4]) / step
                    if drift > SPACING_DRIFT:
                        continue
                    candidate = (before[0] + 1, before[1] - drift, (i, j), skipped, per)
                    if candidate[:2] > entry[:2]:
                        entry = candidate
                if (j, k) not in best or entry[:2] > best[(j, k)][:2]:
                    best[(j, k)] = entry
    if not best:
        return []
    link = max(best, key=lambda key: best[key][:2])
    members = []
    while link is not None:
        members.append((link[1], best[link][3]))
        previous = best[link][2]
        if previous is None:
            members.append((link[0], 0))
        link = previous
    members.reverse()
    out, number = [], 0
    for index, skipped in members:
        number += skipped
        out.append((index, number))
    return out


def pick(lines: list[Line], step: float, extent: int):
    """The graticule among the traced lines: ``[(line, interval number)]`` in
    order across the scan, and the reference they were compared along."""
    if not lines:
        return [], 0.0
    # Compare the lines where the most of them are.
    candidates = np.linspace(0.2, 0.8, 13) * extent
    reference = max(candidates, key=lambda a: sum(line.covers(a) for line in lines))
    crossing_at = sorted((line.at(reference), i) for i, line in enumerate(lines)
                         if line.covers(reference))
    chosen = rhythm([p for p, _ in crossing_at], step)
    return [(lines[crossing_at[index][1]], number) for index, number in chosen], float(reference)


def _signed(number: int, ascending: bool) -> int:
    return number if ascending else -number


def beyond(picked, others: list[Line], at_start: bool, extent: int, coarse: int):
    """How far past the end line of ``picked`` the other family's lines carry
    on, in intervals, and how far short of the edge of the scan they stop, in
    pixels.

    Measured line by line and the middle value taken: a neatline that is a
    meridian leans across the scan, so the parallels do not all begin at one
    column, and each has to be compared with the end line where it meets it.
    ``picked`` are lines of one family in order; ``others`` the lines that
    cross them.
    """
    (end_line, end_number), (next_line, next_number) = (
        (picked[0], picked[1]) if at_start else (picked[-1], picked[-2]))
    away, short = [], []
    for other in others:
        index = 0 if at_start else -1
        # A chain's first mark is the middle of the first strip the line
        # filled; the line itself began about half a strip before.
        stop = other.along[index] + (-coarse / 2 if at_start else coarse / 2)
        along = other.across[index]
        here = end_line.at(along)
        step = abs(next_line.at(along) - here) / abs(next_number - end_number)
        away.append((here - stop if at_start else stop - here) / step)
        short.append(stop if at_start else extent - stop)
    return float(np.median(away)), float(np.median(short))


def label(picked, reference: float, low: float, high: float, interval: float,
          ascending: bool, measured, traced: list[Line]):
    """Give the picked lines their values, from where the paper begins.

    ``picked`` is :func:`pick`, in order of position; ``low`` and ``high`` are
    the sheet's nominal limits on this axis. ``ascending`` says values rise
    with position: true of meridians, which run west to east, and false of
    parallels, which the scan shows north at the top. ``measured`` is
    :func:`beyond` for the start and for the end of the axis, and ``traced``
    is every long line of this family, in the graticule or not.

    A side has a neatline if the crossing lines stop short of the edge of the
    scan, and stop at a ruled line: at the end line of the graticule itself,
    or at a line traced where they stop. Otherwise the map runs off the paper
    there, and the side says nothing.

    A neatline need not be a graticule line, and a sheet's limits are not
    always what the index says. So the limit is not trusted to the minute: the
    neatline is measured against the graticule -- so many intervals outside
    the end line -- and the end line is the graticule value that puts the
    neatline nearest the nominal limit. That holds while the nominal limit is
    within half an interval of the truth.

    Returns ``(sides, neatlines, kept)``: the sides that settled it, ``"low"``
    and/or ``"high"`` in terms of value; the measured value of the neatline on
    each; and the picked lines that are inside the neatlines, now labelled.
    ``sides`` is empty if the map runs off the scan both ways.
    Raises ValueError if a neatline is far from the sheet's limit, or if two
    neatlines disagree.
    """
    if len(picked) < 2:
        raise ValueError("fewer than two graticule lines were found")
    found = {}
    for at_start, (away, short) in zip((True, False), measured):
        if short < MARGIN:
            continue                    # the lines run off the scan here
        end_line, neighbour = (picked[0], picked[1]) if at_start else (picked[-1], picked[-2])
        step = (abs(neighbour[0].at(reference) - end_line[0].at(reference))
                / abs(neighbour[1] - end_line[1]))
        outward = -1 if at_start else 1
        if away < -ON_THE_LINE:
            # The crossing lines stop inside the end line: it is a rule past
            # the neatline that fell in with the rhythm. Drop it and look again.
            rest = picked[1:] if at_start else picked[:-1]
            return label(rest, reference, low, high, interval, ascending,
                         _shifted(measured, at_start, away, end_line, rest), traced)
        if away <= ON_THE_LINE:
            found[at_start] = 0.0
            continue
        expected = end_line[0].at(reference) + outward * away * step
        rules = [abs(line.at(reference) - expected) for line in traced if line.covers(reference)]
        if rules and min(rules) <= RULE_REACH * step:
            rule = min((line for line in traced if line.covers(reference)),
                       key=lambda line: abs(line.at(reference) - expected))
            found[at_start] = abs(rule.at(reference) - end_line[0].at(reference)) / step

    numbers = [number for _, number in picked]
    offsets, neatlines = {}, {}
    for at_start, away in found.items():
        # Which limit this end of the scan is, in terms of value.
        side = "low" if at_start == ascending else "high"
        limit = low if side == "low" else high
        inward = 1 if side == "low" else -1
        value = round((limit + inward * away * interval) / interval) * interval
        at = value - inward * away * interval
        if abs(at - limit) > NEATLINE_TOLERANCE * interval:
            raise ValueError(
                f"the {side} neatline is {away:.2f} intervals outside a graticule line, "
                f"which puts it at {at:.3f}; the sheet's limit is given as {limit:g}")
        offsets[side] = value - _signed(numbers[0 if at_start else -1], ascending) * interval
        neatlines[side] = at
    if not offsets:
        return (), {}, picked
    values = list(offsets.values())
    if max(values) - min(values) > interval / 2:
        raise ValueError(
            f"the two neatlines disagree: {numbers[-1] - numbers[0]} intervals of {interval:g} "
            f"were found between the first and last lines, and the sheet's nominal limits "
            f"({low:g} to {high:g}) hold {(high - low) / interval:.2f}")
    origin = values[0]
    for line, number in picked:
        line.value = round(origin + _signed(number, ascending) * interval, 9)
    return tuple(offsets), neatlines, picked


def _shifted(measured, at_start, away, end_line, rest):
    """``measured`` with one end moved in a line: the crossing lines now stop
    that much further out, in intervals of the new end."""
    new_end, new_next = (rest[0], rest[1]) if at_start else (rest[-1], rest[-2])
    dropped = abs(new_end[1] - end_line[1])
    start, end = measured
    if at_start:
        return (start[0] + dropped, start[1]), end
    return start, (end[0] + dropped, end[1])


# -- crossings --------------------------------------------------------------

def crossing(parallel: Line, meridian: Line):
    """Where a parallel and a meridian cross, as ``(column, row)``, or None if
    either was not traced near there."""
    # A parallel gives row from column, a meridian column from row.
    column = float(meridian.across.mean())
    row = parallel.at(column)
    for _ in range(6):
        column = meridian.at(row)
        row = parallel.at(column)
    if not (parallel.covers(column) and meridian.covers(row)):
        return None
    if parallel.support(column) > CROSSING_SUPPORT or meridian.support(row) > CROSSING_SUPPORT:
        return None
    return column, row


def nearest_affine(control: np.ndarray, project: Projector):
    """The affine nearest the control points, projected metres to pixels, and
    each point's distance from it."""
    projected = project(control[:, 2:4])
    design = np.c_[projected, np.ones(len(projected))]
    rows = [np.linalg.lstsq(design, control[:, i], rcond=None)[0] for i in (0, 1)]
    affine = np.vstack(rows)
    residual = np.hypot(*(design @ affine.T - control[:, :2]).T)
    return affine, residual


def _rms(values) -> float:
    return float(np.sqrt(np.mean(np.square(values)))) if len(values) else 0.0


# -- the whole thing --------------------------------------------------------

def register(rgb: np.ndarray, sheet: Sheet, log=None) -> Registration:
    """Find a scanned sheet's graticule. ``rgb`` is ``(rows, columns, 3)``.
    ``log``, if given, is called with a line about each step."""
    say = log or (lambda *_: None)
    dark = darkness(rgb)
    height, width = dark.shape
    want = expected(sheet)
    coarse = int(max(MIN_COARSE, min(COARSE, FINE / max(want["lean"], 1e-6))))
    say(f"expecting parallels {want['parallel']:.0f} px apart and meridians "
        f"{want['meridian']:.0f} px, leaning up to "
        f"{math.degrees(math.atan(want['lean'])):.1f} degrees; strips of {coarse} px")

    problems: list[str] = []
    labelled_by: list[str] = []

    traced_rows = trace(dark, coarse)
    parallels, along_x = pick(traced_rows, want["parallel"], width)
    say(f"parallels: {len(traced_rows)} long lines traced, {len(parallels)} in the graticule, "
        f"at rows {[round(line.at(along_x)) for line, _ in parallels]}")
    # The same, with the scan on its side: a meridian is a near-horizontal line
    # of the transposed scan.
    traced_columns = trace(np.ascontiguousarray(dark.T), coarse)
    meridians, along_y = pick(traced_columns, want["meridian"], height)
    say(f"meridians: {len(traced_columns)} long lines traced, {len(meridians)} in the "
        f"graticule, "
        f"at columns {[round(line.at(along_y)) for line, _ in meridians]}")
    if len(parallels) < 2 or len(meridians) < 2:
        raise ValueError(f"too little of the graticule was found: {len(parallels)} parallels "
                         f"and {len(meridians)} meridians")

    along_columns = [line for line, _ in parallels]
    along_rows = [line for line, _ in meridians]
    north = beyond(parallels, along_rows, True, height, coarse)
    south = beyond(parallels, along_rows, False, height, coarse)
    west = beyond(meridians, along_columns, True, width, coarse)
    east = beyond(meridians, along_columns, False, width, coarse)
    say("the crossing lines stop, in intervals past the end line and pixels short of the "
        "edge: " + ", ".join(f"{name} {away:+.2f} {short:.0f}" for name, (away, short)
                             in (("north", north), ("south", south), ("west", west), ("east", east))))

    neatlines = {}
    sides, measured, parallels = label(parallels, along_x, sheet.south, sheet.north,
                                       sheet.interval, False, (north, south), traced_rows)
    if not sides:
        problems.append("no neatline south or north: the parallels cannot be labelled")
    for side in sides:
        name = "south" if side == "low" else "north"
        labelled_by.append(name)
        neatlines[name] = measured[side]
    sides, measured, meridians = label(meridians, along_y, sheet.west, sheet.east,
                                       sheet.interval, True, (west, east), traced_columns)
    if not sides:
        problems.append("no neatline west or east: the meridians cannot be labelled")
    for side in sides:
        name = "west" if side == "low" else "east"
        labelled_by.append(name)
        neatlines[name] = measured[side]
    say("neatlines measured: " + ", ".join(f"{k} {v:.3f}" for k, v in neatlines.items()))

    parallels = [line for line, _ in parallels if line.value is not None]
    meridians = [line for line, _ in meridians if line.value is not None]
    say(f"parallels {[line.value for line in parallels]}")
    say(f"meridians {[line.value for line in meridians]}")

    control = []
    for parallel in parallels:
        for meridian in meridians:
            at = crossing(parallel, meridian)
            if at is not None and 0 <= at[0] < width and 0 <= at[1] < height:
                control.append((at[0], at[1], meridian.value, parallel.value))
    control = np.array(control, float).reshape(-1, 4)
    affine, residual = np.zeros((2, 3)), np.zeros(0)
    if len(control) >= 3:
        affine, residual = nearest_affine(control, Projector(sheet.crs))
    if len(control) < 9:
        problems.append(f"only {len(control)} crossings of labelled lines were found")
    say(f"{len(control)} control points; from the nearest affine they are "
        f"{_rms(residual):.1f} px rms, {residual.max() if len(residual) else 0:.1f} px at most")

    return Registration(
        sheet=sheet, control=control, meridians=meridians, parallels=parallels,
        labelled_by=tuple(labelled_by), neatlines=neatlines, affine=affine,
        distortion_rms=_rms(residual),
        distortion_max=float(residual.max()) if len(residual) else 0.0,
        problems=problems,
    )
