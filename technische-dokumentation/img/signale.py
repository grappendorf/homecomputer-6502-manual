"""Anschlussbelegungen der Bausteine aus den Kapiteln 3 bis 6. Die Tabellen dienen
den Zeichnungen (Stummel mit Signalnamen) und den Verdrahtungstabellen im Text."""

# 6502 (DIP-40): Pin -> Signal
CPU = {
    1: "GND", 2: "RDY", 3: "PHI1", 4: "IRQ", 5: "", 6: "NMI", 7: "SYNC", 8: "VCC",
    9: "A0", 10: "A1", 11: "A2", 12: "A3", 13: "A4", 14: "A5", 15: "A6", 16: "A7",
    17: "A8", 18: "A9", 19: "A10", 20: "A11", 21: "GND", 22: "A12", 23: "A13", 24: "A14",
    25: "A15", 26: "D7", 27: "D6", 28: "D5", 29: "D4", 30: "D3", 31: "D2", 32: "D1",
    33: "D0", 34: "R/W", 35: "", 36: "", 37: "PHI0", 38: "SO", 39: "PHI2", 40: "RES",
}
CPU_PIN = {}
for _p, _s in CPU.items():
    if _s and _s not in ("GND", "VCC"):
        CPU_PIN.setdefault(_s, _p)

# 28-poliger Speicher (AT28C256 EEPROM, 61256 SRAM, gleiche Belegung)
SPEICHER = {
    1: "A14", 2: "A12", 3: "A7", 4: "A6", 5: "A5", 6: "A4", 7: "A3", 8: "A2", 9: "A1", 10: "A0",
    11: "D0", 12: "D1", 13: "D2", 14: "GND", 15: "D3", 16: "D4", 17: "D5", 18: "D6", 19: "D7",
    20: "/CE", 21: "A10", 22: "/OE", 23: "A11", 24: "A9", 25: "A8", 26: "A13", 27: "/WE", 28: "VCC",
}
SPEICHER_PIN = {s: p for p, s in SPEICHER.items() if s not in ("GND", "VCC")}

# 6551 ACIA (DIP-28)
ACIA = {
    1: "GND", 2: "CS0", 3: "/CS1", 4: "/RES", 5: "RxC", 6: "XTAL1", 7: "XTAL2", 8: "/RTS",
    9: "/CTS", 10: "TxD", 11: "/DTR", 12: "RxD", 13: "RS0", 14: "RS1", 15: "VCC", 16: "/DCD",
    17: "/DSR", 18: "D0", 19: "D1", 20: "D2", 21: "D3", 22: "D4", 23: "D5", 24: "D6", 25: "D7",
    26: "/IRQ", 27: "PHI2", 28: "R/W",
}

# Bus-Signale je Gruppe (für Drahtfarben)
def gruppe(signal):
    if signal.startswith("A") and signal[1:].isdigit():
        return "adresse"
    if signal.startswith("D") and signal[1:].isdigit():
        return "daten"
    return "steuer"
