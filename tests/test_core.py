"""Tests for geotransfer.core, using small synthetic rasters."""

from __future__ import annotations

import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine

from geotransfer import GeoReferenceError, copy_geo_metadata, read_georeference

WIDTH, HEIGHT = 32, 20
TRANSFORM = Affine(262.48, 0.0, -2189360.54, 0.0, -262.47, 1531470.09)
CRS_3857 = CRS.from_epsg(3857)


def _write_geotiff(path, *, count=1, georeferenced=True, width=WIDTH, height=HEIGHT):
    profile = {
        "driver": "GTiff",
        "width": width,
        "height": height,
        "count": count,
        "dtype": "uint8",
        "compress": "lzw",
    }
    if georeferenced:
        profile["crs"] = CRS_3857
        profile["transform"] = TRANSFORM
    rng = np.random.default_rng(0)
    data = rng.integers(0, 256, size=(count, height, width), dtype="uint8")
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data)
    return data


@pytest.fixture
def reference(tmp_path):
    p = tmp_path / "reference.tif"
    _write_geotiff(p, count=1, georeferenced=True)
    return p


@pytest.fixture
def plain(tmp_path):
    p = tmp_path / "plain.tif"
    data = _write_geotiff(p, count=3, georeferenced=False)
    return p, data


def test_copies_crs_and_transform(tmp_path, reference, plain):
    plain_path, _ = plain
    out = copy_geo_metadata(reference, plain_path, tmp_path / "out.tif")

    geo = read_georeference(out)
    assert geo.crs == CRS_3857
    assert geo.transform == TRANSFORM


def test_pixels_are_unchanged(tmp_path, reference, plain):
    plain_path, data = plain
    out = copy_geo_metadata(reference, plain_path, tmp_path / "out.tif")

    with rasterio.open(out) as src:
        assert src.count == 3
        assert src.profile["compress"] == "lzw"
        np.testing.assert_array_equal(src.read(), data)


def test_source_files_untouched(tmp_path, reference, plain):
    plain_path, _ = plain
    before = plain_path.read_bytes()
    copy_geo_metadata(reference, plain_path, tmp_path / "out.tif")
    assert plain_path.read_bytes() == before
    assert read_georeference(plain_path).crs is None


def test_size_mismatch_rejected(tmp_path, reference):
    small = tmp_path / "small.tif"
    _write_geotiff(small, count=3, georeferenced=False, width=WIDTH - 1, height=HEIGHT)
    with pytest.raises(ValueError, match="pixel dimensions differ"):
        copy_geo_metadata(reference, small, tmp_path / "out.tif")


def test_size_mismatch_allowed_when_not_strict(tmp_path, reference):
    small = tmp_path / "small.tif"
    _write_geotiff(small, count=3, georeferenced=False, width=WIDTH - 1, height=HEIGHT)
    out = copy_geo_metadata(reference, small, tmp_path / "out.tif", strict_size=False)
    assert read_georeference(out).transform == TRANSFORM


def test_refuses_to_clobber_without_overwrite(tmp_path, reference, plain):
    plain_path, _ = plain
    out = tmp_path / "out.tif"
    copy_geo_metadata(reference, plain_path, out)
    with pytest.raises(FileExistsError):
        copy_geo_metadata(reference, plain_path, out)
    copy_geo_metadata(reference, plain_path, out, overwrite=True)


def test_ungeoreferenced_reference_rejected(tmp_path, plain):
    plain_path, _ = plain
    bad_ref = tmp_path / "bad_ref.tif"
    _write_geotiff(bad_ref, count=1, georeferenced=False)
    with pytest.raises(GeoReferenceError, match="no usable georeferencing"):
        copy_geo_metadata(bad_ref, plain_path, tmp_path / "out.tif")


def test_missing_input(tmp_path, plain):
    plain_path, _ = plain
    with pytest.raises(FileNotFoundError):
        copy_geo_metadata(tmp_path / "nope.tif", plain_path, tmp_path / "out.tif")
