#!/usr/bin/env python
"""Download the current FAA IFR low enroute charts and build tileset-ifr-low.

    .venv/Scripts/python scripts/build_ifr_low.py [--no-fetch] [--detect] [--resume]

Runs fetch_charts.py, render_pdfs.py, heal_frames.py and build_chart_tileset.py
for the ifr-low series, replacing the tileset.

The sheets are drawn from the FAA's vector PDFs at 2x, not from its GeoTIFFs,
which are badly rasterised; only the PDFs are downloaded. ``--detect`` also
fetches the GeoTIFFs and re-derives both manifests from them, which is the only
thing they are needed for.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import chart_series_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(chart_series_main("ifr-low", ["detect_ifr_areas.py", "ifr-low"], __doc__.splitlines()[0]))
