#!/usr/bin/env python3
"""Zeichnet die Steckbrett-Abbildungen der technischen Dokumentation:

  bb-takt.svg    Baustufe 1: Takterzeugung
  bb-reset.svg   Baustufe 2: + Reset-Schaltung
  bb-cpu.svg     Baustufe 3: + Prozessor (zweites Steckbrett)

Jede Zeichnung wird beim Erzeugen gegen die Netzliste des Schaltplans
geprüft (breadboard.py), damit Schaltplan und Steckbrett nicht auseinanderlaufen.
Die Beschriftungen (IC1, R1, CLK, ...) sind sprachneutral.
Aufruf: python3 technische-dokumentation/img/zeichnungen.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from breadboard import (Steckbrett, ROT, SCHWARZ, GRUEN, GELB, BLAU, WEISSDRAHT,  # noqa: E402
                        BRAUN, ORANGE)

OUT = Path(__file__).resolve().parent


def stufe(n):
    """Baut Stufe n (1 = Takt, 2 = + Reset, 3 = + Prozessor)."""
    bb = Steckbrett()
    cols = {1: 15, 2: 27, 3: 27}[n]
    b1 = bb.brett(0, 0, cols)
    netze = {}

    def netz(name, *pins):
        netze.setdefault(name, set()).update(pins)

    # ---- Stromversorgung -------------------------------------------------
    bb.draht((-30, b1.xy(1, "T+")[1], "ext:+5V"), (b1, 1, "T+"), ROT, name="+5V")
    bb.draht((-30, b1.xy(1, "T-")[1], "ext:GND"), (b1, 1, "T-"), SCHWARZ, name="GND")
    bb.beschriftung("+5 V", -33, b1.xy(1, "T+")[1] + 2.2, 6.5, "end", ROT, 700)
    bb.beschriftung("GND", -33, b1.xy(1, "T-")[1] + 2.2, 6.5, "end", SCHWARZ, 700)
    bb.draht((b1, 2, "T+"), (b1, 2, "B+"), ROT, name="Brücke+")
    bb.draht((b1, 3, "T-"), (b1, 3, "B-"), SCHWARZ, name="Brücke-")
    netz("VCC", "ext:+5V")
    netz("GND", "ext:GND")

    # ---- Stufe 1: Takt -----------------------------------------------------
    bb.ic("IC1", b1, 5, 14, "74LS04")
    bb.draht((b1, 5, "j"), (b1, 5, "T+"), ROT, name="IC1 VCC")
    bb.draht((b1, 11, "a"), (b1, 11, "B-"), SCHWARZ, name="IC1 GND")
    bb.keramik("C2", b1, (13, "T+"), (13, "T-"), "100n")
    netz("VCC", "IC1.14", "C2.1")
    netz("GND", "IC1.7", "C2.2")

    bb.widerstand("R1", b1, (5, "b"), (6, "b"), "1k")
    bb.widerstand("R2", b1, (7, "b"), (8, "b"), "1k")
    bb.keramik("C1", b1, (6, "c"), (7, "c"), "68n")
    bb.quarz("Q1", b1, (5, "a"), (8, "a"), "1 MHz")
    bb.draht((b1, 8, "d"), (b1, 9, "d"), GELB, name="4-5")
    netz("N1", "IC1.1", "R1.1", "Q1.1")
    netz("N2", "IC1.2", "R1.2", "C1.1")
    netz("N3", "IC1.3", "C1.2", "R2.1")
    netz("N4", "IC1.4", "IC1.5", "R2.2", "Q1.2")

    if n == 1:
        bb.draht((b1, 10, "c"), (b1.xy(14, "c")[0] + 22, b1.xy(1, "c")[1], "ext:CLK"),
                 GELB, bogen=-6, name="CLK")
        bb.beschriftung("CLK", b1.xy(14, "c")[0] + 25, b1.xy(1, "c")[1] + 2.2, 6.5, "start", "#8a6d00", 700)
        netz("CLK", "IC1.6", "ext:CLK")
        offen = [f"IC1.{k}" for k in (8, 9, 10, 11, 12, 13)]
        bb.pruefe(list(netze.values()), offen)
        return bb, dict(extra_links=46, extra_rechts=34)

    # ---- Stufe 2: Reset ----------------------------------------------------
    bb.ic("IC2", b1, 16, 8, "NE555")
    bb.draht((b1, 16, "j"), (b1, 16, "T+"), ROT, name="IC2 VCC")
    bb.draht((b1, 19, "a"), (b1, 19, "B+"), ROT, name="IC2 /RES")
    bb.draht((b1, 16, "a"), (b1, 16, "B-"), SCHWARZ, name="IC2 GND")
    bb.draht((b1, 17, "i"), (b1, 18, "i"), GELB, name="6-7")
    bb.widerstand("R4", b1, (17, "h"), (17, "T+"), "47k")
    bb.elko("C5", b1, (18, "h"), (18, "T-"), "10u")
    bb.keramik("C3", b1, (21, "T+"), (21, "T-"), "100n")
    netz("VCC", "IC2.8", "IC2.4", "R4.2", "C3.1")
    netz("GND", "IC2.1", "C5.-", "C3.2")
    netz("THR", "IC2.6", "IC2.7", "R4.1", "C5.+")
    # Taster, R3, C4: TRIG-Netz
    bb.taster("S1", b1, 22)
    bb.draht((b1, 17, "c"), (b1, 22, "c"), BLAU, bogen=-7, name="TRIG")
    bb.draht((b1, 24, "j"), (b1, 24, "T-"), SCHWARZ, name="S1 GND")
    bb.widerstand("R3", b1, (24, "c"), (24, "B+"), "1M")
    bb.keramik("C4", b1, (22, "b"), (22, "B-"), "100n")
    netz("TRIG", "IC2.2", "S1.1", "R3.1", "C4.1")
    netz("VCC", "R3.2")
    netz("GND", "S1.2", "C4.2")
    # 555-Ausgang -> Inverter IC1D -> /RESET
    bb.draht((b1, 18, "d"), (b1, 10, "h"), GRUEN, bogen=10, name="OUT")
    netz("OUT", "IC2.3", "IC1.9")
    bb.draht((b1, 11, "i"), (b1, 12, "i"), GELB, name="Pin 8 -> R5")
    bb.widerstand("R5", b1, (12, "h"), (12, "T+"), "1k")
    netz("VCC", "R5.2")
    netz("RST", "IC1.8", "R5.1")

    if n == 2:
        bb.draht((b1, 11, "j"), (b1.xy(11, "T-")[0] + 12, -19, "ext:/RESET"), GELB, name="/RESET")  # Messpunkt
        netz("RST", "ext:/RESET")
        bb.beschriftung("/RESET", b1.xy(11, "T-")[0] + 17, -17, 6.5, "start", "#8a6d00", 700)
        bb.draht((b1, 10, "a"), (b1.xy(14, "a")[0], b1.xy(1, "B+")[1] + 18, "ext:CLK"), GELB, bogen=8, name="CLK")
        netz("CLK", "IC1.6", "ext:CLK")
        bb.beschriftung("CLK", b1.xy(14, "a")[0] + 3, b1.xy(1, "B+")[1] + 20, 6.5, "start", "#8a6d00", 700)
        offen = [f"IC1.{k}" for k in (10, 11, 12, 13)] + ["IC2.5", "IC2.7" if False else "IC2.5"]
        offen = sorted(set(offen))
        bb.pruefe(list(netze.values()), offen)
        return bb, dict(extra_links=46, extra_oben=22, extra_unten=22)

    # ---- Stufe 3: Prozessor (zweites Steckbrett) ---------------------------
    b2 = bb.brett(0, 236, 27)
    # Stromversorgung von Brett 1 zu Brett 2
    bb.draht((b1, 1, "B+"), (b2, 1, "T+"), ROT, name="B1->B2 +")
    bb.draht((b1, 2, "B-"), (b2, 2, "T-"), SCHWARZ, name="B1->B2 -")
    bb.draht((b2, 2, "T+"), (b2, 2, "B+"), ROT, name="Brücke2+")
    bb.draht((b2, 3, "T-"), (b2, 3, "B-"), SCHWARZ, name="Brücke2-")
    bb.ic("IC3", b2, 4, 40, "6502")
    top = lambda p: 44 - p      # Spalte von Pin p (21..40) oben
    bot = lambda p: 3 + p       # Spalte von Pin p (1..20) unten
    # Datenleitungen fest auf $EA = 11101010
    for d in range(8):
        pin = 33 - d
        sp = top(pin)
        if (0xEA >> d) & 1:
            bb.draht((b2, sp, "j"), (b2, sp, "T+"), ROT, name=f"D{d}")
            netz("VCC", f"IC3.{pin}")
        else:
            bb.draht((b2, sp, "j"), (b2, sp, "T-"), SCHWARZ, name=f"D{d}")
            netz("GND", f"IC3.{pin}")
    # Versorgung
    bb.draht((b2, bot(8), "a"), (b2, bot(8), "B+"), ROT, name="IC3 VCC")
    bb.draht((b2, bot(1), "a"), (b2, bot(1), "B-"), SCHWARZ, name="IC3 GND1")
    bb.draht((b2, top(21), "j"), (b2, top(21), "T-"), SCHWARZ, name="IC3 GND21")
    netz("VCC", "IC3.8")
    netz("GND", "IC3.1", "IC3.21")
    bb.keramik("C6", b2, (26, "B+"), (26, "B-"), "100n")
    netz("VCC", "C6.1")
    netz("GND", "C6.2")
    # Pull-ups
    bb.widerstand("R6", b2, (bot(2), "c"), (bot(2), "B+"), "3k3")
    bb.widerstand("R9", b2, (bot(4), "c"), (bot(4), "B+"), "3k3")
    bb.widerstand("R8", b2, (bot(6), "c"), (bot(6), "B+"), "3k3")
    bb.widerstand("R7", b2, (top(38), "i"), (top(38), "T+"), "3k3")
    netz("RDY", "IC3.2", "R6.1")
    netz("IRQ", "IC3.4", "R9.1")
    netz("NMI", "IC3.6", "R8.1")
    netz("SO", "IC3.38", "R7.1")
    for r in ("R6", "R9", "R8", "R7"):
        netz("VCC", f"{r}.2")
    # Takt und Reset von Brett 1
    bb.draht((b1, 11, "g"), (b1, 13, "c"), GELB, name="RST quer")
    bb.draht((b1, 13, "a"), (b2, top(40), "j"), GELB, bogen=-14, name="/RESET")
    bb.draht((b1, 10, "a"), (b2, top(37), "j"), GRUEN, bogen=10, name="CLK")
    netz("RST", "IC3.40")
    netz("CLK", "IC1.6", "IC3.37")
    netz("OUT", "IC2.3", "IC1.9")
    # unbelegte Pins
    offen = ([f"IC1.{k}" for k in (10, 11, 12, 13)] + ["IC2.5"]
             + [f"IC3.{p}" for p in (3, 5, 7, 34, 35, 36, 39)]
             + [f"IC3.{p}" for p in range(9, 21)] + [f"IC3.{p}" for p in range(22, 26)])
    bb.pruefe(list(netze.values()), offen)
    return bb, dict(extra_links=46)


TITEL = {
    1: "Takterzeugung auf dem Steckbrett",
    2: "Takterzeugung und Reset auf dem Steckbrett",
    3: "Takt, Reset und Prozessor auf zwei Steckbrettern",
}


def main():
    for n, name in ((1, "bb-takt"), (2, "bb-reset"), (3, "bb-cpu")):
        bb, optionen = stufe(n)
        (OUT / f"{name}.svg").write_text(bb.svg(titel=TITEL[n], beschr=TITEL[n], **optionen), encoding="utf-8")
        print(f"{name}.svg geschrieben, Netzliste stimmt")


if __name__ == "__main__":
    main()
