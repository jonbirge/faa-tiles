"""The FAA chart series this repo downloads and tiles, and where each lives.

Every stage -- fetch_charts.py, the area detectors, build_chart_tileset.py --
looks a series up here, so a series is described once. Standard library only.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import REPO, SCRIPTS, SOURCE  # noqa: E402


@dataclass(frozen=True)
class Series:
    name: str
    title: str
    # Directory listing holding one MM-DD-YYYY folder per edition. The FAA
    # posts the next edition's folder early, so the current one is the latest
    # that is not in the future.
    index_url: str
    # Path inside an edition folder that lists the zips ("" for the folder).
    files_path: str
    # Zips to download, matched against the file name.
    zip_pattern: str
    # GeoTIFFs to keep from those zips, matched against the file name. Anything
    # else in a zip -- insets, notes, other products -- is not extracted.
    tif_pattern: str
    # GeoTIFFs dropped by name even when the pattern keeps them. The build
    # skips these too, in case an older download left them on disk.
    exclude: frozenset[str] = frozenset()
    # Some series are also published as true vector PDFs, which rasterise far
    # cleaner than the FAA's own GeoTIFFs. These name the zips to download and
    # the PDFs to keep from them; the GeoTIFFs are still downloaded, because
    # they carry the georeferencing and the manifests are in their pixel space.
    pdf_zip_pattern: str = ""
    pdf_pattern: str = ""
    # Render the PDFs at this multiple of the GeoTIFF's pixel size and tile
    # those instead (0: tile the GeoTIFFs as downloaded). This is rendering,
    # not upsampling -- every pixel is drawn from the vector geometry.
    pdf_scale: int = 0
    # Paint order where sheets overlap. Sheets are drawn in file-name order and
    # a later sheet lands on top; reverse puts the earliest name on top instead.
    reverse_order: bool = False
    # Sheets meet edge to edge at a drawn frame rule rather than overlapping, so
    # the rule is painted over (heal_frames.py) and the build tiles the healed
    # copies. Needs a manifest with a "frame" per sheet (detect_ifr_areas.py).
    heal_frames: bool = False
    # Lossless WebP tiles instead of lossy q90.
    lossless: bool = False
    # Deepest zoom level tiled. z11 for both series is the user's call, to see
    # how it compares with z12 (roughly a quarter of the tiles).
    max_zoom: int = 11

    @property
    def directory(self) -> Path:
        """Where the GeoTIFFs are downloaded to."""
        return SOURCE / self.name

    @property
    def pdf_directory(self) -> Path:
        """Where the vector PDFs are downloaded to."""
        return self.directory / "pdf"

    @property
    def render_directory(self) -> Path:
        """Where render_pdfs.py writes the rasters it draws from the PDFs."""
        return self.directory / "rendered"

    @property
    def healed_directory(self) -> Path:
        """Where heal_frames.py writes frame-healed copies of the sheets."""
        return self.directory / "healed"

    @property
    def raster_directory(self) -> Path:
        """The rasters before healing: PDF renders if the series renders PDFs."""
        return self.render_directory if self.pdf_scale else self.directory

    @property
    def build_directory(self) -> Path:
        """The rasters a build tiles: healed copies if the series heals frames."""
        return self.healed_directory if self.heal_frames else self.raster_directory

    @property
    def fetches_tifs(self) -> bool:
        """Whether a routine fetch downloads the GeoTIFFs.

        A series that renders PDFs does not. The FAA's PDFs carry no
        georeferencing at all (their metadata says so outright), so it is taken
        from the GeoTIFFs once and recorded in the reviewed ``pdf_manifest``.
        After that the GeoTIFFs are only an input to re-detection for a new
        edition, which ``fetch_charts.py --tifs`` asks for.
        """
        return not self.pdf_scale

    @property
    def pixel_scale(self) -> int:
        """Pixels in a built raster per pixel of the downloaded GeoTIFF.

        The reviewed manifests are in GeoTIFF pixel space, so pixel polygons and
        frame bands are scaled by this before they are used against a render.
        """
        return self.pdf_scale or 1

    @property
    def manifest(self) -> Path:
        """The reviewed map-area manifest for the series."""
        return SCRIPTS / f"{self.name.replace('-', '_')}_areas.json"

    @property
    def pdf_manifest(self) -> Path:
        """The reviewed PDF-to-GeoTIFF registration (detect_pdf_windows.py)."""
        return SCRIPTS / f"{self.name.replace('-', '_')}_pdf.json"

    @property
    def tileset(self) -> Path:
        return REPO / f"tileset-{self.name}"

    def wants_zip(self, name: str) -> bool:
        return re.fullmatch(self.zip_pattern, name, re.IGNORECASE) is not None

    def wants_tif(self, name: str) -> bool:
        return (re.fullmatch(self.tif_pattern, name, re.IGNORECASE) is not None
                and name not in self.exclude)

    def wants_pdf_zip(self, name: str) -> bool:
        return bool(self.pdf_zip_pattern) and re.fullmatch(
            self.pdf_zip_pattern, name, re.IGNORECASE) is not None

    def wants_pdf(self, name: str) -> bool:
        return bool(self.pdf_pattern) and re.fullmatch(
            self.pdf_pattern, name, re.IGNORECASE) is not None


SERIES = {
    s.name: s
    for s in (
        Series(
            name="sectionals",
            title="FAA VFR Sectionals",
            index_url="https://aeronav.faa.gov/visual/",
            files_path="sectional-files/",
            zip_pattern=r".+\.zip",
            tif_pattern=r".+\.tif",
            # The user's call. Both ship inside Hawaiian_Islands.zip alongside
            # Hawaiian Islands and Honolulu, so exclusion is per GeoTIFF.
            exclude=frozenset({
                "Mariana Islands Inset SEC.tif",   # Guam
                "Samoan Islands Inset SEC.tif",    # American Samoa
            }),
        ),
        Series(
            name="ifr-low",
            title="FAA IFR Enroute Low (CONUS)",
            index_url="https://aeronav.faa.gov/enroute/",
            files_path="",
            # L-01 to L-36 only: not Alaska (AKL), Pacific (P) or area (A)
            # charts, which the user left out.
            zip_pattern=r"ENR_L\d\d\.zip",
            # Just the chart itself; zips can also carry inset TIFFs, which
            # the user chose to skip. L-06 is published in two halves,
            # ENR_L06N and ENR_L06S, both part of the chart.
            tif_pattern=r"ENR_L\d\d[NS]?\.tif",
            # The same 36 charts as vector PDFs, two per zip (DELUS1 is L-01
            # and L-02, and so on through DELUS35). Rendered at 2x the
            # GeoTIFF's 400 dpi, they antialias properly instead of carrying
            # the FAA raster's baked-in staircasing -- the user's call after
            # seeing the two side by side.
            pdf_zip_pattern=r"DELUS\d{1,2}\.zip",
            pdf_pattern=r"ENR_L\d\d\.pdf",
            pdf_scale=2,
            # The user's call, after seeing overlap artefacts with name order.
            reverse_order=True,
            # The user's call, after black seams between every pair of charts.
            heal_frames=True,
            # Rendered at 2x, the sheets resolve past z12, and the PDF test the
            # user approved was z12. The earlier z11 was a trial against the
            # GeoTIFFs, which do not hold that much detail.
            max_zoom=12,
            # The user's call: IFR charts are thin linework and small type on
            # white, which lossy compression softens.
            lossless=True,
        ),
    )
}


def series(name: str) -> Series:
    try:
        return SERIES[name]
    except KeyError:
        raise SystemExit(f"unknown series {name!r}; choose from {', '.join(SERIES)}") from None
