#!/usr/bin/env python3
"""Gemeinsame Bibliothek zum Bauen der Handbücher (Aufruf über build.py
des jeweiligen Handbuchs, das konfiguriere() und main() aufruft).

Baut das Handbuch für jede Sprache (pages/de, pages/en) und schreibt je
Sprache build/<Basisname der Sprache>.pdf|html:
  de: HOMECOMPUTER 6502 Bedienungshandbuch_de.pdf
  en: HOMECOMPUTER 6502 User Manual_en.pdf

Ablauf je Sprache:
  1. Alle Seiten aus pages/<sprache>/ in Dateinamen-Reihenfolge lesen, jeweils
     den Inhalt von <main> nehmen und zu einer HTML-Datei zusammenfügen.
  2. Für jedes <section class="kapitel"> ein Deckblatt erzeugen
     (Nummer, Titel, Liste der h2-Überschriften).
  3. Das Inhaltsverzeichnis (<nav class="inhalt" data-auto>) aus Kapiteln,
     Einleitung und Anhängen füllen.
  4. Kolumnentitel je Abschnitt als benannte @page-Regeln erzeugen.
  5. Mit Chrome/Chromium headless drucken. Danach die Seitenzahlen der
     Überschriften aus den Links im PDF lesen, ins Inhaltsverzeichnis
     eintragen und ein zweites Mal drucken.

Die Schaltplan-SVGs für Anhang F liegen fertig im Git (schematic/); bei
Bedarf erneuern sie mit extract-schematic.py aus dem PDF.
Braucht nur Python 3, Chrome oder Chromium und qpdf.
Aufruf:  python3 <handbuch>/build.py   (Chrome-Pfad notfalls über $CHROME,
          Sprachen über $SPRACHEN, Standard: de en)
"""

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Wird von konfiguriere() gesetzt (jedes Handbuch hat einen kleinen build.py).
HIER = SEITEN = AUSGABE = SCHALTPLAN_SVG = None
BASISNAME = {}
DOK_TITEL = {}
KAPITEL_MARKE = {"de": "Kapitel", "en": "Chapter"}
SPRACHEN = [x.strip() for x in os.environ.get("SPRACHEN", "de en").split() if x.strip()]

CHROME_KANDIDATEN = [
    "google-chrome-stable", "google-chrome", "chromium", "chromium-browser",
    "microsoft-edge-stable", "vivaldi-stable",
]


def fehler(text):
    print(f"build.py: {text}", file=sys.stderr)
    sys.exit(1)


def finde_chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for name in CHROME_KANDIDATEN:
        pfad = shutil.which(name)
        if pfad:
            return pfad
    fehler("Chrome oder Chromium nicht gefunden. Pfad in $CHROME angeben.")


def attribute(tag):
    return {k: html.unescape(v) for k, v in re.findall(r'([\w-]+)="([^"]*)"', tag)}


def klassen(tag):
    return attribute(tag).get("class", "").split()


def nur_text(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def css_text(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ------------------------------------------------------------ Zusammenfügen

def lies_seiten(sprache):
    dateien = sorted((SEITEN / sprache).glob("*.html"))
    if not dateien:
        fehler(f"keine Seiten in {SEITEN / sprache}")
    teile = []
    for datei in dateien:
        text = datei.read_text(encoding="utf-8")
        m = re.search(r"<main\b[^>]*>(.*)</main>", text, re.S)
        if not m:
            fehler(f"{datei.name}: kein <main>")
        teile.append(f"\n<!-- {datei.name} -->\n{m.group(1).strip()}\n")
    return "".join(teile)


SECTION_ODER_UEBERSCHRIFT = re.compile(
    r"<section\b[^>]*>|<(h1|h2)\b([^>]*)>(.*?)</\1>", re.S)


def verarbeite(inhalt, sprache):
    """Vergibt ids, sammelt das Inhaltsverzeichnis und die Kolumnentitel,
    setzt Kapitel-Deckblätter ein."""
    eintraege = []   # (stufe, id, nummer, titel)
    kapitel = {}     # id -> {"nr", "titel", "themen": [...]}
    seitenregeln = []
    aktuell = {"art": None, "id": None}
    zaehler = {"n": 0}

    def neue_id(vorschlag):
        zaehler["n"] += 1
        basis = re.sub(r"[^a-z0-9]+", "-", vorschlag.lower()).strip("-") or "abschnitt"
        return f"{basis}-{zaehler['n']}"

    def ersetze(m):
        tag = m.group(0)
        if tag.startswith("<section"):
            a = attribute(tag)
            k = klassen(tag)
            art = next((x for x in ("kapitel", "anhang", "einleitung") if x in k), None)
            aktuell["art"] = art
            if art is None:
                return tag
            if art == "kapitel":
                nr = a.get("data-nr", "?")
                sid = a.get("id") or f"kapitel-{nr}"
                kapitel[sid] = {"nr": nr, "titel": a.get("data-titel", ""), "themen": []}
                eintraege.append((1, sid, nr, a.get("data-titel", "")))
                aktuell["id"] = sid
                marker = f"<!--KAPITELSTART {sid}-->"
            else:
                sid = a.get("id") or neue_id(art)
                aktuell["id"] = sid
                marker = ""
            seite = f"abschnitt-{len(seitenregeln) + 1}"
            seitenregeln.append((seite, a.get("data-kurztitel", "")))
            tag = re.sub(r"\s+id=\"[^\"]*\"", "", tag)
            tag = tag[:-1] + f' id="{sid}-text" style="page: {seite}">'
            return marker + tag

        ebene, attrs, text = m.group(1), m.group(2), m.group(3)
        titel = nur_text(text)
        a = attribute(attrs)
        if aktuell["art"] == "kapitel" and ebene == "h2":
            hid = a.get("id") or neue_id(titel)
            kapitel[aktuell["id"]]["themen"].append(titel)
            eintraege.append((2, hid, "", titel))
        elif aktuell["art"] in ("anhang", "einleitung") and ebene == "h1":
            hid = a.get("id") or aktuell["id"]
            nummer = ""
            b = re.search(r'<span class="buchstabe">(.*?)</span>', text)
            if b:
                nummer = nur_text(b.group(1))
                titel = nur_text(text.replace(b.group(0), ""))
            eintraege.append((1, hid, nummer, titel))
        else:
            return tag
        if "id" in a:
            return tag
        return f'<{ebene}{attrs} id="{hid}">{text}</{ebene}>'

    inhalt = SECTION_ODER_UEBERSCHRIFT.sub(ersetze, inhalt)

    def deckblatt(m):
        sid = m.group(1)
        k = kapitel[sid]
        themen = "\n".join(f"    <li>{html.escape(t)}</li>" for t in k["themen"])
        return f"""<section class="kapitel-start">
  <div class="kreis kreis-1"></div>
  <div class="kreis kreis-2"></div>
  <div class="marke">{KAPITEL_MARKE.get(sprache, 'Kapitel')}</div>
  <div class="nummer">{html.escape(k['nr'])}</div>
  <h1 id="{sid}">{html.escape(k['titel'])}</h1>
  <ul class="themen">
{themen}
  </ul>
  <div class="streifen"></div>
</section>
"""

    inhalt = re.sub(r"<!--KAPITELSTART (\S+)-->", deckblatt, inhalt)
    return inhalt, eintraege, seitenregeln


def inhaltsverzeichnis(eintraege, seiten=None):
    seiten = seiten or {}
    zeilen = ["<ol>"]
    offen = False
    for stufe, hid, nummer, titel in eintraege:
        seite = seiten.get(hid, "000")
        link = (f'<a href="#{hid}">'
                + (f'<span class="nr">{html.escape(nummer)}</span>' if stufe == 1 else "")
                + f'<span class="titel">{html.escape(titel)}</span>'
                + '<span class="fueller"></span>'
                + f'<span class="seite">{seite}</span></a>')
        if stufe == 1:
            if offen:
                zeilen.append("</ol></li>")
            zeilen.append(f'<li class="stufe-1">{link}<ol>')
            offen = True
        else:
            zeilen.append(f'<li class="stufe-2">{link}</li>')
    if offen:
        zeilen.append("</ol></li>")
    zeilen.append("</ol>")
    return "\n".join(zeilen)


def kolumnentitel(seitenregeln):
    regeln = []
    stil = ("font: 700 6.5pt/1 var(--schrift-titel); letter-spacing: .16em; "
            "text-transform: uppercase; color: var(--grau); "
            "vertical-align: bottom; padding-bottom: 5mm;")
    for name, titel in seitenregeln:
        if not titel:
            continue
        t = css_text(titel)
        regeln.append(f"@page {name}:left {{ @top-left {{ content: {t}; {stil} }} }}")
        regeln.append(f"@page {name}:right {{ @top-right {{ content: {t}; {stil} text-align: right; }} }}")
    return "\n".join(regeln)


def klebe_satzzeichen(text):
    """Hängt Doppelpunkt, Punkt, Ausrufe- und Fragezeichen an die Taste davor.

    Eine Taste ist ein eigener Kasten (inline-block). Dahinter darf der
    Umbruch das Satzzeichen allein in die nächste Zeile schieben. Im
    nowrap-Span rutscht beides zusammen weiter."""
    def satz(m):
        return f'<span class="kleb">{m.group(1)}{m.group(2)}</span>'

    return re.sub(
        r'(?<!kleb">)(<kbd\b[^>]*>[^<]*</kbd>)[ \t\u00a0\n]*([.:!?])',
        satz, text)


def schreibe_html(inhalt, eintraege, seitenregeln, datei, sprache, seiten=None):
    verzeichnis = inhaltsverzeichnis(eintraege, seiten)
    text = re.sub(r"(<nav\b[^>]*\bdata-auto\b[^>]*>)\s*(</nav>)",
                  lambda m: m.group(1) + "\n" + verzeichnis + "\n" + m.group(2), inhalt)
    text = klebe_satzzeichen(text)
    doc = f"""<!doctype html>
<html lang="{sprache}">
<head>
<meta charset="utf-8">
<title>{DOK_TITEL.get(sprache, BASISNAME[sprache])}</title>
<link rel="stylesheet" href="../../shared/css/manual.css">
<style>
{kolumnentitel(seitenregeln)}
</style>
</head>
<body>
<main>
{text}
</main>
</body>
</html>
"""
    datei.write_text(doc, encoding="utf-8")


# --------------------------------------------------------------- Schaltplan

def schaltplan_pruefen(inhalt):
    """Prüft, ob die von Anhang F eingebundenen Schaltplan-SVGs in
    schematic/ (Git) vorhanden sind. Erzeugt werden sie von
    extract-schematic.py, nicht hier."""
    gebraucht = sorted({m.group(1) for m in re.finditer(
        r'src="\.\./schematic/([^"]+\.svg)"', inhalt)})
    if not gebraucht:
        return
    fehlend = [name for name in gebraucht if not (SCHALTPLAN_SVG / name).exists()]
    if fehlend:
        fehler(f"Schaltplan-SVGs fehlen in {SCHALTPLAN_SVG.relative_to(HIER.parent)}/: " + ", ".join(fehlend)
               + "\n  (erneuern mit dem extract-schematic*.py des Handbuchs)")


# ------------------------------------------------------------------ Drucken

def drucke(chrome, html_datei, ziel):
    with tempfile.TemporaryDirectory() as profil:
        befehl = [
            chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
            f"--user-data-dir={profil}",
            "--no-pdf-header-footer", "--generate-pdf-document-outline",
            "--allow-file-access-from-files", "--virtual-time-budget=10000",
            f"--print-to-pdf={ziel}", html_datei.as_uri(),
        ]
        r = subprocess.run(befehl, capture_output=True, text=True)
    if r.returncode != 0 or not Path(ziel).exists():
        fehler(f"Chrome ist gescheitert:\n{r.stderr}")


def vergleichbar(text):
    return re.sub(r"[^0-9A-ZÄÖÜ]", "", text.upper())


def seitenzahlen(pdf, eintraege):
    """Sucht die Seite jedes Eintrags in den Lesezeichen des PDFs.
    Chrome legt für jede Überschrift ein Lesezeichen mit Zielseite an
    (Titel so, wie gedruckt, also oft in Großbuchstaben). Die Einträge
    kommen in derselben Reihenfolge vor wie die Lesezeichen."""
    if not shutil.which("qpdf"):
        fehler("qpdf nicht gefunden (wird für die Seitenzahlen gebraucht)")
    r = subprocess.run(["qpdf", "--json", "--json-key=pages", "--json-key=outlines", pdf],
                       capture_output=True, text=True)
    if r.returncode not in (0, 3):
        fehler(f"qpdf ist gescheitert:\n{r.stderr}")
    daten = json.loads(r.stdout)
    seite_nr = {p["object"]: i + 1 for i, p in enumerate(daten["pages"])}

    lesezeichen = []

    def sammle(liste):
        for o in liste:
            dest = o.get("dest") or []
            if dest and dest[0] in seite_nr:
                lesezeichen.append((vergleichbar(o.get("title", "")), seite_nr[dest[0]]))
            sammle(o.get("kids", []))

    sammle(daten.get("outlines", []))

    seiten, i = {}, 0
    for _, hid, _, titel in eintraege:
        gesucht = vergleichbar(titel)
        for j in range(i, len(lesezeichen)):
            if gesucht and lesezeichen[j][0].endswith(gesucht):
                seiten[hid] = str(lesezeichen[j][1])
                i = j + 1
                break
    return seiten


def baue_sprache(chrome, sprache):
    html_datei = AUSGABE / f"{BASISNAME[sprache]}_{sprache}.html"
    pdf_datei = AUSGABE / f"{BASISNAME[sprache]}_{sprache}.pdf"
    inhalt, eintraege, seitenregeln = verarbeite(lies_seiten(sprache), sprache)
    schaltplan_pruefen(inhalt)

    # Durchgang 1: Seitenumbruch bestimmen
    schreibe_html(inhalt, eintraege, seitenregeln, html_datei, sprache)
    with tempfile.TemporaryDirectory() as tmp:
        probe = os.path.join(tmp, "probe.pdf")
        drucke(chrome, html_datei, probe)
        seiten = seitenzahlen(probe, eintraege)

    fehlend = [titel for _, hid, _, titel in eintraege if hid not in seiten]
    if fehlend:
        print(f"[{sprache}] Warnung: keine Seitenzahl für: " + ", ".join(fehlend),
              file=sys.stderr)

    # Durchgang 2: mit Seitenzahlen im Inhaltsverzeichnis
    schreibe_html(inhalt, eintraege, seitenregeln, html_datei, sprache, seiten)
    drucke(chrome, html_datei, str(pdf_datei))
    print(f"{pdf_datei.relative_to(HIER.parent)} ({len(eintraege)} Einträge im Inhalt)")


def konfiguriere(hier, basisname, dok_titel):
    """hier = Ordner des Handbuchs (mit pages/, img/, schematic/)."""
    global HIER, SEITEN, AUSGABE, SCHALTPLAN_SVG, BASISNAME, DOK_TITEL
    HIER = Path(hier).resolve()
    SEITEN = HIER / "pages"
    AUSGABE = HIER / "build"
    SCHALTPLAN_SVG = HIER / "schematic"
    BASISNAME, DOK_TITEL = basisname, dok_titel


def main():
    chrome = finde_chrome()
    AUSGABE.mkdir(exist_ok=True)
    for sprache in SPRACHEN:
        baue_sprache(chrome, sprache)

