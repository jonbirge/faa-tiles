#!/usr/bin/env python
"""Build tileset-worldwide-vfr: every free VFR chart we can find, on one globe.

    .venv/Scripts/python scripts/build_worldwide_vfr.py [--no-fetch] [--detect] [--resume]
                                                        [--redistributable-only]

Runs fetch_charts.py, the preparation stages and build_chart_tileset.py for the
``worldwide-vfr`` composite, replacing the tileset. The composite owns no sheets:
it paints the series listed as its ``layers`` in chart_series.py, bottom to top,
each from its own directory and its own reviewed manifest. The FAA's sectionals
and terminal area charts are two of those layers, read from where
tileset-sectionals-tac already has them, so they are neither downloaded nor
upsampled again.

This is a **stepped** tileset. Its layers run from charts at 1:1,000,000 to
charts at 1:250,000, and tiling all of it at the finest sheets' zoom would
magnify the coarse ones sixteenfold over most of the planet. So each layer is
tiled only as deep as its own ``max_zoom``, every level past the shallowest is
sparse, and a viewer asking for a tile a level does not have falls back to the
stretched parent -- as it already does over ocean. ``fullzoom`` in
metadata.json says how deep the pyramid is complete.

**Free to download is not free to republish.** Each layer's publisher and
licence are recorded in chart_series.py and written into metadata.json, and
several of them -- read the ``note`` on each licence -- reserve republication or
say nothing either way. ``--redistributable-only`` leaves those layers out and
writes tileset-worldwide-vfr-public instead, which is the one to put on a
public site. The research behind each is in docs/worldwide-vfr-research.

Map areas are detected and reviewed per layer, so ``--detect`` here re-runs
detection for *every* layer that has a detector and rewrites their reviewed
manifests, the FAA's included. To redo one layer for a new edition run its
detector by hand, e.g. ``scripts/detect_sectional_areas.py faa-caribbean --sheet
<dir>``, and review the contact sheets and the manifest diff. Layers whose
manifest entries are marked ``manual`` are hand-traced and never re-detected.

Pass ``--workers`` on this build: see CLAUDE.md on what 28 render workers cost.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import chart_series_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(chart_series_main("worldwide-vfr", __doc__.splitlines()[0]))
