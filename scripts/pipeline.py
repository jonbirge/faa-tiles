"""Shared plumbing for the build_*.py wrappers: run each stage as its own script.

The wrappers do no work themselves. They run the stage scripts in order, with
this interpreter, stopping at the first failure, so what a wrapper does is
exactly what you would get typing the stages by hand.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time

from chart_series import series as chart_series
from layout import REPO, SCRIPTS


def run(script: str, *args: str) -> None:
    """Run ``scripts/<script>`` with ``args``; exit with its code if it fails."""
    command = [sys.executable, str(SCRIPTS / script), *args]
    print(f"\n=== {script} {' '.join(args)}", flush=True)
    started = time.monotonic()
    code = subprocess.run(command, cwd=REPO).returncode
    if code != 0:
        print(f"=== {script} failed (exit {code}); stopping", file=sys.stderr, flush=True)
        raise SystemExit(code)
    print(f"=== {script} done in {(time.monotonic() - started) / 60:.1f} min", flush=True)


def chart_series_main(series: str, detector: list[str], description: str, argv=None) -> int:
    """fetch -> (detect) -> build for one chart series. ``detector`` is the map
    area script and its arguments."""
    ap = argparse.ArgumentParser(
        description=description,
        epilog="Any other options are passed to build_chart_tileset.py, "
               "e.g. --max-zoom 8 --only ENR_L01 --no-reverse-order.",
    )
    ap.add_argument("--no-fetch", action="store_true",
                    help="use the GeoTIFFs already in source/ instead of downloading")
    ap.add_argument("--detect", action="store_true",
                    help=f"re-run {detector[0]} before building. Off by default: map areas "
                         "are reviewed and committed, and a new edition should be "
                         "detected and reviewed deliberately, not silently")
    ap.add_argument("--resume", action="store_true",
                    help="keep tiles already written instead of rebuilding from scratch")
    args, passthrough = ap.parse_known_args(argv)

    if not args.no_fetch:
        run("fetch_charts.py", series)
    if args.detect:
        run(*detector)
    if chart_series(series).heal_frames:
        run("heal_frames.py", series)
    run("build_chart_tileset.py", series, "--resume" if args.resume else "--overwrite", *passthrough)
    return 0
