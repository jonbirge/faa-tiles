"""The public site in www/: the tileset picker page and its manifest writer."""

import importlib.util
import json
import re
from pathlib import Path

from cesiumtiles.viewer import CESIUM_VERSION

WWW = Path(__file__).resolve().parents[1] / "www"
PAGE = (WWW / "index.html").read_text(encoding="utf-8")


def _update_tilesets():
    spec = importlib.util.spec_from_file_location("update_tilesets", WWW / "update_tilesets.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scan_lists_subdirectories_with_metadata(tmp_path: Path):
    (tmp_path / "b-ifr").mkdir()
    (tmp_path / "b-ifr" / "metadata.json").write_text(json.dumps({"name": "IFR Low"}))
    (tmp_path / "a-vfr").mkdir()
    (tmp_path / "a-vfr" / "metadata.json").write_text(json.dumps({}))
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "metadata.json").write_text("{not json")
    (tmp_path / "empty").mkdir()
    (tmp_path / "metadata.json").write_text(json.dumps({"name": "root is not listed"}))

    assert _update_tilesets().scan(tmp_path) == [
        {"path": "./a-vfr", "name": "a-vfr"},        # no name: the directory's
        {"path": "./b-ifr", "name": "IFR Low"},
    ]


def test_page_uses_the_same_cesium_as_the_tester():
    assert set(re.findall(r"cesium@([\d.]+)/", PAGE)) == {CESIUM_VERSION}


def test_page_renders_at_the_displays_full_resolution():
    # Cesium's default renders at CSS pixels, half the sharpness of a 2x screen.
    assert "viewer.useBrowserRecommendedResolution = false" in PAGE
    assert "viewer.resolutionScale = 1.0" in PAGE


def test_page_has_no_controls_but_tileset_buttons():
    for widget in ("animation", "baseLayerPicker", "fullscreenButton", "geocoder",
                   "homeButton", "infoBox", "navigationHelpButton", "sceneModePicker",
                   "selectionIndicator", "timeline"):
        assert f"{widget}: false" in PAGE, widget
    assert "<select" not in PAGE and "<input" not in PAGE


def test_page_uses_the_unsnapped_extent_and_handles_the_antimeridian():
    # The same two rules as the tester; see CLAUDE.md for the failures they fix.
    assert "meta.data_bounds || meta.bounds" in PAGE
    assert "e[0] > e[2] ? [-180 + 1e-5, e[1], 180 - 1e-5, e[3]] : e" in PAGE


def test_page_finds_tilesets_by_manifest_then_by_listing():
    assert 'new URL("tilesets.json", HERE)' in PAGE
    assert "fromListing" in PAGE
    # It must recognise itself when a server answers the folder with index.html.
    assert '<meta name="faa-tiles-index"' in PAGE
