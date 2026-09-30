#!/bin/bash
# Build the technical documentation for each language: pages/<de|en>/*.html ->
# build/HOMECOMPUTER 6502 Technische Dokumentation_<de|en>.pdf (see build.py).
# Languages via $SPRACHEN (default: "de en").
# Needs python3, qpdf and Chrome or Chromium (other path via $CHROME).
set -euo pipefail
cd "$(dirname "$0")"
for tool in python3 qpdf; do
  if ! command -v "${tool}" >/dev/null; then
    echo "${tool} not found" >&2
    exit 1
  fi
done
exec python3 build.py "$@"
