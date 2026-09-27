"""Downloading the series the FAA does not publish, without touching the network.

``scripts/`` is not a package, so it goes on the path the way the scripts do.
"""

from __future__ import annotations

import datetime as dt
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
from osgeo import gdal, osr
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import fetch_ofm  # noqa: E402
import fetchers  # noqa: E402
from chart_series import series  # noqa: E402

gdal.UseExceptions()


# -- links ------------------------------------------------------------------

def test_links_are_found_in_attributes_and_in_scripts_and_made_absolute():
    html = '''
      <a href="/media/abc/one.tif">one</a>
      <a href='two.zip'>two</a>
      <script>var files = ["src/geotiffs/WAC_1_A.tif", "https:\\/\\/other.example\\/three.pdf"];</script>
      <a href="/media/abc/one.tif">again</a>
    '''
    assert fetchers.page_links("https://example.org/charts/", html) == [
        "https://example.org/media/abc/one.tif",
        "https://example.org/charts/two.zip",
        "https://example.org/charts/src/geotiffs/WAC_1_A.tif",
        "https://other.example/three.pdf",
    ]


def test_the_latest_edition_of_each_sheet_is_kept_under_the_sheets_name():
    """Denmark's URLs carry a random media id and the edition date, so the URL
    changes with every edition while the sheet does not."""
    links = [
        "https://aim.naviair.dk/media/aaa/edition-46_20260416-icao-anc-1-500000-denmark-geo-tiff.tif",
        "https://aim.naviair.dk/media/bbb/edition-46_20260903-icao-anc-1-500000-denmark-geo-tiff.tif",
        "https://aim.naviair.dk/media/ccc/edition-46_20260416-icao-anc-1-500000-denmark-printed-version-geo-tiff.tif",
        "https://aim.naviair.dk/media/ddd/edition-46_20260903-icao-anc-1-500000-denmark-pdf.pdf",
        "https://aim.naviair.dk/media/eee/edition-45_20260416-icao-anc-1-250000-copenhagen-area-geo-tiff.tif",
    ]
    found = fetchers.latest_by_sheet(links, series("dk-icao").link_pattern)
    assert found == {"denmark": ("20260903", links[1])}
    small = fetchers.latest_by_sheet(links, series("dk-250").link_pattern)
    assert small == {"copenhagen-area": ("20260416", links[4])}


def test_spanish_sheets_are_reissued_one_at_a_time():
    links = [f"https://aip.enaire.es/recursos/descargas/VFR500/{name}" for name in (
        "2025_GC_CANARIAS.zip", "2026_LE6_SUR.zip", "2025_LE6_SUR.zip",
        "2026_LE6_SUR.pdf", "VFR500_Index_Map.pdf")]
    found = fetchers.latest_by_sheet(links, series("es-vfr500").link_pattern)
    assert found == {"GC_CANARIAS": ("2025", links[0]), "LE6_SUR": ("2026", links[1])}


def test_a_link_pattern_must_say_which_sheet_a_link_is():
    with pytest.raises(ValueError, match="sheet"):
        fetchers.latest_by_sheet(["https://example.org/a.tif"], r".*/(\w+)\.tif")


def test_a_zip_gives_up_its_one_raster(tmp_path):
    archive = tmp_path / "sheet.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("2025_GC_CANARIAS.tif", b"raster")
        z.writestr("2025_GC_CANARIAS.tfw", b"world file")
    fetchers.raster_from_zip(archive, tmp_path / "GC_CANARIAS.tif")
    assert (tmp_path / "GC_CANARIAS.tif").read_bytes() == b"raster"

    two = tmp_path / "two.zip"
    with zipfile.ZipFile(two, "w") as z:
        z.writestr("a.tif", b"a")
        z.writestr("b.tif", b"b")
    with pytest.raises(RuntimeError, match="expected one raster"):
        fetchers.raster_from_zip(two, tmp_path / "out.tif")


def test_a_file_is_current_only_while_the_server_still_offers_the_same_one(tmp_path):
    (tmp_path / "denmark.tif").write_bytes(b"x")
    state = {"length": 10, "last_modified": "Thu, 03 Sep 2026 00:00:00 GMT"}
    record = {"denmark.tif": {"url": "https://a/b.tif", **state}}
    assert fetchers.is_current(tmp_path, "denmark.tif", "https://a/b.tif", state, record)
    # A new edition arrives at a new URL, or the same URL changes underneath.
    assert not fetchers.is_current(tmp_path, "denmark.tif", "https://a/c.tif", state, record)
    assert not fetchers.is_current(tmp_path, "denmark.tif", "https://a/b.tif",
                                   {**state, "length": 11}, record)
    # A record with no file behind it is not a download.
    assert not fetchers.is_current(tmp_path, "gone.tif", "https://a/b.tif", state,
                                   {"gone.tif": {"url": "https://a/b.tif", **state}})


def test_an_unknown_fetcher_is_refused(tmp_path):
    import dataclasses
    odd = dataclasses.replace(series("ch-icao"), fetcher="carrier-pigeon")
    with pytest.raises(SystemExit, match="unknown fetcher"):
        fetchers.run(odd, tmp_path)


# -- open flightmaps --------------------------------------------------------

@pytest.mark.parametrize("day, cycle, start", [
    (dt.date(2026, 9, 3), "2609", dt.date(2026, 9, 3)),     # the day it takes effect
    (dt.date(2026, 9, 2), "2608", dt.date(2026, 8, 6)),     # the day before
    (dt.date(2026, 9, 27), "2609", dt.date(2026, 9, 3)),
    (dt.date(2026, 1, 1), "2513", dt.date(2025, 12, 25)),   # a cycle spans the new year
    (dt.date(2024, 1, 25), "2401", dt.date(2024, 1, 25)),
])
def test_airac_cycle(day, cycle, start):
    assert fetch_ofm.airac(day) == (cycle, start)


def _png(color, size=fetch_ofm.TILE, alpha=255, palette=False):
    image = Image.new("RGBA", (size, size), (*color, alpha))
    if palette:
        image = image.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=8)
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def _tile_zip(tiles, compression):
    """A zip laid out as open flightmaps lays its own out, wanted tiles among
    the layers and sizes that are not wanted."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression) as z:
        z.writestr("clip/aero/512/latest/11/1070/720.png", b"not wanted")
        for (x, y), data in tiles.items():
            z.writestr(f"clip/merged/512/latest/11/{x}/{y}.png", data)
            z.writestr(f"clip/merged/256/latest/11/{x}/{y}.png", b"half size")
            z.writestr(f"clip/merged/512/latest/10/{x}/{y}.png", b"a level up")
    return buffer.getvalue()


@pytest.mark.parametrize("compression", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
def test_tiles_are_cut_out_of_a_span_of_the_zip(compression):
    tiles = {(1070, 720): _png((200, 30, 30)), (1071, 720): _png((30, 30, 200))}
    data = _tile_zip(tiles, compression)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = {}
        for info in archive.infolist():
            match = fetch_ofm.MEMBER.fullmatch(info.filename)
            if match:
                members[(int(match.group(1)), int(match.group(2)))] = info
    # Only the wanted layer, size and zoom.
    assert set(members) == set(tiles)
    first, last = fetch_ofm.span_of(members.values())
    span = data[first:last + 1]
    assert first > 0, "the span should not start at the head of the zip"
    for key, info in members.items():
        assert fetch_ofm.member_bytes(span, first, info) == tiles[key]


def test_tiles_are_assembled_where_they_belong(tmp_path):
    """A 512 px z11 tile is four 256 px z12 tiles, so the raster must sit on
    the tile grid exactly: an assembled pixel is a tile pixel."""
    red, blue = (200, 30, 30), (30, 30, 200)
    tiles = {
        (1070, 720): _png(red, palette=True),          # palette, as the real ones are
        (1072, 721): _png(blue),
        (1071, 720): _png((0, 0, 0), alpha=0),         # clipped away by the publisher
    }
    out = tmp_path / "region.tif"
    width, height = fetch_ofm.assemble(tiles, out, "2609")
    assert (width, height) == (3 * 512, 2 * 512)

    raster = gdal.Open(str(out))
    assert raster.RasterCount == 4
    assert raster.GetRasterBand(4).GetColorInterpretation() == gdal.GCI_AlphaBand
    srs = osr.SpatialReference(raster.GetProjection())
    assert srs.GetAuthorityCode(None) == "3857"
    gt = raster.GetGeoTransform()
    span = 2 * fetch_ofm.HALF_WORLD / 2 ** 11
    assert gt[0] == pytest.approx(-fetch_ofm.HALF_WORLD + 1070 * span)
    assert gt[3] == pytest.approx(fetch_ofm.HALF_WORLD - 720 * span)
    assert gt[1] == pytest.approx(span / 512) and gt[5] == pytest.approx(-span / 512)

    pixels = raster.ReadAsArray()
    assert tuple(pixels[:3, 100, 100]) == pytest.approx(red, abs=8) and pixels[3, 100, 100] == 255
    assert tuple(pixels[:3, 512 + 100, 1024 + 100]) == blue
    # Transparent where the publisher clipped, and where no tile was published.
    assert pixels[3, 100, 512 + 100] == 0
    assert pixels[3, 512 + 100, 100] == 0


def test_a_tile_of_the_wrong_size_is_refused(tmp_path):
    with pytest.raises(OSError, match="not 512"):
        fetch_ofm.assemble({(1070, 720): _png((1, 2, 3), size=256)}, tmp_path / "r.tif", "2609")


def test_a_server_that_ignores_ranges_is_told_apart_from_a_bad_zip(monkeypatch):
    """zipfile reports any OSError while reading as "not a zip file"; the
    fetcher has to know it was the server, so it can download the zip whole."""
    def whole_file(url, first, last):
        raise fetch_ofm.RangeIgnored("sent the lot")
    monkeypatch.setattr(fetch_ofm, "fetch_range", whole_file)
    with pytest.raises(fetch_ofm.RangeIgnored):
        fetch_ofm.wanted_members("https://example.org/tiles.zip", 1 << 30)


def test_a_missing_cycle_falls_back_to_the_one_before(monkeypatch):
    import urllib.error
    asked = []

    def state(url):
        asked.append(url)
        if "/2609/" in url:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        return {"length": 123, "last_modified": "x"}
    monkeypatch.setattr(fetch_ofm, "remote_state", state)
    cycle, url, _ = fetch_ofm.region_source("https://snapshots.example/", "lsas",
                                            dt.date(2026, 9, 27))
    assert cycle == "2608" and "/2608/tiles/lsas/" in url
    assert len(asked) == 2
