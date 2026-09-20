#!/usr/bin/env python
"""Mosaic every sheet of an FAA chart series into one Cesium tileset.

    .venv/Scripts/python scripts/build_chart_tileset.py SERIES [--out DIR] [options]

SERIES is a name from chart_series.py (``sectionals``, ``tac``, ``ifr-low``,
``ifr-high``, ``sectionals-tac``). Stages, each its own script so it can be
rerun alone:

  1. fetch_charts.py SERIES      download the current edition into source/SERIES
                                 -- GeoTIFFs, or just the vector PDFs for a
                                 series that renders its own rasters
  2. detect_*_areas.py           find each sheet's map area into
                                 scripts/SERIES_areas.json; rerun and review
                                 for every new edition. Which script is the
                                 series' ``detector``:
                                   sectionals, tac:       detect_sectional_areas.py
                                   ifr-low, ifr-high:     detect_ifr_areas.py
  3. render_pdfs.py SERIES       (the IFR series) draw the sheets from their
                                 PDFs at 4x
  4. heal_frames.py SERIES       (the IFR series) paint over the frame rule
  5. this script                 mosaic the sheets into z/x/y tiles

Overlaps are resolved by file name: sheets are painted in lexicographic order,
so where two overlap, the one later in the alphabet is on top. ``--reverse-order``
paints in reverse, putting the earliest name on top; each series sets its own
default (on for the IFR series), and ``--no-reverse-order`` overrides it. Either way
it is a placeholder for a smarter rule, not a considered choice.

A **composite** series (``sectionals-tac``) paints several series into one
tileset. Its members keep their own downloads, stages and reviewed manifests,
so nothing is fetched or prepared twice; the composite only says which order
they paint in -- every sheet of one layer is below every sheet of the next --
and which of them earn the detail level. That level is one zoom past
``--max-zoom``, holding only the tiles the finer sheets reach: it gives the
terminal area charts their own resolution without quadrupling the mosaic that
surrounds them. ``--no-detail`` builds a plain uniform pyramid instead.

Tiles are lossy WebP q90 unless the series sets ``lossless`` (both IFR series do);
``--[no-]lossless`` overrides it.

The warp is exact by default and resamples with cubic. ``--warp-tolerance`` lets
it approximate the projection (in source pixels, like gdalwarp's -et) and
``--resampling bilinear`` takes the cheaper reconstruction filter; both trade
fidelity for speed on either backend, and both are meant for trials rather than
for a chart being kept.

Max zoom comes from the series (``max_zoom``) and ``--max-zoom`` overrides it.
Each series stops where its *prepared* sheets stop holding detail, which is not
the same as where the downloads do: the sectionals are 42.3 m/px (native z11.5)
and z12.5 once upsampled 2x, so z12; the IFR sheets are drawn from vector at 4x
and resolve past z14, so z13. Match this to whatever the last preparation stage
produces -- the IFR sheets went a whole build at z13 from 2x renders, magnifying,
before that was noticed.
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


def sources(chart_series, directory: Path, manifest: dict, detail: bool = False) -> list[MosaicSource]:
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
            + f"\nrun scripts/{chart_series.detector} {chart_series.name} and review its output"
        )
    # Map areas are recorded against the downloaded GeoTIFFs, so their pixel
    # polygons scale with a series that tiles renders drawn at a multiple of it.
    return [MosaicSource(p, MapArea.from_dict(manifest[p.name], chart_series.pixel_scale),
                         detail=detail)
            for p in charts]


def layers(chart_series, args) -> list[MosaicSource]:
    """Every sheet to paint, in paint order, across a series' layers.

    A plain series is one layer of its own sheets; a composite is its members in
    order, each read from its own directory against its own reviewed manifest,
    so a layer that is already downloaded and prepared is simply reused. Paint
    order runs within a layer first: all of one series' sheets sit below all of
    the next's, whatever their names.
    """
    chosen: list[MosaicSource] = []
    for member in chart_series.members:
        manifest = json.loads(member.manifest.read_text(encoding="utf-8"))
        if args.charts:
            directory = args.charts
        else:
            directory = member.build_directory
            check_stages(member)
        sheets = sources(member, directory, manifest,
                         detail=member.name in chart_series.detail_layers)
        if args.only:
            sheets = [s for s in sheets if any(Path(s.path).name.startswith(n) for n in args.only)]
        reverse = member.reverse_order if args.reverse_order is None else args.reverse_order
        if reverse:
            sheets.reverse()
        if sheets:
            print(f"layer {member.name}: {len(sheets)} sheet{'s' if len(sheets) != 1 else ''} in "
                  f"{'reverse ' if reverse else ''}file-name order, "
                  f"{Path(sheets[-1].path).name} on top", flush=True)
        chosen.extend(sheets)
    if not chosen:
        # sources() has already refused an empty directory, so the only way to
        # get here is a filter that matched nothing.
        raise SystemExit(f"--only matched no charts: {args.only}")
    return chosen


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", choices=sorted(SERIES))
    ap.add_argument("--out", type=Path, help="output tileset (default: tileset-SERIES)")
    ap.add_argument("--charts", type=Path,
                    help="directory of GeoTIFFs (default: source/SERIES, or its healed/ "
                         "subdirectory for a series that heals frames)")
    ap.add_argument("--max-zoom", type=int, default=None, help="default: the series' setting")
    ap.add_argument("--min-zoom", type=int, default=0)
    ap.add_argument("--detail-zoom", type=int, default=None,
                    help="one sparse level past --max-zoom, holding only the tiles the "
                         "series' finer layers reach (default: the series' setting). A "
                         "client falls back to the stretched parent everywhere it is "
                         "absent, as it already does over ocean.")
    ap.add_argument("--detail", action=argparse.BooleanOptionalAction, default=True,
                    help="build the detail level where the series has one (default: yes)")
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

    if args.charts and chart_series.is_composite:
        raise SystemExit(f"--charts cannot stand in for {chart_series.name}'s layers "
                         f"({', '.join(chart_series.layers)}), which read separate directories")
    chosen = layers(chart_series, args)

    max_zoom = args.max_zoom if args.max_zoom is not None else chart_series.max_zoom
    detail_zoom = args.detail_zoom if args.detail_zoom is not None else chart_series.detail_zoom
    if not args.detail or not any(s.detail for s in chosen):
        detail_zoom = 0
    elif detail_zoom and detail_zoom <= max_zoom:
        # A shallow --max-zoom is how a trial build is asked for, and a detail
        # level at or under it is not a level at all.
        print(f"detail level z{detail_zoom} is not past z{max_zoom}; skipping it", flush=True)
        detail_zoom = 0
    if detail_zoom:
        print(f"detail level: z{detail_zoom} over "
              f"{', '.join(chart_series.detail_layers)}", flush=True)

    lossless = chart_series.lossless if args.lossless is None else args.lossless
    print(f"tiles: WebP {'lossless' if lossless else f'q{args.quality}'}", flush=True)
    print(f"warp: {args.warp}, {args.resampling}, tolerance {args.warp_tolerance:g} source px",
          flush=True)

    result = build_mosaic(
        chosen, out,
        min_zoom=args.min_zoom, max_zoom=max_zoom, detail_zoom=detail_zoom or None,
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
