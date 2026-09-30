#!/usr/bin/env python3
"""Zeichnet schematische Oszilloskopbilder (kein bestimmtes Gerät):

  messung-takt.svg    Kapitel 1: Takt, 1 MHz
  messung-reset.svg   Kapitel 2: Versorgung und /RESET beim Einschalten
  messung-cpu.svg     Kapitel 3: Takt und Adressleitung A0
  messung-adressen.svg  Kapitel 3: die Adressleitungen A15 bis A0

Deutsch in img/de/, englisch in img/en/ (nur Beschriftung und Dezimalzeichen).
Die Kurven sind gerechnet, nicht gemessen: Rechtecke mit leichtem Überschwingen.
Aufruf: python3 technische-dokumentation/img/oszilloskop.py"""
import html
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
FONT = "Helvetica, Arial, sans-serif"
SCREEN, GITTER, GITTER_M = "#23282e", "#3a424b", "#59636e"
KANAL = {1: "#f2c94c", 2: "#62c7e6"}
TEXT = "#c9ced4"
DIV = 36
NX, NY = 10, 8
M = 14                       # Rand
B, H = NX * DIV, NY * DIV

TEXTE = {
    "de": {"versorgung": "Versorgung", "dezimal": ",", "takt": "Takt"},
    "en": {"versorgung": "Supply", "dezimal": ".", "takt": "Clock"},
}


def zahl(x, sprache):
    s = f"{x:g}"
    return s.replace(".", TEXTE[sprache]["dezimal"])


def frequenz(f, sprache):
    for grenze, einheit in ((1e6, "MHz"), (1e3, "kHz"), (1, "Hz")):
        if f >= grenze:
            wert = f / grenze
            s = f"{wert:.3g}"
            return s.replace(".", TEXTE[sprache]["dezimal"]) + " " + einheit
    return f"{f:g} Hz"


def zeit(t, sprache):
    for grenze, einheit in ((1, "s"), (1e-3, "ms"), (1e-6, "µs"), (1e-9, "ns")):
        if t >= grenze * 0.999:
            return zahl(round(t / grenze, 3), sprache) + " " + einheit
    return f"{t:g} s"


def spannung(v, sprache):
    return zahl(v, sprache) + " V"


def raster(x0, y0, breite=B, hoehe=H, nx=NX, ny=NY):
    dx, dy = breite / nx, hoehe / ny
    o = [f'<rect x="{x0}" y="{y0}" width="{breite}" height="{hoehe}" rx="4" fill="{SCREEN}"/>']
    for i in range(1, nx):
        x = x0 + i * dx
        o.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y0 + hoehe}" stroke="{GITTER_M if i == nx // 2 else GITTER}" stroke-width=".7"/>')
    for j in range(1, ny):
        y = y0 + j * dy
        o.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + breite}" y2="{y:.1f}" stroke="{GITTER_M if j == ny // 2 else GITTER}" stroke-width=".7"/>')
    # Teilstriche auf den Mittelachsen
    cx, cy = x0 + breite / 2, y0 + hoehe / 2
    for i in range(nx * 5 + 1):
        x = x0 + i * dx / 5
        o.append(f'<line x1="{x:.1f}" y1="{cy - 2:.1f}" x2="{x:.1f}" y2="{cy + 2:.1f}" stroke="{GITTER_M}" stroke-width=".6"/>')
    for j in range(ny * 5 + 1):
        y = y0 + j * dy / 5
        o.append(f'<line x1="{cx - 2:.1f}" y1="{y:.1f}" x2="{cx + 2:.1f}" y2="{y:.1f}" stroke="{GITTER_M}" stroke-width=".6"/>')
    o.append(f'<rect x="{x0}" y="{y0}" width="{breite}" height="{hoehe}" rx="4" fill="none" stroke="#0f1215" stroke-width="1.4"/>')
    return "\n".join(o)


def kurve(punkte, farbe, x0, y0, tdiv, vdiv, null_div, breite=B, nx=NX, deckkraft=1.0):
    """punkte: [(t in s, v in V)] -> SVG-Pfad. null_div: Lage von 0 V in Teilungen von unten."""
    pxdiv = breite / nx
    d = []
    for i, (t, v) in enumerate(punkte):
        x = x0 + t / tdiv * pxdiv
        y = y0 + H - (null_div + v / vdiv) * DIV
        x = min(max(x, x0), x0 + breite)
        y = min(max(y, y0 + 1), y0 + H - 1)
        d.append(f'{"M" if i == 0 else "L"}{x:.1f} {y:.1f}')
    return (f'<path d="{" ".join(d)}" fill="none" stroke="{farbe}" stroke-width="1.6" '
            f'stroke-linejoin="round" stroke-linecap="round" stroke-opacity="{deckkraft}"/>')


def marke(kanal, x0, y0, null_div, vdiv=None):
    """Masse-Marke des Kanals am linken Rand."""
    y = y0 + H - null_div * DIV
    f = KANAL[kanal]
    return (f'<path d="M{x0 - 11} {y - 6:.1f} L{x0 - 1} {y - 6:.1f} L{x0 + 3} {y:.1f} L{x0 - 1} {y + 6:.1f} L{x0 - 11} {y + 6:.1f} Z" fill="{f}"/>'
            f'<text x="{x0 - 6.5}" y="{y + 3.3:.1f}" font-size="8.5" text-anchor="middle" font-weight="700" fill="#23282e">{kanal}</text>')


def infoleiste(x0, y, kanaele, tdiv_text, sprache):
    """kanaele: [(nr, 'V/div-Text')]"""
    o = [f'<rect x="{x0}" y="{y}" width="{B}" height="22" rx="3" fill="#15191d"/>']
    x = x0 + 8
    for nr, text in kanaele:
        o.append(f'<rect x="{x}" y="{y + 5}" width="12" height="12" rx="2" fill="{KANAL[nr]}"/>'
                 f'<text x="{x + 6}" y="{y + 14.3}" font-size="8.6" text-anchor="middle" font-weight="700" fill="#23282e">{nr}</text>'
                 f'<text x="{x + 17}" y="{y + 14.5}" font-size="9" fill="{TEXT}">{html.escape(text)}</text>')
        x += 78
    o.append(f'<text x="{x0 + B - 8}" y="{y + 14.5}" font-size="9" text-anchor="end" fill="{TEXT}">{html.escape(tdiv_text)}</text>')
    return "\n".join(o)


def svg(inhalt, breite, hoehe, titel):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {breite} {hoehe}" '
            f'font-family="{FONT}" role="img" aria-label="{html.escape(titel)}">\n'
            f'<title>{html.escape(titel)}</title>\n{inhalt}\n</svg>\n')


# ------------------------------------------------------------ Signalformen

def rechteck(periode, hoch, tief, t_ende, schritt, anstieg=0.03, klingeln=0.0, versatz=0.0,
             einschwing=0.0, tau=0.0):
    """Rechtecksignal als Punkteliste. Flankenzeit = anstieg * Periode."""
    pts = []
    t = 0.0
    def pegel(t):
        ph = ((t - versatz) / periode) % 1.0
        return hoch if ph < 0.5 else tief
    n = int(t_ende / schritt)
    flanke = None
    for i in range(n + 1):
        t = i * schritt
        ph = ((t - versatz) / periode) % 1.0
        # Zeit seit der letzten Flanke (in Perioden)
        if ph < 0.5:
            seit, ziel, start, rein = ph, hoch, tief, True
        else:
            seit, ziel, start, rein = ph - 0.5, tief, hoch, False
        a = max(anstieg, 1e-6)
        if seit < a:
            v = start + (ziel - start) * seit / a
        else:
            v = ziel
            if klingeln:
                dt = (seit - a) / periode
                ring = klingeln * math.exp(-dt / 0.035) * math.cos(2 * math.pi * dt / 0.11)
                v = ziel + (ring if rein else -ring) * (hoch - tief) / 5
            if einschwing and rein:
                v = ziel - einschwing * math.exp(-(seit - a) / periode / tau) if tau else ziel
        pts.append((t, v))
    return pts



def signal(periode, versatz, t_ende, schritt, hoch, tief, seed, anstieg=60e-9, knick=0.8,
           kriech=0.45e-6, unterschwinger=0.12, ring_f=45e6, rausch=0.009, salve=0.035):
    """Rechtecksignal mit den Unregelmäßigkeiten einer echten Schaltung:
    langsame, abgeflachte steigende Flanke (kriecht zum oberen Pegel), schnelle
    fallende Flanke mit Unterschwinger, Schwingungssalven an den Flanken und
    Grundrauschen. Zufall aus seed, damit das Bild reproduzierbar bleibt."""
    import random
    rng = random.Random(seed)
    amp = hoch - tief
    pts = []
    n = int(t_ende / schritt)
    for i in range(n + 1):
        t = i * schritt
        ph = ((t - versatz) / periode) % 1.0
        if ph < 0.5:                       # oben: seit der steigenden Flanke
            dt = ph * periode
            if dt < anstieg:
                v = knick * amp * dt / anstieg
            else:
                v = amp * (knick + (1 - knick) * (1 - math.exp(-(dt - anstieg) / kriech)))
            ring = 0.35 * amp * salve * math.exp(-dt / 40e-9) * math.sin(2 * math.pi * ring_f * dt)
            # Überschwinger am Knick
            v += ring
            v += rng.gauss(0, rausch * 0.9) * (1 + 1.6 * math.exp(-dt / 60e-9))
            # das Rauschen auf dem oberen Pegel wird gegen Ende etwas stärker
            v += rng.gauss(0, rausch * 0.7) * (dt / (periode / 2))
        else:                              # unten: seit der fallenden Flanke
            dt = (ph - 0.5) * periode
            tf = 6e-9
            if dt < tf:
                v = amp * (1 - dt / tf) - unterschwinger * dt / tf
            else:
                v = -unterschwinger * math.exp(-(dt - tf) / 25e-9) * math.cos(2 * math.pi * ring_f * (dt - tf))
                v += salve * amp * 0.5 * math.exp(-(dt - tf) / 70e-9) * math.sin(2 * math.pi * 2.3 * ring_f * dt)
            v += rng.gauss(0, rausch) * (1 + 3.5 * math.exp(-dt / 70e-9))
            # kurz vor der steigenden Flanke: Einstreuung
            vor = (0.5 * periode - dt)
            v += rng.gauss(0, rausch * 1.4) * math.exp(-vor / 50e-9)
            v = max(v, -amp * 0.12)
        pts.append((t, tief + v))
    return pts


def faserig(funktion, farbe, *arg, **kw):
    """Zeichnet eine Kurve zweimal mit verschiedenem Zufall: die zweite halbtransparent
    wie die Nachleuchtspur eines Oszilloskops."""
    return "\n".join((funktion(seed=11, deckkraft=1.0), funktion(seed=27, deckkraft=0.35)))


# --------------------------------------------------------------- Abbildungen

def bemassung(xa, xb, yb, text):
    return (f'<path d="M{xa:.1f} {yb + 4:.1f} L{xa:.1f} {yb - 4:.1f} M{xb:.1f} {yb + 4:.1f} L{xb:.1f} {yb - 4:.1f} M{xa:.1f} {yb:.1f} L{xb:.1f} {yb:.1f}" '
            f'stroke="{TEXT}" stroke-width=".9" fill="none"/>'
            f'<text x="{(xa + xb) / 2:.1f}" y="{yb - 7:.1f}" font-size="9.5" text-anchor="middle" fill="{TEXT}">{text}</text>')


def spur(erzeuger, farbe, x0, y0, tdiv, vdiv, null):
    """Zwei Durchläufe mit verschiedenem Zufall übereinander (Nachleuchten)."""
    return "\n".join(kurve(erzeuger(seed), farbe, x0, y0, tdiv, vdiv, null, deckkraft=d)
                     for seed, d in ((11, 1.0), (27, 0.15)))


def takt(sprache):
    x0, y0 = M, M
    tdiv, vdiv = 500e-9, 1.0
    null = 2.0
    def erz(seed):
        return signal(1e-6, 0.25e-6, NX * tdiv, 4e-9, 4.24, 0.0, seed)
    inh = raster(x0, y0) + spur(erz, KANAL[1], x0, y0, tdiv, vdiv, null) + marke(1, x0, y0, null)
    xa = x0 + 0.25e-6 / tdiv * DIV
    xb = x0 + 1.25e-6 / tdiv * DIV
    inh += bemassung(xa, xb, y0 + H - (null + 4.9) * DIV, "1 µs = 1 MHz")
    inh += infoleiste(x0, y0 + H + 6, [(1, "1 V/div")], "500 ns/div", sprache)
    return svg(inh, B + 2 * M, H + 2 * M + 28, "Takt, 1 MHz")


def reset(sprache):
    import random
    t = TEXTE[sprache]
    x0, y0 = M, M
    tdiv, vdiv = 100e-3, 1.0
    n1, n2 = 1.6, 0.6
    t0 = 0.4 * tdiv                      # Einschalten
    ende = t0 + 0.56                     # /RESET geht hoch

    def versorgung(seed):
        rng = random.Random(seed)
        pts = []
        n = 500
        for i in range(n + 1):
            ts = i * NX * tdiv / n
            dt = ts - t0
            if dt < 0:
                v = rng.gauss(0, 0.018)
            else:
                anst = 0.05 * tdiv
                v = 4.3 * min(dt / anst, 1.0) if dt < anst else 4.3
                if dt >= anst:
                    v += 1.3 * math.exp(-(dt - anst) / (0.012 * tdiv)) * math.cos(2 * math.pi * (dt - anst) / (0.03 * tdiv))
                    v += (4.92 - 4.3) * (1 - math.exp(-(dt - anst) / (0.25 * tdiv)))
                v += rng.gauss(0, 0.02)
            pts.append((ts, v))
        return pts

    def reset_spur(seed):
        rng = random.Random(seed)
        pts = []
        n = 500
        for i in range(n + 1):
            ts = i * NX * tdiv / n
            if ts < t0:
                v = rng.gauss(0, 0.018)
            elif ts < ende:
                anst = 0.05 * tdiv
                v = 1.05 * min((ts - t0) / anst, 1.0) + 0.05 * math.log1p((ts - t0) / (0.3 * tdiv))
                v += rng.gauss(0, 0.016)
            else:
                dt = ts - ende
                v = 4.35 * min(dt / (0.02 * tdiv), 1.0) - 0.0
                v += 0.25 * math.exp(-dt / (0.004 * tdiv)) * math.cos(2 * math.pi * dt / (0.012 * tdiv))
                v += 0.25 * (1 - math.exp(-dt / (0.3 * tdiv)))
                v += rng.gauss(0, 0.02)
            pts.append((ts, v))
        return pts

    inh = raster(x0, y0)
    for seed, d in ((11, 1.0), (27, 0.15)):
        inh += kurve(versorgung(seed), KANAL[1], x0, y0, tdiv, vdiv, n1, deckkraft=d)
        inh += kurve(reset_spur(seed), KANAL[2], x0, y0, tdiv, vdiv, n2, deckkraft=d)
    inh += marke(1, x0, y0, n1) + marke(2, x0, y0, n2)
    xa = x0 + (t0 + 0.05 * tdiv) / tdiv * DIV
    xb = x0 + ende / tdiv * DIV
    inh += bemassung(xa, xb, y0 + H - (n2 + 1.9) * DIV, "≈ 560 ms")
    inh += (f'<text x="{x0 + 6.5 * DIV:.1f}" y="{y0 + H - (n1 + 5) * DIV - 10:.1f}" font-size="9.5" fill="{KANAL[1]}">{t["versorgung"]}</text>'
            f'<text x="{x0 + 6.5 * DIV:.1f}" y="{y0 + H - (n2 + 4.4) * DIV + 26:.1f}" font-size="9.5" fill="{KANAL[2]}">/RESET</text>')
    inh += infoleiste(x0, y0 + H + 6, [(1, "1 V/div"), (2, "1 V/div")], "100 ms/div", sprache)
    return svg(inh, B + 2 * M, H + 2 * M + 28, "Versorgung und Reset beim Einschalten")


def cpu(sprache):
    x0, y0 = M, M
    tdiv, vdiv = 1e-6, 2.0
    n1, n2 = 5.2, 1.4
    def takt_erz(seed):
        return signal(1e-6, 0.25e-6, NX * tdiv, 8e-9, 4.3, 0.0, seed)
    def a0_erz(seed):
        return signal(4e-6, 0.75e-6, NX * tdiv, 8e-9, 3.35, 0.0, seed, anstieg=110e-9, kriech=0.7e-6,
                      unterschwinger=0.1, salve=0.03)
    inh = raster(x0, y0)
    inh += spur(takt_erz, KANAL[1], x0, y0, tdiv, vdiv, n1) + spur(a0_erz, KANAL[2], x0, y0, tdiv, vdiv, n2)
    inh += marke(1, x0, y0, n1) + marke(2, x0, y0, n2)
    inh += (f'<text x="{x0 + 9.3 * DIV:.1f}" y="{y0 + H - (n1 + 2.3) * DIV - 6:.1f}" font-size="9.5" text-anchor="end" fill="{KANAL[1]}">{TEXTE[sprache]["takt"]} 1 MHz</text>'
            f'<text x="{x0 + 9.3 * DIV:.1f}" y="{y0 + H - (n2 + 2.3) * DIV - 6:.1f}" font-size="9.5" text-anchor="end" fill="{KANAL[2]}">A0 250 kHz</text>')
    inh += infoleiste(x0, y0 + H + 6, [(1, "2 V/div"), (2, "2 V/div")], "1 µs/div", sprache)
    return svg(inh, B + 2 * M, H + 2 * M + 28, "Takt und Adressleitung A0")


def adressen(sprache):
    """Vier kleine Schirme mit je vier Adressleitungen, eigene Zeitbasis je Schirm."""
    import random
    gruppen = [((15, 14, 13, 12), 20e-3), ((11, 10, 9, 8), 1e-3), ((7, 6, 5, 4), 50e-6), ((3, 2, 1, 0), 5e-6)]
    kopf = 16
    breite = B
    nx = 10
    px = breite / nx
    o = []
    y = M
    rng = random.Random(5)
    for leitungen, tdiv in gruppen:
        hoehe = 4 * 30 + kopf
        o.append(raster(M, y, breite, hoehe, nx, 4))
        for i, n in enumerate(leitungen):
            f = 250e3 / 2 ** n
            periode = 4e-6 * 2 ** n
            yb = y + kopf + 30 * (i + 1) - 6
            for seed, deck in ((1, 1.0), (2, 0.15)):
                r = random.Random(100 * n + seed)
                d = []
                samples = 450
                for k in range(samples + 1):
                    t = k * nx * tdiv / samples
                    hoch = int(t / (periode / 2)) % 2 == 1
                    # Flanken leicht verrundet und verrauscht
                    ph = (t / (periode / 2)) % 1.0
                    schritt = periode / 2 / 1.0
                    weich = 1.0
                    v = 1.0 if hoch else 0.0
                    if hoch and ph < 0.04:
                        v = 0.75 + 0.25 * ph / 0.04
                    v += r.gauss(0, 0.012 if v > 0.5 else 0.015)
                    # Einstreuung kurz nach einer fallenden Flanke
                    if (not hoch) and ph < 0.05:
                        v += r.gauss(0, 0.035)
                    x = M + t / tdiv * px
                    d.append(f'{"M" if k == 0 else "L"}{x:.1f} {yb - v * 17:.1f}')
                o.append(f'<path d="{" ".join(d)}" fill="none" stroke="{KANAL[1]}" stroke-width="1.4" '
                         f'stroke-linejoin="round" stroke-opacity="{deck}"/>')
            o.append(f'<text x="{M + 5}" y="{yb - 4:.1f}" font-size="9.5" font-weight="700" fill="{KANAL[2]}" stroke="{SCREEN}" stroke-width="3" paint-order="stroke">A{n}</text>')
            o.append(f'<text x="{M + breite - 6}" y="{yb - 4:.1f}" font-size="9" text-anchor="end" fill="{TEXT}" stroke="{SCREEN}" stroke-width="3" paint-order="stroke">{frequenz(f, sprache)}</text>')
        o.append(f'<text x="{M + breite - 6}" y="{y + 11}" font-size="9" text-anchor="end" fill="{TEXT}">{zeit(tdiv, sprache)}/div</text>')
        y += hoehe + 8
    return svg("\n".join(o), breite + 2 * M, y - 8 + M, "Adressleitungen A15 bis A0")


def led(sprache):
    """Kapitel 8: Spannung an PB0 bei der blinkenden LED, etwa 2 Hz."""
    x0, y0 = M, M
    tdiv, vdiv = 100e-3, 1.0
    null = 2.0
    halb = 0.2572
    def erz(seed):
        return signal(2 * halb, 0.12, NX * tdiv, 2e-3, 4.2, 0.0, seed, anstieg=1e-3, knick=0.97, kriech=0.01,
                      unterschwinger=0.0, rausch=0.012, salve=0.0)
    inh = raster(x0, y0) + spur(erz, KANAL[1], x0, y0, tdiv, vdiv, null) + marke(1, x0, y0, null)
    xa = x0 + 0.12 / tdiv * DIV
    xb = x0 + (0.12 + halb) / tdiv * DIV
    inh += bemassung(xa, xb, y0 + H - (null + 5.0) * DIV, "≈ " + zahl(0.26, sprache) + "\u202fs")
    inh += infoleiste(x0, y0 + H + 6, [(1, "1 V/div")], "100 ms/div", sprache)
    return svg(inh, B + 2 * M, H + 2 * M + 28, "Spannung an PB0")


def sid(sprache):
    """Kapitel 12: Ausgangssignal des SID, Sägezahn A4 = 440 Hz (wechselspannungsgekoppelt)."""
    import random
    x0, y0 = M, M
    tdiv, vdiv = 1e-3, 0.5
    null = 4.0
    f = 440.0
    def erz(seed):
        r = random.Random(seed)
        pts = []
        n = 700
        for i in range(n + 1):
            t = i * NX * tdiv / n
            ph = (t * f + 0.35) % 1.0
            v = 0.9 * (2 * ph - 1)                 # Sägezahn, etwa 1,8 V Spitze-Spitze
            if ph < 0.02:                            # steile Rückflanke mit kleinem Unterschwinger
                v -= 0.18 * (1 - ph / 0.02)
            v += r.gauss(0, 0.012)
            pts.append((t, v))
        return pts
    inh = raster(x0, y0) + spur(erz, KANAL[1], x0, y0, tdiv, vdiv, null) + marke(1, x0, y0, null)
    per = 1 / f
    xa = x0 + 0.35 / f / tdiv * DIV
    xa = x0 + ((1 - 0.35) % 1.0) / f / tdiv * DIV
    xb = xa + per / tdiv * DIV
    inh += bemassung(xa, xb, y0 + H - (null + 3.1) * DIV, "2,27\u202fms = 440\u202fHz".replace(",", TEXTE[sprache]["dezimal"]))
    inh += infoleiste(x0, y0 + H + 6, [(1, "500 mV/div")], "1 ms/div", sprache)
    return svg(inh, B + 2 * M, H + 2 * M + 28, "Ausgang des SID")


def irq(sprache):
    """Kapitel 11: Pegel an PA7 (LED) beim Interrupt-Programm: erst jede Sekunde, nach dem NMI jede Zehntelsekunde."""
    import random
    x0, y0 = M, M
    tdiv, vdiv = 0.4, 2.0
    null = 2.5
    wechsel = [1.0002, 2.0004]
    t = 2.4
    # Nach dem NMI: der nächste Tick (alle 0,1 s) schaltet sofort, danach alle 0,1 s
    nach = 2.4 + 0.043
    while nach < 4.0:
        wechsel.append(nach)
        nach += 0.10002
    def erz(seed):
        r = random.Random(seed)
        pts = []
        pegel = 0
        n = 800
        for i in range(n + 1):
            ts = i * NX * tdiv / n
            pegel = sum(1 for w in wechsel if w <= ts) % 2
            pts.append((ts, 4.3 * pegel + r.gauss(0, 0.012)))
        return pts
    inh = raster(x0, y0) + spur(erz, KANAL[1], x0, y0, tdiv, vdiv, null) + marke(1, x0, y0, null)
    xn = x0 + 2.4 / tdiv * DIV
    inh += (f'<path d="M{xn:.1f} {y0 + 10} L{xn:.1f} {y0 + H - 6}" stroke="{KANAL[2]}" stroke-width="1" stroke-dasharray="3 3"/>'
            f'<text x="{xn + 4:.1f}" y="{y0 + 18}" font-size="9.5" fill="{KANAL[2]}" font-weight="700">NMI</text>')
    inh += bemassung(x0 + 1.0002 / tdiv * DIV, x0 + 2.0004 / tdiv * DIV, y0 + H - (null + 2.6) * DIV, "1\u202fs")
    inh += infoleiste(x0, y0 + H + 6, [(1, "2 V/div")], "400 ms/div", sprache)
    return svg(inh, B + 2 * M, H + 2 * M + 28, "Pegel an PA7")


def main():
    for sprache in ("de", "en"):
        ziel = OUT / sprache
        ziel.mkdir(exist_ok=True)
        for name, fn in (("messung-takt", takt), ("messung-reset", reset),
                         ("messung-cpu", cpu), ("messung-adressen", adressen),
                         ("messung-led", led), ("messung-sid", sid), ("messung-irq", irq)):
            (ziel / f"{name}.svg").write_text(fn(sprache), encoding="utf-8")
    print("Oszilloskopbilder geschrieben (de, en)")


if __name__ == "__main__":
    main()
