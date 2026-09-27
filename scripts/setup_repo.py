#!/usr/bin/env python
"""Set up a fresh clone: create the venv, install everything, make source/.

    python scripts/setup_repo.py [--recreate]

Run it with the Python you want the venv built on (3.14 is what this repo is
developed with). It uses only the standard library, so it works before anything
is installed, on Windows, Linux or macOS.

Steps, each skipped when already done:

  1. create .venv (``--recreate`` deletes and rebuilds it)
  2. upgrade pip, then install requirements-dev.txt -- which pulls in
     requirements.txt and its extra indexes: GDAL from the geospatial-wheels
     index, CPU PyTorch from the PyTorch index -- and the packages in this repo
     as an editable install
  3. check the key imports actually load
  4. create source/, where every download lands
  5. point git at the tracked hooks in .githooks/ and prune on fetch -- git
     config is per clone and cannot be committed, so a clone has to be told

It downloads no charts; the build_*.py wrappers do that. It prints them at the end.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import venv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import REPO, SOURCE, venv_python  # noqa: E402

MIN_PYTHON = (3, 10)
VENV = REPO / ".venv"
CHECK = (
    "from osgeo import gdal; import rasterio, numpy, torch, spandrel, pypdfium2, "
    "cesiumtiles, geotransfer; "
    "print('  gdal', gdal.__version__, '| rasterio', rasterio.__version__, "
    "'| torch', torch.__version__, "
    "'| pypdfium2', pypdfium2.version.PYPDFIUM_INFO.version)"
)


def step(title: str) -> None:
    print(f"\n== {title}", flush=True)


def call(*command) -> None:
    code = subprocess.run([str(c) for c in command], cwd=REPO).returncode
    if code != 0:
        raise SystemExit(f"failed (exit {code}): {' '.join(str(c) for c in command)}")


#: Local git settings a clone needs. ``.githooks/post-merge`` deletes a merged
#: PR's local branch, and only sees its remote as gone once fetches prune.
GIT_CONFIG = {"core.hooksPath": ".githooks", "fetch.prune": "true"}


def configure_git(repo: Path = REPO) -> bool:
    """Apply GIT_CONFIG to the clone at *repo*; False where there is none."""
    if not (repo / ".git").exists() or shutil.which("git") is None:
        return False
    for key, value in GIT_CONFIG.items():
        code = subprocess.run(["git", "config", "--local", key, value], cwd=repo).returncode
        if code != 0:
            raise SystemExit(f"failed (exit {code}): git config --local {key} {value}")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--recreate", action="store_true", help="delete and rebuild .venv")
    args = ap.parse_args(argv)

    if sys.version_info < MIN_PYTHON:
        raise SystemExit(f"Python {'.'.join(map(str, MIN_PYTHON))}+ required; this is {sys.version.split()[0]}")

    step("virtual environment")
    if args.recreate and VENV.exists():
        print(f"  removing {VENV}")
        shutil.rmtree(VENV)
    python = venv_python()
    if python.exists():
        print(f"  {VENV} already exists")
    else:
        print(f"  creating {VENV} with Python {sys.version.split()[0]}")
        venv.EnvBuilder(with_pip=True).create(VENV)
        python = venv_python()

    step("dependencies")
    call(python, "-m", "pip", "install", "--upgrade", "pip")
    call(python, "-m", "pip", "install", "-r", REPO / "requirements-dev.txt")
    call(python, "-m", "pip", "install", "-e", REPO)

    step("checking imports")
    call(python, "-c", CHECK)

    step("source directory")
    SOURCE.mkdir(exist_ok=True)
    print(f"  {SOURCE}")

    step("git settings")
    if configure_git():
        for key, value in GIT_CONFIG.items():
            print(f"  {key} = {value}")
    else:
        print("  not a git clone, or git is not installed; skipped")

    shown = python.relative_to(REPO).as_posix()
    print(f"""
Setup complete. Next:

  {shown} scripts/build_sectionals.py      # VFR sectionals      ~80 min, 48 GB of intermediates
  {shown} scripts/build_sectionals_tac.py  # the same + the TACs  ~60 min more
  {shown} scripts/build_ifr_low.py         # IFR low enroute      ~130 min
  {shown} scripts/build_ifr_high.py        # IFR high enroute     ~50 min
  {shown} scripts/build_wall_planning.py   # wall planning chart; needs files in source/wall-planning/
  {shown} -m cesiumtiles.serve .           # tile tester at http://127.0.0.1:8000/
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
