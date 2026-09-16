"""Download every current FAA VFR sectional GeoTIFF into ./sectionals.

    python scripts/fetch_sectionals.py [--workers N] [--out DIR]

Finds the current edition by listing https://aeronav.faa.gov/visual/ and taking
the latest ``MM-DD-YYYY`` directory that is not in the future -- the FAA posts
the next edition's directory before it takes effect, so "newest" is wrong. Then
lists that edition's ``sectional-files/`` and runs a team of
``fetch_sectional.py`` processes over the zips, WORKERS at a time.

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
from pathlib import Path
from urllib.parse import urljoin

# How many fetch_sectional.py processes run at once.
WORKERS = 8

# Charts not wanted in the tileset, by GeoTIFF file name. The FAA packs these
# into the same zip as sheets we do want (both are in Hawaiian_Islands.zip, with
# Hawaiian Islands and Honolulu), so the zip is still downloaded and these are
# simply not extracted. build_sectional_tileset.py skips them too, in case an
# older download left them in ./sectionals.
EXCLUDE = {
    "Mariana Islands Inset SEC.tif",   # Guam
    "Samoan Islands Inset SEC.tif",    # American Samoa
}

BASE_URL = "https://aeronav.faa.gov/visual/"
REPO = Path(__file__).resolve().parent.parent
WORKER = Path(__file__).resolve().parent / "fetch_sectional.py"

HREF = re.compile(r'href="([^"]+)"', re.IGNORECASE)
EDITION = re.compile(r"/(\d{2})-(\d{2})-(\d{4})/$")


def list_links(url: str) -> list[str]:
    """Absolute URLs of every link in an IIS directory listing."""
    with urllib.request.urlopen(url, timeout=60) as resp:
        html = resp.read().decode("utf-8", "replace")
    return [urljoin(url, href) for href in HREF.findall(html)]


def current_edition(today: dt.date) -> tuple[dt.date, str]:
    """The latest edition directory dated on or before ``today``."""
    editions = []
    for link in list_links(BASE_URL):
        m = EDITION.search(link)
        if m:
            month, day, year = map(int, m.groups())
            editions.append((dt.date(year, month, day), link))
    past = [e for e in editions if e[0] <= today]
    if not past:
        raise RuntimeError(f"no edition on or before {today} in {BASE_URL}")
    return max(past)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workers", type=int, default=WORKERS,
                    help=f"parallel downloads (default {WORKERS})")
    ap.add_argument("--out", type=Path, default=REPO / "sectionals",
                    help="output directory (default ./sectionals)")
    args = ap.parse_args(argv)

    date, edition_url = current_edition(dt.date.today())
    files_url = urljoin(edition_url, "sectional-files/")
    zips = sorted(u for u in list_links(files_url) if u.lower().endswith(".zip"))
    if not zips:
        print(f"no zips found at {files_url}", file=sys.stderr)
        return 1

    print(f"edition {date:%Y-%m-%d}: {len(zips)} sectionals from {files_url}")
    print(f"-> {args.out} with {args.workers} workers", flush=True)
    args.out.mkdir(parents=True, exist_ok=True)

    def run(url: str) -> int:
        command = [sys.executable, str(WORKER), url, str(args.out), "--exclude", *sorted(EXCLUDE)]
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
