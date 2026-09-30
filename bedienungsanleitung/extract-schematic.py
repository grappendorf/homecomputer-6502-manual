#!/usr/bin/env python3
"""Extrahiert die Seiten des Schaltplan-PDFs als SVG in bedienungsanleitung/schematic/.

Die fertigen seite-N.svg liegen im Git; bedienungsanleitung/build.py braucht dann kein
pdftocairo mehr und bindet die eingelesenen Dateien direkt in Anhang F ein.

Ablauf:
  1. Mit pdfinfo die Seitenzahl des Schaltplan-PDFs lesen.
  2. Jede Seite mit pdftocairo in seite-N.svg umwandeln.
  3. Querformatige Seiten ins Hochformat drehen (90° gegen den Uhrzeigersinn).
     Im CSS gedreht, wäre das Bild vor dem Drehen breiter als die Seite, und
     Chrome verkleinert dann beim Drucken das ganze Dokument.
  4. Nur Dateien mit abweichendem Inhalt ersetzen; bei Fehlern bleibt das
     Zielverzeichnis unangetastet (erst umwandeln, dann schreiben).

Erneuern:  python3 bedienungsanleitung/extract-schematic.py           (schreibt, was fehlt)
Prüfen:    python3 bedienungsanleitung/extract-schematic.py --check   (0 = aktuell, 1 = veraltet)

Der PDF-Pfad ist wie bei build.py ($SCHALTPLAN oder Hardware-Repo daneben),
das Zielverzeichnis über $SCHALTPLAN_ZIEL. Braucht pdfinfo und pdftocairo
(poppler-utils).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
# Schaltplan aus dem Hardware-Repo daneben (anderer Pfad über $SCHALTPLAN).
SCHALTPLAN = Path(os.environ.get("SCHALTPLAN") or HIER.parent.parent / "homecomputer-6502"
                  / "schematics" / "homecomputer-6502-final-kicad-schematic.pdf")
# bedienungsanleitung/schematic/ — liegt im Git, build.py liest von hier.
ZIEL = Path(os.environ.get("SCHALTPLAN_ZIEL") or HIER / "schematic")


def fehler(text):
    print(f"extract-schematic.py: {text}", file=sys.stderr)
    sys.exit(1)


def hochformat(text):
    """Gibt den SVG-Text zurück, querformatige Seiten um 90° gegen den
    Uhrzeigersinn gedreht ins Hochformat."""
    kopf = re.search(r"<svg\b[^>]*>", text)
    if not kopf:
        fehler("kein <svg>-Element im pdftocairo-Ergebnis")
    vb = re.search(r'viewBox="([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)"', kopf.group(0))
    if not vb:
        fehler("keine viewBox im SVG-Kopf")
    x, y, b, h = (float(v) for v in vb.groups())
    if h >= b:
        return text
    neu = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'width="{h}pt" height="{b}pt" viewBox="0 0 {h} {b}">'
           f'<g transform="translate(0 {b}) rotate(-90) translate({-x} {-y})">')
    ende = text.rindex("</svg>")
    return text[:kopf.start()] + neu + text[kopf.end():ende] + "</g></svg>\n"


def seitenzahl():
    info = subprocess.run(["pdfinfo", SCHALTPLAN], capture_output=True, text=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", info, re.M)
    if not m:
        fehler(f"{SCHALTPLAN}: Seitenzahl nicht zu lesen")
    return int(m.group(1))


def umwandeln(n):
    """Seite n des PDFs als fertiger (ggf. gedrehter) SVG-Text.
    Der Zielname muss auf .svg enden, sonst hängt pdftocairo die
    Seitenzahl an (seite.svg -> seite-1.svg)."""
    with tempfile.TemporaryDirectory() as tmp:
        roh = Path(tmp) / f"seite-{n}.svg"
        subprocess.run(["pdftocairo", "-svg", "-f", str(n), "-l", str(n),
                        SCHALTPLAN, roh], check=True)
        if not roh.exists():
            fehler(f"pdftocairo hat für Seite {n} keine SVG erzeugt")
        return hochformat(roh.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Schaltplan-PDF -> schematic/*.svg")
    parser.add_argument("--check", action="store_true",
                        help="nur prüfen, ob schematic/ dem PDF entspricht "
                             "(Exit 1, wenn veraltet oder fehlend)")
    args = parser.parse_args()

    for werkzeug in ("pdfinfo", "pdftocairo"):
        if not shutil.which(werkzeug):
            fehler(f"{werkzeug} nicht gefunden (poppler-utils)")
    if not SCHALTPLAN.exists():
        fehler(f"Schaltplan fehlt: {SCHALTPLAN} (Pfad über $SCHALTPLAN)")

    veraltet = []
    for n in range(1, seitenzahl() + 1):
        neu = umwandeln(n)
        ziel = ZIEL / f"seite-{n}.svg"
        aktuell = ziel.read_text(encoding="utf-8") if ziel.exists() else None
        if aktuell == neu:
            continue
        veraltet.append(n)
        if args.check:
            print(f"veraltet: {ziel.relative_to(HIER.parent)}"
                  + ("" if aktuell is not None else " (fehlt)"), file=sys.stderr)
            continue
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(neu, encoding="utf-8")

    if args.check:
        if veraltet:
            sys.exit(1)
        print(f"aktuell: {ZIEL.relative_to(HIER.parent)} stimmt mit dem PDF überein")
    elif veraltet:
        print(f"{ZIEL.relative_to(HIER.parent)}: {len(veraltet)} Seite(n) erneuert "
              f"({', '.join(str(n) for n in veraltet)})")
    else:
        print(f"{ZIEL.relative_to(HIER.parent)}: unverändert, alle Seiten aktuell")


if __name__ == "__main__":
    main()
