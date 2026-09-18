"""Render a mosaic's max-zoom tiles on the GPU, one source sheet at a time.

The CPU backend loops over *tiles* and, for each, warps the sheets that reach
it. That shape is wrong for a GPU: every tile re-reads and re-decodes its own
source window, and one 256 px tile is far too little work to be worth a launch.
This inverts the loop, as the user laid it out:

1. **One sheet at a time**, in paint order, bottom first.
2. For that sheet, map *every* tile it touches to a footprint in source pixels,
   in one batched GPU pass.
3. Group those tiles into overlapping **chunks** of the sheet. A whole sheet
   does not fit: the largest is 3.07 Gpx, 9.2 GB as uint8 and ~49 GB as the
   float32 the sampler needs, against 12 GB of VRAM. Each tile is assigned to
   one chunk that contains its entire footprint, so no tile straddles an edge.
4. **Decode each chunk once**, on threads, upload it premultiplied, reduce it to
   the right mip level, and prefilter it once.
5. Sample its tiles in **batches**, all on the GPU.
6. Hand the results to encoder threads. A tile with one contributing sheet --
   the vast majority -- is finished on the GPU and encoded immediately. A seam
   tile is held as a partial until its last sheet has been drawn, then
   composited and encoded **once**; the plan says up front how many sheets each
   tile has.

Encoding runs on threads in this process rather than in worker processes:
GDAL releases the GIL while encoding, 22 threads reach ~1,300 tiles/s, and
nothing has to be pickled between processes. That rate is the floor this stage
is built around -- 713k z13 IFR tiles is ~9 minutes of encoding -- so decode,
GPU and encode all run concurrently rather than in turn.

Only the max zoom is rendered here. Lower zooms are built from it afterwards.
"""

from __future__ import annotations

import math
import os
import queue
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from osgeo import gdal, osr

from cesiumtiles import gpuwarp
from cesiumtiles.scheme import MERCATOR_HALF_WORLD

gdal.UseExceptions()

TILE = 256

# Chunk stride, in mip-level source pixels. A chunk is this plus the largest
# tile footprint and a filter margin, ~6.9k px square for the IFR sheets at z13:
# ~760 MB of float32 RGBA, and about 3 GB at peak through the prefilter.
CHUNK = 6144
# Refuse a chunk bigger than this rather than allocate it. See
# gpuwarp.MAX_WINDOW_PIXELS for why bounds like this exist.
MAX_CHUNK_PIXELS = 72 * 1024 * 1024

# Tiles sampled per GPU call. The float64 coordinate pass is the memory-hungry
# part, ~5 MB per tile, so 128 keeps a batch under 1 GB.
BATCH = 128

# Finished tiles allowed to wait for an encoder (256 KB each).
ENCODE_QUEUE = 2048
# GPU batches allowed to wait for the dispatcher (~33 MB each).
HANDOFF_QUEUE = 8

# Full-resolution rows per decode task, and how many decode at once.
READ_ROWS = 1024
READERS = 8

# Points per tile edge used to find its footprint in the source. The mapping is
# smooth at tile scale; the filter margin covers what a 5x5 lattice misses.
LATTICE = 5

# Share of the card this process may allocate before torch raises, instead of
# the Windows driver spilling into system RAM (see gpuwarp.limit_memory).
MEMORY_SHARE = 0.8

# Seam tiles waiting for their last sheet are held in RAM up to this, then
# spilled to a temporary directory beside the tiles.
PARTIAL_RAM_BYTES = 4 * 2**30


class _Partials:
    """Seam tiles waiting for more sheets: premultiplied float16 ``(4, 256, 256)``."""

    def __init__(self, spill_dir: Path):
        self.ram: dict[tuple[int, int], np.ndarray] = {}
        self.spilled: set[tuple[int, int]] = set()
        self.bytes = 0
        self.peak = 0
        self.spill_dir = spill_dir

    def __contains__(self, key) -> bool:
        return key in self.ram or key in self.spilled

    def _file(self, key) -> Path:
        return self.spill_dir / f"{key[0]}_{key[1]}.npy"

    def put(self, key, value: np.ndarray) -> None:
        value = value.astype(np.float16, copy=False)
        if self.bytes + value.nbytes <= PARTIAL_RAM_BYTES:
            self.ram[key] = value
            self.bytes += value.nbytes
            self.peak = max(self.peak, len(self.ram) + len(self.spilled))
        else:
            self.spill_dir.mkdir(parents=True, exist_ok=True)
            np.save(self._file(key), value)
            self.spilled.add(key)

    def pop(self, key) -> np.ndarray:
        if key in self.ram:
            value = self.ram.pop(key)
            self.bytes -= value.nbytes
            return value.astype(np.float32)
        self.spilled.discard(key)
        path = self._file(key)
        value = np.load(path).astype(np.float32)
        path.unlink()
        return value


class _Encoder:
    """Encoder threads with a bounded queue, so the GPU cannot run ahead of them
    and fill RAM with finished tiles waiting to be written."""

    def __init__(self, threads: int, write_tile, tile_path, creation_options):
        self.pool = ThreadPoolExecutor(threads, thread_name_prefix="encode")
        # Deep enough (~0.5 GB of finished tiles) that the encoders keep working
        # through the main thread's pauses; a shallow queue left them idle for
        # every chunk decode, and the stages ran in turn instead of together.
        self.slots = threading.BoundedSemaphore(ENCODE_QUEUE)
        self.write_tile, self.tile_path = write_tile, tile_path
        self.options = creation_options
        self.written: set[tuple[int, int]] = set()
        self.lock = threading.Lock()
        self.errors: list[BaseException] = []
        self.waited = 0.0   # seconds the main thread spent blocked on a full queue

    def _run(self, x, y, color, alpha):
        try:
            self.write_tile(self.tile_path(x, y), color, alpha, self.options)
            with self.lock:
                self.written.add((x, y))
        except BaseException as exc:  # surfaced on the main thread
            self.errors.append(exc)
        finally:
            self.slots.release()

    def submit(self, x, y, color: np.ndarray, alpha: np.ndarray) -> None:
        if self.errors:
            raise self.errors[0]
        started = time.perf_counter()
        self.slots.acquire()
        self.waited += time.perf_counter() - started
        self.pool.submit(self._run, x, y, color, alpha)

    def close(self) -> None:
        self.pool.shutdown(wait=True)
        if self.errors:
            raise self.errors[0]


def _unpremultiply_uint8(premultiplied: torch.Tensor) -> torch.Tensor:
    """``(B, 4, H, W)`` premultiplied 0..1 to straight ``(B, 4, H, W)`` uint8.

    Matches the CPU path's ``_finish``: alpha rounded to 8 bits, colour divided
    by the unrounded alpha, fully transparent pixels black.
    """
    alpha = premultiplied[:, 3:4].clamp(0.0, 1.0)
    rgb = torch.minimum(premultiplied[:, :3], alpha)
    safe = torch.where(alpha > 0, alpha, torch.ones_like(alpha))
    colour = torch.round(rgb / safe * 255.0).clamp_(0, 255)
    return torch.cat((colour, torch.round(alpha * 255.0)), dim=1).to(torch.uint8)


def _decode_window(path: str, x0: int, y0: int, width: int, height: int, factor: int,
                   readers: ThreadPoolExecutor) -> list[tuple[int, np.ndarray]]:
    """Decode a window into row strips, on several threads.

    Each thread opens its own GDAL handle -- datasets are not shareable across
    threads. CPU only, so it can run while the GPU works on the previous chunk.
    """
    rows = max(factor, (READ_ROWS // factor) * factor)

    def decode(row):
        dataset = gdal.Open(path)
        return row, dataset.ReadAsArray(x0, y0 + row, width, min(rows, height - row))

    return list(readers.map(decode, range(0, height, rows)))


def _upload_window(strips, width: int, height: int, factor: int, device: str) -> torch.Tensor:
    """Decoded strips to one premultiplied float32 ``(4, h, w)`` at the mip level.

    Premultiplied before the box reduction, so masked-out collar cannot bleed
    colour across the map's edge.
    """
    out = torch.zeros((4, height // factor, width // factor), device=device, dtype=torch.float32)
    for row, raw in strips:
        if raw.ndim == 2:
            raw = raw[None]
        pixels = torch.from_numpy(raw).to(device).to(torch.float32).div_(255.0)
        if pixels.shape[0] >= 4:
            rgb, alpha = pixels[:3], pixels[3:4]
        else:
            rgb = pixels[:3] if pixels.shape[0] == 3 else pixels[:1].expand(3, -1, -1)
            alpha = torch.ones_like(rgb[:1])
        block = torch.cat((rgb * alpha, alpha), dim=0)
        if factor > 1:
            block = F.avg_pool2d(block.unsqueeze(0), factor).squeeze(0)
        r0 = row // factor
        out[:, r0:r0 + block.shape[1]] = block
    return out


def _footprints(lcc, inverse, wests, norths, span):
    """Each tile's source-pixel bounding box and scale, from a small lattice.

    Returns ``(col_min, col_max, row_min, row_max, scale)`` as numpy arrays.
    """
    device = wests.device
    frac = torch.linspace(0.0, 1.0, LATTICE, device=device, dtype=torch.float64)
    x = wests[:, None, None] + frac[None, None, :] * span
    y = norths[:, None, None] - frac[None, :, None] * span
    x, y = torch.broadcast_tensors(x, y)
    lon, lat = gpuwarp.mercator_to_lonlat(x, y)
    east, north = lcc.forward(lon, lat)
    a, b, c, d, e, f = (float(v) for v in inverse)
    col = a + b * east + c * north
    row = d + e * east + f * north
    points = torch.stack((col, row), dim=-1)                     # (B, L, L, 2)
    step_px = TILE / (LATTICE - 1)
    across = (points[:, :, 1:] - points[:, :, :-1]).norm(dim=-1).amax(dim=(1, 2))
    down = (points[:, 1:, :] - points[:, :-1, :]).norm(dim=-1).amax(dim=(1, 2))
    scale = torch.maximum(across, down) / step_px
    flat = points.reshape(points.shape[0], -1, 2)
    lo, hi = flat.amin(dim=1), flat.amax(dim=1)
    return (lo[:, 0].cpu().numpy(), hi[:, 0].cpu().numpy(),
            lo[:, 1].cpu().numpy(), hi[:, 1].cpu().numpy(), scale.cpu().numpy())


def render_top(prepared, plan, top: int, tile_dir, creation_options, *,
               resume: bool = False, threads: int | None = None,
               device: str | None = None, resampling: str = "cubic",
               say=print, quiet: bool = False) -> set[tuple[int, int]]:
    """Render every planned max-zoom tile. Returns the ``(x, y)`` written.

    ``prepared`` and ``plan`` are exactly what the CPU backend receives, and
    sources are read through the same :func:`mosaic.source_view`, so the two
    backends see identical pixels. A source whose projection the GPU sampler
    does not implement is warped with GDAL on threads instead, and fed through
    the same compositing, so a series can mix the two.
    """
    from cesiumtiles.mosaic import ERROR_THRESHOLD, TileBuildError, source_view, write_tile

    device = device or gpuwarp.best_device()
    gpuwarp.limit_memory(device, MEMORY_SHARE)
    threads = threads or max(1, (os.cpu_count() or 2) - 2)
    tile_dir = Path(tile_dir)
    n = 1 << top
    span = 2 * MERCATOR_HALF_WORLD / n
    world = 2 * MERCATOR_HALF_WORLD

    def tile_path(x, y):
        return tile_dir / str(top) / str(x) / f"{y}.webp"

    remaining: dict[tuple[int, int], int] = {}
    by_source: dict[int, list[tuple[int, int, int]]] = {}
    already: set[tuple[int, int]] = set()
    for (x, y), contributors in plan.items():
        if resume and tile_path(x, y).exists():
            already.add((x, y))
            continue
        remaining[(x, y)] = len(contributors)
        for index, wrap in contributors:
            by_source.setdefault(index, []).append((x, y, wrap))

    total = len(remaining)
    encoder = _Encoder(threads, write_tile, tile_path, creation_options)
    encoder.written.update(already)
    readers = ThreadPoolExecutor(READERS, thread_name_prefix="decode")
    # One thread that runs a whole chunk's decode (itself fanned out over the
    # readers) ahead of the main thread.
    prefetcher = ThreadPoolExecutor(1, thread_name_prefix="prefetch")
    spill = Path(tempfile.mkdtemp(prefix=".partials-", dir=tile_dir))
    partials = _Partials(spill)
    mercator = osr.SpatialReference()
    mercator.ImportFromEPSG(3857)
    mercator_wkt = mercator.ExportToWkt()

    started = time.monotonic()
    state = {"done": 0, "last": started}
    # Main-thread seconds per stage, reported at the end. Whatever dominates is
    # what the pass is waiting on; "encoder" is time blocked on a full queue.
    # "decode" is only time spent *waiting* for a prefetched chunk; "prefilter"
    # includes uploading it.
    timing = dict(footprints=0.0, decode=0.0, prefilter=0.0, sample=0.0, deliver=0.0)

    def timed(stage, started_at):
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        timing[stage] += time.perf_counter() - started_at

    def report(force=False):
        now = time.monotonic()
        if quiet or not (force or now - state["last"] >= 10.0):
            return
        state["last"] = now
        rate = state["done"] / max(now - started, 1e-9)
        eta = (total - state["done"]) / rate if rate > 0 else 0.0
        say(f"  z{top} (gpu): {state['done']:,}/{total:,} "
            f"({100 * state['done'] / max(total, 1):.1f}%)  {rate:,.0f} tiles/s  "
            f"eta {eta / 60:.1f} min")

    # A tile's number of contributing sheets is fixed by the plan, so whether it
    # can be finished straight off the GPU is known in advance. That lets the
    # main thread do only GPU work and transfers, while a dispatcher thread does
    # the per-tile bookkeeping -- splitting batches, compositing seam tiles,
    # feeding the encoders -- alongside it. Done on the main thread, that
    # bookkeeping cost ~15 s of a 50 s pass on two sheets.
    sheets_per_tile = {key: count for key, count in remaining.items()}
    handoff: queue.Queue = queue.Queue(maxsize=HANDOFF_QUEUE)
    dispatch_errors: list[BaseException] = []

    def dispatch():
        try:
            while True:
                item = handoff.get()
                if item is None:
                    return
                single_keys, finished, multi_keys, layers = item
                for j, key in enumerate(single_keys):
                    remaining[key] = 0
                    state["done"] += 1
                    tile = finished[j]
                    if tile[3].max() == 0:
                        continue                  # nothing of this sheet here
                    encoder.submit(key[0], key[1], tile[:3], tile[3])
                for j, key in enumerate(multi_keys):
                    layer = layers[j].astype(np.float32)
                    if key in partials:
                        # Sheets arrive bottom first, so this one lands *over*.
                        beneath = partials.pop(key)
                        layer = layer + beneath * (1.0 - layer[3:4])
                    remaining[key] -= 1
                    if remaining[key] > 0:
                        partials.put(key, layer)
                        continue
                    state["done"] += 1
                    done = _unpremultiply_uint8(torch.from_numpy(layer[None]))[0].numpy()
                    if done[3].max() > 0:
                        encoder.submit(key[0], key[1], done[:3], done[3])
                report()
        except BaseException as exc:
            dispatch_errors.append(exc)
            while handoff.get() is not None:      # drain so the producer never blocks
                pass

    dispatcher = threading.Thread(target=dispatch, name="dispatch", daemon=True)
    dispatcher.start()

    def deliver(keys, contributions: torch.Tensor):
        """Hand one sheet's contributions to the dispatcher.

        ``contributions`` is ``(B, 4, 256, 256)`` premultiplied 0..1 on the
        device. Single-sheet tiles are finished here, on the GPU, and cross as
        uint8; seam tiles cross as float16 to be composited on the CPU.
        """
        if dispatch_errors:
            raise dispatch_errors[0]
        single = [i for i, k in enumerate(keys) if sheets_per_tile[k] == 1]
        multi = [i for i, k in enumerate(keys) if sheets_per_tile[k] > 1]
        finished = (_unpremultiply_uint8(contributions[single]).cpu().numpy()
                    if single else None)
        layers = (contributions[multi].to(torch.float16).cpu().numpy()
                  if multi else None)
        handoff.put(([keys[i] for i in single], finished, [keys[i] for i in multi], layers))

    try:
        for index in sorted(by_source):
            tiles = by_source[index]
            source = prepared[index]
            view_path = f"/vsimem/gpumosaic/{os.getpid()}/{index}.vrt"
            source_view(source, view_path)
            dataset = gdal.Open(view_path)
            wkt = dataset.GetProjection()
            xs = np.array([t[0] for t in tiles], dtype=np.float64)
            ys = np.array([t[1] for t in tiles], dtype=np.float64)
            wraps = np.array([t[2] for t in tiles], dtype=np.float64)
            wests_np = -MERCATOR_HALF_WORLD + xs * span + wraps * world
            norths_np = MERCATOR_HALF_WORLD - ys * span
            keys_all = [(t[0], t[1]) for t in tiles]

            if not gpuwarp.supports(wkt):
                _render_with_gdal(view_path, keys_all, wests_np, norths_np, span,
                                  mercator_wkt, resampling, ERROR_THRESHOLD,
                                  readers, device, deliver)
                gdal.Unlink(view_path)
                continue

            lcc = gpuwarp.LambertConformalConic.from_wkt(wkt)
            inverse = gdal.InvGeoTransform(dataset.GetGeoTransform())
            width, height = dataset.RasterXSize, dataset.RasterYSize
            wests = torch.from_numpy(wests_np).to(device)
            norths = torch.from_numpy(norths_np).to(device)

            clock = time.perf_counter()
            col0, col1, row0, row1, scale = _footprints(lcc, inverse, wests, norths, span)
            timed("footprints", clock)
            factor = gpuwarp.mip_factor(float(scale.max()))
            misses = (col1 < 0) | (row1 < 0) | (col0 > width) | (row0 > height)
            missed = np.nonzero(misses)[0]
            for start in range(0, len(missed), BATCH):
                part = missed[start:start + BATCH]
                deliver([keys_all[i] for i in part],
                        torch.zeros((len(part), 4, TILE, TILE), device=device))

            hits = np.nonzero(~misses)[0]
            chunks: dict[tuple[int, int], list[int]] = {}
            for i in hits:
                key = (int(max(0.0, col0[i]) // factor // CHUNK),
                       int(max(0.0, row0[i]) // factor // CHUNK))
                chunks.setdefault(key, []).append(int(i))

            # Plan every chunk's window first, so the next one can be decoded on
            # the reader threads while this one is on the GPU.
            windows = []
            margin = gpuwarp.WINDOW_MARGIN * factor
            for members in chunks.values():
                x0 = max(0, int(math.floor(col0[members].min())) - margin)
                y0 = max(0, int(math.floor(row0[members].min())) - margin)
                x1 = min(width, int(math.ceil(col1[members].max())) + margin)
                y1 = min(height, int(math.ceil(row1[members].max())) + margin)
                x0, y0 = x0 - x0 % factor, y0 - y0 % factor
                x1 = x0 + max(factor, ((x1 - x0) // factor) * factor)
                y1 = y0 + max(factor, ((y1 - y0) // factor) * factor)
                x1 = min(x1, width - (width - x0) % factor)
                y1 = min(y1, height - (height - y0) % factor)
                w_px, h_px = (x1 - x0) // factor, (y1 - y0) // factor
                if w_px <= 0 or h_px <= 0:
                    # Only possible in a sliver at the raster's edge narrower
                    # than one mip pixel: nothing there to draw.
                    for start in range(0, len(members), BATCH):
                        part = members[start:start + BATCH]
                        deliver([keys_all[i] for i in part],
                                torch.zeros((len(part), 4, TILE, TILE), device=device))
                    continue
                if w_px * h_px > MAX_CHUNK_PIXELS:
                    raise TileBuildError(
                        f"{source.name}: a chunk needs {w_px}x{h_px} px at 1/{factor}; "
                        "refusing rather than exhausting memory")
                windows.append((members, x0, y0, x1 - x0, y1 - y0, w_px, h_px))

            def fetch(window):
                _, wx, wy, ww, wh, _, _ = window
                return prefetcher.submit(_decode_window, view_path, wx, wy, ww, wh,
                                         factor, readers)

            pending = fetch(windows[0]) if windows else None
            for k, window in enumerate(windows):
                members, x0, y0, full_w, full_h, w_px, h_px = window
                clock = time.perf_counter()
                strips = pending.result()           # usually already decoded
                timed("decode", clock)
                pending = fetch(windows[k + 1]) if k + 1 < len(windows) else None
                clock = time.perf_counter()
                chunk = _upload_window(strips, full_w, full_h, factor, device)
                del strips
                chunk = gpuwarp.prefilter(chunk, float(scale[members].max()) / factor)
                timed("prefilter", clock)
                size = torch.tensor([w_px, h_px], device=device, dtype=torch.float64)
                origin = torch.tensor([x0, y0], device=device, dtype=torch.float64)

                for start in range(0, len(members), BATCH):
                    batch = members[start:start + BATCH]
                    clock = time.perf_counter()
                    picked = torch.as_tensor(batch, device=device)
                    coords = gpuwarp.source_pixels_batch(
                        lcc, inverse, wests[picked], norths[picked], span, TILE)
                    grid = (2.0 * (coords - origin) / factor / size - 1.0).to(torch.float32)
                    del coords
                    sampled = F.grid_sample(
                        chunk.unsqueeze(0), grid.reshape(1, len(batch) * TILE, TILE, 2),
                        mode="bicubic", padding_mode="zeros", align_corners=False)
                    del grid
                    contributions = (sampled.reshape(4, len(batch), TILE, TILE)
                                     .permute(1, 0, 2, 3).clamp_(min=0.0))
                    del sampled
                    timed("sample", clock)
                    clock = time.perf_counter()
                    deliver([keys_all[i] for i in batch], contributions)
                    timing["deliver"] += time.perf_counter() - clock
                del chunk
            dataset = None
            gdal.Unlink(view_path)
        handoff.put(None)
        dispatcher.join()
        if dispatch_errors:
            raise dispatch_errors[0]
        encoder.close()
        report(force=True)
    finally:
        if dispatcher.is_alive():
            handoff.put(None)
            dispatcher.join()
        prefetcher.shutdown(wait=True)
        readers.shutdown(wait=True)
        shutil.rmtree(spill, ignore_errors=True)

    if not quiet:
        say(f"  z{top} (gpu): {len(encoder.written) - len(already):,} tiles written; "
            f"at most {partials.peak:,} seam tiles held at once, "
            f"{len(partials.spilled)} spilled")
        wall = time.monotonic() - started
        parts = ", ".join(f"{k} {v:.1f}s" for k, v in timing.items())
        say(f"  z{top} (gpu): {wall:.1f}s wall; main thread: {parts} "
            f"(of which blocked on encoders {encoder.waited:.1f}s)")
    if any(remaining.values()):
        left = sum(1 for v in remaining.values() if v)
        raise TileBuildError(f"{left} tiles never received all their sheets")
    return encoder.written


def _render_with_gdal(view_path, keys, wests, norths, span, mercator_wkt,
                      resampling, error_threshold, readers, device, deliver):
    """The fallback for a projection the GPU sampler does not implement: warp
    each tile with GDAL on threads, then composite through the same path."""

    def warp(i):
        dataset = gdal.Open(view_path)
        warped = gdal.Warp(
            "", dataset, format="MEM",
            outputBounds=(wests[i], norths[i] - span, wests[i] + span, norths[i]),
            width=TILE, height=TILE, dstSRS=mercator_wkt, dstAlpha=True,
            resampleAlg=resampling, errorThreshold=error_threshold)
        values = warped.ReadAsArray().astype(np.float32) / 255.0
        alpha = values[-1:]
        rgb = values[:3] if values.shape[0] >= 4 else np.repeat(values[:1], 3, axis=0)
        return np.concatenate((rgb * alpha, alpha), axis=0)

    for start in range(0, len(keys), BATCH):
        batch = list(range(start, min(start + BATCH, len(keys))))
        stack = np.stack(list(readers.map(warp, batch)))
        deliver([keys[i] for i in batch], torch.from_numpy(stack).to(device))


# -- overviews ----------------------------------------------------------------
#
# Each lower zoom is built from the four children beneath it. Per parent, on
# one core: decoding the four children took 4.4 ms, the 2x2 premultiplied
# average 14.7 ms, and encoding 5.5 ms -- the arithmetic, not the codecs, was
# 60% of it. The average is trivial for a GPU in batches, so it runs there,
# while decoding and encoding stay on threads.

# Parents averaged per GPU call: children arrive as uint8, 1 MB per parent,
# and the float32 canvas is 4 MB per parent.
PARENT_BATCH = 128


def _decode_children(tile_dir: Path, z: int, parents, readers: ThreadPoolExecutor) -> np.ndarray:
    """``(P, 2, 2, 256, 256, 4)`` straight uint8 children; zeros where one is
    missing, which is what the CPU cascade treats it as too.

    Decoded with imagecodecs straight from the file's bytes. Opening each tile
    as a GDAL dataset cost far more than decoding it and serialised the threads:
    measured on z13 IFR tiles, GDAL managed 720/s on one thread and *fell* to
    940/s on 22, while imagecodecs does 6,300/s on one and ~18,700/s on 22 --
    with identical pixels (500 of 500 checked). Pillow holds the GIL outright.
    An opaque tile is stored as RGB, so its alpha is filled in.
    """
    import imagecodecs

    out = np.zeros((len(parents), 2, 2, TILE, TILE, 4), np.uint8)

    def load(job):
        i, dy, dx, path = job
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            return
        pixels = imagecodecs.webp_decode(data)
        out[i, dy, dx, :, :, :pixels.shape[2]] = pixels
        if pixels.shape[2] == 3:
            out[i, dy, dx, :, :, 3] = 255

    jobs = [(i, dy, dx, tile_dir / str(z + 1) / str(2 * x + dx) / f"{2 * y + dy}.webp")
            for i, (x, y) in enumerate(parents) for dy in (0, 1) for dx in (0, 1)]
    list(readers.map(load, jobs))
    return out


def _average_parents(children: np.ndarray, device: str) -> np.ndarray:
    """Box-filter children into parents, in premultiplied space, on the device.

    Premultiplied so transparent pixels do not darken edges -- the same rule as
    the CPU cascade's ``_render_parent``, and the same rounding (round half to
    even, colour divided by the unrounded alpha). Returns ``(P, 4, 256, 256)``
    straight uint8.
    """
    batch = torch.from_numpy(children).to(device)                  # P,2,2,H,W,4 uint8
    count = batch.shape[0]
    pixels = batch.to(torch.float32).div_(255.0)
    # P,2(dy),2(dx),H,W,4 -> P,4,2H,2W
    canvas = pixels.permute(0, 5, 1, 3, 2, 4).reshape(count, 4, 2 * TILE, 2 * TILE)
    alpha = canvas[:, 3:4]
    premultiplied = torch.cat((canvas[:, :3] * alpha, alpha), dim=1)
    pooled = F.avg_pool2d(premultiplied, 2)
    return _unpremultiply_uint8(pooled).cpu().numpy()


def render_overviews(tile_dir, written, top: int, min_zoom: int, creation_options, *,
                     resume: bool = False, threads: int | None = None,
                     device: str | None = None, say=print, quiet: bool = False) -> None:
    """Build zooms ``top - 1`` down to ``min_zoom`` from the level above each.

    Levels run in order, each finishing before the next starts, because a level
    is read back from the tiles the one above it wrote.
    """
    from cesiumtiles.mosaic import write_tile

    device = device or gpuwarp.best_device()
    gpuwarp.limit_memory(device, MEMORY_SHARE)
    threads = threads or max(1, (os.cpu_count() or 2) - 2)
    tile_dir = Path(tile_dir)
    readers = ThreadPoolExecutor(threads, thread_name_prefix="decode")
    prefetcher = ThreadPoolExecutor(1, thread_name_prefix="prefetch")
    try:
        for z in range(top - 1, min_zoom - 1, -1):
            started = time.monotonic()

            def tile_path(x, y, z=z):
                return tile_dir / str(z) / str(x) / f"{y}.webp"

            parents = sorted({(x >> 1, y >> 1) for x, y in written})
            if resume:
                done = {p for p in parents if tile_path(*p).exists()}
                parents = [p for p in parents if p not in done]
            else:
                done = set()
            encoder = _Encoder(threads, write_tile, tile_path, creation_options)
            encoder.written.update(done)
            batches = [parents[i:i + PARENT_BATCH] for i in range(0, len(parents), PARENT_BATCH)]
            pending = (prefetcher.submit(_decode_children, tile_dir, z, batches[0], readers)
                       if batches else None)
            for k, batch in enumerate(batches):
                children = pending.result()
                pending = (prefetcher.submit(_decode_children, tile_dir, z, batches[k + 1], readers)
                           if k + 1 < len(batches) else None)
                averaged = _average_parents(children, device)
                del children
                for j, (x, y) in enumerate(batch):
                    tile = averaged[j]
                    if tile[3].max() == 0:
                        continue
                    encoder.submit(x, y, tile[:3], tile[3])
            encoder.close()
            written = encoder.written
            if not quiet:
                elapsed = time.monotonic() - started
                say(f"  z{z} (gpu): {len(written):,} tiles in {elapsed:.1f}s "
                    f"({len(parents) / max(elapsed, 1e-9):,.0f} tiles/s)")
    finally:
        prefetcher.shutdown(wait=True)
        readers.shutdown(wait=True)
