"""The chart series this repo downloads and tiles, and where each lives.

Every stage -- fetch_charts.py, the area detectors, build_chart_tileset.py --
looks a series up here, so a series is described once. The FAA's series came
first; the series from other publishers, which ``worldwide-vfr`` paints around
them, are described the same way and say who published them and on what terms.
Standard library only.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import REPO, SCRIPTS, SOURCE  # noqa: E402


@dataclass(frozen=True)
class Licence:
    """The terms a publisher releases a chart on.

    Free to download is not the same as free to republish. Every series records
    which it is, because the tilesets built here can end up on a public site:
    ``redistributable`` says whether tiles derived from the chart may be
    published, and a build can be held to the series where it is true
    (``build_chart_tileset.py --redistributable-only``). It is False unless the
    terms were read and say otherwise -- unclear terms are not permission.
    """

    name: str
    url: str = ""
    redistributable: bool = False
    # The credit line the terms ask for, shown wherever the tiles are.
    attribution: str = ""
    # What decided ``redistributable``, in a sentence, for whoever reviews it.
    note: str = ""


# Works of the US government are not subject to copyright in the US, and the
# FAA publishes its digital charts for free use.
FAA_LICENCE = Licence(
    name="Public domain (US Government work)",
    url="https://www.faa.gov/air_traffic/flight_info/aeronav/digital_products/",
    redistributable=True,
    attribution="Federal Aviation Administration",
    note="17 USC 105: no copyright in works of the United States Government.",
)


OFM_LICENCE = Licence(
    name="OFMA General Users' License",
    url="http://web.archive.org/web/20250406184228/https://www.openflightmaps.org/"
        "live/downloads/20150306-GUL.pdf",
    redistributable=True,
    attribution="Contains information from the open flightmaps database "
                "(openflightmaps.org); base map (c) OpenStreetMap contributors",
    note="Modelled on the ODbL: distribution and commercial use are granted, with "
         "attribution. The text is dated 2015 and is no longer on the live site; it was "
         "read from an archived copy, and no licence specific to the tiles was found.",
)

SWISSTOPO_LICENCE = Licence(
    name="swisstopo terms of use for free geodata (OGD)",
    url="https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices",
    redistributable=True,
    attribution="(c) swisstopo",
    note="Use, processing, distribution and commercial use are allowed; a source "
         "reference is mandatory.",
)

NAVIAIR_LICENCE = Licence(
    name="No terms stated (Naviair)",
    url="https://aim.naviair.dk/charts/",
    attribution="Naviair",
    note="Free download, but no licence was found on the charts page, the AIM home "
         "page or AIP GEN 3.2, and paper copies are sold. Unclear is not permission.",
)

ENAIRE_LICENCE = Licence(
    name="ENAIRE legal notice (all rights reserved)",
    url="https://www.enaire.es/aviso_legal",
    attribution="ENAIRE",
    note="Section 6 prohibits reproduction and communication to the public without "
         "ENAIRE's prior written authorisation.",
)

US_MILITARY_LICENCE = Licence(
    name="Public domain (US Government work)",
    url="https://maps.lib.utexas.edu/maps/faq.html",
    redistributable=True,
    attribution="U.S. Defense Mapping Agency / National Imagery and Mapping Agency; "
                "scans courtesy of the University of Texas Libraries",
    note="17 USC 105 for sheets with a US imprint. The University of Texas, which hosts "
         "the scans, warns that the US Government may claim copyright outside the US. "
         "Sheets produced by the UK or Australia are Crown copyright and are a series of "
         "their own.",
)

CROWN_LICENCE = Licence(
    name="Crown copyright (UK Ministry of Defence, Australian Department of Defence)",
    url="https://maps.lib.utexas.edu/maps/faq.html",
    attribution="UK Ministry of Defence / Australian Department of Defence; scans courtesy "
                "of the University of Texas Libraries",
    note="TPC E-2A, for one, carries a 1996 Crown copyright notice, which runs 50 years. "
         "Not redistributable until cleared sheet by sheet.",
)

ROMATSA_LICENCE = Licence(
    name="ROMATSA AIP copyright (all rights reserved)",
    url="https://www.aisro.ro/",
    attribution="ROMATSA",
    note="Reproduction needs ROMATSA's permission.",
)

TAIWAN_LICENCE = Licence(
    name="Open Government Data License, Taiwan, version 1.0",
    url="https://data.gov.tw/license",
    redistributable=True,
    attribution="Civil Aviation Administration, MOTC (Taiwan)",
    note="Declared on the CAA's main site; the chart is on a domain of its own with no "
         "licence text. Read as covered, not confirmed.",
)

EANS_LICENCE = Licence(
    name="EANS terms (no reproduction without written consent)",
    url="https://aim.eans.ee/en/vfr-chart",
    attribution="Estonian Air Navigation Services",
    note="Reproduction needs written consent.",
)

LGS_LICENCE = Licence(
    name="No policy stated (Latvijas gaisa satiksme)",
    url="https://ais.lgs.lv/page/VFR_Suport",
    attribution="Latvijas gaisa satiksme",
    note="The AIP says its copyright policy is not applicable; the sheet carries "
         "copyright marks. Unclear is not permission.",
)

DECEA_LICENCE = Licence(
    name="DECEA usage policy; AISWEB footer shows CC BY 4.0",
    url="https://ajuda.decea.mil.br/app/uploads/2019/04/Pol%C3%ADtica-de-Uso-POR.pdf",
    attribution="DECEA (Departamento de Controle do Espaco Aereo), Brazil",
    note="The two statements disagree. The policy allows non-commercial distribution "
         "and forbids what it does not authorise; the site footer carries a CC BY 4.0 "
         "badge. Leaning permitted for a non-commercial site with attribution, but not "
         "settled, so not marked redistributable.",
)


@dataclass(frozen=True)
class Series:
    name: str
    title: str
    # Who publishes the chart, and on what terms. Carried into the tileset's
    # metadata.json with the sheets each layer contributed.
    publisher: str = "Federal Aviation Administration"
    licence: Licence = FAA_LICENCE
    # A chart kept for its coverage rather than its currency: decades-old
    # sheets filling regions where nothing current is published free. Never
    # something to navigate by, and the metadata says so.
    historical: bool = False
    # How the series is downloaded. ``faa`` lists an edition folder of zips, as
    # below; the others are in fetchers.py:
    #   links  every link on ``index_url`` matching ``link_pattern`` -- a file,
    #          or a zip holding one. The pattern names a ``sheet`` group and may
    #          name a ``date`` (or ``year``) group; the latest of each sheet is
    #          kept, under the sheet's name, so a new edition replaces the old
    #          file and the reviewed manifest still names it.
    #   urls   the files in ``urls``, as they are
    #   ofm    open flightmaps tile zips for ``regions``, assembled into one
    #          raster a region
    fetcher: str = "faa"
    link_pattern: str = ""
    # The downloads are scans of paper, with no georeferencing in them: kept as
    # they come (``scan_suffix``) and registered by the graticule printed on
    # them, from the reviewed sheet index (rectify_charts.py). Everything after
    # that names a sheet's raster ``<sheet>.tif``, as for any other series.
    scan_suffix: str = ""
    urls: tuple[str, ...] = ()
    regions: tuple[str, ...] = ()
    # Seconds to wait between downloads, for a publisher whose terms or whose
    # servers ask for a light touch. Such a series is fetched one file at a time.
    fetch_delay: float = 0.0
    # The whole raster is map: no collar, no legend, nothing to detect. Such a
    # series has no detector and no manifest. A raster's own alpha band, if it
    # has one, is honoured either way.
    whole_image: bool = False
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
    # The PDFs carry their own georeferencing (pdf_georef.py), so there is no
    # GeoTIFF to register them against and no reviewed registration: each
    # sheet's window and affine are read from its PDF. ``pdf_dpi`` is the
    # resolution ``pdf_scale`` multiplies -- 300 dpi is 42.3 m a pixel at
    # 1:500,000, a sectional's pitch -- and ``pdf_viewports`` names the
    # viewports of a page that are sheets (the largest, if none is named).
    geopdf: bool = False
    pdf_dpi: int = 300
    pdf_viewports: tuple[str, ...] = ()
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
    # Write the prepared rasters JPEG-compressed. For a series that began as
    # JPEG scans and has hundreds of sheets: a tenth the size of lossless
    # copies, of pixels that were never lossless to begin with.
    lossy_intermediates: bool = False
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
    # A composite whose members are drawn at very different scales: each earns
    # tiles only as deep as its own ``max_zoom``, and every level past the
    # shallowest is sparse (mosaic.plan_stepped). ``detail_layers`` is the
    # one-step case of this and is not used with it.
    stepped: bool = False

    @property
    def is_composite(self) -> bool:
        return bool(self.layers)

    @property
    def members(self) -> tuple["Series", ...]:
        """The series this one paints, in paint order; itself if it is not a
        composite, so a caller can loop either way. A composite's layer may be
        a composite itself, and is taken apart into its own members here."""
        if not self.layers:
            return (self,)
        return tuple(member for name in self.layers for member in SERIES[name].members)

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
    def sheet_index(self) -> Path:
        """The reviewed index of a scanned series' sheets: each one's limits,
        projection and graticule (rectify_charts.py)."""
        return SCRIPTS / f"{self.name.replace('-', '_')}_sheets.json"

    @property
    def rectified_directory(self) -> Path:
        """Where rectify_charts.py writes the georeferenced rasters it makes
        from a scanned series' downloads."""
        return self.directory / "rectified"

    @property
    def stages(self) -> tuple[tuple[str, Path], ...]:
        """Each preparation stage as ``(script, output directory)``, in order.

        The first reads what was downloaded; each later one reads the previous
        one's output; the build tiles the last. A series with no stages is
        tiled straight from its download.
        """
        out = []
        if self.scan_suffix:
            out.append(("rectify_charts.py", self.rectified_directory))
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

    def pdf_entries(self) -> dict:
        """What render_pdfs.py draws each sheet from: read out of the PDFs for a
        series that carries its own georeferencing, and out of the reviewed
        registration for one that was registered against its GeoTIFFs."""
        if self.geopdf:
            import pdf_georef
            return pdf_georef.manifest(self)
        import json
        return json.loads(self.pdf_manifest.read_text(encoding="utf-8"))

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
        """The map-area manifest for the series: reviewed and committed, except
        for a scanned series, whose map areas are its graticules' and are
        written beside the rasters they were measured on. What is reviewed of
        a scanned series is its sheet index."""
        self._own("map-area manifest")
        if self.scan_suffix:
            return self.rectified_directory / "areas.json"
        return SCRIPTS / f"{self.name.replace('-', '_')}_areas.json"

    @property
    def pdf_manifest(self) -> Path:
        """The reviewed PDF-to-GeoTIFF registration (detect_pdf_windows.py)."""
        return SCRIPTS / f"{self.name.replace('-', '_')}_pdf.json"

    @property
    def tileset(self) -> Path:
        return REPO / f"tileset-{self.name}"

    @property
    def public_tileset(self) -> Path:
        """Where a build held to redistributable layers is written, so it never
        replaces the full tileset it was cut down from."""
        return REPO / f"tileset-{self.name}-public"

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
            name="ifr-high",
            title="FAA IFR Enroute High (CONUS)",
            index_url="https://aeronav.faa.gov/enroute/",
            files_path="",
            # H-01 to H-12 cover the lower 48 on twelve sheets, where the low
            # charts need 36. Alaska (AKH), Caribbean (CB) and the oceanic
            # charts are out of scope, as they are for ifr-low.
            zip_pattern=r"ENR_H\d\d\.zip",
            # One GeoTIFF per zip, and no split panels: unlike L-06, no high
            # sheet is published in halves.
            tif_pattern=r"ENR_H\d\d\.tif",
            # Same drawn frame as the low charts, so the same detector.
            detector="detect_ifr_areas.py",
            # The same twelve charts as vector PDFs, two per zip: DEHUS1 is
            # H-01 and H-02, through DEHUS11 for H-11 and H-12. Six zips.
            pdf_zip_pattern=r"DEHUS\d{1,2}\.zip",
            pdf_pattern=r"ENR_H\d\d\.pdf",
            # 4x, as for ifr-low, and for the same reason: it is what puts the
            # warp in the minifying regime at this series' max_zoom. Measured
            # off the downloaded sheets, all twelve are 24000x8000 at 92.60
            # m/px -- exactly half the low charts' 46.30, this being the
            # smaller-scale chart. So the 4x render is 23.15 m/px, native z13,
            # and a z12 tile (29.3 m/px on the ground here) minifies it 0.79x:
            # the identical ratio ifr-low gets from 4x at z13.
            pdf_scale=4,
            # Plain file-name order, unlike ifr-low. These sheets really do
            # overlap, so order decides what is seen rather than just tidying a
            # seam, and H-12 -- the one sheet drawn finer (78.71 m/px, rotated
            # 61 degrees) over the eastern seaboard -- sorts last and so lands
            # on top of the coarser sheets it covers. Still a placeholder for a
            # real overlap rule, as it is everywhere else.
            reverse_order=False,
            # Not healed, because these sheets overlap rather than abutting:
            # measured on the 2026-09-03 edition, east-west neighbours share
            # 15-31% of a sheet and H-10/H-12 share 49%. There is map under
            # each frame rule -- the next sheet's -- so the rule is cropped away
            # (detect_ifr_areas.py writes ``include`` from ``clean``) and the
            # neighbour shows through, rather than being painted over.
            heal_frames=False,
            # One level shallower than ifr-low, because the chart is drawn at
            # half the scale. z13 from these renders would magnify 1.58x, which
            # is the mistake ifr-low made when it was tiled at z13 from 2x.
            max_zoom=12,
            # Same artwork as the low charts: thin linework and small type on
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
        # -- beyond the FAA's own series: the layers of worldwide-vfr --------
        #
        # Researched in docs/worldwide-vfr-research. Each is free to download;
        # whether it may be republished is its ``licence``.
        Series(
            name="faa-caribbean",
            title="FAA Caribbean VFR Aeronautical Charts",
            index_url="https://aeronav.faa.gov/visual/",
            # A sibling of sectional-files/, which is why the sectionals never
            # picked these two sheets up.
            files_path="Caribbean/",
            zip_pattern=r"Caribbean_\d_VFR\.zip",
            tif_pattern=r"Caribbean \d VFR Chart\.tif",
            # A map in a paper collar, drawn by the same office as a sectional.
            detector="detect_sectional_areas.py",
            upsample_model="realcugan-up2x-denoise3x.pth",
            upsample_scale=2,
            # 1:1,000,000 at 84.67 m/px is native z10.8 at these latitudes and
            # z11.8 upsampled, so z11 minifies it 0.6x -- the regime the
            # sectionals are tiled in. z12 would magnify.
            max_zoom=11,
        ),
        Series(
            name="ofm",
            title="open flightmaps VFR charts (Europe)",
            publisher="open flightmaps association",
            licence=OFM_LICENCE,
            fetcher="ofm",
            index_url="https://snapshots.openflightmaps.org/",
            # Every region that publishes tile zips. Malta, South Africa and
            # Namibia publish PDFs only and are not here.
            regions=("ebbu", "ed", "efin", "ehaa", "ekdk", "epww", "esaa", "ldzo", "lf",
                     "lggg", "lhcc", "li", "ljla", "lkaa", "lovv", "lrbb", "lsas", "lzbb"),
            tif_pattern=r"[a-z]+\.tif",
            # Clipped to each region's rectangle by the publisher, with alpha
            # outside it; regions overlap and draw the same chart twice, so
            # paint order between them barely shows.
            whole_image=True,
            # Rendered from vector by the publisher at 512 px a z11 tile, which
            # is pixel for pixel a 256 px z12 tile. Nothing to upsample.
            max_zoom=12,
        ),
        Series(
            name="ch-icao",
            title="Aeronautical Chart ICAO Switzerland 1:500,000",
            publisher="Federal Office of Topography swisstopo",
            licence=SWISSTOPO_LICENCE,
            fetcher="urls",
            urls=("https://data.geo.admin.ch/ch.bazl.luftfahrtkarten-icao/luftfahrtkarten-icao/"
                  "luftfahrtkarten-icao_total_50_2056.tif",),
            tif_pattern=r"luftfahrtkarten-icao_total_50_2056\.tif",
            detector="detect_sectional_areas.py",
            upsample_model="realcugan-up2x-denoise3x.pth",
            upsample_scale=2,
            # 50 m/px at 47 N is native z11.06; upsampled it is z12.06.
            max_zoom=12,
        ),
        Series(
            name="dk-icao",
            title="ICAO Aeronautical Chart 1:500,000 Denmark",
            publisher="Naviair",
            licence=NAVIAIR_LICENCE,
            fetcher="links",
            index_url="https://aim.naviair.dk/charts/",
            # The digital issue, re-made before each AIRAC date with the hand
            # amendments applied; the "printed-version" is the paper edition as
            # first issued and is passed over.
            link_pattern=r".*/edition-\d+_(?P<date>\d{8})-icao-anc-1-500000-"
                         r"(?P<sheet>denmark)-geo-tiff\.tif",
            tif_pattern=r"denmark\.tif",
            detector="detect_sectional_areas.py",
            upsample_model="realcugan-up2x-denoise3x.pth",
            upsample_scale=2,
            # 31.75 m/px at 56 N is native z11.4; upsampled, z12.4.
            max_zoom=12,
        ),
        Series(
            name="dk-250",
            title="ICAO Aeronautical Charts 1:250,000 Copenhagen Area and Faroe Islands",
            publisher="Naviair",
            licence=NAVIAIR_LICENCE,
            fetcher="links",
            index_url="https://aim.naviair.dk/charts/",
            link_pattern=r".*/edition-\d+_(?P<date>\d{8})-icao-anc-1-250000-"
                         r"(?P<sheet>copenhagen-area|faroe-islands)-geo-tiff\.tif",
            tif_pattern=r"(copenhagen-area|faroe-islands)\.tif",
            detector="detect_sectional_areas.py",
            # 10.58 m/px is native z13 at Copenhagen and z12.8 in the Faroes,
            # so these reach z13 as downloaded.
            max_zoom=13,
        ),
        # -- charts that are georeferenced vector PDFs -----------------------
        #
        # Drawn from the vector geometry, as the FAA's IFR charts are, with the
        # registration read out of the PDF itself (pdf_georef.py). 300 dpi
        # twice over is 21 m a pixel at 1:500,000, which z12 minifies 0.7x.
        Series(
            name="ro-icao",
            title="Romania VFR Chart ICAO 1:500,000",
            publisher="ROMATSA",
            licence=ROMATSA_LICENCE,
            fetcher="links",
            index_url="https://www.aisro.ro/publications/hartivfrv02.php",
            link_pattern=r".*/(?P<date>\d{4}_\d{2}_\d{2})_(?P<sheet>LR[A-Z]{2})_ED[\d.]+\.pdf",
            tif_pattern=r"LR[A-Z]{2}\.tif",
            geopdf=True,
            pdf_scale=2,
            # The page's other viewport is the key map in the legend.
            pdf_viewports=("Layers",),
            # The viewport is the map's frame, and nothing is printed over it.
            whole_image=True,
            max_zoom=12,
        ),
        Series(
            name="tw-vfr",
            title="Taiwan VFR Chart 1:500,000",
            publisher="Civil Aviation Administration, MOTC",
            licence=TAIWAN_LICENCE,
            fetcher="links",
            index_url="https://www.eaipvfr.tw/",
            link_pattern=r".*/PDF/(?P<sheet>Taiwan_Eng_Map)_(?P<date>\d{8})_print\.pdf",
            tif_pattern=r"Taiwan_Eng_Map(-[a-z0-9-]+)?\.tif",
            geopdf=True,
            pdf_scale=2,
            # The island, and the four panels beside it: Kinmen, Matsu, the
            # north of the island enlarged, and the restricted VFR routes. Not
            # "world", which is the key map. Painted in name order, so the
            # island is on top of the panels that overlap it.
            pdf_viewports=("kinmen", "Matsu", "Taiwan"),
            whole_image=True,
            max_zoom=12,
        ),
        Series(
            name="es-vfr500",
            title="ENAIRE VFR500 (Spain 1:500,000)",
            publisher="ENAIRE",
            licence=ENAIRE_LICENCE,
            fetcher="links",
            index_url="https://aip.enaire.es/AIP/CartasInsigniaImpresas-es.html",
            # Sheets are re-issued one at a time, so the year differs between
            # them; each zip holds the sheet's TIFF and a world file.
            link_pattern=r".*/VFR500/(?P<year>\d{4})_(?P<sheet>[A-Z0-9_]+)\.zip",
            tif_pattern=r"[A-Z0-9_]+\.tif",
            # Each TIFF is the map half of its sheet alone, from edge to edge
            # and wholly opaque; the legend is on the PDF only.
            whole_image=True,
            upsample_model="realcugan-up2x-denoise3x.pth",
            upsample_scale=2,
            # 42.33 m/px, a sectional's pitch: native z11.5 at 40 N.
            max_zoom=12,
        ),
        Series(
            name="br-wac",
            title="Brazil World Aeronautical Charts 1:1,000,000",
            publisher="DECEA",
            licence=DECEA_LICENCE,
            fetcher="links",
            index_url="https://geoaisweb.decea.mil.br/",
            link_pattern=r".*src/geotiffs/(?P<sheet>WAC_\d+_[A-Z0-9_]+)\.tif",
            tif_pattern=r"WAC_\d+_[A-Z0-9_]+\.tif",
            # The usage policy names crawlers as a violation. 46 files, one at
            # a time, only when the server's copy is newer than ours.
            fetch_delay=5.0,
            # Published already cropped to the 6 x 4 degree neatline.
            whole_image=True,
            upsample_model="realcugan-up2x-denoise3x.pth",
            upsample_scale=2,
            # 0.000762 degrees a pixel is native z10.85; upsampled, z11.85.
            max_zoom=11,
        ),
        # -- the US military's world series, as a gap filler ------------------
        #
        # Decades old and never to be navigated by, but they cover the planet,
        # and most of it has no current chart that is free. Scans of library
        # copies, unregistered; see rectify_charts.py and graticule.py.
        Series(
            name="onc",
            title="Operational Navigation Charts 1:1,000,000 (historical)",
            publisher="U.S. Defense Mapping Agency",
            licence=US_MILITARY_LICENCE,
            historical=True,
            fetcher="links",
            index_url="https://maps.lib.utexas.edu/maps/onc/",
            link_pattern=r".*/maps/onc/txu-pclmaps-oclc-8322829_(?P<sheet>[a-z]_\d+[a-z]?)\.jpg",
            scan_suffix=".jpg",
            lossy_intermediates=True,
            tif_pattern=r"[a-z]_\d+[a-z]?\.tif",
            # The library asks little of its visitors and gets a great deal of
            # automated traffic. One file at a time, with a pause.
            fetch_delay=1.0,
            upsample_model="realcugan-up2x-denoise3x.pth",
            upsample_scale=2,
            # Scanned at about 160 dpi: 158 m/px, native z10 at the equator and
            # z9.3 at 50 degrees. Upsampled that is z11 and z10.3, so z10 is
            # where every sheet is still being minified.
            max_zoom=10,
        ),
        Series(
            name="tpc",
            title="Tactical Pilotage Charts 1:500,000 (historical)",
            publisher="U.S. Defense Mapping Agency",
            licence=US_MILITARY_LICENCE,
            historical=True,
            fetcher="links",
            index_url="https://maps.lib.utexas.edu/maps/tpc/",
            link_pattern=r".*/maps/tpc/txu-pclmaps-oclc-22834566_(?P<sheet>[a-z]-\d+-?[a-z]r?)\.jpg",
            scan_suffix=".jpg",
            lossy_intermediates=True,
            tif_pattern=r"[a-z]-\d+-?[a-z]r?\.tif",
            fetch_delay=1.0,
            upsample_model="realcugan-up2x-denoise3x.pth",
            upsample_scale=2,
            # About 80 m/px: native z10.9 at the equator, z10.3 at 50 degrees;
            # upsampled, a level more.
            max_zoom=11,
        ),
        Series(
            name="worldwide-vfr",
            title="World-wide VFR charts",
            publisher="various",
            # Bottom to top. Coarse under fine; a community chart under the
            # official one where both are free (the user's call); and the FAA's
            # own sectionals and terminal area charts over everything they
            # reach, since they are what the rest is laid around.
            layers=("onc", "tpc", "br-wac", "faa-caribbean", "ofm", "ro-icao", "tw-vfr",
                    "es-vfr500", "dk-icao", "ch-icao", "dk-250", "sectionals", "tac"),
            stepped=True,
            max_zoom=13,
        ),
    )
}


def series(name: str) -> Series:
    try:
        return SERIES[name]
    except KeyError:
        raise SystemExit(f"unknown series {name!r}; choose from {', '.join(SERIES)}") from None
