#!/usr/bin/env python
"""Find each sectional's map area and write it to the area manifest.

    .venv/Scripts/python scripts/detect_sectional_areas.py [--sheet DIR] [CHART ...]

Each sheet is a map inside a printed collar: a legend panel down the left, notes
along the bottom, sometimes a strip across the top, often a thin paper margin on
the other sides. The collar is paper white; the map is not.

Neatlines are not one kind of line. Some are meridians or parallels, curved in
the image; some are straight in the image; and at Alaskan latitudes a meridian
leans steeply while the legend panel beside it is an upright rectangle. So no
lon/lat rectangle fits every sheet, and each side is found in image space
instead:

1. Walk in from the image edge in ``WINDOWS`` bands along the side, and record
   where sustained non-paper begins.
2. Fit a curve through those depths, trimming outliers: a band crossing a
   colourful legend graphic reads shallow, one over pale map (snowfield) reads
   deep. West and east get straight lines, because a meridian is straight in a
   conic projection; north and south get quadratics, to follow a parallel's arc.
   Each side is measured only between the two sides across it, so no band runs
   along a perpendicular collar, and the curve is held flat beyond the last
   band rather than extrapolated.
3. Move the fitted curve inward past the deepest surviving measurement, plus a
   margin. Erring inward costs a kilometre of map that a neighbouring sheet
   overlaps anyway; erring outward pastes a strip of collar onto the globe.

The four curves bound a pixel polygon, written to ``scripts/sectional_areas.json``
as that chart's ``include``. Hand-authored keys are never touched: ``exclude``
polygons (enlarged insets drawn over the map), ``open_sides`` (sides to leave
unfitted because an inset near them fools the fit), and ``"manual": true``, which
skips the chart entirely -- for sheets that are not a map in a collar at all.

``--sheet DIR`` writes contact sheets with every chart's final map area outlined.
Rerun this for each new edition and review the sheets and the manifest diff.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from osgeo import gdal, ogr

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from cesiumtiles.mosaic import MapArea, MosaicSource, _map_points, prepare_sources  # noqa: E402

gdal.UseExceptions()
ogr.UseExceptions()

SECTIONALS = REPO / "sectionals"
MANIFEST = Path(__file__).resolve().parent / "sectional_areas.json"

DECIMATE = 4          # measure on a 1/4-scale image
WINDOWS = 48          # bands per side
PAPER = 250           # min channel value counted as paper (collar paper is 255; Canada tint is 232-242)
MAP_RUN = 600         # full-res pixels (~25 km) of mostly non-paper that mark the map
MAP_ONSET = 48        # full-res pixels right at the map edge that must be non-paper
MIN_COLLAR = 8        # full-res pixels of paper before a side counts as collared
TRIM_PASSES = 4       # outlier-trimming refits
KEEP_RESIDUAL = 60    # full-res pixels from the fit a measurement may sit and still count
MARGIN = 24           # full-res pixels moved inward past the deepest kept measurement
EDGE_TRIM = 40        # full-res pixels trimmed from every image edge (thin paper margins)
PAPER_WARNING = 0.25  # paper fraction just inside an edge that suggests collar was left in


def _paper(path: Path) -> np.ndarray:
    # Sampled, not averaged: averaging smears the type in a notes panel into
    # grey, which reads as map and stops the walk halfway through the collar.
    ds = gdal.Open(str(path))
    small = gdal.Translate("", ds, format="MEM", width=ds.RasterXSize // DECIMATE,
                           height=ds.RasterYSize // DECIMATE, rgbExpand="rgb", resampleAlg="near")
    return small.ReadAsArray().min(axis=0) >= PAPER


def paper_inside_edges(path: Path, area: MapArea, depth: int = 120) -> dict[str, float]:
    """Fraction of paper in the band just inside each side of a map area.

    Map right up against a neatline is rarely paper; a collar is mostly paper.
    A high figure means the outline stops short of the neatline and some
    collar will reach the globe.
    """
    [prepared] = prepare_sources([MosaicSource(path, area)])
    if prepared.pixel_area_wkt is None:
        return {}
    paper = _paper(path)
    rows, cols = paper.shape
    area_geom = ogr.CreateGeometryFromWkt(prepared.pixel_area_wkt)
    band = area_geom.Buffer(-4).Difference(area_geom.Buffer(-depth))
    mem = gdal.GetDriverByName("MEM").Create("", cols, rows, 1, gdal.GDT_Byte)
    mem.SetGeoTransform((0, DECIMATE, 0, 0, 0, DECIMATE))
    layer_ds = ogr.GetDriverByName("MEM").CreateDataSource("")
    layer = layer_ds.CreateLayer("band", geom_type=ogr.wkbMultiPolygon)
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(band)
    layer.CreateFeature(feature)
    gdal.RasterizeLayer(mem, [1], layer, burn_values=[1])
    inside = mem.ReadAsArray().astype(bool)

    # Attribute each band pixel to the image side it is nearest, which for a
    # collar outline is the side it runs along.
    yy, xx = np.nonzero(inside)
    distance = np.stack([xx, cols - xx, yy, rows - yy])
    side = np.argmin(distance, axis=0)
    result = {}
    for i, name in enumerate(("west", "east", "north", "south")):
        picked = side == i
        if picked.sum() > 50:
            result[name] = float(paper[yy[picked], xx[picked]].mean())
    return result


def _depth(paper_band: np.ndarray) -> int | None:
    """Collar depth in decimated pixels for one band, walking along axis 1."""
    frac = paper_band.mean(axis=0)
    run = MAP_RUN // DECIMATE
    onset = MAP_ONSET // DECIMATE
    for i in range(0, len(frac) - run):
        # The map must start here, not just lie somewhere ahead: a scale-bar
        # line printed just outside the neatline is dark for a row or two, and
        # with only the long-run test it passed for the map edge.
        if frac[i:i + onset].mean() < 0.35 and np.median(frac[i:i + run]) < 0.3:
            return i
    return None


class _Side:
    """A fitted collar edge: ``depth(position)`` in full-res pixels, already
    moved inward, and clamped flat beyond the span that was measured."""

    def __init__(self, coef, offset, lo, hi):
        self.coef, self.offset, self.lo, self.hi = coef, offset, lo, hi

    def __call__(self, t):
        return np.polyval(self.coef, np.clip(t, self.lo, self.hi)) + self.offset


def _fit_side(paper: np.ndarray, degree: int, span: tuple[float, float]) -> _Side | None:
    """Fit the side at column 0 of ``paper`` from bands whose centres fall in
    ``span`` (full-res positions along the side). None if it has no collar."""
    rows = paper.shape[0]
    edges = np.linspace(0, rows, WINDOWS + 1).astype(int)
    pos, depth = [], []
    for a, b in zip(edges, edges[1:]):
        centre = (a + b) / 2 * DECIMATE
        if not span[0] <= centre <= span[1]:
            continue
        d = _depth(paper[a:b])
        if d is not None:
            pos.append(centre)
            depth.append(d * DECIMATE)
    pos, depth = np.array(pos), np.array(depth, dtype=float)
    if len(depth) < 8 or np.median(depth) < MIN_COLLAR:
        return None

    # Start from the median line, which ignores a minority of wild bands, then
    # refit on the bands near it.
    keep = np.abs(depth - np.median(depth)) <= max(KEEP_RESIDUAL, 3 * np.median(np.abs(depth - np.median(depth))))
    for _ in range(TRIM_PASSES):
        if keep.sum() < degree + 4:
            return None
        coef = np.polyfit(pos[keep], depth[keep], degree)
        resid = depth - np.polyval(coef, pos)
        mad = np.median(np.abs(resid[keep]))
        keep = np.abs(resid) <= max(KEEP_RESIDUAL, 4 * mad)
    coef = np.polyfit(pos[keep], depth[keep], degree)
    resid = depth[keep] - np.polyval(coef, pos[keep])
    return _Side(coef, float(max(resid.max(), 0.0)) + MARGIN, pos[keep].min(), pos[keep].max())


def detect(path: Path, open_sides=()) -> tuple[list[list[float]] | None, list[str]]:
    """The chart's map area as a pixel polygon, plus notes for the reviewer.

    ``open_sides`` names sides known to have no collar, for sheets where
    something printed over the map near that edge (an inset) fools the fit."""
    paper = _paper(path)
    ds = gdal.Open(str(path))
    width, height = ds.RasterXSize, ds.RasterYSize
    notes = []

    # Orient each side so column 0 is its outer edge; positions run along it.
    views = {
        "west": paper,
        "east": paper[:, ::-1],
        "north": paper.T,
        "south": paper[::-1, :].T,
    }
    # Meridians are straight lines in a conic projection, and so are neatlines
    # drawn straight; parallels are gentle arcs. Hence lines for west/east and
    # quadratics for north/south.
    degree = {"west": 1, "east": 1, "north": 2, "south": 2}
    extent = {"west": height, "east": height, "north": width, "south": width}

    # Each side is measured only between the two sides across it, so a band
    # never runs along a perpendicular collar. Start from the middle half, then
    # alternate, letting each pair tighten the other.
    fits: dict[str, _Side | None] = {}
    spans = {s: (0.25 * extent[s], 0.75 * extent[s]) for s in views}
    for order in (("west", "east"), ("north", "south"), ("west", "east"), ("north", "south")):
        for side in order:
            fits[side] = None if side in open_sides else _fit_side(views[side], degree[side], spans[side])
        a, b = order
        other = ("north", "south") if a == "west" else ("west", "east")
        lo = fits[a](np.array([extent[a] / 2]))[0] if fits[a] else 0.0
        hi = fits[b](np.array([extent[b] / 2]))[0] if fits[b] else 0.0
        for side in other:
            spans[side] = (lo + 0.02 * extent[side], extent[side] - hi - 0.02 * extent[side])

    samples = 256
    big = 10 * max(width, height)
    # Sides with no collar still often carry a ragged paper margin a few tens of
    # pixels wide, too thin for a fit to see, so every image edge is trimmed.
    e = EDGE_TRIM
    region = ogr.CreateGeometryFromWkt(
        f"POLYGON(({e} {e},{width - e} {e},{width - e} {height - e},{e} {height - e},{e} {e}))")
    for side in views:
        fit = fits[side]
        if fit is None:
            continue
        along = extent[side]
        t = np.linspace(-0.05 * along, 1.05 * along, samples)
        d = fit(t)
        notes.append(f"{side}: {d.min():.0f}-{d.max():.0f} px")
        if side == "west":
            line = [(x, y) for x, y in zip(d, t)] + [(big, 1.05 * along), (big, -0.05 * along)]
        elif side == "east":
            line = [(width - x, y) for x, y in zip(d, t)] + [(-big, 1.05 * along), (-big, -0.05 * along)]
        elif side == "north":
            line = [(x, y) for x, y in zip(t, d)] + [(1.05 * along, big), (-0.05 * along, big)]
        else:
            line = [(x, height - y) for x, y in zip(t, d)] + [(1.05 * along, -big), (-0.05 * along, -big)]
        half = ogr.CreateGeometryFromWkt(
            "POLYGON((" + ",".join(f"{x} {y}" for x, y in line + line[:1]) + "))")
        region = region.Intersection(half)

    if region.IsEmpty():
        return None, notes + ["nothing left inside the detected collar"]
    if region.GetGeometryName() != "POLYGON":
        return None, notes + [f"detected area is a {region.GetGeometryName()}, expected one polygon"]
    region = region.SimplifyPreserveTopology(1.0)
    ring = region.GetGeometryRef(0)
    points = [[round(ring.GetX(i), 1), round(ring.GetY(i), 1)] for i in range(ring.GetPointCount() - 1)]
    return points, notes


def contact_sheets(manifest: dict, out_dir: Path, width: int = 420, per_sheet: int = 16) -> None:
    from PIL import Image, ImageDraw

    out_dir.mkdir(parents=True, exist_ok=True)
    names = sorted(manifest)
    for sheet in range(0, len(names), per_sheet):
        thumbs = []
        for name in names[sheet:sheet + per_sheet]:
            path = SECTIONALS / name
            ds = gdal.Open(str(path))
            scale = width / ds.RasterXSize
            small = gdal.Translate("", ds, format="MEM", width=width, rgbExpand="rgb", resampleAlg="average")
            im = Image.fromarray(small.ReadAsArray().transpose(1, 2, 0))
            draw = ImageDraw.Draw(im)
            [p] = prepare_sources([MosaicSource(path, MapArea.from_dict(manifest[name]))])
            if p.pixel_area_wkt:
                geom = _map_points(ogr.CreateGeometryFromWkt(p.pixel_area_wkt),
                                   lambda pts: [(x * scale, y * scale) for x, y in pts])
                polys = [geom] if geom.GetGeometryName() == "POLYGON" else \
                    [geom.GetGeometryRef(i) for i in range(geom.GetGeometryCount())]
                for poly in polys:
                    for r in range(poly.GetGeometryCount()):
                        ring = poly.GetGeometryRef(r)
                        draw.line([ring.GetPoint_2D(i) for i in range(ring.GetPointCount())],
                                  fill=(255, 0, 255), width=2)
            draw.text((4, 4), name.removesuffix(" SEC.tif"), fill=(255, 0, 0))
            thumbs.append(im)
        cols = 4
        cell = max(t.height for t in thumbs)
        canvas = Image.new("RGB", (width * cols, cell * ((len(thumbs) + cols - 1) // cols)), (80, 80, 80))
        for i, t in enumerate(thumbs):
            canvas.paste(t, ((i % cols) * width, (i // cols) * cell))
        target = out_dir / f"areas-{sheet // per_sheet}.png"
        canvas.save(target)
        print(f"wrote {target}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("charts", nargs="*", help="chart file names to detect (default: all)")
    ap.add_argument("--sheet", type=Path, help="write review contact sheets into this directory")
    ap.add_argument("--no-detect", action="store_true", help="only draw contact sheets")
    args = ap.parse_args(argv)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    names = args.charts or sorted(p.name for p in SECTIONALS.glob("*.tif"))

    if not args.no_detect:
        for name in names:
            entry = manifest.setdefault(name, {})
            if entry.get("manual"):
                print(f"{name}: manual, skipped")
                continue
            points, notes = detect(SECTIONALS / name, entry.get("open_sides", ()))
            entry.pop("limits", None)
            if points is None:
                entry.pop("include", None)
            else:
                entry["include"] = [{"pixel": points}]
            print(f"{name}: " + ("; ".join(notes) or "no collar found"), flush=True)
        ordered = {k: manifest[k] for k in sorted(manifest)}
        MANIFEST.write_text(json.dumps(ordered, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {MANIFEST}")

    print(f"\npaper just inside each edge (flagged above {PAPER_WARNING:.0%}):")
    flagged = 0
    for name in names:
        fractions = paper_inside_edges(SECTIONALS / name, MapArea.from_dict(manifest.get(name, {})))
        high = {k: v for k, v in fractions.items() if v > PAPER_WARNING}
        flagged += bool(high)
        shown = "  ".join(f"{k} {v:.0%}" for k, v in fractions.items())
        print(f"  {'!!' if high else '  '} {name:40s} {shown}")
    print(f"{flagged} chart(s) flagged")

    if args.sheet:
        contact_sheets(manifest, args.sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
