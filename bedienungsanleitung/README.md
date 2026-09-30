# User Manual

The user manual of the HomeComputer 6502 as a PDF (A5), structured like the C64 manual.

```
./build.sh
```

Result: `build/HOMECOMPUTER 6502 Bedienungshandbuch_de.pdf` and `HOMECOMPUTER 6502 User Manual_en.pdf` (each with an `.html` of the same name for previewing in a browser). The source files are in `pages/de/` and `pages/en/`, one folder per language. Choose the languages with `$SPRACHEN` (default `de en`). Needs Chrome or Chromium (other path via `$CHROME`) and `qpdf`. The schematic SVGs are ready-made in `schematic/`; renew them with `extract-schematic.sh` (needs `pdftocairo`, poppler-utils).

## Structure

| Path | Content |
|---|---|
| `pages/de/*.html`, `pages/en/*.html` | one file per part and language, order by file name |
| `../shared/css/manual.css` | page format, colors, all building blocks (shared) |
| `../shared/css/fonts.css`, `../shared/fonts/` | Raleway, Lato, IBM Plex Mono, VT323 (local, SIL OFL) |
| `img/` | figures, drawn by `img/zeichnungen.py` (language-dependent ones in `img/de/` and `img/en/`) |
| `../../homecomputer-6502/schematics/homecomputer-6502-final-kicad-schematic.pdf` | schematic in the hardware repo next to this one (other path via `$SCHALTPLAN`) |
| `schematic/seite-N.svg` | schematic pages as SVG, kept in Git; renewed by `extract-schematic.py`, included by Appendix F |
| `build.sh` | outer entry point, checks the tools and starts `build.py` |
| `build.py` | joins the pages and prints the PDF |
| `extract-schematic.sh` | outer entry point, checks pdfinfo/pdftocairo and starts `extract-schematic.py` |
| `extract-schematic.py` | extracts `schematic/*.svg` from the schematic PDF (`--check` verifies the state) |

Every page is a complete HTML document; `build.py` takes only the content of `<main>`.

- **Chapter:** `<section class="kapitel" data-nr="3" data-titel="…" data-kurztitel="…">` containing `h2`/`h3`. `build.py` generates the title page with the number and the topic list (from the `h2`s).
- **Appendix:** `<section class="anhang" data-kurztitel="…">` with `<h1><span class="buchstabe">A</span>Title</h1>`.
- **Table of contents:** `<nav class="inhalt" data-auto>` is filled in; page numbers come from a second print pass.
- `data-kurztitel` is the running head at the top of the page.

## Building blocks

```html
<kbd>Return</kbd>                                   key
<code>PRINT 2+2</code>                               command in text
<pre class="listing">10 PRINT "HALLO"</pre>         listing
<figure class="lcd"><pre>…4 lines…</pre><figcaption>…</figcaption></figure>
<aside class="kasten"><div class="kasten-titel">Note</div><p>…</p></aside>
<aside class="kasten achtung">…</aside>
<figure class="abbildung"><div class="bild-platzhalter">Image: …</div><figcaption>…</figcaption></figure>
```

Command reference (Appendix A, section with `class="anhang referenz"`):

```html
<h3>GOTO</h3>                                        keyword
<p class="syntax">GOTO <var>line</var></p>           syntax, <var> = fill in yourself
<table class="beispiele"><tbody><tr><td><code>…</code></td><td>…</td></tr></tbody></table>
<table class="funktionen">…</table>                  function on the left, description on the right
```

Text in `[Platzhalter: …]` (placeholder) is still to be written.
