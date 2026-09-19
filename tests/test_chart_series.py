"""How each FAA chart series is described, and where its stages read and write.

``scripts/`` is not a package, so it goes on the path the way the scripts do.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from chart_series import SERIES, series  # noqa: E402


def test_unknown_series_is_refused():
    with pytest.raises(SystemExit):
        series("ifr-high")


def test_sectionals_are_upsampled_from_the_downloaded_geotiffs():
    s = series("sectionals")
    # No vector source exists for these, so the GeoTIFFs are the input.
    assert s.fetches_tifs
    assert not s.wants_pdf_zip("DELUS1.zip") and not s.wants_pdf("ENR_L01.pdf")
    # Guam and Samoa are excluded per GeoTIFF: they ship in a zip we do want.
    assert s.wants_tif("Hawaiian Islands SEC.tif")
    assert not s.wants_tif("Mariana Islands Inset SEC.tif")
    # One stage: super-resolution, which doubles the manifests' pixel scale.
    assert s.upsample_scale == 2 and s.pixel_scale == 2
    assert s.upsample_model.endswith(".pth")
    assert [script for script, _ in s.stages] == ["upsample_charts.py"]
    assert s.input_directory("upsample_charts.py") == s.directory
    assert s.build_directory == s.upscaled_directory


def test_ifr_low_is_drawn_from_the_vector_pdfs_and_never_upsampled():
    s = series("ifr-low")
    assert s.pdf_scale == 4 and s.pixel_scale == 4
    # The PDFs carry no georeferencing, so a routine build skips the GeoTIFFs;
    # they are an input to re-detection only.
    assert not s.fetches_tifs
    # Vector geometry has nothing for a super-resolver to recover, and the user
    # ruled denoise out for these charts besides.
    assert s.upsample_scale == 0 and not s.upsample_model


def test_ifr_low_stage_directories_chain():
    s = series("ifr-low")
    assert s.pdf_directory == s.directory / "pdf"
    # Downloaded PDFs -> renders -> healed copies, and the build tiles the last.
    assert [script for script, _ in s.stages] == ["render_pdfs.py", "heal_frames.py"]
    assert s.input_directory("render_pdfs.py") == s.directory
    assert s.input_directory("heal_frames.py") == s.render_directory
    assert s.build_directory == s.healed_directory
    assert s.pdf_manifest.name == "ifr_low_pdf.json"
    assert s.manifest.name == "ifr_low_areas.json"


def test_a_stage_a_series_does_not_run_has_no_input():
    with pytest.raises(KeyError):
        series("ifr-low").input_directory("upsample_charts.py")
    with pytest.raises(KeyError):
        series("sectionals").input_directory("render_pdfs.py")


def test_every_stage_reads_the_previous_stages_output():
    for s in SERIES.values():
        if s.is_composite:
            continue
        previous = s.directory
        for script, output in s.stages:
            assert s.input_directory(script) == previous
            previous = output
        assert s.build_directory == previous


@pytest.mark.parametrize("name, zoom", [
    ("sectionals", 12), ("ifr-low", 13), ("tac", 13), ("sectionals-tac", 12),
])
def test_max_zoom(name, zoom):
    """The user's call. Each matches where its prepared sheets stop holding
    detail: IFR renders from vector at 4x reach z14, upsampled sectionals z12.5,
    and a TAC is 1:250,000 -- half the sectionals' pitch, so one level finer."""
    assert series(name).max_zoom == zoom


@pytest.mark.parametrize("name, wanted", [
    ("DELUS1.zip", True),
    ("DELUS35.zip", True),
    ("delus27.zip", True),        # the index's spelling varies
    ("DELAK1.zip", False),        # Alaska
    ("DELCB1.zip", False),        # Caribbean
    ("DEHUS1.zip", False),        # high altitude
    ("DELUS1_tif.zip", False),
])
def test_ifr_low_pdf_zip_pattern(name, wanted):
    assert series("ifr-low").wants_pdf_zip(name) is wanted


@pytest.mark.parametrize("name, wanted", [
    ("ENR_L01.pdf", True),
    ("ENR_L36.pdf", True),
    ("ENR_AKL01.pdf", False),
    ("ENR_H01.pdf", False),
])
def test_ifr_low_pdf_pattern(name, wanted):
    assert series("ifr-low").wants_pdf(name) is wanted


def test_l06_ships_as_two_geotiff_panels():
    """One PDF page, two GeoTIFFs: the tif pattern must keep both halves."""
    s = series("ifr-low")
    assert s.wants_tif("ENR_L06N.tif") and s.wants_tif("ENR_L06S.tif")
    assert s.wants_pdf("ENR_L06.pdf")


def test_every_series_has_its_own_directories():
    """Composites excepted -- they own no sheets, and say so rather than
    quietly pointing a stage at a directory nothing writes."""
    plain = [s for s in SERIES.values() if not s.is_composite]
    assert len({s.directory for s in plain}) == len(plain)
    for s in SERIES.values():
        if s.is_composite:
            with pytest.raises(SystemExit):
                s.directory
            with pytest.raises(SystemExit):
                s.manifest


def test_every_series_names_a_detector_or_is_a_composite():
    """A composite detects nothing itself; every layer it paints must."""
    for s in SERIES.values():
        assert bool(s.detector) is not s.is_composite
        if s.is_composite:
            assert all(m.detector for m in s.members)


def test_terminal_area_charts_keep_only_the_chart_itself():
    s = series("tac")
    assert s.wants_zip("Boston_TAC.zip") and s.wants_zip("Anchorage-Fairbanks_TAC.zip")
    assert not s.wants_zip("Seattle_SEC.zip")
    # One zip can hold two TACs, so the sheets are chosen per GeoTIFF.
    assert s.wants_tif("Anchorage TAC.tif") and s.wants_tif("Fairbanks TAC.tif")
    assert s.wants_tif("Colorado Springs TAC.tif") and s.wants_tif("Puerto Rico-VI TAC.tif")
    # The other products that ship in the same zips are not map.
    assert not s.wants_tif("Denver FLY.tif")            # flyway planning chart
    assert not s.wants_tif("Anchorage Graphic.tif")     # airspace graphic
    assert not s.wants_tif("New York TAC VFR Planning Charts.tif")
    # Rasters at source like the sectionals, and upsampled the same way.
    assert s.fetches_tifs and s.upsample_scale == 2 and s.pixel_scale == 2
    assert s.upsample_model == series("sectionals").upsample_model
    assert [script for script, _ in s.stages] == ["upsample_charts.py"]


def test_sectionals_tac_paints_its_layers_in_order_over_their_own_directories():
    s = series("sectionals-tac")
    assert s.is_composite
    assert [m.name for m in s.members] == ["sectionals", "tac"]
    # The layers are the series themselves, so nothing is downloaded, upsampled
    # or reviewed twice: a layer already built as its own tileset is reused.
    assert [m.directory for m in s.members] == [series("sectionals").directory,
                                                series("tac").directory]
    assert [m.manifest for m in s.members] == [series("sectionals").manifest,
                                               series("tac").manifest]
    assert s.tileset.name == "tileset-sectionals-tac"


def test_only_the_finer_layer_earns_the_detail_level():
    s = series("sectionals-tac")
    assert s.detail_layers == ("tac",)
    # One sparse level past the level that covers the whole mosaic.
    assert s.detail_zoom == s.max_zoom + 1
    assert s.detail_zoom == series("tac").max_zoom
    assert all(name in s.layers for name in s.detail_layers)


def test_a_plain_series_has_no_detail_level():
    for name in ("sectionals", "ifr-low", "tac"):
        assert series(name).detail_zoom == 0 and not series(name).detail_layers
