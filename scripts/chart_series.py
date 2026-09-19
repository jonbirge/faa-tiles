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
    index_url: str = ""
    # Path inside an edition folder that lists the zips ("" for the folder).
    files_path: str = ""
    # Zips to download, matched against the file name.
    zip_pattern: str = ""
    # GeoTIFFs to keep from those zips, matched against the file name. Anything
    # else in a zip -- insets, notes, other products -- is not extracted.
    tif_pattern: str = ""
    # The script that writes this series' map-area manifest. Each series' sheets
    # are a different detection problem: a sectional or a TAC is a map inside a
    # paper collar, an IFR sheet is a map inside a drawn frame.
    detector: str = ""
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
    # Super-resolve the sheets before tiling (0: do not). Weights are a file
    # name under source/models. Only for series whose sheets are rasters at
    # source; a series that renders vector PDFs has nothing to recover.
    upsample_model: str = ""
    upsample_scale: int = 0
    # Paint order where sheets overlap. Sheets are drawn in file-name order and
    # a later sheet lands on top; reverse puts the earliest name on top instead.
    reverse_order: bool = False
    # Sheets meet edge to edge at a drawn frame rule rather than overlapping, so
    # the rule is painted over (heal_frames.py) and the build tiles the healed
    # copies. Needs a manifest with a "frame" per sheet (detect_ifr_areas.py).
    heal_frames: bool = False
    # Lossless WebP tiles instead of lossy q90.
    lossless: bool = False
    # Deepest zoom level tiled; see each series' note (sectionals z12, IFR z13).
    # Keep this in step with any stage that changes resolution (pdf_scale,
    # upsample_scale) -- they determine whether the warp magnifies or minifies.
    max_zoom: int = 11
    # A composite series: other series painted into one tileset, in this order,
    # later ones on top. It downloads, prepares and detects nothing of its own
    # -- each member stays a series, fetched and reviewed as one -- so a
    # composite reuses whatever its members already have on disk.
    layers: tuple[str, ...] = ()
    # Members fine enough to earn a level past ``max_zoom``, and which level
    # that is (0: none). It is sparse -- only the tiles those members reach
    # (mosaic.plan_detail_tiles) -- so it costs a fraction of a full level.
    detail_layers: tuple[str, ...] = ()
    detail_zoom: int = 0

    @property
    def is_composite(self) -> bool:
        return bool(self.layers)

    @property
    def members(self) -> tuple["Series", ...]:
        """The series this one paints, in paint order; itself if it is not a
        composite, so a caller can loop either way."""
        return tuple(SERIES[name] for name in self.layers) if self.layers else (self,)

    def _own(self, what: str) -> None:
        if self.is_composite:
            raise SystemExit(
                f"{self.name} is a composite of {', '.join(self.layers)} and has no {what} "
                f"of its own; run that stage against a member series instead")

    @property
    def directory(self) -> Path:
        """Where the GeoTIFFs are downloaded to."""
        self._own("download directory")
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
    def upscaled_directory(self) -> Path:
        """Where upsample_charts.py writes super-resolved copies of the sheets."""
        return self.directory / "upscaled"

    @property
    def healed_directory(self) -> Path:
        """Where heal_frames.py writes frame-healed copies of the sheets."""
        return self.directory / "healed"

    @property
    def stages(self) -> tuple[tuple[str, Path], ...]:
        """Each preparation stage as ``(script, output directory)``, in order.

        The first reads what was downloaded; each later one reads the previous
        one's output; the build tiles the last. A series with no stages is
        tiled straight from its download.
        """
        out = []
        if self.pdf_scale:
            out.append(("render_pdfs.py", self.render_directory))
        if self.upsample_scale:
            out.append(("upsample_charts.py", self.upscaled_directory))
        if self.heal_frames:
            out.append(("heal_frames.py", self.healed_directory))
        return tuple(out)

    def input_directory(self, script: str) -> Path:
        """Where the stage run by ``script`` reads its rasters from."""
        previous = self.directory
        for name, output in self.stages:
            if name == script:
                return previous
            previous = output
        raise KeyError(f"{self.name} has no {script} stage")

    @property
    def build_directory(self) -> Path:
        """The rasters a build tiles: the last preparation stage's output."""
        return self.stages[-1][1] if self.stages else self.directory

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
        frame bands are scaled by this before they are used against a prepared
        raster. Stages that change resolution multiply together.
        """
        return (self.pdf_scale or 1) * (self.upsample_scale or 1)

    @property
    def manifest(self) -> Path:
        """The reviewed map-area manifest for the series."""
        self._own("map-area manifest")
        return SCRIPTS / f"{self.name.replace('-', '_')}_areas.json"

    @property
    def pdf_manifest(self) -> Path:
        """The reviewed PDF-to-GeoTIFF registration (detect_pdf_windows.py)."""
        return SCRIPTS / f"{self.name.replace('-', '_')}_pdf.json"

    @property
    def tileset(self) -> Path:
        return REPO / f"tileset-{self.name}"

    def wants_zip(self, name: str) -> bool:
        return bool(self.zip_pattern) and re.fullmatch(
            self.zip_pattern, name, re.IGNORECASE) is not None

    def wants_tif(self, name: str) -> bool:
        return (bool(self.tif_pattern)
                and re.fullmatch(self.tif_pattern, name, re.IGNORECASE) is not None
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
            detector="detect_sectional_areas.py",
            # The user's call. Both ship inside Hawaiian_Islands.zip alongside
            # Hawaiian Islands and Honolulu, so exclusion is per GeoTIFF.
            exclude=frozenset({
                "Mariana Islands Inset SEC.tif",   # Guam
                "Samoan Islands Inset SEC.tif",    # American Samoa
            }),
            # The FAA's sectional rasters staircase, and unlike the IFR charts
            # there is no vector source to fall back on -- the sectional PDFs
            # wrap the same rasters. Real-CUGAN 2x it is; the user compared
            # denoise3x against a plain z12 build of the same three sheets and
            # kept the upsampling.
            upsample_model="realcugan-up2x-denoise3x.pth",
            upsample_scale=2,
            # The median lower-48 sheet is 42.3 m/px, native z11.5; upsampled
            # 2x it is z12.5. So z12 tiles (30 m/px) are slightly *coarser* than
            # the upsampled source and the warp minifies, which is where the
            # upsampling pays off. z13 (15 m/px) would be 1.4x finer than even the
            # upsampled sheets -- interpolation for ~4x the tiles, disk and time.
            # The user's call, on those numbers, after first choosing z13.
            max_zoom=12,
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
            detector="detect_ifr_areas.py",
            # The same 36 charts as vector PDFs, two per zip (DELUS1 is L-01
            # and L-02, and so on through DELUS35). Rendered above the
            # GeoTIFF's 400 dpi, they antialias properly instead of carrying
            # the FAA raster's baked-in staircasing -- the user's call after
            # seeing the two side by side.
            pdf_zip_pattern=r"DELUS\d{1,2}\.zip",
            pdf_pattern=r"ENR_L\d\d\.pdf",
            # 4x, i.e. 1600 dpi. This is tied to max_zoom and must be revisited
            # with it: a z13 tile is ~14.7 m/px on the ground where these sheets
            # sit, so at 2x (23.15 m/px) the warp was *magnifying* 1.58x and the
            # tiles were finer than the source feeding them. At 4x the source is
            # 11.58 m/px and the warp minifies (0.79x), which is the regime
            # GDAL's kernel widening handles properly -- and the extra detail is
            # real vector, not interpolation.
            pdf_scale=4,
            # The user's call, after seeing overlap artefacts with name order.
            reverse_order=True,
            # The user's call, after black seams between every pair of charts.
            heal_frames=True,
            # Rendered at 4x the sheets resolve past z13, which is where
            # the user asked to tile them. The earlier z11 and z12 were trials.
            max_zoom=13,
            # The user's call: IFR charts are thin linework and small type on
            # white, which lossy compression softens.
            lossless=True,
        ),
        Series(
            name="tac",
            title="FAA VFR Terminal Area Charts",
            index_url="https://aeronav.faa.gov/visual/",
            files_path="tac-files/",
            zip_pattern=r".+_TAC\.zip",
            # The TAC itself and nothing else. A zip also carries that city's
            # Flyway Planning chart ("Denver FLY.tif"), sometimes an airspace
            # graphic ("Anchorage Graphic.tif") or a planning chart ("New York
            # TAC VFR Planning Charts.tif"), none of which are map. It is per
            # GeoTIFF rather than per zip because one zip can hold two TACs:
            # 30 zips yield 34 sheets -- Anchorage/Fairbanks,
            # Denver/Colorado Springs, Seattle/Portland, Tampa/Orlando.
            tif_pattern=r".+ TAC\.tif",
            # A TAC is a map in a paper collar, exactly like a sectional, so it
            # is the same detection problem and the same script.
            detector="detect_sectional_areas.py",
            # Same rasterisation, same staircasing, same absence of a vector
            # source as the sectionals; the FAA's own note calls these 300 dpi
            # 8-bit images. Upsampled with the same weights so the two series
            # meet on equal terms where a TAC is laid over its sectional.
            upsample_model="realcugan-up2x-denoise3x.pth",
            upsample_scale=2,
            # 1:250,000 at 300 dpi is 21.17 m/px, measured off the world files
            # -- exactly half the sectionals' 42.3, so native z12.5 and z13.5
            # upsampled. z13 is where these sheets stop holding detail, the same
            # rule that put the sectionals at z12.
            max_zoom=13,
        ),
        Series(
            name="sectionals-tac",
            title="FAA VFR Sectionals with Terminal Area Charts",
            # The fourth tileset: the sectional mosaic with each terminal area
            # chart laid over it where one is published. TACs paint last, so
            # they are on top wherever they reach (the user's call), and they
            # carry the z13 detail level because they are the finer sheets.
            layers=("sectionals", "tac"),
            detail_layers=("tac",),
            max_zoom=12,
            detail_zoom=13,
        ),
    )
}


def series(name: str) -> Series:
    try:
        return SERIES[name]
    except KeyError:
        raise SystemExit(f"unknown series {name!r}; choose from {', '.join(SERIES)}") from None
