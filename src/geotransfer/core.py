"""Copy georeferencing metadata from one raster onto a plain image of the same size."""

from __future__ import annotations

import shutil
import warnings
from contextlib import contextmanager
from pathlib import Path

import rasterio
from rasterio.errors import NotGeoreferencedWarning

__all__ = ["GeoReference", "GeoReferenceError", "read_georeference", "copy_geo_metadata"]


@contextmanager
def _open(path, mode="r"):
    """Open a dataset, muting the warning about the missing georeferencing.

    Opening files that lack a geotransform is the whole point of this module,
    so rasterio's NotGeoreferencedWarning is noise here rather than signal.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", NotGeoreferencedWarning)
        with rasterio.open(path, mode) as dataset:
            yield dataset


class GeoReferenceError(RuntimeError):
    """Raised when georeferencing cannot be read from or applied to a dataset."""


class GeoReference:
    """The spatial information that makes a TIFF a GeoTIFF.

    A dataset is georeferenced either by an affine ``transform`` (the common
    case) or by a set of ground control points (``gcps``). RPCs are carried
    along as well for completeness.
    """

    def __init__(self, crs, transform, gcps=None, rpcs=None, area_or_point=None):
        self.crs = crs
        self.transform = transform
        self.gcps = gcps
        self.rpcs = rpcs
        self.area_or_point = area_or_point

    @property
    def has_gcps(self) -> bool:
        return bool(self.gcps and self.gcps[0])

    @property
    def is_georeferenced(self) -> bool:
        if self.has_gcps or self.rpcs:
            return True
        return self.crs is not None and self.transform is not None and not self.transform.is_identity

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        epsg = self.crs.to_string() if self.crs else None
        return f"GeoReference(crs={epsg!r}, transform={self.transform!r}, gcps={len(self.gcps[0]) if self.has_gcps else 0})"


def read_georeference(path: str | Path) -> GeoReference:
    """Read the georeferencing of ``path`` without touching its pixels."""
    path = Path(path)
    with _open(path) as src:
        gcps = src.gcps if src.gcps and src.gcps[0] else None
        try:
            rpcs = src.rpcs or None
        except Exception:  # older/odd drivers may not expose RPCs
            rpcs = None
        return GeoReference(
            crs=src.crs,
            transform=src.transform,
            gcps=gcps,
            rpcs=rpcs,
            area_or_point=src.tags().get("AREA_OR_POINT"),
        )


def copy_geo_metadata(
    reference_path: str | Path,
    image_path: str | Path,
    output_path: str | Path,
    *,
    overwrite: bool = False,
    strict_size: bool = True,
    copy_nodata: bool = False,
) -> Path:
    """Write a new GeoTIFF with the pixels of ``image_path`` and the geo metadata of ``reference_path``.

    The image data is copied byte-for-byte (the file is duplicated and only its
    GeoTIFF header tags are rewritten), so there is no recompression and no
    change to band count, colour interpretation, or compression settings.

    Parameters
    ----------
    reference_path:
        An existing GeoTIFF whose CRS / transform (or GCPs) should be used.
    image_path:
        A TIFF with the same pixel dimensions as ``reference_path`` but no
        georeferencing.
    output_path:
        Where to write the result. Must not already exist unless ``overwrite``.
    overwrite:
        Allow replacing an existing ``output_path``.
    strict_size:
        Raise if the two inputs differ in width/height. Turning this off lets
        you apply a transform to a differently sized image, which will place
        the pixels incorrectly unless you know what you are doing.
    copy_nodata:
        Also copy the reference's nodata value onto the output. Off by default
        because the two files often have different band layouts.

    Returns
    -------
    Path
        The path that was written.
    """
    reference_path = Path(reference_path)
    image_path = Path(image_path)
    output_path = Path(output_path)

    for label, p in (("reference", reference_path), ("image", image_path)):
        if not p.is_file():
            raise FileNotFoundError(f"{label} file not found: {p}")

    if output_path.exists():
        if not overwrite:
            raise FileExistsError(f"output already exists (pass overwrite=True): {output_path}")
        if output_path.samefile(image_path) or output_path.samefile(reference_path):
            raise ValueError("output_path must differ from both input files")

    geo = read_georeference(reference_path)
    if not geo.is_georeferenced:
        raise GeoReferenceError(f"reference has no usable georeferencing: {reference_path}")

    with _open(image_path) as src:
        img_shape = (src.width, src.height)
        driver = src.driver
    if driver != "GTiff":
        raise GeoReferenceError(f"image must be a TIFF, got driver {driver!r}: {image_path}")

    with _open(reference_path) as ref:
        ref_shape = (ref.width, ref.height)
        nodata = ref.nodata

    if strict_size and img_shape != ref_shape:
        raise ValueError(
            "pixel dimensions differ: reference is "
            f"{ref_shape[0]}x{ref_shape[1]}, image is {img_shape[0]}x{img_shape[1]}. "
            "Pass strict_size=False to apply the transform anyway."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image_path, output_path)

    try:
        with _open(output_path, "r+") as dst:
            if geo.crs is not None:
                dst.crs = geo.crs
            if geo.has_gcps:
                dst.gcps = (geo.gcps[0], geo.gcps[1] or geo.crs)
            elif geo.transform is not None:
                dst.transform = geo.transform
            if geo.rpcs:
                dst.rpcs = geo.rpcs
            if geo.area_or_point:
                dst.update_tags(AREA_OR_POINT=geo.area_or_point)
            if copy_nodata and nodata is not None:
                dst.nodata = nodata
    except Exception:
        output_path.unlink(missing_ok=True)
        raise

    written = read_georeference(output_path)
    if not written.is_georeferenced:
        output_path.unlink(missing_ok=True)
        raise GeoReferenceError(f"georeferencing did not stick when writing {output_path}")

    return output_path
