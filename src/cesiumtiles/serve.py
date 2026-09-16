"""A small static server for previewing a generated tileset.

``python -m http.server`` almost works, but it sends no CORS headers, so the
moment a Cesium app on another origin (or another port) tries to read the tiles
the browser blocks them. It also caches aggressively enough to hide a re-tile.
This server fixes both and knows the tile MIME types explicitly.

It is a development convenience, not a production server: it binds to localhost
by default and serves a single directory.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import socket
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path

from cesiumtiles.viewer import render_viewer

__all__ = ["TileRequestHandler", "discover_tileset", "list_tilesets", "serve_tileset", "main"]

DEFAULT_PORT = 8000


def list_tilesets(root: Path) -> list[tuple[str, dict | None]]:
    """Every tileset at ``root`` or one directory below it, as ``(spec, metadata)``.

    A tileset is a directory holding a ``metadata.json``. The scan is one level
    deep, not recursive: ``root`` itself, then its immediate subdirectories in
    name order. Specs are relative to the web root, which is what the page
    resolves against. Metadata that fails to parse is reported as ``None``
    rather than hiding the directory, so a half-written tileset still shows up.
    """
    found = []
    candidates = [(".", root)] + [
        ("./" + child.name, child) for child in sorted(p for p in root.iterdir() if p.is_dir())
    ]
    for spec, directory in candidates:
        meta = directory / "metadata.json"
        if not meta.is_file():
            continue
        try:
            found.append((spec, json.loads(meta.read_text(encoding="utf-8"))))
        except ValueError:
            found.append((spec, None))
    return found


def discover_tileset(root: Path) -> tuple[str, dict | None]:
    """Find what the tile tester should open with, under ``root``: the first
    tileset ``list_tilesets`` finds, or ``("", None)`` if there is none."""
    found = list_tilesets(root)
    return found[0] if found else ("", None)


class TileRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Serves tiles with correct content types and permissive CORS.

    The tile tester is served from memory at ``/``, so a tileset on disk stays
    pure data -- tiles and metadata, no viewer mixed in with them.
    """

    # Rendered per request, not cached, so editing viewer.html and reloading
    # the browser is enough to see the change.
    viewer_source = ""
    viewer_metadata = None
    root: Path | None = None

    # Explicit, so we do not depend on the machine's registry/mime.types.
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".webp": "image/webp",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".json": "application/json",
        ".html": "text/html",
        ".js": "text/javascript",
        ".css": "text/css",
        "": "application/octet-stream",
    }

    cors = True

    def end_headers(self):
        if self.cors:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        # Tiles are immutable per build, but metadata and the viewer are not;
        # re-tiling during a session should not be masked by a stale cache.
        if self.path.rstrip("/").endswith((".json", ".html")) or self.path.endswith("/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_OPTIONS(self):  # noqa: N802 - name fixed by BaseHTTPRequestHandler
        self.send_response(204)
        self.end_headers()

    def do_GET(self):  # noqa: N802 - name fixed by BaseHTTPRequestHandler
        if self.path.split("?")[0] == "/tilesets.json" and self.root is not None:
            # Scanned per request, so a tileset built while the server runs
            # appears in the tester's menu on the next page load.
            listing = [
                {
                    "path": spec,
                    "name": (meta or {}).get("name") or (Path(spec).name if spec != "." else self.root.name),
                    "tiles": (meta or {}).get("tiles"),
                    "valid": meta is not None,
                }
                for spec, meta in list_tilesets(self.root)
            ]
            body = json.dumps(listing).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.split("?")[0] in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            body = render_viewer(self.viewer_metadata, self.viewer_source).encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        # One line per request is too noisy for thousands of tiles; report only
        # failures, which is what actually needs attention during a preview.
        status = args[1] if len(args) > 1 else ""
        if str(status).startswith(("4", "5")):
            sys.stderr.write(f"  {self.address_string()} {fmt % args}\n")


class _Server(socketserver.ThreadingTCPServer):
    # SO_REUSEADDR means opposite things on the two platforms: on POSIX it just
    # skips the TIME_WAIT wait, but on Windows it lets a second server bind a
    # port that is already in use, so requests would split between them at
    # random instead of failing loudly. Only enable it where it is safe.
    allow_reuse_address = sys.platform != "win32"
    daemon_threads = True


def serve_tileset(
    directory: str | Path = ".",
    *,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    cors: bool = True,
    background: bool = False,
) -> _Server:
    """Serve ``directory`` over HTTP.

    Returns the server. With ``background=True`` it is already running on its
    own thread and the caller is responsible for ``shutdown()``; otherwise this
    blocks until interrupted.
    """
    root = Path(directory).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")

    spec, metadata = discover_tileset(root)
    if not spec:
        print(f"warning: no metadata.json in {root} or its subdirectories; "
              "the tester will start empty", file=sys.stderr)

    handler_class = type("_Configured", (TileRequestHandler,), {
        "cors": cors,
        "viewer_source": spec,
        "viewer_metadata": metadata,
        "root": root,
    })
    handler = functools.partial(handler_class, directory=str(root))

    try:
        server = _Server((host, port), handler)
    except OSError as exc:
        raise OSError(
            f"cannot bind {host}:{port} ({exc.strerror or exc}). "
            "Another server may already be running; try --port."
        ) from exc

    shown = host if host != "0.0.0.0" else socket.gethostbyname(socket.gethostname())
    print(f"serving {root}\n  http://{shown}:{port}/   (Ctrl-C to stop)")

    if background:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cesiumtiles-serve",
        description="Serve tilesets for local preview and host the tile tester at /.",
    )
    parser.add_argument("directory", nargs="?", default=".",
                        help="directory to serve: a parent holding tilesets, or a "
                             "single tileset (default: the working directory)")
    parser.add_argument("-p", "--port", type=int, default=DEFAULT_PORT,
                        help="port to listen on (default: %(default)s)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="address to bind; use 0.0.0.0 to expose on the LAN "
                             "(default: %(default)s)")
    parser.add_argument("--no-cors", dest="cors", action="store_false",
                        help="do not send Access-Control-Allow-Origin headers")
    parser.add_argument("--open", action="store_true", help="open the viewer in a browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.open:
            server = serve_tileset(args.directory, host=args.host, port=args.port,
                                   cors=args.cors, background=True)
            webbrowser.open(f"http://{args.host}:{args.port}/")
            try:
                threading.Event().wait()
            except KeyboardInterrupt:
                print("\nstopped")
            finally:
                server.shutdown()
                server.server_close()
        else:
            serve_tileset(args.directory, host=args.host, port=args.port, cors=args.cors)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
