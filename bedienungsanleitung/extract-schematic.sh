#!/bin/bash
# Extract the schematic PDF pages as SVG: schematic/seite-N.svg (see the
# Python script). Pass --check to only verify that schematic/ is current.
# Needs python3 and poppler-utils (pdfinfo, pdftocairo).
set -euo pipefail
cd "$(dirname "$0")"
for tool in python3 pdfinfo pdftocairo; do
  if ! command -v "${tool}" >/dev/null; then
    echo "${tool} not found" >&2
    exit 1
  fi
done
exec python3 extract-schematic.py "$@"
