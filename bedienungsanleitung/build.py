#!/usr/bin/env python3
"""Baut die Bedienungsanleitung (de, en). Siehe shared/manualbuild.py.
Aufruf:  python3 bedienungsanleitung/build.py"""
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "shared"))
import manualbuild  # noqa: E402

manualbuild.konfiguriere(
    HIER,
    basisname={"de": "HOMECOMPUTER 6502 Bedienungshandbuch",
               "en": "HOMECOMPUTER 6502 User Manual"},
    dok_titel={"de": "HomeComputer 6502 – Bedienungshandbuch",
               "en": "HomeComputer 6502 – User Manual"},
)

if __name__ == "__main__":
    manualbuild.main()
