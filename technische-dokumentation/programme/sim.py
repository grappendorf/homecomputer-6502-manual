"""Kleiner Simulator für die Programme der Kapitel 7 bis 9 (py65 + Geräte-Modelle)."""
import re
from py65.devices.mpu6502 import MPU
from py65.memory import ObservableMemory

def labels(datei):
    d = {}
    for z in open(datei):
        m = re.match(r"al ([0-9A-F]+) \.(\S+)", z)
        if m:
            d[m.group(2)] = int(m.group(1), 16)
    return d

class Maschine:
    def __init__(self, rom_datei, lbl=None, ereignis=None):
        self.mem = ObservableMemory()
        self.mpu = MPU(memory=self.mem)
        self.rom = open(rom_datei, "rb").read()
        for i, b in enumerate(self.rom):
            self.mem._subject[0x8000 + i] = b
        self.labels = labels(lbl) if lbl else {}
        self.eingabe = []
        self.ausgabe = []
        self.log = []          # (Zyklen, Adresse, Wert) der Schreibzugriffe auf IO
        self.rom_schreib = set(range(0x8000, 0x10000))
        # ACIA
        self.mem.subscribe_to_read(range(0x7F00, 0x7F04), self._acia_lesen)
        self.mem.subscribe_to_write(range(0x7F00, 0x7F04), self._acia_schreiben)
        # ROM schreibgeschützt
        self.mem.subscribe_to_write(range(0x8000, 0x10000), lambda a, v: self.mem._subject[a])
        self.mpu.pc = self.mem[0xFFFC] | (self.mem[0xFFFD] << 8)
        self.mpu.sp = 0xFF

    def _acia_lesen(self, adr):
        r = adr & 3
        if r == 0:
            return self.eingabe.pop(0) if self.eingabe else 0
        if r == 1:
            return 0x10 | (0x08 if self.eingabe else 0)
        return self.mem._subject[adr]

    def _acia_schreiben(self, adr, wert):
        if adr & 3 == 0:
            self.ausgabe.append(wert)

    def laufen(self, ende_pc, max_schritte=3_000_000):
        """Läuft, bis der PC ende_pc erreicht (z. B. Warteschleife auf Eingabe)."""
        for _ in range(max_schritte):
            self.mpu.step()
            if self.mpu.pc == ende_pc and not self.eingabe:
                return
        raise RuntimeError("zu viele Schritte")

    def text(self):
        return bytes(self.ausgabe).decode("latin1")
