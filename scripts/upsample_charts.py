#!/usr/bin/env python
"""Super-resolve every sheet of a chart series before it is tiled.

    .venv/Scripts/python scripts/upsample_charts.py SERIES [--model M] [--force] [CHART ...]

The FAA's VFR sectionals are rasterised badly -- edges staircase at any zoom --
and unlike the IFR charts there is no vector source to fall back on, because the
sectional PDFs wrap the very same rasters. So the sheets are run through
Real-CUGAN 2x (``upsample_model`` and ``upsample_scale`` in the series), which
the user compared side by side against a plain build of the same sheets at the
same zoom and kept.

Whole sheets are upsampled, not just their map areas. Cropping first would save
time, but it puts an offset as well as a scale between the reviewed manifests
and the raster, and ``Series.pixel_scale`` is deliberately only a scale.

This is the slow stage. On the GPU it is minutes; on the CPU build of torch it
is hours, and ``upsample.py`` reports which it is using. A copy newer than its
input is skipped unless ``--force``.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from osgeo import gdal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart_series import SERIES, series  # noqa: E402
from layout import MODELS  # noqa: E402
from upsample import best_device, load_model, upsample_raster  # noqa: E402

gdal.UseExceptions()

SCRIPT = "upsample_charts.py"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", choices=sorted(SERIES))
    ap.add_argument("charts", nargs="*", help="chart file names (default: all)")
    ap.add_argument("--model", default=None, help="weights (default: the series' setting)")
    ap.add_argument("--device", default=None, help="torch device (default: cuda if available)")
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="rewrite copies that are up to date")
    args = ap.parse_args(argv)
    chart_series = series(args.series)
    if not chart_series.upsample_scale:
        raise SystemExit(f"{chart_series.name} does not upsample its sheets")

    in_dir = chart_series.input_directory(SCRIPT)
    out_dir = chart_series.upscaled_directory
    names = args.charts or sorted(p.name for p in in_dir.glob("*.tif")
                                  if chart_series.wants_tif(p.name))
    if not names:
        raise SystemExit(f"no rasters in {in_dir}; run the earlier stages first")

    out_dir.mkdir(parents=True, exist_ok=True)
    todo = [n for n in names
            if args.force or not (out_dir / n).is_file()
            or (out_dir / n).stat().st_mtime < (in_dir / n).stat().st_mtime]

    weights = args.model or str(MODELS / chart_series.upsample_model)
    device = args.device or best_device()
    print(f"{len(todo)} of {len(names)} sheet(s) to upsample "
          f"{chart_series.upsample_scale}x -> {out_dir}", flush=True)
    if device == "cpu":
        print("  torch reports no CUDA device; this will take hours on the CPU",
              file=sys.stderr, flush=True)
    if not todo:
        return 0

    model = load_model(weights, args.threads, device)
    print(f"  model {model.name}", flush=True)
    started = time.monotonic()
    for i, name in enumerate(todo, 1):
        source, target = in_dir / name, out_dir / name
        t0 = time.monotonic()
        # The upsampler reads three bands; the sectionals are palette-indexed,
        # and resampling raw palette indices would blend them into nonsense.
        rgb = gdal.Open(str(source))
        expand = rgb.RasterCount == 1 and rgb.GetRasterBand(1).GetRasterColorTable() is not None
        del rgb
        read_from = source
        vrt = out_dir / (name + ".rgb.vrt")
        if expand:
            gdal.Translate(str(vrt), str(source), format="VRT", rgbExpand="rgb")
            read_from = vrt

        part = out_dir / (name + ".part.tif")
        upsample_raster(read_from, part, model, quiet=True)
        part.replace(target)
        vrt.unlink(missing_ok=True)
        elapsed = time.monotonic() - started
        print(f"  [{i}/{len(todo)}] {name}: {(time.monotonic() - t0) / 60:.1f} min"
              f"{' (palette expanded)' if expand else ''}"
              f", {elapsed / 60:.0f} min so far, ~{elapsed / i * (len(todo) - i) / 60:.0f} min left",
              flush=True)
    print(f"upsampled in {(time.monotonic() - started) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
