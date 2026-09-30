#!/bin/bash
# Build the manuals. Usage: ./build.sh [bedienungsanleitung|technische-dokumentation|all]
# Default: all. Extra arguments go to the manual's build script.
set -euo pipefail
cd "$(dirname "$0")"
what="${1:-all}"
[ $# -gt 0 ] && shift
case "${what}" in
  bedienungsanleitung) exec bedienungsanleitung/build.sh "$@" ;;
  technische-dokumentation) exec technische-dokumentation/build.sh "$@" ;;
  all)
    bedienungsanleitung/build.sh "$@"
    technische-dokumentation/build.sh "$@"
    ;;
  *) echo "unknown manual: ${what}" >&2; exit 1 ;;
esac
