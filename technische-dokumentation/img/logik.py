#!/usr/bin/env python3
"""Schematische Logikanalysator-Bilder (kein bestimmtes Gerät) für die Kapitel 4 bis 6.
Die Buszyklen werden aus den Programmen gerechnet, nicht gemessen.

  logik-eeprom.svg   Kapitel 4: Reset-Vektor und die Schleife LDA/JMP
  logik-acia.svg     Kapitel 5: Schreibzugriffe auf die ACIA
  logik-dekoder.svg  Kapitel 6: Chip-Select-Signale bei ROM-, IO- und RAM-Zugriffen

Deutsch in img/de/, englisch in img/en/.
Aufruf: python3 technische-dokumentation/img/logik.py"""
import html
from pathlib import Path

OUT = Path(__file__).resolve().parent
FONT = "Helvetica, Arial, sans-serif"
SCREEN, GITTER = "#23282e", "#323a43"
TEXT, TEXT_D = "#c9ced4", "#8b949e"
GELB, BLAU, GRUEN, ORANGE = "#f2c94c", "#62c7e6", "#7fd38a", "#f0935f"
R = 26                       # Zeilenhöhe
GUTTER = 62

TEXTE = {
    "de": {"adresse": "Adresse", "daten": "Daten", "befehl": "Befehl", "zyklus": "Takt",
           "reset": "Reset-Vektor", "hinweis": "", "ansicht": "Takt"},
    "en": {"adresse": "Address", "daten": "Data", "befehl": "Instruction", "zyklus": "Cycle",
           "reset": "Reset vector", "hinweis": "", "ansicht": "Cycle"},
}


def _t(s):
    return html.escape(s)


def _bit(werte, i):
    v = werte[i]
    return v if isinstance(v, tuple) else (v, v)


def diagramm(zeilen, zyklen, befehle, sprache, zw=40, titel=""):
    """zeilen: [(Name, Art, Werte, Farbe)]. Art: 'takt', 'bit' (0/1 oder (erste, zweite Hälfte)),
    'bus' (Text je Zyklus). befehle: [(Text, Anzahl Zyklen)]."""
    t = TEXTE[sprache]
    n = zyklen
    breite = GUTTER + n * zw + 10
    kopf = 34
    hoehe = kopf + len(zeilen) * R + 20
    o = [f'<rect x="0" y="0" width="{breite}" height="{hoehe}" rx="4" fill="{SCREEN}"/>']
    # Zyklusgitter
    for i in range(n + 1):
        x = GUTTER + i * zw
        o.append(f'<line x1="{x}" y1="{kopf - 4}" x2="{x}" y2="{hoehe - 14}" stroke="{GITTER}" stroke-width=".8"/>')
    # Befehlsleiste
    x = GUTTER
    for text, anz in befehle:
        o.append(f'<path d="M{x + 2} {kopf - 8} L{x + 2} {kopf - 14} L{x + anz * zw - 2} {kopf - 14} L{x + anz * zw - 2} {kopf - 8}" '
                 f'fill="none" stroke="{TEXT_D}" stroke-width=".9"/>'
                 f'<text x="{x + anz * zw / 2}" y="{kopf - 18}" font-size="8.4" text-anchor="middle" fill="{TEXT}" font-weight="600">{_t(text)}</text>')
        x += anz * zw
    o.append(f'<text x="8" y="{kopf - 18}" font-size="8" fill="{TEXT_D}">{t["befehl"]}</text>')
    for k, (name, art, werte, farbe) in enumerate(zeilen):
        y0 = kopf + k * R
        yc = y0 + R / 2
        o.append(f'<text x="8" y="{yc + 3}" font-size="9" fill="{TEXT}" font-weight="600">{_t(name)}</text>')
        hoch, tief = yc - 7, yc + 7
        if art == "takt":
            d = []
            for i in range(n):
                xa = GUTTER + i * zw
                d.append(f'{"M" if i == 0 else "L"}{xa} {tief} L{xa + zw / 2} {tief} L{xa + zw / 2} {hoch} L{xa + zw} {hoch} L{xa + zw} {tief}')
            o.append(f'<path d="{" ".join(d)}" fill="none" stroke="{farbe}" stroke-width="1.5" stroke-linejoin="round"/>')
        elif art == "bit":
            d = []
            pegel = lambda v: hoch if v else tief      # noqa: E731
            yv = None
            for i in range(n):
                xa = GUTTER + i * zw
                a, b = _bit(werte, i)
                if yv is None:
                    d.append(f"M{xa} {pegel(a)}")
                elif pegel(a) != yv:
                    d.append(f"L{xa} {yv} L{xa} {pegel(a)}")
                if a != b:
                    d.append(f"L{xa + zw / 2} {pegel(a)} L{xa + zw / 2} {pegel(b)}")
                yv = pegel(b)
                d.append(f"L{xa + zw} {yv}")
            o.append(f'<path d="{" ".join(d)}" fill="none" stroke="{farbe}" stroke-width="1.5" stroke-linejoin="round"/>')
        elif art == "bus":
            for i in range(n):
                xa = GUTTER + i * zw
                xb = xa + zw
                s = 3
                o.append(f'<path d="M{xa + s} {yc} L{xa + s + 3} {hoch} L{xb - s - 3} {hoch} L{xb - s} {yc} L{xb - s - 3} {tief} L{xa + s + 3} {tief} Z" '
                         f'fill="{farbe}" fill-opacity=".13" stroke="{farbe}" stroke-width="1.3" stroke-linejoin="round"/>'
                         f'<text x="{(xa + xb) / 2}" y="{yc + 3.2}" font-size="8.6" text-anchor="middle" fill="{TEXT}" '
                         f'font-family="IBM Plex Mono, Menlo, monospace" font-weight="600">{_t(werte[i])}</text>')
    # Zyklusnummern
    for i in range(n):
        o.append(f'<text x="{GUTTER + i * zw + zw / 2}" y="{hoehe - 5}" font-size="7.4" text-anchor="middle" fill="{TEXT_D}">{i + 1}</text>')
    o.append(f'<text x="8" y="{hoehe - 5}" font-size="7.4" fill="{TEXT_D}">{t["zyklus"]}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {breite} {hoehe}" font-family="{FONT}" role="img" '
            f'aria-label="{_t(titel)}">\n<title>{_t(titel)}</title>\n' + "\n".join(o) + "\n</svg>\n")


# ------------------------------------------------------------- Beispiele

def hex4(a):
    return f"{a:04X}"


def hex2(d):
    return f"{d:02X}"


def eeprom(sprache):
    t = TEXTE[sprache]
    # (Adresse, Daten) je Buszyklus: Reset-Vektor, dann LDA #$12 / JMP $8000 / LDA ...
    z = [(0xFFFC, 0x00), (0xFFFD, 0x80), (0x8000, 0xA9), (0x8001, 0x12), (0x8002, 0x4C),
         (0x8003, 0x00), (0x8004, 0x80), (0x8000, 0xA9), (0x8001, 0x12)]
    zeilen = [("φ2", "takt", None, TEXT),
              ("R/W", "bit", [1] * len(z), GELB),
              (t["adresse"], "bus", [hex4(a) for a, _ in z], BLAU),
              (t["daten"], "bus", [hex2(d) for _, d in z], ORANGE)]
    befehle = [(t["reset"], 2), ("LDA #$12", 2), ("JMP $8000", 3), ("LDA …", 2)]
    return diagramm(zeilen, len(z), befehle, sprache, zw=41, titel="Buszyklen nach dem Reset")


def acia(sprache):
    t = TEXTE[sprache]
    z = [(0x8005, 0xA9, 1), (0x8006, 0x0B, 1), (0x8007, 0x85, 1), (0x8008, 0x02, 1), (0x0002, 0x0B, 0),
         (0x8009, 0xA9, 1), (0x800A, 0x1F, 1), (0x800B, 0x85, 1), (0x800C, 0x03, 1), (0x0003, 0x1F, 0)]
    a15 = [1 if a & 0x8000 else 0 for a, _, _ in z]
    zeilen = [("φ2", "takt", None, TEXT),
              ("R/W", "bit", [rw for _, _, rw in z], GELB),
              ("A15", "bit", a15, BLAU),
              ("/CS_ROM", "bit", [0 if v else 1 for v in a15], GRUEN),
              (t["adresse"], "bus", [hex4(a) for a, _, _ in z], BLAU),
              (t["daten"], "bus", [hex2(d) for _, d, _ in z], ORANGE)]
    befehle = [("LDA #$0B", 2), ("STA $02", 3), ("LDA #$1F", 2), ("STA $03", 3)]
    return diagramm(zeilen, len(z), befehle, sprache, zw=38, titel="Schreibzugriffe auf die ACIA")


def dekoder_signale(adresse, phi2):
    """Rechnet die Chip-Select-Signale nach den Gleichungen des Kapitels 6."""
    a15 = (adresse >> 15) & 1
    cs_rom = 0 if a15 else 1                              # /CS_ROM = nicht A15
    hoch = all((adresse >> b) & 1 for b in range(8, 15))   # A14..A8
    cs_io = 0 if (hoch and cs_rom) else 1                 # 8-fach-NAND 74LS30
    n_ram = 0 if (cs_rom and cs_io) else 1                # NAND 74LS00 (Gatter A)
    ram = 1 - n_ram                                       # Inverter
    cs_ram = 0 if (ram and phi2) else 1                   # NAND 74LS00 (Gatter B)
    return cs_rom, cs_io, n_ram, cs_ram


def dekoder(sprache):
    t = TEXTE[sprache]
    # LDA $7F01 bei $8010, dann STA $0200 bei $8013
    z = [(0x8010, 0xAD, 1), (0x8011, 0x01, 1), (0x8012, 0x7F, 1), (0x7F01, 0x10, 1),
         (0x8013, 0x8D, 1), (0x8014, 0x00, 1), (0x8015, 0x02, 1), (0x0200, 0x48, 0)]
    cs_rom = [dekoder_signale(a, 1)[0] for a, _, _ in z]
    cs_io = [dekoder_signale(a, 1)[1] for a, _, _ in z]
    cs_ram = [(1, dekoder_signale(a, 1)[3]) for a, _, _ in z]
    # Gültigkeit der Kurven prüfen: genau ein Baustein je Zyklus
    for i, (a, _, _) in enumerate(z):
        gewaehlt = [cs_rom[i] == 0, cs_io[i] == 0, cs_ram[i][1] == 0]
        assert sum(gewaehlt) == 1, (hex(a), gewaehlt)
    zeilen = [("φ2", "takt", None, TEXT),
              ("R/W", "bit", [rw for _, _, rw in z], GELB),
              (t["adresse"], "bus", [hex4(a) for a, _, _ in z], BLAU),
              ("/CS_ROM", "bit", cs_rom, GRUEN),
              ("/CS_IO", "bit", cs_io, GRUEN),
              ("/CS_RAM", "bit", cs_ram, GRUEN),
              (t["daten"], "bus", [hex2(d) for _, d, _ in z], ORANGE)]
    befehle = [("LDA $7F01", 4), ("STA $0200", 4)]
    return diagramm(zeilen, len(z), befehle, sprache, zw=45, titel="Chip-Select-Signale")


def main():
    for sprache in ("de", "en"):
        ziel = OUT / sprache
        ziel.mkdir(exist_ok=True)
        for name, fn in (("logik-eeprom", eeprom), ("logik-acia", acia), ("logik-dekoder", dekoder)):
            (ziel / f"{name}.svg").write_text(fn(sprache), encoding="utf-8")
    print("Logikanalysator-Bilder geschrieben (de, en)")


if __name__ == "__main__":
    main()
