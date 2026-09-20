#!/usr/bin/env python
"""Download the current FAA IFR high enroute charts and build tileset-ifr-high.

    .venv/Scripts/python scripts/build_ifr_high.py [--no-fetch] [--detect] [--resume]

Runs fetch_charts.py, render_pdfs.py, heal_frames.py and build_chart_tileset.py
for the ifr-high series, replacing the tileset. The same four stages as
build_ifr_low.py, on the same scripts: these are the same charts drawn at a
smaller scale, so nothing about the pipeline is different.

H-01 to H-12 cover the lower 48 on twelve sheets, where the low charts need 36.
Like them, the sheets are drawn from the FAA's vector PDFs at 4x rather than
from its GeoTIFFs, which are badly rasterised; only the PDFs are downloaded.
``--detect`` also fetches the GeoTIFFs and re-derives both manifests from them,
which is the only thing they are needed for.

Zoom: z12, one level shallower than ifr-low, because a high chart is drawn at
half the scale. Measured off the downloaded sheets, all twelve are 24000x8000
at 92.60 m/px against the low charts' 46.30, so the 4x render is 23.15 m/px and
a z12 tile minifies it by exactly the ratio a z13 tile minifies a low sheet's.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import chart_series_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(chart_series_main("ifr-high", __doc__.splitlines()[0]))
