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
    color: #e8e8e8; background: rgba(20, 22, 26, 0.84);
    border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 6px;
    padding: 10px 12px; width: 300px; backdrop-filter: blur(6px);
    max-height: calc(100vh - 40px); overflow-y: auto;
  }
  #panel h1 { margin: 0 0 6px; font-size: 13px; letter-spacing: 0.02em; }
  #panel h2 {
    margin: 12px 0 5px; font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.09em; color: #7f8794;
    border-top: 1px solid rgba(255, 255, 255, 0.12); padding-top: 8px;
  }
  #panel dl { margin: 0; display: grid; grid-template-columns: auto 1fr; gap: 1px 10px; }
  #panel dt { color: #8d95a0; }
  #panel dd { margin: 0; overflow-wrap: anywhere; }
  #panel button {
    margin-top: 8px; width: 100%; cursor: pointer; color: #e8e8e8;
    background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px; padding: 5px; font: inherit;
  }
  #panel button:hover { background: rgba(255, 255, 255, 0.18); }
  #panel button:active { background: rgba(255, 255, 255, 0.26); }
  .num { font-variant-numeric: tabular-nums; }
  #error { color: #ff8b8b; margin-top: 8px; display: none; }
</style>
</head>
<body>
<div id="cesiumContainer"></div>
<div id="panel">
  <h1 id="title">loading</h1>
  <dl id="facts"></dl>
  <button id="home">Fly to chart</button>

  <h2>On screen</h2>
  <dl id="visible"></dl>

  <h2>Downloaded</h2>
  <dl id="traffic"></dl>
  <button id="reset">Reset counters &amp; cache</button>

  <div id="error"></div>
</div>
<script>
const METADATA = __METADATA__;

// The imagery rectangle must be the *unsnapped* data extent, never the
// tile-snapped `bounds`. Cesium's _createTileImagerySkeletons intersects an
// imagery tile against this rectangle, and when an edge coincides exactly with
// a tile boundary that intersection comes back undefined, which then blows up
// inside rectangleToNativeRectangle ("can't access property west"). Measured:
// tile-snapped edges produce ~60 such calls while panning the chart border,
// the data extent produces none.
function extentOf(meta) {
  return meta.data_bounds || meta.bounds;
}

function bytes(n) {
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / 1048576).toFixed(2) + " MB";
}

function rows(dl, pairs) {
  dl.textContent = "";
  for (const [k, v] of pairs) {
    const dt = document.createElement("dt"); dt.textContent = k;
    const dd = document.createElement("dd"); dd.textContent = v; dd.className = "num";
    dl.append(dt, dd);
  }
}

function facts(meta) {
  const [w, s, e, n] = extentOf(meta);
  return [
    ["scheme", meta.scheme + " / " + meta.crs],
    ["format", meta.format + " (" + meta.convention + ")"],
    ["zooms", meta.minzoom + "-" + meta.maxzoom],
    ["tiles", meta.tiles.toLocaleString()],
    ["size", (meta.bytes / 1e6).toFixed(1) + " MB"],
    ["extent", w.toFixed(3) + ", " + s.toFixed(3)],
    ["", e.toFixed(3) + ", " + n.toFixed(3)],
  ];
}

// -- download accounting ------------------------------------------------
// Resource Timing gives the real transfer size per tile. The tiles are
// same-origin, so transferSize/encodedBodySize are populated rather than
// zeroed for cross-origin opacity.
//
// Telling a real download from a cache hit needs care, because browsers do not
// agree on how to report one. A cache hit can arrive as transferSize 0, or as a
// fixed ~300-byte header placeholder alongside a full encodedBodySize and a 200
// status. The reliable, browser-independent test is whether the body could have
// crossed the wire at all: if transferSize is smaller than encodedBodySize, it
// did not. That covers 304 revalidations and plain cache hits alike.
//
// Cesium also keeps its own in-memory imagery cache, and a tile it serves from
// there makes no request at all, so it appears in none of these counters.
function makeTracker(meta) {
  const m = meta.url_template.match(/^(.*)\\{z\\}\\/\\{x\\}\\/\\{y\\}(\\..+)$/);
  const esc = (s) => s.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&");
  const re = new RegExp(
    esc(m ? m[1] : "tiles/") + "(\\\\d+)\\\\/(\\\\d+)\\\\/(\\\\d+)" + esc(m ? m[2] : ".webp") + "(?:\\\\?|$)"
  );

  const state = {
    downloaded: 0, cached: 0,
    network: 0, payload: 0, imagery: 0,
    last: "-", byLevel: new Map(), since: Date.now(),
  };

  function consume(entry) {
    const hit = re.exec(entry.name);
    if (!hit) return;
    const [, z, x, y] = hit;
    state.last = z + "/" + x + "/" + y;

    const body = entry.encodedBodySize || 0;
    const wire = entry.transferSize || 0;
    state.imagery += entry.decodedBodySize || 0;
    state.network += wire;                 // everything that touched the network

    if (body > 0 && wire < body) {
      state.cached++;                      // body came from cache, not the wire
    } else {
      state.downloaded++;
      state.payload += body;
    }
    state.byLevel.set(+z, (state.byLevel.get(+z) || 0) + 1);
  }

  performance.getEntriesByType("resource").forEach(consume);
  try {
    new PerformanceObserver((list) => list.getEntries().forEach(consume))
      .observe({ type: "resource", buffered: false });
  } catch (err) {
    /* Resource Timing unavailable; the panel will just show zeros. */
  }

  state.reset = function () {
    state.downloaded = 0; state.cached = 0;
    state.network = 0; state.payload = 0; state.imagery = 0;
    state.last = "-"; state.byLevel.clear(); state.since = Date.now();
    try { performance.clearResourceTimings(); } catch (err) { /* not fatal */ }
  };
  return state;
}

// -- what the globe is actually drawing ---------------------------------
// Walks Cesium's render list. These are private fields, so everything is
// guarded: a Cesium upgrade that renames them should degrade to "unavailable"
// rather than break the page.
function visibleTiles(viewer) {
  try {
    const rendered = viewer.scene.globe._surface._tilesToRender;
    if (!rendered) return null;
    const seen = new Set();
    const byLevel = new Map();
    let loading = 0;
    for (const terrainTile of rendered) {
      const imagery = terrainTile.data && terrainTile.data.imagery;
      if (!imagery) continue;
      for (const slot of imagery) {
        const tile = slot.readyImagery || slot.loadingImagery;
        if (!tile || tile.level === undefined) continue;
        if (!slot.readyImagery) loading++;
        const key = tile.level + "/" + tile.x + "/" + tile.y;
        if (seen.has(key)) continue;
        seen.add(key);
        let box = byLevel.get(tile.level);
        if (!box) byLevel.set(tile.level, (box = { n: 0, x0: tile.x, x1: tile.x, y0: tile.y, y1: tile.y }));
        box.n++;
        box.x0 = Math.min(box.x0, tile.x); box.x1 = Math.max(box.x1, tile.x);
        box.y0 = Math.min(box.y0, tile.y); box.y1 = Math.max(box.y1, tile.y);
      }
    }
    return { total: seen.size, loading, byLevel, terrain: rendered.length };
  } catch (err) {
    return null;
  }
}

function start(meta) {
  document.getElementById("title").textContent = meta.name;
  rows(document.getElementById("facts"), facts(meta));

  const [w, s, e, n] = extentOf(meta);
  const rectangle = Cesium.Rectangle.fromDegrees(w, s, e, n);

  // A cache-busting token is what makes "reset" meaningful. Clearing the
  // browser's HTTP cache is not possible from script, so instead the layer is
  // rebuilt against a fresh query string: new URLs miss both Cesium's in-memory
  // tile cache and the browser's, and the counters then measure a genuine cold
  // load rather than replaying what is already local.
  let bust = 0;
  function newLayer() {
    return new Cesium.ImageryLayer(new Cesium.UrlTemplateImageryProvider({
      url: meta.url_template + (bust ? "?r=" + bust : ""),
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
    }));
  }

  // No Ion token is used: our own tiles are the base layer, and the default
  // ellipsoid terrain needs no network access.
  const viewer = new Cesium.Viewer("cesiumContainer", {
    baseLayer: newLayer(),
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

  const tracker = makeTracker(meta);
  document.getElementById("reset").addEventListener("click", () => {
    bust = Date.now();
    viewer.imageryLayers.removeAll();   // drops Cesium's cached tile images
    viewer.imageryLayers.add(newLayer());
    tracker.reset();
    refresh();
  });

  const visibleEl = document.getElementById("visible");
  const trafficEl = document.getElementById("traffic");

  function refresh() {
    const view = visibleTiles(viewer);
    const altitude = viewer.camera.positionCartographic.height;
    const shown = [["altitude", altitude > 9999 ? (altitude / 1000).toFixed(0) + " km" : Math.round(altitude) + " m"]];

    if (!view) {
      shown.push(["tiles", "unavailable"]);
    } else {
      shown.push(["tiles", view.total + (view.loading ? "  (" + view.loading + " loading)" : "")]);
      const levels = [...view.byLevel.keys()].sort((a, b) => a - b);
      for (const level of levels) {
        const b = view.byLevel.get(level);
        shown.push(["z" + level, b.n + " \\u00d7  x " + b.x0 + (b.x1 > b.x0 ? "-" + b.x1 : "") +
                                 "  y " + b.y0 + (b.y1 > b.y0 ? "-" + b.y1 : "")]);
      }
      if (!levels.length) shown.push(["", "none in view"]);
    }
    rows(visibleEl, shown);

    const seconds = Math.max(1, (Date.now() - tracker.since) / 1000);
    const traffic = [
      ["downloaded", tracker.downloaded + " tiles"],
      ["network", bytes(tracker.network)],
      ["avg tile", tracker.downloaded ? bytes(Math.round(tracker.payload / tracker.downloaded)) : "-"],
      ["from cache", tracker.cached + " tiles"],
      ["imagery seen", bytes(tracker.imagery)],
      ["last tile", tracker.last],
      ["elapsed", seconds < 60 ? seconds.toFixed(0) + " s" : (seconds / 60).toFixed(1) + " min"],
    ];
    const levels = [...tracker.byLevel.keys()].sort((a, b) => a - b);
    if (levels.length) {
      traffic.push(["by level", levels.map((z) => "z" + z + ":" + tracker.byLevel.get(z)).join("  ")]);
    }
    rows(trafficEl, traffic);
  }

  refresh();
  setInterval(refresh, 400);

  // Exposed deliberately: makes the page inspectable from the dev console.
  window.viewer = viewer;
  window.tilesetMetadata = meta;
  window.tileTracker = tracker;
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
