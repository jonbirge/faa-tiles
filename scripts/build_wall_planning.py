#!/usr/bin/env python
"""Build tileset-planning from the FAA VFR Wall Planning Chart, upsampled.

    .venv/Scripts/python scripts/build_wall_planning.py [build_vfr_tileset.py options]

There is no automated download: the FAA's "Planning Set" link was dead when
this was written (visual/<edition>/All_Files/Planning.zip returned 404 for every
edition). Put the source files in source/wall-planning/ by hand, then run this.

It needs either

    vfr_wall_planning_geo.tif    the chart already georeferenced (reused as is)

or both of

    vfr_geotiff_original.tif     the FAA's palette-indexed GeoTIFF, which carries
                                 the georeferencing
    vfr_wall_planning.tif        the full-colour render of the same sheet, same
                                 pixel size, with no georeferencing

and runs build_vfr_tileset.py, which georeferences the render, crops to the
neatline, upsamples 2x with Real-CUGAN (the winner of the side-by-side against
APISR and waifu2x; weights download on first use) and tiles to z10. Options are
passed through, e.g. --dry-run, --lossless, --max-zoom 7.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import WALL_PLANNING  # noqa: E402
from pipeline import run  # noqa: E402

COMBINED = "vfr_wall_planning_geo.tif"
ORIGINALS = ("vfr_geotiff_original.tif", "vfr_wall_planning.tif")


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    have_combined = (WALL_PLANNING / COMBINED).is_file()
    missing = [name for name in ORIGINALS if not (WALL_PLANNING / name).is_file()]
    if not have_combined and missing:
        WALL_PLANNING.mkdir(parents=True, exist_ok=True)
        print(f"missing source files in {WALL_PLANNING}:", file=sys.stderr)
        for name in missing:
            print(f"  {name}", file=sys.stderr)
        print(f"(or supply {COMBINED} alone). See --help.", file=sys.stderr)
        return 1
    run("build_vfr_tileset.py", *argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
