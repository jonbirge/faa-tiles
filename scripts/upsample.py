#!/usr/bin/env python
"""Upsample a georeferenced raster 2x with a learned super-resolution model.

Why a model rather than a kernel: every resampling kernel GDAL offers except
`near` is linear, so each bandlimits edges by construction and rings on them. On
a rasterised vector drawing -- flat regions meeting at step edges -- that
ringing is the dominant artifact. The README's "Upsample the source before
tiling" section has the measurements and the comparison of candidates.

Runs block by block, so peak memory stays in the hundreds of MB however large
the raster is: a 754 Mpx output never exists in RAM. Blocks are read with an
overlap and cropped back afterwards, because a model handed an isolated tile has
no context at its edges and independently upsampled tiles seam where they meet.

    python scripts/upsample.py --out up.tif chart.tif
    python scripts/upsample.py --out up.tif --model waifu2x chart.tif
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import torch
from osgeo import gdal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import MODELS, VENDOR  # noqa: E402

gdal.UseExceptions()

SCALE = 2

# Real-CUGAN, chosen on a side-by-side of APISR, Real-CUGAN and waifu2x over the
# whole chart. Weights are fetched rather than vendored, into source/models. The
# denoise3x variant sits beside it; pass --model to use it.
DEFAULT_MODEL = MODELS / "realcugan-up2x-no-denoise.pth"
DEFAULT_MODEL_URL = (
    "https://huggingface.co/spaces/saber2022/Real-CUGAN/resolve/main/"
    "weights_v3/up2x-latest-no-denoise.pth"
)


def ensure_weights(path: Path, url: str = DEFAULT_MODEL_URL) -> Path:
    """Fetch the default weights on first use, so a fresh checkout just works."""
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  fetching {path.name}\n    from {url}")
    urllib.request.urlretrieve(url, path)
    print(f"    {path.stat().st_size / 1e6:.1f} MB")
    return path


class SpandrelModel:
    """Any architecture spandrel recognises: RealCUGAN, ESRGAN/RRDB, SwinIR..."""

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
        return self.net(x).clamp_(0, 1).squeeze(0).mul_(255.0).numpy()


class Waifu2xModel:
    """nunif's waifu2x. Its CUNet architecture is not one spandrel knows."""

    def __init__(self, threads: int, noise_level: int = 0):
        vendor = VENDOR / "nunif"
        if not vendor.is_dir():
            raise SystemExit(
                f"waifu2x needs a nunif checkout at {vendor}:\n"
                "  git clone --depth 1 https://github.com/nagadomi/nunif.git source/vendor/nunif\n"
                "  (cd source/vendor/nunif && python -m waifu2x.download_models)"
            )
        sys.path.insert(0, str(vendor))
        from waifu2x.utils import Waifu2x

        torch.set_num_threads(threads)
        self.runner = Waifu2x(
            model_dir=str(vendor / "waifu2x" / "pretrained_models" / "cunet" / "art"),
            gpus=[-1],
        )
        self.method, self.noise_level = "noise_scale", noise_level
        self.runner.load_model(self.method, self.noise_level)
        self.name = f"waifu2x cunet/art (noise {noise_level})"

    @torch.inference_mode()
    def __call__(self, rgb: np.ndarray) -> np.ndarray:
        x = torch.from_numpy(rgb).float().div_(255.0)
        # convert() returns (rgb, alpha); we pass no alpha and want none back.
        y, _alpha = self.runner.convert(x, None, self.method, self.noise_level,
                                        tile_size=256, batch_size=1)
        return y.clamp_(0, 1).mul_(255.0).cpu().numpy()


def load_model(spec: str | Path, threads: int = 0):
    """`spec` is a path to spandrel-loadable weights, or the literal 'waifu2x'."""
    threads = threads or torch.get_num_threads()
    if str(spec) == "waifu2x":
        return Waifu2xModel(threads)
    path = Path(spec)
    if path == DEFAULT_MODEL:
        ensure_weights(path)
    return SpandrelModel(path, threads)


def _cropped(source: Path, bbox):
    """The crop as a lazy VRT in the source's own CRS -- no pixels are moved."""
    ds = gdal.Open(str(source))
    if bbox is None:
        return ds
    west, south, east, north = bbox
    ring = f"{west} {south},{east} {south},{east} {north},{west} {north},{west} {south}"
    return gdal.Warp("", ds, format="VRT", outputBounds=bbox,
                     dstSRS=ds.GetProjection(), cutlineWKT=f"POLYGON(({ring}))",
                     cutlineSRS=ds.GetProjection(), resampleAlg="near")


def upsample_raster(source, out, model, *, bbox=None, window=None, block=256, overlap=16,
                    limit=0, quiet=False) -> Path:
    """Write a 2x upsampled GeoTIFF of ``source``.

    Optionally cropped: ``bbox`` is a rectangle in the source CRS (resampled
    north-up), ``window`` is ``(x0, y0, x1, y1)`` in source pixels (no
    resampling; keeps a rotated geotransform). An output pixel ``(u, v)`` maps
    to source pixel ``(x0 + u / 2, y0 + v / 2)``.

    ``model`` is a callable taking and returning (3, H, W) arrays, as returned by
    :func:`load_model`.
    """
    source, out = Path(source), Path(out)
    if window is not None:
        x0, y0, x1, y1 = window
        src = gdal.Translate("", str(source), format="VRT", srcWin=[x0, y0, x1 - x0, y1 - y0])
    else:
        src = _cropped(source, bbox)
    w, h = src.RasterXSize, src.RasterYSize

    # All four linear terms, not just the pixel sizes: a sheet can be rotated in
    # its projection (every IFR enroute chart is), and halving only gt[1] and
    # gt[5] would shear it off its own map.
    gt = list(src.GetGeoTransform())
    for i in (1, 2, 4, 5):
        gt[i] /= SCALE

    out.parent.mkdir(parents=True, exist_ok=True)
    dst = gdal.GetDriverByName("GTiff").Create(
        str(out), w * SCALE, h * SCALE, 3, gdal.GDT_Byte,
        options=["COMPRESS=LZW", "PREDICTOR=2", "TILED=YES", "BIGTIFF=YES",
                 "NUM_THREADS=ALL_CPUS"])
    dst.SetGeoTransform(gt)
    dst.SetProjection(src.GetProjection())

    blocks = [(x, y) for y in range(0, h, block) for x in range(0, w, block)]
    if limit:
        blocks = blocks[:limit]
    if not quiet:
        print(f"  model   {getattr(model, 'name', 'custom')}")
        print(f"  source  {w} x {h}  ->  {w * SCALE} x {h * SCALE}")
        print(f"  blocks  {len(blocks):,} of {block}px (+{overlap} overlap)")

    started = time.perf_counter()
    for i, (x, y) in enumerate(blocks):
        # Read with context, so the model can see past the block edge.
        rx, ry = max(0, x - overlap), max(0, y - overlap)
        rw = min(w - rx, block + (x - rx) + overlap)
        rh = min(h - ry, block + (y - ry) + overlap)

        up = model(src.ReadAsArray(rx, ry, rw, rh))

        # Crop the context back off, in output pixels.
        left, top = (x - rx) * SCALE, (y - ry) * SCALE
        keep_w, keep_h = min(block, w - x) * SCALE, min(block, h - y) * SCALE
        dst.WriteRaster(
            x * SCALE, y * SCALE, keep_w, keep_h,
            np.ascontiguousarray(
                up[:, top:top + keep_h, left:left + keep_w].astype(np.uint8)
            ).tobytes(),
            buf_type=gdal.GDT_Byte, band_list=[1, 2, 3])

        if not quiet and (i % 200 == 0 or i == len(blocks) - 1):
            done = i + 1
            rate = done / (time.perf_counter() - started)
            print(f"    {done:>6,}/{len(blocks):,}  {rate:5.1f} blocks/s  "
                  f"eta {(len(blocks) - done) / rate / 60:5.1f} min", flush=True)

    dst.FlushCache()
    dst = None
    if not quiet:
        print(f"  wrote {out} ({out.stat().st_size / 1e6:.0f} MB) in "
              f"{(time.perf_counter() - started) / 60:.1f} min")
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source", type=Path, help="georeferenced input raster")
    p.add_argument("--out", required=True, type=Path, help="output GeoTIFF")
    p.add_argument("--model", default=str(DEFAULT_MODEL),
                   help="spandrel-loadable weights, or 'waifu2x' (default: Real-CUGAN)")
    p.add_argument("--bbox", nargs=4, type=float, default=None,
                   metavar=("W", "S", "E", "N"),
                   help="crop to this rectangle, in the source's own CRS")
    p.add_argument("--block", type=int, default=256)
    p.add_argument("--overlap", type=int, default=16,
                   help="source pixels of context per side; 0 will seam (default: %(default)s)")
    p.add_argument("--threads", type=int, default=0, help="torch threads (0 = all cores)")
    p.add_argument("--limit", type=int, default=0, help="stop after N blocks, for timing")
    args = p.parse_args(argv)

    upsample_raster(args.source, args.out, load_model(args.model, args.threads),
                    bbox=tuple(args.bbox) if args.bbox else None,
                    block=args.block, overlap=args.overlap, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
