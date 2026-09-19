#!/usr/bin/env python
"""Download the current FAA VFR sectionals and build tileset-sectionals.

    .venv/Scripts/python scripts/build_sectionals.py [--no-fetch] [--detect] [--resume]

Runs fetch_charts.py, upsample_charts.py and build_chart_tileset.py for the
sectionals series, replacing the tileset.

The sheets are super-resolved 2x with Real-CUGAN first: the FAA's rasters
staircase and, unlike the IFR charts, there is no vector source to fall back on.
Budget for it -- ~48 GB of upsampled sheets and ~52 min on a GPU (hours on a
CPU), then 5.3 GB of z12 tiles in ~26 min (measured 2026-09-18).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import chart_series_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(chart_series_main("sectionals", __doc__.splitlines()[0]))
