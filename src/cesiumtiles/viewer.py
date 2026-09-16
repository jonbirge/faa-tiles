"""Emit a self-contained Cesium viewer and tile tester for a generated tileset.

``gdal raster tile`` can write Leaflet, OpenLayers, MapML and STAC front ends,
but not a Cesium one, so we write our own. The page reads ``metadata.json`` at
runtime, so re-tiling with different bounds or zooms needs no change to the
HTML, and it can be pointed at any other tileset -- a directory beside it or a
remote XYZ service -- without regenerating anything.
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
    padding: 10px 12px; width: 318px; backdrop-filter: blur(6px);
    max-height: calc(100vh - 40px); overflow-y: auto;
  }
  #panel h2 {
    margin: 12px 0 5px; font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.09em; color: #7f8794;
    border-top: 1px solid rgba(255, 255, 255, 0.12); padding-top: 8px;
  }
  #panel h2:first-child { margin-top: 0; border-top: 0; padding-top: 0; }
  #panel dl { margin: 0; display: grid; grid-template-columns: auto 1fr; gap: 1px 10px; }
  #panel dt { color: #8d95a0; }
  #panel dd { margin: 0; overflow-wrap: anywhere; }
  #panel button, #panel input, #panel select {
    color: #e8e8e8; background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 4px;
    padding: 5px; font: inherit;
  }
  #panel button { margin-top: 8px; width: 100%; cursor: pointer; }
  #panel button:hover { background: rgba(255, 255, 255, 0.18); }
  #panel button:active { background: rgba(255, 255, 255, 0.26); }
  #source { width: 100%; box-sizing: border-box; }
  .controls {
    display: grid; grid-template-columns: auto 1fr auto 1fr;
    gap: 4px 6px; align-items: center; margin-top: 6px;
  }
  .controls label { color: #8d95a0; }
  .controls select, .controls input { width: 100%; box-sizing: border-box; }
  .swatch {
    display: inline-block; width: 9px; height: 9px; margin-right: 6px;
    border-radius: 2px; vertical-align: baseline;
    box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.45);
  }
  .num { font-variant-numeric: tabular-nums; }
  #error { color: #ff8b8b; margin-top: 8px; display: none; }
  #note { color: #c2a74e; margin-top: 6px; display: none; }
</style>
</head>
<body>
<div id="cesiumContainer"></div>
<div id="panel">
  <h2>Source</h2>
  <input id="source" spellcheck="false"
         placeholder="tileset directory, or a {z}/{x}/{y} URL">
  <div class="controls">
    <label for="scheme">scheme</label>
    <select id="scheme">
      <option value="mercator">mercator</option>
      <option value="geographic">geographic</option>
    </select>
    <label for="tilesize">px</label>
    <input id="tilesize" type="number" min="32" max="2048" step="1">
    <label for="minzoom">min z</label>
    <input id="minzoom" type="number" min="0" max="24" step="1">
    <label for="maxzoom">max z</label>
    <input id="maxzoom" type="number" min="0" max="24" step="1">
  </div>
  <button id="load">Load source</button>
  <div id="note"></div>
  <div id="error"></div>

  <h2>Tileset</h2>
  <dl id="facts"></dl>
  <button id="home">Fly to extent</button>

  <h2>On screen</h2>
  <dl id="visible"></dl>
  <button id="grid">Show tile grid</button>

  <h2>Downloaded</h2>
  <dl id="traffic"></dl>
  <button id="reset">Reset counters &amp; cache</button>
</div>
<script>
const METADATA = __METADATA__;

// -- tile grid colouring -------------------------------------------------
// Blue and orange alternate by level parity, each family darkening as the level
// rises. The alternation is the whole point: the levels visible together are
// consecutive, so making neighbours differ in HUE rather than in lightness is
// what makes them tellable apart. A single smooth ramp cannot manage it -- ten
// steps in one hue land about 0.047 apart in lightness and read as one colour,
// and even a two-hue smooth ramp scored a protan deltaE of 0.6 between
// neighbours. This scheme measures 21.4 protan and 28.0 normal-vision on its
// worst adjacent pair, against floors of 8 and 15. Lightness still carries the
// ordering inside each hue, so z5 and z7 stay distinguishable too.
const GRID_BLUE = ["#5facff", "#4693f3", "#2c79d8", "#0f64c0", "#0052ac"];
const GRID_ORANGE = ["#ff9866", "#ff7e4c", "#eb6834", "#d25117", "#bd3d00"];

function gridColor(level) {
  const family = level % 2 === 0 ? GRID_BLUE : GRID_ORANGE;
  return family[Math.min(family.length - 1, Math.floor(level / 2))];
}

// The imagery rectangle must be the *unsnapped* data extent, never the
// tile-snapped `bounds`. Cesium's _createTileImagerySkeletons intersects an
// imagery tile against this rectangle, and when an edge coincides exactly with
// a tile boundary that intersection comes back undefined, which then blows up
// inside rectangleToNativeRectangle ("can't access property west"). Measured:
// tile-snapped edges produce ~60 such calls while panning the border, the data
// extent produces none.
function extentOf(meta) {
  return meta.data_bounds || meta.bounds || [-180, -85, 180, 85];
}

function bytes(n) {
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / 1048576).toFixed(2) + " MB";
}

function rows(dl, pairs) {
  dl.textContent = "";
  for (const [k, v, swatch] of pairs) {
    const dt = document.createElement("dt"); dt.textContent = k;
    const dd = document.createElement("dd"); dd.className = "num";
    if (swatch) {
      const chip = document.createElement("span");
      chip.className = "swatch";
      chip.style.background = swatch;
      dd.appendChild(chip);
    }
    dd.appendChild(document.createTextNode(v));
    dl.append(dt, dd);
  }
}

function facts(meta) {
  const [w, s, e, n] = extentOf(meta);
  const fallbackCrs = meta.scheme === "geographic" ? "EPSG:4326" : "EPSG:3857";
  const out = [
    ["name", meta.name || "(unnamed)"],
    ["scheme", meta.scheme + " / " + (meta.crs || fallbackCrs)],
    ["zooms", meta.minzoom + "-" + meta.maxzoom],
  ];
  if (meta.format) out.push(["format", meta.format + " (" + (meta.convention || "xyz") + ")"]);
  if (meta.tiles) out.push(["tiles", meta.tiles.toLocaleString()]);
  if (meta.bytes) out.push(["size", (meta.bytes / 1e6).toFixed(1) + " MB"]);
  out.push(["extent", w.toFixed(3) + ", " + s.toFixed(3)]);
  out.push(["", e.toFixed(3) + ", " + n.toFixed(3)]);
  return out;
}

// -- download accounting ------------------------------------------------
// Resource Timing gives the real transfer size per tile.
//
// Telling a real download from a cache hit needs care, because browsers do not
// agree on how to report one. A cache hit can arrive as transferSize 0, or as a
// fixed ~300-byte header placeholder alongside a full encodedBodySize and a 200
// status. The reliable, browser-independent test is whether the body could have
// crossed the wire at all: if transferSize is smaller than encodedBodySize, it
// did not. That covers 304 revalidations and plain cache hits alike.
//
// A cross-origin tile server that omits Timing-Allow-Origin reports all three
// sizes as zero. Those are counted separately and the byte totals marked
// unavailable, rather than silently reported as zero.
//
// Cesium also keeps its own in-memory imagery cache, and a tile it serves from
// there makes no request at all, so it appears in none of these counters.
function makeTracker() {
  const state = {
    pattern: /(\\d+)\\/(\\d+)\\/(\\d+)(?:\\.[A-Za-z0-9]+)?(?:\\?|$)/,
    prefix: "",
    downloaded: 0, cached: 0, opaque: 0,
    network: 0, payload: 0, imagery: 0,
    last: "-", byLevel: new Map(), since: Date.now(),
  };

  function consume(entry) {
    if (state.prefix && entry.name.indexOf(state.prefix) === -1) return;
    const hit = state.pattern.exec(entry.name);
    if (!hit) return;
    const z = hit[1], x = hit[2], y = hit[3];
    state.last = z + "/" + x + "/" + y;

    const body = entry.encodedBodySize || 0;
    const wire = entry.transferSize || 0;
    const decoded = entry.decodedBodySize || 0;
    state.imagery += decoded;
    state.network += wire;

    if (body === 0 && wire === 0 && decoded === 0) {
      state.opaque++;                      // cross-origin, sizes withheld
    } else if (body > 0 && wire < body) {
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
    state.downloaded = 0; state.cached = 0; state.opaque = 0;
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
function visibleTiles(viewer, layer) {
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
        if (layer && tile.imageryLayer !== layer) continue;
        if (!slot.readyImagery) loading++;
        const key = tile.level + "/" + tile.x + "/" + tile.y;
        if (seen.has(key)) continue;
        seen.add(key);
        let box = byLevel.get(tile.level);
        if (!box) {
          box = { n: 0, x0: tile.x, x1: tile.x, y0: tile.y, y1: tile.y };
          byLevel.set(tile.level, box);
        }
        box.n++;
        box.x0 = Math.min(box.x0, tile.x); box.x1 = Math.max(box.x1, tile.x);
        box.y0 = Math.min(box.y0, tile.y); box.y1 = Math.max(box.y1, tile.y);
      }
    }
    return { total: seen.size, loading: loading, byLevel: byLevel };
  } catch (err) {
    return null;
  }
}

// -- resolving whatever was typed into a tileset ------------------------
// Either a URL template containing {z}/{x}/{y}, used as given, or a directory
// expected to hold the metadata.json one of our own tilesets writes.
async function resolveSource(spec, form) {
  spec = (spec || "").trim();
  if (!spec) throw new Error("enter a directory or a {z}/{x}/{y} URL");

  if (spec.indexOf("{z}") !== -1) {
    return {
      name: spec, url_template: spec,
      scheme: form.scheme, minzoom: form.minzoom,
      maxzoom: form.maxzoom, tilesize: form.tilesize,
      templateOnly: true,
    };
  }

  const base = spec.replace(/\\/+$/, "");
  const response = await fetch(base + "/metadata.json");
  if (!response.ok) {
    throw new Error("no metadata.json under " + base + " (HTTP " + response.status + ")");
  }
  const meta = await response.json();
  // Its url_template is relative to its own directory, not to this page.
  meta.url_template = base + "/" + meta.url_template;
  return meta;
}

function start(initialMeta) {
  const viewer = new Cesium.Viewer("cesiumContainer", {
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
    // No Ion token is used: our own tiles become the base layer below, and the
    // default ellipsoid terrain needs no network access.
    baseLayer: false,
  });
  viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString("#10131a");

  const el = (id) => document.getElementById(id);
  const tracker = makeTracker();

  let meta = initialMeta;
  let rectangle = null;
  let baseLayer = null;
  let gridLayer = null;
  let bust = 0;

  const newTilingScheme = () => (meta.scheme === "geographic"
    ? new Cesium.GeographicTilingScheme()
    : new Cesium.WebMercatorTilingScheme());

  function newLayer() {
    const joiner = meta.url_template.indexOf("?") === -1 ? "?r=" : "&r=";
    const provider = new Cesium.UrlTemplateImageryProvider({
      url: meta.url_template + (bust ? joiner + bust : ""),
      tilingScheme: newTilingScheme(),
      rectangle: rectangle,
      minimumLevel: meta.minzoom,
      maximumLevel: meta.maxzoom,
      tileWidth: meta.tilesize,
      tileHeight: meta.tilesize,
      hasAlphaChannel: meta.format !== "jpeg",
      credit: new Cesium.Credit(meta.name || "tiles", false),
    });
    provider.errorEvent.addEventListener(() =>
      note("a tile request failed - a remote server may be refusing cross-origin use"));
    return new Cesium.ImageryLayer(provider);
  }

  // The grid is generated canvases, not fetched files, so it adds nothing to
  // the traffic counters. Only the tile edge is drawn -- a dark hairline
  // underneath keeps it legible where the imagery below is pale.
  function newGridLayer() {
    const provider = new Cesium.TileCoordinatesImageryProvider({ tilingScheme: newTilingScheme() });
    provider.maximumLevel = meta.maxzoom;
    const size = meta.tilesize || 256;
    provider.requestImage = function (x, y, level) {
      const canvas = document.createElement("canvas");
      canvas.width = canvas.height = size;
      const ctx = canvas.getContext("2d");
      ctx.strokeStyle = "rgba(0, 0, 0, 0.30)";
      ctx.lineWidth = 5;
      ctx.strokeRect(2.5, 2.5, size - 5, size - 5);
      ctx.globalAlpha = 0.72;
      ctx.strokeStyle = gridColor(level);
      ctx.lineWidth = 3;
      ctx.strokeRect(2.5, 2.5, size - 5, size - 5);
      return Promise.resolve(canvas);
    };
    return new Cesium.ImageryLayer(provider, { rectangle: rectangle });
  }

  function relayer() {
    const showingGrid = gridLayer !== null;
    viewer.imageryLayers.removeAll();
    baseLayer = newLayer();
    viewer.imageryLayers.add(baseLayer);
    gridLayer = showingGrid ? newGridLayer() : null;
    if (gridLayer) viewer.imageryLayers.add(gridLayer);
  }

  function rebuild(fly) {
    const extent = extentOf(meta);
    rectangle = Cesium.Rectangle.fromDegrees(extent[0], extent[1], extent[2], extent[3]);
    relayer();
    // Count only tiles belonging to the source now loaded.
    tracker.prefix = meta.url_template.split("{z}")[0];
    window.tilesetMetadata = meta;   // kept current, not captured at startup
    rows(el("facts"), facts(meta));
    el("scheme").value = meta.scheme;
    el("minzoom").value = meta.minzoom;
    el("maxzoom").value = meta.maxzoom;
    el("tilesize").value = meta.tilesize;
    if (fly) viewer.camera.setView({ destination: rectangle });
    refresh();
  }

  function note(message) {
    const box = el("note");
    box.style.display = message ? "block" : "none";
    box.textContent = message || "";
  }

  function problem(message) {
    const box = el("error");
    box.style.display = message ? "block" : "none";
    box.textContent = message || "";
  }

  el("load").addEventListener("click", async () => {
    problem(""); note("");
    const spec = el("source").value;
    try {
      const loaded = await resolveSource(spec, {
        scheme: el("scheme").value,
        minzoom: Number(el("minzoom").value) || 0,
        maxzoom: Number(el("maxzoom").value) || 18,
        tilesize: Number(el("tilesize").value) || 256,
      });
      if (loaded.templateOnly) {
        note("no metadata.json: using the scheme and zooms set above, whole-world extent");
      }
      meta = loaded;
      meta.source_spec = spec;
      bust = 0;
      tracker.reset();
      rebuild(true);
    } catch (err) {
      problem(err.message);
    }
  });

  el("home").addEventListener("click", () =>
    viewer.camera.flyTo({ destination: rectangle, duration: 1.5 }));

  // Clearing the browser's HTTP cache is not possible from script, so reset
  // rebuilds the layer against a fresh query string instead: new URLs miss both
  // Cesium's in-memory tile cache and the browser's, and the counters then
  // measure a genuine cold load rather than replaying what is already local.
  el("reset").addEventListener("click", () => {
    bust = Date.now();
    relayer();
    tracker.reset();
    refresh();
  });

  el("grid").addEventListener("click", () => {
    if (gridLayer) {
      viewer.imageryLayers.remove(gridLayer, true);
      gridLayer = null;
    } else {
      gridLayer = newGridLayer();
      viewer.imageryLayers.add(gridLayer);
    }
    el("grid").textContent = gridLayer ? "Hide tile grid" : "Show tile grid";
    refresh();
  });

  function refresh() {
    const view = visibleTiles(viewer, baseLayer);
    const altitude = viewer.camera.positionCartographic.height;
    const shown = [["altitude", altitude > 9999
      ? (altitude / 1000).toFixed(0) + " km" : Math.round(altitude) + " m"]];

    if (!view) {
      shown.push(["tiles", "unavailable"]);
    } else {
      shown.push(["tiles", view.total + (view.loading ? "  (" + view.loading + " loading)" : "")]);
      const levels = [...view.byLevel.keys()].sort((a, b) => a - b);
      for (const level of levels) {
        const b = view.byLevel.get(level);
        const span = b.n + " \\u00d7  x " + b.x0 + (b.x1 > b.x0 ? "-" + b.x1 : "") +
                     "  y " + b.y0 + (b.y1 > b.y0 ? "-" + b.y1 : "");
        shown.push(["z" + level, span, gridLayer ? gridColor(level) : null]);
      }
      if (!levels.length) shown.push(["", "none in view"]);
    }
    rows(el("visible"), shown);

    const seconds = Math.max(1, (Date.now() - tracker.since) / 1000);
    const opaque = tracker.opaque > 0 && tracker.payload === 0;
    const traffic = [
      ["downloaded", (tracker.downloaded + tracker.opaque) + " tiles"],
      ["network", opaque ? "n/a (cross-origin)" : bytes(tracker.network)],
      ["avg tile", tracker.downloaded
        ? bytes(Math.round(tracker.payload / tracker.downloaded)) : "-"],
      ["from cache", tracker.cached + " tiles"],
      ["imagery seen", opaque ? "n/a" : bytes(tracker.imagery)],
      ["last tile", tracker.last],
      ["elapsed", seconds < 60 ? seconds.toFixed(0) + " s" : (seconds / 60).toFixed(1) + " min"],
    ];
    const levels = [...tracker.byLevel.keys()].sort((a, b) => a - b);
    if (levels.length) {
      traffic.push(["by level", levels.map((z) => "z" + z + ":" + tracker.byLevel.get(z)).join("  ")]);
    }
    rows(el("traffic"), traffic);
  }

  el("source").value = meta.source_spec || ".";
  rebuild(true);
  setInterval(refresh, 400);

  // Exposed deliberately: makes the page inspectable from the dev console.
  window.viewer = viewer;
  window.tileTracker = tracker;
  window.loadSource = (spec) => { el("source").value = spec; el("load").click(); };
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
        .replace("__TITLE__", str(metadata.get("name", "Tile tester")))
        .replace("__METADATA__", json.dumps(metadata, indent=2))
    )


def write_viewer(output_dir: str | Path, metadata: dict) -> Path:
    """Write ``index.html`` next to the tiles and return its path."""
    path = Path(output_dir) / "index.html"
    path.write_text(render_viewer(metadata), encoding="utf-8")
    return path
