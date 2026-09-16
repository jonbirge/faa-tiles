"""The preview server: MIME types, CORS, and clean shutdown."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

import pytest

from cesiumtiles.serve import serve_tileset


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def tileset(tmp_path):
    """A minimal directory shaped like a real tileset."""
    root = tmp_path / "tileset"
    (root / "tiles" / "3" / "1").mkdir(parents=True)
    (root / "tiles" / "3" / "1" / "2.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
    (root / "index.html").write_text("<!DOCTYPE html><title>t</title>", encoding="utf-8")
    (root / "metadata.json").write_text(json.dumps({"minzoom": 0, "maxzoom": 3}), encoding="utf-8")
    return root


@pytest.fixture
def server(tileset):
    port = _free_port()
    srv = serve_tileset(tileset, port=port, background=True)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        srv.shutdown()
        srv.server_close()


def _get(url):
    return urllib.request.urlopen(url, timeout=10)


def test_serves_the_viewer(server):
    r = _get(server + "/")
    assert r.status == 200
    assert r.headers["Content-Type"].startswith("text/html")


def test_tiles_get_the_right_mime_type(server):
    r = _get(server + "/tiles/3/1/2.webp")
    assert r.status == 200
    assert r.headers["Content-Type"] == "image/webp"


def test_metadata_is_json(server):
    r = _get(server + "/metadata.json")
    assert r.headers["Content-Type"] == "application/json"
    assert json.loads(r.read())["maxzoom"] == 3


def test_cors_header_is_present(server):
    # Without this, a Cesium app on another origin cannot read the tiles.
    for path in ["/", "/metadata.json", "/tiles/3/1/2.webp"]:
        assert _get(server + path).headers["Access-Control-Allow-Origin"] == "*"


def test_mutable_files_are_not_cached(server):
    assert _get(server + "/metadata.json").headers["Cache-Control"] == "no-cache"
    assert _get(server + "/").headers["Cache-Control"] == "no-cache"
    # Tiles are immutable per build, so they may be cached.
    assert _get(server + "/tiles/3/1/2.webp").headers["Cache-Control"] is None


def test_missing_tile_is_a_plain_404(server):
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        _get(server + "/tiles/3/9/9.webp")
    assert excinfo.value.code == 404


def test_cors_can_be_disabled(tileset):
    port = _free_port()
    srv = serve_tileset(tileset, port=port, cors=False, background=True)
    try:
        assert _get(f"http://127.0.0.1:{port}/").headers["Access-Control-Allow-Origin"] is None
    finally:
        srv.shutdown()
        srv.server_close()


def test_rejects_a_missing_directory(tmp_path):
    with pytest.raises(NotADirectoryError):
        serve_tileset(tmp_path / "absent", port=_free_port(), background=True)


def test_reports_a_port_clash_helpfully(tileset):
    port = _free_port()
    first = serve_tileset(tileset, port=port, background=True)
    try:
        with pytest.raises(OSError, match="--port"):
            serve_tileset(tileset, port=port, background=True)
    finally:
        first.shutdown()
        first.server_close()
