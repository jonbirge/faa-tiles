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
        previous = s.directory
        for script, output in s.stages:
            assert s.input_directory(script) == previous
            previous = output
        assert s.build_directory == previous


@pytest.mark.parametrize("name, zoom", [("sectionals", 12), ("ifr-low", 13)])
def test_max_zoom(name, zoom):
    """The user's call. Each matches where its prepared sheets stop holding
    detail: IFR renders from vector at 4x reach z14, upsampled sectionals z12.5."""
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
    directories = {s.directory for s in SERIES.values()}
    assert len(directories) == len(SERIES)
