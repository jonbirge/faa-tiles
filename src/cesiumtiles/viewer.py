"""Render the tile tester page.

The page itself lives in ``viewer.html`` next to this module -- real HTML, so it
edits like HTML rather than like a Python string. This module only fills in its
four placeholders.

``gdal raster tile`` can write Leaflet, OpenLayers, MapML and STAC front ends,
but not a Cesium one, so we supply our own. It is never written into a tileset:
``cesiumtiles-serve`` renders it and serves it at ``/``, which is what lets one
tester sit above several tilesets and switch between them.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["write_viewer", "render_viewer", "template_path", "CESIUM_VERSION"]

CESIUM_VERSION = "1.135"

_TEMPLATE_NAME = "viewer.html"


def template_path() -> Path:
    """Where the page source lives. Edit that file, not this module."""
    return Path(__file__).resolve().parent / _TEMPLATE_NAME


def _read_template() -> str:
    path = template_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"{_TEMPLATE_NAME} is missing from the package at {path}. It ships as "
            "package data; reinstall with `pip install -e .` if this is a checkout."
        )
    # Read on every call rather than caching at import. The server renders per
    # request, so editing viewer.html and reloading the browser is enough to see
    # the change -- no restart.
    return path.read_text(encoding="utf-8")


def render_viewer(metadata: dict | None = None, source: str = ".") -> str:
    """Return the tile-tester HTML.

    ``source`` is the tileset the page opens with, resolved the same way the
    Source box resolves what you type into it: a directory holding a
    ``metadata.json``, or a ``{z}/{x}/{y}`` template. ``metadata`` is baked in
    only as a fallback for when that lookup fails.
    """
    metadata = metadata or {}
    return (
        _read_template()
        .replace("__CESIUM__", CESIUM_VERSION)
        .replace("__TITLE__", str(metadata.get("name", "Tile tester")))
        .replace("__METADATA__", json.dumps(metadata, indent=2) if metadata else "null")
        .replace("__SOURCE__", json.dumps(source))
    )


def write_viewer(path: str | Path, metadata: dict | None = None, source: str = ".") -> Path:
    """Write a standalone copy of the tile tester to ``path`` and return it."""
    path = Path(path)
    path.write_text(render_viewer(metadata, source), encoding="utf-8")
    return path
