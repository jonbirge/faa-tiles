"""Rectifying scanned charts, against scans drawn to order (see test_graticule).

``scripts/`` is not a package, so it goes on the path the way the scripts do.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from osgeo import gdal, osr
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import graticule  # noqa: E402
import rectify_charts as rectify  # noqa: E402
from test_graticule import CRS, INTERVAL, PIXEL, SOUTH, WEST, Scan  # noqa: E402

gdal.UseExceptions()



def _rectified(tmp_path, scan):
    """A drawn scan, registered and rectified: ``(raster, limits, registration)``."""
    jpeg = tmp_path / "drawn.jpg"
    Image.fromarray(scan.rgb).save(jpeg, quality=95)
    registration = graticule.register(scan.rgb, scan.sheet(), scan.reading())
    limits = rectify.limits_of(registration)
    out = tmp_path / "drawn.tif"
    done = rectify.rectify(jpeg, out, registration, limits)
    return gdal.Open(str(out)), limits, registration, done


def _darkness_at(raster, lonlat):
    """How dark the rectified raster is at each ``(lon, lat)``: the darkest
    pixel within one of where the point should be."""
    wgs = osr.SpatialReference()
    wgs.ImportFromEPSG(4326)
    wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    srs = osr.SpatialReference(raster.GetProjection())
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    forward = osr.CoordinateTransformation(wgs, srs)
    inverse = gdal.InvGeoTransform(raster.GetGeoTransform())
    pixels = raster.ReadAsArray().astype(int).max(axis=0)
    out = []
    for lon, lat in lonlat:
        x, y, _ = forward.TransformPoint(lon, lat)
        column, row = gdal.ApplyGeoTransform(inverse, x, y)
        column, row = int(column), int(row)
        out.append(pixels[row - 1:row + 2, column - 1:column + 2].min())
    return np.array(out)


def _crossings(limits, inset=0.0):
    lons = np.arange(np.ceil(limits["west"] / INTERVAL) * INTERVAL + inset, limits["east"], INTERVAL)
    lats = np.arange(np.ceil(limits["south"] / INTERVAL) * INTERVAL + inset, limits["north"],
                     INTERVAL)
    return [(lon, lat) for lon in lons for lat in lats]


@pytest.mark.parametrize("stretch", [0.0, 0.03])
def test_a_rectified_scan_has_its_graticule_where_the_graticule_is(tmp_path, stretch):
    """The test that matters: ask the rectified raster for the places where a
    meridian crosses a parallel, and find a line at every one of them -- whether
    the scanner held the sheet true or stretched it 3% down its length."""
    raster, limits, registration, done = _rectified(tmp_path, Scan(stretch=stretch, seed=5))
    at_crossings = _darkness_at(raster, _crossings(limits))
    assert len(at_crossings) > 80
    assert (at_crossings < 90).mean() > 0.97
    # And between the lines, the map: sea, not ink.
    between = _darkness_at(raster, _crossings(limits, inset=INTERVAL / 2)[:-1])
    assert (between > 150).mean() > 0.9
    assert done["control"] > 80


def test_a_rectified_scan_is_in_the_sheets_own_projection(tmp_path):
    raster, limits, _, done = _rectified(tmp_path, Scan(seed=6))
    srs = osr.SpatialReference(raster.GetProjection())
    assert srs.GetAttrValue("PROJECTION") == "Lambert_Conformal_Conic_2SP"
    gt = raster.GetGeoTransform()
    # North up and square, at the scan's own pixel size.
    assert gt[2] == 0 and gt[4] == 0
    assert gt[1] == pytest.approx(PIXEL, rel=0.01) and gt[5] == pytest.approx(-PIXEL, rel=0.01)
    assert done["pixel"] == pytest.approx(PIXEL, rel=0.01)
    assert raster.RasterCount == 3


def test_the_map_area_is_the_graticules(tmp_path):
    """From the neatline where there is one to the last graticule line where
    the map runs off the scan, drawn in by a few pixels."""
    _, limits, registration, _ = _rectified(tmp_path, Scan(seed=7))
    step = 0.02
    assert WEST < limits["west"] < WEST + step and SOUTH < limits["south"] < SOUTH + step
    last_meridian = max(line.value for line in registration.meridians)
    last_parallel = max(line.value for line in registration.parallels)
    assert last_meridian - step < limits["east"] < last_meridian
    assert last_parallel - step < limits["north"] < last_parallel


def test_crossings_measured_on_the_wrong_line_are_left_out():
    scan = Scan(seed=8, clutter=False)
    registration = graticule.register(scan.rgb, scan.sheet(), scan.reading())
    control = registration.control.copy()
    wrong = [5, 40, 77]
    control[wrong, 0] += (14.0, -22.0, 9.0)
    kept = rectify.consistent(control, graticule.Projector(CRS))
    assert not kept[wrong].any()
    assert kept.sum() >= len(control) - len(wrong) - 3


def test_a_stretched_scan_keeps_its_crossings():
    """What a scanner does is smooth, and smooth is not an outlier."""
    scan = Scan(stretch=0.03, seed=9, clutter=False)
    registration = graticule.register(scan.rgb, scan.sheet(), scan.reading())
    kept = rectify.consistent(registration.control, graticule.Projector(CRS))
    assert kept.mean() > 0.95


# -- the sheet index --------------------------------------------------------

INDEX = {
    "interval": 0.5, "pixel_size": 80.6,
    "sheets": {
        "e-2a": {"title": "TPC E-2A", "band": [48, 56], "west": -1.8688, "south": 52.0002,
                 "east": 6.4782, "north": 56.0, "limits_from": "mun", "crown": True},
        "m-26b": {"title": "TPC M-26B", "band": [-8, 0], "limits_from": None, "crown": False},
        "m-26c": {"title": "TPC M-26C", "band": [-8, 0], "limits_from": None, "crown": False},
    },
}


def test_a_sheets_projection_follows_from_its_band():
    crs = rectify.crs_for([48, 56], 2.5)
    assert "+proj=lcc" in crs and "+lat_1=49.333333" in crs and "+lat_2=54.666667" in crs
    assert "+lon_0=2.500000" in crs
    # South of the equator the band is negative, and so are its parallels.
    assert "+lat_1=-6.666667" in rectify.crs_for([-8, 0], -61)


def test_what_is_known_of_a_sheet_before_its_scan_is_looked_at():
    known = rectify.sheet_for("e-2a", INDEX["sheets"]["e-2a"], INDEX)
    assert known.west == -1.8688 and known.interval == 0.5 and known.pixel_size == 80.6
    assert known.middle == pytest.approx((2.3047, 54.0001))
    # With no limits, only the row and the quarter say where the sheet is: B is
    # the northern half of its band, C the southern.
    north = rectify.sheet_for("m-26b", INDEX["sheets"]["m-26b"], INDEX)
    south = rectify.sheet_for("m-26c", INDEX["sheets"]["m-26c"], INDEX)
    assert north.west is None and north.middle[1] == -2 and south.middle[1] == -6


def test_a_reading_outranks_the_index():
    entry = dict(INDEX["sheets"]["e-2a"], read={"column": 110, "row": 8574, "parallel": 52.0,
                                                 "meridian": -1.0})
    assert rectify.reading_of(entry) == graticule.Reading(110.0, 8574.0, 52.0, -1.0)
    assert rectify.reading_of(INDEX["sheets"]["e-2a"]) is None
    assert rectify.sheet_for("e-2a", entry, INDEX).middle == (-1.0, 52.0)


def test_readings_are_written_into_the_sheet_index(tmp_path, monkeypatch):
    import chart_series
    path = tmp_path / "tpc_sheets.json"
    path.write_text(json.dumps(INDEX), encoding="utf-8")
    monkeypatch.setattr(chart_series.Series, "sheet_index", property(lambda self: path))
    readings = tmp_path / "readings.json"
    readings.write_text(json.dumps({
        "e-2a": {"column": 110.2, "row": 8574, "parallel": 52, "meridian": -1, "crown": True,
                 "page": 0},
        # Surveyed but not yet read: left alone.
        "m-26b": {"column": 767, "row": 6041, "parallel": None, "meridian": None},
    }), encoding="utf-8")
    index = rectify.load_index(chart_series.series("tpc"))
    assert rectify.apply_readings(chart_series.series("tpc"), index, readings) == 0
    written = json.loads(path.read_text(encoding="utf-8"))["sheets"]
    assert written["e-2a"]["read"] == {"column": 110.2, "row": 8574.0, "parallel": 52.0,
                                       "meridian": -1.0}
    assert "read" not in written["m-26b"]

    readings.write_text(json.dumps({"z-99z": {"column": 1, "row": 1, "parallel": 1,
                                              "meridian": 1}}), encoding="utf-8")
    with pytest.raises(SystemExit, match="not a sheet"):
        rectify.apply_readings(chart_series.series("tpc"), index, readings)


def test_a_sheet_with_no_reading_is_not_rectified_on_the_indexs_word(tmp_path):
    scan = Scan(seed=10)
    jpeg = tmp_path / "e-2a.jpg"
    Image.fromarray(scan.rgb).save(jpeg, quality=95)
    task = ("e-2a", str(jpeg), str(tmp_path / "e-2a.tif"), INDEX["sheets"]["e-2a"], INDEX, False)
    stem, outcome = rectify.work(task)
    assert "skipped" in outcome and not (tmp_path / "e-2a.tif").exists()


def test_each_line_is_shown_where_it_meets_the_edge_of_the_map():
    """Which is where its label is printed."""
    scan = Scan(seed=11)
    found = graticule.survey(scan.rgb, scan.sheet())
    shown = rectify.corner(found)
    assert shown.ends == ("south", "west") and shown.steps == (0, 0)
    # The end lines meet the edge at the corner, and cross there.
    column, row = scan.pixel([(WEST, SOUTH)])[0]
    assert shown.at == pytest.approx((column, row), abs=3)
    for window, meets in zip(shown.windows, shown.meets):
        left, top, right, bottom = window
        assert (right - left, bottom - top) == rectify.PANEL
        assert meets == pytest.approx((column, row), abs=20)
        # With margin on the one side of it and map on the other.
        assert left + 150 < column < right - 150 and top + 150 < row < bottom - 150


def test_a_line_not_traced_to_the_edge_gives_way_to_the_next():
    """A line is shown where it stops. One that stops well short of where its
    neighbours do was not traced to the edge of the map, and its label is not
    where it stops."""
    scan = Scan(seed=11)
    found = graticule.survey(scan.rgb, scan.sheet())
    south = found.parallels[-1][0]
    kept = south.along > south.along[0] + 2.5 * rectify._spacing(found.meridians, found.along_y)
    south.along, south.across = south.along[kept], south.across[kept]
    shown = rectify.corner(found)
    assert shown.steps == (1, 0)
    # The next parallel north, where it meets the west edge.
    column, row = scan.pixel([(WEST, SOUTH + INTERVAL)])[0]
    # To within a strip: where a line stops is known no better than that.
    assert shown.meets[0] == pytest.approx((column, row), abs=20)
    assert shown.at == pytest.approx((column, row), abs=4)


def test_a_line_followed_out_into_the_margin_gives_way_too():
    scan = Scan(seed=11)
    found = graticule.survey(scan.rgb, scan.sheet())
    south = found.parallels[-1][0]
    beyond = np.arange(south.along[0] - 200, south.along[0], found.coarse)
    south.along = np.r_[beyond, south.along]
    south.across = np.r_[np.full(len(beyond), south.across[0]), south.across]
    assert rectify.corner(found).steps == (1, 0)


def test_the_caption_is_above_the_scan_and_not_over_it():
    """A caption drawn on the cell covered the labels along its top edge."""
    scan = Scan(seed=12)
    found = graticule.survey(scan.rgb, scan.sheet())
    cell, shown = rectify.draw_cell(scan.rgb, found, "TPC X-1A  [x-1a]")
    assert cell.size == (rectify.CELL[0], rectify.CELL[1] + rectify.CAPTION)
    left, top, right, bottom = shown.windows[0]
    drawn = np.asarray(cell)[rectify.CAPTION:, :rectify.PANEL[0] - 6, :].astype(int)
    original = scan.rgb[top:bottom, left:right - 6]
    # The top of the view is all there, marks aside.
    assert (np.abs(drawn[:30] - original[:30]).max(axis=2) < 40).mean() > 0.95


def test_a_line_is_not_marked_across_the_margin_where_its_label_is():
    scan = Scan(seed=12)
    found = graticule.survey(scan.rgb, scan.sheet())
    shown = rectify.corner(found)
    left, top, right, bottom = shown.windows[0]
    panel = np.asarray(rectify.draw_panel(scan.rgb, found, shown,
                                          shown.windows[0])).astype(int)
    changed = np.abs(panel - scan.rgb[top:bottom, left:right]).max(axis=2) > 40
    column, row = (int(v) for v in shown.meets[0])
    # Marked inside the map, and not in the paper west and south of the corner.
    assert changed[:, column - left + 20:].any()
    assert not changed[:, :column - left - 12].any()
    # (Below the corner, that is: a parallel drawn on a cone does not stay on
    # one row of a scan.)
    assert not changed[row - top + 12:, :column - left + 60].any()
