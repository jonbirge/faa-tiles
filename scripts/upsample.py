#!/usr/bin/env python
"""Upsample a georeferenced raster 2x with a learned super-resolution model.

Why a model rather than a kernel: every resampling kernel GDAL offers except
`near` is linear, so each bandlimits edges by construction and rings on them.
On a rasterised vector drawing -- flat regions meeting at step edges -- that
ringing is the dominant artifact. See the README's "Upsample the source before
tiling" section for the measurements.

Runs block by block, so peak memory is a few hundred MB regardless of how large
the raster is. Blocks are read with an overlap and cropped back afterwards: a
model given an isolated tile has no context at its edges, and independently
upsampled tiles seam visibly where they meet.

    python scripts/upsample.py --model models/2x_APISR_RRDB_GAN_generator.pth \\
        --out upsampled/apisr.tif

    python scripts/upsample.py --model waifu2x --out upsampled/waifu2x.tif
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch
from osgeo import gdal

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
gdal.UseExceptions()

# The neatline crop, as measured for the wall planning chart.
from build_vfr_tileset import COMBINED, NEATLINE_LCC  # noqa: E402

SCALE = 2


class SpandrelModel:
    """Any architecture spandrel recognises: ESRGAN/RRDB, RealCUGAN, SwinIR..."""

    def __init__(self, path: Path, threads: int):
        from spandrel import ModelLoader

        descriptor = ModelLoader().load_from_file(str(path))
        if descriptor.scale != SCALE:
            raise SystemExit(f"{path.name} is a {descriptor.scale}x model; this script does 2x")
        torch.set_num_threads(threads)
        self.net = descriptor.eval().cpu()
        self.name = f"{descriptor.architecture.name} ({path.name})"

    @torch.inference_mode()
    def __call__(self, rgb: np.ndarray) -> np.ndarray:
        x = torch.from_numpy(rgb).float().div_(255.0).unsqueeze(0)
        y = self.net(x).clamp_(0, 1).squeeze(0).mul_(255.0)
        return y.numpy()


class Waifu2xModel:
    """nunif's waifu2x. Its CUNet architecture is not one spandrel knows."""

    def __init__(self, threads: int, noise_level: int = 0):
        sys.path.insert(0, str(REPO / "vendor" / "nunif"))
        from waifu2x.utils import Waifu2x

        torch.set_num_threads(threads)
        self.runner = Waifu2x(model_dir=str(REPO / "vendor" / "nunif" / "waifu2x" /
                                            "pretrained_models" / "cunet" / "art"), gpus=[-1])
        self.method = "noise_scale" if noise_level >= 0 else "scale"
        self.noise_level = max(noise_level, 0)
        self.runner.load_model(self.method, self.noise_level)
        self.name = f"waifu2x cunet/art ({self.method}, noise {self.noise_level})"

    @torch.inference_mode()
    def __call__(self, rgb: np.ndarray) -> np.ndarray:
        x = torch.from_numpy(rgb).float().div_(255.0)
        # convert() returns (rgb, alpha); we feed no alpha and want none back.
        y, _alpha = self.runner.convert(x, None, self.method, self.noise_level,
                                        tile_size=256, batch_size=1)
        return y.clamp_(0, 1).mul_(255.0).cpu().numpy()


def cropped_source(path: Path, bbox):
    """The neatline crop, as a lazy VRT -- no pixels are moved."""
    ds = gdal.Open(str(path))
    if bbox is None:
        return ds
    west, south, east, north = bbox
    cut = f"POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"
    return gdal.Warp("", ds, format="VRT", outputBounds=bbox, dstSRS=ds.GetProjection(),
                     cutlineWKT=cut, cutlineSRS=ds.GetProjection(), resampleAlg="near")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True,
                   help="path to a spandrel-loadable .pth, or the literal 'waifu2x'")
    p.add_argument("--out", required=True, type=Path, help="output GeoTIFF")
    p.add_argument("--source", type=Path, default=COMBINED)
    p.add_argument("--no-crop", action="store_true", help="skip the neatline crop")
    p.add_argument("--block", type=int, default=256, help="source pixels per block (default: %(default)s)")
    p.add_argument("--overlap", type=int, default=16,
                   help="source pixels of context on each side, cropped off after "
                        "(default: %(default)s). 0 will seam.")
    p.add_argument("--threads", type=int, default=0, help="torch threads (0 = all cores)")
    p.add_argument("--limit", type=int, default=0, help="stop after N blocks, for timing runs")
    args = p.parse_args(argv)

    threads = args.threads or torch.get_num_threads()
    model = (Waifu2xModel(threads) if args.model == "waifu2x"
             else SpandrelModel(Path(args.model), threads))

    src = cropped_source(args.source, None if args.no_crop else NEATLINE_LCC)
    w, h = src.RasterXSize, src.RasterYSize
    gt = list(src.GetGeoTransform())
    gt[1] /= SCALE
    gt[5] /= SCALE

    args.out.parent.mkdir(parents=True, exist_ok=True)
    dst = gdal.GetDriverByName("GTiff").Create(
        str(args.out), w * SCALE, h * SCALE, 3, gdal.GDT_Byte,
        options=["COMPRESS=LZW", "PREDICTOR=2", "TILED=YES", "BIGTIFF=YES",
                 "NUM_THREADS=ALL_CPUS"])
    dst.SetGeoTransform(gt)
    dst.SetProjection(src.GetProjection())

    blocks = [(x, y) for y in range(0, h, args.block) for x in range(0, w, args.block)]
    if args.limit:
        blocks = blocks[: args.limit]
    print(f"model   {model.name}")
    print(f"source  {w} x {h}  ->  {w * SCALE} x {h * SCALE}")
    print(f"blocks  {len(blocks):,} of {args.block}px (+{args.overlap} overlap), {threads} threads")

    started = time.perf_counter()
    for i, (x, y) in enumerate(blocks):
        # Read with context, so the model sees past the block edge.
        rx = max(0, x - args.overlap)
        ry = max(0, y - args.overlap)
        rw = min(w - rx, args.block + (x - rx) + args.overlap)
        rh = min(h - ry, args.block + (y - ry) + args.overlap)
        patch = src.ReadAsArray(rx, ry, rw, rh)

        up = model(patch)

        # Crop the context back off, in output pixels.
        left = (x - rx) * SCALE
        top = (y - ry) * SCALE
        keep_w = min(args.block, w - x) * SCALE
        keep_h = min(args.block, h - y) * SCALE
        dst.WriteRaster(x * SCALE, y * SCALE, keep_w, keep_h,
                        np.ascontiguousarray(
                            up[:, top:top + keep_h, left:left + keep_w].astype(np.uint8)
                        ).tobytes(),
                        buf_type=gdal.GDT_Byte, band_list=[1, 2, 3])

        if i % 200 == 0 or i == len(blocks) - 1:
            done = i + 1
            rate = done / (time.perf_counter() - started)
            eta = (len(blocks) - done) / rate
            print(f"  {done:>6,}/{len(blocks):,}  {rate:5.1f} blocks/s  "
                  f"eta {eta / 60:5.1f} min", flush=True)

    dst.FlushCache()
    dst = None
    elapsed = time.perf_counter() - started
    size_mb = args.out.stat().st_size / 1e6
    print(f"\nwrote {args.out}  ({size_mb:.0f} MB) in {elapsed / 60:.1f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
