#!/usr/bin/env python
"""Register each chart PDF against its GeoTIFF, and record the georeferencing.

    .venv/Scripts/python scripts/detect_pdf_windows.py SERIES [--out FILE] [CHART ...]

The FAA's vector PDFs are worth rendering -- they antialias properly, where the
published GeoTIFFs carry the staircasing of a bad rasteriser -- but their own
metadata says plainly that they are *not* georeferenced. So this runs once per
edition, against the downloaded GeoTIFFs (``fetch_charts.py SERIES --tifs``),
and writes ``scripts/SERIES_pdf.json``:

  * ``pdf`` and ``window``  which PDF page, and which box of it at the GeoTIFF's
                            own resolution, is this sheet. Usually the whole
                            page, but ENR_L06 is one page holding the two
                            panels the GeoTIFFs publish as ENR_L06N and
                            ENR_L06S, each with its own affine.
  * ``size``                the GeoTIFF's pixel size, which the window must match
  * ``geotransform``        the affine, at the GeoTIFF's resolution
  * ``projection``          the sheet's CRS as WKT
  * ``match``               how well the rendered window matched the GeoTIFF's
                            ink, for review: expect > 0.8

``render_pdfs.py`` then needs the PDFs alone, so routine builds never download
the GeoTIFFs at all. Rerun and review this for every new edition, as with the
map areas.

Registration is coarse-to-fine: an ink-profile correlation over the whole page
at 1/8 scale to find the panel, then an exhaustive +/-16 px search on several
full-resolution windows, whose offsets must agree.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from osgeo import gdal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart_series import SERIES, Series, series  # noqa: E402

gdal.UseExceptions()

DPI = 72.0            # PDF points per inch, to turn page size into pixels
COARSE = 8            # reduction factor for the whole-page search
FINE = 16             # pixels of offset tried each way at full resolution
PROBE = 1200          # size of each full-resolution probe window
PROBES = ((0.30, 0.35), (0.70, 0.35), (0.30, 0.70), (0.70, 0.70), (0.50, 0.50))
MIN_INK = 2000        # a probe with less ink than this says nothing; skip it
MIN_MATCH = 0.70      # below this the sheet is reported as needing a look


def ink(array: np.ndarray) -> np.ndarray:
    """1.0 where the pixel is dark enough to be chart line work or type."""
    return (array[:3].min(axis=0) < 128).astype(np.float32)


def match(a: np.ndarray, b: np.ndarray) -> float:
    norm = np.sqrt(float((a * a).sum()) * float((b * b).sum()))
    return float((a * b).sum() / norm) if norm else 0.0


def pdf_for(chart_series: Series, name: str) -> Path:
    """The PDF holding sheet ``name``: its own, or the one it is a panel of.

    ENR_L06N.tif and ENR_L06S.tif are both panels of ENR_L06.pdf.
    """
    stem = Path(name).stem
    for candidate in (stem, stem.rstrip("NS")):
        path = chart_series.pdf_directory / f"{candidate}.pdf"
        if path.is_file():
            return path
    raise SystemExit(f"no PDF for {name} in {chart_series.pdf_directory}; "
                     f"run scripts/fetch_charts.py {chart_series.name} first")


def render(page, scale: float, box: tuple[int, int, int, int] | None = None,
           page_px: tuple[int, int] | None = None) -> np.ndarray:
    """Render ``page`` at ``scale`` px per point, optionally just ``box``.

    ``box`` is (x, y, w, h) in the page's *full* pixel grid, which ``page_px``
    gives; pdfium crops in points, from each edge.
    """
    crop = (0, 0, 0, 0)
    if box is not None:
        pw, ph = page_px
        x, y, w, h = box
        crop = (x / scale, (ph - y - h) / scale, (pw - x - w) / scale, y / scale)
    bitmap = page.render(scale=scale, crop=crop, fill_color=(255, 255, 255, 255))
    return np.asarray(bitmap.to_pil().convert("RGB")).transpose(2, 0, 1)


def coarse_offset(page, page_px, scale, sheet_ink) -> tuple[int, int]:
    """Where in the page the sheet sits, to within a few full-resolution pixels.

    Correlates row and column ink profiles independently, which is enough: the
    panels are axis-aligned boxes of the page, and far cheaper than a 2-D search
    over a 24000 px wide page.
    """
    page_small = ink(render(page, scale / COARSE))
    sheet_small = sheet_ink

    def best_shift(long_profile, short_profile) -> int:
        span = len(long_profile) - len(short_profile)
        if span <= 0:
            return 0
        scores = [match(short_profile, long_profile[s:s + len(short_profile)])
                  for s in range(span + 1)]
        return int(np.argmax(scores))

    dx = best_shift(page_small.sum(axis=0), sheet_small.sum(axis=0))
    dy = best_shift(page_small.sum(axis=1), sheet_small.sum(axis=1))
    return dx * COARSE, dy * COARSE


def fine_offset(page, page_px, scale, ds, origin) -> tuple[int, int, float]:
    """Refine ``origin`` with full-resolution probes; returns (x, y, match)."""
    width, height = ds.RasterXSize, ds.RasterYSize
    votes, scores = [], []
    for fx, fy in PROBES:
        x = min(max(int(width * fx) - PROBE // 2, 0), width - PROBE)
        y = min(max(int(height * fy) - PROBE // 2, 0), height - PROBE)
        sheet = ink(ds.ReadAsArray(x, y, PROBE, PROBE))
        if sheet.sum() < MIN_INK:
            continue
        box = (origin[0] + x - FINE, origin[1] + y - FINE, PROBE + 2 * FINE, PROBE + 2 * FINE)
        if box[0] < 0 or box[1] < 0 or box[0] + box[2] > page_px[0] or box[1] + box[3] > page_px[1]:
            continue
        rendered = ink(render(page, scale, box, page_px))
        best = (-1.0, 0, 0)
        for dy in range(-FINE, FINE + 1):
            for dx in range(-FINE, FINE + 1):
                window = rendered[FINE + dy:FINE + dy + PROBE, FINE + dx:FINE + dx + PROBE]
                if window.shape != sheet.shape:
                    continue
                score = match(sheet, window)
                if score > best[0]:
                    best = (score, dx, dy)
        votes.append((best[1], best[2]))
        scores.append(best[0])
    if not votes:
        return origin[0], origin[1], 0.0
    dx = int(np.median([v[0] for v in votes]))
    dy = int(np.median([v[1] for v in votes]))
    spread = max(max(abs(v[0] - dx) for v in votes), max(abs(v[1] - dy) for v in votes))
    if spread > 2:
        print(f"    probe offsets disagree by {spread} px: {votes}", file=sys.stderr)
    return origin[0] + dx, origin[1] + dy, float(np.median(scores))


def register(chart_series: Series, name: str) -> dict:
    ds = gdal.Open(str(chart_series.directory / name))
    width, height = ds.RasterXSize, ds.RasterYSize
    pdf_path = pdf_for(chart_series, name)
    page = pdfium.PdfDocument(str(pdf_path))[0]
    pw, ph = page.get_size()

    # The smallest page scale that can hold the sheet. Where the sheet is the
    # whole page the two axes agree exactly; where it is a panel, the page is
    # wider but the same height, so the height decides.
    scale = max(width / pw, height / ph)
    page_px = (round(pw * scale), round(ph * scale))
    dpi = scale * DPI
    if not 100 <= dpi <= 1200:
        raise SystemExit(f"{name}: implausible {dpi:.1f} dpi from a {pw:.0f}x{ph:.0f} pt page")

    if page_px == (width, height):
        origin = (0, 0)  # the sheet is the whole page; nothing to search for
    else:
        small = ds.ReadAsArray(buf_xsize=max(1, width // COARSE), buf_ysize=max(1, height // COARSE))
        origin = coarse_offset(page, page_px, scale, ink(small))
        origin = (min(max(origin[0], 0), page_px[0] - width),
                  min(max(origin[1], 0), page_px[1] - height))
    x, y, score = fine_offset(page, page_px, scale, ds, origin)
    return {
        "pdf": pdf_path.name,
        "window": [x, y, width, height],
        "size": [width, height],
        "dpi": round(dpi, 2),
        "geotransform": [float(v) for v in ds.GetGeoTransform()],
        "projection": ds.GetProjection(),
        "match": round(score, 3),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", choices=sorted(SERIES))
    ap.add_argument("charts", nargs="*", help="chart file names (default: all downloaded)")
    ap.add_argument("--out", type=Path, help="output manifest (default: the series' pdf manifest)")
    args = ap.parse_args(argv)
    chart_series = series(args.series)
    if not chart_series.pdf_scale:
        raise SystemExit(f"{chart_series.name} does not render PDFs")
    out = args.out or chart_series.pdf_manifest

    names = args.charts or sorted(p.name for p in chart_series.directory.glob("*.tif")
                                  if chart_series.wants_tif(p.name))
    if not names:
        raise SystemExit(f"no GeoTIFFs in {chart_series.directory}; run "
                         f"scripts/fetch_charts.py {chart_series.name} --tifs first")

    entries = json.loads(out.read_text(encoding="utf-8")) if out.is_file() and args.charts else {}
    poor = []
    started = time.monotonic()
    for i, name in enumerate(names, 1):
        t0 = time.monotonic()
        entry = register(chart_series, name)
        entries[name] = entry
        x, y, w, h = entry["window"]
        whole = "whole page" if (x, y) == (0, 0) else f"at {x},{y}"
        print(f"[{i}/{len(names)}] {name}: {entry['pdf']} {whole}, {w}x{h} @ {entry['dpi']} dpi, "
              f"match {entry['match']:.3f} ({time.monotonic() - t0:.0f}s)", flush=True)
        if entry["match"] < MIN_MATCH:
            poor.append(name)

    out.write_text(json.dumps(dict(sorted(entries.items())), indent=2) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"\nwrote {out} ({len(entries)} sheets) in {(time.monotonic() - started) / 60:.1f} min")
    if poor:
        print(f"review these, their PDF matched the GeoTIFF poorly: {', '.join(poor)}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
