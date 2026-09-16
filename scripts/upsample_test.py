"""Compare 2x upsampling kernels on real chart content.

Two things are measured, because they trade off against each other:

  ringing   how far an output pixel strays outside the range of the source
            pixels it sits between. A step edge has unbounded bandwidth, so a
            sinc-family kernel overshoots on both sides of every edge -- the
            halo. Piecewise-constant artwork should produce none at all.

  sharpness mean gradient magnitude across the result. Kernels that avoid
            ringing usually do it by blurring, which shows up here as a drop.
"""
import numpy as np
from osgeo import gdal, osr

gdal.UseExceptions()
SRC = r"E:\faa-tiles\vfr_wall_planning_geo.tif"
OUT = r"C:\Users\jrbir\AppData\Local\Temp\claude\E--faa-tiles\55e59bfc-a279-4a48-a3c1-e6022ffe4bbd\scratchpad"

ds = gdal.Open(SRC)
gt = ds.GetGeoTransform()

# A patch over Denver: flat airspace fills, magenta airway lines, type, and
# shaded relief all in one crop -- the mix is the whole difficulty.
wgs = osr.SpatialReference(); wgs.ImportFromEPSG(4326)
wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
src_srs = osr.SpatialReference(); src_srs.ImportFromWkt(ds.GetProjection())
src_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
x, y = osr.CoordinateTransformation(wgs, src_srs).TransformPoint(-104.99, 39.74)[:2]
px = int((x - gt[0]) / gt[1]) - 128
py = int((y - gt[3]) / gt[5]) - 128
SIZE = 256
print(f"crop at source pixel ({px}, {py}), {SIZE}x{SIZE}\n")

src = ds.ReadAsArray(px, py, SIZE, SIZE).astype(np.float32)   # (3, SIZE, SIZE)

# Reference for "what range should an output pixel stay inside": for a 2x
# upsample, every output pixel lies between the four source pixels around it.
lo = np.minimum.reduce([src[:, :-1, :-1], src[:, :-1, 1:], src[:, 1:, :-1], src[:, 1:, 1:]])
hi = np.maximum.reduce([src[:, :-1, :-1], src[:, :-1, 1:], src[:, 1:, :-1], src[:, 1:, 1:]])


def upsample(alg, factor=2):
    out = gdal.Translate(
        "", ds, format="MEM", srcWin=[px, py, SIZE, SIZE],
        width=SIZE * factor, height=SIZE * factor, resampleAlg=alg,
    )
    return out.ReadAsArray().astype(np.float32)


def measure(up):
    # Each 2x2 output block maps to one source pixel; compare against the
    # four-neighbour envelope of the interior grid.
    inner = up[:, 1:-1, 1:-1][:, ::2, ::2]          # one sample per interior cell
    n = min(inner.shape[1], lo.shape[1]), min(inner.shape[2], lo.shape[2])
    a = inner[:, :n[0], :n[1]]
    l = lo[:, :n[0], :n[1]]
    h = hi[:, :n[0], :n[1]]
    over = np.maximum(a - h, 0) + np.maximum(l - a, 0)
    ringing_pct = (over > 1.0).mean() * 100
    ringing_max = over.max()
    gy = np.abs(np.diff(up, axis=1)).mean()
    gx = np.abs(np.diff(up, axis=2)).mean()
    return ringing_pct, ringing_max, (gx + gy) / 2


print(f"{'kernel':14s} {'ringing %':>10s} {'worst':>7s} {'sharpness':>10s}")
results = {}
for alg in ["near", "bilinear", "cubic", "cubicspline", "lanczos"]:
    up = upsample(alg)
    pct, worst, sharp = measure(up)
    results[alg] = up
    print(f"{alg:14s} {pct:9.2f}% {worst:7.1f} {sharp:10.2f}")

# Side-by-side montage of a 96px detail, so the effect is visible as well as
# measured. Each panel is the same ground, upsampled differently.
DETAIL = 96
panels = []
for alg in ["near", "cubic", "lanczos"]:
    up = results[alg]
    panels.append(up[:, 100:100 + DETAIL * 2, 100:100 + DETAIL * 2])
gap = np.full((3, DETAIL * 2, 8), 255, np.float32)
montage = np.concatenate([panels[0], gap, panels[1], gap, panels[2]], axis=2)
mem = gdal.GetDriverByName("MEM").Create("", montage.shape[2], montage.shape[1], 3, gdal.GDT_Byte)
for i in range(3):
    mem.GetRasterBand(i + 1).WriteArray(np.clip(montage[i], 0, 255))
gdal.GetDriverByName("PNG").CreateCopy(OUT + r"\upsample_compare.png", mem)
print("\nmontage (near | cubic | lanczos) written")
