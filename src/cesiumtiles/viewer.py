"""Emit a self-contained Cesium viewer for a generated tileset.

``gdal raster tile`` can write Leaflet, OpenLayers, MapML and STAC front ends,
but not a Cesium one, so we write our own. The page loads Cesium from the CDN
and reads ``metadata.json`` at runtime, which means re-tiling with different
bounds or zooms needs no change to the HTML.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = ["write_viewer", "render_viewer"]

CESIUM_VERSION = "1.135"

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/cesium@__CESIUM__/Build/Cesium/Widgets/widgets.css">
<script src="https://cdn.jsdelivr.net/npm/cesium@__CESIUM__/Build/Cesium/Cesium.js"></script>
<style>
  html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #000; }
  #cesiumContainer { width: 100%; height: 100%; }
  #panel {
    position: absolute; top: 10px; left: 10px; z-index: 10;
    font: 12px/1.5 ui-monospace, "Cascadia Mono", Consolas, monospace;
    color: #e8e8e8; background: rgba(20, 22, 26, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 6px;
    padding: 10px 12px; max-width: 320px; backdrop-filter: blur(6px);
  }
  #panel h1 { margin: 0 0 6px; font-size: 13px; letter-spacing: 0.02em; }
  #panel dl { margin: 0; display: grid; grid-template-columns: auto 1fr; gap: 1px 10px; }
  #panel dt { color: #8d95a0; }
  #panel dd { margin: 0; }
  #panel button {
    margin-top: 9px; width: 100%; cursor: pointer; color: #e8e8e8;
    background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px; padding: 5px; font: inherit;
  }
  #panel button:hover { background: rgba(255, 255, 255, 0.18); }
  #error { color: #ff8b8b; margin-top: 8px; display: none; }
</style>
</head>
<body>
<div id="cesiumContainer"></div>
<div id="panel">
  <h1 id="title">loading</h1>
  <dl id="facts"></dl>
  <button id="home">Fly to chart</button>
  <div id="error"></div>
</div>
<script>
const METADATA = __METADATA__;

function facts(meta) {
  const [w, s, e, n] = meta.bounds;
  return [
    ["scheme", meta.scheme + " / " + meta.crs],
    ["format", meta.format + " (" + meta.convention + ")"],
    ["zooms", meta.minzoom + "-" + meta.maxzoom],
    ["tiles", meta.tiles.toLocaleString()],
    ["size", (meta.bytes / 1e6).toFixed(1) + " MB"],
    ["west", w.toFixed(4)], ["south", s.toFixed(4)],
    ["east", e.toFixed(4)], ["north", n.toFixed(4)],
  ];
}

function buildPanel(meta) {
  document.getElementById("title").textContent = meta.name;
  const dl = document.getElementById("facts");
  for (const [k, v] of facts(meta)) {
    const dt = document.createElement("dt"); dt.textContent = k;
    const dd = document.createElement("dd"); dd.textContent = v;
    dl.append(dt, dd);
  }
}

function start(meta) {
  buildPanel(meta);
  const [w, s, e, n] = meta.bounds;
  const rectangle = Cesium.Rectangle.fromDegrees(w, s, e, n);

  const provider = new Cesium.UrlTemplateImageryProvider({
    url: meta.url_template,
    tilingScheme: meta.scheme === "geographic"
      ? new Cesium.GeographicTilingScheme()
      : new Cesium.WebMercatorTilingScheme(),
    rectangle: rectangle,
    minimumLevel: meta.minzoom,
    maximumLevel: meta.maxzoom,
    tileWidth: meta.tilesize,
    tileHeight: meta.tilesize,
    hasAlphaChannel: meta.format !== "jpeg",
    credit: new Cesium.Credit(meta.name, false),
  });

  // No Ion token is used: our own tiles are the base layer, and the default
  // ellipsoid terrain needs no network access.
  const viewer = new Cesium.Viewer("cesiumContainer", {
    baseLayer: new Cesium.ImageryLayer(provider),
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    navigationHelpButton: false,
    sceneModePicker: true,
    timeline: false,
    animation: false,
    infoBox: false,
    selectionIndicator: false,
    fullscreenButton: true,
  });
  viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#10131a");

  const flyHome = () => viewer.camera.flyTo({ destination: rectangle, duration: 1.5 });
  document.getElementById("home").addEventListener("click", flyHome);
  viewer.camera.setView({ destination: rectangle });

  // Exposed deliberately: makes the page inspectable from the dev console.
  window.viewer = viewer;
  window.tilesetMetadata = meta;
  return viewer;
}

function fail(message) {
  const box = document.getElementById("error");
  box.style.display = "block";
  box.textContent = message;
}

// Prefer the metadata.json on disk so the page stays correct after a re-tile,
// but fall back to the copy baked in at generation time (e.g. file:// use).
fetch("metadata.json")
  .then((r) => (r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status))))
  .catch(() => METADATA)
  .then(start)
  .catch((err) => fail("Could not start the viewer: " + err.message));
</script>
</body>
</html>
"""


def render_viewer(metadata: dict) -> str:
    """Return the viewer HTML for ``metadata`` (as written to metadata.json)."""
    return (
        _TEMPLATE.replace("__CESIUM__", CESIUM_VERSION)
        .replace("__TITLE__", str(metadata.get("name", "Tileset")))
        .replace("__METADATA__", json.dumps(metadata, indent=2))
    )


def write_viewer(output_dir: str | Path, metadata: dict) -> Path:
    """Write ``index.html`` next to the tiles and return its path."""
    path = Path(output_dir) / "index.html"
    path.write_text(render_viewer(metadata), encoding="utf-8")
    return path
