#!/usr/bin/env python3
"""Schaltpläne der Kapitel 4 bis 6 im Stil des Buches:

  sp-eeprom.svg   Kapitel 4: Oszillator-Baustein und EEPROM
  sp-acia.svg     Kapitel 5: Adressdekodierung für das ROM und die ACIA
  sp-ram.svg      Kapitel 6: Adressdekoder, SRAM und ACIA im IO-Bereich

Jeder Schaltplan wird gegen die zugehörigen Steckbrett-Zeichnungen geprüft.
Aufruf: python3 technische-dokumentation/img/schaltplaene2.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schaltplan import Plan, vergleiche  # noqa: E402
import zeichnungen2 as z2  # noqa: E402
import signale  # noqa: E402

OUT = Path(__file__).resolve().parent

ADR_LINKS = [(10, "A0"), (9, "A1"), (8, "A2"), (7, "A3"), (6, "A4"), (5, "A5"), (4, "A6"), (3, "A7"),
             (25, "A8"), (24, "A9"), (21, "A10"), (23, "A11"), (2, "A12"), (26, "A13"), (1, "A14")]
DAT = [(11, "D0"), (12, "D1"), (13, "D2"), (15, "D3"), (16, "D4"), (17, "D5"), (18, "D6"), (19, "D7")]


def oszillator(p, x, y):
    p.ic("QG1", x, y, 80, 50, links=[(1, "TS", None)], rechts=[(8, "OUT", None)],
         oben=[(14, "VCC", None)], unten=[(7, "GND", None)], titel="QG1", typ="1 MHz")
    p.gnd(x - 10, y + 10)
    p.vcc(x + 40, y - 10)
    p.gnd(x + 40, y + 60)
    p.draht((x + 90, y + 10), (x + 96, y + 10))
    p.fahne(x + 96, y + 10, "CLK")


def speicher_voll(p, x, y, name, typ, ce_quelle, we_quelle):
    """Vollständiges 28-poliges Speichersymbol mit Adress- und Datenbus."""
    links = [(n, s, None) for n, s in ADR_LINKS]
    rechts = [(n, s, None) for n, s in DAT] + [None, None, (27, "/WE", None), (20, "/CE", None), (22, "/OE", None)]
    p.ic(name, x, y, 90, 160, links=links, rechts=rechts, oben=[(28, "VCC", None)], unten=[(14, "GND", None)],
         titel=name, typ=typ)
    # Busse
    pts = [(x - 10, y + 10 + i * 10) for i in range(15)]
    p.bus(x - 34, pts, [s for _, s in ADR_LINKS], "A0–A14", "links")
    pts = [(x + 100, y + 10 + i * 10) for i in range(8)]
    p.bus(x + 124, pts, [s for _, s in DAT], "D0–D7", "rechts")
    # /WE, /CE, /OE
    yw, yc, yo = y + 10 + 10 * 10, y + 10 + 11 * 10, y + 10 + 12 * 10
    xr = x + 112
    if we_quelle == "VCC":
        p.draht((x + 100, yw), (xr, yw))
        p.vcc(xr, yw)
    else:
        p.draht((x + 100, yw), (xr, yw))
        p.fahne(xr, yw, we_quelle)
    if ce_quelle == "GND":
        p.draht((x + 100, yc), (xr, yc), (xr, yo), (x + 100, yo))
        p.knoten(xr, yc)
        p.gnd(xr, yo)
    else:
        p.draht((x + 100, yc), (xr, yc), (xr, yo), (x + 100, yo))
        p.draht((xr, yc), (xr + 6, yc))
        p.fahne(xr + 6, yc, ce_quelle)
    # Versorgung
    p.vcc(x + 45, y - 10)
    p.gnd(x + 45, y + 170)


def eeprom():
    p = Plan()
    oszillator(p, 20, -80)
    speicher_voll(p, 150, 40, "IC4", "AT28C256", "GND", "VCC")
    # Kondensator
    p.kondensator("C7", 250, 12, "100 nF", laenge=15, beschr="rechts")
    p.vcc(250, -3)
    p.gnd(250, 27)
    return p


def acia_symbol(p, x, y, cs1):
    """6551. Gibt nichts zurück; zeichnet Kasten, Busse, Quarz, Stiftleiste."""
    links = [(2, "CS0", None), (3, "/CS1", None), (28, "R/W", None), (13, "RS0", None), (14, "RS1", None)]
    links += [(18 + d, f"D{d}", None) for d in range(8)]
    links += [(4, "/RES", None), (27, "PHI2", None), (26, "/IRQ", "nc")]
    rechts = [(12, "RxD", None), (10, "TxD", None), (11, "/DTR", "nc"), (8, "/RTS", "nc"), (9, "/CTS", None),
              (16, "/DCD", None), (17, "/DSR", None), (5, "RxC", "nc"), (6, "XTAL1", None), (7, "XTAL2", None)]
    bw = 100
    h = 10 + (len(links) - 1) * 10 + 10
    p.ic("IC5", x, y, bw, h, links=links, rechts=rechts, oben=[(15, "VCC", None)], unten=[(1, "GND", None)],
         titel="IC5", typ="6551")
    yl = lambda i: y + 10 + i * 10      # noqa: E731
    xl, xr = x - 10, x + bw + 10
    p.vcc(xl, yl(0))
    p.fahne(xl - 6, yl(1), cs1, rechts=False)
    p.draht((xl, yl(1)), (xl - 6, yl(1)))
    p.fahne(xl - 6, yl(2), "R/W", rechts=False)
    p.draht((xl, yl(2)), (xl - 6, yl(2)))
    p.fahne(xl - 6, yl(3), "A0", rechts=False)
    p.draht((xl, yl(3)), (xl - 6, yl(3)))
    p.fahne(xl - 6, yl(4), "A1", rechts=False)
    p.draht((xl, yl(4)), (xl - 6, yl(4)))
    p.bus(xl - 50, [(xl, yl(5 + d)) for d in range(8)], [f"D{d}" for d in range(8)], "D0–D7", "links")
    p.fahne(xl - 6, yl(13), "/RESET", rechts=False)
    p.draht((xl, yl(13)), (xl - 6, yl(13)))
    p.fahne(xl - 6, yl(14), "PHI2", rechts=False)
    p.draht((xl, yl(14)), (xl - 6, yl(14)))
    p.vcc(x + bw / 2, y - 10)
    p.gnd(x + bw / 2, y + h + 10)
    # Schnittstelle: JP1 (Pin 3 RXD oben, Pin 2 TXD, Pin 1 GND unten)
    jx = xr + 58
    p.ic("JP1", jx, y, 56, 40, links=[(3, "RXD", None), (2, "TXD", None), (1, "GND", None)], titel="JP1", abstand=10)
    p.draht((xr, yl(0)), (jx - 10, yl(0)))
    p.draht((xr, yl(1)), (jx - 10, yl(1)))
    p.gnd(jx - 10, yl(2))
    # /CTS, /DCD, /DSR an GND
    rx = xr + 14
    p.draht((xr, yl(4)), (rx, yl(4)), (rx, yl(6)), (xr, yl(6)))
    p.draht((xr, yl(5)), (rx, yl(5)))
    p.knoten(rx, yl(5))
    p.gnd(rx, yl(6))
    # Quarz 1,8432 MHz zwischen XTAL1 und XTAL2, 27 pF von XTAL2 nach Masse
    xq = xr + 40
    p.draht((xr, yl(8)), (xq, yl(8)))
    p.quarz("Q2", xq, yl(8) + 20, "1,8432 MHz", senkrecht=True)
    p.draht((xr, yl(9)), (xr + 14, yl(9)), (xr + 14, yl(8) + 40), (xq, yl(8) + 40))
    p.draht((xq, yl(8) + 40), (xq + 36, yl(8) + 40))
    p.kondensator("C8", xq + 36, yl(8) + 60, "27 pF", beschr="rechts")
    p.gnd(xq + 36, yl(8) + 80)
    # Abblockkondensator
    p.kondensator("C9", x + bw + 90, y - 50, "100 nF", laenge=15)
    p.vcc(x + bw + 90, y - 65)
    p.gnd(x + bw + 90, y - 35)


def acia():
    p = Plan()
    # Inverter A15 -> /CS_ROM und ROM
    p.fahne(-10, 20, "A15", rechts=False)
    p.draht((-10, 20), (20, 20))
    p.inverter("IC1A", 50, 20, 1, 2, "IC1", "74LS04")
    p.draht((80, 20), (100, 20))
    p.fahne(100, 20, "/CS_ROM")
    # ROM, nur Chip-Select
    p.ic("IC4", 200, 0, 100, 40, links=[(20, "/CE", None), (22, "/OE", None)], titel="IC4", typ="AT28C256")
    p.fahne(165, 10, "/CS_ROM", rechts=False)
    p.draht((190, 10), (165, 10))
    p.draht((180, 10), (180, 20), (190, 20))
    p.knoten(180, 10)
    acia_symbol(p, 150, 110, "A15")
    return p


def ram():
    p = Plan()
    # 74LS30: A14..A8 und /CS_ROM -> /CS_IO
    eing = [(1, "A14"), (2, "A13"), (3, "A12"), (4, "A11"), (5, "A10"), (6, "A9"), (11, "A8"), (12, "/CS_ROM")]
    x7, y7 = 120, 0
    for i, (pin, nm) in enumerate(eing):
        p.fahne(x7 - 16, y7 + 10 + i * 10, nm, rechts=False)
        p.draht((x7 - 16, y7 + 10 + i * 10), (x7 - 10, y7 + 10 + i * 10))
    ausg = p.nand("IC7", x7, y7, eing, 8, "IC7", "74LS30")
    # /CS_IO
    p.draht(ausg, (ausg[0] + 14, ausg[1]))
    p.fahne(ausg[0] + 14, ausg[1], "/CS_IO")
    # 74LS00 Gatter A: /CS_ROM, /CS_IO -> /RAM
    ya = 130
    p.fahne(84, ya + 10, "/CS_ROM", rechts=False)
    p.draht((84, ya + 10), (110, ya + 10))
    p.fahne(84, ya + 20, "/CS_IO", rechts=False)
    p.draht((84, ya + 20), (110, ya + 20))
    oa = p.nand("IC6A", 120, ya, [(1, ""), (2, "")], 3, "IC6", "74LS00")
    p.draht(oa, (oa[0] + 20, oa[1]))
    p.netzname(oa[0] + 6, oa[1], "/RAM", dy=-4)
    # Inverter E: /RAM -> RAM
    p.inverter("IC1E", oa[0] + 50, oa[1], 11, 10, "IC1", "")
    p.draht((oa[0] + 20, oa[1]), (oa[0] + 20, oa[1]))
    p.draht(oa, (oa[0] + 20, oa[1]))
    # Gatter B
    yb = 190
    ob = p.nand("IC6B", 260, yb, [(4, ""), (5, "")], 6, "IC6", "")
    p.draht((oa[0] + 80, oa[1]), (244, oa[1]), (244, yb + 10), (250, yb + 10))
    p.netzname(oa[0] + 84, oa[1], "RAM", dy=-4)
    p.fahne(236, yb + 20, "PHI2", rechts=False)
    p.draht((236, yb + 20), (250, yb + 20))
    p.draht(ob, (ob[0] + 14, ob[1]))
    p.fahne(ob[0] + 14, ob[1], "/CS_RAM")
    # SRAM, nur Chip-Select und /WE
    p.ic("IC8", 340, 270, 80, 50, links=[(20, "/CE", None), (22, "/OE", None), (27, "/WE", None)], titel="IC8", typ="61256",
         abstand=10, versatz=10)
    p.fahne(308, 280, "/CS_RAM", rechts=False)
    p.draht((330, 280), (308, 280))
    p.draht((318, 280), (318, 290), (330, 290))
    p.knoten(318, 280)
    p.fahne(308, 300, "R/W", rechts=False)
    p.draht((330, 300), (308, 300))
    # ACIA nur /CS1
    p.ic("IC5", 340, 340, 80, 30, links=[(3, "/CS1", None)], titel="IC5", typ="6551")
    p.fahne(308, 350, "/CS_IO", rechts=False)
    p.draht((330, 350), (308, 350))
    # Stromversorgung der Bausteine
    p.versorgung(300, 20, "IC7", 14, 7, "C10", "100 nF")
    p.versorgung(300, 100, "IC6", 14, 7, "C11", "100 nF")
    p.versorgung(470, 270, "IC8", 28, 14, "C12", "100 nF")
    return p


def main():
    plaene = (
        ("sp-eeprom", eeprom, "Schaltplan: Oszillator und EEPROM", ["bb-takt-modul", "bb-eeprom"]),
        ("sp-acia", acia, "Schaltplan: Adressdekodierung und ACIA", ["bb-eeprom-cs", "bb-inverter", "bb-acia"]),
        ("sp-ram", ram, "Schaltplan: Adressdekoder und SRAM", ["bb-dekoder", "bb-sram", "bb-acia-io", "bb-inverter-ram"]),
    )
    figuren = z2.alle()
    for name, fn, titel, bbs in plaene:
        plan = fn()
        for b in bbs:
            n = vergleiche(plan, figuren[b][0])
            print(f"  {name} ~ {b}: {n} gemeinsame Anschlüsse stimmen")
        (OUT / f"{name}.svg").write_text(plan.svg(titel), encoding="utf-8")
        print(f"{name}.svg geschrieben")


if __name__ == "__main__":
    main()
