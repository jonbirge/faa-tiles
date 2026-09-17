#!/usr/bin/env python
"""Download the current FAA IFR low enroute charts and build tileset-ifr-low.

    .venv/Scripts/python scripts/build_ifr_low.py [--no-fetch] [--detect] [--resume]

Runs fetch_charts.py ifr-low, then build_chart_tileset.py ifr-low, which replaces
the tileset. Takes about 10 minutes on 24 cores and writes ~0.9 GB.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import chart_series_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(chart_series_main("ifr-low", ["detect_ifr_areas.py", "ifr-low"], __doc__.splitlines()[0]))
