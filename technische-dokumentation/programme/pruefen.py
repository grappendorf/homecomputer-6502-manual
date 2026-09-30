#!/usr/bin/env python3
"""Übersetzt die Programme der Kapitel 7 bis 12 und prüft sie in einem 6502-Simulator
(py65) mit einfachen Modellen für die ACIA, das VIA und das HD44780-Display:

  monitor  die Sitzung aus Kapitel 7 (m, w, j)
  blink    Kapitel 8: LED-Wechsel etwa alle Viertelsekunde
  lcd      Kapitel 9: Initialisierung ohne Zeitverletzung, Text in den richtigen Zeilen

Braucht ca65/ld65 (cc65) und py65 (pip install py65).
Aufruf: python3 technische-dokumentation/programme/pruefen.py"""
import subprocess
import sys
import tempfile
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
from erzeugen import erzeuge  # noqa: E402
from geraete import Sid, Tastatur, Via1Timer1  # noqa: E402
from sim import Maschine  # noqa: E402


def baue(sprache, name, tmp):
    quelle = HIER / sprache / f"{name}.s"
    obj, binar, lbl = tmp / f"{name}.o", tmp / f"{name}.bin", tmp / f"{name}.lbl"
    subprocess.run(["ca65", "-g", "-o", obj, quelle], check=True)
    subprocess.run(["ld65", "-C", HIER / "ram.cfg", "-Ln", lbl, "-o", binar, obj], check=True)
    return str(binar), str(lbl)


def pruefe_monitor(binar, lbl):
    m = Maschine(binar, lbl)
    getc = m.labels["getc"]

    def sende(zeile):
        m.eingabe = list((zeile + "\r").encode())
        m.laufen(getc)

    m.laufen(getc)
    for i, b in enumerate([0xFF, 0xC0, 0xF7, 0x82, 0xFF, 0x10, 0xFF, 0x02, 0x00, 0xBF, 0x21, 0xBF, 0x00, 0xAF, 0x00, 0xFF]):
        m.mem._subject[0x4000 + i] = b
    for z in ("m 4000", "w 4000 a5", "m 4000", "x", "w 0300 A9", "w 0301 2A", "w 0302 8D",
              "w 0303 00", "w 0304 7F", "w 0305 60", "j 0300"):
        sende(z)
    t = m.text().replace("\r\n", "\n")
    erwartet = [
        "Welcome to the 6502 monitor program!",
        "> m 4000\n4000  FF C0 F7 82 FF 10 FF 02  00 BF 21 BF 00 AF 00 FF   |..........!.....|",
        "> w 4000 a5\n4000:A5",
        "> m 4000\n4000  A5 C0 F7 82 FF 10 FF 02  00 BF 21 BF 00 AF 00 FF   |..........!.....|",
        "> x\nUnknown command",
        "> j 0300\n*> ",
    ]
    for e in erwartet:
        assert e in t, f"Monitor: fehlt {e!r}\n{t}"


def pruefe_blink(binar, lbl):
    m = Maschine(binar, lbl)
    log = []
    m.mem.subscribe_to_write(range(0x7F20, 0x7F30), lambda a, v: log.append((m.mpu.processorCycles, a, v)))
    while m.mpu.processorCycles < 1_200_000:
        m.mpu.step()
    assert log[0][1:] == (0x7F22, 0xFF)
    orb = [(c, v) for c, a, v in log if a == 0x7F20]
    assert [v for _, v in orb[:4]] == [0, 0xFF, 0, 0xFF]
    halbperiode = orb[2][0] - orb[1][0]
    assert 250_000 < halbperiode < 265_000, halbperiode


class HD44780:
    """Ein Controller im 4-Bit-Betrieb mit Zeitprüfung (in Taktzyklen = µs bei 1 MHz)."""

    def __init__(self, name):
        self.name, self.state, self.n, self.hi = name, "init", 0, None
        self.ddram, self.addr, self.inc = {}, 0, 1
        self.disp = self.cursor = self.blink = 0
        self.fehler, self.sperre, self.fn = [], 40000, False

    def nibble(self, rs, wert, t):
        if t < self.sperre:
            self.fehler.append(f"{self.name}: zu früh bei {t}, frei ab {self.sperre}")
        if self.state == "init":
            if self.n < 3:
                if wert != 3:
                    self.fehler.append(f"{self.name}: Initialisierung {wert:x}")
                self.sperre = t + (4100 if self.n == 0 else 100)
                self.n += 1
            else:
                if wert != 2:
                    self.fehler.append(f"{self.name}: viertes Nibble {wert:x}")
                self.state, self.sperre = "4bit", t + 40
            return
        if self.hi is None:
            self.hi = wert
            return
        b, self.hi = (self.hi << 4) | wert, None
        dauer = 40
        if rs:
            self.ddram[self.addr] = chr(b)
            self.addr += self.inc
        elif b & 0x80:
            self.addr = b & 0x7F
        elif b & 0x20:
            self.fn = True
        elif b & 0x08:
            self.disp, self.cursor, self.blink = (b >> 2) & 1, (b >> 1) & 1, b & 1
        elif b & 0x04:
            self.inc = 1 if b & 2 else -1
        elif b & 0x01:
            self.ddram, self.addr, self.inc, dauer = {}, 0, 1, 1520
        self.sperre = t + dauer

    def zeile(self, start):
        return "".join(self.ddram.get(start + i, " ") for i in range(40)).rstrip()


def pruefe_lcd(binar, lbl):
    lcd = [HD44780("E1"), HD44780("E2")]
    m = Maschine(binar, lbl)
    port = [0]
    letzte = []

    def ora(a, v):
        alt, port[0] = port[0], v
        letzte.append(v)
        for i, bit in enumerate((0x20, 0x40)):
            if alt & bit and not v & bit:
                lcd[i].nibble((v >> 4) & 1, v & 0x0F, m.mpu.processorCycles)
    m.mem.subscribe_to_write([0x7F21], ora)
    halt = m.labels["halt"]
    for _ in range(3_000_000):
        m.mpu.step()
        if m.mpu.pc == halt:
            break
    else:
        raise AssertionError("LCD: Programm erreicht halt nicht")
    for l in lcd:
        assert not l.fehler, l.fehler
        assert l.state == "4bit" and l.fn and l.disp == 1
    assert lcd[0].cursor == 1 and lcd[0].blink == 1
    assert lcd[0].zeile(0x00) == "Welcome to the 6502 HomeComputer!"
    assert lcd[0].zeile(0x40) == ">"
    assert lcd[1].zeile(0x00) == "This is line 3."
    assert lcd[1].zeile(0x40) == ""
    # die LED (PA7) leuchtet und bleibt bei allen späteren Schreibzugriffen an
    ab = max(i for i, v in enumerate(letzte) if v & 0x80) if any(v & 0x80 for v in letzte) else -1
    assert ab >= 0 and all(v & 0x80 for v in letzte[ab - 40:ab + 1]), "LED-Bit geht verloren"
    assert letzte[-1] & 0x80


def lauf_ms(m, ms, vor=None):
    ende = m.mpu.processorCycles + ms * 1000
    while m.mpu.processorCycles < ende:
        m.mpu.step()
        if vor:
            vor()


def pruefe_tastatur(binar, lbl):
    ms = 1000
    ereignisse = [(40 * ms, 120 * ms, 0, 1, True),      # A: Zeile 0, Spalte 1 = Scancode 1, mit Prellen
                  (200 * ms, 280 * ms, 3, 7, False),     # Z: Scancode 31
                  (340 * ms, 420 * ms, 9, 4, False),     # Leertaste: Zeile 9 (VIA1 PB1), Scancode 76
                  (480 * ms, 560 * ms, 10, 1, False)]    # L: Zeile 10 (VIA1 PB2), Scancode 81
    m = Maschine(binar, lbl)
    Tastatur(m, ereignisse)
    lauf_ms(m, 700)
    t = m.text().replace("\r\n", "\n")
    assert t == "Scancode: $01\nScancode: $1F\nScancode: $4C\nScancode: $51\n", repr(t)


def pruefe_irq(binar, lbl):
    m = Maschine(binar, lbl)
    via = Via1Timer1(m)
    led = []
    m.mem.subscribe_to_write([0x7F21], lambda a, v: led.append((m.mpu.processorCycles, v)))

    nmi_t = 2_400_000
    gesendet = False
    while m.mpu.processorCycles < 3_600_000:
        m.mpu.step()
        via.schritt()
        if not gesendet and m.mpu.processorCycles >= nmi_t:
            m.mpu.nmi()
            gesendet = True
        if via.irq():
            m.mpu.irq()
    wechsel = [c for c, v in led]          # [0] = LED aus beim Start, danach jeder Wechsel
    dt = [b - a for a, b in zip(wechsel[1:], wechsel[2:])]
    assert 1_000_000 < dt[0] < 1_001_000, dt            # vor dem NMI: jede Sekunde
    spaeter = [b - a for a, b in zip(wechsel[1:], wechsel[2:]) if a > nmi_t + 500_000]
    assert len(spaeter) >= 5 and all(99_000 < d < 101_000 for d in spaeter), dt   # nach dem NMI: alle 0,1 s


def pruefe_synth(binar, lbl):
    ms = 1000
    ereignisse = [(40 * ms, 200 * ms, 0, 1, False),      # A -> C4
                  (320 * ms, 480 * ms, 3, 7, False)]     # Z -> G#4 (Taste an der Y-Stelle)
    m = Maschine(binar, lbl)
    Tastatur(m, ereignisse)
    sid = Sid(m)
    lauf_ms(m, 700)
    frei = [(c, r, v) for c, r, v in sid.log if r in (0, 1, 4)]
    freq = {}
    for c, r, v in sid.log:
        if r in (0, 1):
            freq.setdefault("f", 0)
            freq["f"] = (freq["f"] & (0xFF00 if r == 0 else 0x00FF)) | (v << 8 if r == 1 else v)
            freq.setdefault("liste", []).append((c, freq["f"]))
    notiert = sorted({f for _, f in freq["liste"] if f})
    assert 0x1125 in notiert and 0x1B38 in notiert, [hex(x) for x in notiert]
    ctrl = [(c, v) for c, r, v in sid.log if r == 4]
    assert ctrl[0][1] == 0x20 and any(v == 0x21 for _, v in ctrl) and ctrl[-1][1] == 0x20
    reg = {r: v for _, r, v in sid.log if r in (5, 6, 24)}
    assert reg == {5: 0x09, 6: 0x8A, 24: 0x0F}, reg


def main():
    erzeuge()
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for sprache in ("de", "en"):
            for name, test in (("monitor", pruefe_monitor), ("blink", pruefe_blink), ("lcd", pruefe_lcd),
                               ("tastatur", pruefe_tastatur), ("irq", pruefe_irq), ("synth", pruefe_synth)):
                binar, lbl = baue(sprache, name, tmp)
                test(binar, lbl)
                print(f"{sprache}/{name}.s: übersetzt und geprüft")


if __name__ == "__main__":
    main()
