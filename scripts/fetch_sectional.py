"""Download one FAA sectional zip and extract the GeoTIFF(s) from it.

    python scripts/fetch_sectional.py URL OUT_DIR [--exclude NAME ...]

This is the worker half of ``fetch_sectionals.py``, which runs a team of these
in parallel. It stands alone so a single chart can be re-fetched by hand.

The zip is streamed to a temp file in ``OUT_DIR`` (same drive, so the final
rename is atomic), every ``.tif`` member is copied out with its folder path
dropped, and the zip is deleted. Each TIFF is written as ``.part`` and renamed
only once complete, so an interrupted run never leaves a truncated chart that
looks finished. Standard library only.
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


def extract_tifs(zip_path: Path, out_dir: Path, exclude=()) -> list[Path]:
    """Copy every .tif member of ``zip_path`` flat into ``out_dir``, except
    those whose file name is in ``exclude``."""
    written, seen = [], 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            name = PurePosixPath(info.filename).name
            if info.is_dir() or not name.lower().endswith((".tif", ".tiff")):
                continue
            seen += 1
            if name in exclude:
                continue
            target = out_dir / name
            part = target.with_name(target.name + ".part")
            with zf.open(info) as src, open(part, "wb") as dst:
                shutil.copyfileobj(src, dst, CHUNK)
            os.replace(part, target)
            written.append(target)
    if not seen:
        raise RuntimeError(f"no .tif in {zip_path.name}")
    return written


def fetch(url: str, out_dir: Path, exclude=()) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".", suffix=".zip", dir=out_dir)
    os.close(fd)
    zip_path = Path(tmp)
    try:
        download(url, zip_path)
        tifs = extract_tifs(zip_path, out_dir, exclude)
    finally:
        zip_path.unlink(missing_ok=True)
    return tifs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("url")
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--exclude", nargs="*", default=[], metavar="NAME",
                    help="GeoTIFF file names inside the zip to skip")
    args = ap.parse_args(argv)

    zip_name = PurePosixPath(args.url).name
    start = time.monotonic()
    try:
        tifs = fetch(args.url, args.out_dir, set(args.exclude))
    except Exception as exc:
        print(f"FAIL {zip_name}: {exc}", file=sys.stderr, flush=True)
        return 1
    mb = sum(t.stat().st_size for t in tifs) / 1e6
    names = ", ".join(t.name for t in tifs)
    print(f"ok   {zip_name} -> {names} ({mb:.0f} MB, {time.monotonic() - start:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
