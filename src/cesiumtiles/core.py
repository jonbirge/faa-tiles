"""Build a static z/x/y tile pyramid from a GeoTIFF, ready to serve to Cesium.

The tiling itself is delegated to GDAL's ``gdal raster tile`` algorithm, which
since GDAL 3.11 is the maintained reference implementation (``gdal2tiles`` is
deprecated in favour of it from 3.13). This module adds the parts it does not
cover: cropping to a geographic rectangle, choosing sensible zoom defaults, and
emitting Cesium-flavoured metadata and a viewer.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from osgeo import gdal, osr

from cesiumtiles.scheme import SCHEMES, TilingScheme

gdal.UseExceptions()

__all__ = ["TilesetResult", "TileBuildError", "build_tileset"]

# Our scheme names -> the OGC TileMatrixSet that gdal raster tile implements.
_GDAL_TILING_SCHEME = {"mercator": "WebMercatorQuad", "geographic": "WorldCRS84Quad"}

_FORMATS = {
    "webp": ("WEBP", ".webp"),
    "png": ("PNG", ".png"),
    "jpeg": ("JPEG", ".jpg"),
}


class TileBuildError(RuntimeError):
    """Raised when a tileset cannot be built."""


@dataclass
class TilesetResult:
    """What a build produced, read back from disk rather than assumed."""

    output_dir: Path
    tile_dir: Path
    scheme: str
    crs: str
    tile_format: str
    min_zoom: int
    max_zoom: int
    native_zoom: int
    tile_count: int
    total_bytes: int
    bounds_lonlat: tuple[float, float, float, float]
    per_zoom: dict[int, int] = field(default_factory=dict)

    @property
    def total_mb(self) -> float:
        return self.total_bytes / 1e6

    def summary(self) -> str:
        w, s, e, n = self.bounds_lonlat
        lines = [
            f"tileset  {self.output_dir}",
            f"scheme   {self.scheme} ({self.crs}), {self.tile_format}, XYZ convention",
            f"zooms    {self.min_zoom}-{self.max_zoom} (source resolution reached at z{self.native_zoom})",
            f"extent   {w:.4f},{s:.4f} .. {e:.4f},{n:.4f}  lon/lat",
            f"tiles    {self.tile_count:,} totalling {self.total_mb:.1f} MB",
        ]
        for z in sorted(self.per_zoom):
            lines.append(f"           z{z:<3d} {self.per_zoom[z]:>8,d}")
        return "\n".join(lines)


def _oriented(srs: osr.SpatialReference) -> osr.SpatialReference:
    """Force lon/lat (x, y) ordering, so coordinates mean what they look like."""
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


def _srs_from(value: str) -> osr.SpatialReference:
    srs = osr.SpatialReference()
    srs.SetFromUserInput(value)
    return _oriented(srs)


def _srs_from_wkt(wkt: str) -> osr.SpatialReference:
    srs = osr.SpatialReference()
    srs.ImportFromWkt(wkt)
    return _oriented(srs)


def _to_lonlat(wkt: str) -> osr.CoordinateTransformation:
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    return osr.CoordinateTransformation(_srs_from_wkt(wkt), _oriented(wgs84))


def _reproject_bounds(transform, bounds, samples: int = 32):
    """Reproject a rectangle by densifying its edges, not just its four corners.

    A rectangle in one projection is generally a curve in another, so sampling
    along the edges is what stops the result from clipping off the bulging side.
    """
    west, south, east, north = bounds
    points = []
    for i in range(samples + 1):
        f = i / samples
        x = west + (east - west) * f
        y = south + (north - south) * f
        points += [(x, south), (x, north), (west, y), (east, y)]

    projected = [transform.TransformPoint(x, y)[:2] for x, y in points]
    xs = [p[0] for p in projected]
    ys = [p[1] for p in projected]
    return min(xs), min(ys), max(xs), max(ys)


def _rectangle_wkt(bounds) -> str:
    west, south, east, north = bounds
    corners = f"{west} {south},{east} {south},{east} {north},{west} {north},{west} {south}"
    return f"POLYGON(({corners}))"


def _source_extent(dataset) -> tuple[float, float, float, float]:
    gt = dataset.GetGeoTransform()
    if gt is None or gt == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        raise TileBuildError("source has no geotransform; it is not georeferenced")
    west = gt[0]
    north = gt[3]
    east = west + gt[1] * dataset.RasterXSize
    south = north + gt[5] * dataset.RasterYSize
    return min(west, east), min(south, north), max(west, east), max(south, north)


def _native_zoom(dataset, grid: TilingScheme) -> int:
    """The zoom whose pixels match the source's own resolution."""
    target = _srs_from(grid.crs)
    warped = gdal.AutoCreateWarpedVRT(dataset, dataset.GetProjection(), target.ExportToWkt())
    if warped is None:
        raise TileBuildError("could not reproject the source into the tiling CRS")
    return grid.zoom_for_resolution(abs(warped.GetGeoTransform()[1]))


def _scan_tiles(tile_dir: Path, suffix: str):
    """Count what is actually on disk, rather than trusting what we asked for."""
    per_zoom: dict[int, int] = {}
    extent_by_zoom: dict[int, tuple[int, int, int, int]] = {}
    total_bytes = 0

    for z_dir in sorted(p for p in tile_dir.iterdir() if p.is_dir() and p.name.isdigit()):
        columns, rows, count = [], [], 0
        for x_dir in (p for p in z_dir.iterdir() if p.is_dir() and p.name.isdigit()):
            found = [p for p in x_dir.iterdir() if p.suffix == suffix and p.stem.isdigit()]
            if not found:
                continue
            columns.append(int(x_dir.name))
            rows.extend(int(p.stem) for p in found)
            count += len(found)
            total_bytes += sum(p.stat().st_size for p in found)
        if count:
            z = int(z_dir.name)
            per_zoom[z] = count
            extent_by_zoom[z] = (min(columns), max(columns), min(rows), max(rows))

    return per_zoom, total_bytes, extent_by_zoom


def _creation_options(driver: str, lossless: bool, quality: int) -> list[str]:
    if driver == "WEBP":
        return ["LOSSLESS=TRUE"] if lossless else [f"QUALITY={quality}"]
    if driver == "PNG":
        return ["ZLEVEL=9"]
    if driver == "JPEG":
        return [f"QUALITY={quality}"]
    return []


def _discard(path: str | None) -> None:
    """Remove a scratch VRT, ignoring a file that is already gone."""
    if path:
        try:
            os.unlink(path)
        except OSError:
            pass


def _crop(dataset, source_path: Path, bbox, bbox_crs, source_lonlat) -> tuple[str, tuple]:
    """Clip the source to ``bbox`` exactly, using a warp cutline.

    Returns the path of a VRT on disk rather than an open dataset. For large
    jobs ``gdal raster tile`` parallelises by spawning child ``gdal`` processes,
    each handling a range of tiles, so its input has to be something a separate
    process can open: an anonymous dataset fails outright (and silently drops to
    one thread on jobs small enough not to spawn), and a ``/vsimem`` path is
    invisible outside this process. A real file keeps cropping fully parallel.
    """
    west, south, east, north = bbox
    if east <= west or north <= south:
        raise ValueError(
            f"bbox must be (west, south, east, north) with east>west and north>south, got {bbox}"
        )

    to_source = osr.CoordinateTransformation(
        _srs_from(bbox_crs), _srs_from_wkt(dataset.GetProjection())
    )
    requested = _reproject_bounds(to_source, bbox)
    extent = _source_extent(dataset)

    overlaps = (
        requested[0] < extent[2]
        and requested[2] > extent[0]
        and requested[1] < extent[3]
        and requested[3] > extent[1]
    )
    if not overlaps:
        raise TileBuildError(
            f"bbox {bbox} ({bbox_crs}) does not overlap the source, whose extent in lon/lat is "
            f"{tuple(round(v, 4) for v in source_lonlat)}"
        )

    clipped = (
        max(requested[0], extent[0]),
        max(requested[1], extent[1]),
        min(requested[2], extent[2]),
        min(requested[3], extent[3]),
    )
    handle, vrt_path = tempfile.mkstemp(prefix="cesiumtiles-crop-", suffix=".vrt")
    os.close(handle)
    cropped = gdal.Warp(
        vrt_path,
        str(source_path),
        format="VRT",
        outputBounds=clipped,
        dstSRS=dataset.GetProjection(),
        cutlineWKT=_rectangle_wkt(bbox),
        cutlineSRS=bbox_crs,
        dstAlpha=True,
        resampleAlg="near",
    )
    if cropped is None:
        raise TileBuildError("cropping the source failed")
    cropped.FlushCache()
    del cropped  # close the handle; workers reopen the VRT by name
    return vrt_path, clipped


def build_tileset(
    source: str | Path,
    output_dir: str | Path,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    bbox_crs: str = "EPSG:4326",
    scheme: str = "mercator",
    min_zoom: int = 0,
    max_zoom: int | None = None,
    tile_format: str = "webp",
    lossless: bool = True,
    quality: int = 95,
    resampling: str = "cubic",
    overview_resampling: str = "lanczos",
    threads: str | int = "ALL_CPUS",
    skip_blank: bool = False,
    resume: bool = False,
    overwrite: bool = False,
    title: str | None = None,
    quiet: bool = False,
) -> TilesetResult:
    """Cut ``source`` into a static XYZ tile pyramid under ``output_dir``.

    ``max_zoom`` defaults to the zoom at which tile pixels match the source's own
    resolution, so no detail is thrown away and none is invented. ``bbox`` is
    ``(west, south, east, north)`` in ``bbox_crs`` -- lon/lat degrees by default
    -- and crops the source exactly, via a warp cutline, before tiling. Pass
    ``bbox_crs="source"`` to give the rectangle in the source raster's own CRS,
    which is what you want for trimming to a map's neatline.

    Tiles land in ``output_dir/tiles/{z}/{x}/{y}.<ext>`` alongside a
    ``metadata.json``. No viewer is written into the tileset; serve it with
    ``cesiumtiles-serve``, which hosts the tile tester itself.
    """
    source = Path(source)
    output_dir = Path(output_dir)

    if not source.is_file():
        raise FileNotFoundError(f"source not found: {source}")
    if scheme not in SCHEMES:
        raise ValueError(f"scheme must be one of {sorted(SCHEMES)}, got {scheme!r}")
    if tile_format not in _FORMATS:
        raise ValueError(f"tile_format must be one of {sorted(_FORMATS)}, got {tile_format!r}")

    grid = SCHEMES[scheme]
    driver, suffix = _FORMATS[tile_format]
    tile_dir = output_dir / "tiles"

    if output_dir.exists() and any(output_dir.iterdir()) and not (overwrite or resume):
        raise FileExistsError(f"{output_dir} is not empty (pass overwrite=True or resume=True)")
    if overwrite and not resume and output_dir.exists():
        shutil.rmtree(output_dir)
    tile_dir.mkdir(parents=True, exist_ok=True)

    dataset = gdal.Open(str(source))
    if not dataset.GetProjection():
        raise TileBuildError(f"source has no CRS; georeference it first: {source}")

    # A map's neatline is usually a rectangle in the projection the chart was
    # drawn in, not in lon/lat, so cropping to it needs the source's own frame.
    if bbox is not None and str(bbox_crs).lower() == "source":
        bbox_crs = dataset.GetProjection()

    source_lonlat = _reproject_bounds(_to_lonlat(dataset.GetProjection()), _source_extent(dataset))

    # gdal raster tile clones its input per worker thread, which it can only do
    # for a dataset that has a name, so always hand it a path rather than an
    # open dataset.
    if bbox is None:
        tiling_input, data_bounds_lonlat = str(source.resolve()), source_lonlat
        scratch_vrt = None
    else:
        tiling_input, clipped = _crop(dataset, source.resolve(), bbox, bbox_crs, source_lonlat)
        data_bounds_lonlat = _reproject_bounds(_to_lonlat(dataset.GetProjection()), clipped)
        scratch_vrt = tiling_input

    native = _native_zoom(gdal.Open(tiling_input), grid)
    resolved_max = native if max_zoom is None else max_zoom
    if min_zoom > resolved_max:
        _discard(scratch_vrt)
        raise ValueError(f"min_zoom ({min_zoom}) exceeds max_zoom ({resolved_max})")

    options = {
        "output-format": driver,
        "tiling-scheme": _GDAL_TILING_SCHEME[scheme],
        "convention": "xyz",
        "min-zoom": min_zoom,
        "max-zoom": resolved_max,
        "resampling": resampling,
        "overview-resampling": overview_resampling,
        "num-threads": str(threads),
        "creation-option": _creation_options(driver, lossless, quality),
        "webviewer": ["none"],
    }
    # gdal.Run treats any boolean key that is present as enabled, whatever value
    # it carries, so a flag we do not want must be left out entirely.
    for flag, wanted in (("skip-blank", skip_blank), ("resume", resume), ("quiet", quiet)):
        if wanted:
            options[flag] = True
    # JPEG cannot carry alpha, so the warp must not add one.
    options["no-alpha" if driver == "JPEG" else "add-alpha"] = True

    try:
        gdal.Run("raster", "tile", input=tiling_input, output=str(tile_dir), **options)
    finally:
        _discard(scratch_vrt)

    per_zoom, total_bytes, extent_by_zoom = _scan_tiles(tile_dir, suffix)
    if not per_zoom:
        raise TileBuildError("no tiles were produced; check the bbox and zoom range")

    actual_min, actual_max = min(per_zoom), max(per_zoom)
    x_min, x_max, y_min, y_max = extent_by_zoom[actual_max]
    west, south, _, _ = grid.tile_bounds(actual_max, x_min, y_max)
    _, _, east, north = grid.tile_bounds(actual_max, x_max, y_min)
    covered = _reproject_bounds(
        _to_lonlat(_srs_from(grid.crs).ExportToWkt()), (west, south, east, north)
    )

    result = TilesetResult(
        output_dir=output_dir,
        tile_dir=tile_dir,
        scheme=scheme,
        crs=grid.crs,
        tile_format=tile_format,
        min_zoom=actual_min,
        max_zoom=actual_max,
        native_zoom=native,
        tile_count=sum(per_zoom.values()),
        total_bytes=total_bytes,
        bounds_lonlat=covered,
        per_zoom=per_zoom,
    )

    _write_metadata(result, source, data_bounds_lonlat, suffix, title)
    return result


def _write_metadata(result: TilesetResult, source: Path, data_bounds, suffix: str, title):
    west, south, east, north = result.bounds_lonlat
    metadata = {
        "name": title or source.stem,
        "source": source.name,
        "format": result.tile_format,
        "scheme": result.scheme,
        "crs": result.crs,
        "convention": "xyz",
        "tilesize": 256,
        "minzoom": result.min_zoom,
        "maxzoom": result.max_zoom,
        "nativezoom": result.native_zoom,
        "url_template": f"tiles/{{z}}/{{x}}/{{y}}{suffix}",
        "bounds": [west, south, east, north],
        "data_bounds": [round(v, 8) for v in data_bounds],
        "center": [(west + east) / 2, (south + north) / 2, result.max_zoom],
        "tiles": result.tile_count,
        "bytes": result.total_bytes,
        "tiles_per_zoom": {str(z): n for z, n in sorted(result.per_zoom.items())},
    }
    path = result.output_dir / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    # No viewer is written here: a tileset on disk stays pure data. The
    # tile tester is served by `cesiumtiles-serve`, which can therefore sit
    # above several tilesets and switch between them.
