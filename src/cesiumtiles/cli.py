"""Command line entry point: ``cesiumtiles SOURCE OUTPUT [options]``."""

from __future__ import annotations

import argparse
import sys

from cesiumtiles.core import build_tileset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cesiumtiles",
        description=(
            "Cut a GeoTIFF into a static z/x/y tile pyramid for Cesium. The maximum "
            "zoom defaults to the level at which tile pixels match the source's own "
            "resolution, and only tiles overlapping the data are written."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  cesiumtiles chart.tif ./tileset\n"
            "  cesiumtiles chart.tif ./colorado --bbox -109.1 36.9 -102.0 41.1\n"
            "  cesiumtiles chart.tif ./small --format webp --lossy --quality 95\n"
            "  cesiumtiles chart.tif ./trimmed --bbox-crs source \\\n"
            "      --bbox -2078595 -1374023 2574081 1473465\n"
        ),
    )
    parser.add_argument("source", help="georeferenced input raster (GeoTIFF)")
    parser.add_argument("output", help="directory to write the tileset into")

    crop = parser.add_argument_group("cropping")
    crop.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
        help="crop to this rectangle before tiling (lon/lat degrees by default)",
    )
    crop.add_argument(
        "--bbox-crs",
        default="EPSG:4326",
        metavar="CRS",
        help="CRS the --bbox values are given in, or 'source' for the raster's own "
        "CRS, which is what a map neatline is rectangular in (default: %(default)s)",
    )

    grid = parser.add_argument_group("tile grid")
    grid.add_argument(
        "--scheme",
        choices=["mercator", "geographic"],
        default="mercator",
        help="mercator=EPSG:3857 WebMercatorQuad, geographic=EPSG:4326 WorldCRS84Quad "
        "(default: %(default)s)",
    )
    grid.add_argument("--min-zoom", type=int, default=0, help="lowest zoom to write (default: %(default)s)")
    grid.add_argument(
        "--max-zoom",
        type=int,
        default=None,
        help="highest zoom to write (default: auto, matching the source resolution)",
    )

    img = parser.add_argument_group("tile images")
    img.add_argument("--format", dest="tile_format", choices=["webp", "png", "jpeg"], default="webp",
                     help="tile image format (default: %(default)s)")
    img.add_argument("--lossy", action="store_true",
                     help="use lossy compression for webp (much smaller; may ring on fine linework)")
    img.add_argument("--quality", type=int, default=95, metavar="N",
                     help="quality for lossy webp/jpeg, 1-100 (default: %(default)s)")
    img.add_argument("--resampling", default="lanczos", help="warp kernel for the top zoom (default: %(default)s)")
    img.add_argument("--overview-resampling", default="lanczos",
                     help="kernel used to build lower zooms (default: %(default)s)")
    img.add_argument("--skip-blank", action="store_true",
                     help="omit fully transparent tiles; smaller, but the viewer will see 404s")

    run = parser.add_argument_group("run control")
    run.add_argument("--threads", default="ALL_CPUS", help="worker count or ALL_CPUS (default: %(default)s)")
    run.add_argument("--title", default=None, help="name recorded in metadata and shown in the viewer")
    run.add_argument("-f", "--overwrite", action="store_true", help="replace a non-empty output directory")
    run.add_argument("--resume", action="store_true", help="only write tiles that are missing")
    run.add_argument("-q", "--quiet", action="store_true", help="suppress the GDAL progress bar")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.quality < 1 or args.quality > 100:
        print("error: --quality must be between 1 and 100", file=sys.stderr)
        return 2

    try:
        result = build_tileset(
            args.source,
            args.output,
            bbox=tuple(args.bbox) if args.bbox else None,
            bbox_crs=args.bbox_crs,
            scheme=args.scheme,
            min_zoom=args.min_zoom,
            max_zoom=args.max_zoom,
            tile_format=args.tile_format,
            lossless=not args.lossy,
            quality=args.quality,
            resampling=args.resampling,
            overview_resampling=args.overview_resampling,
            threads=args.threads,
            skip_blank=args.skip_blank,
            resume=args.resume,
            overwrite=args.overwrite,
            title=args.title,
            quiet=args.quiet,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(result.summary())
    print(f"\nserve it with:  python -m http.server -d {result.output_dir} 8000")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
