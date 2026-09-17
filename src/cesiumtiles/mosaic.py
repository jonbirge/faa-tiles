"""Mosaic many overlapping georeferenced rasters into one Web Mercator pyramid.

``build_tileset`` hands a single raster to ``gdal raster tile``. A chart *series*
is a different problem: dozens of sheets, each in its own projection, each with
printed furniture that must not land on the globe, overlapping their neighbours.
This module renders that directly, tile by tile:

1. **Prepare.** Each source's :class:`MapArea` -- neatline limits, polygons to
   keep, polygons to cut out -- is resolved into one polygon in the source's
   pixel space. Traced into Web Mercator it is the source's footprint.
2. **Plan.** Footprints are rasterised row by row onto the max-zoom tile grid,
   giving, for every tile, the ordered list of sources that reach it. Tiles no
   source reaches are never visited, so the empty ocean between Hawaii and the
   mainland costs nothing.
3. **Mask.** The same pixel-space polygon is burnt into a mask raster per
   source, which the warp reads as an alpha band. Any shape works: a neatline
   rectangle, a tilted sheet, a map with an enlarged inset cut out of it.
4. **Render.** Each planned tile warps its contributors with GDAL and composites
   them in source order, later sources on top.
5. **Overviews.** Each lower zoom is built from the four children beneath it,
   one level at a time, every level fully parallel.

Sources that straddle the antimeridian are handled by unwrapping each footprint
around its own centre meridian and warping with a whole-world x offset, so a tile
on either side of 180 degrees draws from the same sheet.
"""

from __future__ import annotations

import json
import math
import multiprocessing as mp
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence
from xml.sax.saxutils import escape

import numpy as np
from osgeo import gdal, ogr, osr

from cesiumtiles.core import TileBuildError, TilesetResult, _scan_tiles
from cesiumtiles.scheme import MERCATOR_HALF_WORLD, WEB_MERCATOR

gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

__all__ = [
    "Limits", "MapArea", "MosaicSource", "Polygon", "PreparedSource",
    "build_mosaic", "covering_arc", "plan_tiles", "prepare_sources",
]

EARTH_RADIUS = 6378137.0
MAX_LATITUDE = 85.0511287798066
TILE_SIZE = 256
# Lon/lat edges are densified at this spacing before projecting, so a
# neatline that follows a parallel stays on it in pixel space.
DENSIFY_DEGREES = 0.01
# Pixel-space edges are split into this many pieces per image width before
# being traced into Mercator, where a straight pixel edge is a curve.
FOOTPRINT_SEGMENTS = 64


# -- geometry ---------------------------------------------------------------

def lon_to_x(lon: float) -> float:
    return lon * MERCATOR_HALF_WORLD / 180.0


def x_to_lon(x: float) -> float:
    return x * 180.0 / MERCATOR_HALF_WORLD


def lat_to_y(lat: float) -> float:
    lat = max(-MAX_LATITUDE, min(MAX_LATITUDE, lat))
    return EARTH_RADIUS * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def y_to_lat(y: float) -> float:
    return math.degrees(2 * math.atan(math.exp(y / EARTH_RADIUS)) - math.pi / 2)


def _unwrap(lon: float, centre: float) -> float:
    """``lon`` moved by whole turns to lie within 180 degrees of ``centre``."""
    return centre + ((lon - centre + 180.0) % 360.0) - 180.0


def _normalise(lon: float) -> float:
    """Longitude into [-180, 180], leaving values already there untouched."""
    while lon > 180.0:
        lon -= 360.0
    while lon < -180.0:
        lon += 360.0
    return lon


def _ring_polygon(points) -> ogr.Geometry:
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in points:
        ring.AddPoint_2D(float(x), float(y))
    ring.CloseRings()
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return poly


def _box(west: float, south: float, east: float, north: float) -> ogr.Geometry:
    return _ring_polygon([(west, south), (east, south), (east, north), (west, north)])


def _map_points(geometry: ogr.Geometry, transform) -> ogr.Geometry:
    """Rebuild a polygonal geometry with every ring's points passed through
    ``transform``, which takes and returns a list of ``(x, y)``."""
    kind = ogr.GT_Flatten(geometry.GetGeometryType())
    if kind == ogr.wkbPolygon:
        out = ogr.Geometry(ogr.wkbPolygon)
        for r in range(geometry.GetGeometryCount()):
            ring = geometry.GetGeometryRef(r)
            moved = transform([ring.GetPoint_2D(i) for i in range(ring.GetPointCount())])
            new_ring = ogr.Geometry(ogr.wkbLinearRing)
            for x, y in moved:
                new_ring.AddPoint_2D(x, y)
            out.AddGeometry(new_ring)
        return out
    if kind in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection):
        out = ogr.Geometry(ogr.wkbMultiPolygon)
        for g in range(geometry.GetGeometryCount()):
            part = geometry.GetGeometryRef(g)
            if ogr.GT_Flatten(part.GetGeometryType()) in (ogr.wkbPolygon, ogr.wkbMultiPolygon):
                mapped = _map_points(part, transform)
                if ogr.GT_Flatten(mapped.GetGeometryType()) == ogr.wkbPolygon:
                    out.AddGeometry(mapped)
                else:
                    for i in range(mapped.GetGeometryCount()):
                        out.AddGeometry(mapped.GetGeometryRef(i))
        return out
    raise TileBuildError(f"expected polygonal geometry, got {geometry.GetGeometryName()}")


def covering_arc(intervals: Sequence[tuple[float, float]]) -> tuple[float, float]:
    """The shortest ``(west, east)`` longitude arc covering every interval.

    Intervals are ``(lo, hi)`` degrees with ``lo <= hi``, and may run past
    +/-180. The result is normalised to [-180, 180]; ``west > east`` means the
    arc crosses the antimeridian, which is how Cesium rectangles express it too.
    """
    if not intervals:
        raise ValueError("no intervals")
    segments = []
    for lo, hi in intervals:
        if hi - lo >= 360.0:
            return -180.0, 180.0
        start = ((lo + 180.0) % 360.0) - 180.0
        segments.append((start, start + (hi - lo)))
    segments.sort()

    merged = [list(segments[0])]
    for lo, hi in segments[1:]:
        if lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])

    # Gap after each merged run; the last one wraps round to the first.
    gaps = [merged[k + 1][0] - merged[k][1] for k in range(len(merged) - 1)]
    gaps.append(merged[0][0] + 360.0 - max(hi for _, hi in merged))
    widest = max(range(len(gaps)), key=gaps.__getitem__)
    if gaps[widest] <= 0:
        return -180.0, 180.0
    if widest == len(gaps) - 1:
        west, east = merged[0][0], max(hi for _, hi in merged)
    else:
        west, east = merged[widest + 1][0], merged[widest][1]
    return _normalise(west), _normalise(east)


def _arc_centre(west: float, east: float) -> float:
    width = east - west if east >= west else east - west + 360.0
    return _normalise(west + width / 2)


# -- sources ----------------------------------------------------------------

@dataclass(frozen=True)
class Limits:
    """Neatline limits in degrees; ``None`` leaves that side to the image edge.

    Sectional neatlines run along meridians and parallels, so this is the
    natural description of a chart's map area, and unlike a pixel box it holds
    from one edition to the next.
    """

    west: float | None = None
    south: float | None = None
    east: float | None = None
    north: float | None = None


@dataclass(frozen=True)
class Polygon:
    """A ring of ``(x, y)`` points: lon/lat degrees, or source image pixels
    (column, row from the top-left) when ``frame`` is ``"pixel"``."""

    points: tuple[tuple[float, float], ...]
    frame: str = "lonlat"

    def __post_init__(self):
        if self.frame not in ("lonlat", "pixel"):
            raise ValueError(f"frame must be 'lonlat' or 'pixel', got {self.frame!r}")
        if len(self.points) < 3:
            raise ValueError("a polygon needs at least three points")


@dataclass(frozen=True)
class MapArea:
    """Which part of a source is map: ``limits``, intersected with the union of
    ``include`` (if any), minus the union of ``exclude``."""

    limits: Limits | None = None
    include: tuple[Polygon, ...] = ()
    exclude: tuple[Polygon, ...] = ()

    @property
    def is_whole_image(self) -> bool:
        return self.limits is None and not self.include and not self.exclude

    @classmethod
    def from_dict(cls, spec: Mapping, pixel_scale: float = 1.0) -> "MapArea":
        """Build from the manifest form::

            {"limits": {"west": -109, "south": 32},
             "include": [{"lonlat": [[lon, lat], ...]}],
             "exclude": [{"pixel": [[col, row], ...]}]}

        ``pixel_scale`` scales the ``pixel`` polygons, for a raster drawn at a
        multiple of the resolution the manifest was recorded against. Polygons
        in ``lonlat`` are on the ground and never scale.
        """
        def polygons(items):
            out = []
            for item in items or ():
                (frame, points), = item.items()
                scale = pixel_scale if frame == "pixel" else 1.0
                out.append(Polygon(tuple((float(x) * scale, float(y) * scale) for x, y in points),
                                   frame))
            return tuple(out)

        limits = spec.get("limits")
        return cls(
            limits=Limits(**limits) if limits is not None else None,
            include=polygons(spec.get("include")),
            exclude=polygons(spec.get("exclude")),
        )


@dataclass(frozen=True)
class MosaicSource:
    path: Path
    area: MapArea = field(default_factory=MapArea)


@dataclass
class PreparedSource:
    """A source resolved for planning and rendering."""

    path: str
    name: str
    pixel_area_wkt: str | None      # None: the whole image is map
    footprint_wkt: str              # Web Mercator, unwrapped around the centre
    lon_range: tuple[float, float]
    lat_range: tuple[float, float]
    native_zoom: int
    mask_path: str | None = None


def _wgs84_based(wkt: str) -> str:
    """The same projection, re-based on the WGS84 geographic CRS.

    Charts are drawn on NAD83, which agrees with WGS84 to about 2 m -- well
    under a z12 pixel. Left as NAD83, PROJ picks between several datum
    transformations depending on where a tile falls and warns that seams may
    appear. Treating the datums as equal gives one exact operation everywhere.
    """
    srs = osr.SpatialReference(wkt)
    if srs.IsProjected():
        wgs84 = osr.SpatialReference()
        wgs84.ImportFromEPSG(4326)
        srs.CopyGeogCSFrom(wgs84)
    elif srs.IsGeographic():
        srs.ImportFromEPSG(4326)
    return srs.ExportToWkt()


def _densify_lonlat(points) -> list[tuple[float, float]]:
    out = []
    ring = list(points) + [points[0]]
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        steps = max(1, math.ceil(max(abs(x1 - x0), abs(y1 - y0)) / DENSIFY_DEGREES))
        out.extend((x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps) for i in range(steps))
    return out


def _prepare(source: MosaicSource) -> PreparedSource | None:
    path = Path(source.path)
    dataset = gdal.Open(str(path))
    wkt = dataset.GetProjection()
    gt = dataset.GetGeoTransform(can_return_null=True)
    if not wkt or gt is None:
        raise TileBuildError(f"source is not georeferenced: {path}")
    inverse = gdal.InvGeoTransform(gt)
    width, height = dataset.RasterXSize, dataset.RasterYSize

    src_srs = osr.SpatialReference(_wgs84_based(wkt))
    src_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    wgs84.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    to_lonlat = osr.CoordinateTransformation(src_srs, wgs84)
    from_lonlat = osr.CoordinateTransformation(wgs84, src_srs)

    def pixels_to_lonlat(points):
        crs = [gdal.ApplyGeoTransform(gt, px, py) for px, py in points]
        return [p[:2] for p in to_lonlat.TransformPoints(crs)]

    centre_lon = pixels_to_lonlat([(width / 2, height / 2)])[0][0]

    def lonlat_to_pixels(points):
        unwrapped = [(_unwrap(lon, centre_lon), lat) for lon, lat in points]
        crs = from_lonlat.TransformPoints(unwrapped)
        return [tuple(gdal.ApplyGeoTransform(inverse, x, y)) for x, y, *_ in crs]

    def to_pixel_polygon(polygon: Polygon) -> ogr.Geometry:
        if polygon.frame == "pixel":
            return _ring_polygon(polygon.points)
        unwrapped = [(_unwrap(lon, centre_lon), lat) for lon, lat in polygon.points]
        return _ring_polygon(lonlat_to_pixels(_densify_lonlat(unwrapped)))

    image = _box(0, 0, width, height)
    area = source.area
    if area.is_whole_image:
        pixel_area = image
    else:
        pixel_area = image.Clone()
        if area.limits is not None:
            # Open sides reach a degree past the image, so they never cut it.
            corners = pixels_to_lonlat([(0, 0), (width, 0), (width, height), (0, height)]
                                       + [(width / 2, 0), (width / 2, height), (0, height / 2), (width, height / 2)])
            lons = [_unwrap(lon, centre_lon) for lon, _ in corners]
            lats = [lat for _, lat in corners]
            lim = area.limits
            west = _unwrap(lim.west, centre_lon) if lim.west is not None else min(lons) - 1
            east = _unwrap(lim.east, centre_lon) if lim.east is not None else max(lons) + 1
            south = lim.south if lim.south is not None else min(lats) - 1
            north = lim.north if lim.north is not None else max(lats) + 1
            if east <= west or north <= south:
                raise ValueError(f"degenerate limits for {path.name}: {lim}")
            box = Polygon(((west, south), (east, south), (east, north), (west, north)))
            pixel_area = pixel_area.Intersection(to_pixel_polygon(box))
        if area.include:
            union = ogr.Geometry(ogr.wkbMultiPolygon)
            for polygon in area.include:
                union = union.Union(to_pixel_polygon(polygon))
            pixel_area = pixel_area.Intersection(union)
        for polygon in area.exclude:
            pixel_area = pixel_area.Difference(to_pixel_polygon(polygon))
    if pixel_area.IsEmpty() or pixel_area.GetArea() <= 0:
        return None

    traced = pixel_area.Clone()
    traced.Segmentize(max(width, height) / FOOTPRINT_SEGMENTS)

    def pixels_to_mercator(points):
        return [(lon_to_x(_unwrap(lon, centre_lon)), lat_to_y(lat)) for lon, lat in pixels_to_lonlat(points)]

    footprint = _map_points(traced, pixels_to_mercator)
    if not footprint.IsValid():
        footprint = footprint.MakeValid()
    min_x, max_x, min_y, max_y = footprint.GetEnvelope()

    # The finest Mercator resolution a source needs is where it is nearest the
    # equator: a ground metre spans 1/cos(latitude) Mercator metres.
    ground = math.hypot(gt[1], gt[4])
    nearest_equator = min(abs(y_to_lat(min_y)), abs(y_to_lat(max_y))) if min_y * max_y > 0 else 0.0
    native = WEB_MERCATOR.zoom_for_resolution(ground / math.cos(math.radians(nearest_equator)))

    return PreparedSource(
        path=str(path),
        name=path.name,
        pixel_area_wkt=None if area.is_whole_image else pixel_area.ExportToWkt(),
        footprint_wkt=footprint.ExportToWkt(),
        lon_range=(x_to_lon(min_x), x_to_lon(max_x)),
        lat_range=(y_to_lat(min_y), y_to_lat(max_y)),
        native_zoom=native,
    )


def prepare_sources(sources: Sequence[MosaicSource]) -> list[PreparedSource]:
    """Resolve every source's map area and footprint. Order is preserved."""
    prepared = []
    for source in sources:
        p = _prepare(source)
        if p is None:
            print(f"warning: {Path(source.path).name} has no map area left; skipped")
            continue
        prepared.append(p)
    if not prepared:
        raise TileBuildError("no source has any map area")
    return prepared


def plan_tiles(prepared: Sequence[PreparedSource], z: int) -> dict[tuple[int, int], list[tuple[int, int]]]:
    """Map each tile ``(x, y)`` at zoom ``z`` to its contributors.

    Contributors are ``(source_index, wrap)`` in source order, where ``wrap`` is
    how many whole worlds the source's unwrapped footprint sits from the tile.
    Each footprint is cut into tile-row strips and each strip's x extent gives
    its columns. That can include a tile inside a concave notch, which then
    renders empty and is not written; it never misses one.
    """
    n = 1 << z
    span = 2 * MERCATOR_HALF_WORLD / n
    eps = 1e-9
    plan: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for index, source in enumerate(prepared):
        footprint = ogr.CreateGeometryFromWkt(source.footprint_wkt)
        min_x, max_x, min_y, max_y = footprint.GetEnvelope()
        row_first = max(0, math.floor((MERCATOR_HALF_WORLD - max_y) / span + eps))
        row_last = min(n - 1, math.ceil((MERCATOR_HALF_WORLD - min_y) / span - eps) - 1)
        for ty in range(row_first, row_last + 1):
            north = MERCATOR_HALF_WORLD - ty * span
            strip = footprint.Intersection(_box(min_x - span, north - span, max_x + span, north))
            if strip.IsEmpty() or strip.GetArea() <= 0:
                continue
            sx0, sx1, _, _ = strip.GetEnvelope()
            col_first = math.floor((sx0 + MERCATOR_HALF_WORLD) / span + eps)
            col_last = math.ceil((sx1 + MERCATOR_HALF_WORLD) / span - eps) - 1
            for tx in range(col_first, col_last + 1):
                wrap = tx // n
                plan.setdefault((tx - wrap * n, ty), []).append((index, wrap))
    return plan


# -- workers ----------------------------------------------------------------

_worker: dict = {}


def _init_worker(sources, tile_dir, suffix, creation_options, resampling, resume, cache_mb):
    gdal.UseExceptions()
    gdal.SetCacheMax(cache_mb * 1024 * 1024)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3857)
    _worker.update(
        sources=sources,
        tile_dir=Path(tile_dir),
        suffix=suffix,
        creation_options=creation_options,
        resampling=resampling,
        resume=resume,
        datasets={},
        webp=gdal.GetDriverByName("WEBP"),
        mem=gdal.GetDriverByName("MEM"),
        mercator_wkt=srs.ExportToWkt(),
    )


def _write_mask(source: PreparedSource) -> str:
    """Burn a source's map area into a Byte mask the size of the source."""
    dataset = gdal.Open(source.path)
    width, height = dataset.RasterXSize, dataset.RasterYSize
    mask = gdal.GetDriverByName("GTiff").Create(
        source.mask_path, width, height, 1, gdal.GDT_Byte,
        options=["COMPRESS=DEFLATE", "TILED=YES", "SPARSE_OK=TRUE"],
    )
    # Identity-like transform with rows counting down, so the pixel-space
    # polygon rasterises onto the pixels it names.
    mask.SetGeoTransform((0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
    layer_ds = ogr.GetDriverByName("MEM").CreateDataSource("")
    layer = layer_ds.CreateLayer("area", geom_type=ogr.wkbMultiPolygon)
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(ogr.CreateGeometryFromWkt(source.pixel_area_wkt))
    layer.CreateFeature(feature)
    gdal.RasterizeLayer(mask, [1], layer, burn_values=[255])
    mask.FlushCache()
    del mask
    return source.name


def _tile_path(z: int, x: int, y: int) -> Path:
    return _worker["tile_dir"] / str(z) / str(x) / f"{y}{_worker['suffix']}"


def _dataset(index: int):
    """The source as a VRT: palette expanded to RGB, so resampling blends colours
    rather than indices; CRS re-based on WGS84 (see ``_wgs84_based``); and, if it
    has a map area, the mask attached as an alpha band, which the warp honours."""
    cached = _worker["datasets"].get(index)
    if cached is not None:
        return cached
    source = _worker["sources"][index]
    base = gdal.Open(source.path)
    band = base.GetRasterBand(1)
    expand = "rgb" if base.RasterCount == 1 and band.GetColorTable() is not None else None
    vrt_path = f"/vsimem/mosaic/{os.getpid()}/{index}.vrt"
    gdal.Translate(vrt_path, base, format="VRT", rgbExpand=expand,
                   outputSRS=_wgs84_based(base.GetProjection()))
    if source.mask_path:
        vrt = gdal.Open(vrt_path, gdal.GA_Update)
        vrt.AddBand(gdal.GDT_Byte)
        alpha = vrt.GetRasterBand(vrt.RasterCount)
        alpha.SetColorInterpretation(gdal.GCI_AlphaBand)
        alpha.SetMetadataItem(
            "source_0",
            f"<SimpleSource><SourceFilename relativeToVRT=\"0\">{escape(source.mask_path)}</SourceFilename>"
            f"<SourceBand>1</SourceBand></SimpleSource>",
            "new_vrt_sources",
        )
        vrt.FlushCache()
        del vrt
    view = gdal.Open(vrt_path)
    _worker["datasets"][index] = view
    return view


def _write_tile(path: Path, color: np.ndarray, alpha: np.ndarray) -> None:
    opaque = bool(alpha.min() == 255)
    bands = 3 if opaque else 4
    mem = _worker["mem"].Create("", TILE_SIZE, TILE_SIZE, bands, gdal.GDT_Byte)
    for b in range(3):
        mem.GetRasterBand(b + 1).WriteArray(color[b])
    if not opaque:
        mem.GetRasterBand(4).WriteArray(alpha)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    _worker["webp"].CreateCopy(str(part), mem, options=_worker["creation_options"])
    os.replace(part, path)


def _finish(accum_color: np.ndarray, accum_alpha: np.ndarray):
    """Premultiplied float accumulators -> straight 8-bit colour and alpha."""
    alpha8 = np.clip(np.rint(accum_alpha * 255.0), 0, 255).astype(np.uint8)
    safe = np.where(accum_alpha > 0, accum_alpha, 1.0)
    color8 = np.clip(np.rint(accum_color / safe), 0, 255).astype(np.uint8)
    return color8, alpha8


def _render_top(task):
    """Warp and composite one max-zoom tile. Returns ``(x, y, written)``."""
    z, x, y, contributors = task
    path = _tile_path(z, x, y)
    if _worker["resume"] and path.exists():
        return x, y, True

    span = 2 * MERCATOR_HALF_WORLD / (1 << z)
    west = -MERCATOR_HALF_WORLD + x * span
    north = MERCATOR_HALF_WORLD - y * span

    color = np.zeros((3, TILE_SIZE, TILE_SIZE), np.float32)
    alpha = np.zeros((TILE_SIZE, TILE_SIZE), np.float32)
    # Composite front to back ("under"): the last source is on top, so start
    # there and stop as soon as the tile is opaque; sources beneath are hidden.
    for index, wrap in reversed(contributors):
        tile_west = west + wrap * 2 * MERCATOR_HALF_WORLD
        warped = gdal.Warp(
            "", _dataset(index), format="MEM",
            outputBounds=(tile_west, north - span, tile_west + span, north),
            width=TILE_SIZE, height=TILE_SIZE, dstSRS=_worker["mercator_wkt"],
            dstAlpha=True, resampleAlg=_worker["resampling"],
        )
        pixels = warped.ReadAsArray().astype(np.float32)
        layer_alpha = pixels[-1] / 255.0
        rgb = pixels[:3] if pixels.shape[0] >= 4 else np.repeat(pixels[:1], 3, axis=0)

        weight = (1.0 - alpha) * layer_alpha
        color += weight * rgb
        alpha += weight
        if alpha.min() >= 1.0 - 1e-6:
            break

    if alpha.max() <= 0.5 / 255.0:
        return x, y, False
    _write_tile(path, *_finish(color, alpha))
    return x, y, True


def _render_parent(task):
    """Box-filter four children into their parent. Returns ``(x, y, written)``."""
    z, x, y = task
    path = _tile_path(z, x, y)
    if _worker["resume"] and path.exists():
        return x, y, True

    canvas = np.zeros((4, 2 * TILE_SIZE, 2 * TILE_SIZE), np.float32)
    found = False
    for dy in (0, 1):
        for dx in (0, 1):
            child = _tile_path(z + 1, 2 * x + dx, 2 * y + dy)
            if not child.exists():
                continue
            found = True
            pixels = gdal.Open(str(child)).ReadAsArray().astype(np.float32)
            a = pixels[3] / 255.0 if pixels.shape[0] == 4 else np.ones(pixels.shape[1:], np.float32)
            r0, c0 = dy * TILE_SIZE, dx * TILE_SIZE
            canvas[:3, r0:r0 + TILE_SIZE, c0:c0 + TILE_SIZE] = pixels[:3] * a
            canvas[3, r0:r0 + TILE_SIZE, c0:c0 + TILE_SIZE] = a
    if not found:
        return x, y, False
    # Average premultiplied colour, so transparent pixels do not darken edges.
    small = canvas.reshape(4, TILE_SIZE, 2, TILE_SIZE, 2).mean(axis=(2, 4))
    if small[3].max() <= 0.5 / 255.0:
        return x, y, False
    _write_tile(path, *_finish(small[:3], small[3]))
    return x, y, True


# -- driver -----------------------------------------------------------------

class _Progress:
    def __init__(self, label: str, total: int, quiet: bool, every: float = 10.0):
        self.label, self.total, self.quiet, self.every = label, total, quiet, every
        self.done = 0
        self.start = self.last = time.monotonic()

    def step(self) -> None:
        self.done += 1
        now = time.monotonic()
        if not self.quiet and (now - self.last >= self.every or self.done == self.total):
            self.last = now
            elapsed = now - self.start
            rate = self.done / elapsed if elapsed > 0 else 0.0
            eta = (self.total - self.done) / rate if rate > 0 else 0.0
            print(f"  {self.label}: {self.done:,}/{self.total:,} "
                  f"({100 * self.done / self.total:.1f}%)  {rate:,.0f} tiles/s  "
                  f"eta {eta / 60:.1f} min", flush=True)


def build_mosaic(
    sources: Sequence[MosaicSource],
    output_dir: str | Path,
    *,
    min_zoom: int = 0,
    max_zoom: int | None = None,
    quality: int = 90,
    lossless: bool = False,
    resampling: str = "cubic",
    workers: int | None = None,
    cache_mb: int = 256,
    resume: bool = False,
    overwrite: bool = False,
    title: str | None = None,
    quiet: bool = False,
) -> TilesetResult:
    """Mosaic ``sources`` into ``output_dir/tiles/{z}/{x}/{y}.webp``.

    Sources are painted in the order given, later ones on top where they
    overlap. ``max_zoom`` defaults to the finest native zoom over all sources.
    Tiles are written only where some source has map area.
    """
    output_dir = Path(output_dir)
    tile_dir = output_dir / "tiles"
    suffix = ".webp"
    if output_dir.exists() and any(output_dir.iterdir()) and not (overwrite or resume):
        raise FileExistsError(f"{output_dir} is not empty (pass overwrite=True or resume=True)")
    if overwrite and not resume and output_dir.exists():
        shutil.rmtree(output_dir)
    tile_dir.mkdir(parents=True, exist_ok=True)

    say = (lambda *a: None) if quiet else (lambda *a: print(*a, flush=True))
    started = time.monotonic()

    prepared = prepare_sources(sources)
    native = max(p.native_zoom for p in prepared)
    top = native if max_zoom is None else max_zoom
    if min_zoom > top:
        raise ValueError(f"min_zoom ({min_zoom}) exceeds max_zoom ({top})")

    plan = plan_tiles(prepared, top)
    say(f"{len(prepared)} sources, native zoom z{native}, building z{min_zoom}-z{top}; "
        f"{len(plan):,} tiles planned at z{top}")

    # Masks are build intermediates, kept beside the output (same drive) and
    # removed afterwards, so the tileset itself stays tiles and metadata only.
    mask_dir = Path(tempfile.mkdtemp(prefix=".masks-", dir=output_dir))
    for index, source in enumerate(prepared):
        if source.pixel_area_wkt is not None:
            source.mask_path = str(mask_dir / f"{index}.tif")

    options = ["LOSSLESS=TRUE"] if lossless else [f"QUALITY={quality}"]
    workers = workers or os.cpu_count() or 1
    initargs = (prepared, str(tile_dir), suffix, options, resampling, resume, cache_mb)

    try:
        with mp.get_context("spawn").Pool(workers, _init_worker, initargs) as pool:
            masked = [p for p in prepared if p.mask_path]
            if masked:
                progress = _Progress("masks", len(masked), quiet, every=5.0)
                for _ in pool.imap_unordered(_write_mask, masked):
                    progress.step()

            tasks = [(top, x, y, plan[(x, y)]) for x, y in sorted(plan)]
            progress = _Progress(f"z{top}", len(tasks), quiet)
            written = set()
            for x, y, ok in pool.imap_unordered(_render_top, tasks, chunksize=16):
                if ok:
                    written.add((x, y))
                progress.step()

            for z in range(top - 1, min_zoom - 1, -1):
                parents = sorted({(x >> 1, y >> 1) for x, y in written})
                progress = _Progress(f"z{z}", len(parents), quiet)
                written = set()
                for x, y, ok in pool.imap_unordered(_render_parent, [(z, x, y) for x, y in parents], chunksize=16):
                    if ok:
                        written.add((x, y))
                    progress.step()
    finally:
        shutil.rmtree(mask_dir, ignore_errors=True)

    per_zoom, total_bytes, extent_by_zoom = _scan_tiles(tile_dir, suffix)
    if not per_zoom:
        raise TileBuildError("no tiles were produced")

    actual_top = max(per_zoom)
    n = 1 << actual_top
    columns = {int(p.name) for p in (tile_dir / str(actual_top)).iterdir() if p.name.isdigit()}
    _, _, y_min, y_max = extent_by_zoom[actual_top]
    covered_west, covered_east = covering_arc([(c * 360.0 / n - 180.0, (c + 1) * 360.0 / n - 180.0) for c in columns])
    span = 2 * MERCATOR_HALF_WORLD / n
    covered = (
        covered_west,
        y_to_lat(MERCATOR_HALF_WORLD - (y_max + 1) * span),
        covered_east,
        y_to_lat(MERCATOR_HALF_WORLD - y_min * span),
    )
    data_west, data_east = covering_arc([p.lon_range for p in prepared])
    data_bounds = (
        data_west,
        min(p.lat_range[0] for p in prepared),
        data_east,
        max(p.lat_range[1] for p in prepared),
    )

    result = TilesetResult(
        output_dir=output_dir,
        tile_dir=tile_dir,
        scheme="mercator",
        crs=WEB_MERCATOR.crs,
        tile_format="webp",
        min_zoom=min(per_zoom),
        max_zoom=actual_top,
        native_zoom=native,
        tile_count=sum(per_zoom.values()),
        total_bytes=total_bytes,
        bounds_lonlat=covered,
        per_zoom=per_zoom,
    )
    _write_metadata(result, prepared, data_bounds, title)
    say(f"done in {(time.monotonic() - started) / 60:.1f} min")
    return result


def _write_metadata(result: TilesetResult, prepared, data_bounds, title) -> None:
    west, south, east, north = result.bounds_lonlat
    metadata = {
        "name": title or result.output_dir.name,
        "source": f"{len(prepared)} rasters",
        "sources": [p.name for p in prepared],
        "format": result.tile_format,
        "scheme": result.scheme,
        "crs": result.crs,
        "convention": "xyz",
        "tilesize": TILE_SIZE,
        "minzoom": result.min_zoom,
        "maxzoom": result.max_zoom,
        "nativezoom": result.native_zoom,
        "url_template": "tiles/{z}/{x}/{y}.webp",
        # west > east means the extent crosses the antimeridian, as in Cesium.
        "bounds": [west, south, east, north],
        "data_bounds": [round(v, 8) for v in data_bounds],
        "center": [_arc_centre(west, east), (south + north) / 2, result.max_zoom],
        "tiles": result.tile_count,
        "bytes": result.total_bytes,
        "tiles_per_zoom": {str(z): count for z, count in sorted(result.per_zoom.items())},
    }
    path = result.output_dir / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
