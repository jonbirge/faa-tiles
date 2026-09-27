"""Register a scanned chart by the graticule printed on it.

A scan of a paper chart carries no georeferencing, but it carries something
better than four corner ticks: a graticule, ruled across the whole map at a
known spacing in a known projection. This module finds it and fits the scan to
it, which is how the US military ONC and TPC sheets -- 920 scans, none
georeferenced -- get onto the globe (``georeference_charts.py``).

What is known about a sheet beforehand is a :class:`Sheet`: its projection, its
nominal neatline, the graticule spacing, and its pixel size to within a few
percent. :func:`register` then works in four steps.

1. **Coarse.** The scan is reduced to two *directional* responses, one to thin
   dark near-vertical lines and one to near-horizontal ones, and the graticule
   is correlated against them over a grid of scales and rotations. Meridians and
   parallels are searched separately, because a wrong guess at the labelling
   (below) bends the parallels' spacing and must not drag the meridians' scale
   with it.
2. **Fit.** Along every predicted line, perpendicular profiles are accumulated
   a segment at a time and the dark line found in each; an affine is fitted to
   those measurements, robustly. A measurement fixes one coordinate only -- a
   meridian says where x is, a parallel where y is -- and the two rows of the
   affine are tied softly to a similarity so neither runs off alone.
3. **Label.** A graticule looks the same one interval along, so the fit so far
   knows where the lines are but not which is which. The neatline settles it:
   the nominal west meridian is a printed line with paper beyond it, where the
   next predicted line finds nothing. Every whole-interval shift is scored that
   way on whichever sides have a margin, the best is taken, and the fit is
   redone with the right labels -- which matters, because a conic projection's
   spacing changes with latitude.
4. **Distortion.** What the affine leaves is the scanner's: sheets this size are
   fed through in passes and stitched, and the residuals run to several pixels
   in smooth waves. They are smoothed into a correction, returned as a grid of
   control points.

Nothing here reads a label off the sheet, so a nominal neatline that is wrong by
a whole interval gives a confident, wrong registration. The index the bounds
come from has to be right; ``georeference_charts.py`` cross-checks it.

numpy and GDAL only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from osgeo import osr

osr.UseExceptions()

# The directional responses pool FINE pixels across a line and COARSE along it.
# Across: wide enough that a meridian leaning a few degrees stays in one cell
# for most of a cell's length. Along: long enough that type and symbols, which
# are dark for a few pixels, average away against a line that is dark throughout.
FINE = 6
COARSE = 32
# Thin-line darkness is clipped here before pooling, so heavy black type cannot
# outweigh a hairline by being blacker.
RESPONSE_CEILING = 120.0
# Window for the local mean that "thin" is measured against, in pixels each side.
BACKGROUND = 15

# The coarse search: scale as a fraction of the sheet's stated pixel size, and
# rotation in degrees. The steps follow from FINE: a line must stay within one
# cell across over half a sheet (~4500 px), so 0.15% and 0.1 degree.
SCALE_RANGE = 0.03
SCALE_STEP = 0.0015
ROTATION_RANGE = 1.5
ROTATION_STEP = 0.1

# Spacing of the samples along a graticule line, in metres on the ground, and
# how many make one measured segment.
SAMPLE_M = 1200.0
SEGMENT = 30
# A line is found in a segment if its accumulated profile peaks this far above
# the profile's median (0..255 darkness), and this many spreads above it.
MIN_CONTRAST = 40.0
MIN_PROMINENCE = 6.0

# A line is "present" if this fraction of its segments found it, and "absent"
# below the lower figure; in between it is no evidence either way.
PRESENT = 0.5
ABSENT = 0.25
# Whole-interval relabelling shifts tried each way.
MAX_SHIFT = 8


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
    # Metres per pixel, right to within SCALE_RANGE.
    pixel_size: float


@dataclass
class Registration:
    """A sheet fitted to its graticule.

    ``affine`` maps projected metres to pixels, ``pixel = affine @ (X, Y, 1)``.
    ``control`` is the same mapping with the scanner's distortion added back,
    as rows of ``(column, row, X, Y)`` on a grid over the map.
    """

    sheet: Sheet
    affine: np.ndarray
    control: np.ndarray
    # Whole intervals the labelling was moved by, east and north positive.
    shift: tuple[int, int]
    # Root-mean-square misfit of the measurements, pixels, before and after the
    # distortion correction, as (x, y).
    rms_affine: tuple[float, float]
    rms_corrected: tuple[float, float]
    # Largest correction anywhere on the control grid, pixels.
    distortion: float
    measurements: int
    # Fraction of segments found, per line, for the nominal neatline's four
    # sides and for the lines one interval outside them.
    sides: dict = field(default_factory=dict)
    problems: list = field(default_factory=list)

    @property
    def pixel_size(self) -> tuple[float, float]:
        a = self.affine
        return 1 / math.hypot(a[0, 0], a[1, 0]), 1 / math.hypot(a[0, 1], a[1, 1])

    @property
    def rotation(self) -> float:
        """Degrees the scan is turned from the projection's north-up."""
        return math.degrees(math.atan2(-self.affine[1, 0], self.affine[0, 0]))

    @property
    def geotransform(self) -> tuple[float, ...]:
        """GDAL's pixel-to-projected transform for ``affine``."""
        full = np.vstack([self.affine, [0, 0, 1]])
        inverse = np.linalg.inv(full)
        return (inverse[0, 2], inverse[0, 0], inverse[0, 1],
                inverse[1, 2], inverse[1, 0], inverse[1, 1])

    @property
    def ok(self) -> bool:
        return not self.problems


# -- the graticule ----------------------------------------------------------

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

    def meridian(self, lon: float, south: float, north: float) -> np.ndarray:
        lat = np.arange(south, north + 1e-9, SAMPLE_M / 111_000.0)
        return self(np.c_[np.full_like(lat, lon), lat])

    def parallel(self, lat: float, west: float, east: float) -> np.ndarray:
        step = SAMPLE_M / 111_000.0 / max(0.2, math.cos(math.radians(lat)))
        lon = np.arange(west, east + 1e-9, step)
        return self(np.c_[lon, np.full_like(lon, lat)])


def _lines(project: Projector, sheet: Sheet, shift=(0, 0), reach: int = MAX_SHIFT):
    """The graticule around a sheet as ``(kind, value, xy)``, labelled as if the
    sheet's labels were ``shift`` intervals from where they are."""
    step = sheet.interval
    dx, dy = shift[0] * step, shift[1] * step
    west = math.floor(sheet.west / step) * step - reach * step
    east = math.ceil(sheet.east / step) * step + reach * step
    south = max(-89.0, math.floor(sheet.south / step) * step - reach * step)
    north = min(89.0, math.ceil(sheet.north / step) * step + reach * step)
    lons = np.arange(west, east + 1e-9, step)
    lats = np.arange(south, north + 1e-9, step)
    out = []
    for lon in lons:
        out.append(("lon", float(lon), project.meridian(lon + dx, south + dy, north + dy)))
    for lat in lats:
        if abs(lat + dy) < 89.0:
            out.append(("lat", float(lat), project.parallel(lat + dy, west + dx, east + dx)))
    return out


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


def directional(response: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """``(vertical, horizontal)``: responses to near-vertical and near-horizontal
    lines, pooled FINE across the line (max) and COARSE along it (mean)."""
    t = np.minimum(response, RESPONSE_CEILING)
    h, w = t.shape
    hv, wv = h // COARSE * COARSE, w // FINE * FINE
    vertical = t[:hv, :wv].reshape(hv // COARSE, COARSE, wv // FINE, FINE).max(axis=3).mean(axis=1)
    hh, wh = h // FINE * FINE, w // COARSE * COARSE
    horizontal = t[:hh, :wh].reshape(hh // FINE, FINE, wh // COARSE, COARSE).max(axis=1).mean(axis=2)
    return vertical, horizontal


# -- transforms -------------------------------------------------------------

def similarity(pixel_size: float, rotation: float) -> np.ndarray:
    """Projected metres to pixels, rows down, with no translation."""
    theta = math.radians(rotation)
    c, s = math.cos(theta) / pixel_size, math.sin(theta) / pixel_size
    return np.array([[c, -s, 0.0], [-s, -c, 0.0]])


def apply(affine: np.ndarray, xy: np.ndarray) -> np.ndarray:
    return xy @ affine[:, :2].T + affine[:, 2]


# -- step 1: coarse ---------------------------------------------------------

def _coarse(vertical, horizontal, lines, centre, size, pixel_size):
    """The best similarity for the meridians and for the parallels, each by
    correlation over scale and rotation, combined into one starting affine."""
    width, height = size
    meridians = np.vstack([xy for kind, _, xy in lines if kind == "lon"])
    parallels = np.vstack([xy for kind, _, xy in lines if kind == "lat"])
    searches = (
        (meridians, vertical, np.fft.rfft2(vertical), FINE, COARSE, 0),
        (parallels, horizontal, np.fft.rfft2(horizontal), COARSE, FINE, 1),
    )
    scales = np.arange(1 - SCALE_RANGE, 1 + SCALE_RANGE + 1e-9, SCALE_STEP)
    rotations = np.arange(-ROTATION_RANGE, ROTATION_RANGE + 1e-9, ROTATION_STEP)
    best = [None, None]
    for scale in scales:
        for rotation in rotations:
            affine = similarity(pixel_size * scale, rotation)
            at = apply(affine, np.array([centre]))[0]
            affine[:, 2] = (width / 2 - at[0], height / 2 - at[1])
            for points, response, spectrum, fx, fy, axis in searches:
                rows, columns = response.shape
                p = apply(affine, points)
                px, py = p[:, 0] / fx, p[:, 1] / fy
                inside = (px >= 0) & (px < columns) & (py >= 0) & (py < rows)
                if inside.sum() < 50:
                    continue
                template = np.zeros((rows, columns), np.float32)
                template[py[inside].astype(int), px[inside].astype(int)] = 1.0
                correlation = np.fft.irfft2(spectrum * np.conj(np.fft.rfft2(template)),
                                            s=response.shape)
                # A shift along the lines says nothing; allow a cell or two of it.
                if axis == 0:
                    correlation[3:-2, :] = -np.inf
                else:
                    correlation[:, 3:-2] = -np.inf
                iy, ix = np.unravel_index(np.argmax(correlation), correlation.shape)
                score = correlation[iy, ix] / template.sum()
                if best[axis] is None or score > best[axis][0]:
                    dx = (ix if ix <= columns // 2 else ix - columns) * fx
                    dy = (iy if iy <= rows // 2 else iy - rows) * fy
                    moved = affine.copy()
                    moved[:, 2] += (dx, dy)
                    best[axis] = (score, moved)
    if best[0] is None or best[1] is None:
        raise ValueError("no graticule line falls inside the image; check the sheet's bounds "
                         "and pixel size")
    return np.vstack([best[0][1][0], best[1][1][1]]), (best[0][0], best[1][0])


# -- step 2: measure and fit ------------------------------------------------

def measure(dark: np.ndarray, affine: np.ndarray, lines, reach: int, along: int = 3):
    """Where each predicted line really is, a segment at a time.

    Returns rows of ``(X, Y, measured coordinate, axis, line index, offset)``:
    ``axis`` is 0 where the measurement is of x (a meridian) and 1 of y (a
    parallel), and ``offset`` is how far the line was from its prediction.
    Also returns the number of segments each line offered.
    """
    height, width = dark.shape
    margin = reach + along + 2
    offsets = np.arange(-reach, reach + 1)
    found, offered = [], []
    for index, (kind, _value, xy) in enumerate(lines):
        p = apply(affine, xy)
        inside = ((p[:, 0] > margin) & (p[:, 0] < width - margin)
                  & (p[:, 1] > margin) & (p[:, 1] < height - margin))
        indices = np.flatnonzero(inside)
        count = 0
        for start in range(0, len(indices) - SEGMENT + 1, SEGMENT):
            segment = indices[start:start + SEGMENT]
            if segment[-1] - segment[0] != SEGMENT - 1:
                continue        # the line left the image and came back
            count += 1
            xs = np.round(p[segment, 0]).astype(int)
            ys = np.round(p[segment, 1]).astype(int)
            if kind == "lon":
                profiles = np.stack([dark[y - along:y + along + 1, x - reach:x + reach + 1].mean(axis=0)
                                     for x, y in zip(xs, ys)])
            else:
                profiles = np.stack([dark[y - reach:y + reach + 1, x - along:x + along + 1].mean(axis=1)
                                     for x, y in zip(xs, ys)])
            # The median across the segment: a line is dark in most of its
            # profiles, type and symbols crossing it are dark in a few.
            profile = np.median(profiles, axis=0)
            base = np.median(profile)
            spread = np.median(np.abs(profile - base)) + 1.0
            peak = int(np.argmax(profile))
            rise = profile[peak] - base
            if rise < MIN_CONTRAST or rise / spread < MIN_PROMINENCE:
                continue
            lo, hi = max(0, peak - 3), min(len(profile), peak + 4)
            weight = np.clip(profile[lo:hi] - base, 0, None)
            offset = float((offsets[lo:hi] * weight).sum() / weight.sum())
            middle = segment[len(segment) // 2]
            predicted = p[middle, 0] if kind == "lon" else p[middle, 1]
            found.append((xy[middle, 0], xy[middle, 1], predicted + offset,
                          0 if kind == "lon" else 1, index, offset))
        offered.append(count)
    return np.array(found, float).reshape(-1, 6), np.array(offered)


def fit(measurements: np.ndarray, tie: float):
    """An affine through the measurements, its rows tied towards a similarity.

    ``x = aX + bY + c`` takes the meridians' measurements and ``y = dX + eY + f``
    the parallels'. ``tie`` weights two soft constraints, ``a = -e`` and
    ``b = d``, which hold exactly for a similarity with rows counted downward.
    Measurements further than 2.5 standard deviations are dropped and the fit
    repeated. Returns ``(affine, kept, residuals)``.
    """
    X, Y, target, axis = measurements[:, 0], measurements[:, 1], measurements[:, 2], measurements[:, 3]
    unit = 1e5      # metres, so the unknowns are all of order one
    rows = np.zeros((len(target), 6))
    is_x = axis == 0
    rows[is_x, 0], rows[is_x, 1], rows[is_x, 2] = X[is_x] / unit, Y[is_x] / unit, 1
    rows[~is_x, 3], rows[~is_x, 4], rows[~is_x, 5] = X[~is_x] / unit, Y[~is_x] / unit, 1
    ties = np.array([[tie, 0, 0, 0, tie, 0], [0, tie, 0, -tie, 0, 0]], float)
    kept = np.ones(len(target), bool)
    for _ in range(10):
        solution, *_ = np.linalg.lstsq(np.vstack([rows[kept], ties]),
                                       np.r_[target[kept], 0, 0], rcond=None)
        residuals = rows @ solution - target
        again = np.abs(residuals) < max(2.5 * residuals[kept].std(), 1.5)
        if (again == kept).all():
            break
        kept = again
    affine = np.array([[solution[0] / unit, solution[1] / unit, solution[2]],
                       [solution[3] / unit, solution[4] / unit, solution[5]]])
    return affine, kept, residuals


def _refine(dark, affine, lines, schedule):
    for reach, tie in schedule:
        measurements, _ = measure(dark, affine, lines, reach)
        if (measurements[:, 3] == 0).sum() < 6 or (measurements[:, 3] == 1).sum() < 6:
            raise ValueError("too few graticule lines were found to fit the sheet")
        affine, kept, residuals = fit(measurements, tie)
    return affine, measurements, kept, residuals


# -- step 3: labelling ------------------------------------------------------

def _found(dark, affine, line, reach=8) -> tuple[float, int]:
    """Fraction of one line's segments in which a line is found, and how many
    segments it offered."""
    measurements, offered = measure(dark, affine, [line], reach)
    return (len(measurements) / offered[0] if offered[0] else 0.0), int(offered[0])


def _side_scores(dark, affine, project: Projector, sheet: Sheet, shift=(0, 0)):
    """How the nominal neatline fares on each side, and the line an interval
    beyond it, under labels moved by ``shift``.

    The lines are placed by ``affine``, which was fitted with the labels where
    they were assumed to be; moving the labels by ``shift`` means the nominal
    west meridian is looked for where the fit drew ``west - shift``.
    """
    step = sheet.interval
    dx, dy = shift[0] * step, shift[1] * step
    pad = MAX_SHIFT * step
    south, north = sheet.south - pad, sheet.north + pad
    west, east = sheet.west - pad, sheet.east + pad
    south, north = max(-89.0, south), min(89.0, north)
    out = {}
    for side, value, outward in (("west", sheet.west, -1), ("east", sheet.east, +1)):
        at = value - dx
        line = ("lon", at, project.meridian(at, south, north))
        beyond = ("lon", at + outward * step, project.meridian(at + outward * step, south, north))
        out[side] = (_found(dark, affine, line), _found(dark, affine, beyond))
    for side, value, outward in (("south", sheet.south, -1), ("north", sheet.north, +1)):
        at = value - dy
        if abs(at) >= 89.0 or abs(at + outward * step) >= 89.0:
            out[side] = ((0.0, 0), (0.0, 0))
            continue
        line = ("lat", at, project.parallel(at, west, east))
        beyond = ("lat", at + outward * step, project.parallel(at + outward * step, west, east))
        out[side] = (_found(dark, affine, line), _found(dark, affine, beyond))
    return out


def _axis_shift(dark, affine, project, sheet, axis: int):
    """The whole-interval shift along one axis that puts the neatline where the
    paper begins, with the evidence for it.

    Scored on each side that has a margin: the nominal line found, and the one
    an interval outside it not. A side where the map runs off the scan -- charts
    bleed past their neatline to overlap their neighbours, usually north and
    east -- has no "outside", and is left out. Returns ``(shift, score, sides
    used)``; the score is None if neither side could be judged.
    """
    names = ("west", "east") if axis == 0 else ("south", "north")
    candidates = []
    for k in range(-MAX_SHIFT, MAX_SHIFT + 1):
        shift = (k, 0) if axis == 0 else (0, k)
        sides = _side_scores(dark, affine, project, sheet, shift)
        score, used = 0.0, []
        for name in names:
            (line, offered), (beyond, offered_beyond) = sides[name]
            if offered < 3 or offered_beyond < 3:
                continue        # off the scan: no evidence from this side
            score += line - beyond
            used.append(name)
        if used:
            candidates.append((score / len(used), -abs(k), k, used))
    if not candidates:
        return 0, None, []
    score, _, k, used = max(candidates)
    return k, score, used


# -- step 4: distortion -----------------------------------------------------

def _smooth(points: np.ndarray, values: np.ndarray, nodes: np.ndarray, width: float) -> np.ndarray:
    """Gaussian-weighted local means of scattered ``values`` at ``nodes``.
    Where no value is within reach, the correction tails off to nothing."""
    if len(points) == 0:
        return np.zeros(len(nodes))
    out = np.empty(len(nodes))
    for i, node in enumerate(nodes):
        d2 = ((points - node) ** 2).sum(axis=1)
        weight = np.exp(-d2 / (2 * width * width))
        # One notional measurement of zero keeps a node far from any data at zero.
        out[i] = (weight * values).sum() / (weight.sum() + 0.5)
    return out


def _control(affine, measurements, kept, residuals, size, spacing, width):
    """Control points on a grid over the scan: where the affine puts each node,
    moved by the smoothed residual there."""
    columns, rows = size
    inverse = np.linalg.inv(np.vstack([affine, [0, 0, 1]]))
    grid_x = np.arange(0, columns + spacing, spacing, dtype=float)
    grid_y = np.arange(0, rows + spacing, spacing, dtype=float)
    pixels = np.array([(x, y) for y in grid_y for x in grid_x])
    projected = pixels @ inverse[:2, :2].T + inverse[:2, 2]

    where = apply(affine, measurements[:, :2])
    # residuals are fitted minus measured, so the true pixel is fitted - residual
    is_x = (measurements[:, 3] == 0) & kept
    is_y = (measurements[:, 3] == 1) & kept
    dx = _smooth(where[is_x], -residuals[is_x], pixels, width)
    dy = _smooth(where[is_y], -residuals[is_y], pixels, width)
    control = np.c_[pixels[:, 0] + dx, pixels[:, 1] + dy, projected]
    return control, dx, dy


def _rms(values) -> float:
    return float(np.sqrt(np.mean(np.square(values)))) if len(values) else float("nan")


# -- the whole thing --------------------------------------------------------

def register(rgb: np.ndarray, sheet: Sheet) -> Registration:
    """Fit a scanned sheet to its graticule. ``rgb`` is ``(rows, columns, 3)``."""
    dark = darkness(rgb)
    height, width = dark.shape
    project = Projector(sheet.crs)
    centre = project([((sheet.west + sheet.east) / 2, (sheet.south + sheet.north) / 2)])[0]

    lines = _lines(project, sheet)
    vertical, horizontal = directional(thin(dark))
    affine, _scores = _coarse(vertical, horizontal, lines, centre, (width, height),
                              sheet.pixel_size)
    # Loosely tied at first: the labels may be out, which bends the parallels'
    # spacing away from the meridians'.
    affine, *_ = _refine(dark, affine, lines, ((16, 3.0), (12, 3.0), (8, 3.0)))

    shift_x, score_x, used_x = _axis_shift(dark, affine, project, sheet, 0)
    shift_y, score_y, used_y = _axis_shift(dark, affine, project, sheet, 1)
    shift = (shift_x, shift_y)
    problems = []
    if score_x is None:
        problems.append("no margin west or east: the longitude labelling is unchecked")
    elif score_x < PRESENT - ABSENT:
        problems.append(f"the west/east neatline was not found clearly (score {score_x:.2f})")
    if score_y is None:
        problems.append("no margin south or north: the latitude labelling is unchecked")
    elif score_y < PRESENT - ABSENT:
        problems.append(f"the south/north neatline was not found clearly (score {score_y:.2f})")

    # The fit drew the line it called L where the sheet prints L + shift. So the
    # affine wanted draws every point where the old one drew the point a shift
    # back, which a grid of points over the sheet pins down.
    if shift != (0, 0):
        lon, lat = np.meshgrid(np.linspace(sheet.west, sheet.east, 12),
                               np.linspace(sheet.south, sheet.north, 12))
        points = np.c_[lon.ravel(), lat.ravel()]
        back = points - (shift_x * sheet.interval, shift_y * sheet.interval)
        target = apply(affine, project(back))
        design = np.c_[project(points), np.ones(len(points))]
        affine = np.vstack([np.linalg.lstsq(design, target[:, 0], rcond=None)[0],
                            np.linalg.lstsq(design, target[:, 1], rcond=None)[0]])
    affine, measurements, kept, residuals = _refine(
        dark, affine, lines, ((16, 3.0), (10, 30.0), (8, 30.0), (8, 30.0)))

    is_x, is_y = measurements[:, 3] == 0, measurements[:, 3] == 1
    rms_affine = (_rms(residuals[kept & is_x]), _rms(residuals[kept & is_y]))

    spacing = max(width, height) / 24
    smoothing = 0.6 * sheet.interval * 111_000.0 / sheet.pixel_size
    control, dx, dy = _control(affine, measurements, kept, residuals, (width, height),
                               spacing, smoothing)
    # What is left once the correction is applied, measured at the measurements.
    where = apply(affine, measurements[:, :2])
    left_x = -residuals[kept & is_x] - _smooth(where[kept & is_x], -residuals[kept & is_x],
                                                where[kept & is_x], smoothing)
    left_y = -residuals[kept & is_y] - _smooth(where[kept & is_y], -residuals[kept & is_y],
                                                where[kept & is_y], smoothing)

    sides = {name: {"line": round(line, 2), "beyond": round(beyond, 2),
                    "segments": offered, "segments_beyond": offered_beyond}
             for name, ((line, offered), (beyond, offered_beyond))
             in _side_scores(dark, affine, project, sheet).items()}
    if kept.sum() < 60:
        problems.append(f"only {int(kept.sum())} measurements fit")
    if max(rms_affine) > 8.0:
        problems.append(f"the affine misfit is {max(rms_affine):.1f} px")

    return Registration(
        sheet=sheet, affine=affine, control=control, shift=shift,
        rms_affine=rms_affine, rms_corrected=(_rms(left_x), _rms(left_y)),
        distortion=float(np.hypot(dx, dy).max()), measurements=int(kept.sum()),
        sides=sides, problems=problems,
    )
