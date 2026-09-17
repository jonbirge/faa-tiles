"""Where things live in a checkout. Standard library only.

Everything downloaded or otherwise not authored here -- FAA chart GeoTIFFs,
model weights, third-party checkouts, and the intermediates derived from them
-- lives under ``source/``, so deleting that one directory reclaims all of it.
Tilesets (``tileset-*``) stay at the top level, where the tile tester finds
them. Both are gitignored.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"

SOURCE = REPO / "source"
MODELS = SOURCE / "models"            # super-resolution weights
VENDOR = SOURCE / "vendor"            # third-party checkouts (nunif, for waifu2x)
WALL_PLANNING = SOURCE / "wall-planning"


def venv_python() -> Path:
    """The project venv's interpreter, on Windows or POSIX."""
    windows = REPO / ".venv" / "Scripts" / "python.exe"
    return windows if windows.exists() else REPO / ".venv" / "bin" / "python"
