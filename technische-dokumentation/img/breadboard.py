"""Zeichnet stilisierte Steckbrett-Diagramme (Ansicht von oben) als SVG und
prüft dabei, ob die gezeichnete Verdrahtung der Netzliste entspricht.

Ein Steckbrett hat die Zeilen j..f (oben), a..e (unten) und je zwei
Stromschienen oben (T-, T+) und unten (B+, B-). Löcher derselben Spalte
sind innerhalb einer Hälfte verbunden, die Stromschienen der Länge nach.
Die Mittelrinne trennt oben und unten.

Benutzung:
    bb = Steckbrett()
    b1 = bb.brett(ox, oy, spalten)
    bb.ic("IC1", b1, 5, 14, "74LS04")
    bb.widerstand("R1", b1, (5, "c"), (6, "c"), "1k")
    bb.draht(b1, (5, "j"), (b1, "T+", 5))
    bb.pruefe(netze)   # wirft AssertionError bei Abweichungen
    svg = bb.svg()
"""
import html

P = 10.0                      # Lochabstand (= 0,1 Zoll)
RAND = 18.0
ZEILEN = {                    # y-Offset innerhalb des Bretts
    "T-": 14, "T+": 24,
    "j": 44, "i": 54, "h": 64, "g": 74, "f": 84,
    "e": 114, "d": 124, "c": 134, "b": 144, "a": 154,
    "B+": 174, "B-": 184,
}
BRETT_H = 200.0
TOP = set("jihgf")
BOT = set("edcba")

# Farben
PLATINE = "#f3f0e6"
PLATINE_R = "#d6d1c0"
RINNE = "#e4e0d1"
LOCH = "#4d4a42"
WEISS = "#ffffff"
TINTE = "#2A2826"
GRAU = "#6f6d69"
ORANGE = "#E4643C"
ROT, SCHWARZ, BLAU, GRUEN, GELB, WEISSDRAHT, BRAUN = (
    "#d8392b", "#33312f", "#2f63c4", "#2f9e57", "#f0c419", "#eeeeee", "#8b5a2b")
DRAHT_RAND = "#00000033"

RING = {"0": "#1b1b1b", "1": "#7a4a1d", "2": "#d23b2a", "3": "#f08a24", "4": "#f2d21b",
        "5": "#3da35d", "6": "#2d6bd1", "7": "#8a4fc9", "8": "#8d8d8d", "9": "#f3f3f3"}


def ringe(wert):
    """'3k3' -> Farbringe (vier Ringe: zwei Ziffern, Multiplikator, Gold)."""
    w = wert.replace("Ω", "")
    if "k" in w:
        a, _, b = w.partition("k")
        ziffern = (a + b).ljust(2, "0")
        mult = 3 - len(b)
    elif "M" in w:
        a, _, b = w.partition("M")
        ziffern = (a + b).ljust(2, "0")
        mult = 6 - len(b)
    else:
        a, _, b = w.partition("R")
        ziffern = (a + b).ljust(2, "0")
        mult = -len(b)
    ziffern = ziffern[:2]
    m = mult - (len(ziffern) - 2)
    mult_farbe = {-1: "#c9a227", 0: "#1b1b1b"}.get(m) or RING[str(m)]
    return [RING[ziffern[0]], RING[ziffern[1]], mult_farbe, "#c9a227"]


class Brett:
    def __init__(self, nr, ox, oy, spalten):
        self.nr, self.ox, self.oy, self.n = nr, ox, oy, spalten

    @property
    def breite(self):
        return 2 * RAND + (self.n - 1) * P

    def xy(self, spalte, zeile):
        return (self.ox + RAND + (spalte - 1) * P, self.oy + ZEILEN[zeile])

    def knoten(self, spalte, zeile):
        if zeile in ("T+", "T-", "B+", "B-"):
            return (self.nr, zeile)
        return (self.nr, spalte, "o" if zeile in TOP else "u")


class Steckbrett:
    def __init__(self):
        self.bretter = []
        self.teile = []       # (z-Ordnung, svg-Text)
        self.belegt = {}      # Knoten-Loch -> Bezeichnung (Doppelbelegung prüfen)
        self.pins = {}        # "IC1.3" -> Knoten
        self.kurz = []        # (Knoten, Knoten) fest verbunden (z.B. im Taster)
        self.labels = []
        self._uf = {}
        self.alle_pins = []

    # ------------------------------------------------------------ Bretter
    def brett(self, ox, oy, spalten):
        b = Brett(len(self.bretter) + 1, ox, oy, spalten)
        self.bretter.append(b)
        return b

    # ------------------------------------------------------ Union-Find
    def _find(self, k):
        self._uf.setdefault(k, k)
        while self._uf[k] != k:
            self._uf[k] = self._uf[self._uf[k]]
            k = self._uf[k]
        return k

    def _union(self, a, b):
        self._uf[self._find(a)] = self._find(b)

    def _loch(self, b, spalte, zeile, wer):
        if not (1 <= spalte <= b.n):
            raise AssertionError(f"{wer}: Spalte {spalte} außerhalb des Bretts")
        if zeile in ("T+", "T-", "B+", "B-"):
            schluessel = (b.nr, spalte, zeile)
        else:
            schluessel = (b.nr, spalte, zeile)
        if schluessel in self.belegt:
            raise AssertionError(
                f"Loch {spalte}{zeile} doppelt belegt: {self.belegt[schluessel]} und {wer}")
        self.belegt[schluessel] = wer
        return b.knoten(spalte, zeile)

    def _pin(self, name, knoten):
        self.pins[name] = knoten
        self.alle_pins.append(name)
        self._find(knoten)

    # ---------------------------------------------------------- Zeichnen
    def _add(self, z, text):
        self.teile.append((z, text))

    def _drahtpfad(self, p, q, bogen):
        (x1, y1), (x2, y2) = p, q
        dx, dy = x2 - x1, y2 - y1
        if bogen == 0 or (dx == 0 and dy == 0):
            return f"M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}"
        laenge = (dx * dx + dy * dy) ** 0.5
        nx, ny = -dy / laenge, dx / laenge
        cx = (x1 + x2) / 2 + nx * bogen
        cy = (y1 + y2) / 2 + ny * bogen
        return f"M{x1:.1f} {y1:.1f} Q{cx:.1f} {cy:.1f} {x2:.1f} {y2:.1f}"

    def draht(self, von, nach, farbe=GRUEN, bogen=0, name=None, z=50):
        """von/nach: (Brett, Spalte, Zeile) oder (x, y, 'ext:<Name>')."""
        pts, knoten = [], []
        for ende in (von, nach):
            if isinstance(ende[0], Brett):
                b, sp, ze = ende
                knoten.append(self._loch(b, sp, ze, name or "Draht"))
                pts.append(b.xy(sp, ze))
            else:
                x, y, ext = ende
                k = ("ext", ext)
                self._find(k)
                knoten.append(k)
                pts.append((x, y))
        self._union(*knoten)
        pfad = self._drahtpfad(pts[0], pts[1], bogen)
        self._add(z, f'<path d="{pfad}" fill="none" stroke="#000" stroke-opacity=".28" '
                     f'stroke-width="4.6" stroke-linecap="round"/>'
                     f'<path d="{pfad}" fill="none" stroke="{farbe}" stroke-width="3.2" stroke-linecap="round"/>')
        for (x, y), e in zip(pts, (von, nach)):
            if isinstance(e[0], Brett):
                self._add(z, f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.3" fill="{farbe}" stroke="#00000044" stroke-width=".8"/>')
        return self

    def beschriftung(self, text, x, y, groesse=6.5, anker="middle", farbe=TINTE, gewicht=600):
        self.labels.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{groesse}" text-anchor="{anker}" '
            f'fill="{farbe}" font-weight="{gewicht}">{html.escape(text)}</text>')

    def _bein(self, p, q, farbe="#b4b4ae", z=40):
        self._add(z, f'<path d="M{p[0]:.1f} {p[1]:.1f} L{q[0]:.1f} {q[1]:.1f}" stroke="{farbe}" '
                     f'stroke-width="1.5" stroke-linecap="round" fill="none"/>')

    # -------------------------------------------------------------- IC
    def ic(self, name, b, pin1_spalte, pins, beschriftung, breit=None):
        """DIP-IC, Kerbe links. Schmale ICs (300 mil: 74LS-Reihe, NE555) sitzen mit den
        Pins in den Zeilen e und f beiderseits der Rinne. Breite ICs (600 mil: 6502,
        28-polige Speicher, 6551) sind sechs Löcher breit und sitzen in den Zeilen d
        und h, denn die Rinne ist nur drei Löcher breit. Unterseite: Pin 1 .. n/2,
        Oberseite: Pin n .. n/2+1."""
        if breit is None:
            breit = pins >= 24
        zu, zo = ("d", "h") if breit else ("e", "f")
        h = pins // 2
        x_l = b.xy(pin1_spalte, zu)[0]
        x_r = b.xy(pin1_spalte + h - 1, zu)[0]
        y_o = b.xy(1, zo)[1]
        y_u = b.xy(1, zu)[1]
        for k in range(1, h + 1):
            sp = pin1_spalte + k - 1
            self._pin(f"{name}.{k}", self._loch(b, sp, zu, f"{name}.{k}"))
            self._pin(f"{name}.{pins + 1 - k}", self._loch(b, sp, zo, f"{name}.{pins + 1 - k}"))
        # Pins (silberne Stummel)
        for k in range(1, h + 1):
            x = b.xy(pin1_spalte + k - 1, zu)[0]
            self._add(30, f'<rect x="{x - 1.6:.1f}" y="{y_o - 4:.1f}" width="3.2" height="{y_u - y_o + 8:.1f}" fill="#c9c9c3"/>')
        # Gehäuse
        w = x_r - x_l + 2 * 5.5
        self._add(31, f'<rect x="{x_l - 5.5:.1f}" y="{y_o + 2:.1f}" width="{w:.1f}" height="{y_u - y_o - 4:.1f}" rx="2.2" fill="#33312f"/>')
        cx = (x_l + x_r) / 2
        cy = (y_o + y_u) / 2
        self._add(32, f'<path d="M{x_l - 5.5:.1f} {cy - 4:.1f} A4 4 0 0 1 {x_l - 5.5:.1f} {cy + 4:.1f}" fill="{PLATINE}" stroke="none"/>')
        self._add(32, f'<circle cx="{x_l + 1.5:.1f}" cy="{y_u - 6:.1f}" r="1.4" fill="#7a7874"/>')
        size = 7.5 if pins <= 16 else (8.6 if pins <= 28 else 10)
        self._add(33, f'<text x="{cx:.1f}" y="{cy - 1.5:.1f}" font-size="{size - 1.5}" text-anchor="middle" fill="#e4643c" font-weight="700">{html.escape(name)}</text>'
                      f'<text x="{cx:.1f}" y="{cy + size:.1f}" font-size="{size}" text-anchor="middle" fill="#e9e7e4" font-weight="600">{html.escape(beschriftung)}</text>')
        # Pinnummern
        for k in range(1, h + 1):
            x = b.xy(pin1_spalte + k - 1, "e")[0]
            self._add(33, f'<text x="{x:.1f}" y="{y_u - 4.4:.1f}" font-size="3.7" text-anchor="middle" fill="#bdbab5">{k}</text>')
            self._add(33, f'<text x="{x:.1f}" y="{y_o + 7.4:.1f}" font-size="3.7" text-anchor="middle" fill="#bdbab5">{pins + 1 - k}</text>')

    # ------------------------------------------------- zweibeinige Teile
    def _zwei(self, name, b, h1, h2, pin_namen=("1", "2")):
        ks = []
        for (sp, ze), pn in zip((h1, h2), pin_namen):
            k = self._loch(b, sp, ze, f"{name}.{pn}")
            self._pin(f"{name}.{pn}", k)
            ks.append(k)
        return b.xy(*h1), b.xy(*h2)

    def _koerper_pose(self, p, q, laenge):
        """Liegt das Teil flach (Löcher weit genug auseinander), oder steht es
        auf? Gibt (Mittelpunkt, Winkel in Grad, Beinpunkte) zurück."""
        (x1, y1), (x2, y2) = p, q
        dx, dy = x2 - x1, y2 - y1
        d = (dx * dx + dy * dy) ** 0.5
        if d >= laenge + 6:
            import math
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            w = math.degrees(math.atan2(dy, dx))
            ux, uy = dx / d, dy / d
            a = (mx - ux * laenge / 2, my - uy * laenge / 2)
            c = (mx + ux * laenge / 2, my + uy * laenge / 2)
            return (mx, my), w, (a, c), "flach"
        # stehend: Körper senkrecht über der Zeile
        mx = (x1 + x2) / 2
        unten = max(y1, y2)
        mitte_y = unten - 4 - laenge / 2
        a = (mx, unten - 4)
        c = (mx, unten - 4 - laenge)
        return (mx, mitte_y), 90, (a, c), "stehend"

    def widerstand(self, name, b, h1, h2, wert, beschriftung_pos=None):
        p, q = self._zwei(name, b, h1, h2)
        import math
        d = math.hypot(q[0] - p[0], q[1] - p[1])
        laenge = 26 if d >= 32 else (max(18, d - 8) if d >= 26 else 26)
        (mx, my), w, (a, c), art = self._koerper_pose(p, q, laenge)
        # Beine
        if art == "flach":
            self._bein(p, a)
            self._bein(q, c)
        else:
            # Bein 1 zum Fuß, Bein 2 außen am Körper entlang zum Kopf
            ziel_a, ziel_c = (a, c) if p[0] <= q[0] else (c, a)
            self._bein(p, ziel_a)
            self._bein(q, (q[0], ziel_c[1]))
            self._bein((q[0], ziel_c[1]), ziel_c)
        bande = ringe(wert)
        self._add(45, f'<g transform="translate({mx:.1f} {my:.1f}) rotate({w:.1f})">'
                      f'<rect x="{-laenge / 2}" y="-3.6" width="{laenge}" height="7.2" rx="3.4" fill="#e3c594" stroke="#00000033" stroke-width=".6"/>'
                      + "".join(f'<rect x="{xx * laenge / 26}" y="-3.6" width="2.3" height="7.2" fill="{f}"/>'
                                for xx, f in zip((-8.2, -4.6, -1.0, 6.2), bande))
                      + '</g>')
        if beschriftung_pos:
            self.beschriftung(f"{name} {wert}", *beschriftung_pos[:2],
                              anker=beschriftung_pos[2] if len(beschriftung_pos) > 2 else "middle")

    def keramik(self, name, b, h1, h2, wert="100n", beschriftung_pos=None):
        p, q = self._zwei(name, b, h1, h2)
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        # Scheibe steht etwas neben den Löchern (senkrecht zur Verbindung)
        import math
        dx, dy = q[0] - p[0], q[1] - p[1]
        d = math.hypot(dx, dy)
        if abs(dy) > abs(dx):          # senkrecht zwischen den Löchern
            cx, cy = mx, my
        else:                           # zwischen Löchern derselben Zeile: darüber
            cx, cy = mx, my - 11
        r = 5.2
        for pt in (p, q):
            ex, ey = pt
            self._bein(pt, (cx + (ex - cx) * .35, cy + (ey - cy) * .35))
        self._add(45, f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="#f0a93a" stroke="#00000033" stroke-width=".6"/>'
                      f'<text x="{cx:.1f}" y="{cy + 2:.1f}" font-size="5.2" text-anchor="middle" fill="#6b3f06" font-weight="600">{html.escape(self._ckurz(wert))}</text>')
        if beschriftung_pos:
            self.beschriftung(f"{name} {wert}", *beschriftung_pos[:2],
                              anker=beschriftung_pos[2] if len(beschriftung_pos) > 2 else "middle")

    @staticmethod
    def _ckurz(w):
        return {"100n": "104", "68n": "683", "10n": "103", "22p": "22"}.get(w, w)

    def elko(self, name, b, plus, minus, wert="10u", beschriftung_pos=None):
        p, q = self._zwei(name, b, plus, minus, ("+", "-"))
        import math
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        if abs(q[1] - p[1]) > abs(q[0] - p[0]):
            cx, cy = mx, my
        else:
            cx, cy = mx, my - 11
        r = 7.2
        for pt in (p, q):
            self._bein(pt, (cx + (pt[0] - cx) * .3, cy + (pt[1] - cy) * .3))
        # Streifen auf der Minus-Seite
        ang = math.atan2(q[1] - cy, q[0] - cx) if (q != p) else 0
        self._add(45, f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="#2f5fb0" stroke="#00000044" stroke-width=".6"/>'
                      f'<g transform="translate({cx:.1f} {cy:.1f}) rotate({math.degrees(ang):.1f})">'
                      f'<path d="M{r * 0.42:.1f} {-r * 0.91:.1f} A{r} {r} 0 0 1 {r * 0.42:.1f} {r * 0.91:.1f} Z" fill="#dfe6f3"/>'
                      f'</g>'
                      f'<text x="{cx - 1:.1f}" y="{cy + 1.8:.1f}" font-size="5" text-anchor="middle" fill="#fff" font-weight="600">{html.escape(wert)}</text>')
        px, py = p
        self._add(46, f'<text x="{px + (cx - px) * 0.0:.1f}" y="{py:.1f}" font-size="0"> </text>')
        if beschriftung_pos:
            self.beschriftung(f"{name} {wert}", *beschriftung_pos[:2],
                              anker=beschriftung_pos[2] if len(beschriftung_pos) > 2 else "middle")

    def quarz(self, name, b, h1, h2, wert="1 MHz", beschriftung_pos=None, unter=False):
        p, q = self._zwei(name, b, h1, h2)
        import math
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        laenge = 30
        d = math.hypot(q[0] - p[0], q[1] - p[1])
        w = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        if abs(q[0] - p[0]) >= abs(q[1] - p[1]):
            cy = my + 11 if unter else my - 9
        else:
            cy = my
        self._bein(p, (mx - min(d / 2, 10) * 0, cy))
        self._bein(q, (mx, cy))
        self._add(45, f'<g transform="translate({mx:.1f} {cy:.1f})">'
                      f'<rect x="-{laenge / 2}" y="-6" width="{laenge}" height="12" rx="6" fill="#d8d9dc" stroke="#7d7f86" stroke-width=".8"/>'
                      f'<rect x="-{laenge / 2 - 3}" y="-3.4" width="{laenge - 6}" height="6.8" rx="3.4" fill="#eceef1"/>'
                      f'<text x="0" y="1.7" font-size="4.6" text-anchor="middle" fill="#5c5f66" font-weight="600">{html.escape(wert)}</text>'
                      f'</g>')

    def taster(self, name, b, spalte, links="o"):
        """Kleiner Taster über der Rinne: Beine in (spalte, e), (spalte+2, e),
        (spalte, f), (spalte+2, f). Die beiden Beine derselben Hälfte sind im
        Taster verbunden, gedrückt verbindet er die Hälften."""
        kn = {}
        for sp in (spalte, spalte + 2):
            for ze in ("e", "f"):
                k = self._loch(b, sp, ze, f"{name}.{sp}{ze}")
                kn[(sp, ze)] = k
                self._find(k)
        self._union(kn[(spalte, "e")], kn[(spalte + 2, "e")])
        self._union(kn[(spalte, "f")], kn[(spalte + 2, "f")])
        self._pin(f"{name}.1", kn[(spalte, "e")])
        self._pin(f"{name}.2", kn[(spalte, "f")])
        x1 = b.xy(spalte, "e")[0]
        x2 = b.xy(spalte + 2, "e")[0]
        y1 = b.xy(1, "f")[1]
        y2 = b.xy(1, "e")[1]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        for x in (x1, x2):
            self._add(40, f'<rect x="{x - 1.6:.1f}" y="{y1 - 3:.1f}" width="3.2" height="{y2 - y1 + 6:.1f}" fill="#c9c9c3"/>')
        self._add(45, f'<rect x="{cx - 11:.1f}" y="{cy - 12:.1f}" width="22" height="24" rx="2.5" fill="#4a4845" stroke="#00000055" stroke-width=".7"/>'
                      f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="#1e1d1b"/>'
                      f'<circle cx="{cx:.1f}" cy="{cy - .6:.1f}" r="5.6" fill="#3b3936"/>')


    # ------------------------------------------- Stummel mit Signalname
    def stummel(self, b, sp, ze, name, farbe=GRUEN, laenge=None, schrift=5.4, z=50):
        """Kurzer Draht senkrecht vom Loch weg, am Ende ein gedrehter Signalname.
        Gleichnamige Stummel gelten als verbunden (Anschluss an anderer Stelle)."""
        x, y = b.xy(sp, ze)
        hoch = ze in TOP or ze in ("T+", "T-")
        if laenge is None:          # bis knapp hinter den Brettrand
            y2 = b.oy - 9 if hoch else b.oy + BRETT_H + 9
        else:
            y2 = y - laenge if hoch else y + laenge
        self.draht((b, sp, ze), (x, y2, "sig:" + name), farbe, name=f"Stummel {name} {sp}{ze}", z=z)
        self._add(z, f'<circle cx="{x:.1f}" cy="{y2:.1f}" r="2.3" fill="{farbe}" stroke="#00000044" stroke-width=".7"/>')
        ty = y2 - 4.5 if hoch else y2 + 4.5
        anker = "start" if hoch else "end"
        self.labels.append(
            f'<text transform="translate({x + schrift * 0.36:.1f} {ty:.1f}) rotate(-90)" font-size="{schrift}" '
            f'text-anchor="{anker}" fill="{TINTE}" font-weight="600">{html.escape(name)}</text>')

    # ------------------------------------------------ Oszillator-Baustein
    def oszillator(self, name, b, pin1_spalte, beschriftung="1 MHz"):
        """Quarzoszillator im DIP-14-Metallgehäuse mit nur vier Beinen
        (Pin 1, 7, 8, 14). Kerbe/Punkt an Pin 1."""
        h = 7
        x_l = b.xy(pin1_spalte, "e")[0]
        x_r = b.xy(pin1_spalte + h - 1, "e")[0]
        y_o = b.xy(1, "f")[1]
        y_u = b.xy(1, "e")[1]
        for pin, sp, ze in ((1, pin1_spalte, "e"), (7, pin1_spalte + 6, "e"),
                            (8, pin1_spalte + 6, "f"), (14, pin1_spalte, "f")):
            self._pin(f"{name}.{pin}", self._loch(b, sp, ze, f"{name}.{pin}"))
            x = b.xy(sp, ze)[0]
            y0, y1 = (y_u - 3, y_u + 4) if ze == "e" else (y_o - 4, y_o + 3)
            self._add(30, f'<rect x="{x - 1.6:.1f}" y="{y0:.1f}" width="3.2" height="{y1 - y0:.1f}" fill="#c9c9c3"/>')
        w = x_r - x_l + 2 * 5.5
        cx, cy = (x_l + x_r) / 2, (y_o + y_u) / 2
        self._add(31, f'<rect x="{x_l - 5.5:.1f}" y="{y_o + 2:.1f}" width="{w:.1f}" height="{y_u - y_o - 4:.1f}" rx="2.2" '
                      f'fill="#d8d9dc" stroke="#7d7f86" stroke-width=".9"/>'
                      f'<rect x="{x_l - 2.5:.1f}" y="{y_o + 5.5:.1f}" width="{w - 6:.1f}" height="{y_u - y_o - 11:.1f}" rx="1.6" fill="#eceef1"/>'
                      f'<circle cx="{x_l + 1.5:.1f}" cy="{y_u - 6:.1f}" r="1.5" fill="#7a7874"/>')
        self._add(33, f'<text x="{cx:.1f}" y="{cy - 1:.1f}" font-size="6.6" text-anchor="middle" fill="{ORANGE}" font-weight="700">{html.escape(name)}</text>'
                      f'<text x="{cx:.1f}" y="{cy + 7.6:.1f}" font-size="7.6" text-anchor="middle" fill="#4d5057" font-weight="600">{html.escape(beschriftung)}</text>')
        for pin, sp, ze in ((1, pin1_spalte, "e"), (7, pin1_spalte + 6, "e")):
            x = b.xy(sp, ze)[0]
            self._add(33, f'<text x="{x:.1f}" y="{y_u - 4.4:.1f}" font-size="3.7" text-anchor="middle" fill="#7d7f86">{pin}</text>')
        for pin, sp, ze in ((14, pin1_spalte, "f"), (8, pin1_spalte + 6, "f")):
            x = b.xy(sp, ze)[0]
            self._add(33, f'<text x="{x:.1f}" y="{y_o + 7.4:.1f}" font-size="3.7" text-anchor="middle" fill="#7d7f86">{pin}</text>')

    # --------------------------------------------------------- Stiftleiste
    def stiftleiste(self, name, b, sp, ze, n, beschriftungen=()):
        """Stiftleiste mit n Kontakten in einer Reihe, Pin 1 links. Reine Zahlen als
        Beschriftung stehen im Gehäuse, Namen darüber."""
        for k in range(n):
            self._pin(f"{name}.{k + 1}", self._loch(b, sp + k, ze, f"{name}.{k + 1}"))
        zahlen = bool(beschriftungen) and all(t.isdigit() for t in beschriftungen)
        x0 = b.xy(sp, ze)[0] - 5
        x1 = b.xy(sp + n - 1, ze)[0] + 5
        y = b.xy(sp, ze)[1]
        h = 15 if zahlen else 10
        self._add(40, f'<rect x="{x0:.1f}" y="{y - h / 2:.1f}" width="{x1 - x0:.1f}" height="{h}" rx="1.2" fill="#2f2d2b"/>')
        for k in range(n):
            x = b.xy(sp + k, ze)[0]
            self._add(41, f'<rect x="{x - 1.5:.1f}" y="{y + (2 if zahlen else 0) - 1.5:.1f}" width="3" height="3" fill="#e0c36a"/>')
        for k, t in enumerate(beschriftungen):
            x = b.xy(sp + k, ze)[0]
            if zahlen:
                self._add(42, f'<text x="{x:.1f}" y="{y - 1.6:.1f}" font-size="4.8" text-anchor="middle" fill="#e9e7e4" font-weight="600">{html.escape(t)}</text>')
            else:
                versatz = 9.5 if k % 2 == 0 else 15
                self.labels.append(f'<text x="{x:.1f}" y="{y - versatz:.1f}" font-size="4.4" text-anchor="middle" fill="{TINTE}" font-weight="600">{html.escape(t)}</text>')

    # ----------------------------------------------------------------- LED
    def led(self, name, b, anode, kathode, farbe="#e8392f"):
        """5-mm-LED zwischen zwei Löchern (Anode zuerst). Die Kathode ist das kürzere
        Bein und liegt auf der abgeflachten Seite des Gehäuses."""
        import math
        p, q = self._zwei(name, b, anode, kathode, ("A", "K"))
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        r = 9.5
        if abs(q[1] - p[1]) >= abs(q[0] - p[0]):
            cx, cy = mx, my
        else:
            cx, cy = mx, my - 12
        for pt in (p, q):
            d = math.hypot(pt[0] - cx, pt[1] - cy) or 1
            self._bein(pt, (cx + (pt[0] - cx) / d * r * 0.6, cy + (pt[1] - cy) / d * r * 0.6))
        ang = math.atan2(q[1] - cy, q[0] - cx) if (q != p) else 0
        self._add(45, f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="#2f5fb0" stroke="#00000044" stroke-width=".6"/>'
                      f'<g transform="translate({cx:.1f} {cy:.1f}) rotate({math.degrees(ang):.1f})">'
                      f'<path d="M{r * 0.42:.1f} {-r * 0.91:.1f} A{r} {r} 0 0 1 {r * 0.42:.1f} {r * 0.91:.1f} Z" fill="#dfe6f3"/>'
                      f'</g>'
                      f'<text x="{cx - 1:.1f}" y="{cy + 1.8:.1f}" font-size="5" text-anchor="middle" fill="#fff" font-weight="600">{html.escape(wert)}</text>')
        px, py = p
        self._add(46, f'<text x="{px + (cx - px) * 0.0:.1f}" y="{py:.1f}" font-size="0"> </text>')
        if beschriftung_pos:
            self.beschriftung(f"{name} {wert}", *beschriftung_pos[:2],
                              anker=beschriftung_pos[2] if len(beschriftung_pos) > 2 else "middle")

    def quarz(self, name, b, h1, h2, wert="1 MHz", beschriftung_pos=None, unter=False):
        p, q = self._zwei(name, b, h1, h2)
        import math
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        laenge = 30
        d = math.hypot(q[0] - p[0], q[1] - p[1])
        w = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        if abs(q[0] - p[0]) >= abs(q[1] - p[1]):
            cy = my + 11 if unter else my - 9
        else:
            cy = my
        self._bein(p, (mx - min(d / 2, 10) * 0, cy))
        self._bein(q, (mx, cy))
        self._add(45, f'<g transform="translate({mx:.1f} {cy:.1f})">'
                      f'<rect x="-{laenge / 2}" y="-6" width="{laenge}" height="12" rx="6" fill="#d8d9dc" stroke="#7d7f86" stroke-width=".8"/>'
                      f'<rect x="-{laenge / 2 - 3}" y="-3.4" width="{laenge - 6}" height="6.8" rx="3.4" fill="#eceef1"/>'
                      f'<text x="0" y="1.7" font-size="4.6" text-anchor="middle" fill="#5c5f66" font-weight="600">{html.escape(wert)}</text>'
                      f'</g>')

    def taster(self, name, b, spalte, links="o"):
        """Kleiner Taster über der Rinne: Beine in (spalte, e), (spalte+2, e),
        (spalte, f), (spalte+2, f). Die beiden Beine derselben Hälfte sind im
        Taster verbunden, gedrückt verbindet er die Hälften."""
        kn = {}
        for sp in (spalte, spalte + 2):
            for ze in ("e", "f"):
                k = self._loch(b, sp, ze, f"{name}.{sp}{ze}")
                kn[(sp, ze)] = k
                self._find(k)
        self._union(kn[(spalte, "e")], kn[(spalte + 2, "e")])
        self._union(kn[(spalte, "f")], kn[(spalte + 2, "f")])
        self._pin(f"{name}.1", kn[(spalte, "e")])
        self._pin(f"{name}.2", kn[(spalte, "f")])
        x1 = b.xy(spalte, "e")[0]
        x2 = b.xy(spalte + 2, "e")[0]
        y1 = b.xy(1, "f")[1]
        y2 = b.xy(1, "e")[1]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        for x in (x1, x2):
            self._add(40, f'<rect x="{x - 1.6:.1f}" y="{y1 - 3:.1f}" width="3.2" height="{y2 - y1 + 6:.1f}" fill="#c9c9c3"/>')
        self._add(45, f'<rect x="{cx - 11:.1f}" y="{cy - 12:.1f}" width="22" height="24" rx="2.5" fill="#4a4845" stroke="#00000055" stroke-width=".7"/>'
                      f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="#1e1d1b"/>'
                      f'<circle cx="{cx:.1f}" cy="{cy - .6:.1f}" r="5.6" fill="#3b3936"/>')


    # ------------------------------------------- Stummel mit Signalname
    def stummel(self, b, sp, ze, name, farbe=GRUEN, laenge=None, schrift=5.4, z=50):
        """Kurzer Draht senkrecht vom Loch weg, am Ende ein gedrehter Signalname.
        Gleichnamige Stummel gelten als verbunden (Anschluss an anderer Stelle)."""
        x, y = b.xy(sp, ze)
        hoch = ze in TOP or ze in ("T+", "T-")
        if laenge is None:          # bis knapp hinter den Brettrand
            y2 = b.oy - 9 if hoch else b.oy + BRETT_H + 9
        else:
            y2 = y - laenge if hoch else y + laenge
        self.draht((b, sp, ze), (x, y2, "sig:" + name), farbe, name=f"Stummel {name} {sp}{ze}", z=z)
        self._add(z, f'<circle cx="{x:.1f}" cy="{y2:.1f}" r="2.3" fill="{farbe}" stroke="#00000044" stroke-width=".7"/>')
        ty = y2 - 4.5 if hoch else y2 + 4.5
        anker = "start" if hoch else "end"
        self.labels.append(
            f'<text transform="translate({x + schrift * 0.36:.1f} {ty:.1f}) rotate(-90)" font-size="{schrift}" '
            f'text-anchor="{anker}" fill="{TINTE}" font-weight="600">{html.escape(name)}</text>')

    # ------------------------------------------------ Oszillator-Baustein
    def oszillator(self, name, b, pin1_spalte, beschriftung="1 MHz"):
        """Quarzoszillator im DIP-14-Metallgehäuse mit nur vier Beinen
        (Pin 1, 7, 8, 14). Kerbe/Punkt an Pin 1."""
        h = 7
        x_l = b.xy(pin1_spalte, "e")[0]
        x_r = b.xy(pin1_spalte + h - 1, "e")[0]
        y_o = b.xy(1, "f")[1]
        y_u = b.xy(1, "e")[1]
        for pin, sp, ze in ((1, pin1_spalte, "e"), (7, pin1_spalte + 6, "e"),
                            (8, pin1_spalte + 6, "f"), (14, pin1_spalte, "f")):
            self._pin(f"{name}.{pin}", self._loch(b, sp, ze, f"{name}.{pin}"))
            x = b.xy(sp, ze)[0]
            y0, y1 = (y_u - 3, y_u + 4) if ze == "e" else (y_o - 4, y_o + 3)
            self._add(30, f'<rect x="{x - 1.6:.1f}" y="{y0:.1f}" width="3.2" height="{y1 - y0:.1f}" fill="#c9c9c3"/>')
        w = x_r - x_l + 2 * 5.5
        cx, cy = (x_l + x_r) / 2, (y_o + y_u) / 2
        self._add(31, f'<rect x="{x_l - 5.5:.1f}" y="{y_o + 2:.1f}" width="{w:.1f}" height="{y_u - y_o - 4:.1f}" rx="2.2" '
                      f'fill="#d8d9dc" stroke="#7d7f86" stroke-width=".9"/>'
                      f'<rect x="{x_l - 2.5:.1f}" y="{y_o + 5.5:.1f}" width="{w - 6:.1f}" height="{y_u - y_o - 11:.1f}" rx="1.6" fill="#eceef1"/>'
                      f'<circle cx="{x_l + 1.5:.1f}" cy="{y_u - 6:.1f}" r="1.5" fill="#7a7874"/>')
        self._add(33, f'<text x="{cx:.1f}" y="{cy - 1:.1f}" font-size="6.6" text-anchor="middle" fill="{ORANGE}" font-weight="700">{html.escape(name)}</text>'
                      f'<text x="{cx:.1f}" y="{cy + 7.6:.1f}" font-size="7.6" text-anchor="middle" fill="#4d5057" font-weight="600">{html.escape(beschriftung)}</text>')
        for pin, sp, ze in ((1, pin1_spalte, "e"), (7, pin1_spalte + 6, "e")):
            x = b.xy(sp, ze)[0]
            self._add(33, f'<text x="{x:.1f}" y="{y_u - 4.4:.1f}" font-size="3.7" text-anchor="middle" fill="#7d7f86">{pin}</text>')
        for pin, sp, ze in ((14, pin1_spalte, "f"), (8, pin1_spalte + 6, "f")):
            x = b.xy(sp, ze)[0]
            self._add(33, f'<text x="{x:.1f}" y="{y_o + 7.4:.1f}" font-size="3.7" text-anchor="middle" fill="#7d7f86">{pin}</text>')

    # --------------------------------------------------------- Stiftleiste
    def stiftleiste(self, name, b, sp, ze, n, beschriftungen=()):
        """Stiftleiste mit n Kontakten in einer Reihe, Pin 1 links."""
        for k in range(n):
            self._pin(f"{name}.{k + 1}", self._loch(b, sp + k, ze, f"{name}.{k + 1}"))
        x0 = b.xy(sp, ze)[0] - 5
        x1 = b.xy(sp + n - 1, ze)[0] + 5
        y = b.xy(sp, ze)[1]
        self._add(40, f'<rect x="{x0:.1f}" y="{y - 5:.1f}" width="{x1 - x0:.1f}" height="10" rx="1.2" fill="#2f2d2b"/>')
        for k in range(n):
            x = b.xy(sp + k, ze)[0]
            self._add(41, f'<rect x="{x - 1.5:.1f}" y="{y - 1.5:.1f}" width="3" height="3" fill="#e0c36a"/>')
        for k, t in enumerate(beschriftungen):
            x = b.xy(sp + k, ze)[0]
            versatz = 9.5 if k % 2 == 0 else 15      # versetzt, damit die Namen nicht überlappen
            self.labels.append(f'<text x="{x:.1f}" y="{y - versatz:.1f}" font-size="4.4" text-anchor="middle" fill="{TINTE}" font-weight="600">{html.escape(t)}</text>')


    # ----------------------------------------------------------------- LED
    def led(self, name, b, anode, kathode, farbe="#e8392f"):
        """5-mm-LED zwischen zwei Löchern (Anode zuerst). Die Kathode ist das kürzere
        Bein und liegt auf der abgeflachten Seite des Gehäuses."""
        import math
        p, q = self._zwei(name, b, anode, kathode, ("A", "K"))
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        r = 9.5
        if abs(q[1] - p[1]) >= abs(q[0] - p[0]):
            cx, cy = mx, my
        else:
            cx, cy = mx, my - 12
        for pt, ver in ((p, 0.0), (q, 4.0)):
            self._bein(pt, (cx + (pt[0] - cx) * 0.0, cy + (pt[1] - cy) * 0.35 + (ver if pt is q else 0) * 0))
        ang = math.atan2(q[1] - cy, q[0] - cx)
        self._add(45, f'<g transform="translate({cx:.1f} {cy:.1f})">'
                      f'<circle r="{r}" fill="{farbe}" stroke="#00000055" stroke-width=".8"/>'
                      f'<circle r="{r - 3.4}" fill="#ffffff" fill-opacity=".28"/>'
                      f'<ellipse cx="{-r * 0.32:.1f}" cy="{-r * 0.38:.1f}" rx="2.6" ry="1.6" fill="#ffffff" fill-opacity=".7" transform="rotate(-30 {-r * 0.32:.1f} {-r * 0.38:.1f})"/>'
                      f'<path d="M{(r - 0.2) * math.cos(ang) - 6 * math.sin(ang):.1f} {(r - 0.2) * math.sin(ang) + 6 * math.cos(ang):.1f} '
                      f'L{(r - 0.2) * math.cos(ang) + 6 * math.sin(ang):.1f} {(r - 0.2) * math.sin(ang) - 6 * math.cos(ang):.1f}" '
                      f'stroke="#00000066" stroke-width="1.6"/>'
                      f'</g>')

    # ------------------------------------------------------------- Trimmer
    def trimmer(self, name, b, sp, ze, wert="10k"):
        """Trimmpotentiometer mit drei Beinen nebeneinander (Pin 1, 2 = Schleifer, 3)."""
        for k in range(3):
            self._pin(f"{name}.{k + 1}", self._loch(b, sp + k, ze, f"{name}.{k + 1}"))
        cx, cy = b.xy(sp + 1, ze)[0], b.xy(sp + 1, ze)[1] - 9
        for k in range(3):
            x = b.xy(sp + k, ze)[0]
            self._add(40, f'<rect x="{x - 1.4:.1f}" y="{cy:.1f}" width="2.8" height="{b.xy(sp, ze)[1] - cy + 3:.1f}" fill="#c9c9c3"/>')
        self._add(45, f'<rect x="{cx - 14:.1f}" y="{cy - 12:.1f}" width="28" height="22" rx="2.2" fill="#2f6fb8" stroke="#00000044" stroke-width=".8"/>'
                      f'<circle cx="{cx:.1f}" cy="{cy - 1:.1f}" r="6.4" fill="#e9eef5" stroke="#00000044" stroke-width=".7"/>'
                      f'<path d="M{cx - 4.6:.1f} {cy - 1:.1f} L{cx + 4.6:.1f} {cy - 1:.1f}" stroke="#555" stroke-width="1.4"/>'
                      f'<text x="{cx:.1f}" y="{cy + 7.6:.1f}" font-size="4.4" text-anchor="middle" fill="#fff" font-weight="700">{html.escape(wert)}</text>')


    # ------------------------------------------- LCD-Modul mit Flachbandkabel
    def lcd_modul(self, b, sp_von, sp_bis, ze, y_unten, zeilen=(), cursor=None, hoehe=213, titel="LCD 4 × 40"):
        """Zeichnet ein Textdisplay (4 × 40 Zeichen) in Originalgröße über dem Steckbrett. Es ist
        am rechten Rand abgebrochen dargestellt. Ein 18-poliges Flachbandkabel führt von seinem
        Anschluss zur Stiftleiste auf dem Steckbrett (Pin 1: rote Ader). Rein grafisch."""
        xl = b.xy(sp_von, ze)[0] - 6
        xr = b.xy(sp_bis, ze)[0] + 6
        y_h = b.xy(sp_von, ze)[1]
        # Kabel
        self._add(46, f'<rect x="{xl:.1f}" y="{y_unten:.1f}" width="{xr - xl:.1f}" height="{y_h - 6 - y_unten:.1f}" fill="#d9d8d3" stroke="#a9a8a2" stroke-width=".6"/>'
                      f'<rect x="{xl:.1f}" y="{y_unten:.1f}" width="3.4" height="{y_h - 6 - y_unten:.1f}" fill="#c0392b"/>'
                      + "".join(f'<line x1="{xl + 5 + 10 * k:.1f}" y1="{y_unten:.1f}" x2="{xl + 5 + 10 * k:.1f}" y2="{y_h - 6:.1f}" stroke="#bdbcb6" stroke-width=".8"/>'
                                for k in range(1, 18)))
        # Stecker auf der Stiftleiste (Brett) und am Modul
        for yy, dir_ in ((y_h - 9, 1), (y_unten - 8, -1)):
            self._add(47, f'<rect x="{xl - 2:.1f}" y="{yy:.1f}" width="{xr - xl + 4:.1f}" height="17" rx="1.6" fill="#2b2a28" stroke="#00000055" stroke-width=".6"/>'
                          f'<rect x="{xl + 3:.1f}" y="{yy + 6:.1f}" width="{xr - xl - 6:.1f}" height="5" rx="1" fill="#3d3b38"/>')
        # Modul
        pl, pr = b.ox + 4, b.ox + b.breite - 2
        pt = y_unten - hoehe
        o = [f'<rect x="{pl:.1f}" y="{pt:.1f}" width="{pr - pl:.1f}" height="{y_unten - pt:.1f}" rx="3" fill="#20303f" stroke="#0e161e" stroke-width="1.2"/>']
        for cx_, cy_ in ((pl + 9, pt + 9), (pl + 9, y_unten - 22)):
            o.append(f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="3.6" fill="#0e161e"/><circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="2" fill="#c9ccd2"/>')
        # Blende und Glas
        bx, by = pl + 20, pt + 22
        bw, bh = pr - bx + 8, 124
        o.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh}" rx="2" fill="#3a3c41" stroke="#1b1c1f" stroke-width="1"/>')
        gx, gy, gw, gh = bx + 8, by + 8, bw, bh - 16
        o.append(f'<rect x="{gx:.1f}" y="{gy:.1f}" width="{gw:.1f}" height="{gh}" fill="#8FA6EA" stroke="#6F83C8" stroke-width="1.2"/>')
        zw, zh = 11.4, 25.5               # Zelle: Breite, Zeilenabstand
        x0z, y0z = gx + 6, gy + 6
        ncol = int((gw - 8) // zw)
        for r in range(4):
            for c in range(ncol):
                o.append(f'<rect x="{x0z + c * zw:.1f}" y="{y0z + r * zh:.1f}" width="{zw - 1.6:.1f}" height="{zh - 6:.1f}" fill="#1F2B63" fill-opacity=".09"/>')
        for r, text in enumerate(zeilen):
            if text:
                t = text[:ncol]
                o.append(f'<text x="{x0z:.1f}" y="{y0z + r * zh + zh - 9.6:.1f}" font-family="Courier New, Courier, monospace" '
                         f'font-size="17" font-weight="700" fill="#1F2B63" textLength="{len(t) * zw - 1.6:.1f}" lengthAdjust="spacing">{html.escape(t)}</text>')
        if cursor:
            c, r = cursor
            o.append(f'<rect x="{x0z + c * zw:.1f}" y="{y0z + r * zh:.1f}" width="{zw - 1.6:.1f}" height="{zh - 6:.1f}" fill="#1F2B63"/>')
        # Beschriftung auf der Platine
        o.append(f'<text x="{pl + 22:.1f}" y="{y_unten - 22:.1f}" font-size="9" fill="#9fb3c8" font-weight="700">{html.escape(titel)}</text>')
        # Abgebrochener rechter Rand
        zack = " ".join(f"{pr + (3 if k % 2 else -4):.1f},{pt - 6 + k * (y_unten - pt + 12) / 16:.1f}" for k in range(17))
        o.append(f'<polygon points="{pr + 14:.1f},{pt - 8:.1f} {zack} {pr + 14:.1f},{y_unten + 8:.1f}" fill="#ffffff"/>')
        self._add(44, "".join(o))


    # --------------------------------------------------------- Ferritperle
    def ferrit(self, name, b, h1, h2):
        """Bedrahtete Ferritperle (Drossel), liegt wie ein Widerstand zwischen zwei Löchern."""
        p, q = self._zwei(name, b, h1, h2)
        (mx, my), w, (a, c), art = self._koerper_pose(p, q, 20)
        if art == "flach":
            self._bein(p, a)
            self._bein(q, c)
        else:
            self._bein(p, a if p[0] <= q[0] else c)
            self._bein(q, (q[0], (c if p[0] <= q[0] else a)[1]))
        self._add(45, f'<g transform="translate({mx:.1f} {my:.1f}) rotate({w:.1f})">'
                      f'<rect x="-10" y="-4.4" width="20" height="8.8" rx="2" fill="#2c2c30" stroke="#00000066" stroke-width=".7"/>'
                      f'<rect x="-10" y="-4.4" width="3.2" height="8.8" rx="1" fill="#b8bcc4"/>'
                      f'<rect x="6.8" y="-4.4" width="3.2" height="8.8" rx="1" fill="#b8bcc4"/>'
                      f'<rect x="-4" y="-2" width="8" height="1.6" fill="#55565c"/></g>')

    # ----------------------------------------------------------- Transistor
    def transistor(self, name, b, sp, ze, beschriftung="2N2222"):
        """Transistor im TO-92-Gehäuse, flache Seite zum Betrachter: Beine von links nach
        rechts Emitter, Basis, Kollektor (E, B, C), in drei nebeneinanderliegenden Löchern."""
        namen = ("E", "B", "C")
        for k in range(3):
            self._pin(f"{name}.{namen[k]}", self._loch(b, sp + k, ze, f"{name}.{namen[k]}"))
        x1, y = b.xy(sp, ze)
        x3 = b.xy(sp + 2, ze)[0]
        cx = (x1 + x3) / 2
        for k in range(3):
            x = b.xy(sp + k, ze)[0]
            self._add(40, f'<rect x="{x - 1.2:.1f}" y="{y - 9:.1f}" width="2.4" height="9" fill="#c9c9c3"/>')
        self._add(45, f'<path d="M{cx - 12:.1f} {y - 8:.1f} L{cx - 12:.1f} {y - 15:.1f} A12 12 0 0 1 {cx + 12:.1f} {y - 15:.1f} L{cx + 12:.1f} {y - 8:.1f} Z" '
                      f'fill="#2b2b2e" stroke="#00000066" stroke-width=".8"/>'
                      f'<text x="{cx:.1f}" y="{y - 11.4:.1f}" font-size="4.2" text-anchor="middle" fill="#d9d9dc" font-weight="600">{html.escape(beschriftung)}</text>')


    # -------------------------------------------------------- Tastatur-Modul
    def tastatur_modul(self, b, sp_von, sp_bis, y_unten, hoehe=118, titel="89 Tasten"):
        """Zeichnet eine Notebook-Tastatur (nicht maßstäblich) über dem Steckbrett, mit einer
        Reihe Lötpads an der Unterkante. Gibt die x-Positionen der Pads (über den Spalten
        sp_von..sp_bis) und ihre y-Lage zurück. Rein grafisch."""
        pl, pr = b.ox + 2, b.ox + b.breite - 2
        pt = y_unten - hoehe
        o = [f'<rect x="{pl:.1f}" y="{pt:.1f}" width="{pr - pl:.1f}" height="{hoehe}" rx="4" fill="#2f3135" stroke="#17181a" stroke-width="1.2"/>']
        reihen = [(15, 0.8), (15, 1.0), (15, 1.0), (14, 1.0), (13, 1.0), (10, 1.0)]
        ky = pt + 7
        kh = 14.6
        for n_tasten, _f in reihen:
            kw = (pr - pl - 14 - (n_tasten - 1) * 2.4) / n_tasten
            x = pl + 7
            for k in range(n_tasten):
                breite = kw
                if n_tasten == 10 and k == 3:
                    breite = kw * 3.6
                if n_tasten == 10 and k > 3:
                    pass
                if x + breite > pr - 6:
                    break
                o.append(f'<rect x="{x:.1f}" y="{ky:.1f}" width="{breite:.1f}" height="{kh - 1:.1f}" rx="2" fill="#4a4d52" stroke="#25272a" stroke-width=".6"/>'
                         f'<rect x="{x + 1.4:.1f}" y="{ky + 1.2:.1f}" width="{breite - 2.8:.1f}" height="{kh - 4.4:.1f}" rx="1.4" fill="#5b5f65"/>')
                x += breite + 2.4
            ky += kh + 2.2
        # Leiste mit Lötpads
        xl = b.xy(sp_von, "c")[0] - 6
        xr = b.xy(sp_bis, "c")[0] + 6
        o.append(f'<rect x="{xl:.1f}" y="{y_unten - 9:.1f}" width="{xr - xl:.1f}" height="9" rx="1" fill="#c8a24a" stroke="#00000044" stroke-width=".6"/>')
        xs = []
        for sp in range(sp_von, sp_bis + 1):
            x = b.xy(sp, "c")[0]
            xs.append(x)
            o.append(f'<circle cx="{x:.1f}" cy="{y_unten - 4.5:.1f}" r="2.6" fill="#e8d28a" stroke="#00000055" stroke-width=".5"/>')
        o.append(f'<text x="{pl + 8:.1f}" y="{y_unten - 14:.1f}" font-size="8" fill="#9aa0a8" font-weight="700">{html.escape(titel)}</text>')
        self._add(44, "".join(o))
        return xs, y_unten - 4.5

    # ------------------------------------------------------- Stromschienen
    def schiene_beschriften(self, b):
        pass

    # ------------------------------------------------------- Netzprüfung
    def _netz_von(self, pin):
        return self._find(self.pins[pin])

    def pruefe(self, netze, offen=()):
        """netze: Liste von Mengen aus Pin-/Extern-Namen ('IC1.3', 'ext:GND').
        Jedes Netz muss zusammenhängen, und zwischen verschiedenen Netzen darf
        keine Verbindung bestehen. Pins in `offen` müssen unverbunden sein.
        Nicht genannte Pins der Bauteile gelten als Fehler."""
        ausnahmen = []
        benannt = set()
        for netz in netze:
            wurzeln = set()
            for n in netz:
                benannt.add(n)
                if n.startswith(("ext:", "sig:")):
                    wurzeln.add(self._find(("ext", n)))
                else:
                    if n not in self.pins:
                        ausnahmen.append(f"unbekannter Pin {n}")
                        continue
                    wurzeln.add(self._find(self.pins[n]))
            if len(wurzeln) > 1:
                ausnahmen.append(f"Netz {sorted(netz)} ist NICHT verbunden")
        # Zusammenfassen der Wurzeln je Netz und Vergleich
        wurzel_zu_netz = {}
        for i, netz in enumerate(netze):
            for n in netz:
                if n.startswith(("ext:", "sig:")):
                    w = self._find(("ext", n))
                elif n in self.pins:
                    w = self._find(self.pins[n])
                else:
                    continue
                if w in wurzel_zu_netz and wurzel_zu_netz[w] != i:
                    ausnahmen.append(
                        f"Netze {sorted(netze[wurzel_zu_netz[w]])} und {sorted(netz)} sind kurzgeschlossen")
                wurzel_zu_netz[w] = i
        for n in offen:
            benannt.add(n)
            w = self._find(self.pins[n])
            andere = [p for p in self.pins if p != n and self._find(self.pins[p]) == w]
            if andere:
                ausnahmen.append(f"Pin {n} sollte offen sein, hängt aber an {sorted(andere)}")
        nicht = [p for p in self.alle_pins if p not in benannt]
        if nicht:
            ausnahmen.append(f"Pins ohne Vorgabe: {nicht}")
        if ausnahmen:
            raise AssertionError("Netzprüfung fehlgeschlagen:\n  " + "\n  ".join(ausnahmen))

    # -------------------------------------------------------------- SVG
    def _brett_svg(self, b, zeigt_schienen=True):
        o = []
        x0, y0, w, h = b.ox, b.oy, b.breite, BRETT_H
        o.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="5" fill="{PLATINE}" stroke="{PLATINE_R}" stroke-width="1.2"/>')
        # Rinne
        ry1 = b.xy(1, "f")[1] + 7.5
        ry2 = b.xy(1, "e")[1] - 7.5
        o.append(f'<rect x="{x0 + 1}" y="{ry1}" width="{w - 2}" height="{ry2 - ry1}" fill="{RINNE}"/>')
        # Schienenlinien
        xa, xe = b.xy(1, "a")[0] - 9, b.xy(b.n, "a")[0] + 9
        for zeile, farbe in (("T+", ROT), ("T-", BLAU), ("B+", ROT), ("B-", BLAU)):
            y = b.xy(1, zeile)[1]
            dy = -7 if zeile in ("T+", "T-") else 7
            dy = -7 if zeile in ("T-", "B+") else 7
            # Linie außen an der jeweiligen Schiene
            if zeile in ("T-", "B-"):
                yl = y + (-7 if zeile == "T-" else 7)
            else:
                yl = y + (7 if zeile == "T+" else -7)
            o.append(f'<line x1="{xa:.1f}" y1="{yl:.1f}" x2="{xe:.1f}" y2="{yl:.1f}" stroke="{farbe}" stroke-width=".9" stroke-opacity=".75"/>')
            o.append(f'<text x="{xa - 4:.1f}" y="{y + 2.2:.1f}" font-size="6.5" text-anchor="end" fill="{farbe}" font-weight="700">{"+" if "+" in zeile else "−"}</text>')
        # Löcher
        for s in range(1, b.n + 1):
            x = b.xy(s, "a")[0]
            for zeile in "jihgfedcba":
                y = b.xy(s, zeile)[1]
                o.append(f'<rect x="{x - 2.1:.1f}" y="{y - 2.1:.1f}" width="4.2" height="4.2" rx=".9" fill="{LOCH}"/>')
            for zeile in ("T+", "T-", "B+", "B-"):
                if (s - 1) % 6 == 5:      # kleine Lücken wie beim echten Brett
                    continue
                y = b.xy(s, zeile)[1]
                o.append(f'<rect x="{x - 2.1:.1f}" y="{y - 2.1:.1f}" width="4.2" height="4.2" rx=".9" fill="{LOCH}"/>')
            if s == 1 or s % 5 == 0:
                o.append(f'<text x="{x:.1f}" y="{b.xy(1, "j")[1] - 6.5:.1f}" font-size="4.6" text-anchor="middle" fill="{GRAU}">{s}</text>')
        for zeile in "jihgf":
            y = b.xy(1, zeile)[1]
            o.append(f'<text x="{x0 + 6:.1f}" y="{y + 1.6:.1f}" font-size="4.6" text-anchor="middle" fill="{GRAU}">{zeile}</text>')
        for zeile in "edcba":
            y = b.xy(1, zeile)[1]
            o.append(f'<text x="{x0 + 6:.1f}" y="{y + 1.6:.1f}" font-size="4.6" text-anchor="middle" fill="{GRAU}">{zeile}</text>')
        return "\n".join(o)

    def svg(self, rand=6, extra_links=0, extra_rechts=0, extra_oben=0, extra_unten=0,
            titel="", beschr="", ausschnitt=None):
        x0 = min(b.ox for b in self.bretter) - rand - extra_links
        y0 = min(b.oy for b in self.bretter) - rand - extra_oben
        x1 = max(b.ox + b.breite for b in self.bretter) + rand + extra_rechts
        y1 = max(b.oy + BRETT_H for b in self.bretter) + rand + extra_unten
        if ausschnitt:
            x0, y0, x1, y1 = ausschnitt
        w, h = x1 - x0, y1 - y0
        teile = "\n".join(t for _, t in sorted(self.teile, key=lambda t: t[0]))
        bretter = "\n".join(self._brett_svg(b) for b in self.bretter)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" '
                f'font-family="Helvetica, Arial, sans-serif" role="img" aria-label="{html.escape(beschr)}">\n'
                f'<title>{html.escape(titel)}</title>\n'
                f'{bretter}\n{teile}\n' + "\n".join(self.labels) + '\n</svg>\n')
