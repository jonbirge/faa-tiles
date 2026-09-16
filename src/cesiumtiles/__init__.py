"""Static z/x/y tile pyramids from GeoTIFFs, ready to serve to Cesium."""

from cesiumtiles.core import TileBuildError, TilesetResult, build_tileset
from cesiumtiles.scheme import GEOGRAPHIC, SCHEMES, WEB_MERCATOR, TileRange, TilingScheme
from cesiumtiles.serve import serve_tileset
from cesiumtiles.viewer import render_viewer, write_viewer

__version__ = "0.1.0"

__all__ = [
    "GEOGRAPHIC",
    "SCHEMES",
    "WEB_MERCATOR",
    "TileBuildError",
    "TileRange",
    "TilesetResult",
    "TilingScheme",
    "build_tileset",
    "render_viewer",
    "serve_tileset",
    "write_viewer",
    "__version__",
]
