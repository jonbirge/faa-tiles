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
import socket
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path

__all__ = ["TileRequestHandler", "serve_tileset", "main"]

DEFAULT_PORT = 8000


class TileRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Serves tiles with correct content types and permissive CORS."""

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
    directory: str | Path = "tileset",
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
    if not (root / "index.html").is_file():
        print(f"warning: no index.html in {root}; is this a tileset?", file=sys.stderr)

    handler_class = type("_Configured", (TileRequestHandler,), {"cors": cors})
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
        description="Serve a generated tileset for local preview, with CORS enabled.",
    )
    parser.add_argument("directory", nargs="?", default="tileset",
                        help="tileset directory to serve (default: %(default)s)")
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
