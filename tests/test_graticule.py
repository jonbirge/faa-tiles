"""Registering a scanned chart by its graticule, against scans drawn to order.

A real scan cannot say where its lines *ought* to be found, so these draw one:
a conic chart with a graticule, a neatline, paper round two sides and the map
running off the other two, turned a little and stretched by a scanner that
slipped. Where every crossing is, is then known.

``scripts/`` is not a package, so it goes on the path the way the scripts do.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from osgeo import osr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import graticule as g  # noqa: E402

osr.UseExceptions()

CRS = ("+proj=lcc +lat_1=49.333333 +lat_2=54.666667 +lat_0=52 +lon_0=2.5 +datum=WGS84 "
       "+units=m +no_defs")
PIXEL = 250.0          # metres; a sheet a third the size of a real scan
INTERVAL = 0.5
WEST, SOUTH = -2.0, 52.0
SIZE = (2300, 1900)    # columns, rows
PAPER = 238
SEA = (168, 198, 226)


class Scan:
    """A chart drawn into an image, and the mapping it was drawn with."""

    def __init__(self, *, rotation=0.6, stretch=0.0, west=WEST, south=SOUTH, seed=1,
                 margin_west=260, margin_south=240, clutter=True):
        self.width, self.height = SIZE
        self.west, self.south = west, south
        self.stretch = stretch
        wgs = osr.SpatialReference()
        wgs.ImportFromEPSG(4326)
        wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        srs = osr.SpatialReference()
        srs.SetFromUserInput(CRS)
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        self.forward = osr.CoordinateTransformation(wgs, srs)
        self.inverse = osr.CoordinateTransformation(srs, wgs)
        theta = math.radians(rotation)
        c, s = math.cos(theta) / PIXEL, math.sin(theta) / PIXEL
        self.affine = np.array([[c, -s, 0.0], [-s, -c, 0.0]])
        # The south-west corner of the neatline goes where the margins put it.
        corner = self.ideal([(west, south)])[0]
        self.affine[:, 2] = (margin_west - corner[0], self.height - margin_south - corner[1])
        self.rgb = self.draw(np.random.default_rng(seed), clutter)

    def ideal(self, lonlat):
        """Where the paper has a point, before the scanner."""
        xy = np.array(self.forward.TransformPoints(np.asarray(lonlat, float).tolist()))[:, :2]
        return xy @ self.affine[:, :2].T + self.affine[:, 2]

    def scanned(self, ideal):
        """Where the scanner put it: rows stretched more the further down."""
        out = np.array(ideal, float)
        out[:, 1] += self.stretch * out[:, 1] ** 2 / self.height
        return out

    def pixel(self, lonlat):
        return self.scanned(self.ideal(lonlat))

    def draw(self, rng, clutter):
        columns, rows = np.meshgrid(np.arange(self.width, dtype=float),
                                    np.arange(self.height, dtype=float))
        # Undo the scanner, then the affine, then the projection.
        a = self.stretch / self.height
        ideal_rows = rows if a == 0 else (-1 + np.sqrt(1 + 4 * a * rows)) / (2 * a)
        linear = np.linalg.inv(self.affine[:, :2])
        shifted = np.stack([columns - self.affine[0, 2], ideal_rows - self.affine[1, 2]], axis=-1)
        projected = shifted @ linear.T
        lonlat = np.array(self.inverse.TransformPoints(projected.reshape(-1, 2).tolist()))
        lon = lonlat[:, 0].reshape(rows.shape)
        lat = lonlat[:, 1].reshape(rows.shape)

        image = np.full((self.height, self.width, 3), PAPER, np.uint8)
        # Paper west and south of the neatline; the map runs off north and east.
        inside = (lon >= self.west) & (lat >= self.south)
        image[inside] = SEA
        # A line is a pixel and a bit either side of its value.
        degrees_per_pixel = PIXEL / 111_000.0
        near_lat = np.abs(lat / INTERVAL - np.round(lat / INTERVAL)) * INTERVAL
        near_lon = (np.abs(lon / INTERVAL - np.round(lon / INTERVAL)) * INTERVAL
                    * np.cos(np.radians(lat)))
        line = (near_lat < 1.3 * degrees_per_pixel) | (near_lon < 1.3 * degrees_per_pixel)
        grown = inside.copy()
        grown[:-2] |= inside[2:]
        grown[:, 2:] |= inside[:, :-2]
        # The neatline is ruled, whether or not it falls on the graticule.
        edge = ((np.abs(lat - self.south) < 1.3 * degrees_per_pixel)
                | (np.abs(lon - self.west) * np.cos(np.radians(lat)) < 1.3 * degrees_per_pixel))
        image[(line | edge) & grown] = (25, 25, 25)
        if clutter:
            # Type and symbols: short dark marks all over the map, and the blue
            # grid a military chart carries beside its graticule.
            for _ in range(1500):
                r, c = rng.integers(20, self.height - 20), rng.integers(20, self.width - 20)
                if inside[r, c]:
                    h, w = rng.integers(2, 9), rng.integers(4, 30)
                    image[r:r + h, c:c + w] = (30, 30, 40)
            diagonal = (columns * 0.97 + rows * 0.24) % 333 < 2.5
            image[diagonal & inside] = (40, 90, 200)
            # A legend box in the margin, ruled in black.
            image[self.height - 190:self.height - 187, 60:900] = 20
            image[self.height - 60:self.height - 57, 60:900] = 20
        return image

    def sheet(self, **limits):
        middle = (self.west + 4.5, self.south + 3.0)
        return g.Sheet("drawn", CRS, INTERVAL, PIXEL * 1.02, middle, **limits)


@pytest.fixture(scope="module")
def scan():
    return Scan()


@pytest.fixture(scope="module")
def registered(scan):
    return g.register(scan.rgb, scan.sheet(), g.Reading("south", SOUTH, "west", WEST))


def _drawn(scan):
    """How many crossings the scan shows: graticule values inside the map and
    inside the image."""
    lons = np.arange(scan.west - 1, scan.west + 20, INTERVAL)
    lats = np.arange(scan.south - 1, scan.south + 12, INTERVAL)
    points = np.array([(lon, lat) for lon in lons for lat in lats
                       if lon >= scan.west - 1e-9 and lat >= scan.south - 1e-9])
    at = scan.pixel(points)
    return int(((at[:, 0] > 8) & (at[:, 0] < scan.width - 8)
                & (at[:, 1] > 8) & (at[:, 1] < scan.height - 8)).sum())


def _misfit(scan, registration):
    truth = scan.pixel(registration.control[:, 2:4])
    return np.hypot(*(truth - registration.control[:, :2]).T)


def test_every_crossing_is_found_where_it_was_drawn(scan, registered):
    assert registered.ok
    # Nearly all of them: a line is not traced to the very edge of the scan.
    assert len(registered.control) >= 0.9 * _drawn(scan)
    misfit = _misfit(scan, registered)
    # The worst are at the neatline, where a line is followed a strip past its
    # last mark to meet it.
    assert misfit.max() < 2.5
    assert np.sqrt(np.mean(misfit ** 2)) < 0.8


def test_the_lines_carry_the_values_that_were_read(registered):
    parallels = [line.value for line in registered.parallels]
    meridians = [line.value for line in registered.meridians]
    # North at the top of a scan, so parallels come in falling order.
    assert parallels == sorted(parallels, reverse=True) and parallels[-1] == SOUTH
    assert meridians == sorted(meridians) and meridians[0] == WEST
    assert np.allclose(np.diff(meridians), INTERVAL) and np.allclose(np.diff(parallels), -INTERVAL)
    assert registered.labelled_by == ("read",)


def test_paper_is_told_from_the_edge_of_the_scan(registered):
    """South and west the lines stop at a neatline with paper beyond; north and
    east the map runs off the scan, and those sides say nothing."""
    assert set(registered.survey.neatline) == {"south", "west"}
    assert registered.survey.neatline["south"] == 0 and registered.survey.neatline["west"] == 0
    assert registered.neatlines == {"south": SOUTH, "west": WEST}


def test_the_scan_is_measured_not_assumed(scan, registered):
    across, down = registered.pixel_size
    assert across == pytest.approx(PIXEL, rel=0.003) and down == pytest.approx(PIXEL, rel=0.003)
    assert registered.rotation == pytest.approx(0.6, abs=0.03)
    # Drawn rigid, so the control points are an affine's to within measurement.
    assert registered.distortion_max < 3.0


def test_a_scanner_that_slipped_is_followed():
    """3% longer at the bottom than the top, as a real sample was. No affine
    fits that, and none is asked to: every crossing is found where it is."""
    scan = Scan(stretch=0.03, seed=2)
    registered = g.register(scan.rgb, scan.sheet(), g.Reading("south", SOUTH, "west", WEST))
    assert len(registered.control) >= 0.85 * _drawn(scan)
    misfit = _misfit(scan, registered)
    assert np.percentile(misfit, 95) < 1.5
    # A crossing or two at the neatline is followed less well where the rows
    # are stretching; rectify_charts.py leaves out what is not smooth.
    assert misfit.max() < 8.0
    # And the distance from the nearest affine says how far it slipped.
    assert registered.distortion_max > 4.0


def test_limits_will_do_in_place_of_a_reading_if_they_are_nearly_right(scan):
    nearly = scan.sheet(west=WEST + 0.13, south=SOUTH - 0.1, east=7.0, north=56.0)
    registered = g.register(scan.rgb, nearly)
    assert set(registered.labelled_by) == {"south", "west"}
    assert registered.parallels[-1].value == SOUTH and registered.meridians[0].value == WEST
    # The neatline is reported where it was measured, not where the index put it.
    assert registered.neatlines == {"south": SOUTH, "west": WEST}


def test_limits_a_whole_interval_out_label_the_sheet_a_line_out(scan):
    """Which is why they are not to be relied on: nothing in the scan says the
    index is wrong, and the registration is confident and mistaken."""
    wrong = scan.sheet(west=WEST - INTERVAL, south=SOUTH, east=7.0, north=56.0)
    registered = g.register(scan.rgb, wrong)
    assert registered.meridians[0].value == WEST - INTERVAL
    assert registered.ok


def test_limits_between_two_lines_are_refused(scan):
    between = scan.sheet(west=WEST + 0.24, south=SOUTH, east=7.0, north=56.0)
    with pytest.raises(ValueError, match="west neatline"):
        g.register(scan.rgb, between)


def test_a_sheet_with_no_reading_and_no_limits_is_surveyed_but_not_labelled(scan):
    registered = g.register(scan.rgb, scan.sheet())
    assert not registered.ok
    assert len(registered.control) == 0
    assert len(registered.survey.parallels) >= 8 and len(registered.survey.meridians) > 10


def test_a_reading_names_an_end_of_its_own_family(scan):
    with pytest.raises(ValueError, match="parallel is read"):
        g.register(scan.rgb, scan.sheet(), g.Reading("west", SOUTH, "west", WEST))


def test_a_neatline_between_graticule_lines_is_measured():
    """A sheet whose limits are not graticule values: the neatline is a ruled
    line of its own, a fraction of an interval outside the first line."""
    scan = Scan(west=WEST - 0.2, south=SOUTH - 0.15, seed=3)
    registered = g.register(scan.rgb, scan.sheet(), g.Reading("south", SOUTH, "west", WEST))
    assert registered.meridians[0].value == WEST and registered.parallels[-1].value == SOUTH
    assert registered.neatlines["west"] == pytest.approx(WEST - 0.2, abs=0.04)
    assert registered.neatlines["south"] == pytest.approx(SOUTH - 0.15, abs=0.04)


# -- the pieces -------------------------------------------------------------

def test_rhythm_picks_the_evenly_spaced_lines_and_counts_the_missing():
    #            a border rule          a line not traced      a neatline between lines
    positions = [40, 300, 400, 500, 601, 801, 902, 1003, 1040]
    chosen = g.rhythm(positions, 100.0)
    assert [positions[i] for i, _ in chosen] == [300, 400, 500, 601, 801, 902, 1003]
    assert [number for _, number in chosen] == [0, 1, 2, 3, 5, 6, 7]


def test_rhythm_follows_a_spacing_that_drifts_but_not_one_that_jumps():
    drifting = [0, 100, 201, 303, 406, 510]
    assert len(g.rhythm(drifting, 100.0)) == 6
    jumping = [0, 100, 200, 300, 392, 484]
    assert len(g.rhythm(jumping, 100.0)) < 6


def test_a_line_carries_on_past_its_ends_as_it_was_heading():
    along = np.arange(0.0, 1000.0, 50.0)
    line = g.Line(along, 200.0 + 0.1 * along)
    assert line.at(500.0) == pytest.approx(250.0)
    assert line.at(-100.0) == pytest.approx(190.0)
    assert line.at(1500.0) == pytest.approx(350.0)


def test_a_chain_that_strayed_loses_the_stretch_it_strayed_for():
    along = np.arange(16.0, 3200.0, 32.0)
    across = 500.0 + 0.02 * along + 1e-5 * (along - 1600) ** 2
    strayed = across.copy()
    strayed[70:] += np.linspace(0, 120, len(along) - 70)      # off along an airway
    kept = g.smooth_part(g.Line(along, strayed), 32, 3200)
    assert kept is not None
    assert kept.along[-1] < along[76]
    assert np.abs(kept.across - np.interp(kept.along, along, across)).max() < g.STRAY


def test_what_is_expected_of_a_graticule_follows_from_the_sheet(scan):
    want = g.expected(scan.sheet(), scan.width)
    # Half a degree of latitude is 55.6 km; of longitude at 55 N, 31.9 km.
    assert want["parallel"] == pytest.approx(55_660 / (PIXEL * 1.02), rel=0.01)
    assert want["meridian"] == pytest.approx(31_900 / (PIXEL * 1.02), rel=0.02)
    # A few degrees of convergence at the edge of the sheet, and a little for
    # a scan that is not square. A wider scan reaches further from the middle.
    assert 0.06 < want["lean"] < 0.15
    assert g.expected(scan.sheet(), 4 * scan.width)["lean"] > 2 * want["lean"]


def test_the_spacing_is_measured_on_the_scan_not_taken_from_the_sheet():
    """Scans of one series were made at more than one resolution. The lines
    themselves say how far apart they are."""
    lines = [40, 300, 388, 476, 565, 653, 741, 1000]       # 88 apart, among others
    assert g.commonest_spacing(lines, 100.0) == pytest.approx(88.2, abs=0.5)
    # Nothing near what was expected: the guess stands.
    assert g.commonest_spacing([0, 300, 600, 900], 100.0) == 100.0
    assert g.commonest_spacing([10], 100.0) == 100.0


def test_a_scan_at_another_resolution_is_still_registered(scan):
    """The sheet says 250 m a pixel; this scan is told 290, as if it were one of
    a series scanned finer than the rest."""
    import dataclasses
    coarse = dataclasses.replace(scan.sheet(), pixel_size=290.0)
    registered = g.register(scan.rgb, coarse, g.Reading("south", SOUTH, "west", WEST))
    assert len(registered.control) >= 0.9 * _drawn(scan)
    assert registered.pixel_size[0] == pytest.approx(PIXEL, rel=0.003)
