"""Fetch open flightmaps' tiles and assemble them into one raster a region.

open flightmaps (openflightmaps.org) draws VFR charts of most of Europe from a
community-kept database and publishes them, every AIRAC cycle, as finished Web
Mercator tiles: one zip a region, holding three layers at two tile sizes and
eight zoom levels. There is no GeoTIFF to download -- it was withdrawn in 2019
-- so the raster this pipeline wants is put back together from the tiles.

Only one layer, one size and one zoom of each zip is wanted: ``merged`` (the
chart over its base map), 512 px, z11. A 512 px z11 tile is pixel for pixel
four 256 px z12 tiles, so that set *is* the chart at z12 and tiling it costs no
resampling. It is about a quarter of a zip, so rather than download the zip:

1. the zip's central directory is read from its tail by ranged requests;
2. the span of the file holding the wanted members is fetched in one request;
3. each tile is cut out of the span, decoded, and written into the raster as
   one block.

The server does not always honour a range: Sweden's zip, at 1.1 GB, came back
whole with a 200. When that happens the zip is downloaded to disk, read there,
and deleted.

The raster is a tiled GeoTIFF in EPSG:3857 with an alpha band, which is where
the publisher's clipping to each region's rectangle survives. Its block size is
the tile size, so assembling it is a copy.

The cycle is computed, not discovered: AIRAC cycles run 28 days from a fixed
date. The zips appear about a week before a cycle takes effect, and a cycle
whose zip is missing falls back to the one before.
"""

from __future__ import annotations

import datetime as dt
import io
import re
import struct
import sys
import time
import urllib.error
import zipfile
import zlib
from pathlib import Path

import numpy as np
from osgeo import gdal, osr
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetchers import (  # noqa: E402
    download, is_current, load_record, remote_state, request, save_record,
)

gdal.UseExceptions()

LAYER = "merged"
TILE = 512
ZOOM = 11
MEMBER = re.compile(rf"clip/{LAYER}/{TILE}/latest/{ZOOM}/(\d+)/(\d+)\.png")

HALF_WORLD = 20037508.342789244
AIRAC_EPOCH = dt.date(2003, 1, 23)
AIRAC_DAYS = 28
BLOCK = 4 << 20


def airac(today: dt.date) -> tuple[str, dt.date]:
    """The AIRAC cycle in effect on ``today`` as ``("YYNN", first day)``."""
    start = AIRAC_EPOCH + dt.timedelta(
        days=(today - AIRAC_EPOCH).days // AIRAC_DAYS * AIRAC_DAYS)
    number = (start - dt.date(start.year, 1, 1)).days // AIRAC_DAYS + 1
    return f"{start.year % 100:02d}{number:02d}", start


def zip_url(index_url: str, cycle: str, region: str) -> str:
    return (f"{index_url.rstrip('/')}/live/{cycle}/tiles/{region}/noninteractive/epsg3857/"
            "slippyTiles_clipped.zip")


class RangeIgnored(OSError):
    """The server answered a ranged request with the whole file."""


class RangeReader(io.RawIOBase):
    """A remote file read by ranged requests, a block at a time, so ``zipfile``
    can find a zip's directory without the zip being downloaded."""

    def __init__(self, url: str, length: int):
        self.url, self.length = url, length
        self.position = 0
        self.blocks: dict[int, bytes] = {}
        self.ignored = False

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.length}[whence]
        self.position = max(0, min(self.length, base + offset))
        return self.position

    def _block(self, index: int) -> bytes:
        if index not in self.blocks:
            first = index * BLOCK
            last = min(self.length, first + BLOCK) - 1
            try:
                self.blocks[index] = fetch_range(self.url, first, last)
            except RangeIgnored:
                # zipfile turns any OSError into "not a zip file", so what
                # really happened is kept here for the caller to read.
                self.ignored = True
                raise
        return self.blocks[index]

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = self.length - self.position
        end = min(self.length, self.position + size)
        out = bytearray()
        while self.position < end:
            index, within = divmod(self.position, BLOCK)
            piece = self._block(index)[within:within + end - self.position]
            out += piece
            self.position += len(piece)
        return bytes(out)

    def readinto(self, buffer) -> int:
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


def fetch_range(url: str, first: int, last: int) -> bytes:
    with request(url, headers={"Range": f"bytes={first}-{last}"}) as response:
        if response.status != 206:
            raise RangeIgnored(f"{url} ignored a ranged request (status {response.status})")
        return response.read()


def wanted_members(url: str, length: int) -> dict[tuple[int, int], zipfile.ZipInfo]:
    """``{(x, y): member}`` for every tile of the wanted layer, size and zoom."""
    reader = RangeReader(url, length)
    try:
        archive = zipfile.ZipFile(reader)
    except zipfile.BadZipFile:
        if reader.ignored:
            raise RangeIgnored(f"{url} ignored a ranged request") from None
        raise
    with archive:
        out = {}
        for info in archive.infolist():
            match = MEMBER.fullmatch(info.filename)
            if match:
                out[(int(match.group(1)), int(match.group(2)))] = info
        return out


def member_bytes(span: bytes, span_start: int, info: zipfile.ZipInfo) -> bytes:
    """One member's file contents, cut out of a span of the zip."""
    at = info.header_offset - span_start
    signature, _, _, method, _, _, _, _, _, name_length, extra_length = struct.unpack(
        "<4sHHHHHIIIHH", span[at:at + 30])
    if signature != b"PK\x03\x04":
        raise OSError(f"no local header for {info.filename} where the directory says")
    start = at + 30 + name_length + extra_length
    data = span[start:start + info.compress_size]
    if method == zipfile.ZIP_STORED:
        return data
    if method == zipfile.ZIP_DEFLATED:
        return zlib.decompress(data, -15)
    raise OSError(f"{info.filename} is compressed by method {method}")


def tiles_by_range(url: str, length: int) -> tuple[dict[tuple[int, int], bytes], int]:
    """The wanted tiles, fetched as one span of the remote zip. Returns the
    tiles and how many bytes were fetched for them."""
    members = wanted_members(url, length)
    if not members:
        raise OSError(f"no {LAYER}/{TILE}/z{ZOOM} tiles in the zip")
    first, last = span_of(members.values())
    last = min(last, length - 1)
    span = fetch_range(url, first, last)
    return {key: member_bytes(span, first, info) for key, info in members.items()}, last - first


def tiles_by_download(url: str, directory: Path) -> tuple[dict[tuple[int, int], bytes], int]:
    """The wanted tiles, from the whole zip downloaded to ``directory``."""
    local = directory / ".tiles.zip"
    try:
        size = download(url, local)
        with zipfile.ZipFile(local) as archive:
            tiles = {}
            for info in archive.infolist():
                match = MEMBER.fullmatch(info.filename)
                if match:
                    tiles[(int(match.group(1)), int(match.group(2)))] = archive.read(info)
        if not tiles:
            raise OSError(f"no {LAYER}/{TILE}/z{ZOOM} tiles in the zip")
        return tiles, size
    finally:
        local.unlink(missing_ok=True)


def span_of(members) -> tuple[int, int]:
    """The byte range holding every member, with room for their local headers,
    whose extra fields the directory does not give the length of."""
    first = min(info.header_offset for info in members)
    last = max(info.header_offset + 30 + len(info.filename.encode()) + 1024 + info.compress_size
               for info in members)
    return first, last


def assemble(tiles: dict[tuple[int, int], bytes], out: Path, cycle: str) -> tuple[int, int]:
    """Write ``{(x, y): PNG bytes}`` at ``ZOOM`` into one GeoTIFF."""
    columns = [x for x, _ in tiles]
    rows = [y for _, y in tiles]
    x0, y0 = min(columns), min(rows)
    width = (max(columns) - x0 + 1) * TILE
    height = (max(rows) - y0 + 1) * TILE
    span = 2 * HALF_WORLD / (1 << ZOOM)

    part = out.with_name(out.name + ".part.tif")
    raster = gdal.GetDriverByName("GTiff").Create(
        str(part), width, height, 4, gdal.GDT_Byte,
        options=["TILED=YES", f"BLOCKXSIZE={TILE}", f"BLOCKYSIZE={TILE}", "COMPRESS=DEFLATE",
                 "PREDICTOR=2", "BIGTIFF=YES", "SPARSE_OK=TRUE", "INTERLEAVE=PIXEL",
                 "ALPHA=YES", "NUM_THREADS=ALL_CPUS"])
    raster.SetGeoTransform((-HALF_WORLD + x0 * span, span / TILE, 0.0,
                            HALF_WORLD - y0 * span, 0.0, -span / TILE))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3857)
    raster.SetProjection(srs.ExportToWkt())
    raster.SetMetadataItem("TIFFTAG_IMAGEDESCRIPTION",
                           f"open flightmaps, AIRAC {cycle}, {LAYER} {TILE} px z{ZOOM}")
    for (x, y), data in sorted(tiles.items()):
        # The merged tiles are palette PNGs; expanded here, so nothing
        # downstream ever resamples a palette index.
        pixels = np.asarray(Image.open(io.BytesIO(data)).convert("RGBA"))
        if pixels.shape[:2] != (TILE, TILE):
            raise OSError(f"tile {x}/{y} is {pixels.shape[1]}x{pixels.shape[0]}, not {TILE}")
        if not pixels[:, :, 3].any():
            continue        # left sparse
        raster.WriteRaster((x - x0) * TILE, (y - y0) * TILE, TILE, TILE,
                           np.ascontiguousarray(pixels.transpose(2, 0, 1)).tobytes(),
                           buf_type=gdal.GDT_Byte, band_list=[1, 2, 3, 4])
    raster.FlushCache()
    raster = None
    part.replace(out)
    return width, height


def region_source(index_url: str, region: str, today: dt.date):
    """``(cycle, url, state)`` for the newest cycle that has the region's zip."""
    cycle, start = airac(today)
    for _ in range(3):
        url = zip_url(index_url, cycle, region)
        try:
            state = remote_state(url)
            if state["length"]:
                return cycle, url, state
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
        cycle, start = airac(start - dt.timedelta(days=1))
    raise OSError(f"no tile zip for {region} in the last three cycles")


def fetch(chart_series, out: Path, list_only: bool) -> int:
    today = dt.date.today()
    print(f"{chart_series.title}: {len(chart_series.regions)} regions, AIRAC {airac(today)[0]} "
          f"-> {out}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    record = load_record(out)
    failed = []
    started = time.monotonic()
    for region in chart_series.regions:
        name = f"{region}.tif"
        try:
            cycle, url, state = region_source(chart_series.index_url, region, today)
            if list_only:
                print(f"  {name}  {cycle}  {state['length'] / 1e6:,.0f} MB  {url}")
                continue
            if is_current(out, name, url, state, record):
                print(f"ok   {name}: current (AIRAC {cycle})", flush=True)
                continue
            t0 = time.monotonic()
            try:
                tiles, fetched = tiles_by_range(url, state["length"])
            except RangeIgnored:
                print(f"     {region}: the server sent the whole zip; downloading it", flush=True)
                tiles, fetched = tiles_by_download(url, out)
            width, height = assemble(tiles, out / name, cycle)
            record[name] = {"url": url, "edition": cycle, **state,
                            "fetched": today.isoformat(), "tiles": len(tiles)}
            save_record(out, record)
            print(f"ok   {name}: AIRAC {cycle}, {len(tiles):,} tiles, {width} x {height} px, "
                  f"{fetched / 1e6:,.0f} of {state['length'] / 1e6:,.0f} MB fetched, "
                  f"{time.monotonic() - t0:.0f}s", flush=True)
        except Exception as exc:
            failed.append(region)
            print(f"FAIL {name}: {exc}", file=sys.stderr, flush=True)
    if not list_only:
        print(f"done in {time.monotonic() - started:.0f}s: "
              f"{len(chart_series.regions) - len(failed)} ok, {len(failed)} failed")
    if failed:
        print("failed: " + ", ".join(failed), file=sys.stderr)
    return 1 if failed else 0
