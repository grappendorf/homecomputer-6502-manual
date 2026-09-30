#!/usr/bin/env python3
"""Baut die technische Dokumentation (de, en). Siehe shared/manualbuild.py.
Aufruf:  python3 technische-dokumentation/build.py"""
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER.parent / "shared"))
import manualbuild  # noqa: E402

manualbuild.konfiguriere(
    HIER,
    basisname={"de": "HOMECOMPUTER 6502 Technische Dokumentation",
               "en": "HOMECOMPUTER 6502 Technical Documentation"},
    dok_titel={"de": "HomeComputer 6502 – Technische Dokumentation und Bauanleitung",
               "en": "HomeComputer 6502 – Technical Documentation and Build Guide"},
)

if __name__ == "__main__":
    manualbuild.main()
