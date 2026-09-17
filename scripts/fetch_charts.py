"""Download every current chart file in an FAA chart series.

    python scripts/fetch_charts.py SERIES [--workers N] [--out DIR] [--list]

SERIES is a name from chart_series.py: ``sectionals`` or ``ifr-low``.

Finds the current edition by listing the series' index and taking the latest
``MM-DD-YYYY`` directory that is not in the future -- the FAA posts the next
edition's directory before it takes effect, so "newest" is wrong. Then lists
that edition's zips, keeps the ones the series wants, and runs a team of
``fetch_chart.py`` processes over them, WORKERS at a time.

A series that renders vector PDFs (``pdf_zip_pattern``) fetches those zips in
the same pass, into ``source/SERIES/pdf/``. The GeoTIFFs are downloaded either
way: they carry the georeferencing the renders borrow.

Standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart_series import SERIES, series  # noqa: E402

# How many fetch_chart.py processes run at once.
WORKERS = 8

WORKER = Path(__file__).resolve().parent / "fetch_chart.py"

HREF = re.compile(r'href="([^"]+)"', re.IGNORECASE)
EDITION = re.compile(r"/(\d{2})-(\d{2})-(\d{4})/$")


def list_links(url: str) -> list[str]:
    """Absolute URLs of every link in an IIS directory listing."""
    with urllib.request.urlopen(url, timeout=60) as resp:
        html = resp.read().decode("utf-8", "replace")
    return [urljoin(url, href) for href in HREF.findall(html)]


def current_edition(index_url: str, today: dt.date) -> tuple[dt.date, str]:
    """The latest edition directory under ``index_url`` dated on or before ``today``."""
    editions = []
    for link in list_links(index_url):
        m = EDITION.search(link)
        if m:
            month, day, year = map(int, m.groups())
            editions.append((dt.date(year, month, day), link))
    past = [e for e in editions if e[0] <= today]
    if not past:
        raise RuntimeError(f"no edition on or before {today} in {index_url}")
    return max(past)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", choices=sorted(SERIES))
    ap.add_argument("--workers", type=int, default=WORKERS,
                    help=f"parallel downloads (default {WORKERS})")
    ap.add_argument("--out", type=Path, help="output directory (default: the series directory)")
    ap.add_argument("--list", action="store_true", help="print the zips that would be fetched, then stop")
    ap.add_argument("--tifs", action=argparse.BooleanOptionalAction, default=None,
                    help="download the GeoTIFFs (default: yes, unless the series renders PDFs, "
                         "which needs them only for re-detection)")
    args = ap.parse_args(argv)
    chart_series = series(args.series)
    out = args.out or chart_series.directory
    want_tifs = chart_series.fetches_tifs if args.tifs is None else args.tifs

    date, edition_url = current_edition(chart_series.index_url, dt.date.today())
    files_url = urljoin(edition_url, chart_series.files_path)
    links = list_links(files_url)
    tif_zips = sorted(u for u in links if chart_series.wants_zip(PurePosixPath(urlparse(u).path).name))
    pdf_zips = sorted(u for u in links
                      if chart_series.wants_pdf_zip(PurePosixPath(urlparse(u).path).name))
    if not tif_zips:
        print(f"no wanted zips found at {files_url}", file=sys.stderr)
        return 1
    if chart_series.pdf_zip_pattern and not pdf_zips:
        print(f"no PDF zips found at {files_url}", file=sys.stderr)
        return 1
    zips = (tif_zips if want_tifs else []) + pdf_zips

    kinds = ", ".join(k for k in (f"{len(tif_zips)} GeoTIFF" if want_tifs else "",
                                  f"{len(pdf_zips)} vector PDF" if pdf_zips else "") if k)
    print(f"{chart_series.title}, edition {date:%Y-%m-%d}: {kinds} zips from {files_url}")
    if args.list:
        for u in zips:
            print("  " + PurePosixPath(urlparse(u).path).name)
        return 0
    print(f"-> {out} with {args.workers} workers", flush=True)
    out.mkdir(parents=True, exist_ok=True)

    def run(url: str) -> int:
        command = [sys.executable, str(WORKER), chart_series.name, url, "--out", str(out)]
        return subprocess.run(command).returncode

    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        codes = list(pool.map(run, zips))

    failed = [u.rsplit("/", 1)[-1] for u, c in zip(zips, codes) if c != 0]
    print(f"done in {time.monotonic() - start:.0f}s: "
          f"{len(zips) - len(failed)} ok, {len(failed)} failed")
    if failed:
        print("failed: " + ", ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
