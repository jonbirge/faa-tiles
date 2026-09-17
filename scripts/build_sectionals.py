#!/usr/bin/env python
"""Download the current FAA VFR sectionals and build tileset-sectionals.

    .venv/Scripts/python scripts/build_sectionals.py [--no-fetch] [--detect] [--resume]

Runs fetch_charts.py sectionals, then build_chart_tileset.py sectionals, which
replaces the tileset. Takes about 25 minutes on 24 cores and writes ~5.7 GB.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import chart_series_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(chart_series_main("sectionals", ["detect_sectional_areas.py"], __doc__.splitlines()[0]))
