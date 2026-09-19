#!/usr/bin/env python
"""Mosaic every sheet of an FAA chart series into one Cesium tileset.

    .venv/Scripts/python scripts/build_chart_tileset.py SERIES [--out DIR] [options]

SERIES is a name from chart_series.py (``sectionals``, ``ifr-low``). Stages,
each its own script so it can be rerun alone:

  1. fetch_charts.py SERIES      download the current edition into source/SERIES
                                 -- GeoTIFFs, or just the vector PDFs for a
                                 series that renders its own rasters
  2. detect_*_areas.py           find each sheet's map area into
                                 scripts/SERIES_areas.json; rerun and review
                                 for every new edition.
                                   sectionals: detect_sectional_areas.py
                                   ifr-low:    detect_ifr_areas.py
  3. render_pdfs.py SERIES       (ifr-low) draw the sheets from their PDFs at 4x
  4. heal_frames.py SERIES       (ifr-low) paint over the frame rule
  5. this script                 mosaic the sheets into z/x/y tiles

Overlaps are resolved by file name: sheets are painted in lexicographic order,
so where two overlap, the one later in the alphabet is on top. ``--reverse-order``
paints in reverse, putting the earliest name on top; each series sets its own
default (on for ``ifr-low``), and ``--no-reverse-order`` overrides it. Either way
it is a placeholder for a smarter rule, not a considered choice.

Tiles are lossy WebP q90 unless the series sets ``lossless`` (``ifr-low`` does);
``--[no-]lossless`` overrides it.

The warp is exact by default and resamples with cubic. ``--warp-tolerance`` lets
it approximate the projection (in source pixels, like gdalwarp's -et) and
``--resampling bilinear`` takes the cheaper reconstruction filter; both trade
fidelity for speed on either backend, and both are meant for trials rather than
for a chart being kept.

Max zoom comes from the series (``max_zoom``), currently z11 for both, and
``--max-zoom`` overrides it. The sheets' native resolution is about z12 -- the
lower 48 sectionals ~z11.6, the finest IFR sheets ~z12.0 -- so z11 trades some
detail for about a quarter of the tiles.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cesiumtiles.mosaic import MapArea, MosaicSource, build_mosaic  # noqa: E402
from chart_series import SERIES, series  # noqa: E402

QUALITY = 90  # lossy WebP where a series is not lossless: large tilesets, and q90 keeps type legible


def check_stages(chart_series) -> None:
    """Refuse to tile a preparation stage that is missing or older than its input.

    The chain starts at whatever the series downloads: the GeoTIFFs, or the PDFs
    for a series that draws its own rasters from them.
    """
    if chart_series.pdf_scale:
        # Nothing but PDFs is downloaded, so the sheet list comes from the
        # reviewed registration rather than from a directory of GeoTIFFs.
        manifest = json.loads(chart_series.pdf_manifest.read_text(encoding="utf-8"))
        names = sorted(n for n in manifest if chart_series.wants_tif(n))
        previous = {n: chart_series.pdf_directory / manifest[n]["pdf"] for n in names}
    else:
        names = sorted(p.name for p in chart_series.directory.glob("*.tif")
                       if chart_series.wants_tif(p.name))
        previous = {n: chart_series.directory / n for n in names}

    for script, after in chart_series.stages:
        stale = [n for n in names if not (after / n).is_file()
                 or (after / n).stat().st_mtime < previous[n].stat().st_mtime]
        if stale:
            raise SystemExit(f"{len(stale)} sheet(s) missing or out of date in {after}, e.g. {stale[0]}; "
                             f"run scripts/{script} {chart_series.name} first")
        previous = {n: after / n for n in names}


def sources(chart_series, directory: Path, manifest: dict) -> list[MosaicSource]:
    # The series' patterns and exclusions apply here too: they are not normally
    # downloaded, but an older download may have left unwanted sheets behind.
    charts = sorted(p for p in directory.glob("*.tif") if chart_series.wants_tif(p.name))
    if not charts:
        raise SystemExit(
            f"no GeoTIFFs in {directory}; run scripts/fetch_charts.py {chart_series.name} first")
    missing = [p.name for p in charts if p.name not in manifest]
    if missing:
        raise SystemExit(
            "no map area recorded for: " + ", ".join(missing)
            + "\ndetect and review map areas first (see this script's docstring)"
        )
    # Map areas are recorded against the downloaded GeoTIFFs, so their pixel
    # polygons scale with a series that tiles renders drawn at a multiple of it.
    return [MosaicSource(p, MapArea.from_dict(manifest[p.name], chart_series.pixel_scale))
            for p in charts]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", choices=sorted(SERIES))
    ap.add_argument("--out", type=Path, help="output tileset (default: tileset-SERIES)")
    ap.add_argument("--charts", type=Path,
                    help="directory of GeoTIFFs (default: source/SERIES, or its healed/ "
                         "subdirectory for a series that heals frames)")
    ap.add_argument("--max-zoom", type=int, default=None, help="default: the series' setting")
    ap.add_argument("--min-zoom", type=int, default=0)
    ap.add_argument("--quality", type=int, default=QUALITY, help="lossy WebP quality (default: %(default)s)")
    ap.add_argument("--lossless", action=argparse.BooleanOptionalAction, default=None,
                    help="lossless WebP tiles (default: the series' setting)")
    ap.add_argument("--workers", type=int, default=None,
                    help="render processes (default: all cores on the CPU backend, 4 on the GPU)")
    ap.add_argument("--warp", choices=("gpu", "cpu"), default="cpu",
                    help="how max-zoom tiles are resampled (default: %(default)s). "
                         "gpu evaluates the projection per pixel in torch and "
                         "prefilters isotropically; cpu uses gdal.Warp. Sources "
                         "whose projection the gpu path does not implement fall "
                         "back to gdal automatically.")
    ap.add_argument("--resampling", default="cubic",
                    help="resampling kernel for the max-zoom warp (default: %(default)s). "
                         "All the pipelines use cubic, on the measurement that lanczos "
                         "rang most and cubic halved it at nearly the same sharpness; "
                         "bilinear is cheaper again, and on the gpu backend markedly so.")
    ap.add_argument("--warp-tolerance", type=float, default=0.0, metavar="PIXELS",
                    help="how far the warp may cut the projection's corner, in source "
                         "pixels (default: %(default)s, exact). On the cpu backend this is "
                         "gdal.Warp's errorThreshold, whose own default is 0.125; on the gpu "
                         "backend it widens the lattice the projection is evaluated on. "
                         "Exactness is deliberate for a chart being kept -- any non-zero "
                         "threshold moved ~1%% of pixels by up to the full range on chart "
                         "hairlines -- so this is for trials, previews and benchmarks.")
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="build from just these charts (file name prefixes)")
    ap.add_argument("--reverse-order", action=argparse.BooleanOptionalAction, default=None,
                    help="paint sheets in reverse file-name order, so the earliest name is on "
                         "top where sheets overlap (default: the series' setting)")
    ap.add_argument("--resume", action="store_true", help="keep tiles already written")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing tileset")
    args = ap.parse_args(argv)
    chart_series = series(args.series)
    out = args.out or chart_series.tileset

    manifest = json.loads(chart_series.manifest.read_text(encoding="utf-8"))
    directory = args.charts or chart_series.build_directory
    if not args.charts:
        check_stages(chart_series)
    chosen = sources(chart_series, directory, manifest)
    if args.only:
        chosen = [s for s in chosen if any(Path(s.path).name.startswith(n) for n in args.only)]
        if not chosen:
            raise SystemExit(f"--only matched no charts: {args.only}")
    reverse = chart_series.reverse_order if args.reverse_order is None else args.reverse_order
    if reverse:
        chosen.reverse()
    print(f"paint order: {'reverse ' if reverse else ''}file name, "
          f"{Path(chosen[-1].path).name} on top", flush=True)

    lossless = chart_series.lossless if args.lossless is None else args.lossless
    print(f"tiles: WebP {'lossless' if lossless else f'q{args.quality}'}", flush=True)
    print(f"warp: {args.warp}, {args.resampling}, tolerance {args.warp_tolerance:g} source px",
          flush=True)

    result = build_mosaic(
        chosen, out,
        min_zoom=args.min_zoom, max_zoom=args.max_zoom if args.max_zoom is not None else chart_series.max_zoom,
        quality=args.quality, lossless=lossless, backend=args.warp,
        resampling=args.resampling, tolerance=args.warp_tolerance,
        workers=args.workers, resume=args.resume, overwrite=args.overwrite,
        title=chart_series.title,
    )
    print(result.summary())
    print(f"preview it with:  .venv/Scripts/cesiumtiles-serve {out.parent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
