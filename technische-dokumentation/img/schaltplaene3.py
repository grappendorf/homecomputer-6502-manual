#!/usr/bin/env python3
"""Schaltpläne der Kapitel 8 und 9 im Stil des Buches:

  sp-via.svg   Kapitel 8: Dekoder 74LS137, VIA 6522 und Leuchtdiode
  sp-lcd.svg   Kapitel 9: Port A des VIA und der Anschluss für das Display

Jeder Schaltplan wird gegen die zugehörigen Steckbrett-Zeichnungen geprüft.
Aufruf: python3 technische-dokumentation/img/schaltplaene3.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schaltplan import Plan, vergleiche  # noqa: E402
import zeichnungen3 as z3  # noqa: E402

OUT = Path(__file__).resolve().parent


def zeile(y0, i):
    return y0 + 10 + i * 10


def via_symbol(p, x, y, port_a="nc", pb0_led=True):
    """6522 mit allen Anschlüssen. Rückgabe: Anfang der rechten Seite."""
    links = [(24, "CS1", None), (23, "/CS2", None), (22, "R/W", None), (25, "PHI2", None), (34, "/RES", None),
             (38, "RS0", None), (37, "RS1", None), (36, "RS2", None), (35, "RS3", None)]
    links += [(33 - d, f"D{d}", None) for d in range(8)]
    links += [(21, "/IRQ", "nc"), (40, "CA1", "nc"), (39, "CA2", "nc")]
    rechts = [(2 + k, f"PA{k}", "nc") for k in range(8)] + [(10 + k, f"PB{k}", "nc") for k in range(8)]
    rechts += [(18, "CB1", "nc"), (19, "CB2", "nc")]
    rechts[8] = (10, "PB0", None)
    h = 10 + 19 * 10 + 10
    bw = 110
    p.ic("IC9", x, y, bw, h, links=links, rechts=rechts, oben=[(20, "VCC", None)], unten=[(1, "GND", None)],
         titel="IC9", typ="6522")
    xl, xr = x - 10, x + bw + 10
    p.vcc(xl, zeile(y, 0))
    for i, nm in ((1, "/CS_VIA"), (2, "R/W"), (3, "PHI2"), (4, "/RESET"), (5, "A0"), (6, "A1"), (7, "A2"), (8, "A3")):
        p.draht((xl, zeile(y, i)), (xl - 6, zeile(y, i)))
        p.fahne(xl - 6, zeile(y, i), nm, rechts=False)
    p.bus(xl - 50, [(xl, zeile(y, 9 + d)) for d in range(8)], [f"D{d}" for d in range(8)], "D0–D7", "links")
    p.vcc(x + bw / 2, y - 10)
    p.gnd(x + bw / 2, y + h + 10)
    return xr, h


def via():
    p = Plan()
    # 74LS137
    x, y = 150, 0
    links = [(6, "G1", None), (1, "A", None), (2, "B", None), (3, "C", None), (5, "/G2", None), (4, "/GL", None)]
    rechts = [(15, "Y0", None), (14, "Y1", None), (13, "Y2", "nc"), (12, "Y3", "nc"), (11, "Y4", "nc"),
              (10, "Y5", "nc"), (9, "Y6", "nc"), (7, "Y7", "nc")]
    p.ic("IC10", x, y, 80, 90, links=links, rechts=rechts, oben=[(16, "VCC", None)], unten=[(8, "GND", None)],
         titel="IC10", typ="74LS137")
    p.vcc(x - 10, zeile(y, 0))
    for i, nm in ((1, "A5"), (2, "A6"), (3, "A7"), (4, "/CS_IO")):
        p.draht((x - 10, zeile(y, i)), (x - 16, zeile(y, i)))
        p.fahne(x - 16, zeile(y, i), nm, rechts=False)
    p.gnd(x - 10, zeile(y, 5))
    for i, nm in ((0, "/CS_ACIA"), (1, "/CS_VIA")):
        p.draht((x + 90, zeile(y, i)), (x + 96, zeile(y, i)))
        p.fahne(x + 96, zeile(y, i), nm)
    p.vcc(x + 40, y - 10)
    p.gnd(x + 40, y + 100)
    # ACIA: nur /CS1, jetzt vom Dekoder
    p.ic("IC5", 420, 40, 80, 30, links=[(3, "/CS1", None)], titel="IC5", typ="6551")
    p.draht((x + 90, zeile(y, 0)), (x + 96, zeile(y, 0)))
    p.fahne(380, zeile(40, 0), "/CS_ACIA", rechts=False)
    p.draht((410, zeile(40, 0)), (380, zeile(40, 0)))
    p.kondensator("C13", 330, 8, "100 nF", laenge=15)
    p.vcc(330, -7)
    p.gnd(330, 23)
    # VIA
    xr, h = via_symbol(p, 150, 150)
    y8 = zeile(150, 8)
    p.draht((xr, y8), (xr + 20, y8))
    p.widerstand("R10", xr + 40, y8, "270 Ω", senkrecht=False, beschr="oben")
    p.draht((xr + 60, y8), (xr + 60, y8 + 10))
    p.led("D1", xr + 60, y8 + 30)
    p.gnd(xr + 60, y8 + 50)
    p.kondensator("C14", xr + 90, 150 + 30, "100 nF", laenge=15)
    p.vcc(xr + 90, 150 + 15)
    p.gnd(xr + 90, 150 + 45)
    return p


def lcd():
    p = Plan()
    # VIA Port A (Ausschnitt)
    p.ic("IC9", 20, 0, 100, 90, rechts=[(2 + k, f"PA{k}", None) for k in range(8)], titel="IC9", typ="6522")
    for k in range(7):
        y = zeile(0, k)
        p.draht((130, y), (136, y))
        p.fahne(136, y, f"PA{k}")
    # PA7: Leuchtdiode über 270 Ω
    y7 = zeile(0, 7)
    p.draht((130, y7), (150, y7))
    p.widerstand("R10", 170, y7, "270 Ω", senkrecht=False, beschr="oben")
    p.draht((190, y7), (190, y7 + 10))
    p.led("D1", 190, y7 + 30)
    p.gnd(190, y7 + 50)
    # Display-Anschluss JP2: links Signale, rechts Versorgung
    xj = 250
    links = [(1, "D7", None), (2, "D6", None), (3, "D5", None), (4, "D4", None), (5, "D3", "nc"), (6, "D2", "nc"),
             (7, "D1", "nc"), (8, "D0", "nc"), (9, "E1", None), (11, "RS", None), (15, "E2", None)]
    rechts = [(14, "VDD", None), (17, "LED+", None), (12, "V0", None), (10, "R/W", None), (13, "VSS", None),
              (18, "LED−", None), (16, "", "nc")]
    p.ic("JP2", xj, 0, 100, 120, links=links, rechts=rechts, titel="JP2", typ="LCD")
    zuordnung = {0: "PA3", 1: "PA2", 2: "PA1", 3: "PA0", 8: "PA5", 9: "PA4", 10: "PA6"}
    for i, nm in zuordnung.items():
        y = zeile(0, i)
        p.draht((xj - 10, y), (xj - 16, y))
        p.fahne(xj - 16, y, nm, rechts=False)
    xr = xj + 110
    p.vcc(xr, zeile(0, 0))
    # Hintergrundbeleuchtung
    y1 = zeile(0, 1)
    p.widerstand("R11", xr + 40, y1 - 20, "150 Ω", pins=("2", "1"))
    p.draht((xr, y1), (xr + 40, y1))
    p.vcc(xr + 40, y1 - 40)
    # Kontrast
    y2 = zeile(0, 2)
    p.poti("R12", xr + 80, y2, "10 kΩ")
    p.draht((xr, y2), (xr + 58, y2))
    p.vcc(xr + 80, y2 - 20)
    p.gnd(xr + 80, y2 + 20)
    # GND: R/W, VSS, LED-
    y3, y5 = zeile(0, 3), zeile(0, 5)
    p.draht((xr, y3), (xr + 14, y3), (xr + 14, y5), (xr, y5))
    p.draht((xr, zeile(0, 4)), (xr + 14, zeile(0, 4)))
    p.knoten(xr + 14, zeile(0, 4))
    p.gnd(xr + 14, y5)
    return p


def main():
    plaene = (
        ("sp-via", via, "Schaltplan: Dekoder, VIA und LED", ["bb-dekoder137", "bb-acia-137", "bb-via"]),
        ("sp-lcd", lcd, "Schaltplan: Display-Anschluss am VIA", ["bb-via-lcd", "bb-lcd"]),
    )
    figuren = z3.alle()
    for name, fn, titel, bbs in plaene:
        plan = fn()
        for b in bbs:
            n = vergleiche(plan, figuren[b][0])
            print(f"  {name} ~ {b}: {n} gemeinsame Anschlüsse stimmen")
        (OUT / f"{name}.svg").write_text(plan.svg(titel), encoding="utf-8")
        print(f"{name}.svg geschrieben")


if __name__ == "__main__":
    main()
