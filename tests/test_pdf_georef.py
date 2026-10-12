"""Reading the georeferencing a PDF chart carries, against PDFs made to order.

``scripts/`` is not a package, so it goes on the path the way the scripts do.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from osgeo import gdal, osr
from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject, DictionaryObject, FloatObject, NameObject, TextStringObject,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import pdf_georef  # noqa: E402

gdal.UseExceptions()

# As Esri's software writes one, vertical datum appended and all.
MERCATOR = (
    'PROJCS["WGS_1984_World_Mercator",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",'
    'SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],'
    'UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator"],'
    'PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],'
    'PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],'
    'UNIT["Meter",1.0]],VERTCS["WGS_1984",DATUM["D_WGS_1984",'
    'SPHEROID["WGS_1984",6378137.0,298.257223563]],PARAMETER["Vertical_Shift",0.0],'
    'PARAMETER["Direction",1.0],UNIT["Meter",1.0]]'
)
PAGE = (1200.0, 900.0)


def _viewport(name, box, corners, lpts=(0, 0, 0, 1, 1, 1, 1, 0), wkt=MERCATOR):
    """A viewport dictionary: ``corners`` are (lat, lon) at each of ``lpts``."""
    measure = DictionaryObject({
        NameObject("/Type"): NameObject("/Measure"),
        NameObject("/Subtype"): NameObject("/GEO"),
        NameObject("/GPTS"): ArrayObject([FloatObject(v) for pair in corners for v in pair]),
        NameObject("/LPTS"): ArrayObject([FloatObject(v) for v in lpts]),
        NameObject("/GCS"): DictionaryObject({
            NameObject("/Type"): NameObject("/PROJCS"),
            NameObject("/WKT"): TextStringObject(wkt),
        }),
    })
    return DictionaryObject({
        NameObject("/Type"): NameObject("/Viewport"),
        NameObject("/Name"): TextStringObject(name),
        NameObject("/BBox"): ArrayObject([FloatObject(v) for v in box]),
        NameObject("/Measure"): measure,
    })


def _corners(west, south, east, north):
    """Anticlockwise from bottom-left, as (lat, lon): the default order."""
    return [(south, west), (north, west), (north, east), (south, east)]


@pytest.fixture
def chart(tmp_path):
    writer = PdfWriter()
    page = writer.add_blank_page(*PAGE)
    page[NameObject("/VP")] = ArrayObject([
        _viewport("key map", (40, 700, 240, 860), _corners(116, 21, 124, 27)),
        _viewport("Taiwan", (300, 50, 1150, 850), _corners(119, 21.5, 122.4, 25.8)),
        # Written top-left to bottom-right, with its points in that frame.
        _viewport("inset", (40, 400, 240, 200), [(24.5, 118), (24, 118), (24, 119), (24.5, 119)]),
    ])
    path = tmp_path / "chart.pdf"
    writer.write(str(path))
    return path


def test_viewports_are_read_largest_first(chart):
    found = pdf_georef.viewports(chart)
    assert [v.name for v in found] == ["Taiwan", "inset", "key map"]
    taiwan = found[0]
    assert taiwan.box == (300, 50, 1150, 850) and taiwan.page_size == PAGE
    # Longitude first, as everything downstream has it.
    assert taiwan.lonlat[0] == (119, 21.5) and taiwan.lonlat[2] == (122.4, 25.8)
    assert taiwan.page[0] == (300, 50) and taiwan.page[2] == (1150, 850)


def test_a_box_written_corner_for_corner_the_other_way_is_still_a_box(chart):
    inset = next(v for v in pdf_georef.viewports(chart) if v.name == "inset")
    assert inset.box == (40, 200, 240, 400)
    # Its first point is the box's first corner as written: the top-left.
    assert inset.page[0] == (40, 400) and inset.lonlat[0] == (118, 24.5)


def test_the_window_and_its_geotransform_put_the_corners_where_they_are(chart):
    taiwan = pdf_georef.viewports(chart)[0]
    record = pdf_georef.entry(chart, taiwan, dpi=144)
    # 144 dpi is two pixels a point; rows count down from the top of the page.
    assert record["window"] == [600, 100, 1700, 1600]
    assert record["pdf"] == "chart.pdf" and record["viewport"] == "Taiwan"

    srs = osr.SpatialReference(record["projection"])
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    wgs = osr.SpatialReference()
    wgs.ImportFromEPSG(4326)
    wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    back = osr.CoordinateTransformation(srs, wgs)
    gt = record["geotransform"]
    for (column, row), (lon, lat) in (((0, 0), (119, 25.8)), ((1700, 1600), (122.4, 21.5)),
                                      ((0, 1600), (119, 21.5))):
        x, y = gdal.ApplyGeoTransform(gt, column, row)
        found_lon, found_lat, _ = back.TransformPoint(x, y)
        assert (found_lon, found_lat) == pytest.approx((lon, lat), abs=1e-6)


def test_a_projection_with_a_vertical_datum_appended_is_still_a_projection(chart):
    """A GeoTIFF given a compound system it cannot describe is written with no
    projection at all, and every sheet of Taiwan's was."""
    record = pdf_georef.entry(chart, pdf_georef.viewports(chart)[0], dpi=72)
    assert record["projection"].startswith("PROJCS[")
    raster = gdal.GetDriverByName("GTiff").Create("/vsimem/t.tif", 4, 4, 1)
    raster.SetProjection(record["projection"])
    raster.SetGeoTransform(record["geotransform"])
    del raster
    assert "Mercator" in gdal.Open("/vsimem/t.tif").GetProjection()
    gdal.Unlink("/vsimem/t.tif")


def test_horizontal_cuts_at_the_end_of_the_first_system():
    assert pdf_georef.horizontal(MERCATOR).endswith('UNIT["Meter",1.0]]')
    assert "VERTCS" not in pdf_georef.horizontal(MERCATOR)
    with pytest.raises(ValueError, match="no coordinate system"):
        pdf_georef.horizontal("LOCAL_CS[]")


def test_sheets_are_the_viewports_named_or_the_largest(chart):
    found = pdf_georef.viewports(chart)
    assert [v.name for v in pdf_georef.choose(found, ())] == ["Taiwan"]
    assert [v.name for v in pdf_georef.choose(found, ("inset", "Taiwan"))] == ["inset", "Taiwan"]
    assert pdf_georef.choose(found, ("nowhere",)) == []
    assert pdf_georef.choose([], ()) == []


def test_a_registration_that_does_not_fit_its_own_corners_is_refused(tmp_path):
    """Albania's chart declares a box a fifth of a degree across for a map of
    three degrees. Its corners at least agree with each other; these do not."""
    writer = PdfWriter()
    page = writer.add_blank_page(*PAGE)
    skewed = [(21.5, 119), (25.8, 119), (25.8, 122.4), (23.0, 121.0)]
    page[NameObject("/VP")] = ArrayObject([_viewport("bad", (300, 50, 1150, 850), skewed)])
    path = tmp_path / "bad.pdf"
    writer.write(str(path))
    with pytest.raises(ValueError, match="does not fit its own corners"):
        pdf_georef.entry(path, pdf_georef.viewports(path)[0], dpi=144)


def test_a_page_with_no_viewports_has_none(tmp_path):
    writer = PdfWriter()
    writer.add_blank_page(*PAGE)
    path = tmp_path / "plain.pdf"
    writer.write(str(path))
    assert pdf_georef.viewports(path) == []
