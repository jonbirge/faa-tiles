"""Transfer GeoTIFF georeferencing between rasters of identical size."""

from geotransfer.core import (
    GeoReference,
    GeoReferenceError,
    copy_geo_metadata,
    read_georeference,
)

__version__ = "0.1.0"

__all__ = [
    "GeoReference",
    "GeoReferenceError",
    "copy_geo_metadata",
    "read_georeference",
    "__version__",
]
