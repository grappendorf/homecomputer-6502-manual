"""Zeichnet Schaltpläne im Stil des Buches (SVG) und leitet die Netzliste aus der
Zeichnung ab, damit sie gegen die Steckbrett-Zeichnungen geprüft werden kann.

Verbunden sind Drahtenden, Bauteilanschlüsse und Drahtknicke, die auf demselben
Punkt liegen. Ein Drahtende mitten auf einem anderen Draht gilt ebenfalls als
Verbindung (mit Knotenpunkt). Kreuzungen ohne Knotenpunkt verbinden nichts.
Versorgungssymbole und Netzfahnen gleichen Namens sind verbunden."""
import html

TINTE = "#2A2826"
GRAU = "#6f6d69"
GRAU_H = "#9a9893"
ORANGE = "#E4643C"
ORANGE_D = "#B8481F"
LCD = "#eef1fb"
LCD_R = "#6F83C8"
FONT = "Helvetica, Arial, sans-serif"
W = 1.4                      # Linienstärke


def _t(text):
    return html.escape(text)


class Plan:
    def __init__(self):
        self.o = []              # SVG-Elemente (Bauteile, Text)
        self.draehte = []        # Polylinien
        self.pins = {}           # Name -> (x, y)
        self.punkte = []         # Knotenpunkte
        self._uf = {}
        self.namen = {}          # Netzname -> Liste von Punkten
        self.xmin = self.ymin = 1e9
        self.xmax = self.ymax = -1e9
        self.no_connect = set()
        self.namenspunkte = []

    # -------------------------------------------------------- Union-Find
    def _find(self, k):
        self._uf.setdefault(k, k)
        while self._uf[k] != k:
            self._uf[k] = self._uf[self._uf[k]]
            k = self._uf[k]
        return k

    def _union(self, a, b):
        self._uf[self._find(a)] = self._find(b)

    def _box(self, x, y, r=0):
        self.xmin, self.xmax = min(self.xmin, x - r), max(self.xmax, x + r)
        self.ymin, self.ymax = min(self.ymin, y - r), max(self.ymax, y + r)

    # ---------------------------------------------------------- Drähte
    def draht(self, *pts):
        for p in pts:
            self._box(*p)
        for a, b in zip(pts, pts[1:]):
            self._union(a, b)
        self.draehte.append(pts)

    def knoten(self, x, y):
        self.punkte.append((x, y))

    def _auto_t_verbindungen(self):
        """Drahtende auf einem fremden Drahtsegment: verbinden und Punkt setzen."""
        segmente = []
        for i, w in enumerate(self.draehte):
            for a, b in zip(w, w[1:]):
                segmente.append((i, a, b))
        for i, w in enumerate(self.draehte):
            for ende in (w[0], w[-1]):
                for j, a, b in segmente:
                    if j == i:
                        continue
                    if a[0] == b[0] == ende[0] and min(a[1], b[1]) < ende[1] < max(a[1], b[1]):
                        self._union(ende, a)
                        self.punkte.append(ende)
                    elif a[1] == b[1] == ende[1] and min(a[0], b[0]) < ende[0] < max(a[0], b[0]):
                        self._union(ende, a)
                        self.punkte.append(ende)

    def _namen_auf_draehten(self):
        """Mit netzname() benannte Punkte, die auf einem Draht liegen, gehören zu ihm."""
        for (x, y) in self.namenspunkte:
            for w in self.draehte:
                for a, b in zip(w, w[1:]):
                    if ((a[0] == b[0] == x and min(a[1], b[1]) <= y <= max(a[1], b[1])) or
                            (a[1] == b[1] == y and min(a[0], b[0]) <= x <= max(a[0], b[0]))):
                        self._union((x, y), a)

    def _pin(self, name, x, y):
        self.pins[name] = (x, y)
        self._find((x, y))
        self._box(x, y, 2)

    # -------------------------------------------------------- Zeichnen
    def linie(self, x1, y1, x2, y2, farbe=TINTE, w=W, dash=None):
        self._box(x1, y1)
        self._box(x2, y2)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{farbe}" stroke-width="{w}" stroke-linecap="round"{d}/>')

    def text(self, s, x, y, groesse=8, anker="start", farbe=TINTE, gewicht=400):
        w = len(s) * groesse * 0.56
        a, b = {"start": (0, w), "end": (-w, 0), "middle": (-w / 2, w / 2)}[anker]
        self._box(x + a, y - groesse, 0)
        self._box(x + b, y + 2, 0)
        self.o.append(f'<text x="{x}" y="{y}" font-size="{groesse}" text-anchor="{anker}" fill="{farbe}" '
                      f'font-weight="{gewicht}">{_t(s)}</text>')

    def bez(self, name, wert, x, y, anker="start"):
        """Bezeichnung (fett) und Wert (grau) untereinander."""
        self.text(name, x, y, 8.5, anker, TINTE, 700)
        if wert:
            self.text(wert, x, y + 9.5, 8, anker, GRAU)

    def pinnr(self, nr, x, y, anker="middle"):
        self.text(str(nr), x, y, 6.2, anker, GRAU_H)

    # ----------------------------------------------------- Versorgung
    def vcc(self, x, y, name="ext:+5V"):
        self._union((x, y), name)
        self._box(x, y - 12, 6)
        self.o.append(f'<path d="M{x} {y} L{x} {y - 8}" stroke="{ORANGE_D}" stroke-width="{W}" fill="none"/>'
                      f'<path d="M{x - 4.5} {y - 8} L{x + 4.5} {y - 8} L{x} {y - 14} Z" fill="{ORANGE}" stroke="{ORANGE_D}" stroke-width=".8" stroke-linejoin="round"/>')
        self.text("+5 V", x + 7, y - 9, 7.5, "start", ORANGE_D, 700)

    def vcc9(self, x, y):
        """+9-V-Versorgung (nur für den SID)."""
        self._union((x, y), "ext:+9V")
        self._box(x, y - 12, 6)
        self.o.append(f'<path d="M{x} {y} L{x} {y - 8}" stroke="{ORANGE_D}" stroke-width="{W}" fill="none"/>'
                      f'<path d="M{x - 4.5} {y - 8} L{x + 4.5} {y - 8} L{x} {y - 14} Z" fill="{ORANGE}" stroke="{ORANGE_D}" stroke-width=".8" stroke-linejoin="round"/>')
        self.text("+9 V", x + 7, y - 9, 7.5, "start", ORANGE_D, 700)

    def gnd(self, x, y, name="ext:GND"):
        self._union((x, y), name)
        self._box(x, y + 10, 6)
        c = GRAU
        self.o.append(f'<path d="M{x} {y} L{x} {y + 3}" stroke="{c}" stroke-width="{W}" fill="none"/>'
                      f'<path d="M{x - 7} {y + 3} H{x + 7} M{x - 4.6} {y + 6.4} H{x + 4.6} M{x - 2.2} {y + 9.8} H{x + 2.2}" '
                      f'stroke="{c}" stroke-width="{W}" stroke-linecap="round" fill="none"/>')

    def fahne(self, x, y, name, rechts=True):
        """Netzfahne: Signal verlässt die Zeichnung (oder kommt herein). Flach genug
        für Pins im Abstand 10."""
        self._union((x, y), "sig:" + name)
        h, spitze = 4.2, 4.2
        b = 5 + 4.1 * len(name)
        if rechts:
            pts = f"{x},{y} {x + spitze},{y - h} {x + spitze + b},{y - h} {x + spitze + b},{y + h} {x + spitze},{y + h}"
            tx = x + spitze + 3
        else:
            pts = f"{x},{y} {x - spitze},{y - h} {x - spitze - b},{y - h} {x - spitze - b},{y + h} {x - spitze},{y + h}"
            tx = x - spitze - b + 2
        self._box(x + (spitze + b if rechts else -spitze - b), y, 2)
        self.o.append(f'<polygon points="{pts}" fill="#fff" stroke="{ORANGE}" stroke-width="1.1" stroke-linejoin="round"/>')
        self.text(name, tx, y + 2.5, 7, "start", ORANGE_D, 700)

    # ------------------------------------------------------ Bauteile
    def widerstand(self, name, x, y, wert, senkrecht=True, pins=("1", "2"), beschr="rechts"):
        """Pins: senkrecht (oben, unten), waagerecht (links, rechts), je 20 vom Mittelpunkt."""
        if senkrecht:
            p1, p2 = (x, y - 20), (x, y + 20)
            self.linie(x, y - 20, x, y - 9)
            self.linie(x, y + 9, x, y + 20)
            self.o.append(f'<rect x="{x - 4.5}" y="{y - 9}" width="9" height="18" rx="1.2" fill="#fff" stroke="{TINTE}" stroke-width="{W}"/>')
            if beschr == "rechts":
                self.bez(name, wert, x + 9, y - 1)
            elif beschr == "links":
                self.bez(name, wert, x - 9, y - 1, "end")
        else:
            p1, p2 = (x - 20, y), (x + 20, y)
            self.linie(x - 20, y, x - 9, y)
            self.linie(x + 9, y, x + 20, y)
            self.o.append(f'<rect x="{x - 9}" y="{y - 4.5}" width="18" height="9" rx="1.2" fill="#fff" stroke="{TINTE}" stroke-width="{W}"/>')
            if beschr == "unten":
                self.bez(name, wert, x, y + 17, "middle")
            else:
                self.bez(name, wert, x, y - 14 - (9.5 if wert else 0), "middle")
        self._pin(f"{name}.{pins[0]}", *p1)
        self._pin(f"{name}.{pins[1]}", *p2)

    def kondensator(self, name, x, y, wert, senkrecht=True, pins=("1", "2"), elko=False, beschr="rechts", laenge=20):
        """senkrecht: pins (oben, unten). Elko: zweiter Anschluss (unten/rechts) ist Minus; pins ('+','-')."""
        if senkrecht:
            p1, p2 = (x, y - laenge), (x, y + laenge)
            self.linie(x, y - laenge, x, y - 2.6)
            self.linie(x, y + 2.6, x, y + laenge)
            self.linie(x - 8, y - 2.6, x + 8, y - 2.6)
            if elko:
                self.o.append(f'<path d="M{x - 8} {y + 6.5} Q{x} {y + 1.2} {x + 8} {y + 6.5}" fill="none" stroke="{TINTE}" stroke-width="{W}"/>')
                self.linie(x, y + 4.6, x, y + laenge)
                self.text("+", x - 9, y - 6, 8, "end", TINTE, 700)
            else:
                self.linie(x - 8, y + 2.6, x + 8, y + 2.6)
            if beschr == "rechts":
                self.bez(name, wert, x + 11, y - 1)
            elif beschr == "links":
                self.bez(name, wert, x - 11, y - 1, "end")
        else:
            p1, p2 = (x - laenge, y), (x + laenge, y)
            self.linie(x - laenge, y, x - 2.6, y)
            self.linie(x + 2.6, y, x + laenge, y)
            self.linie(x - 2.6, y - 8, x - 2.6, y + 8)
            self.linie(x + 2.6, y - 8, x + 2.6, y + 8)
            if beschr == "unten":
                self.bez(name, wert, x, y + 19, "middle")
            else:
                self.bez(name, wert, x, y - 13 - (9.5 if wert else 0), "middle")
        self._pin(f"{name}.{pins[0]}", *p1)
        self._pin(f"{name}.{pins[1]}", *p2)

    def quarz(self, name, x, y, wert, pins=("1", "2"), beschr="oben", senkrecht=False):
        if senkrecht:
            p1, p2 = (x, y - 20), (x, y + 20)
            self.linie(x, y - 20, x, y - 6.5)
            self.linie(x, y + 6.5, x, y + 20)
            self.linie(x - 8, y - 6.5, x + 8, y - 6.5)
            self.linie(x - 8, y + 6.5, x + 8, y + 6.5)
            self.o.append(f'<rect x="{x - 6}" y="{y - 3}" width="12" height="6" fill="#fff" stroke="{TINTE}" stroke-width="{W}"/>')
            self.bez(name, wert, x + 12, y - 1)
            self._pin(f"{name}.{pins[0]}", *p1)
            self._pin(f"{name}.{pins[1]}", *p2)
            return
        p1, p2 = (x - 20, y), (x + 20, y)
        self.linie(x - 20, y, x - 6.5, y)
        self.linie(x + 6.5, y, x + 20, y)
        self.linie(x - 6.5, y - 8, x - 6.5, y + 8)
        self.linie(x + 6.5, y - 8, x + 6.5, y + 8)
        self.o.append(f'<rect x="{x - 3}" y="{y - 6}" width="6" height="12" fill="#fff" stroke="{TINTE}" stroke-width="{W}"/>')
        if beschr == "oben":
            self.bez(name, wert, x, y - 22, "middle")
        self._pin(f"{name}.{pins[0]}", *p1)
        self._pin(f"{name}.{pins[1]}", *p2)

    def taster(self, name, x, y, wert="", pins=("1", "2"), beschr="rechts"):
        """Schließer mit Druckknopf, senkrecht: oben, unten."""
        p1, p2 = (x, y - 20), (x, y + 20)
        self.linie(x, y - 20, x, y - 8)
        self.linie(x, y + 20, x, y + 8)
        self.o.append(f'<circle cx="{x}" cy="{y - 8}" r="1.7" fill="#fff" stroke="{TINTE}" stroke-width="1.1"/>'
                      f'<circle cx="{x}" cy="{y + 8}" r="1.7" fill="#fff" stroke="{TINTE}" stroke-width="1.1"/>')
        self.linie(x, y + 6.3, x - 9, y - 4.5)
        self.linie(x - 4.5, y + 0.9, x - 4.5, y - 11, dash="2 1.8", w=1)
        self.linie(x - 9.5, y - 11, x + 0.5, y - 11, w=1.2)
        if beschr == "links":
            self.bez(name, wert, x - 13, y - 1, "end")
        else:
            self.bez(name, wert, x + 11, y - 1)
        self._pin(f"{name}.{pins[0]}", *p1)
        self._pin(f"{name}.{pins[1]}", *p2)

    def led(self, name, x, y, laenge=20, beschr="rechts"):
        """Leuchtdiode senkrecht: Anode oben (name.A), Kathode unten (name.K)."""
        self.linie(x, y - laenge, x, y - 6)
        self.linie(x, y + 6, x, y + laenge)
        self.o.append(f'<polygon points="{x - 7},{y - 6} {x + 7},{y - 6} {x},{y + 6}" fill="#fff" stroke="{TINTE}" stroke-width="{W}" stroke-linejoin="round"/>')
        self.linie(x - 7, y + 6, x + 7, y + 6)
        for dy in (0, 6):
            self.o.append(f'<path d="M{x + 5} {y - 8 + dy} L{x + 11} {y - 14 + dy} M{x + 8.4} {y - 14 + dy} L{x + 11} {y - 14 + dy} L{x + 11} {y - 11.4 + dy}" '
                          f'stroke="{ORANGE_D}" stroke-width="1.1" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        self.text(name, x + 15, y + 2, 8.5, "start", TINTE, 700)
        self._pin(f"{name}.A", x, y - laenge)
        self._pin(f"{name}.K", x, y + laenge)

    def poti(self, name, x, y, wert, pins=("1", "2", "3")):
        """Trimmpotentiometer senkrecht: Pin 1 oben, Pin 3 unten, Schleifer (Pin 2) links bei x-22."""
        self.linie(x, y - 20, x, y - 9)
        self.linie(x, y + 9, x, y + 20)
        self.o.append(f'<rect x="{x - 4.5}" y="{y - 9}" width="9" height="18" rx="1.2" fill="#fff" stroke="{TINTE}" stroke-width="{W}"/>')
        self.linie(x - 22, y, x - 10, y)
        self.o.append(f'<path d="M{x - 10} {y} L{x - 5} {y - 3} L{x - 5} {y + 3} Z" fill="{TINTE}"/>')
        self.bez(name, wert, x + 9, y - 1)
        self._pin(f"{name}.{pins[0]}", x, y - 20)
        self._pin(f"{name}.{pins[1]}", x - 22, y)
        self._pin(f"{name}.{pins[2]}", x, y + 20)

    def npn(self, name, x, y, beschr="rechts"):
        """NPN-Transistor: Basis links (x-24, y), Kollektor oben rechts (x+12, y-24), Emitter unten rechts (x+12, y+24)."""
        self.linie(x - 24, y, x - 4, y)
        self.linie(x - 4, y - 12, x - 4, y + 12, w=2.4)
        self.linie(x - 4, y - 5, x + 12, y - 16)
        self.linie(x + 12, y - 16, x + 12, y - 24)
        self.linie(x - 4, y + 5, x + 12, y + 16)
        self.linie(x + 12, y + 16, x + 12, y + 24)
        self.o.append(f'<polygon points="{x + 12},{y + 16} {x + 3},{y + 13.5} {x + 8},{y + 7}" fill="{TINTE}"/>')
        self.text(name, x + 19, y + 3, 8.5, "start", TINTE, 700)
        self._pin(f"{name}.B", x - 24, y)
        self._pin(f"{name}.C", x + 12, y - 24)
        self._pin(f"{name}.E", x + 12, y + 24)

    def ferrit(self, name, x, y, wert="", senkrecht=False):
        """Ferritperle wie ein Widerstand mit einem Balken in der Mitte."""
        self.linie(x - 20, y, x - 9, y)
        self.linie(x + 9, y, x + 20, y)
        self.o.append(f'<rect x="{x - 9}" y="{y - 4.5}" width="18" height="9" rx="1.2" fill="#fff" stroke="{TINTE}" stroke-width="{W}"/>'
                      f'<rect x="{x - 2}" y="{y - 4.5}" width="4" height="9" fill="{TINTE}"/>')
        self.bez(name, wert, x, y - 14 - (9.5 if wert else 0), "middle")
        self._pin(f"{name}.1", x - 20, y)
        self._pin(f"{name}.2", x + 20, y)

    def inverter(self, name, x, y, pin_ein, pin_aus, bez_ic, typ):
        """Inverter, Eingang links (x-30), Ausgang rechts (x+30)."""
        self.linie(x - 30, y, x - 14, y)
        self.o.append(f'<polygon points="{x - 14},{y - 15} {x - 14},{y + 15} {x + 13},{y}" fill="{LCD}" stroke="{TINTE}" stroke-width="{W}" stroke-linejoin="round"/>'
                      f'<circle cx="{x + 16.5}" cy="{y}" r="3.5" fill="#fff" stroke="{TINTE}" stroke-width="{W}"/>')
        self.linie(x + 20, y, x + 30, y)
        self._pin(f"{bez_ic}.{pin_ein}", x - 30, y)
        self._pin(f"{bez_ic}.{pin_aus}", x + 30, y)
        self.pinnr(pin_ein, x - 25, y - 4)
        self.pinnr(pin_aus, x + 25, y - 4)
        self.text(name, x - 2, y - 21, 8.5, "middle", TINTE, 700)
        self.text(typ, x - 2, y + 27, 8, "middle", GRAU)

    def ic(self, name, x, y, breite, hoehe, links=(), rechts=(), oben=(), unten=(), titel="", typ="",
           ic_name=None, abstand=10, versatz=10):
        """IC-Kasten. Pin-Listen: (Pinnummer, Bezeichnung, Verbindung).
        Verbindung: 'nc' = offen mit Kreuz, None = Anschluss ohne Stummel-Kreuz,
        sonst Anschlusspunkt wird als Pin 'name.nr' registriert.
        Stummel 10 lang. oben/unten: Pins an x-Positionen (Spalten ab Mitte, je 20 auseinander)."""
        ic_name = ic_name or name
        self.o.append(f'<rect x="{x}" y="{y}" width="{breite}" height="{hoehe}" rx="2.5" fill="{LCD}" stroke="{TINTE}" stroke-width="{W}"/>')
        self._box(x, y, 0)
        self._box(x + breite, y + hoehe, 0)
        if titel:
            self.text(titel, x + breite / 2, y + hoehe / 2 - 1 if not typ else y + hoehe / 2 - 4, 9.5, "middle", TINTE, 700)
        if typ:
            self.text(typ, x + breite / 2, y + hoehe / 2 + 8, 8.5, "middle", GRAU)

        def stummel(px, py, dx, dy, nr, bez, art, innen_x, innen_y, anker, nr_pos):
            ex, ey = px + dx * 10, py + dy * 10
            self.linie(px, py, ex, ey)
            self._pin(f"{ic_name}.{nr}", ex, ey)
            self.pinnr(nr, *nr_pos)
            if bez:
                self.text(bez, innen_x, innen_y, 7.5, anker, TINTE)
            if art == "nc":
                self.no_connect.add((ex, ey))
                s = 2.6
                self.o.append(f'<path d="M{ex - s} {ey - s} L{ex + s} {ey + s} M{ex - s} {ey + s} L{ex + s} {ey - s}" stroke="{GRAU_H}" stroke-width="1.1" fill="none"/>')

        for i, eintrag in enumerate(links):
            if eintrag is None:
                continue
            nr, bez, art = eintrag
            yy = y + versatz + i * abstand
            stummel(x, yy, -1, 0, nr, bez, art, x + 4, yy + 2.6, "start", (x - 5, yy - 2.2))
        for i, eintrag in enumerate(rechts):
            if eintrag is None:
                continue
            nr, bez, art = eintrag
            yy = y + versatz + i * abstand
            stummel(x + breite, yy, 1, 0, nr, bez, art, x + breite - 4, yy + 2.6, "end", (x + breite + 5, yy - 2.2))
        n = len(oben)
        for i, eintrag in enumerate(oben):
            if eintrag is None:
                continue
            nr, bez, art = eintrag
            xx = x + breite / 2 + (i - (n - 1) / 2) * 20
            stummel(xx, y, 0, -1, nr, bez, art, xx, y + 10, "middle", (xx + 6, y - 4))
        n = len(unten)
        for i, eintrag in enumerate(unten):
            if eintrag is None:
                continue
            nr, bez, art = eintrag
            xx = x + breite / 2 + (i - (n - 1) / 2) * 20
            stummel(xx, y + hoehe, 0, 1, nr, bez, art, xx, y + hoehe - 4, "middle", (xx + 6, y + hoehe + 13))


    # ---------------------------------------------- Signalnamen und Busse
    def netzname(self, x, y, name, text=True, dx=3, dy=-3, anker="start"):
        """Gibt dem Punkt (x, y) einen Signalnamen (verbindet gleichnamige Punkte)
        und schreibt ihn klein daneben."""
        self._union((x, y), "sig:" + name)
        self.namenspunkte.append((x, y))
        if text:
            self.text(name, x + dx, y + dy, 6.6, anker, ORANGE_D, 700)

    def bus(self, x_bus, pin_punkte, namen, beschriftung, seite="links", abstand_text=True):
        """Dicke Sammelleitung senkrecht bei x_bus. pin_punkte: [(x, y)] der Anschlüsse,
        namen: Signalnamen dazu. seite: auf welcher Seite des Bausteins der Bus liegt."""
        ys = [y for _, y in pin_punkte]
        self.o.append(f'<path d="M{x_bus} {min(ys) - 5} L{x_bus} {max(ys) + 5}" stroke="{LCD_R}" stroke-width="3.6" '
                      f'stroke-linecap="round" fill="none"/>')
        self._box(x_bus, min(ys) - 14, 10)
        for (px, py), nm in zip(pin_punkte, namen):
            self.draht((px, py), (x_bus, py))
            self._union((px, py), "sig:" + nm)
            if seite == "links":
                self.text(nm, x_bus + 4, py - 2, 6.4, "start", ORANGE_D, 700)
            else:
                self.text(nm, x_bus - 4, py - 2, 6.4, "end", ORANGE_D, 700)
        self.text(beschriftung, x_bus, min(ys) - 10, 7.5, "middle", LCD_R, 700)

    def nand(self, name, x, y, eingaenge, pin_aus, bez_ic, typ="", abstand=10):
        """NAND-Gatter als Kasten mit & und Blase am Ausgang. eingaenge: [(Pinnummer, Bezeichnung)].
        Anschlüsse links bei x-10, Ausgang rechts bei x+w+10. Gibt den Ausgangspunkt zurück."""
        n = len(eingaenge)
        w = 30
        h = 10 + (n - 1) * abstand + 10
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2.5" fill="{LCD}" stroke="{TINTE}" stroke-width="{W}"/>'
                      f'<text x="{x + w / 2}" y="{y + h / 2 + 3.5}" font-size="10" text-anchor="middle" fill="{TINTE}" font-weight="700">&amp;</text>')
        self._box(x - 10, y, 0)
        self._box(x + w + 10, y + h, 0)
        for i, (pin, bez) in enumerate(eingaenge):
            yy = y + 10 + i * abstand
            self.linie(x - 10, yy, x, yy)
            self._pin(f"{bez_ic}.{pin}", x - 10, yy)
            self.pinnr(pin, x - 5, yy - 2.2)
        ya = y + h / 2
        self.o.append(f'<circle cx="{x + w + 3.5}" cy="{ya}" r="3.5" fill="#fff" stroke="{TINTE}" stroke-width="{W}"/>')
        self.linie(x + w + 7, ya, x + w + 10, ya)
        self._pin(f"{bez_ic}.{pin_aus}", x + w + 10, ya)
        self.pinnr(pin_aus, x + w + 4, ya - 6)
        self.text(name, x + w / 2, y - 4, 8.5, "middle", TINTE, 700)
        if typ:
            self.text(typ, x + w / 2, y + h + 10, 8, "middle", GRAU)
        return (x + w + 10, ya)

    def versorgung(self, x, y, ic_name, pin_vcc, pin_gnd, c_name, c_wert):
        """Stromversorgung eines ICs: Kondensator links, Anschlüsse des ICs rechts."""
        self.kondensator(c_name, x, y + 25, c_wert, laenge=25)
        self.vcc(x, y)
        self.gnd(x, y + 50)
        self.ic(ic_name, x + 40, y + 10, 46, 30, oben=[(pin_vcc, "", None)], unten=[(pin_gnd, "", None)], titel=ic_name)
        self.vcc(x + 63, y)
        self.gnd(x + 63, y + 50)

    # -------------------------------------------------------- Ausgabe
    def netze(self):
        """Gruppen verbundener Anschlüsse: Menge von Pinnamen je Netz."""
        self._auto_t_verbindungen()
        self._namen_auf_draehten()
        gruppen = {}
        for name, pt in self.pins.items():
            gruppen.setdefault(self._find(pt), set()).add(name)
        for k in list(self._uf):
            if isinstance(k, str) and k.startswith(("ext:", "sig:")):
                gruppen.setdefault(self._find(k), set()).add(k)
        return list(gruppen.values())

    def svg(self, titel, rand=10):
        self._auto_t_verbindungen()
        linien = []
        for w in self.draehte:
            d = " ".join(("M" if i == 0 else "L") + f"{x} {y}" for i, (x, y) in enumerate(w))
            linien.append(f'<path d="{d}" fill="none" stroke="{TINTE}" stroke-width="{W}" stroke-linejoin="round" stroke-linecap="round"/>')
        punkte = "".join(f'<circle cx="{x}" cy="{y}" r="2.6" fill="{TINTE}"/>' for x, y in sorted(set(self.punkte)))
        x0, y0 = self.xmin - rand, self.ymin - rand
        b, h = self.xmax - self.xmin + 2 * rand, self.ymax - self.ymin + 2 * rand
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0:.0f} {b:.0f} {h:.0f}" '
                f'font-family="{FONT}" role="img" aria-label="{_t(titel)}">\n<title>{_t(titel)}</title>\n'
                + "\n".join(linien) + "\n" + "\n".join(self.o) + "\n" + punkte + "\n</svg>\n")


def vergleiche(plan, bb):
    """Prüft, ob die Netzliste des Schaltplans mit der des Steckbretts übereinstimmt.
    Verglichen werden nur Anschlüsse, die in beiden Zeichnungen vorkommen, dazu die
    Versorgung (ext:+5V, ext:GND) und Signalnamen (sig:...), die beide kennen."""
    sp_netze = plan.netze()
    bb_netze = {}
    for n in bb.alle_pins:
        bb_netze.setdefault(bb._find(bb.pins[n]), set()).add(n)
    bb_tokens = set()
    for k in list(bb._uf):
        if isinstance(k, tuple) and k[0] == "ext" and k[1].startswith(("ext:+5V", "ext:+9V", "ext:GND", "sig:")):
            bb_netze.setdefault(bb._find(k), set()).add(k[1])
            bb_tokens.add(k[1])
    sp_tokens = {n for g in sp_netze for n in g if n.startswith(("ext:", "sig:"))}
    erlaubt = (set(plan.pins) & set(bb.pins)) | (sp_tokens & bb_tokens)

    def teile(gruppen):
        r = set()
        for g in gruppen:
            g2 = frozenset(n for n in g if n in erlaubt)
            if g2:
                r.add(g2)
        return r

    sp = teile(sp_netze)
    bbt = teile(list(bb_netze.values()))
    fehler = []
    for g in sp - bbt:
        fehler.append(f"nur im Schaltplan: {sorted(g)}")
    for g in bbt - sp:
        fehler.append(f"nur auf dem Steckbrett: {sorted(g)}")
    if fehler:
        raise AssertionError("Schaltplan und Steckbrett stimmen nicht überein:\n  " + "\n  ".join(fehler))
    return len(erlaubt)
