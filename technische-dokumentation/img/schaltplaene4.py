#!/usr/bin/env python3
"""Schaltpläne der Kapitel 10 bis 12 im Stil des Buches:

  sp-tastatur.svg  Kapitel 10: zweites VIA, Tastaturanschluss, Tastaturzeilen am ersten VIA
  sp-irq.svg       Kapitel 11: gemeinsame IRQ-Leitung und NMI-Taster
  sp-sid.svg       Kapitel 12: SID mit Ausgangsstufe

Jeder Schaltplan wird gegen die zugehörigen Steckbrett-Zeichnungen geprüft.
Aufruf: python3 technische-dokumentation/img/schaltplaene4.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schaltplan import Plan, vergleiche  # noqa: E402
import zeichnungen4 as z4  # noqa: E402

OUT = Path(__file__).resolve().parent


def zeile(y0, i):
    return y0 + 10 + i * 10


def via2_symbol(p, x, y):
    """Zweites VIA mit Tastaturleitungen als Flaggen C0..C7 (Port A) und R0..R7 (Port B)."""
    links = [(24, "CS1", None), (23, "/CS2", None), (22, "R/W", None), (25, "PHI2", None), (34, "/RES", None),
             (38, "RS0", None), (37, "RS1", None), (36, "RS2", None), (35, "RS3", None)]
    links += [(33 - d, f"D{d}", None) for d in range(8)]
    links += [(21, "/IRQ", "nc"), (40, "CA1", "nc"), (39, "CA2", "nc")]
    rechts = [(2 + k, f"PA{k}", None) for k in range(8)] + [(10 + k, f"PB{k}", None) for k in range(8)]
    rechts += [(18, "CB1", "nc"), (19, "CB2", "nc")]
    h = 10 + 19 * 10 + 10
    bw = 110
    p.ic("IC11", x, y, bw, h, links=links, rechts=rechts, oben=[(20, "VCC", None)], unten=[(1, "GND", None)],
         titel="IC11", typ="6522")
    xl, xr = x - 10, x + bw + 10
    p.vcc(xl, zeile(y, 0))
    for i, nm in ((1, "/CS_VIA2"), (2, "R/W"), (3, "PHI2"), (4, "/RESET"), (5, "A0"), (6, "A1"), (7, "A2"), (8, "A3")):
        p.draht((xl, zeile(y, i)), (xl - 6, zeile(y, i)))
        p.fahne(xl - 6, zeile(y, i), nm, rechts=False)
    p.bus(xl - 50, [(xl, zeile(y, 9 + d)) for d in range(8)], [f"D{d}" for d in range(8)], "D0–D7", "links")
    for k in range(8):
        p.draht((xr, zeile(y, k)), (xr + 6, zeile(y, k)))
        p.fahne(xr + 6, zeile(y, k), f"C{k}")
        p.draht((xr, zeile(y, 8 + k)), (xr + 6, zeile(y, 8 + k)))
        p.fahne(xr + 6, zeile(y, 8 + k), f"R{k}")
    p.vcc(x + bw / 2, y - 10)
    p.gnd(x + bw / 2, y + h + 10)
    return h


def tastatur():
    p = Plan()
    # Dekoder: nur Y2
    p.ic("IC10", 150, 0, 80, 30, rechts=[(13, "Y2", None)], titel="IC10", typ="74LS137")
    p.draht((240, zeile(0, 0)), (246, zeile(0, 0)))
    p.fahne(246, zeile(0, 0), "/CS_VIA2")
    # VIA2
    via2_symbol(p, 150, 70)
    # Tastaturanschluss JP3
    xj = 470
    pins = [(k, f"R{14 - k}" if k <= 14 else f"C{22 - k}", None) for k in range(1, 23)]
    p.ic("JP3", xj, 70, 70, 10 + 21 * 10 + 10, links=[(k, nm, a) for k, nm, a in pins], titel="JP3", typ="Tastatur")
    for i, (k, nm, _a) in enumerate(pins):
        y = zeile(70, i)
        p.draht((xj - 10, y), (xj - 16, y))
        p.fahne(xj - 16, y, nm, rechts=False)
    # VIA1: Port B als Zeilen 8..13
    p.ic("IC9", 150, 330, 110, 70, rechts=[(10 + k, f"PB{k}", None) for k in range(6)], titel="IC9", typ="6522")
    for k in range(6):
        y = zeile(330, k)
        p.draht((270, y), (276, y))
        p.fahne(276, y, f"R{8 + k}")
    p.kondensator("C15", 330, 40, "100 nF", laenge=15)
    p.vcc(330, 25)
    p.gnd(330, 55)
    return p


def irq():
    p = Plan()
    # Drei Quellen an einer gemeinsamen Leitung (wired-OR)
    quellen = [("IC5", "ACIA 6551", 26), ("IC9", "VIA 1", 21), ("IC11", "VIA 2", 21)]
    xs = 20
    for i, (nm, typ, pin) in enumerate(quellen):
        y = 10 + i * 50
        p.ic(nm, xs, y, 90, 30, rechts=[(pin, "/IRQ", None)], titel=nm, typ=typ)
        p.draht((xs + 100, y + 20), (xs + 130, y + 20))
    xb = xs + 130
    p.draht((xb, 30), (xb, 130))
    p.knoten(xb, 80)
    p.draht((xb, 80), (xb + 24, 80))
    p.fahne(xb + 24, 80, "/IRQ")
    # Prozessor mit Pull-up-Widerständen und NMI-Taster
    xc = 330
    p.ic("IC3", xc, 0, 90, 40, links=[(4, "/IRQ", None), (6, "/NMI", None)], titel="IC3", typ="6502")
    for i, nm in ((0, "/IRQ"), (1, "/NMI")):
        p.draht((xc - 10, zeile(0, i)), (xc - 16, zeile(0, i)))
        p.fahne(xc - 16, zeile(0, i), nm, rechts=False)
    p.widerstand("R9", 280, 110, "3k3", pins=("2", "1"), beschr="links")
    p.vcc(280, 90)
    p.fahne(280, 130, "/IRQ", rechts=False)
    p.widerstand("R8", 360, 110, "3k3", pins=("2", "1"))
    p.vcc(360, 90)
    p.fahne(360, 130, "/NMI")
    p.taster("S2", 440, 130, "NMI", pins=("1", "2"))
    p.fahne(440, 110, "/NMI", rechts=False)
    p.gnd(440, 150)
    return p


def sid():
    p = Plan()
    links = [(5, "/RES", None), (6, "φ2", None), (7, "R/W", None), (8, "/CS", None)]
    links += [(9 + k, f"A{k}", None) for k in range(5)]
    links += [(15 + d, f"D{d}", None) for d in range(8)]
    rechts = [(1, "CAP1A", None), None, (2, "CAP1B", None), None, (3, "CAP2A", None), None, (4, "CAP2B", None),
              (26, "EXT IN", "nc"), (24, "POTX", "nc"), (23, "POTY", "nc")]
    x, y, bw = 150, 0, 110
    h = 10 + 16 * 10 + 10
    p.ic("IC12", x, y, bw, h, links=links, rechts=rechts, oben=[(28, "V12", None), None, (25, "VCC", None)],
         unten=[(14, "GND", None), None, (27, "AUDIO", None)], titel="IC12", typ="8580")
    xl, xr = x - 10, x + bw + 10
    for i, nm in enumerate(("/RESET", "PHI2", "R/W", "/CS_SID")):
        p.draht((xl, zeile(y, i)), (xl - 6, zeile(y, i)))
        p.fahne(xl - 6, zeile(y, i), nm, rechts=False)
    for k in range(5):
        p.draht((xl, zeile(y, 4 + k)), (xl - 6, zeile(y, 4 + k)))
        p.fahne(xl - 6, zeile(y, 4 + k), f"A{k}", rechts=False)
    p.bus(xl - 50, [(xl, zeile(y, 9 + d)) for d in range(8)], [f"D{d}" for d in range(8)], "D0–D7", "links")
    # Versorgung
    p.vcc9(x + bw / 2 - 20, y - 10)
    p.vcc(x + bw / 2 + 20, y - 10)
    p.gnd(x + bw / 2 - 20, y + h + 10)
    p.kondensator("C16", xr + 90, 20, "100 nF", laenge=15)
    p.vcc9(xr + 90, 5)
    p.gnd(xr + 90, 35)
    p.kondensator("C17", xr + 150, 20, "100 nF", laenge=15)
    p.vcc(xr + 150, 5)
    p.gnd(xr + 150, 35)
    # Filterkondensatoren
    for nm, (r1, r2) in (("C18", (0, 2)), ("C19", (4, 6))):
        ya, yb = zeile(y, r1), zeile(y, r2)
        p.draht((xr, ya), (xr + 40, ya))
        p.draht((xr, yb), (xr + 40, yb))
        p.kondensator(nm, xr + 40, (ya + yb) / 2, "22 nF", laenge=10)
    # Dekoder: nur Y3
    p.ic("IC10", x - 150, -80, 80, 30, rechts=[(12, "Y3", None)], titel="IC10", typ="74LS137")
    p.draht((x - 60, zeile(-80, 0)), (x - 54, zeile(-80, 0)))
    p.fahne(x - 54, zeile(-80, 0), "/CS_SID")
    # Ausgangsstufe unter dem Baustein
    ya = y + h + 70
    xa = x + bw / 2 + 20
    p.draht((xa, y + h + 10), (xa, ya))
    p.widerstand("R13", xa, ya + 30, "1 kΩ", beschr="links")
    p.draht((xa, ya), (xa, ya + 10))
    p.gnd(xa, ya + 50)
    p.ferrit("FB1", xa + 20, ya, "")
    p.widerstand("R14", xa + 60, ya, "10 kΩ", senkrecht=False, beschr="oben")
    xbase = xa + 80
    p.knoten(xa, ya)
    p.draht((xbase, ya), (xbase, ya + 10))
    p.kondensator("C20", xbase, ya + 30, "1 nF", beschr="links")
    p.gnd(xbase, ya + 50)
    p.knoten(xbase, ya)
    p.npn("T1", xbase + 24, ya)
    p.vcc9(xbase + 36, ya - 24)
    p.draht((xbase + 36, ya + 24), (xbase + 36, ya + 34))
    p.widerstand("R15", xbase + 36, ya + 54, "1 kΩ")
    p.gnd(xbase + 36, ya + 74)
    xe = xbase + 70
    p.draht((xbase + 36, ya + 24), (xe, ya + 24))
    p.knoten(xbase + 36, ya + 24)
    p.kondensator("C21", xe, ya + 44, "10 µF", elko=True, pins=("+", "-"), laenge=20)
    p.draht((xe, ya + 64), (xe + 10, ya + 64))
    p.ic("JP8", xe + 20, ya + 54, 56, 30, links=[(1, "OUT", None), (2, "GND", None)], titel="")
    p.text("JP8", xe + 48, ya + 50, 8.5, "middle", "#2A2826", 700)
    p.gnd(xe + 10, ya + 74)
    return p


def main():
    plaene = (
        ("sp-tastatur", tastatur, "Schaltplan: Tastatur am VIA",
         ["bb-dekoder137-via2", "bb-via2", "bb-via-tast", "bb-tastatur"]),
        ("sp-irq", irq, "Schaltplan: Interrupt-Leitung und NMI-Taster", ["bb-nmi"]),
        ("sp-sid", sid, "Schaltplan: SID mit Ausgangsstufe", ["bb-sid", "bb-audio", "bb-dekoder137-sid"]),
    )
    figuren = z4.alle()
    for name, fn, titel, bbs in plaene:
        plan = fn()
        for b in bbs:
            n = vergleiche(plan, figuren[b][0])
            print(f"  {name} ~ {b}: {n} gemeinsame Anschlüsse stimmen")
        (OUT / f"{name}.svg").write_text(plan.svg(titel), encoding="utf-8")
        print(f"{name}.svg geschrieben")


if __name__ == "__main__":
    main()
