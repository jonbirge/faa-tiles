#!/usr/bin/env bash
# Write tilesets.json beside index.html, listing the tilesets in this folder.
#
# Run on the server after adding or removing a tileset:
#
#     bash update_tilesets.sh
#
# index.html reads tilesets.json to find its tilesets, because a web page cannot
# list a directory and most servers show index.html rather than a listing once
# it exists. A tileset is an immediate subdirectory holding a metadata.json;
# only its presence is checked. The buttons take their labels from each
# metadata.json when the page loads, so the names here are just directory names.
set -euo pipefail

root="${1:-$(cd "$(dirname "$0")" && pwd)}"
cd "$root"

entries=()
for dir in */; do
  dir="${dir%/}"
  [ -f "$dir/metadata.json" ] || continue
  escaped="${dir//\\/\\\\}"
  escaped="${escaped//\"/\\\"}"
  entries+=("  {\"path\": \"./$escaped\", \"name\": \"$escaped\"}")
  echo "./$dir"
done

{
  echo "["
  for i in "${!entries[@]}"; do
    if [ "$i" -lt $((${#entries[@]} - 1)) ]; then echo "${entries[$i]},"; else echo "${entries[$i]}"; fi
  done
  echo "]"
} > tilesets.json

echo "${#entries[@]} tileset(s) written to $root/tilesets.json"
