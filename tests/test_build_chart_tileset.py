"""What a build paints and what it says about it, without building anything.

``scripts/`` is not a package, so it goes on the path the way the scripts do.
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_chart_tileset as build  # noqa: E402
import chart_series  # noqa: E402
from chart_series import Licence, Series, series  # noqa: E402

CLOSED = Licence(name="All rights reserved", url="https://example.org/terms",
                 attribution="Example ANSP", note="Reproduction needs written permission.")
OPEN = Licence(name="Open", url="https://example.org/open", redistributable=True,
               attribution="(c) Example Survey")


def _sheet(path, bounds, alpha=False):
    west, south, east, north = bounds
    profile = {"driver": "GTiff", "width": 64, "height": 64, "dtype": "uint8",
               "crs": CRS.from_string("EPSG:4326"),
               "transform": from_bounds(west, south, east, north, 64, 64)}
    with rasterio.open(path, "w", count=4 if alpha else 3, **profile) as dst:
        dst.write(np.full((4 if alpha else 3, 64, 64), 200, np.uint8))
    return path


@pytest.fixture
def world(tmp_path, monkeypatch):
    """A two-layer stepped composite over a temporary source directory: a
    coarse open layer that is map from edge to edge, under a finer closed one
    with a reviewed manifest."""
    monkeypatch.setattr(chart_series, "SOURCE", tmp_path)
    coarse = Series(name="t-coarse", title="Coarse", publisher="Example Survey", licence=OPEN,
                    fetcher="urls", tif_pattern=r".+\.tif", whole_image=True, max_zoom=7)
    fine = Series(name="t-fine", title="Fine", publisher="Example ANSP", licence=CLOSED,
                  fetcher="urls", tif_pattern=r".+\.tif", detector="detect_sectional_areas.py",
                  max_zoom=9)
    both = Series(name="t-world", title="World", layers=("t-coarse", "t-fine"), stepped=True,
                  max_zoom=9)
    for s in (coarse, fine, both):
        monkeypatch.setitem(chart_series.SERIES, s.name, s)
    (tmp_path / "t-coarse").mkdir()
    (tmp_path / "t-fine").mkdir()
    _sheet(tmp_path / "t-coarse" / "a.tif", (0, 40, 10, 50), alpha=True)
    _sheet(tmp_path / "t-fine" / "b.tif", (4, 44, 5, 45))
    manifest = tmp_path / "t_fine_areas.json"
    manifest.write_text('{"b.tif": {"limits": {"west": 4.1}}}', encoding="utf-8")
    monkeypatch.setattr(Series, "manifest",
                        property(lambda self: tmp_path / f"{self.name.replace('-', '_')}_areas.json"))
    return both


def _args(**over):
    base = dict(charts=None, only=None, reverse_order=None)
    return argparse.Namespace(**{**base, **over})


def test_a_stepped_composite_gives_each_layer_its_own_zoom(world):
    by_layer = {}
    chosen = build.layers(world, _args(), sheets_by_layer=by_layer)
    assert [(Path(s.path).name, s.zoom) for s in chosen] == [("a.tif", 7), ("b.tif", 9)]
    assert by_layer == {"t-coarse": ["a.tif"], "t-fine": ["b.tif"]}
    # The whole-image layer needs no manifest and has no map area to mask...
    assert chosen[0].area.is_whole_image
    # ...while the other's reviewed area is read as it always was.
    assert chosen[1].area.limits.west == 4.1


def test_an_ordinary_series_is_not_stepped():
    """No zoom of its own: the mosaic's max_zoom applies, as it always has."""
    assert not series("sectionals").stepped and not series("sectionals-tac").stepped


def test_redistributable_only_leaves_out_what_may_not_be_republished(world):
    kept, left_out = build.painted_members(world, redistributable_only=True)
    assert [m.name for m in kept] == ["t-coarse"]
    assert [m.name for m in left_out] == ["t-fine"]
    everything, nothing = build.painted_members(world)
    assert [m.name for m in everything] == ["t-coarse", "t-fine"] and not nothing


def test_a_build_can_be_held_to_some_of_its_layers(world):
    kept, _ = build.painted_members(world, only_layers=["t-fine"])
    assert [m.name for m in kept] == ["t-fine"]
    # In the composite's order, whatever order they were asked for in.
    kept, _ = build.painted_members(world, only_layers=["t-fine", "t-coarse"])
    assert [m.name for m in kept] == ["t-coarse", "t-fine"]
    with pytest.raises(SystemExit, match="no layer named t-missing"):
        build.painted_members(world, only_layers=["t-missing"])


def test_metadata_credits_every_layer_that_painted(world):
    members, _ = build.painted_members(world)
    metadata = build.layer_metadata(world, members, {"t-coarse": ["a.tif"], "t-fine": ["b.tif"]})
    assert [layer["name"] for layer in metadata["layers"]] == ["t-coarse", "t-fine"]
    fine = metadata["layers"][1]
    assert fine["publisher"] == "Example ANSP" and fine["licence"] == "All rights reserved"
    assert fine["redistributable"] is False and fine["sheets"] == ["b.tif"]
    assert metadata["attribution"] == "(c) Example Survey; Example ANSP"
    # One closed layer closes the tileset.
    assert metadata["redistributable"] is False

    public, _ = build.painted_members(world, redistributable_only=True)
    metadata = build.layer_metadata(world, public, {"t-coarse": ["a.tif"]})
    assert metadata["redistributable"] is True
    assert metadata["attribution"] == "(c) Example Survey"


@pytest.fixture
def joint(world, tmp_path, monkeypatch):
    """The coarse layer as a joint production: sheet ``c`` is another
    country's, and the sheet index says so."""
    index = tmp_path / "t_coarse_sheets.json"
    index.write_text('{"sheets": {"a": {"crown": false}, "c": {"crown": true}}}',
                     encoding="utf-8")
    monkeypatch.setattr(Series, "sheet_index",
                        property(lambda self: tmp_path / f"{self.name.replace('-', '_')}_sheets.json"))
    coarse = dataclasses.replace(chart_series.SERIES["t-coarse"], flagged=(("crown", CLOSED),))
    monkeypatch.setitem(chart_series.SERIES, "t-coarse", coarse)
    _sheet(tmp_path / "t-coarse" / "c.tif", (10, 40, 20, 50), alpha=True)
    return world


def test_a_sheet_can_be_under_other_terms_than_its_series(joint):
    coarse = chart_series.SERIES["t-coarse"]
    assert coarse.licence_of("a.tif") is OPEN and coarse.licence_of("c.tif") is CLOSED
    # A sheet the index does not know is the series'.
    assert coarse.licence_of("z.tif") is OPEN
    assert chart_series.SERIES["t-fine"].licence_of("b.tif") is CLOSED


def test_redistributable_only_leaves_out_a_closed_sheet_of_an_open_series(joint, capsys):
    members, _ = build.painted_members(joint, redistributable_only=True)
    by_layer = {}
    chosen = build.layers(joint, _args(), members, by_layer, redistributable_only=True)
    assert [Path(s.path).name for s in chosen] == ["a.tif"]
    assert by_layer == {"t-coarse": ["a.tif"]}
    assert "leaving out 1 sheet(s) under All rights reserved" in capsys.readouterr().out
    assert build.layer_metadata(joint, members, by_layer)["redistributable"] is True

    everything = build.layers(joint, _args())
    assert [Path(s.path).name for s in everything] == ["a.tif", "c.tif", "b.tif"]


def test_metadata_describes_a_series_once_for_each_of_its_terms(joint):
    members, _ = build.painted_members(joint, only_layers=["t-coarse"])
    metadata = build.layer_metadata(joint, members, {"t-coarse": ["a.tif", "c.tif"]})
    assert [(layer["name"], layer["sheets"], layer["redistributable"])
            for layer in metadata["layers"]] == [("t-coarse", ["a.tif"], True),
                                                 ("t-coarse-crown", ["c.tif"], False)]
    assert metadata["redistributable"] is False
    assert metadata["attribution"] == "(c) Example Survey; Example ANSP"


def test_a_layer_that_painted_nothing_is_not_credited(world):
    members, _ = build.painted_members(world)
    metadata = build.layer_metadata(world, members, {"t-coarse": ["a.tif"]})
    assert [layer["name"] for layer in metadata["layers"]] == ["t-coarse"]


def test_the_same_credit_is_given_once():
    sectionals_tac = series("sectionals-tac")
    members, _ = build.painted_members(sectionals_tac)
    metadata = build.layer_metadata(sectionals_tac, members,
                                    {"sectionals": ["a.tif"], "tac": ["b.tif"]})
    assert metadata["attribution"] == "Federal Aviation Administration"
    assert metadata["redistributable"] is True


def test_historical_layers_are_marked(world, monkeypatch):
    old = dataclasses.replace(chart_series.SERIES["t-coarse"], historical=True)
    monkeypatch.setitem(chart_series.SERIES, "t-coarse", old)
    members, _ = build.painted_members(world)
    metadata = build.layer_metadata(world, members, {"t-coarse": ["a.tif"], "t-fine": ["b.tif"]})
    assert [layer["historical"] for layer in metadata["layers"]] == [True, False]
