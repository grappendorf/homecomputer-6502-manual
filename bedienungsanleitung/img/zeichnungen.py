#!/usr/bin/env python3
"""Zeichnet die stilisierten Abbildungen des Computers in zwei Sprachen:
  deutsch: computer.svg, ueberblick.svg, rueckseite.svg, tastatur.svg, adsr.svg
  englisch: das Gleiche in en/ (plus en/zeichensatz.svg, Kopie mit
  englischen Beschriftungen)
Aufruf: python3 manual/img/zeichnungen.py"""
import html
from pathlib import Path
OUT = Path(__file__).resolve().parent
ORANGE, ORANGE_D, ORANGE_DD = "#E4643C", "#C9542E", "#A9431E"
LCD, LCD_T, TASTE, TASTE_O = "#8FA6EA", "#1F2B63", "#2A2826", "#44423F"
GELB, GRAU_T = "#fbdd90", "#6f6d69"
FONT = "Helvetica, Arial, sans-serif"

# Texte je Sprache
TEXTE = {
    "de": {
        "laut": "laut", "zeit": "Zeit", "ton_an": "Ton an", "ton_aus": "Ton aus",
        "sustain": "Sustain-Pegel",
        "titel_adr": "Hüllkurve", "aria_adr": "Hüllkurve mit Attack, Decay, Sustain und Release",
        "titel_rueck": "Rückseite", "aria_rueck": "Rückseite des HomeComputer 6502",
        "titel_tast": "Tastatur", "aria_tast": "Tastatur des HomeComputer 6502",
        "aria_drauf": "HomeComputer 6502 von oben",
    },
    "en": {
        "laut": "loud", "zeit": "Time", "ton_an": "Tone on", "ton_aus": "Tone off",
        "sustain": "Sustain level",
        "titel_adr": "Envelope", "aria_adr": "Envelope with attack, decay, sustain and release",
        "titel_rueck": "Back", "aria_rueck": "Back of the HomeComputer 6502",
        "titel_tast": "Keyboard", "aria_tast": "Keyboard of the HomeComputer 6502",
        "aria_drauf": "HomeComputer 6502 top view",
    },
}

# Tastenreihen: (Beschriftung, Breite in Einheiten, Gruppe)
# Gruppen: n = normal, e = Editieren, u = Umschalten, s = Sonderfunktion, x = ohne Funktion
F = [("Esc",1,"e")] + [(f"F{i}",1,"x") for i in range(1,13)] + [("Num",1,"x"),("Druck",1,"x"),("Rollen",1,"x"),("Pause",1,"s")]
R2 = [("^",1,"n")] + [(c,1,"n") for c in "1234567890"] + [("ß",1,"n"),("´",1,"n"),("⌫",2,"e"),("Pos1",1,"e")]
R3 = [("Tab",1.5,"x")] + [(c,1,"n") for c in "QWERTZUIOPÜ+"] + [("Enter",1.5,"e"),("Bild↑",1,"x")]
R4 = [("Caps",1.75,"u")] + [(c,1,"n") for c in "ASDFGHJKLÖÄ#"] + [("",1.25,"e"),("Bild↓",1,"x")]
R5 = [("Shift",2.25,"u")] + [(c,1,"n") for c in "YXCVBNM,.-"] + [("Shift",1.75,"u"),("↑",1,"e"),("Ende",1,"e")]
R6 = [("Strg",1,"u"),("Fn",1,"s"),("Win",1,"s"),("Alt",1,"x"),("<",1,"n"),("",4,"n"),("AltGr",1,"u"),("Menü",1,"x"),("Strg",1,"u"),("Einfg",1,"e"),("Entf",1,"e"),("←",1,"e"),("↓",1,"e"),("→",1,"e")]
ROWS = [F, R2, R3, R4, R5, R6]

# Englische Tastennamen (Tastaturlayout bleibt das deutsche QWERTZ)
KEY_EN = {
    "Druck": "PrtSc", "Rollen": "ScrLk", "Pos1": "Home", "Bild↑": "PgUp",
    "Bild↓": "PgDn", "Ende": "End", "Strg": "Ctrl", "Menü": "Menu",
    "Einfg": "Ins", "Entf": "Del", "Enter": "Return",
}

def rows(sprache):
    if sprache == "de":
        return ROWS
    return [[(KEY_EN.get(l, l), w, g) for l, w, g in row] for row in ROWS]

FILL = {"n": (TASTE_O, "#ffffff"), "e": (ORANGE, "#ffffff"), "u": (LCD, LCD_T), "s": (GELB, "#3b3b3b"), "x": ("#b9b6b1", "#4a4845")}

def keyboard(x0, y0, width, row_h, gap, sprache, labels=True, colored=True):
    o = []
    enter_x = None
    for r, row in enumerate(rows(sprache)):
        total = sum(w for _, w, _ in row)
        unit = (width + gap) / total
        x = x0
        y = y0 + r * row_h
        for label, w, g in row:
            kw = w * unit - gap
            kh = row_h - gap
            fill, tc = FILL[g] if colored else (TASTE_O, "#fff")
            if r == 2 and label in ("Enter", "Return"):
                enter_x = (x, kw)
            if r == 3 and g == "e" and label == "" and enter_x:
                # unterer Teil der Enter-Taste, oben verbunden
                ex, ew = enter_x
                o.append(f'<rect x="{x:.1f}" y="{y - gap - 2:.1f}" width="{ex + ew - x:.1f}" height="{kh + gap + 2:.1f}" rx="2.5" fill="{fill}"/>')
                x += w * unit
                continue
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{kw:.1f}" height="{kh:.1f}" rx="2.5" fill="{fill}"/>')
            if labels and label:
                fs = 9 if len(label) == 1 else (6.2 if len(label) <= 4 else 5.6)
                o.append(f'<text x="{x + kw/2:.1f}" y="{y + kh/2 + fs*0.36:.1f}" font-family="{FONT}" font-size="{fs}" font-weight="700" text-anchor="middle" fill="{tc}">{html.escape(label)}</text>')
            x += w * unit
    return o

def grille(x0, y0, hole=5.5, pitch=9, cols=4, rows_=6, led=False):
    o = []
    for r in range(rows_):
        for c in range(cols):
            o.append(f'<rect x="{x0 + c*pitch:.1f}" y="{y0 + r*pitch:.1f}" width="{hole}" height="{hole}" rx="1" fill="{ORANGE_DD}"/>')
    if led:
        lx, ly = x0 + (cols-1)*pitch + hole/2, y0 + hole/2
        o.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.6" fill="#ffe27a"/>')
        o.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4.5" fill="#ffe27a" opacity=".35"/>')
    return o

def marker(n, x, y):
    return [f'<circle cx="{x}" cy="{y}" r="9" fill="#ffffff" stroke="{TASTE}" stroke-width="1.5"/>',
            f'<text x="{x}" y="{y + 3.6}" font-family="{FONT}" font-size="10.5" font-weight="700" text-anchor="middle" fill="{TASTE}">{n}</text>']

def draufsicht(t, sprache="de", markers=False, labels=False):
    W, H = 480, 300
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{t["aria_drauf"]}">',
         '<title>HomeComputer 6502</title>']
    o.append(f'<rect x="14" y="22" width="{W-28}" height="{H-30}" rx="14" fill="#000" opacity=".18"/>')
    o.append(f'<rect x="8" y="8" width="{W-16}" height="{H-24}" rx="14" fill="{ORANGE_D}"/>')
    o.append(f'<rect x="8" y="8" width="{W-16}" height="{H-34}" rx="14" fill="{ORANGE}"/>')
    # Kante zwischen Anzeigeteil und Tastaturteil
    o.append(f'<rect x="8" y="96" width="{W-16}" height="3" fill="{ORANGE_D}"/>')
    lx, ly, lw, lh = 140, 28, 200, 50
    o.append(f'<rect x="{lx-6}" y="{ly-6}" width="{lw+12}" height="{lh+12}" rx="3" fill="{ORANGE_DD}"/>')
    o.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="1.5" fill="{LCD}"/>')
    o.append(f'<text x="{lx+8}" y="{ly+15}" font-family="VT323, monospace" font-size="12" fill="{LCD_T}">READY.</text>')
    o.append(f'<rect x="{lx+8}" y="{ly+19}" width="5" height="8" fill="{LCD_T}"/>')
    o += grille(52, 26)
    o += grille(W - 52 - 3*9 - 5.5, 26, led=True)
    o += keyboard(22, 108, W - 44, 25.5, 2.2, sprache, labels=labels, colored=False)
    if markers:
        o += marker(1, lx + lw/2, 12)
        o += marker(2, 34, 50)
        o += marker(3, W - 30, 16)
        o += marker(4, 14, 190)
    o.append('</svg>')
    return "\n".join(o) + "\n"

def rueckseite(t):
    W, H = 480, 110
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{t["aria_rueck"]}">',
         f'<title>{t["titel_rueck"]}</title>']
    y0, h = 34, 56
    o.append(f'<rect x="10" y="{y0+6}" width="{W-20}" height="{h}" rx="6" fill="#000" opacity=".15"/>')
    o.append(f'<rect x="8" y="{y0}" width="{W-16}" height="{h}" rx="6" fill="{ORANGE}"/>')
    o.append(f'<rect x="8" y="{y0+h-8}" width="{W-16}" height="8" rx="3" fill="{ORANGE_D}"/>')
    cy = y0 + h/2 - 2
    # 1 Poti-Öffnung
    px = 62
    o.append(f'<circle cx="{px}" cy="{cy-10}" r="6.5" fill="{ORANGE_DD}"/>')
    o.append(f'<circle cx="{px}" cy="{cy-10}" r="3.8" fill="#9a8f7c"/>')
    o.append(f'<rect x="{px-3.8}" y="{cy-10.8}" width="7.6" height="1.6" fill="#5b554b"/>')
    # 2 Mini-USB (Laden)
    o.append(f'<rect x="{px-8}" y="{cy+6}" width="16" height="7" rx="1.5" fill="{TASTE}"/>')
    o.append(f'<rect x="{px-5.5}" y="{cy+8.2}" width="11" height="2.6" rx=".8" fill="#8a8781"/>')
    # 3 und 4 Schiebeschalter
    for sx in (150, 342):
        o.append(f'<rect x="{sx-12}" y="{cy-5}" width="24" height="10" rx="2" fill="{TASTE}"/>')
        o.append(f'<rect x="{sx-9}" y="{cy-4}" width="9" height="8" rx="1.5" fill="#6d6a64"/>')
    # 5 Micro-USB (seriell, Strom)
    ux = 400
    o.append(f'<rect x="{ux-7}" y="{cy+6}" width="14" height="6" rx="2" fill="{TASTE}"/>')
    o.append(f'<rect x="{ux-4.5}" y="{cy+7.8}" width="9" height="2.4" rx=".8" fill="#8a8781"/>')
    for n, x in [(1, px), (2, px + 26), (3, 150), (4, 342), (5, ux)]:
        o.append(f'<line x1="{x}" y1="{y0-2}" x2="{x}" y2="21" stroke="{TASTE}" stroke-width="1"/>')
        o += marker(n, x, 12)
    o.append(f'<line x1="{px + 26}" y1="21" x2="{px+26}" y2="{cy+4}" stroke="{TASTE}" stroke-width="1"/>')
    o.append(f'<line x1="{px + 26}" y1="{cy+4}" x2="{px+9}" y2="{cy+9}" stroke="{TASTE}" stroke-width="1"/>')
    o.append('</svg>')
    return "\n".join(o) + "\n"

def tastatur(t, sprache="de"):
    W, H = 480, 170
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{t["aria_tast"]}">',
         f'<title>{t["titel_tast"]}</title>']
    o.append(f'<rect x="2" y="2" width="{W-4}" height="{H-4}" rx="8" fill="{TASTE}"/>')
    o += keyboard(10, 10, W - 20, 25.3, 2.2, sprache, labels=True, colored=True)
    o.append('</svg>')
    return "\n".join(o) + "\n"

def adsr(t):
    W, H = 480, 190
    x0, y0, yb = 40, 30, 150          # Achsenursprung links unten bei (x0, yb)
    xa, xd, xs, xr = 90, 150, 330, 430
    ys = 80                            # Sustain-Pegel
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{t["aria_adr"]}">',
         f'<title>{t["titel_adr"]}</title>']
    for xa_, xb_, fill in [(x0, xa, "#fbe3d9"), (xa, xd, "#fff4d7"), (xd, xs, "#e3e9fb"), (xs, xr, "#ececea")]:
        o.append(f'<rect x="{xa_}" y="{y0}" width="{xb_-xa_}" height="{yb-y0}" fill="{fill}"/>')
    o.append(f'<polyline points="{x0},{yb} {xa},{y0+4} {xd},{ys} {xs},{ys} {xr},{yb}" fill="none" stroke="{ORANGE}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
    o.append(f'<line x1="{x0}" y1="{yb}" x2="{W-20}" y2="{yb}" stroke="{TASTE}" stroke-width="1.5"/>')
    o.append(f'<line x1="{x0}" y1="{yb}" x2="{x0}" y2="{y0-10}" stroke="{TASTE}" stroke-width="1.5"/>')
    o.append(f'<text x="{x0-6}" y="{y0}" font-family="{FONT}" font-size="10" text-anchor="end" fill="{TASTE}">{t["laut"]}</text>')
    o.append(f'<text x="{W-20}" y="{yb+14}" font-family="{FONT}" font-size="10" text-anchor="end" fill="{TASTE}">{t["zeit"]}</text>')
    for xa_, xb_, name in [(x0, xa, "Attack"), (xa, xd, "Decay"), (xd, xs, "Sustain"), (xs, xr, "Release")]:
        o.append(f'<text x="{(xa_+xb_)/2}" y="{yb+30}" font-family="{FONT}" font-size="11" font-weight="700" text-anchor="middle" fill="{TASTE}">{name}</text>')
    for x, label in [(x0, t["ton_an"]), (xs, t["ton_aus"])]:
        o.append(f'<line x1="{x}" y1="{y0-6}" x2="{x}" y2="{yb}" stroke="{TASTE}" stroke-width="1" stroke-dasharray="3 3"/>')
        o.append(f'<text x="{x+4}" y="{y0-10}" font-family="{FONT}" font-size="10" fill="{TASTE}">{label}</text>')
    o.append(f'<line x1="{xd}" y1="{ys}" x2="{x0}" y2="{ys}" stroke="{TASTE}" stroke-width="1" stroke-dasharray="2 3"/>')
    o.append(f'<text x="{xd+8}" y="{ys-7}" font-family="{FONT}" font-size="10" fill="{TASTE}">{t["sustain"]}</text>')
    o.append('</svg>')
    return "\n".join(o) + "\n"

def schreibe(sprache, ordner=""):
    t = TEXTE[sprache]
    ziel = OUT / ordner
    ziel.mkdir(exist_ok=True)
    (ziel / "adsr.svg").write_text(adsr(t))
    (ziel / "computer.svg").write_text(draufsicht(t, sprache))
    (ziel / "ueberblick.svg").write_text(draufsicht(t, sprache, markers=True))
    (ziel / "rueckseite.svg").write_text(rueckseite(t))
    (ziel / "tastatur.svg").write_text(tastatur(t, sprache))

schreibe("de", "de")
schreibe("en", "en")

# zeichensatz.svg hat keinen Generator: englische Kopie mit übersetzten
# Beschriftungen ableiten (Titel und aria-label).
zs = (OUT / "de" / "zeichensatz.svg").read_text(encoding="utf-8")
zs_en = zs.replace(
    'aria-label="Zeichensatz der Anzeige, 16 Zeilen mal 16 Spalten"',
    'aria-label="Display character set, 16 rows by 16 columns"',
).replace("<title>Zeichensatz</title>", "<title>Character set</title>")
(OUT / "en" / "zeichensatz.svg").write_text(zs_en, encoding="utf-8")
