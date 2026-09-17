"""Download one FAA chart zip and extract the file(s) a series wants from it.

    python scripts/fetch_chart.py SERIES URL [--out DIR]

This is the worker half of ``fetch_charts.py``, which runs a team of these in
parallel. It stands alone so a single chart can be re-fetched by hand.

The zip is streamed to a temp file in the output directory (same drive, so the
final rename is atomic), the members the series keeps are copied out with their
folder path dropped -- GeoTIFFs into the output directory, vector PDFs into its
``pdf/`` subdirectory -- and the zip is deleted. Each file is written as
``.part`` and renamed only once complete, so an interrupted run never leaves a
truncated chart that looks finished. Standard library only.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart_series import Series, series  # noqa: E402

ATTEMPTS = 3
TIMEOUT_S = 60
CHUNK = 1 << 20


def download(url: str, dest: Path) -> int:
    """Stream ``url`` to ``dest``, retrying on failure. Returns bytes written."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT_S) as resp, open(dest, "wb") as f:
                expected = resp.headers.get("Content-Length")
                shutil.copyfileobj(resp, f, CHUNK)
                size = f.tell()
            if expected is not None and size != int(expected):
                raise OSError(f"short read: {size} of {expected} bytes")
            return size
        except OSError as exc:  # URLError and socket timeouts are OSErrors
            if attempt == ATTEMPTS:
                raise
            print(f"  retry {attempt}/{ATTEMPTS - 1} {url}: {exc}", file=sys.stderr, flush=True)
            time.sleep(2 * attempt)
    raise AssertionError("unreachable")


def extract_members(zip_path: Path, out_dir: Path, chart_series: Series) -> list[Path]:
    """Copy the members ``chart_series`` wants flat out of ``zip_path``.

    GeoTIFFs land in ``out_dir``, vector PDFs in its ``pdf/`` subdirectory, so
    one worker handles both kinds of zip.
    """
    written, seen = [], 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            name = PurePosixPath(info.filename).name
            if info.is_dir():
                continue
            lower = name.lower()
            if lower.endswith((".tif", ".tiff")):
                wanted, into = chart_series.wants_tif(name), out_dir
            elif lower.endswith(".pdf"):
                wanted, into = chart_series.wants_pdf(name), out_dir / "pdf"
            else:
                continue
            seen += 1
            if not wanted:
                continue
            into.mkdir(parents=True, exist_ok=True)
            target = into / name
            part = target.with_name(target.name + ".part")
            with zf.open(info) as src, open(part, "wb") as dst:
                shutil.copyfileobj(src, dst, CHUNK)
            os.replace(part, target)
            written.append(target)
    if not seen:
        raise RuntimeError(f"no chart file in {zip_path.name}")
    return written


def fetch(url: str, out_dir: Path, chart_series: Series) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".", suffix=".zip", dir=out_dir)
    os.close(fd)
    zip_path = Path(tmp)
    try:
        download(url, zip_path)
        return extract_members(zip_path, out_dir, chart_series)
    finally:
        zip_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("series", help="chart series name, as in chart_series.py")
    ap.add_argument("url")
    ap.add_argument("--out", type=Path, help="output directory (default: the series directory)")
    args = ap.parse_args(argv)
    chart_series = series(args.series)
    out = args.out or chart_series.directory

    zip_name = PurePosixPath(args.url).name
    start = time.monotonic()
    try:
        tifs = fetch(args.url, out, chart_series)
    except Exception as exc:
        print(f"FAIL {zip_name}: {exc}", file=sys.stderr, flush=True)
        return 1
    mb = sum(t.stat().st_size for t in tifs) / 1e6
    names = ", ".join(t.name for t in tifs) or "nothing wanted"
    print(f"ok   {zip_name} -> {names} ({mb:.0f} MB, {time.monotonic() - start:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
