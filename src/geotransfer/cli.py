"""Command line entry point: ``geotransfer REFERENCE IMAGE OUTPUT``."""

from __future__ import annotations

import argparse
import sys

from geotransfer.core import copy_geo_metadata, read_georeference


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geotransfer",
        description=(
            "Copy the georeferencing (CRS + transform) from a GeoTIFF onto a "
            "plain TIFF of the same pixel size, writing a new GeoTIFF."
        ),
    )
    parser.add_argument("reference", help="GeoTIFF to take the geo metadata from")
    parser.add_argument("image", help="TIFF to take the image data from")
    parser.add_argument("output", help="path of the GeoTIFF to write")
    parser.add_argument("-f", "--overwrite", action="store_true", help="replace output if it exists")
    parser.add_argument(
        "--no-strict-size",
        dest="strict_size",
        action="store_false",
        help="allow inputs with different pixel dimensions",
    )
    parser.add_argument("--copy-nodata", action="store_true", help="also copy the reference nodata value")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        out = copy_geo_metadata(
            args.reference,
            args.image,
            args.output,
            overwrite=args.overwrite,
            strict_size=args.strict_size,
            copy_nodata=args.copy_nodata,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    geo = read_georeference(out)
    print(f"wrote {out}")
    print(f"  crs       {geo.crs.to_string() if geo.crs else None}")
    print(f"  transform {tuple(round(v, 6) for v in geo.transform[:6])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
