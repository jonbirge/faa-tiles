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
from test_graticule import CRS, INTERVAL, PAPER, PIXEL, SOUTH, WEST, Scan  # noqa: E402

gdal.UseExceptions()



def _rectified(tmp_path, scan):
    """A drawn scan, registered and rectified: ``(raster, limits, registration)``."""
    jpeg = tmp_path / "drawn.jpg"
    Image.fromarray(scan.rgb).save(jpeg, quality=95)
    registration = graticule.register(scan.rgb, scan.sheet(), scan.reading())
    limits = rectify.area_of(registration)["limits"]
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


def _covered(area, lon, lat):
    return any(r["lonlat"][0][0] <= lon <= r["lonlat"][1][0]
               and r["lonlat"][0][1] <= lat <= r["lonlat"][2][1] for r in area["include"])


def test_the_map_area_is_the_cells_the_graticule_was_found_round(tmp_path):
    """From the neatline where there is one to the last graticule line where
    the map runs off the scan, drawn in by a few pixels."""
    _, limits, registration, _ = _rectified(tmp_path, Scan(seed=7))
    step = 0.02
    assert WEST < limits["west"] < WEST + step and SOUTH < limits["south"] < SOUTH + step
    last_meridian = max(line.value for line in registration.meridians)
    last_parallel = max(line.value for line in registration.parallels)
    assert last_meridian - step < limits["east"] < last_meridian
    assert last_parallel - step < limits["north"] < last_parallel
    # A plain sheet is one rectangle to each row of cells, and nearly all of
    # the cells there could be: the scan is a little out of square, and the
    # last cell of a row or two is off the edge of it.
    area = rectify.area_of(registration)
    rows, columns = round((last_parallel - SOUTH) / INTERVAL), round((last_meridian - WEST) / INTERVAL)
    assert len(area["include"]) == rows
    assert 0.95 * rows * columns <= area["cells"] <= rows * columns


def test_the_map_area_of_a_square_map_has_the_wedge_where_the_wedge_is_map():
    """An ONC is a rectangle on the paper. West of the meridian through its
    south-west corner there is map at the north edge and paper at the south:
    cells at the top, and none at the bottom."""
    scan = Scan(seed=16, square=True, margin_west=420)
    registration = graticule.register(scan.rgb, scan.sheet(), scan.reading())
    assert registration.ok
    area = rectify.area_of(registration)
    # The paper beside the south-west corner is not in it...
    assert not _covered(area, WEST - INTERVAL / 2, SOUTH + INTERVAL / 2)
    assert _covered(area, WEST + INTERVAL / 2, SOUTH + INTERVAL / 2)
    # ...and nothing in it is paper: every corner of every rectangle is map.
    for rectangle in area["include"]:
        for lon, lat in rectangle["lonlat"]:
            column, row = scan.pixel([(lon, lat)])[0]
            assert scan.rgb[int(row), int(column)].max() < PAPER - 5 or \
                (scan.rgb[int(row) - 3:int(row) + 4, int(column) - 3:int(column) + 4] != PAPER).any()


def test_a_line_lost_between_two_places_it_was_found_leaves_no_hole():
    scan = Scan(seed=7)
    registration = graticule.register(scan.rgb, scan.sheet(), scan.reading())
    before = rectify.area_of(registration)
    lost = registration.parallels[2]
    middle = (lost.along > 900) & (lost.along < 1500)
    lost.along, lost.across = lost.along[~middle], lost.across[~middle]
    assert rectify.area_of(registration) == before


def test_a_line_lost_before_the_edge_is_made_up_from_the_lines_either_side():
    """The meridians it should have crossed were found above it and below."""
    scan = Scan(seed=7)
    registration = graticule.register(scan.rgb, scan.sheet(), scan.reading())
    before = rectify.area_of(registration)
    lost = registration.parallels[2]
    kept = lost.along > lost.along[0] + 800
    lost.along, lost.across = lost.along[kept], lost.across[kept]
    assert rectify.area_of(registration) == before


def test_the_last_line_lost_before_the_edge_takes_its_cells_and_no_others():
    scan = Scan(seed=7)
    registration = graticule.register(scan.rgb, scan.sheet(), scan.reading())
    before = rectify.area_of(registration)
    south = min(registration.parallels, key=lambda line: line.value)
    kept = south.along > south.along[0] + 800
    south.along, south.across = south.along[kept], south.across[kept]
    after = rectify.area_of(registration)
    # 800 px of the line, where a cell is some 130 px wide.
    assert 0 < before["cells"] - after["cells"] <= 7
    assert not _covered(after, WEST + INTERVAL / 2, SOUTH + INTERVAL / 2)
    assert _covered(after, WEST + INTERVAL / 2, SOUTH + 1.5 * INTERVAL)


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
    # The row next to the pole is not on a cone, and says so on its sheets.
    polar = rectify.crs_for([80, 88], -20)
    assert "+proj=stere" in polar and "+lat_0=90" in polar and "+lat_ts=81.050000" in polar
    assert "+proj=lcc" in rectify.crs_for([72, 80], -20)


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
                 "producer": "UK", "imprint": "Produced under the direction of the Director "
                 "General of Military Survey", "page": 0},
        # Surveyed but not yet read: left alone.
        "m-26b": {"column": 767, "row": 6041, "parallel": None, "meridian": None},
    }), encoding="utf-8")
    index = rectify.load_index(chart_series.series("tpc"))
    assert rectify.apply_readings(chart_series.series("tpc"), index, readings) == 0
    written = json.loads(path.read_text(encoding="utf-8"))["sheets"]
    assert written["e-2a"]["read"] == {"column": 110.2, "row": 8574.0, "parallel": 52.0,
                                       "meridian": -1.0}
    assert written["e-2a"]["crown"] is True and written["e-2a"]["producer"] == "UK"
    assert written["e-2a"]["imprint"].startswith("Produced under the direction")
    assert "read" not in written["m-26b"] and "producer" not in written["m-26b"]

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


def test_a_line_that_had_no_label_can_be_passed_over():
    scan = Scan(seed=11)
    found = graticule.survey(scan.rgb, scan.sheet())
    first = rectify.corner(found)
    assert first.steps == (0, 0)
    # The meridian it marked, named by where it crosses the parallel it marked.
    again = rectify.corner(found, {"meridian": [first.at]})
    assert again.steps == (0, 1) and again.parallel is first.parallel
    column, row = scan.pixel([(WEST + INTERVAL, SOUTH)])[0]
    assert again.at == pytest.approx((column, row), abs=4)
    both = rectify.corner(found, {"meridian": [first.at], "parallel": [first.at]})
    assert both.steps == (1, 1)


def test_a_line_followed_out_into_the_margin_gives_way_too():
    scan = Scan(seed=11)
    found = graticule.survey(scan.rgb, scan.sheet())
    south = found.parallels[-1][0]
    beyond = np.arange(south.along[0] - 200, south.along[0], found.coarse)
    south.along = np.r_[beyond, south.along]
    south.across = np.r_[np.full(len(beyond), south.across[0]), south.across]
    assert rectify.corner(found).steps == (1, 0)


def test_the_imprint_is_looked_for_under_the_south_west_corner():
    scan = Scan(seed=13, margin_south=900, margin_west=400)
    found = graticule.survey(scan.rgb, scan.sheet())
    left, top, right, bottom = rectify.imprint_window(found)
    assert (right - left, bottom - top) == rectify.IMPRINT
    column, row = scan.pixel([(WEST, SOUTH)])[0]
    assert left == pytest.approx(column - 200, abs=20)
    # Below the map, all of it.
    assert row + 20 < top < row + 80


def test_the_imprint_can_be_looked_for_in_the_corners_of_the_paper():
    left, right = rectify.paper_windows(9254, 6742)
    assert left == (370, 5742, 1870, 6742) and right == (7384, 5742, 8884, 6742)
    # A scan too small for two of them has them side by side, not overlapping.
    left, right = rectify.paper_windows(2300, 900)
    assert left[2] <= right[0] and left[1] == 0 and right[3] == 900

    scan = Scan(seed=13)
    found = graticule.survey(scan.rgb, scan.sheet())
    view = rectify.imprint_view(scan.rgb, found, "paper")
    assert view.size == (2 * 1150, 1000)
    assert rectify.imprint_view(scan.rgb, found, "corner").size == rectify.IMPRINT


def test_a_map_that_runs_off_the_scan_has_no_imprint_to_show():
    scan = Scan(seed=13, margin_south=-300)
    found = graticule.survey(scan.rgb, scan.sheet())
    assert rectify.imprint_window(found) is None


def test_review_pages_hold_six_sheets_and_say_which(tmp_path):
    cells = []
    for i in range(8):
        Image.new("RGB", (100, 60), "white").save(tmp_path / f"s{i}.jpg")
        cells.append((f"s{i}", tmp_path / f"s{i}.jpg"))
    readings = {stem: {} for stem, _ in cells}
    assert rectify.pages(cells, tmp_path, "corners", readings, "page") == 2
    assert Image.open(tmp_path / "corners-000.jpg").size == (200, 180)
    assert [readings[f"s{i}"]["page"] for i in (0, 5, 6, 7)] == [0, 0, 1, 1]


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


def test_a_review_that_was_stopped_takes_up_where_it_left_off(tmp_path, monkeypatch, capsys):
    """Each sheet is kept as it is surveyed. The first full survey of the ONC
    scans was stopped for want of memory at 140 of 270, with nothing written."""
    import chart_series
    scans = []
    for stem, seed in (("e-2a", 14), ("m-26b", 15)):
        Image.fromarray(Scan(seed=seed, margin_south=900).rgb).save(
            tmp_path / f"{stem}.jpg", quality=95)
        scans.append((stem, tmp_path / f"{stem}.jpg"))
    drawn = dict(INDEX, pixel_size=PIXEL, sheets={
        stem: dict(entry, band=[48, 56], west=WEST, south=SOUTH, east=WEST + 9, north=SOUTH + 6,
                   limits_from="nyu")
        for stem, entry in INDEX["sheets"].items()})
    monkeypatch.setattr(rectify, "crs_for", lambda band, longitude: CRS)
    out = tmp_path / "review"
    tpc = chart_series.series("tpc")

    assert rectify.review(tpc, drawn, scans[:1], out, workers=1, imprints="corner") == 0
    assert "1 of 1 sheet(s) to survey" in capsys.readouterr().out
    first = (out / "surveyed" / "e-2a.json").stat().st_mtime_ns

    assert rectify.review(tpc, drawn, scans, out, workers=1, imprints="corner") == 0
    assert "1 of 2 sheet(s) to survey" in capsys.readouterr().out
    assert (out / "surveyed" / "e-2a.json").stat().st_mtime_ns == first
    readings = json.loads((out / "readings.json").read_text(encoding="utf-8"))
    assert sorted(readings) == ["e-2a", "m-26b"]
    assert all(r["page"] == 0 and r["imprint_page"] == 0 for r in readings.values())
    assert Image.open(out / "corners-000.jpg").size == (2 * rectify.CELL[0],
                                                        3 * (rectify.CELL[1] + rectify.CAPTION))
    assert (out / "imprint-000.jpg").is_file()
