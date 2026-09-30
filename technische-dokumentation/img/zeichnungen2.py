#!/usr/bin/env python3
"""Steckbrett-Abbildungen der Kapitel 4 bis 6 (Speicher, serielle Schnittstelle, Adressdekodierung).

Ab Kapitel 4 sind die Bretter nicht mehr alle auf einer Zeichnung: jedes Kapitel
zeigt die neu bestückten Bretter. Verbindungen zu den anderen Brettern laufen über
kurze Drähte mit Signalnamen (Stummel). Gleichnamige Stummel werden verbunden.

  bb-takt-modul.svg    Brett 1 mit Oszillator-Baustein (Kapitel 4)
  bb-eeprom.svg        Brett 3: EEPROM (Kapitel 4)
  bb-eeprom-cs.svg     Brett 3: EEPROM mit Chip-Select (Kapitel 5)
  bb-inverter.svg      Brett 1, Ausschnitt: Inverter für A15 (Kapitel 5)
  bb-acia.svg          Brett 4: ACIA (Kapitel 5)
  bb-acia-io.svg       Brett 4: ACIA, Chip-Select von /CS_IO (Kapitel 6)
  bb-dekoder.svg       Brett 5: 74LS30 und 74LS00 (Kapitel 6)
  bb-sram.svg          Brett 6: SRAM (Kapitel 6)
  bb-inverter-ram.svg  Brett 1, Ausschnitt: zweiter Inverter (Kapitel 6)

Jede Zeichnung wird gegen ihre Netzliste geprüft (breadboard.py).
Aufruf: python3 technische-dokumentation/img/zeichnungen2.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from breadboard import (Steckbrett, ROT, SCHWARZ, GRUEN, GELB, BLAU)  # noqa: E402
import signale  # noqa: E402

OUT = Path(__file__).resolve().parent
FARBE = {"adresse": GRUEN, "daten": BLAU, "steuer": GELB}
ZUSATZ = dict(extra_links=46, extra_oben=40, extra_unten=40)


def farbe(signal):
    return FARBE[signale.gruppe(signal)]


class Netze:
    def __init__(self):
        self.n = {}

    def __call__(self, name, *pins):
        self.n.setdefault(name, set()).update(pins)

    def liste(self):
        return list(self.n.values())


def strom(bb, b, netze, bruecken=True):
    """Zuleitung von links (von einem anderen Brett) und Brücken zu den unteren Schienen."""
    y1, y2 = b.xy(1, "T+")[1], b.xy(1, "T-")[1]
    bb.draht((-30, y1, "ext:+5V"), (b, 1, "T+"), ROT, name="+5V")
    bb.draht((-30, y2, "ext:GND"), (b, 1, "T-"), SCHWARZ, name="GND")
    bb.beschriftung("+5 V", -33, y1 + 2.2, 6.5, "end", ROT, 700)
    bb.beschriftung("GND", -33, y2 + 2.2, 6.5, "end", SCHWARZ, 700)
    if bruecken:
        bb.draht((b, 2, "T+"), (b, 2, "B+"), ROT, name="Brücke+")
        bb.draht((b, 3, "T-"), (b, 3, "B-"), SCHWARZ, name="Brücke-")
    netze("VCC", "ext:+5V")
    netze("GND", "ext:GND")


# ------------------------------------------------------------ Brett 1
def takt_modul(inverter_a=False, inverter_e=False):
    """Takt und Reset mit Oszillator-Baustein (Brett 1 ab Kapitel 4)."""
    bb = Steckbrett()
    b = bb.brett(0, 0, 37)
    n = Netze()
    strom(bb, b, n)
    # IC1 74LS04: nur noch Gatter D (Reset) gebraucht
    bb.ic("IC1", b, 5, 14, "74LS04")
    bb.draht((b, 5, "j"), (b, 5, "T+"), ROT, name="IC1 VCC")
    bb.draht((b, 11, "a"), (b, 11, "B-"), SCHWARZ, name="IC1 GND")
    bb.keramik("C2", b, (13, "T+"), (13, "T-"), "100n")
    n("VCC", "IC1.14", "C2.1")
    n("GND", "IC1.7", "C2.2")
    # NE555 mit Reset-Schaltung
    bb.ic("IC2", b, 16, 8, "NE555")
    bb.draht((b, 16, "j"), (b, 16, "T+"), ROT, name="IC2 VCC")
    bb.draht((b, 19, "a"), (b, 19, "B+"), ROT, name="IC2 /RES")
    bb.draht((b, 16, "a"), (b, 16, "B-"), SCHWARZ, name="IC2 GND")
    bb.draht((b, 17, "i"), (b, 18, "i"), GELB, name="6-7")
    bb.widerstand("R4", b, (17, "h"), (17, "T+"), "47k")
    bb.elko("C5", b, (18, "h"), (18, "T-"), "10u")
    bb.keramik("C3", b, (21, "T+"), (21, "T-"), "100n")
    n("VCC", "IC2.8", "IC2.4", "R4.2", "C3.1")
    n("GND", "IC2.1", "C5.-", "C3.2")
    n("THR", "IC2.6", "IC2.7", "R4.1", "C5.+")
    bb.taster("S1", b, 22)
    bb.draht((b, 17, "c"), (b, 22, "c"), BLAU, bogen=-7, name="TRIG")
    bb.draht((b, 24, "j"), (b, 24, "T-"), SCHWARZ, name="S1 GND")
    bb.widerstand("R3", b, (24, "c"), (24, "B+"), "1M")
    bb.keramik("C4", b, (22, "b"), (22, "B-"), "100n")
    n("TRIG", "IC2.2", "S1.1", "R3.1", "C4.1")
    n("VCC", "R3.2")
    n("GND", "S1.2", "C4.2")
    bb.draht((b, 18, "d"), (b, 10, "h"), GRUEN, bogen=10, name="OUT")
    n("OUT", "IC2.3", "IC1.9")
    bb.draht((b, 11, "i"), (b, 12, "i"), GELB, name="Pin 8 -> R5")
    bb.widerstand("R5", b, (12, "h"), (12, "T+"), "1k")
    n("VCC", "R5.2")
    n("RST", "IC1.8", "R5.1", "sig:/RESET")
    bb.stummel(b, 11, "j", "/RESET", GELB)
    # Oszillator-Baustein
    bb.oszillator("QG1", b, 28, "1 MHz")
    bb.draht((b, 28, "a"), (b, 28, "B-"), SCHWARZ, name="QG1 Pin 1")
    bb.draht((b, 34, "a"), (b, 34, "B-"), SCHWARZ, name="QG1 GND")
    bb.draht((b, 28, "j"), (b, 28, "T+"), ROT, name="QG1 VCC")
    bb.stummel(b, 34, "j", "CLK", GELB)
    n("VCC", "QG1.14")
    n("GND", "QG1.1", "QG1.7")
    n("CLK", "QG1.8", "sig:CLK")
    offen = [f"IC1.{k}" for k in (10, 11, 12, 13)] + ["IC2.5"]
    if inverter_a:
        bb.stummel(b, 5, "a", "A15", GRUEN)
        bb.stummel(b, 6, "a", "/CS_ROM", GELB)
        n("A15", "IC1.1", "sig:A15")
        n("CS_ROM", "IC1.2", "sig:/CS_ROM")
    else:
        offen += ["IC1.1", "IC1.2"]
    if inverter_e:
        bb.stummel(b, 8, "j", "/RAM", GELB)
        bb.stummel(b, 9, "j", "RAM", GELB)
        n("NRAM", "IC1.11", "sig:/RAM")
        n("RAM", "IC1.10", "sig:RAM")
        offen = [o for o in offen if o not in ("IC1.10", "IC1.11")]
    offen += [f"IC1.{k}" for k in (3, 4, 5, 6)]
    bb.pruefe(n.liste(), offen)
    return bb


# ----------------------------------------------------------- Speicher
def speicher(name, label, ce, we):
    """28-poliger Speicher auf eigenem Brett. ce: 'GND' oder Signalname (z. B. '/CS_ROM').
    we: 'VCC' oder Signalname."""
    bb = Steckbrett()
    b = bb.brett(0, 0, 22)
    n = Netze()
    strom(bb, b, n)
    bb.ic(name, b, 5, 28, label)
    bb.keramik("C7" if name == "IC4" else "C12", b, (21, "T+"), (21, "T-"), "100n")
    kond = "C7" if name == "IC4" else "C12"
    n("VCC", f"{name}.28", f"{kond}.1")
    n("GND", f"{name}.14", f"{kond}.2")
    bb.draht((b, 5, "j"), (b, 5, "T+"), ROT, name="VCC")
    bb.draht((b, 18, "a"), (b, 18, "B-"), SCHWARZ, name="GND")
    for pin, sig in signale.SPEICHER.items():
        if sig in ("GND", "VCC"):
            continue
        sp = 4 + pin if pin <= 14 else 5 + (28 - pin)
        ze = "a" if pin <= 14 else "j"
        if sig == "/CE" or sig == "/OE":
            if ce == "GND":
                bb.draht((b, sp, ze), (b, sp, "T-"), SCHWARZ, name=sig)
                n("GND", f"{name}.{pin}")
            else:
                bb.stummel(b, sp, ze, ce, GELB)
                n(ce, f"{name}.{pin}", "sig:" + ce)
        elif sig == "/WE":
            if we == "VCC":
                bb.draht((b, sp, ze), (b, sp, "T+"), ROT, name=sig)
                n("VCC", f"{name}.{pin}")
            else:
                bb.stummel(b, sp, ze, we, GELB)
                n(we, f"{name}.{pin}", "sig:" + we)
        else:
            bb.stummel(b, sp, ze, sig, farbe(sig))
            n(sig, f"{name}.{pin}", "sig:" + sig)
    bb.pruefe(n.liste())
    return bb


# --------------------------------------------------------------- ACIA
def acia(cs1):
    bb = Steckbrett()
    b = bb.brett(0, 0, 26)
    n = Netze()
    strom(bb, b, n)
    bb.ic("IC5", b, 5, 28, "6551")
    n("VCC", "IC5.15", "C9.1", "IC5.2")
    n("GND", "IC5.1", "IC5.9", "IC5.17", "IC5.16", "C9.2", "JP1.1", "C8.2")
    bb.keramik("C9", b, (24, "T+"), (24, "T-"), "100n")
    # Versorgung und feste Pegel
    bb.draht((b, 18, "j"), (b, 18, "T+"), ROT, name="VCC")          # Pin 15
    bb.draht((b, 5, "a"), (b, 5, "B-"), SCHWARZ, name="GND")         # Pin 1
    bb.draht((b, 6, "a"), (b, 6, "B+"), ROT, name="CS0")             # Pin 2
    bb.draht((b, 13, "a"), (b, 13, "B-"), SCHWARZ, name="CTS")       # Pin 9
    bb.draht((b, 16, "j"), (b, 16, "T-"), SCHWARZ, name="DSR")       # Pin 17
    bb.draht((b, 17, "j"), (b, 17, "T-"), SCHWARZ, name="DCD")       # Pin 16
    # Signale
    bb.stummel(b, 7, "a", cs1, FARBE["adresse"] if cs1 == "A15" else GELB)   # /CS1 Pin 3
    bb.stummel(b, 8, "a", "/RESET", GELB)                                     # /RES Pin 4
    bb.stummel(b, 17, "a", "A0", GRUEN)                                      # RS0 Pin 13
    bb.stummel(b, 18, "a", "A1", GRUEN)                                      # RS1 Pin 14
    bb.stummel(b, 5, "j", "R/W", GELB)                                       # Pin 28
    bb.stummel(b, 6, "j", "PHI2", GELB)                                      # Pin 27
    for d in range(8):
        pin = 18 + d
        bb.stummel(b, 5 + (28 - pin), "j", f"D{d}", BLAU)
        n(f"D{d}", f"IC5.{pin}", f"sig:D{d}")
    n("CS1", "IC5.3", "sig:" + cs1)
    n("RES", "IC5.4", "sig:/RESET")
    n("A0", "IC5.13", "sig:A0")
    n("A1", "IC5.14", "sig:A1")
    n("RW", "IC5.28", "sig:R/W")
    n("PHI2", "IC5.27", "sig:PHI2")
    # Quarz 1,8432 MHz und Kondensator 27 pF
    bb.quarz("Q2", b, (10, "c"), (11, "c"), "1,8432", unter=True)
    bb.keramik("C8", b, (11, "b"), (11, "B-"), "27p")
    n("XTAL1", "IC5.6", "Q2.1")
    n("XTAL2", "IC5.7", "Q2.2", "C8.1")
    # Stiftleiste zum USB-Seriell-Adapter: 1 GND, 2 TXD, 3 RXD
    bb.stiftleiste("JP1", b, 21, "d", 3, ("GND", "TXD", "RXD"))
    bb.draht((b, 21, "a"), (b, 21, "B-"), SCHWARZ, name="JP1 GND")
    bb.draht((b, 14, "c"), (b, 22, "c"), GRUEN, bogen=-5, name="TXD")
    bb.draht((b, 16, "b"), (b, 23, "b"), BLAU, bogen=-5, name="RXD")
    n("TXD", "IC5.10", "JP1.2")
    n("RXD", "IC5.12", "JP1.3")
    offen = ["IC5.5", "IC5.8", "IC5.11", "IC5.26"]
    bb.pruefe(n.liste(), offen)
    return bb


# ------------------------------------------------------------- Dekoder
def dekoder():
    bb = Steckbrett()
    b = bb.brett(0, 0, 27)
    n = Netze()
    strom(bb, b, n)
    # 74LS30: Pin 1..6 = A14..A9, 7 GND, 8 Y, 11 = A8, 12 = /CS_ROM, 14 VCC
    bb.ic("IC7", b, 5, 14, "74LS30")
    bb.draht((b, 5, "j"), (b, 5, "T+"), ROT, name="IC7 VCC")
    bb.draht((b, 11, "a"), (b, 11, "B-"), SCHWARZ, name="IC7 GND")
    for pin, sig in ((1, "A14"), (2, "A13"), (3, "A12"), (4, "A11"), (5, "A10"), (6, "A9")):
        bb.stummel(b, 4 + pin, "a", sig, GRUEN)
        n(sig, f"IC7.{pin}", "sig:" + sig)
    bb.stummel(b, 4 + (15 - 11), "j", "A8", GRUEN)          # Pin 11: Spalte 8
    n("A8", "IC7.11", "sig:A8")
    bb.stummel(b, 4 + (15 - 12), "j", "/CS_ROM", GELB)      # Pin 12: Spalte 7
    n("CSROM_a", "IC7.12", "sig:/CS_ROM")
    bb.stummel(b, 4 + (15 - 8), "j", "/CS_IO", GELB)        # Pin 8: Spalte 11
    n("CSIO_a", "IC7.8", "sig:/CS_IO")
    bb.keramik("C10", b, (13, "T+"), (13, "T-"), "100n")
    n("VCC", "IC7.14", "C10.1")
    n("GND", "IC7.7", "C10.2")
    # 74LS00: Gatter A (Pin 1, 2 -> 3), Gatter B (Pin 4, 5 -> 6)
    bb.ic("IC6", b, 16, 14, "74LS00")
    bb.draht((b, 16, "j"), (b, 16, "T+"), ROT, name="IC6 VCC")
    bb.draht((b, 22, "a"), (b, 22, "B-"), SCHWARZ, name="IC6 GND")
    namen = {1: "/CS_ROM", 2: "/CS_IO", 3: "/RAM", 4: "RAM", 5: "PHI2", 6: "/CS_RAM"}
    for pin, sig in namen.items():
        bb.stummel(b, 15 + pin, "a", sig, GELB)
        n(f"IC6_{pin}", f"IC6.{pin}", "sig:" + sig)
    bb.keramik("C11", b, (25, "T+"), (25, "T-"), "100n")
    n("VCC", "IC6.14", "C11.1")
    n("GND", "IC6.7", "C11.2")
    # gleichnamige Signale sind eine Leitung
    n2 = Netze()
    bb.pruefe(_zusammen(n.liste()), [f"IC7.{p}" for p in (9, 10, 13)] + [f"IC6.{p}" for p in (8, 9, 10, 11, 12, 13)])
    return bb


def _zusammen(netze):
    """Netze mit gleichem Signalnamen (sig:...) zu einem zusammenfassen."""
    ergebnis = []
    for g in netze:
        toks = {x for x in g if x.startswith("sig:")}
        for e in ergebnis:
            if toks & {x for x in e if x.startswith("sig:")}:
                e |= g
                break
        else:
            ergebnis.append(set(g))
    return ergebnis


TITEL = {
    "bb-takt-modul": "Takt und Reset mit Oszillator-Baustein",
    "bb-eeprom": "EEPROM AT28C256 auf dem Steckbrett",
    "bb-eeprom-cs": "EEPROM mit Chip-Select von /CS_ROM",
    "bb-inverter": "Inverter für A15 auf Brett 1",
    "bb-acia": "ACIA 6551 auf dem Steckbrett",
    "bb-acia-io": "ACIA 6551, Chip-Select von /CS_IO",
    "bb-dekoder": "Adressdekoder mit 74LS30 und 74LS00",
    "bb-sram": "SRAM 61256 auf dem Steckbrett",
    "bb-inverter-ram": "Zweiter Inverter auf Brett 1",
}


def alle():
    # Ausschnitt der Brett-1-Zeichnung: Spalten 1..15
    def ausschnitt(bb, bis_spalte, mit_unten=True):
        b = bb.bretter[0]
        x1 = b.xy(bis_spalte, "a")[0] + 12
        return (-52, -34, x1, 240)
    out = {}
    out["bb-takt-modul"] = (takt_modul(), dict(extra_links=46, extra_oben=26, extra_unten=26))
    out["bb-eeprom"] = (speicher("IC4", "AT28C256", "GND", "VCC"), ZUSATZ)
    out["bb-eeprom-cs"] = (speicher("IC4", "AT28C256", "/CS_ROM", "VCC"), ZUSATZ)
    bb = takt_modul(inverter_a=True)
    out["bb-inverter"] = (bb, dict(ausschnitt=ausschnitt(bb, 15)))
    out["bb-acia"] = (acia("A15"), ZUSATZ)
    out["bb-acia-io"] = (acia("/CS_IO"), ZUSATZ)
    out["bb-dekoder"] = (dekoder(), ZUSATZ)
    out["bb-sram"] = (speicher("IC8", "61256", "/CS_RAM", "R/W"), ZUSATZ)
    bb = takt_modul(inverter_a=True, inverter_e=True)
    out["bb-inverter-ram"] = (bb, dict(ausschnitt=ausschnitt(bb, 15)))
    return out


def main():
    for name, (bb, opt) in alle().items():
        (OUT / f"{name}.svg").write_text(bb.svg(titel=TITEL[name], beschr=TITEL[name], **opt), encoding="utf-8")
        print(f"{name}.svg geschrieben, Netzliste stimmt")


if __name__ == "__main__":
    main()
