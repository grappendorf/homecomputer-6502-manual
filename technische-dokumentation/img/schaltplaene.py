#!/usr/bin/env python3
"""Zeichnet die Schaltpläne der Baustufen im Stil des Buches:

  sp-takt.svg    Baustufe 1: Takterzeugung
  sp-reset.svg   Baustufe 2: Reset-Schaltung
  sp-cpu.svg     Baustufe 3: Prozessor

Jede Zeichnung wird gegen die Steckbrett-Zeichnung geprüft (Netzliste aus der
Zeichnung abgeleitet, siehe schaltplan.py). Sprachneutral.
Aufruf: python3 technische-dokumentation/img/schaltplaene.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schaltplan import Plan, vergleiche  # noqa: E402
import zeichnungen  # noqa: E402

OUT = Path(__file__).resolve().parent


def takt():
    p = Plan()
    y = 70
    # Inverter A, B, C
    p.inverter("IC1A", 70, y, 1, 2, "IC1", "74LS04")
    p.inverter("IC1B", 200, y, 3, 4, "IC1", "")
    p.inverter("IC1C", 300, y, 5, 6, "IC1", "")
    p.kondensator("C1", 130, y, "68 nF", senkrecht=False, beschr="oben")
    p.draht((100, y), (110, y))
    p.draht((150, y), (170, y))
    p.draht((230, y), (270, y))
    p.draht((330, y), (347, y))
    p.fahne(347, y, "CLK")
    # R1 über A, R2 über B (unter den Gattern)
    p.widerstand("R1", 72, 105, "1 kΩ", senkrecht=False, beschr="unten")
    p.widerstand("R2", 202, 105, "1 kΩ", senkrecht=False, beschr="unten")
    p.draht((40, y), (40, 105), (52, 105))
    p.draht((92, 105), (105, 105), (105, y))
    p.draht((170, y), (170, 105), (182, 105))
    p.draht((222, 105), (245, 105), (245, y))
    p.knoten(40, y)
    p.knoten(170, y)
    # Quarz oben
    p.quarz("Q1", 143, 35, "1 MHz")
    p.draht((40, y), (40, 35), (123, 35))
    p.draht((163, 35), (245, 35), (245, y))
    # Stromversorgung von IC1
    p.kondensator("C2", 60, 175, "100 nF", laenge=25)
    p.vcc(60, 150)
    p.gnd(60, 200)
    p.ic("IC1", 110, 160, 50, 30, oben=[(14, "", None)], unten=[(7, "", None)], titel="IC1", typ="")
    p.vcc(135, 150)
    p.gnd(135, 200)
    return p


def reset():
    p = Plan()
    p.ic("IC2", 140, 110, 70, 70,
         links=[(6, "THR", None), (7, "DIS", None), (2, "TRIG", None)],
         rechts=[(4, "RESET", None), (3, "OUT", None), (5, "CTRL", "nc")],
         oben=[(8, "VCC", None)], unten=[(1, "GND", None)], titel="NE555", abstand=20, versatz=10)
    # Linke Seite: THR und DIS zusammen, R4 nach oben, C5 nach unten
    p.draht((130, 120), (120, 120), (120, 140), (130, 140))
    p.widerstand("R4", 120, 64, "47 kΩ", pins=("2", "1"))
    p.draht((120, 84), (120, 120))
    p.knoten(120, 120)
    p.kondensator("C5", 120, 200, "10 µF", elko=True, pins=("+", "-"))
    p.draht((120, 140), (120, 180))
    p.knoten(120, 140)
    # TRIG: R3 nach oben, C4 und Taster nach unten
    p.draht((130, 160), (80, 160), (20, 160), (20, 180))
    p.widerstand("R3", 80, 140, "1 MΩ", pins=("2", "1"), beschr="links")
    p.kondensator("C4", 80, 200, "100 nF", pins=("1", "2"), beschr="links")
    p.draht((80, 160), (80, 180))
    p.knoten(80, 160)
    p.taster("S1", 20, 200, "Reset", pins=("1", "2"), beschr="links")
    # Masse-Schiene
    p.draht((20, 220), (20, 230), (80, 230), (120, 230), (175, 230))
    p.draht((80, 220), (80, 230))
    p.draht((120, 220), (120, 230))
    p.draht((175, 190), (175, 230))
    p.knoten(80, 230)
    p.knoten(120, 230)
    p.gnd(175, 230)
    # Versorgungsschiene oben
    p.draht((80, 120), (80, 20), (120, 20), (175, 20), (195, 20), (252, 20), (345, 20))
    p.draht((120, 44), (120, 20))
    p.draht((175, 100), (175, 20))
    p.draht((195, 20), (195, 42))
    p.draht((220, 120), (252, 120), (252, 20))
    p.draht((345, 20), (345, 80))
    for x in (120, 175, 195, 252):
        p.knoten(x, 20)
    p.vcc(175, 20)
    # C3
    p.kondensator("C3", 195, 62, "100 nF", pins=("1", "2"))
    p.gnd(195, 82)
    # Inverter und Ausgang
    p.draht((220, 140), (270, 140))
    p.inverter("IC1D", 300, 140, 9, 8, "IC1", "74LS04")
    p.widerstand("R5", 345, 100, "1 kΩ", pins=("2", "1"))
    p.draht((330, 140), (345, 140), (360, 140))
    p.draht((345, 120), (345, 140))
    p.knoten(345, 140)
    p.fahne(360, 140, "/RESET")
    return p


def cpu():
    p = Plan()
    # Linke Seite: Datenleitungen, erst die an GND, dann die an +5 V, dann der Adressbus
    links = [(33, "D0", None), (31, "D2", None), (29, "D4", None), None, None,
             (32, "D1", None), (30, "D3", None), (28, "D5", None), (27, "D6", None), (26, "D7", None), None]
    adr = [(9 + i, f"A{i}", "nc") for i in range(12)] + [(22 + i, f"A{12 + i}", "nc") for i in range(4)]
    links += adr
    rechts = [(2, "RDY", None), (4, "IRQ", None), (6, "NMI", None), (38, "SO", None),
              (37, "φ0", None), (40, "RES", None), (3, "φ1", "nc"), (39, "φ2", "nc"),
              (7, "SYNC", "nc"), (34, "R/W", "nc"), (5, "", "nc"), (35, "", "nc"), (36, "", "nc")]
    x0, y0, bw = 130, 40, 100
    h = 10 + (len(links) - 1) * 10 + 10
    p.ic("IC3", x0, y0, bw, h, links=links, rechts=rechts, titel="IC3", typ="6502")
    # Datenbus an GND (Pins D0, D2, D4) und +5 V
    def y_l(i):
        return y0 + 10 + i * 10
    gx, vx = 104, 104
    for i in (0, 1, 2):
        p.draht((x0 - 10, y_l(i)), (gx, y_l(i)))
    p.draht((gx, y_l(0)), (gx, y_l(2)))
    for i in (1, 2):
        p.knoten(gx, y_l(i))
    p.knoten(gx, y_l(0))
    p.gnd(gx, y_l(2))
    p.draht((gx, y_l(2)), (gx, y_l(2)))
    v0 = 5
    for i in range(v0, v0 + 5):
        p.draht((x0 - 10, y_l(i)), (vx, y_l(i)))
        p.knoten(vx, y_l(i))
    p.draht((vx, y_l(v0 + 4)), (vx, y_l(v0)))
    p.vcc(vx, y_l(v0))
    # Pull-ups rechts
    xr = x0 + bw + 10
    spalten = {2: 272, 4: 302, 6: 332, 38: 362}
    namen = {2: "R6", 4: "R9", 6: "R8", 38: "R7"}
    for k, (nr, col) in enumerate(spalten.items()):
        yy = y0 + 10 + k * 10
        p.draht((xr, yy), (col, yy), (col, 40))
        p.widerstand(namen[nr], col, 20, "3k3", pins=("2", "1"), beschr="rechts")
        p.vcc(col, 0)
    # CLK und RESET
    p.draht((xr, y0 + 50), (xr + 12, y0 + 50))
    p.fahne(xr + 12, y0 + 50, "CLK")
    p.draht((xr, y0 + 60), (xr + 12, y0 + 60))
    p.fahne(xr + 12, y0 + 60, "/RESET")
    # Stromversorgung des IC
    p.kondensator("C6", 270, 245, "100 nF", beschr="links", laenge=30)
    p.vcc(270, 215)
    p.gnd(270, 275)
    p.ic("IC3", 300, 225, 50, 40, oben=[(8, "VCC", None)], unten=[(1, "GND", None), (21, "GND", None)], titel="IC3",
         ic_name="IC3")
    p.vcc(325, 215)
    p.draht((315, 275), (315, 285), (325, 285), (335, 285), (335, 275))
    p.knoten(325, 285)
    p.gnd(325, 285)
    return p


def main():
    for name, fn, stufe_nr, titel in (
            ("sp-takt", takt, 1, "Schaltplan der Takterzeugung"),
            ("sp-reset", reset, 2, "Schaltplan der Reset-Schaltung"),
            ("sp-cpu", cpu, 3, "Schaltplan des Prozessors")):
        plan = fn()
        bb, _ = zeichnungen.stufe(stufe_nr)
        vergleiche(plan, bb)
        (OUT / f"{name}.svg").write_text(plan.svg(titel), encoding="utf-8")
        print(f"{name}.svg geschrieben, Netzliste stimmt mit dem Steckbrett überein")


if __name__ == "__main__":
    main()
