#!/usr/bin/env python
"""Draw each sheet from its vector PDF, georeferenced, at the series' scale.

    .venv/Scripts/python scripts/render_pdfs.py SERIES [--workers N] [--force] [CHART ...]

The FAA publishes its IFR enroute charts both as GeoTIFFs and as true vector
PDFs. The GeoTIFFs were rasterised badly -- edges staircase at any zoom -- so
the PDFs are rendered here instead, at ``pdf_scale`` times the GeoTIFF's 400
dpi. That is *rendering*, not upsampling: every pixel is drawn from the vector
geometry, so the type and line work antialias properly. Nothing is upscaled and
no model is involved.

The PDFs carry no georeferencing of their own, so each sheet's affine, CRS and
window into the page come from the reviewed manifest that
``detect_pdf_windows.py`` writes. The affine's four scale and rotation terms are
divided by the scale, leaving the sheet on exactly the same ground at twice the
resolution.

Pages are rendered in blocks, both because a whole sheet at 4x is about 9 GB of
RGB and because pdfium silently stops drawing past ~32767 px (see ``BLOCK``).
A render newer than its PDF and the manifest is skipped unless ``--force``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from osgeo import gdal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart_series import SERIES, series  # noqa: E402

gdal.UseExceptions()

CREATION = ["COMPRESS=DEFLATE", "PREDICTOR=2", "TILED=YES", "BIGTIFF=YES", "NUM_THREADS=2"]

# Output pixels per pdfium call, in both axes. **This must stay well under
# 32767.** pdfium rasterises through AGG, whose cell coordinates overflow past
# about 2^15 device pixels: it returns a bitmap of the full size you asked for,
# fills it white, draws the page frame -- and silently omits the interior beyond
# the limit. Nothing raises and no size is wrong, so it reads as a georeferencing
# fault rather than a rendering one. A whole IFR sheet at 2x is 48000 px wide and
# lost its right third this way. Measured: 31868 px renders completely, 35324 px
# starts dropping content, 47900 px loses everything past ~32000. 8192 is also a
# multiple of the 256 px TIFF tile grid.
BLOCK = 8192


def expected_size(entry: dict, scale: int) -> tuple[int, int]:
    """The pixel size a render of ``entry`` at ``scale`` should have."""
    _x, _y, width, height = entry["window"]
    return width * scale, height * scale


def _is_current_size(target: Path, entry: dict, scale: int) -> bool:
    """Whether an existing render was drawn at the scale now configured.

    The other skip checks are mtimes, which say nothing about ``pdf_scale``:
    raising it leaves every render older-but-present, so they would all be
    kept at the wrong resolution and the build would tile them happily.
    """
    try:
        raster = gdal.Open(str(target))
    except RuntimeError:
        return False
    return (raster.RasterXSize, raster.RasterYSize) == expected_size(entry, scale)


def blocks(total: int, size: int = BLOCK):
    """``(offset, length)`` pairs tiling ``total`` pixels in steps of ``size``."""
    for start in range(0, total, size):
        yield start, min(size, total - start)


def render(pdf_path: str, target: str, entry: dict, scale: int) -> str:
    gdal.UseExceptions()
    started = time.monotonic()
    x0, y0, width, height = entry["window"]
    out_width, out_height = width * scale, height * scale

    geotransform = list(entry["geotransform"])
    for i in (1, 2, 4, 5):  # both pixel sizes and both rotation terms
        geotransform[i] /= scale

    page = pdfium.PdfDocument(pdf_path)[0]
    page_width, page_height = page.get_size()          # points
    per_point = entry["dpi"] / 72.0 * scale            # output pixels per point
    page_px = (round(page_width * per_point), round(page_height * per_point))

    part = target + ".part"
    out = gdal.GetDriverByName("GTiff").Create(part, out_width, out_height, 3,
                                               gdal.GDT_Byte, options=CREATION)
    out.SetGeoTransform(geotransform)
    out.SetProjection(entry["projection"])
    for top, rows in blocks(out_height):
        for left, cols in blocks(out_width):
            page_x, page_y = x0 * scale + left, y0 * scale + top
            # pdfium crops in points, trimmed from each edge: left, bottom, right, top.
            crop = (page_x / per_point,
                    (page_px[1] - page_y - rows) / per_point,
                    (page_px[0] - page_x - cols) / per_point,
                    page_y / per_point)
            bitmap = page.render(scale=per_point, crop=crop, fill_color=(255, 255, 255, 255))
            rgb = np.asarray(bitmap.to_pil().convert("RGB"))
            # Rounding can leave a rendered block a pixel short or long of the box.
            block = np.full((rows, cols, 3), 255, np.uint8)
            h, w = min(rows, rgb.shape[0]), min(cols, rgb.shape[1])
            block[:h, :w] = rgb[:h, :w]
            for band in range(3):
                out.GetRasterBand(band + 1).WriteArray(block[:, :, band], left, top)
    out.FlushCache()
    del out
    Path(part).replace(target)
    return (f"{Path(target).name}: {out_width}x{out_height} px from {Path(pdf_path).name}"
            f" ({time.monotonic() - started:.0f}s)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", choices=sorted(SERIES))
    ap.add_argument("charts", nargs="*", help="chart file names (default: all in the manifest)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--force", action="store_true", help="rewrite renders that are up to date")
    args = ap.parse_args(argv)
    chart_series = series(args.series)
    if not chart_series.pdf_scale:
        raise SystemExit(f"{chart_series.name} does not render PDFs")
    if not chart_series.pdf_manifest.is_file():
        raise SystemExit(f"no {chart_series.pdf_manifest}; run "
                         f"scripts/detect_pdf_windows.py {chart_series.name} first")

    manifest = json.loads(chart_series.pdf_manifest.read_text(encoding="utf-8"))
    names = args.charts or sorted(n for n in manifest if chart_series.wants_tif(n))
    missing = [n for n in names if n not in manifest]
    if missing:
        raise SystemExit(f"no PDF window recorded for {', '.join(missing)}; "
                         f"run detect_pdf_windows.py {chart_series.name} and review it first")

    out_dir = chart_series.render_directory
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = chart_series.pdf_manifest.stat().st_mtime
    todo = []
    for name in names:
        entry = manifest[name]
        pdf_path = chart_series.pdf_directory / entry["pdf"]
        if not pdf_path.is_file():
            raise SystemExit(f"no {pdf_path}; run scripts/fetch_charts.py {chart_series.name} first")
        target = out_dir / name
        if (not args.force and target.is_file()
                and target.stat().st_mtime >= pdf_path.stat().st_mtime
                and target.stat().st_mtime >= stamp
                and _is_current_size(target, entry, chart_series.pdf_scale)):
            continue
        todo.append((str(pdf_path), str(target), entry, chart_series.pdf_scale))
    print(f"{len(todo)} of {len(names)} sheet(s) to render at {chart_series.pdf_scale}x -> {out_dir}",
          flush=True)

    started = time.monotonic()
    with ProcessPoolExecutor(args.workers) as pool:
        for line in pool.map(render, *zip(*todo)) if todo else ():
            print("  " + line, flush=True)
    if todo:
        print(f"rendered in {(time.monotonic() - started) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
