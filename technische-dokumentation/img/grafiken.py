#!/usr/bin/env python3
"""Erklärende Grafiken im Buchstil: das Prinzip der Tastaturmatrix (matrix.svg, de/en).
Aufruf: python3 technische-dokumentation/img/grafiken.py"""
import html
from pathlib import Path

OUT = Path(__file__).resolve().parent
TINTE, GRAU, ORANGE, ORANGE_D, LCD_R = "#2A2826", "#6f6d69", "#E4643C", "#B8481F", "#6F83C8"
FONT = "Helvetica, Arial, sans-serif"

T = {
    "de": {"zeile": "Zeile", "spalte": "Spalte", "titel": "Tastaturmatrix, Taste in Zeile 1 und Spalte 2 gedrückt",
           "ausgang": "Ausgänge: genau eine Zeile Low", "eingang": "Eingänge mit Pull-up", "low": "Low",
           "lesen": "liest 0", "high": "High", "frei": "liest 1"},
    "en": {"zeile": "Row", "spalte": "Column", "titel": "Keyboard matrix, key in row 1 and column 2 pressed",
           "ausgang": "Outputs: exactly one row low", "eingang": "Inputs with pull-up", "low": "Low",
           "lesen": "reads 0", "high": "High", "frei": "reads 1"},
}


def matrix(sprache):
    t = T[sprache]
    zeilen, spalten = 3, 4
    x0, y0, dx, dy = 110, 60, 56, 44
    breite = x0 + (spalten - 1) * dx + 60
    hoehe = y0 + (zeilen - 1) * dy + 110
    o = []
    gedr = (1, 2)
    # Pull-ups oben
    for c in range(spalten):
        x = x0 + c * dx
        o.append(f'<line x1="{x}" y1="{y0 - 38}" x2="{x}" y2="{y0 - 24}" stroke="{ORANGE_D}" stroke-width="1.4"/>'
                 f'<path d="M{x - 4.5} {y0 - 38} L{x + 4.5} {y0 - 38} L{x} {y0 - 44} Z" fill="{ORANGE}" stroke="{ORANGE_D}" stroke-width=".8"/>'
                 f'<rect x="{x - 4}" y="{y0 - 24}" width="8" height="16" rx="1" fill="#fff" stroke="{TINTE}" stroke-width="1.3"/>'
                 f'<line x1="{x}" y1="{y0 - 8}" x2="{x}" y2="{y0 + (zeilen - 1) * dy + 40}" stroke="{ORANGE_D if c == gedr[1] else TINTE}" stroke-width="{2.2 if c == gedr[1] else 1.4}"/>')
    # Zeilenleitungen
    for r in range(zeilen):
        y = y0 + r * dy
        farbe = ORANGE_D if r == gedr[0] else TINTE
        o.append(f'<line x1="{x0 - 50}" y1="{y}" x2="{x0 + (spalten - 1) * dx + 24}" y2="{y}" stroke="{farbe}" stroke-width="{2.2 if r == gedr[0] else 1.4}"/>'
                 f'<text x="{x0 - 54}" y="{y + 3}" font-size="9" text-anchor="end" fill="{TINTE}" font-weight="700">{t["zeile"]} {r}</text>')
        if r == gedr[0]:
            o.append(f'<text x="{x0 - 54}" y="{y + 13}" font-size="7.6" text-anchor="end" fill="{ORANGE_D}" font-weight="700">{t["low"]}</text>')
    # Tasten an den Kreuzungen
    for r in range(zeilen):
        for c in range(spalten):
            x, y = x0 + c * dx, y0 + r * dy
            an = (r, c) == gedr
            o.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{ORANGE if an else "#fff"}" stroke="{ORANGE_D if an else TINTE}" stroke-width="1.3"/>'
                     f'<circle cx="{x}" cy="{y}" r="3.2" fill="{"#fff" if an else TINTE}"/>')
    # Spaltenbeschriftung und Leseergebnis unten
    for c in range(spalten):
        x = x0 + c * dx
        yb = y0 + (zeilen - 1) * dy + 40
        o.append(f'<path d="M{x} {yb} L{x - 4.5} {yb - 7} L{x + 4.5} {yb - 7} Z" fill="{TINTE}"/>'
                 f'<text x="{x}" y="{yb + 12}" font-size="9" text-anchor="middle" fill="{TINTE}" font-weight="700">{t["spalte"]} {c}</text>'
                 f'<text x="{x}" y="{yb + 24}" font-size="7.6" text-anchor="middle" fill="{ORANGE_D if c == gedr[1] else GRAU}" font-weight="700">'
                 f'{t["lesen"] if c == gedr[1] else t["frei"]}</text>')
    o.append(f'<text x="{breite / 2}" y="{hoehe - 4}" font-size="8" text-anchor="middle" fill="{GRAU}">{html.escape(t["ausgang"])} · {html.escape(t["eingang"])}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {breite} {hoehe}" font-family="{FONT}" role="img" '
            f'aria-label="{html.escape(t["titel"])}">\n<title>{html.escape(t["titel"])}</title>\n' + "\n".join(o) + "\n</svg>\n")


LCD_F = "#eef1fb"
B = {
    "de": {"titel": "Blockschaltbild des HomeComputer 6502", "takt": "Takt", "takt2": "1 MHz", "reset": "Reset", "reset2": "NE555",
           "adr": "Adressbus A0–A15", "dat": "Datenbus D0–D7", "ste": "R/W, φ2, /RESET",
           "dek": "Adressdekoder", "dek2": "74LS04, 30, 00, 137", "rom": "ROM", "ram": "RAM", "acia": "ACIA", "via1": "VIA 1", "via2": "VIA 2",
           "sid": "SID", "usb": "USB-Seriell", "lcd": "LCD, LED", "tast": "Tastatur", "lsp": "Lautsprecher",
           "leg1": "Adress- und Datenbus", "leg2": "Chip-Select: Name am Baustein", "leg3": "alle /IRQ zusammengeschaltet"},
    "en": {"titel": "Block diagram of the HomeComputer 6502", "takt": "Clock", "takt2": "1 MHz", "reset": "Reset", "reset2": "NE555",
           "adr": "Address bus A0–A15", "dat": "Data bus D0–D7", "ste": "R/W, φ2, /RESET",
           "dek": "Address decoder", "dek2": "74LS04, 30, 00, 137", "rom": "ROM", "ram": "RAM", "acia": "ACIA", "via1": "VIA 1", "via2": "VIA 2",
           "sid": "SID", "usb": "USB serial", "lcd": "LCD, LED", "tast": "Keyboard", "lsp": "Loudspeaker",
           "leg1": "Address and data bus", "leg2": "Chip select: name at each chip", "leg3": "all /IRQ lines joined"},
}


def blockschaltbild(sprache):
    t = B[sprache]
    o = []

    def box(x, y, w, h, titel, zeile2="", fuell=LCD_F, rand=TINTE, tf=TINTE):
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fuell}" stroke="{rand}" stroke-width="1.4"/>')
        if zeile2:
            o.append(f'<text x="{x + w / 2}" y="{y + h / 2 - 1}" font-size="10" text-anchor="middle" fill="{tf}" font-weight="700">{html.escape(titel)}</text>'
                     f'<text x="{x + w / 2}" y="{y + h / 2 + 10}" font-size="7.6" text-anchor="middle" fill="{GRAU}">{html.escape(zeile2)}</text>')
        else:
            o.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 3.5}" font-size="10" text-anchor="middle" fill="{tf}" font-weight="700">{html.escape(titel)}</text>')

    def linie(x1, y1, x2, y2, farbe=TINTE, w=1.4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{farbe}" stroke-width="{w}" stroke-linecap="round"{d}/>')

    # Takt, Reset, Prozessor
    box(20, 6, 100, 26, t["takt"] + ", " + t["takt2"], "")
    box(20, 38, 100, 26, t["reset"] + ", " + t["reset2"], "")
    box(200, 8, 130, 52, "6502", "CPU")
    linie(120, 19, 200, 24)
    linie(120, 51, 200, 44)
    # Busse
    ys = {"adr": 96, "dat": 114, "ste": 132}
    for k, nm in (("adr", t["adr"]), ("dat", t["dat"])):
        o.append(f'<line x1="14" y1="{ys[k]}" x2="446" y2="{ys[k]}" stroke="{LCD_R}" stroke-width="4" stroke-linecap="round"/>'
                 f'<text x="20" y="{ys[k] - 5}" font-size="7.6" fill="{LCD_R}" font-weight="700">{html.escape(nm)}</text>')
    o.append(f'<line x1="14" y1="{ys["ste"]}" x2="446" y2="{ys["ste"]}" stroke="{ORANGE}" stroke-width="2" stroke-linecap="round"/>'
             f'<text x="20" y="{ys["ste"] - 4}" font-size="7.6" fill="{ORANGE_D}" font-weight="700">{html.escape(t["ste"])}</text>')
    linie(265, 60, 265, 132, LCD_R, 3)
    # Zeile 1 unter den Bussen: ROM, RAM, Dekoder
    for x, w, k, adr, cs in ((20, 70, "rom", "$8000–$FFFF", "/CS_ROM"), (100, 70, "ram", "$0000–$7EFF", "/CS_RAM")):
        box(x, 160, w, 40, t[k], adr)
        linie(x + w / 2, 132, x + w / 2, 160, LCD_R, 2.4)
        o.append(f'<text x="{x + 2}" y="{156}" font-size="7" fill="{ORANGE_D}" font-weight="700">{cs}</text>')
    box(300, 160, 146, 40, t["dek"], t["dek2"])
    linie(373, 96, 373, 160, LCD_R, 2.4)
    # IO-Bausteine: Anschluss an die Busse über Winkel zwischen den Kästen
    chips2 = [(20, "acia", "$7F00", "/CS_ACIA", "usb", True, 190, 205), (125, "via1", "$7F20", "/CS_VIA1", "lcd", True, 220, 211),
              (230, "via2", "$7F40", "/CS_VIA2", "tast", True, 250, 217), (335, "sid", "$7F60", "/CS_SID", "lsp", False, 280, 223)]
    for x, k, adr, cs, per, irq, xd, yh in chips2:
        box(x, 252, 92, 40, t[k], adr)
        mitte = x + 46
        o.append(f'<path d="M{xd} 132 L{xd} {yh} L{mitte} {yh} L{mitte} 252" fill="none" stroke="{LCD_R}" stroke-width="2.4" stroke-linejoin="round"/>')
        o.append(f'<text x="{x + 2}" y="{248}" font-size="7" fill="{ORANGE_D}" font-weight="700">{cs}</text>')
        if irq:
            o.append(f'<text x="{x + 90}" y="{248}" font-size="7" text-anchor="end" fill="{ORANGE_D}" font-weight="700">/IRQ</text>')
        box(x, 320, 92, 28, t[per], "", "#fff", GRAU, GRAU)
        linie(mitte, 292, mitte, 320, GRAU, 1.4)
    # Legende
    yl = 372
    o.append(f'<line x1="20" y1="{yl}" x2="40" y2="{yl}" stroke="{LCD_R}" stroke-width="4"/><text x="46" y="{yl + 3}" font-size="7.6" fill="{GRAU}">{html.escape(t["leg1"])}</text>'
             f'<text x="150" y="{yl + 3}" font-size="7.6" fill="{ORANGE_D}" font-weight="700">/CS</text><text x="172" y="{yl + 3}" font-size="7.6" fill="{GRAU}">{html.escape(t["leg2"])}</text>'
             f'<text x="330" y="{yl + 3}" font-size="7.6" fill="{ORANGE_D}" font-weight="700">/IRQ</text><text x="354" y="{yl + 3}" font-size="7.6" fill="{GRAU}">{html.escape(t["leg3"])}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 466 386" font-family="{FONT}" role="img" '
            f'aria-label="{html.escape(t["titel"])}">\n<title>{html.escape(t["titel"])}</title>\n' + "\n".join(o) + "\n</svg>\n")


def main():
    for sprache in ("de", "en"):
        ziel = OUT / sprache
        ziel.mkdir(exist_ok=True)
        (ziel / "matrix.svg").write_text(matrix(sprache), encoding="utf-8")
        (ziel / "blockschaltbild.svg").write_text(blockschaltbild(sprache), encoding="utf-8")
    print("matrix.svg und blockschaltbild.svg geschrieben (de, en)")


if __name__ == "__main__":
    main()
