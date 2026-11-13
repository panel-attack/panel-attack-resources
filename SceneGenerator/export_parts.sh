#!/bin/sh
# Writes PNG: renders the part SVGs already in build/parts/ through Pixelmator Pro into the game theme's scenes/,
# one part at a time, without running the generators (`python3 -m scene_export render` runs them first).
#   ./export_parts.sh                      every part
#   ./export_parts.sh left-urn foliage     the named groups or parts (see scene_export/export.py)
#   ./export_parts.sh --force <path> ...   also replace those PNGs though they were edited
cd "$(dirname "$0")" || exit 1
exec python3 -m scene_export.export "$@"
