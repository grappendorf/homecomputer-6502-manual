#!/usr/bin/env python3
"""Steckbrett-Abbildungen der Kapitel 10 bis 12 (Tastatur, Interrupts, SID).

  bb-dekoder137-via2.svg  Brett 7 mit Ausgang Y2 für das zweite VIA (Kapitel 10)
  bb-via2.svg             Brett 10: zweites VIA 6522 für die Tastatur (Kapitel 10)
  bb-via-tast.svg         Brett 8: Tastaturzeilen am ersten VIA (Kapitel 10; in zeichnungen3.py)
  bb-tastatur.svg         Brett 11: Anschluss der Tastatur (Kapitel 10)
  bb-nmi.svg              NMI-Taster (Kapitel 11)
  bb-dekoder137-sid.svg   Brett 7 mit Y2 und Y3 (Kapitel 12)
  bb-sid.svg              Brett 12: SID 8580 (Kapitel 12)
  bb-audio.svg            Brett 13: Ausgangsstufe des SID (Kapitel 12)

Aufruf: python3 technische-dokumentation/img/zeichnungen4.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from breadboard import Steckbrett, ROT, SCHWARZ, GRUEN, GELB, BLAU  # noqa: E402
from zeichnungen2 import Netze, strom, ZUSATZ  # noqa: E402
import zeichnungen3 as z3  # noqa: E402

OUT = Path(__file__).resolve().parent


def via2():
    bb = Steckbrett()
    b = bb.brett(0, 0, 28)
    n = Netze()
    strom(bb, b, n)
    bb.ic("IC11", b, 4, 40, "6522")
    bb.keramik("C15", b, (26, "T+"), (26, "T-"), "100n")
    n("VCC", "C15.1", "IC11.20", "IC11.24")
    n("GND", "C15.2", "IC11.1")
    bot = lambda p: 3 + p        # noqa: E731
    top = lambda p: 44 - p       # noqa: E731
    bb.draht((b, bot(1), "a"), (b, bot(1), "B-"), SCHWARZ, name="GND")
    bb.draht((b, bot(20), "a"), (b, bot(20), "B+"), ROT, name="VCC")
    bb.draht((b, top(24), "j"), (b, top(24), "T+"), ROT, name="CS1")
    for pin, sig, fb in ((23, "/CS_VIA2", GELB), (22, "R/W", GELB), (25, "PHI2", GELB), (34, "/RESET", GELB),
                         (35, "A3", GRUEN), (36, "A2", GRUEN), (37, "A1", GRUEN), (38, "A0", GRUEN)):
        bb.stummel(b, top(pin), "j", sig, fb)
        n(f"s{pin}", f"IC11.{pin}", "sig:" + sig)
    for d in range(8):
        pin = 33 - d
        bb.stummel(b, top(pin), "j", f"D{d}", BLAU)
        n(f"D{d}", f"IC11.{pin}", f"sig:D{d}")
    for k in range(8):                    # Port A = Spalten, Port B = Zeilen 0..7
        bb.stummel(b, bot(2 + k), "a", f"C{k}", GRUEN)
        n(f"C{k}", f"IC11.{2 + k}", f"sig:C{k}")
        bb.stummel(b, bot(10 + k), "a", f"R{k}", GELB)
        n(f"R{k}", f"IC11.{10 + k}", f"sig:R{k}")
    bb.pruefe(n.liste(), ["IC11.21", "IC11.39", "IC11.40", "IC11.18", "IC11.19"])
    return bb


def tastatur():
    bb = Steckbrett()
    b = bb.brett(0, 0, 31)
    n = Netze()
    strom(bb, b, n, bruecken=False)
    bb.stiftleiste("JP3", b, 5, "c", 22, [str(k) for k in range(1, 23)])
    xs, ypad = bb.tastatur_modul(b, 5, 26, -34)
    for k in range(1, 23):
        sig = f"R{14 - k}" if k <= 14 else f"C{22 - k}"
        col = 4 + k
        bb.draht((b, col, "d"), (xs[k - 1], ypad, "sig:" + sig), GELB if sig[0] == "R" else GRUEN, name=f"JP3.{k}")
        n(sig, f"JP3.{k}", "sig:" + sig)
    bb.pruefe(n.liste())
    return bb


def nmi():
    bb = Steckbrett()
    b = bb.brett(0, 0, 14)
    n = Netze()
    strom(bb, b, n)
    bb.taster("S2", b, 6)
    bb.stummel(b, 6, "a", "/NMI", GELB)
    bb.draht((b, 8, "j"), (b, 8, "T-"), SCHWARZ, name="S2 GND")
    n("NMI", "S2.1", "sig:/NMI")
    n("GND", "S2.2")
    bb.pruefe(n.liste())
    return bb


def sid():
    bb = Steckbrett()
    b = bb.brett(0, 0, 26)
    n = Netze()
    strom(bb, b, n)
    bb.ic("IC12", b, 5, 28, "8580")
    bot = lambda p: 4 + p        # noqa: E731
    top = lambda p: 5 + (28 - p)  # noqa: E731
    # Versorgung: +5 V an Pin 25, +9 V an Pin 28, GND an Pin 14
    bb.draht((b, top(25), "j"), (b, top(25), "T+"), ROT, name="VCC")
    bb.draht((-30, b.xy(1, "i")[1], "ext:+9V"), (b, top(28), "i"), ROT, name="+9V")
    bb.beschriftung("+9 V", -33, b.xy(1, "i")[1] + 2.2, 6.5, "end", ROT, 700)
    bb.draht((b, bot(14), "a"), (b, bot(14), "B-"), SCHWARZ, name="GND")
    bb.keramik("C16", b, (top(28), "j"), (top(28), "T-"), "100n")
    bb.keramik("C17", b, (24, "T+"), (24, "T-"), "100n")
    n("VCC", "IC12.25", "C17.1")
    n("GND", "IC12.14", "C17.2", "C16.2")
    n("V9", "IC12.28", "C16.1", "ext:+9V")
    # Filterkondensatoren 22 nF an CAP1 (Pin 1, 2) und CAP2 (Pin 3, 4)
    bb.keramik("C18", b, (bot(1), "a"), (bot(2), "a"), "22n")
    bb.keramik("C19", b, (bot(3), "a"), (bot(4), "a"), "22n")
    n("CAP1A", "IC12.1", "C18.1")
    n("CAP1B", "IC12.2", "C18.2")
    n("CAP2A", "IC12.3", "C19.1")
    n("CAP2B", "IC12.4", "C19.2")
    for pin, sig, fb in ((5, "/RESET", GELB), (6, "PHI2", GELB), (7, "R/W", GELB), (8, "/CS_SID", GELB)):
        bb.stummel(b, bot(pin), "a", sig, fb)
        n(f"s{pin}", f"IC12.{pin}", "sig:" + sig)
    for k in range(5):
        bb.stummel(b, bot(9 + k), "a", f"A{k}", GRUEN)
        n(f"A{k}", f"IC12.{9 + k}", f"sig:A{k}")
    for d in range(8):
        pin = 15 + d
        bb.stummel(b, top(pin), "j", f"D{d}", BLAU)
        n(f"D{d}", f"IC12.{pin}", f"sig:D{d}")
    bb.stummel(b, top(27), "j", "AUDIO", GELB)
    n("AUDIO", "IC12.27", "sig:AUDIO")
    bb.pruefe(n.liste(), ["IC12.23", "IC12.24", "IC12.26"])
    return bb


def audio():
    bb = Steckbrett()
    b = bb.brett(0, 0, 22)
    n = Netze()
    y1, y2 = b.xy(1, "T+")[1], b.xy(1, "T-")[1]
    bb.draht((-30, y1, "ext:+9V"), (b, 1, "T+"), ROT, name="+9V")
    bb.draht((-30, y2, "ext:GND"), (b, 1, "T-"), SCHWARZ, name="GND")
    bb.beschriftung("+9 V", -33, y1 + 2.2, 6.5, "end", ROT, 700)
    bb.beschriftung("GND", -33, y2 + 2.2, 6.5, "end", SCHWARZ, 700)
    bb.draht((b, 2, "T+"), (b, 2, "B+"), ROT, name="Brücke+")
    bb.draht((b, 3, "T-"), (b, 3, "B-"), SCHWARZ, name="Brücke-")
    n("V9", "ext:+9V")
    n("GND", "ext:GND")
    # AUDIO -> R13 nach Masse, Ferritperle, R14 zur Basis, C20 nach Masse
    bb.stummel(b, 5, "a", "AUDIO", GELB)
    bb.widerstand("R13", b, (5, "b"), (5, "B-"), "1k")
    bb.ferrit("FB1", b, (5, "c"), (9, "c"))
    bb.widerstand("R14", b, (9, "d"), (14, "d"), "10k")
    bb.keramik("C20", b, (14, "b"), (14, "B-"), "1n")
    bb.transistor("T1", b, 13, "e")
    bb.draht((b, 15, "a"), (b, 15, "B+"), ROT, name="Kollektor")
    bb.widerstand("R15", b, (13, "b"), (13, "B-"), "1k")
    bb.elko("C21", b, (13, "c"), (18, "c"), "10u")
    bb.stiftleiste("JP8", b, 18, "b", 2, ("OUT", "GND"))
    bb.draht((b, 19, "a"), (b, 19, "B-"), SCHWARZ, name="JP8 GND")
    n("AUDIO", "R13.1", "FB1.1", "sig:AUDIO")
    n("FB", "FB1.2", "R14.1")
    n("BASE", "R14.2", "T1.B", "C20.1")
    n("EMIT", "T1.E", "R15.1", "C21.+")
    n("V9", "T1.C")
    n("OUT", "C21.-", "JP8.1")
    n("GND", "R13.2", "C20.2", "R15.2", "JP8.2")
    bb.pruefe(n.liste())
    return bb


TITEL = {
    "bb-dekoder137-via2": "Dekoder mit Ausgang für das zweite VIA",
    "bb-dekoder137-sid": "Dekoder mit Ausgängen für das zweite VIA und den SID",
    "bb-via2": "Zweites VIA 6522 für die Tastatur",
    "bb-tastatur": "Tastatur am Steckbrett",
    "bb-nmi": "NMI-Taster auf dem Steckbrett",
    "bb-sid": "SID 8580 auf dem Steckbrett",
    "bb-audio": "Ausgangsstufe des SID auf dem Steckbrett",
}


def alle():
    z = {
        "bb-dekoder137-via2": (z3.dekoder137(y2=True), ZUSATZ),
        "bb-dekoder137-sid": (z3.dekoder137(y2=True, y3=True), ZUSATZ),
        "bb-via2": (via2(), ZUSATZ),
        "bb-tastatur": (tastatur(), dict(extra_links=46, extra_oben=130, extra_unten=10)),
        "bb-nmi": (nmi(), ZUSATZ),
        "bb-sid": (sid(), ZUSATZ),
        "bb-audio": (audio(), ZUSATZ),
    }
    z["bb-via-tast"] = z3.alle()["bb-via-tast"]
    return z


def main():
    for name, (bb, opt) in alle().items():
        if name == "bb-via-tast":
            continue
        (OUT / f"{name}.svg").write_text(bb.svg(titel=TITEL[name], beschr=TITEL[name], **opt), encoding="utf-8")
        print(f"{name}.svg geschrieben, Netzliste stimmt")


if __name__ == "__main__":
    main()
