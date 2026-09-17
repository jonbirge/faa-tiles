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
    # Paint order where sheets overlap. Sheets are drawn in file-name order and
    # a later sheet lands on top; reverse puts the earliest name on top instead.
    reverse_order: bool = False
    # Sheets meet edge to edge at a drawn frame rule rather than overlapping, so
    # the rule is painted over (heal_frames.py) and the build tiles the healed
    # copies. Needs a manifest with a "frame" per sheet (detect_ifr_areas.py).
    heal_frames: bool = False

    @property
    def directory(self) -> Path:
        """Where the GeoTIFFs are downloaded to."""
        return SOURCE / self.name

    @property
    def healed_directory(self) -> Path:
        """Where heal_frames.py writes frame-healed copies of the sheets."""
        return self.directory / "healed"

    @property
    def build_directory(self) -> Path:
        """The GeoTIFFs a build tiles: healed copies if the series heals frames."""
        return self.healed_directory if self.heal_frames else self.directory

    @property
    def manifest(self) -> Path:
        """The reviewed map-area manifest for the series."""
        return SCRIPTS / f"{self.name.replace('-', '_')}_areas.json"

    @property
    def tileset(self) -> Path:
        return REPO / f"tileset-{self.name}"

    def wants_zip(self, name: str) -> bool:
        return re.fullmatch(self.zip_pattern, name, re.IGNORECASE) is not None

    def wants_tif(self, name: str) -> bool:
        return (re.fullmatch(self.tif_pattern, name, re.IGNORECASE) is not None
                and name not in self.exclude)


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
            # The user's call, after seeing overlap artefacts with name order.
            reverse_order=True,
            # The user's call, after black seams between every pair of charts.
            heal_frames=True,
        ),
    )
}


def series(name: str) -> Series:
    try:
        return SERIES[name]
    except KeyError:
        raise SystemExit(f"unknown series {name!r}; choose from {', '.join(SERIES)}") from None
