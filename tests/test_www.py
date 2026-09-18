"""The public site in www/: the tileset picker page and its manifest writer."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from cesiumtiles.viewer import CESIUM_VERSION

WWW = Path(__file__).resolve().parents[1] / "www"
PAGE = (WWW / "index.html").read_text(encoding="utf-8")


def test_update_script_lists_subdirectories_with_metadata(tmp_path: Path):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("no bash")
    for name in ("b-ifr", "a-vfr", "with space"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "metadata.json").write_text("not parsed, only found")
    (tmp_path / "empty").mkdir()
    (tmp_path / "metadata.json").write_text("{}")        # the root is not a tileset

    script = (WWW / "update_tilesets.sh").as_posix()
    subprocess.run([bash, script, tmp_path.as_posix()], check=True, capture_output=True)

    listing = json.loads((tmp_path / "tilesets.json").read_text(encoding="utf-8"))
    assert listing == [{"path": f"./{n}", "name": n} for n in ("a-vfr", "b-ifr", "with space")]


def test_update_script_writes_an_empty_list_when_there_are_no_tilesets(tmp_path: Path):
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("no bash")
    script = (WWW / "update_tilesets.sh").as_posix()
    subprocess.run([bash, script, tmp_path.as_posix()], check=True, capture_output=True)
    assert json.loads((tmp_path / "tilesets.json").read_text(encoding="utf-8")) == []


def test_page_uses_the_same_cesium_as_the_tester():
    assert set(re.findall(r"cesium@([\d.]+)/", PAGE)) == {CESIUM_VERSION}


def test_page_renders_at_the_displays_full_resolution():
    # Cesium's default renders at CSS pixels, half the sharpness of a 2x screen.
    assert "viewer.useBrowserRecommendedResolution = false" in PAGE
    assert "viewer.resolutionScale = 1.0" in PAGE


def test_page_has_no_controls_but_tileset_buttons_and_scene_mode():
    for widget in ("animation", "baseLayerPicker", "fullscreenButton", "geocoder",
                   "homeButton", "infoBox", "navigationHelpButton",
                   "selectionIndicator", "timeline"):
        assert f"{widget}: false" in PAGE, widget
    assert "sceneModePicker: true" in PAGE
    assert "<select" not in PAGE and "<input" not in PAGE


def test_switching_tilesets_never_moves_the_camera():
    # The user's call: compare charts in place, never zoom to a tileset.
    for move in ("setView", "flyTo", "zoomTo", "flyHome"):
        assert move not in PAGE, move


def test_page_has_a_background_map_under_the_charts():
    assert "World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}" in PAGE
    # Switching removes only the chart layer, never the base map.
    assert "viewer.imageryLayers.remove(layer, true)" in PAGE
    assert "removeAll" not in PAGE


def test_page_uses_the_unsnapped_extent_and_handles_the_antimeridian():
    # The same two rules as the tester; see CLAUDE.md for the failures they fix.
    assert "meta.data_bounds || meta.bounds" in PAGE
    assert "e[0] > e[2] ? [-180 + 1e-5, e[1], 180 - 1e-5, e[3]] : e" in PAGE


def test_page_finds_tilesets_by_manifest_then_by_listing():
    assert 'new URL("tilesets.json", HERE)' in PAGE
    assert "fromListing" in PAGE
    # It must recognise itself when a server answers the folder with index.html.
    assert '<meta name="faa-tiles-index"' in PAGE


def test_globe_fills_the_window_with_the_buttons_floating_over_it():
    assert "#globe { position: fixed; inset: 0; }" in PAGE
    nav = PAGE[PAGE.index("  nav {"):PAGE.index("}", PAGE.index("  nav {"))]
    assert "position: fixed" in nav and "z-index" in nav
