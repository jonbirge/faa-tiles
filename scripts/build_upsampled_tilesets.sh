#!/usr/bin/env bash
# Build one tileset per super-resolution model, for A/B comparison in the tester.
#
#   bash scripts/build_upsampled_tilesets.sh
#
# Each model upsamples the neatline-cropped chart 2x (4x the pixels), which
# raises the native zoom from z9 to z10, and the result is tiled with the same
# settings as ./tileset so the only variable is the upsampler.
#
# The upsampled GeoTIFF is an intermediate only and is deleted once tiled: it is
# ~1-2 GB per model and nothing downstream needs it. Pass KEEP=1 to retain them.
set -u

PY=.venv/Scripts/python.exe
SOURCE=source/wall-planning/vfr_wall_planning_geo.tif
mkdir -p source/wall-planning/upsampled

run() {
  local label="$1" model="$2" title="$3"
  local tif="source/wall-planning/upsampled/${label}.tif"
  local out="tileset-${label}"

  echo "=============================================================="
  echo "  ${label}"
  echo "=============================================================="
  "$PY" scripts/upsample.py "$SOURCE" --model "$model" --out "$tif" || return 1
  "$PY" -m cesiumtiles.cli "$tif" "$out" --title "$title" --overwrite --quiet || return 1
  [ "${KEEP:-0}" = "1" ] || rm -f "$tif"
  echo
}

run apisr     "source/models/2x_APISR_RRDB_GAN_generator.pth" "VFR chart - APISR 2x"
run realcugan "source/models/realcugan-up2x-no-denoise.pth"   "VFR chart - Real-CUGAN 2x"
run waifu2x   "waifu2x"                                "VFR chart - waifu2x 2x"

echo "=============================================================="
du -sh tileset tileset-lossy tileset-apisr tileset-realcugan tileset-waifu2x 2>/dev/null
