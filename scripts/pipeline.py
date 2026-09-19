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


def chart_series_main(series: str, description: str, argv=None) -> int:
    """fetch -> (detect) -> prepare -> build for one chart series.

    A composite series has no stages of its own: each of its layers is fetched,
    detected and prepared as the series it is, and the build then paints them
    together. A layer already on disk from its own tileset costs nothing again.
    """
    this = chart_series(series)
    detectors = ", ".join(sorted({m.detector for m in this.members}))
    ap = argparse.ArgumentParser(
        description=description,
        epilog="Any other options are passed to build_chart_tileset.py, "
               "e.g. --max-zoom 8 --only ENR_L01 --no-reverse-order.",
    )
    ap.add_argument("--no-fetch", action="store_true",
                    help="use the GeoTIFFs already in source/ instead of downloading")
    ap.add_argument("--detect", action="store_true",
                    help=f"re-run {detectors} before building. Off by default: map areas "
                         "are reviewed and committed, and a new edition should be "
                         "detected and reviewed deliberately, not silently")
    ap.add_argument("--resume", action="store_true",
                    help="keep tiles already written instead of rebuilding from scratch")
    args, passthrough = ap.parse_known_args(argv)

    if not args.no_fetch:
        # Detection reads the GeoTIFFs; a routine build of a PDF series does not.
        run("fetch_charts.py", series, *(["--tifs"] if args.detect else []))
    for member in this.members:
        if args.detect:
            run(member.detector, member.name)
            if member.pdf_scale:
                run("detect_pdf_windows.py", member.name)
        for script, _output in member.stages:
            run(script, member.name)
    run("build_chart_tileset.py", series, "--resume" if args.resume else "--overwrite", *passthrough)
    return 0
