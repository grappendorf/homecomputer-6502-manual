# Technical Documentation and Build Guide

Build guide and documentation of the HomeComputer 6502, chapter by chapter from the clock to the finished device. So far: introduction and chapters 1 (clock), 2 (reset), 3 (processor), 4 (EEPROM), 5 (serial interface), 6 (RAM), 7 (monitor program), 8 (VIA, LED), 9 (LCD), 10 (keyboard), 11 (interrupts), 12 (SID), 13 (outlook, reference tables, literature). Same structure as `../bedienungsanleitung/`, template (CSS, fonts) from `../shared/`.

```
./build.sh        # builds de and en into build/
```

| Path | Content |
|---|---|
| `pages/de`, `pages/en` | pages per language, order by file name |
| `img/breadboard.py` | library for breadboard drawings, checks the wiring |
| `img/zeichnungen.py` | generates `bb-*.svg` (breadboards per build stage) |
| `img/schaltplan.py` | library for schematics, derives the netlist from the drawing |
| `img/schaltplaene.py` | generates `sp-*.svg` and compares them with the breadboards |
| `img/zeichnungen2.py` | generates the breadboards of chapters 4 to 6 (wires with signal names) |
| `img/schaltplaene2.py` | schematics of chapters 4 to 6, checked against the breadboards |
| `img/zeichnungen3.py` | breadboards of chapters 8 and 9 (decoder 74LS137, VIA, LCD) |
| `img/schaltplaene3.py` | schematics of chapters 8 and 9 |
| `programme/` | programs of chapters 7 to 12 (templates, de/en generated) and `pruefen.py`: assembles them with cc65 and checks them in the simulator (`pip install py65`) |
| `img/zeichnungen4.py` | breadboards of chapters 10 to 12 (second VIA, keyboard, NMI button, SID, output stage) |
| `img/schaltplaene4.py` | schematics of chapters 10 to 12 |
| `img/grafiken.py` | explanatory graphic: keyboard matrix |
| `img/signale.py` | pin assignments (6502, memory, ACIA) |
| `img/logik.py` | schematic logic analyzer pictures `logik-*.svg` (de, en) |
| `img/oszilloskop.py` | generates the schematic oscilloscope pictures `messung-*.svg` (de, en) |

The figures are regenerated with `python3 img/zeichnungen.py`, `python3 img/schaltplaene.py` and `python3 img/oszilloskop.py` and are kept in Git. The schematic and the breadboard of a build stage must produce the same netlist, otherwise `schaltplaene.py` aborts.
