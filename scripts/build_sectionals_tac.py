#!/usr/bin/env python
"""Build tileset-sectionals-tac: the VFR sectionals with the TACs laid over them.

    .venv/Scripts/python scripts/build_sectionals_tac.py [--no-fetch] [--detect] [--resume]

Runs fetch_charts.py, upsample_charts.py and build_chart_tileset.py for the
``sectionals-tac`` composite, replacing the tileset. The composite owns no
sheets: it paints the ``sectionals`` and ``tac`` series, in that order, from
the same directories and the same reviewed manifests those series build their
own tilesets from. So if tileset-sectionals has already been built, the 55
sectionals are neither downloaded nor upsampled again and only the ~35 terminal
area charts are new work.

Zoom: z0-z12 covers the whole mosaic, exactly as tileset-sectionals does, and
one sparse z13 level holds only the tiles the TACs reach. A TAC is 1:250,000 --
21.17 m/px, half the sectionals' pitch -- so z13 is where it stops holding
detail, while tiling the whole country there would quadruple the tileset to
magnify sheets that have nothing more to give. Cesium falls back to the
stretched z12 parent everywhere the detail level is absent, which is what it
would have drawn anyway.

``scripts/tac_areas.json`` is detected and reviewed for the 2026-09-03 edition
already, so a first build needs no ``--detect``. Note that ``--detect`` re-runs
detection for *both* layers and rewrites the reviewed sectional manifest too;
to redo one layer for a new edition, run e.g.
``scripts/detect_sectional_areas.py tac --sheet <dir>`` by hand and review the
contact sheets and the manifest diff.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import chart_series_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(chart_series_main("sectionals-tac", __doc__.splitlines()[0]))
