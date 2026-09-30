"""Geräte-Modelle für pruefen.py: Tastaturmatrix, VIA-Timer mit Interrupt und SID-Register."""


class Tastatur:
    """14 Zeilen (VIA2 PB0..PB7 = 0..7, VIA1 PB0..PB5 = 8..13) und 8 Spalten (VIA2 Port A).
    Ereignisse: (von, bis, zeile, spalte, prellen) in Taktzyklen. Während des Prellens
    wechselt der Kontakt alle 700 µs."""

    def __init__(self, m, ereignisse):
        self.m, self.ereignisse = m, ereignisse
        m.mem.subscribe_to_read([0x7F41], self.spalten)

    def gedrueckt(self, zeile, spalte):
        t = self.m.mpu.processorCycles
        for von, bis, z, s, prellen in self.ereignisse:
            if (z, s) == (zeile, spalte) and von <= t < bis:
                if prellen and t < von + 3000:
                    return int((t - von) / 700) % 2 == 0
                return True
        return False

    def spalten(self, adresse):
        via2 = self.m.mem._subject[0x7F40]
        via1 = self.m.mem._subject[0x7F20]
        wert = 0xFF
        for z in range(14):
            niedrig = not (via2 >> z) & 1 if z < 8 else not (via1 >> (z - 8)) & 1
            if niedrig:
                for s in range(8):
                    if self.gedrueckt(z, s):
                        wert &= ~(1 << s)
        return wert


class Via1Timer1:
    """Timer 1 des VIA1 im Free-Run-Modus mit IRQ-Leitung (Periode N + 2 Takte)."""

    def __init__(self, m):
        self.m = m
        self.ifr = self.ier = 0
        self.latch = [0, 0]
        self.naechster = None
        self.periode = None
        m.mem.subscribe_to_write([0x7F24, 0x7F25, 0x7F2B, 0x7F2E], self.schreiben)
        m.mem.subscribe_to_read([0x7F24, 0x7F2D, 0x7F2E], self.lesen)

    def schreiben(self, a, v):
        if a == 0x7F24:
            self.latch[0] = v
        elif a == 0x7F25:
            self.latch[1] = v
            n = self.latch[0] | (v << 8)
            self.periode = n + 2
            self.naechster = self.m.mpu.processorCycles + self.periode
            self.ifr &= ~0x40
        elif a == 0x7F2E:
            if v & 0x80:
                self.ier |= v & 0x7F
            else:
                self.ier &= ~(v & 0x7F)

    def lesen(self, a):
        if a == 0x7F24:
            self.ifr &= ~0x40
        elif a == 0x7F2D:
            return self.ifr | (0x80 if self.ifr & self.ier else 0)
        elif a == 0x7F2E:
            return self.ier | 0x80

    def schritt(self):
        if self.naechster is not None:
            while self.m.mpu.processorCycles >= self.naechster:
                self.ifr |= 0x40
                self.naechster += self.periode

    def irq(self):
        return bool(self.ifr & self.ier & 0x7F)


class Sid:
    """Merkt sich alle Schreibzugriffe auf die SID-Register $7F60..$7F7C."""

    def __init__(self, m):
        self.m, self.log = m, []
        m.mem.subscribe_to_write(range(0x7F60, 0x7F7D), lambda a, v: self.log.append((m.mpu.processorCycles, a - 0x7F60, v)))
