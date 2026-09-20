"""Where an IFR sheet's map area stops, relative to its frame rule.

``scripts/`` is not a package, so it goes on the path the way the scripts do.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from chart_series import series  # noqa: E402
from detect_ifr_areas import map_area  # noqa: E402

# What detect() records for one sheet: the rectangle to the rule's outside
# edge, and the one just inside its anti-aliased inner edge.
FRAME = {"outer": [100, 200, 1100, 900], "clean": [112, 212, 1088, 888]}


def _rect(polygon):
    xs = [x for x, _ in polygon]
    ys = [y for _, y in polygon]
    return [min(xs), min(ys), max(xs), max(ys)]


def test_abutting_sheets_keep_the_rule_for_healing():
    """ifr-low: there is no map under the rule on either sheet, so the area
    runs to its outer edge and heal_frames.py repaints the band. Cropping
    inside it left a 1-3 km gap along all 32 shared edges."""
    polygon = map_area(FRAME, heal_frames=True)
    assert _rect(polygon) == FRAME["outer"]
    assert polygon == [[100, 200], [1100, 200], [1100, 900], [100, 900]]


def test_overlapping_sheets_crop_the_rule_away():
    """ifr-high: the map under the rule is the neighbour's, so keeping the rule
    would draw a black line across it. The area stops at the clean edge."""
    polygon = map_area(FRAME, heal_frames=False)
    assert _rect(polygon) == FRAME["clean"]
    # Strictly inside the outer rectangle on every side.
    ox0, oy0, ox1, oy1 = FRAME["outer"]
    cx0, cy0, cx1, cy1 = _rect(polygon)
    assert ox0 < cx0 and oy0 < cy0 and cx1 < ox1 and cy1 < oy1


def test_each_ifr_series_gets_the_edge_its_sheets_need():
    """The flag that picks between them is the series' own, so a new IFR series
    only has to say whether its sheets abut."""
    assert _rect(map_area(FRAME, series("ifr-low").heal_frames)) == FRAME["outer"]
    assert _rect(map_area(FRAME, series("ifr-high").heal_frames)) == FRAME["clean"]


def test_the_polygon_winds_as_a_closed_rectangle():
    """mosaic.MapArea reads these as a polygon, not as a bounding box, so the
    four corners have to go round rather than criss-cross."""
    for heal in (True, False):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = map_area(FRAME, heal)
        assert y0 == y1 and x1 == x2 and y2 == y3 and x3 == x0
        assert x0 < x1 and y0 < y2
