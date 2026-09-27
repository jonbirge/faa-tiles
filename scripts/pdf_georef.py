"""Read the georeferencing a PDF chart carries in itself.

Several publishers issue their VFR chart as a vector PDF with the registration
written into the file, as ISO 32000 provides: the page has *viewports*, each a
box on the page with a ``Measure`` dictionary giving the projection as WKT and
the longitude and latitude of the box's corners. Latvia, Estonia, Romania,
Taiwan, Denmark, Spain and Brazil all do. That is everything ``render_pdfs.py``
needs to draw a sheet at whatever scale the target zoom wants, and unlike the
FAA's PDFs nothing has to be registered against a GeoTIFF first.

**This project's GDAL cannot do it.** Its PDF driver is built without a reader
and opens no PDF at all, so the dictionaries are read with ``pypdf`` and the
arithmetic is done here.

A page can hold several viewports -- the main map, an overview, insets printed
over the map, a reverse side -- so which one a sheet is has to be said: by
name, or as the largest on the page.

What comes out is the same record ``detect_pdf_windows.py`` writes for the FAA's
charts, one a sheet: the PDF, the window of the page that is the map, in pixels
at a base resolution, and the geotransform of that window. It is made afresh
from the PDF whenever it is wanted rather than reviewed and committed, because
it is read, not detected: there is nothing in it to review that the publisher
did not write.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from osgeo import osr

osr.UseExceptions()

# A viewport's corners, projected, should be where an affine from the page puts
# them. Further out than this, in pixels at the base resolution, and the file's
# registration is not to be trusted: Albania's chart declares a box a fifth of
# a degree across for a map of three degrees.
MISFIT = 3.0


@dataclass(frozen=True)
class Viewport:
    """One georeferenced box on a page."""

    name: str
    # The box, in points from the page's bottom-left corner: left, bottom,
    # right, top.
    box: tuple[float, float, float, float]
    # Points of the page, and the longitude and latitude at each.
    page: tuple[tuple[float, float], ...]
    lonlat: tuple[tuple[float, float], ...]
    wkt: str
    page_size: tuple[float, float]

    @property
    def area(self) -> float:
        left, bottom, right, top = self.box
        return (right - left) * (top - bottom)


def viewports(path: str | Path, page_number: int = 0) -> list[Viewport]:
    """Every georeferenced viewport of a page, largest first."""
    import pypdf             # read on use: only series that are PDFs need it

    page = pypdf.PdfReader(str(path)).pages[page_number]
    unit = float(page.get("/UserUnit", 1))
    size = (float(page.mediabox.width) * unit, float(page.mediabox.height) * unit)
    found = []
    for item in page.get("/VP", []):
        viewport = item.get_object()
        measure = viewport.get("/Measure")
        if measure is None:
            continue
        measure = measure.get_object()
        if measure.get("/Subtype") != "/GEO" or "/GPTS" not in measure:
            continue
        x0, y0, x1, y1 = (float(v) * unit for v in viewport["/BBox"])
        gpts = [float(v) for v in measure["/GPTS"]]
        # LPTS places the geographic points in the box, as fractions of it;
        # without it they are the box's corners, anticlockwise from bottom-left.
        lpts = [float(v) for v in measure.get("/LPTS", [0, 0, 0, 1, 1, 1, 1, 0])]
        count = min(len(gpts), len(lpts)) // 2
        left, right = min(x0, x1), max(x0, x1)
        bottom, top = min(y0, y1), max(y0, y1)
        # The fractions are of the box as written, which need not be written
        # bottom-left first: Latvia's is top-left to bottom-right.
        page_points = tuple((x0 + lpts[2 * i] * (x1 - x0), y0 + lpts[2 * i + 1] * (y1 - y0))
                            for i in range(count))
        lonlat = tuple((gpts[2 * i + 1], gpts[2 * i]) for i in range(count))
        gcs = measure["/GCS"].get_object()
        found.append(Viewport(
            name=str(viewport.get("/Name", "")), box=(left, bottom, right, top),
            page=page_points, lonlat=lonlat, wkt=str(gcs.get("/WKT", "")), page_size=size))
    return sorted(found, key=lambda v: -v.area)


def horizontal(wkt: str) -> str:
    """The first coordinate system in ``wkt``, whole, and nothing after it.

    Taiwan's chart appends a vertical datum to its projection, as a second
    system after the first. A chart has no use for one, and a GeoTIFF given a
    compound system it cannot describe is written with no projection at all.
    """
    start = min((i for i in (wkt.find("PROJCS["), wkt.find("GEOGCS[")) if i >= 0), default=-1)
    if start < 0:
        raise ValueError(f"no coordinate system in {wkt[:60]!r}")
    depth = 0
    for i in range(start, len(wkt)):
        if wkt[i] == "[":
            depth += 1
        elif wkt[i] == "]":
            depth -= 1
            if depth == 0:
                return wkt[start:i + 1]
    raise ValueError(f"unbalanced brackets in {wkt[:60]!r}")


def spatial_reference(wkt: str) -> osr.SpatialReference:
    srs = osr.SpatialReference()
    srs.ImportFromWkt(horizontal(wkt))
    # These are written by Esri's software, in Esri's dialect.
    srs.MorphFromESRI()
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


def entry(pdf: Path, viewport: Viewport, dpi: float) -> dict:
    """The render record for one viewport: its window of the page in pixels at
    ``dpi``, and that window's geotransform and projection."""
    per_point = dpi / 72.0
    left, bottom, right, top = viewport.box
    page_height = viewport.page_size[1]
    x = int(np.floor(left * per_point))
    y = int(np.floor((page_height - top) * per_point))
    width = int(np.ceil(right * per_point)) - x
    height = int(np.ceil((page_height - bottom) * per_point)) - y

    srs = spatial_reference(viewport.wkt)
    wgs = osr.SpatialReference()
    wgs.ImportFromEPSG(4326)
    wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    # The geographic points are on the projection's own datum.
    geographic = srs.CloneGeogCS()
    geographic.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    forward = osr.CoordinateTransformation(geographic, srs)
    projected = np.array(forward.TransformPoints([list(p) for p in viewport.lonlat]))[:, :2]
    pixels = np.array([(px * per_point - x, (page_height - py) * per_point - y)
                       for px, py in viewport.page])
    if len(pixels) < 3:
        raise ValueError(f"{pdf.name}: viewport {viewport.name!r} has fewer than three points")
    design = np.c_[np.ones(len(pixels)), pixels]
    solution, *_ = np.linalg.lstsq(design, projected, rcond=None)
    misfit = np.hypot(*(design @ solution - projected).T) / abs(solution[1, 0] or 1)
    if misfit.max() > MISFIT:
        raise ValueError(
            f"{pdf.name}: viewport {viewport.name!r} does not fit its own corners "
            f"({misfit.max():.1f} px); its registration cannot be trusted")
    return {
        "pdf": pdf.name,
        "viewport": viewport.name,
        "window": [x, y, width, height],
        "size": [width, height],
        "dpi": float(dpi),
        "geotransform": [float(solution[0, 0]), float(solution[1, 0]), float(solution[2, 0]),
                         float(solution[0, 1]), float(solution[1, 1]), float(solution[2, 1])],
        # WKT 1, which is what a GeoTIFF is written with; a PDF that appends a
        # vertical datum to its projection otherwise comes out as WKT 2 and is
        # written as nothing at all.
        "projection": srs.ExportToWkt(["FORMAT=WKT1_GDAL"]),
    }


def choose(found: list[Viewport], names: tuple[str, ...]) -> list[Viewport]:
    """The viewports that are sheets: those named, or the largest if none is."""
    if not found:
        return []
    if not names:
        return [found[0]]
    chosen = [v for name in names for v in found if v.name == name]
    return chosen


def manifest(chart_series) -> dict:
    """The render records for every PDF a series has downloaded, by the name of
    the raster each becomes."""
    out = {}
    for pdf in sorted(chart_series.pdf_directory.glob("*.pdf")):
        found = viewports(pdf)
        chosen = choose(found, chart_series.pdf_viewports)
        if not chosen:
            raise SystemExit(
                f"{pdf.name} has no viewport named {', '.join(chart_series.pdf_viewports)}; "
                f"it has {', '.join(repr(v.name) for v in found) or 'none at all'}")
        for viewport in chosen:
            name = pdf.stem if len(chosen) == 1 else f"{pdf.stem}-{_slug(viewport.name)}"
            out[f"{name}.tif"] = entry(pdf, viewport, chart_series.pdf_dpi)
    return out


def _slug(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")
