"""Write tilesets.json beside index.html, listing the tilesets in this folder.

Run on the server after adding or removing a tileset:

    python3 update_tilesets.py

index.html reads tilesets.json to find its tilesets, because a web page cannot
list a directory and most servers show index.html rather than a listing once it
exists. A tileset is an immediate subdirectory holding a metadata.json. Only the
standard library is used, so any Python 3 on the server will do.
"""

import json
import sys
from pathlib import Path


def scan(root: Path) -> list[dict]:
    """Every immediate subdirectory of ``root`` holding a readable metadata.json,
    in name order, as ``{"path", "name"}``."""
    found = []
    for directory in sorted(p for p in root.iterdir() if p.is_dir()):
        meta = directory / "metadata.json"
        if not meta.is_file():
            continue
        try:
            name = json.loads(meta.read_text(encoding="utf-8")).get("name")
        except ValueError:
            continue
        found.append({"path": "./" + directory.name, "name": name or directory.name})
    return found


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    listing = scan(root)
    (root / "tilesets.json").write_text(json.dumps(listing, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    for item in listing:
        print(f"{item['path']}: {item['name']}")
    print(f"{len(listing)} tileset(s) written to {root / 'tilesets.json'}")


if __name__ == "__main__":
    main()
