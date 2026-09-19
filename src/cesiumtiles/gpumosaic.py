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
   tile is held as a partial **on the device** until its last sheet has been
   drawn, then composited there and encoded **once**; the plan says up front how
   many sheets each tile has.

Encoding runs on threads in this process rather than in worker processes:
GDAL releases the GIL while encoding, 22 threads reach ~1,300 tiles/s, and
nothing has to be pickled between processes. That rate is the floor this stage
is built around -- 713k z13 IFR tiles is ~9 minutes of encoding -- so decode,
GPU and encode all run concurrently rather than in turn.

Only the max zoom is rendered here. Lower zooms are built from it afterwards.
"""

from __future__ import annotations

import functools
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
# Pinned buffers finished tiles are copied into (~33 MB each). Enough to cover
# batches waiting for the dispatcher plus tiles queued for the encoders.
OUT_BUFFERS = HANDOFF_QUEUE + ENCODE_QUEUE // BATCH + 4

# Full-resolution rows per decode task, and how many decode at once.
READ_ROWS = 1024
READERS = 8

# Points per tile edge used to find its footprint in the source. The mapping is
# smooth at tile scale; the filter margin covers what a 5x5 lattice misses.
LATTICE = 5

# Stage timers force a GPU sync when this is set, so each bucket is exact at the
# cost of stopping the CPU running ahead of the GPU; otherwise they are cheap
# and approximate. `CESIUMTILES_PROFILE=1` in the environment turns it on.
PROFILE = os.environ.get("CESIUMTILES_PROFILE") == "1"

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
            return value
        self.spilled.discard(key)
        path = self._file(key)
        value = np.load(path)
        path.unlink()
        return value


# Device memory the seam pool may hold. A partial is 512 KB, so 2 GiB is ~4,000
# tiles held on the card at once; the rest fall back to _Partials, which is host
# RAM and then disk. On the full IFR series the live set peaked at 19,796, so
# the fallback is not a corner case -- but it is now a *transfer*, not a
# composite: every tile still combines its sheets on the GPU.
SEAM_DEVICE_BYTES = 2 * 2**30


class _SeamPool:
    """Running "under" composites for seam tiles, held on the device.

    A tile covered by more than one sheet cannot be finished until its last
    sheet is drawn, and there is one accumulator per tile -- "under" is
    associative, so a running composite is all that has to be kept, never one
    layer per sheet.

    What changed here is *where the arithmetic happens*. Each sheet's
    contribution used to be downloaded as float16 and combined in numpy on the
    single dispatcher thread; on the full IFR series that thread was busy 1,014
    s of a 1,464 s z13 pass, with up to 19,796 partials live, and it is what
    made the GPU backend lose to the CPU. Now a batch's partials are gathered,
    composited and (where they are finished) unpremultiplied in a handful of
    kernels, and only finished tiles cross to the host -- once each.

    Slots are preallocated: ``count`` premultiplied float16 ``(4, 256, 256)``
    accumulators in one tensor, so a gather or a store is one ``index_select``
    rather than a launch per tile, and the card's share of this is fixed and
    known rather than growing with the live set. Tiles past the last free slot
    spill to ``host`` (RAM, then disk), exactly as they always did.
    """

    def __init__(self, device: str, count: int, host: _Partials):
        self.device = device
        self.host = host
        self.count = max(0, count)
        self.buffer = (torch.empty((self.count, 4, TILE, TILE), device=device,
                                   dtype=torch.float16) if self.count else None)
        self.free = list(range(self.count))
        self.slot_of: dict[tuple[int, int], int] = {}
        self.peak = 0

    def rows(self, indices) -> torch.Tensor:
        return torch.tensor(indices, device=self.device, dtype=torch.long)

    @property
    def live(self) -> int:
        return len(self.slot_of) + len(self.host.ram) + len(self.host.spilled)

    def gather(self, keys) -> torch.Tensor:
        """What is already drawn under ``keys``, ``(K, 4, 256, 256)`` float16 on
        the device and zero for a tile no sheet has reached yet.

        The partials are taken *out* of the pool; the caller composites this
        sheet over them and stores back whatever is still unfinished.
        """
        out = torch.zeros((len(keys), 4, TILE, TILE), device=self.device, dtype=torch.float16)
        rows, slots, host_rows, host_values = [], [], [], []
        for i, key in enumerate(keys):
            slot = self.slot_of.pop(key, None)
            if slot is not None:
                rows.append(i)
                slots.append(slot)
                self.free.append(slot)
            elif key in self.host:
                host_rows.append(i)
                host_values.append(self.host.pop(key))
        if rows:
            out[self.rows(rows)] = self.buffer.index_select(0, self.rows(slots))
        if host_rows:
            # One transfer for the batch's spilled tiles, not one per tile.
            out[self.rows(host_rows)] = torch.from_numpy(np.stack(host_values)).to(self.device)
        return out

    def store(self, keys, values: torch.Tensor) -> None:
        """Keep ``values`` (``(K, 4, 256, 256)`` float16 on the device) for
        ``keys`` until their remaining sheets arrive."""
        rows, slots, overflow = [], [], []
        for i, key in enumerate(keys):
            if self.free:
                slot = self.free.pop()
                self.slot_of[key] = slot
                rows.append(i)
                slots.append(slot)
            else:
                overflow.append(i)
        if rows:
            self.buffer[self.rows(slots)] = values.index_select(0, self.rows(rows))
        if overflow:
            block = values.index_select(0, self.rows(overflow)).cpu().numpy()
            for j, i in enumerate(overflow):
                self.host.put(keys[i], block[j])
        self.peak = max(self.peak, self.live)


def seam_slots(seam_tiles: int, budget: int | None = None) -> int:
    """How many seam accumulators to preallocate on the device: enough for the
    plan's seam tiles, but never more than ``budget`` bytes of them.

    Read from SEAM_DEVICE_BYTES at call time, not bound at import, so a test can
    squeeze the pool to nothing and take the spill path.
    """
    budget = SEAM_DEVICE_BYTES if budget is None else budget
    return max(0, min(seam_tiles, budget // (4 * TILE * TILE * 2)))


class _Encoder:
    """Encoder threads with a bounded queue, so the GPU cannot run ahead of them
    and fill RAM with finished tiles waiting to be written."""

    def __init__(self, threads: int, write_pixels, tile_path, creation_options):
        self.pool = ThreadPoolExecutor(threads, thread_name_prefix="encode")
        # Deep enough (~0.5 GB of finished tiles) that the encoders keep working
        # through the main thread's pauses; a shallow queue left them idle for
        # every chunk decode, and the stages ran in turn instead of together.
        self.slots = threading.BoundedSemaphore(ENCODE_QUEUE)
        self.write_pixels, self.tile_path = write_pixels, tile_path
        self.options = creation_options
        self.written: set[tuple[int, int]] = set()
        self.lock = threading.Lock()
        self.errors: list[BaseException] = []
        self.waited = 0.0   # seconds the main thread spent blocked on a full queue

    def _run(self, x, y, pixels, done):
        try:
            self.write_pixels(self.tile_path(x, y), pixels, self.options)
            with self.lock:
                self.written.add((x, y))
        except BaseException as exc:  # surfaced on the main thread
            self.errors.append(exc)
        finally:
            self.slots.release()
            if done is not None:
                done()

    def submit(self, x, y, pixels: np.ndarray, done=None) -> None:
        """Queue one ``(H, W, 4)`` straight uint8 tile for encoding; ``done`` is
        called once it has been written (or has failed)."""
        if self.errors:
            raise self.errors[0]
        started = time.perf_counter()
        self.slots.acquire()
        self.waited += time.perf_counter() - started
        self.pool.submit(self._run, x, y, pixels, done)

    def close(self) -> None:
        self.pool.shutdown(wait=True)
        if self.errors:
            raise self.errors[0]


class _PinnedPool:
    """Page-locked host buffers that finished tiles are copied into.

    A copy from the GPU into ordinary (pageable) memory is not really
    asynchronous: the driver stages it through a hidden pinned buffer with a CPU
    memcpy, blocking the thread that asked. Profiling one sheet's z13 pass put
    52% of the main thread's time in exactly that. Copies into these buffers are
    DMA the main thread does not wait for; the dispatcher waits on the copy's
    CUDA event instead, and a buffer returns to the pool once every tile read
    from it has been encoded. ``acquire`` blocking is the backpressure.
    """

    def __init__(self, count: int, shape, pinned: bool):
        self.buffers = [torch.empty(shape, dtype=torch.uint8, pin_memory=pinned)
                        for _ in range(count)]
        self.flags = [torch.empty((shape[0],), dtype=torch.bool, pin_memory=pinned)
                      for _ in range(count)]
        self.free: queue.Queue = queue.Queue()
        for slot in range(count):
            self.free.put(slot)
        self.refs = [0] * count
        self.lock = threading.Lock()

    def acquire(self, failed=lambda: None) -> int:
        """A free buffer, waiting for one if need be. ``failed`` is polled while
        waiting and should return an exception if the consumer has died -- its
        buffers would then never come back, and this would wait forever."""
        while True:
            try:
                return self.free.get(timeout=1.0)
            except queue.Empty:
                error = failed()
                if error is not None:
                    raise error

    def hold(self, slot: int, count: int) -> None:
        """Mark ``count`` tiles as reading from ``slot``; free it if none do."""
        if count == 0:
            self.free.put(slot)
            return
        with self.lock:
            self.refs[slot] = count

    def release(self, slot: int) -> None:
        with self.lock:
            self.refs[slot] -= 1
            finished = self.refs[slot] == 0
        if finished:
            self.free.put(slot)


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
        block = _premultiplied(torch.from_numpy(raw).to(device), factor)
        r0 = row // factor
        out[:, r0:r0 + block.shape[1]] = block
    return out


def _premultiplied(pixels: torch.Tensor, factor: int = 1) -> torch.Tensor:
    """``(bands, h, w)`` uint8 on the device to premultiplied float32
    ``(4, h/factor, w/factor)``, box-reduced after premultiplying so masked-out
    collar cannot bleed colour across the map's edge."""
    pixels = pixels.to(torch.float32).div_(255.0)
    if pixels.shape[0] >= 4:
        rgb, alpha = pixels[:3], pixels[3:4]
    else:
        rgb = pixels[:3] if pixels.shape[0] == 3 else pixels[:1].expand(3, -1, -1)
        alpha = torch.ones_like(rgb[:1])
    block = torch.cat((rgb * alpha, alpha), dim=0)
    if factor > 1:
        block = F.avg_pool2d(block.unsqueeze(0), factor).squeeze(0)
    return block


def _decode_into(path: str, x0: int, y0: int, width: int, height: int,
                 staging: np.ndarray, readers: ThreadPoolExecutor) -> int:
    """Decode a full-resolution window straight into ``staging`` (a pinned
    buffer), band by band, in row strips on several threads. Returns the band
    count. GDAL writes into the buffer it is given, so there is no copy between
    decoding and the DMA to the GPU."""
    bands = gdal.Open(path).RasterCount
    window = staging[:bands * height * width].reshape(bands, height, width)

    def decode(row):
        dataset = gdal.Open(path)
        rows = min(READ_ROWS, height - row)
        for band in range(bands):
            dataset.GetRasterBand(band + 1).ReadAsArray(
                x0, y0 + row, width, rows, buf_obj=window[band, row:row + rows])

    list(readers.map(decode, range(0, height, READ_ROWS)))
    return bands


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
               tolerance: float = 0.0, say=print, quiet: bool = False) -> set[tuple[int, int]]:
    """Render every planned max-zoom tile. Returns the ``(x, y)`` written.

    ``prepared`` and ``plan`` are exactly what the CPU backend receives, and
    sources are read through the same :func:`mosaic.source_view`, so the two
    backends see identical pixels. A source whose projection the GPU sampler
    does not implement is warped with GDAL on threads instead, and fed through
    the same compositing, so a series can mix the two.

    ``tolerance`` is how far the projection may be cut short, in source pixels
    -- the same knob, in the same units, that the CPU backend gives gdal.Warp.
    Here it widens the lattice the projection is evaluated on exactly
    (:func:`gpuwarp.lattice_step`), and it is passed to the GDAL fallback as its
    errorThreshold. ``resampling`` chooses the reconstruction filter: cubic is
    the default, bilinear is the cheaper end of the trade.
    """
    from cesiumtiles.mosaic import TileBuildError, source_view, write_pixels

    device = device or gpuwarp.best_device()
    step = gpuwarp.lattice_step(tolerance, TILE)
    mode = gpuwarp.grid_mode(resampling)
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
    encoder = _Encoder(threads, write_pixels, tile_path, creation_options)
    encoder.written.update(already)
    readers = ThreadPoolExecutor(READERS, thread_name_prefix="decode")
    # One thread that runs a whole chunk's decode (itself fanned out over the
    # readers) ahead of the main thread.
    prefetcher = ThreadPoolExecutor(1, thread_name_prefix="prefetch")
    tile_dir.mkdir(parents=True, exist_ok=True)
    spill = Path(tempfile.mkdtemp(prefix=".partials-", dir=tile_dir))
    partials = _Partials(spill)
    seams = _SeamPool(device, seam_slots(sum(1 for c in remaining.values() if c > 1)),
                      partials)
    mercator = osr.SpatialReference()
    mercator.ImportFromEPSG(3857)
    mercator_wkt = mercator.ExportToWkt()

    started = time.monotonic()
    state = {"done": 0, "last": started}
    # Main-thread seconds per stage, reported at the end. Whatever dominates is
    # what the pass is waiting on; "encoder" is time blocked on a full queue.
    # "decode" is only time spent *waiting* for a prefetched chunk; "prefilter"
    # includes uploading it.
    timing = dict(footprints=0.0, decode=0.0, prefilter=0.0, sample=0.0, deliver=0.0,
                  dispatcher=0.0)

    def timed(stage, started_at):
        # Syncing makes each bucket exact but stops the CPU running ahead of the
        # GPU, so it is only done when asked for (see PROFILE).
        if PROFILE and device.startswith("cuda"):
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
    cuda = device.startswith("cuda")
    out_pool = _PinnedPool(OUT_BUFFERS, (BATCH, TILE, TILE, 4), pinned=cuda)
    # Two pinned buffers for source chunks: one being decoded into while the
    # other is uploaded. Sized for the largest chunk MAX_CHUNK_PIXELS allows.
    staging = [torch.empty(4 * MAX_CHUNK_PIXELS, dtype=torch.uint8, pin_memory=cuda)
               for _ in range(2)]
    staging_np = [buffer.numpy() for buffer in staging]
    uploaded: list = [None, None]
    handoff: queue.Queue = queue.Queue(maxsize=HANDOFF_QUEUE)
    dispatch_errors: list[BaseException] = []

    def dispatch():
        try:
            while True:
                item = handoff.get()
                if item is None:
                    return
                single_keys, slot, copied, multi_keys, layers = item
                del item                  # seam layers are device memory now
                if copied is not None:
                    copied.synchronize()          # the DMA into the pinned buffer
                busy_from = time.perf_counter()
                if single_keys:
                    count = len(single_keys)
                    finished = out_pool.buffers[slot][:count].numpy()
                    alive = out_pool.flags[slot][:count].numpy()
                    live = [j for j in range(count) if alive[j]]
                    out_pool.hold(slot, len(live))
                    release = functools.partial(out_pool.release, slot)
                    for key in single_keys:
                        remaining[key] = 0
                    state["done"] += count
                    for j in live:                # the rest have nothing of this sheet
                        key = single_keys[j]
                        encoder.submit(key[0], key[1], finished[j], release)
                if multi_keys:
                    # Sheets arrive bottom first, so this one lands *over* what
                    # is already there. Both sides are premultiplied, so the
                    # whole "under" composite is this one expression -- and it
                    # runs on the device, for the batch at once.
                    beneath = seams.gather(multi_keys)
                    composited = layers + beneath * (1.0 - layers[:, 3:4])
                    del beneath, layers
                    keep, final = [], []
                    for j, key in enumerate(multi_keys):
                        remaining[key] -= 1
                        (keep if remaining[key] > 0 else final).append(j)
                    if keep:
                        seams.store([multi_keys[j] for j in keep], composited[seams.rows(keep)])
                    if final:
                        # float32 for the divide: float16 would round the
                        # unpremultiply, and these are finished pixels.
                        done = _unpremultiply_uint8(
                            composited[seams.rows(final)].to(torch.float32))
                        # Which tiles have anything to write is decided on the
                        # device too, and queued before the big copy, so the
                        # thread waits once rather than scanning every tile.
                        empty = done[:, 3].amax(dim=(1, 2)) == 0
                        pixels = done.permute(0, 2, 3, 1).contiguous().cpu().numpy()
                        alive = ~empty.cpu().numpy()
                        state["done"] += len(final)
                        for j, at in enumerate(final):
                            if alive[j]:
                                key = multi_keys[at]
                                encoder.submit(key[0], key[1], pixels[j])
                    del composited
                report()
                timing["dispatcher"] += time.perf_counter() - busy_from
        except BaseException as exc:
            dispatch_errors.append(exc)
            while handoff.get() is not None:      # drain so the producer never blocks
                pass

    def seams_last(indices, keys_all):
        """``indices`` reordered single-sheet tiles first, seam tiles last, each
        group keeping its order -- what deliver() needs to split by slicing."""
        return sorted(indices, key=lambda i: sheets_per_tile[keys_all[i]] > 1)

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
        # Callers order tiles single-sheet first (see seams_last), so the batch
        # splits into two slices. Indexing with a Python list instead copies an
        # index tensor from pageable memory, which syncs the whole stream.
        seam = [sheets_per_tile[k] > 1 for k in keys]
        split = seam.index(True) if True in seam else len(keys)
        if not all(seam[split:]):
            raise AssertionError("deliver() needs single-sheet tiles before seam tiles")
        single = range(split)
        multi = range(split, len(keys))
        slot = copied = None
        if single:
            straight = _unpremultiply_uint8(contributions[:split])        # B,4,H,W
            slot = out_pool.acquire(lambda: dispatch_errors[0] if dispatch_errors else None)
            count = len(single)
            # Into pinned memory by DMA; the main thread moves on at once.
            out_pool.buffers[slot][:count].copy_(straight.permute(0, 2, 3, 1),
                                                 non_blocking=True)
            # Decided on the GPU, so the dispatcher does not scan every tile.
            out_pool.flags[slot][:count].copy_(straight[:, 3].amax(dim=(1, 2)) > 0,
                                               non_blocking=True)
            if cuda:
                copied = torch.cuda.Event()
                copied.record()
        # Seam tiles stay on the device, as premultiplied float16: the
        # dispatcher composites them there. Downloading every sheet's
        # contribution and combining it in numpy is what the full-series trial
        # measured as the whole build's bottleneck.
        layers = contributions[split:].to(torch.float16) if multi else None
        handoff.put(([keys[i] for i in single], slot, copied,
                     [keys[i] for i in multi], layers))

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
                                  mercator_wkt, resampling, tolerance,
                                  readers, device, deliver,
                                  seams_last(range(len(keys_all)), keys_all))
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
            missed = seams_last([int(i) for i in np.nonzero(misses)[0]], keys_all)
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
            chunks = {key: seams_last(members, keys_all) for key, members in chunks.items()}

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

            # Every tile's corner, in window order, on the device in one transfer
            # per sheet. Building each batch's indices from a Python list and
            # copying them over instead forced a full stream sync per batch --
            # PyTorch syncs after any copy from pageable memory -- which the
            # profiler put at 47% of the main thread's time.
            order = np.concatenate([np.asarray(w[0], dtype=np.int64) for w in windows]) \
                if windows else np.zeros(0, np.int64)
            ordered = torch.from_numpy(order).to(device)
            wests_ordered, norths_ordered = wests[ordered], norths[ordered]
            starts = np.cumsum([0] + [len(w[0]) for w in windows])

            def fetch(k):
                _, wx, wy, ww, wh, _, _ = windows[k]
                if factor == 1 and 4 * ww * wh <= staging[0].numel():
                    # Straight into a pinned buffer, once its last upload is done.
                    slot = k % len(staging)

                    def job():
                        if uploaded[slot] is not None:
                            uploaded[slot].synchronize()
                        bands = _decode_into(view_path, wx, wy, ww, wh,
                                             staging_np[slot], readers)
                        return ("pinned", slot, bands)
                    return prefetcher.submit(job)
                # Mip reads (below native zoom) keep the strip path.
                return prefetcher.submit(lambda: ("strips", _decode_window(
                    view_path, wx, wy, ww, wh, factor, readers), None))

            pending = fetch(0) if windows else None
            for k, window in enumerate(windows):
                members, x0, y0, full_w, full_h, w_px, h_px = window
                clock = time.perf_counter()
                kind, payload, bands = pending.result()     # usually already decoded
                timed("decode", clock)
                pending = fetch(k + 1) if k + 1 < len(windows) else None
                clock = time.perf_counter()
                if kind == "pinned":
                    staged = staging[payload][:bands * full_h * full_w].view(bands, full_h, full_w)
                    on_device = staged.to(device, non_blocking=True)
                    if cuda:
                        uploaded[payload] = torch.cuda.Event()
                        uploaded[payload].record()
                    chunk = _premultiplied(on_device)
                    del on_device
                else:
                    chunk = _upload_window(payload, full_w, full_h, factor, device)
                chunk = gpuwarp.prefilter(chunk, float(scale[members].max()) / factor)
                timed("prefilter", clock)

                for start in range(0, len(members), BATCH):
                    batch = members[start:start + BATCH]
                    clock = time.perf_counter()
                    at = int(starts[k]) + start
                    grid = gpuwarp.sampling_grid(
                        lcc, inverse, wests_ordered[at:at + len(batch)],
                        norths_ordered[at:at + len(batch)], span, TILE,
                        origin=(x0, y0), factor=factor, extent=(w_px, h_px), step=step)
                    sampled = F.grid_sample(
                        chunk.unsqueeze(0), grid.reshape(1, len(batch) * TILE, TILE, 2),
                        mode=mode, padding_mode="zeros", align_corners=False)
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
            f"at most {seams.peak:,} seam tiles held at once, "
            f"{seams.count:,} slots on the device, {partials.peak:,} off it")
        wall = time.monotonic() - started
        dispatcher = timing.pop("dispatcher")
        parts = ", ".join(f"{k} {v:.1f}s" for k, v in timing.items())
        exact = "" if PROFILE else " (approximate; CESIUMTILES_PROFILE=1 for exact)"
        say(f"  z{top} (gpu): {mode} sampling on a {step} px lattice "
            f"(tolerance {tolerance:g} source px)")
        say(f"  z{top} (gpu): {wall:.1f}s wall; main thread: {parts}{exact}; "
            f"dispatcher busy {dispatcher:.1f}s, of which blocked on encoders "
            f"{encoder.waited:.1f}s")
    if any(remaining.values()):
        left = sum(1 for v in remaining.values() if v)
        raise TileBuildError(f"{left} tiles never received all their sheets")
    return encoder.written


def _render_with_gdal(view_path, keys, wests, norths, span, mercator_wkt,
                      resampling, error_threshold, readers, device, deliver, order):
    """The fallback for a projection the GPU sampler does not implement: warp
    each tile with GDAL on threads, then composite through the same path.
    ``order`` lists tile indices single-sheet first, as deliver() requires."""

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

    for start in range(0, len(order), BATCH):
        batch = order[start:start + BATCH]
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
# Batches of children decoded ahead of the GPU; the ring holds one more buffer
# than this (~134 MB of pinned memory each).
AHEAD = 2


def _decode_children(tile_dir: Path, z: int, parents, readers: ThreadPoolExecutor,
                     out: np.ndarray | None = None) -> np.ndarray:
    """Decode ``parents``' children into ``out[:len(parents)]``, shaped
    ``(P, 2, 2, 256, 256, 4)`` straight uint8; zeros where a child is missing,
    which is what the CPU cascade treats it as too.

    Decoded with imagecodecs straight from the file's bytes. Opening each tile
    as a GDAL dataset cost far more than decoding it and serialised the threads:
    measured on z13 IFR tiles, GDAL managed 720/s on one thread and *fell* to
    940/s on 22, while imagecodecs does 6,300/s on one and ~18,700/s on 22 --
    with identical pixels (500 of 500 checked). Pillow holds the GIL outright.

    ``out`` is normally a pinned staging buffer being reused, so every slot is
    written, missing children included.
    """
    import imagecodecs

    if out is None:
        out = np.zeros((len(parents), 2, 2, TILE, TILE, 4), np.uint8)
    level = os.path.join(str(tile_dir), str(z + 1))

    def load(i):
        # One task per parent, and each child decoded *into* the buffer with
        # alpha forced on: the Python around each decode -- paths, tasks, an
        # extra copy -- holds the GIL, and at ~45k children a level it, not the
        # codec, was what the pyramid waited for.
        x, y = parents[i]
        for dy in (0, 1):
            for dx in (0, 1):
                try:
                    with open(os.path.join(level, str(2 * x + dx), f"{2 * y + dy}.webp"), "rb") as f:
                        data = f.read()
                except FileNotFoundError:
                    out[i, dy, dx] = 0
                    continue
                imagecodecs.webp_decode(data, hasalpha=True, out=out[i, dy, dx])

    list(readers.map(load, range(len(parents))))
    return out


def _average_parents(batch: torch.Tensor):
    """Box-filter children into parents on the device.

    ``batch`` is ``(P, 2, 2, 256, 256, 4)`` uint8 children on the device.
    Returns ``(P, 256, 256, 4)`` straight uint8 on the host, and a ``(P,)``
    bool of which parents have anything opaque at all.

    A 2x2 box never straddles two children, so each child is reduced on its own
    and the four 128 px results are placed side by side -- no 512 px canvas. And
    it is done in integers on the uint8 data: with ``c`` colour and ``a`` alpha
    in 0..255, the premultiplied average the CPU cascade computes reduces to
    parent colour ``round(sum(c*a) / sum(a))`` and alpha ``round(sum(a) / 4)``.
    The first version built float32 canvases and spent 16.6 ms of a 29.5 ms
    batch on the arithmetic; this touches a fraction of the memory.
    """
    count, half = batch.shape[0], TILE // 2                  # P,2,2,H,W,4 uint8
    quads = batch.view(count, 2, 2, half, 2, half, 2, 4)
    alpha = quads[..., 3:4].to(torch.int32)
    weighted = (quads[..., :3].to(torch.int32) * alpha).sum(dim=(4, 6))   # P,2,2,h,h,3
    alpha_sum = alpha.sum(dim=(4, 6))                                      # P,2,2,h,h,1
    colour = torch.where(alpha_sum > 0,
                         torch.round(weighted.float() / alpha_sum.clamp(min=1).float()),
                         torch.zeros_like(weighted, dtype=torch.float32))
    parent_alpha = torch.round(alpha_sum.float() / 4.0)
    pixels = torch.cat((colour, parent_alpha), dim=-1).to(torch.uint8)    # P,2,2,h,h,4
    # (P, dy, dx, row, col, band) -> (P, dy*h + row, dx*h + col, band)
    parents = pixels.permute(0, 1, 3, 2, 4, 5).reshape(count, TILE, TILE, 4)
    alive = (parents[..., 3].amax(dim=(1, 2)) > 0).cpu().numpy()
    return parents.cpu().numpy(), alive


def render_overviews(tile_dir, written, top: int, min_zoom: int, creation_options, *,
                     resume: bool = False, threads: int | None = None,
                     device: str | None = None, say=print, quiet: bool = False) -> None:
    """Build zooms ``top - 1`` down to ``min_zoom`` from the level above each.

    Levels run in order, each finishing before the next starts, because a level
    is read back from the tiles the one above it wrote.
    """
    from cesiumtiles.mosaic import write_pixels

    device = device or gpuwarp.best_device()
    gpuwarp.limit_memory(device, MEMORY_SHARE)
    threads = threads or max(1, (os.cpu_count() or 2) - 2)
    tile_dir = Path(tile_dir)
    readers = ThreadPoolExecutor(threads, thread_name_prefix="decode")
    prefetcher = ThreadPoolExecutor(AHEAD, thread_name_prefix="prefetch")
    cuda = device.startswith("cuda")
    shape = (PARENT_BATCH, 2, 2, TILE, TILE, 4)
    ring = [torch.empty(shape, dtype=torch.uint8, pin_memory=cuda) for _ in range(AHEAD + 1)]
    ring_np = [buffer.numpy() for buffer in ring]
    uploaded: list = [None] * len(ring)
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
            encoder = _Encoder(threads, write_pixels, tile_path, creation_options)
            encoder.written.update(done)
            # Main-thread seconds per stage; "decode" is waiting on the prefetch.
            timing = dict(decode=0.0, average=0.0, submit=0.0)
            batches = [parents[i:i + PARENT_BATCH] for i in range(0, len(parents), PARENT_BATCH)]
            # Decode runs AHEAD batches in front of the GPU, into a ring of
            # pinned buffers. Pinned memory uploads ~1.7x faster and without a
            # staging copy; the ring lets decode, upload and the average overlap
            # rather than take turns. A slot is refilled only once the upload
            # that last read it has finished (its CUDA event).
            def fill(k, batch):
                slot = k % len(ring)
                if uploaded[slot] is not None:
                    uploaded[slot].synchronize()
                _decode_children(tile_dir, z, batch, readers, out=ring_np[slot])
                return slot

            pending = {k: prefetcher.submit(fill, k, batches[k])
                       for k in range(min(AHEAD, len(batches)))}
            for k, batch in enumerate(batches):
                clock = time.perf_counter()
                slot = pending.pop(k).result()
                timing["decode"] += time.perf_counter() - clock
                clock = time.perf_counter()
                staged = ring[slot][:len(batch)]
                on_device = staged.to(device, non_blocking=True) if cuda else staged.clone()
                if cuda:
                    uploaded[slot] = torch.cuda.Event()
                    uploaded[slot].record()
                if k + AHEAD < len(batches):
                    pending[k + AHEAD] = prefetcher.submit(fill, k + AHEAD, batches[k + AHEAD])
                averaged, alive = _average_parents(on_device)
                del on_device
                timing["average"] += time.perf_counter() - clock
                clock = time.perf_counter()
                for j, (x, y) in enumerate(batch):
                    if alive[j]:
                        encoder.submit(x, y, averaged[j])
                timing["submit"] += time.perf_counter() - clock
            clock = time.perf_counter()
            encoder.close()
            drain = time.perf_counter() - clock
            written = encoder.written
            if not quiet:
                elapsed = time.monotonic() - started
                parts = ", ".join(f"{k} {v:.1f}s" for k, v in timing.items())
                say(f"  z{z} (gpu): {len(written):,} tiles in {elapsed:.1f}s "
                    f"({len(parents) / max(elapsed, 1e-9):,.0f} tiles/s); main thread: {parts} "
                    f"(blocked on encoders {encoder.waited:.1f}s), final drain {drain:.1f}s")
    finally:
        prefetcher.shutdown(wait=True)
        readers.shutdown(wait=True)
