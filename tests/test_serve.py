"""The preview server: MIME types, CORS, and clean shutdown."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

import pytest

from cesiumtiles.serve import list_tilesets, serve_tileset


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


# -- the tileset menu ----------------------------------------------------


def _write_tileset(directory, name=None):
    directory.mkdir(parents=True)
    meta = {"minzoom": 0, "maxzoom": 3, "tiles": 1}
    if name:
        meta["name"] = name
    (directory / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")


def test_lists_tilesets_one_level_deep(tmp_path):
    _write_tileset(tmp_path / "b_second", "Second")
    _write_tileset(tmp_path / "a_first", "First")
    _write_tileset(tmp_path / "group" / "nested")          # two deep: not listed
    (tmp_path / "not_a_tileset").mkdir()
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "metadata.json").write_text("{not json", encoding="utf-8")

    found = list_tilesets(tmp_path)
    assert [spec for spec, _ in found] == ["./a_first", "./b_second", "./broken"]
    assert found[0][1]["name"] == "First"
    assert found[2][1] is None   # listed, so a half-written tileset is visible


def test_root_that_is_itself_a_tileset_comes_first(tmp_path):
    _write_tileset(tmp_path / "root")
    _write_tileset(tmp_path / "root" / "child")
    assert [spec for spec, _ in list_tilesets(tmp_path / "root")] == [".", "./child"]


def test_serves_the_tileset_menu(tmp_path):
    _write_tileset(tmp_path / "charts", "Charts")
    _write_tileset(tmp_path / "unnamed")
    port = _free_port()
    srv = serve_tileset(tmp_path, port=port, background=True)
    try:
        r = _get(f"http://127.0.0.1:{port}/tilesets.json")
        assert r.headers["Content-Type"] == "application/json"
        assert r.headers["Cache-Control"] == "no-cache"
        listing = json.loads(r.read())
        assert listing == [
            {"path": "./charts", "name": "Charts", "tiles": 1, "valid": True},
            {"path": "./unnamed", "name": "unnamed", "tiles": 1, "valid": True},
        ]
        # Scanned per request: a tileset built while serving shows up.
        _write_tileset(tmp_path / "later", "Later")
        again = json.loads(_get(f"http://127.0.0.1:{port}/tilesets.json").read())
        assert [entry["path"] for entry in again] == ["./charts", "./later", "./unnamed"]
    finally:
        srv.shutdown()
        srv.server_close()
