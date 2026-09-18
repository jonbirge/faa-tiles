"""Static z/x/y tile pyramids from GeoTIFFs, ready to serve to Cesium.

The public names below are imported lazily, on first use, so importing one
submodule -- ``cesiumtiles.gpuwarp`` in a worker, say -- does not drag GDAL, the
server and the viewer in behind it.
"""

from __future__ import annotations

import importlib

__version__ = "0.1.0"

_EXPORTS = {
    "TileBuildError": "cesiumtiles.core",
    "TilesetResult": "cesiumtiles.core",
    "build_tileset": "cesiumtiles.core",
    "GEOGRAPHIC": "cesiumtiles.scheme",
    "SCHEMES": "cesiumtiles.scheme",
    "WEB_MERCATOR": "cesiumtiles.scheme",
    "TileRange": "cesiumtiles.scheme",
    "TilingScheme": "cesiumtiles.scheme",
    "serve_tileset": "cesiumtiles.serve",
    "render_viewer": "cesiumtiles.viewer",
    "write_viewer": "cesiumtiles.viewer",
}

__all__ = sorted(_EXPORTS) + ["__version__"]


def __getattr__(name: str):
    module = _EXPORTS.get(name)
    if module is None:
        raise AttributeError(f"module 'cesiumtiles' has no attribute {name!r}")
    value = getattr(importlib.import_module(module), name)
    globals()[name] = value          # cache, so later lookups skip this
    return value


def __dir__():
    return __all__
