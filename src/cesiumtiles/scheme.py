"""Tile grid mathematics for the two schemes Cesium can consume.

Tiles are addressed ``z/x/y`` with ``y`` counted from the *north* edge, which is
the XYZ ("slippy map") convention that Cesium's ``UrlTemplateImageryProvider``
expects from a ``{z}/{x}/{y}`` template. TMS numbering, which counts ``y`` from
the south, is available via :meth:`TilingScheme.flip_y`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = ["TilingScheme", "WEB_MERCATOR", "GEOGRAPHIC", "SCHEMES", "TileRange"]

# Half the circumference of the WGS84 sphere used by EPSG:3857.
MERCATOR_HALF_WORLD = 20037508.342789244


@dataclass(frozen=True)
class TileRange:
    """An inclusive rectangle of tile indices at one zoom level."""

    z: int
    x_min: int
    x_max: int
    y_min: int
    y_max: int

    @property
    def width(self) -> int:
        return self.x_max - self.x_min + 1

    @property
    def height(self) -> int:
        return self.y_max - self.y_min + 1

    @property
    def count(self) -> int:
        return self.width * self.height

    def __iter__(self):
        for y in range(self.y_min, self.y_max + 1):
            for x in range(self.x_min, self.x_max + 1):
                yield x, y


@dataclass(frozen=True)
class TilingScheme:
    """A quadtree tile grid over a projected or geographic world extent."""

    name: str
    crs: str
    west: float
    south: float
    east: float
    north: float
    columns_at_zoom_0: int
    rows_at_zoom_0: int
    tile_size: int = 256

    # -- grid geometry -------------------------------------------------

    def columns(self, z: int) -> int:
        return self.columns_at_zoom_0 << z

    def rows(self, z: int) -> int:
        return self.rows_at_zoom_0 << z

    def tile_span(self, z: int) -> tuple[float, float]:
        """Width and height of one tile, in CRS units, at zoom ``z``."""
        return (
            (self.east - self.west) / self.columns(z),
            (self.north - self.south) / self.rows(z),
        )

    def resolution(self, z: int) -> float:
        """CRS units per pixel at zoom ``z``."""
        return (self.east - self.west) / (self.columns(z) * self.tile_size)

    def tile_bounds(self, z: int, x: int, y: int) -> tuple[float, float, float, float]:
        """``(west, south, east, north)`` of one tile, in CRS units."""
        span_x, span_y = self.tile_span(z)
        west = self.west + x * span_x
        north = self.north - y * span_y
        return west, north - span_y, west + span_x, north

    def flip_y(self, z: int, y: int) -> int:
        """Convert between XYZ and TMS row numbering (the operation is its own inverse)."""
        return self.rows(z) - 1 - y

    # -- queries -------------------------------------------------------

    def zoom_for_resolution(self, resolution: float) -> int:
        """The smallest zoom whose pixels are at least as fine as ``resolution``.

        This is how the native zoom of a source raster is determined: at the
        returned zoom the tiles slightly oversample the source rather than
        throwing detail away.
        """
        if resolution <= 0:
            raise ValueError("resolution must be positive")
        exact = math.log2(self.resolution(0) / resolution)
        return max(0, math.ceil(exact - 1e-9))

    def tile_range(self, z: int, bounds: tuple[float, float, float, float]) -> TileRange:
        """Every tile at ``z`` that overlaps ``bounds`` (in CRS units).

        Bounds that land exactly on a tile edge do not drag in the neighbouring
        tile, so a region snapped to the grid produces no empty fringe.
        """
        west, south, east, north = bounds
        if east <= west or north <= south:
            raise ValueError(f"degenerate bounds: {bounds}")

        span_x, span_y = self.tile_span(z)
        eps = 1e-9

        x_min = math.floor((west - self.west) / span_x + eps)
        x_max = math.ceil((east - self.west) / span_x - eps) - 1
        y_min = math.floor((self.north - north) / span_y + eps)
        y_max = math.ceil((self.north - south) / span_y - eps) - 1

        x_min = max(0, min(x_min, self.columns(z) - 1))
        x_max = max(x_min, min(x_max, self.columns(z) - 1))
        y_min = max(0, min(y_min, self.rows(z) - 1))
        y_max = max(y_min, min(y_max, self.rows(z) - 1))
        return TileRange(z, x_min, x_max, y_min, y_max)

    def clamp_bounds(self, bounds: tuple[float, float, float, float]):
        """Intersect ``bounds`` with the scheme's world extent."""
        west = max(bounds[0], self.west)
        south = max(bounds[1], self.south)
        east = min(bounds[2], self.east)
        north = min(bounds[3], self.north)
        if east <= west or north <= south:
            raise ValueError(f"bounds {bounds} do not intersect {self.name} world extent")
        return west, south, east, north


WEB_MERCATOR = TilingScheme(
    name="mercator",
    crs="EPSG:3857",
    west=-MERCATOR_HALF_WORLD,
    south=-MERCATOR_HALF_WORLD,
    east=MERCATOR_HALF_WORLD,
    north=MERCATOR_HALF_WORLD,
    columns_at_zoom_0=1,
    rows_at_zoom_0=1,
)

GEOGRAPHIC = TilingScheme(
    name="geographic",
    crs="EPSG:4326",
    west=-180.0,
    south=-90.0,
    east=180.0,
    north=90.0,
    columns_at_zoom_0=2,
    rows_at_zoom_0=1,
)

SCHEMES = {WEB_MERCATOR.name: WEB_MERCATOR, GEOGRAPHIC.name: GEOGRAPHIC}
