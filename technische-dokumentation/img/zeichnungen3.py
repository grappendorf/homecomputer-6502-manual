#!/usr/bin/env python3
"""Steckbrett-Abbildungen der Kapitel 8 und 9 (Dekoder für die IO-Bausteine, VIA, LCD).

  bb-dekoder137.svg  Brett 7: 74LS137 (Kapitel 8)
  bb-acia-137.svg    Brett 4: ACIA, Chip-Select von /CS_ACIA (Kapitel 8)
  bb-via.svg         Brett 8: VIA 6522 mit LED (Kapitel 8)
  bb-via-lcd.svg     Brett 8: VIA mit Port A für das Display (Kapitel 9)
  bb-lcd.svg         Brett 9: Anschluss für das LCD (Kapitel 9)

Aufruf: python3 technische-dokumentation/img/zeichnungen3.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from breadboard import Steckbrett, ROT, SCHWARZ, GRUEN, GELB, BLAU  # noqa: E402
import zeichnungen2 as z2  # noqa: E402
from zeichnungen2 import Netze, strom, farbe, ZUSATZ  # noqa: E402

OUT = Path(__file__).resolve().parent

# 6522 VIA (DIP-40)
VIA = {1: "GND", 2: "PA0", 3: "PA1", 4: "PA2", 5: "PA3", 6: "PA4", 7: "PA5", 8: "PA6", 9: "PA7",
       10: "PB0", 11: "PB1", 12: "PB2", 13: "PB3", 14: "PB4", 15: "PB5", 16: "PB6", 17: "PB7",
       18: "CB1", 19: "CB2", 20: "VCC", 21: "/IRQ", 22: "R/W", 23: "/CS2", 24: "CS1", 25: "PHI2",
       26: "D7", 27: "D6", 28: "D5", 29: "D4", 30: "D3", 31: "D2", 32: "D1", 33: "D0", 34: "/RES",
       35: "RS3", 36: "RS2", 37: "RS1", 38: "RS0", 39: "CA2", 40: "CA1"}


def dekoder137(y2=False, y3=False):
    bb = Steckbrett()
    b = bb.brett(0, 0, 18)
    n = Netze()
    strom(bb, b, n)
    bb.ic("IC10", b, 5, 16, "74LS137")
    bb.keramik("C13", b, (15, "T+"), (15, "T-"), "100n")
    n("VCC", "C13.1")
    n("GND", "C13.2")
    # unten: Pin 1..8 = Spalte 5..12; oben: Pin 16..9 = Spalte 5..12
    bb.stummel(b, 5, "a", "A5", GRUEN)           # A
    bb.stummel(b, 6, "a", "A6", GRUEN)           # B
    bb.stummel(b, 7, "a", "A7", GRUEN)           # C
    bb.draht((b, 8, "a"), (b, 8, "B-"), SCHWARZ, name="/GL")        # Pin 4 an GND
    bb.stummel(b, 9, "a", "/CS_IO", GELB)        # /G2, Pin 5
    bb.draht((b, 10, "a"), (b, 10, "B+"), ROT, name="G1")           # Pin 6 an +5 V
    bb.draht((b, 12, "a"), (b, 12, "B-"), SCHWARZ, name="GND")      # Pin 8
    bb.draht((b, 5, "j"), (b, 5, "T+"), ROT, name="VCC")             # Pin 16
    bb.stummel(b, 6, "j", "/CS_ACIA", GELB)      # Y0, Pin 15
    bb.stummel(b, 7, "j", "/CS_VIA", GELB)       # Y1, Pin 14
    n("A5", "IC10.1", "sig:A5")
    n("A6", "IC10.2", "sig:A6")
    n("A7", "IC10.3", "sig:A7")
    n("GND", "IC10.4", "IC10.8")
    n("CS_IO", "IC10.5", "sig:/CS_IO")
    n("VCC", "IC10.6", "IC10.16")
    n("Y0", "IC10.15", "sig:/CS_ACIA")
    n("Y1", "IC10.14", "sig:/CS_VIA")
    offen = [f"IC10.{p}" for p in (7, 9, 10, 11, 12, 13)]
    if y2:
        bb.stummel(b, 8, "j", "/CS_VIA2", GELB)      # Y2, Pin 13
        n("Y2", "IC10.13", "sig:/CS_VIA2")
        offen.remove("IC10.13")
    if y3:
        bb.stummel(b, 9, "j", "/CS_SID", GELB)       # Y3, Pin 12
        n("Y3", "IC10.12", "sig:/CS_SID")
        offen.remove("IC10.12")
    bb.pruefe(n.liste(), offen)
    return bb


def via(lcd=False, tastatur=False):
    bb = Steckbrett()
    b = bb.brett(0, 0, 34)
    n = Netze()
    strom(bb, b, n)
    bb.ic("IC9", b, 4, 40, "6522")
    bb.keramik("C14", b, (26, "T+"), (26, "T-"), "100n")
    n("VCC", "C14.1", "IC9.20", "IC9.24")
    n("GND", "C14.2", "IC9.1")
    bot = lambda p: 3 + p        # noqa: E731  Spalte der Pins 1..20
    top = lambda p: 44 - p       # noqa: E731  Spalte der Pins 21..40
    bb.draht((b, bot(1), "a"), (b, bot(1), "B-"), SCHWARZ, name="GND")
    bb.draht((b, bot(20), "a"), (b, bot(20), "B+"), ROT, name="VCC")
    bb.draht((b, top(24), "j"), (b, top(24), "T+"), ROT, name="CS1")
    for pin, sig, fb in ((23, "/CS_VIA", GELB), (22, "R/W", GELB), (25, "PHI2", GELB), (34, "/RESET", GELB),
                         (35, "A3", GRUEN), (36, "A2", GRUEN), (37, "A1", GRUEN), (38, "A0", GRUEN)):
        bb.stummel(b, top(pin), "j", sig, fb)
        n(f"s{pin}", f"IC9.{pin}", "sig:" + sig)
    for d in range(8):
        pin = 33 - d
        bb.stummel(b, top(pin), "j", f"D{d}", BLAU)
        n(f"D{d}", f"IC9.{pin}", f"sig:D{d}")
    offen = ["IC9.21", "IC9.39", "IC9.40", "IC9.18", "IC9.19"]
    if lcd:
        for pin in range(2, 9):
            bb.stummel(b, bot(pin), "a", f"PA{pin - 2}", GELB)
            n(f"PA{pin - 2}", f"IC9.{pin}", f"sig:PA{pin - 2}")
        offen += ["IC9.9"] + [f"IC9.{p}" for p in range(11, 18)]
    else:
        offen += [f"IC9.{p}" for p in range(2, 10)] + [f"IC9.{p}" for p in range(11, 18)]
    # Leuchtdiode über 270 Ω: im Kapitel 8 an PB0 (Pin 10), ab Kapitel 9 an PA7 (Pin 9)
    led_pin, led_sig = (9, "PA7") if lcd else (10, "PB0")
    bb.draht((b, bot(led_pin), "b"), (b, 27, "b"), GELB, bogen=-6, name=led_sig)
    bb.widerstand("R10", b, (27, "c"), (31, "c"), "270")
    bb.led("D1", b, (31, "b"), (31, "B-"))
    n("LEDPIN", f"IC9.{led_pin}", "R10.1")
    n("LED", "R10.2", "D1.A")
    n("GND", "D1.K")
    if lcd:
        offen = [o for o in offen if o != "IC9.9"] + ["IC9.10"]
    else:
        offen = [o for o in offen if o != "IC9.10"]
    if tastatur:
        for pin in range(10, 16):
            bb.stummel(b, bot(pin), "a", f"R{pin - 2}", GELB)      # PB0..PB5 = Zeilen 8..13
            n(f"R{pin - 2}", f"IC9.{pin}", f"sig:R{pin - 2}")
        offen = [o for o in offen if o not in [f"IC9.{p}" for p in range(10, 16)]]
    bb.pruefe(n.liste(), offen)
    return bb


def lcd():
    bb = Steckbrett()
    b = bb.brett(0, 0, 30)
    n = Netze()
    strom(bb, b, n)
    labels = [str(k) for k in range(1, 19)]
    bb.stiftleiste("JP2", b, 5, "c", 18, labels)
    bb.lcd_modul(b, 5, 22, "c", -30, zeilen=("Welcome to the 6502 HomeComputer!", ">", "This is line 3.", ""), cursor=(1, 1))
    pin = lambda k: 4 + k        # noqa: E731
    sig = {1: "PA3", 2: "PA2", 3: "PA1", 4: "PA0", 9: "PA5", 11: "PA4", 15: "PA6"}
    for k, s in sig.items():
        bb.stummel(b, pin(k), "a", s, GELB)
        n(s, f"JP2.{k}", "sig:" + s)
    for k in (10, 13, 18):
        bb.draht((b, pin(k), "a"), (b, pin(k), "B-"), SCHWARZ, name=f"JP2.{k}")
        n("GND", f"JP2.{k}")
    bb.draht((b, pin(14), "a"), (b, pin(14), "B+"), ROT, name="JP2.14")
    n("VCC", "JP2.14")
    # Hintergrundbeleuchtung: 150 Ω von +5 V an Pin 17
    bb.widerstand("R11", b, (pin(17), "b"), (pin(17), "B+"), "150")
    n("LEDA", "JP2.17", "R11.1")
    n("VCC", "R11.2")
    # Kontrast: Trimmer 10 k zwischen +5 V und GND, Schleifer an Pin 12
    bb.trimmer("R12", b, 26, "c", "10k")
    bb.draht((b, 26, "a"), (b, 26, "B+"), ROT, name="R12.1")
    bb.draht((b, 28, "a"), (b, 28, "B-"), SCHWARZ, name="R12.3")
    bb.draht((b, 27, "d"), (b, pin(12), "d"), BLAU, bogen=-6, name="V0")
    n("VCC", "R12.1")
    n("GND", "R12.3")
    n("V0", "JP2.12", "R12.2")
    offen = [f"JP2.{k}" for k in (5, 6, 7, 8, 16)]
    bb.pruefe(n.liste(), offen)
    return bb


TITEL = {
    "bb-dekoder137": "Adressdekoder 74LS137 auf dem Steckbrett",
    "bb-acia-137": "ACIA mit Chip-Select von /CS_ACIA",
    "bb-via": "VIA 6522 mit Leuchtdiode auf dem Steckbrett",
    "bb-via-lcd": "VIA 6522 mit Port A für das Display",
    "bb-via-tast": "VIA 6522 mit Display und Tastaturzeilen",
    "bb-lcd": "Anschluss für das LCD auf dem Steckbrett",
}


def alle():
    return {
        "bb-dekoder137": (dekoder137(), ZUSATZ),
        "bb-acia-137": (z2.acia("/CS_ACIA"), ZUSATZ),
        "bb-via": (via(), ZUSATZ),
        "bb-via-lcd": (via(lcd=True), ZUSATZ),
        "bb-via-tast": (via(lcd=True, tastatur=True), ZUSATZ),
        "bb-lcd": (lcd(), dict(extra_links=46, extra_oben=262, extra_unten=40)),
    }


def main():
    for name, (bb, opt) in alle().items():
        (OUT / f"{name}.svg").write_text(bb.svg(titel=TITEL[name], beschr=TITEL[name], **opt), encoding="utf-8")
        print(f"{name}.svg geschrieben, Netzliste stimmt")


if __name__ == "__main__":
    main()
