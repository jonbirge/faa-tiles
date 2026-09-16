# geotransfer

Copy the georeferencing out of a GeoTIFF and onto a plain TIFF that has the
same pixel dimensions, writing a third file that has the *image data* of the
second and the *spatial reference* of the first.

The use case here: the FAA publishes the U.S. VFR Wall Planning Chart as a
georeferenced but palette-indexed GeoTIFF. A full-colour RGB render of the same
chart at the same resolution has the better pixels but no geo metadata. This
tool marries the two.

## How it works

The image file is duplicated byte-for-byte and only the GeoTIFF header tags are
rewritten. Nothing is decoded, resampled, or recompressed, so band count,
colour interpretation, compression and predictor all survive exactly. A 250 MB
chart takes well under a second.

## Setup

The virtual environment lives in `.venv/`.

```bash
py -3 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pip install -e .
```

Runtime-only install: `-r requirements.txt`.

## Use

As a library:

```python
from geotransfer import copy_geo_metadata

copy_geo_metadata(
    "vfr_geotiff_original.tif",   # has the CRS + transform
    "vfr_wall_planning.tif",      # has the pixels
    "vfr_wall_planning_geo.tif",  # gets both
)
```

From the command line:

```bash
.venv/Scripts/geotransfer vfr_geotiff_original.tif vfr_wall_planning.tif vfr_wall_planning_geo.tif
```

### Options

| Option | Meaning |
| --- | --- |
| `overwrite` / `-f` | Replace `output` if it already exists. Off by default. |
| `strict_size` / `--no-strict-size` | Size checking is on by default; the two inputs must match in width and height. Turn it off only if you know the transform still applies. |
| `copy_nodata` / `--copy-nodata` | Also copy the reference's nodata value. Off by default, since the two files often have different band layouts. |

`read_georeference(path)` is also exported if you just want to inspect a file's
CRS, transform, GCPs and `AREA_OR_POINT` tag.

## What gets copied

CRS, affine transform (or GCPs, plus RPCs, if the reference is georeferenced
that way instead), and the `AREA_OR_POINT` pixel-convention tag. The reference's
colour table, band structure and nodata are **not** copied — those belong to the
image file.

## Tests

```bash
.venv/Scripts/python -m pytest
```

The tests build small synthetic rasters in a temp directory; they don't need
the chart files.

## Layout

```
pyproject.toml          packaging + pytest config
requirements.txt        runtime deps
requirements-dev.txt    runtime + test deps
src/geotransfer/
    core.py             copy_geo_metadata / read_georeference
    cli.py              argparse entry point
tests/test_core.py
```
