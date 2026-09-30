#!/usr/bin/env python3
"""Erzeugt aus den Vorlagen (*.s.vorlage) die Programme der Kapitel 7 bis 12 mit
deutschen und englischen Kommentaren: de/<name>.s und en/<name>.s.
Die Marken ;{name} in den Vorlagen werden durch die Kommentare aus kommentare.py ersetzt.
Aufruf: python3 technische-dokumentation/programme/erzeugen.py"""
import re
from pathlib import Path

from kommentare import K

HIER = Path(__file__).resolve().parent
PROGRAMME = ("monitor", "blink", "lcd", "tastatur", "irq", "synth")


def erzeuge():
    for prog in PROGRAMME:
        vorlage = (HIER / f"{prog}.s.vorlage").read_text(encoding="utf-8")
        for sprache in ("de", "en"):
            text = re.sub(r";\{(\w+)\}", lambda m: "; " + K[prog][sprache][m.group(1)], vorlage)
            (HIER / sprache / f"{prog}.s").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    erzeuge()
    print("Programme erzeugt (de, en)")
