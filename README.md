# HomeComputer 6502 – Manuals

Two printed manuals for the HomeComputer 6502, a self-built 8-bit computer with an LCD, a keyboard and a SID sound chip. Written together with an AI agent.

| Folder | Content |
|---|---|
| `bedienungsanleitung/` | User Manual (de/en), A5 PDF. Structure and building blocks: see its `README.md` |
| `technische-dokumentation/` | Technical Documentation (de/en), A5 PDF: a build guide from the first clock signal to the finished computer |
| `shared/` | shared `css/` and `fonts/` |

## Build

```
./build.sh                       # everything
./build.sh bedienungsanleitung   # User Manual only
```

The result for each manual is in `<folder>/build/`. The schematic comes from the hardware repo `../homecomputer-6502/` (see `bedienungsanleitung/README.md`).

## How the manuals were made with AI

Full article: *Documentation with AI* on [grappendorf.net](https://grappendorf.net/ai/documentation-with-ai.html).

- **Model and look.** The model is the Commodore 64 User's Guide: big chapter numbers, short sections, many examples, a long appendix. Two decisions came from the author: vector drawings instead of photos, and A5 ready to print in German and English.
- **Technique.** Every page is plain HTML. One stylesheet defines page format, fonts and all building blocks. A Python script joins the pages and lets Chrome print the PDF. A whole book builds in seconds, so every change can be checked right away.
- **User Manual.** The content already existed in the firmware repository (specifications, descriptions, source code). The appendices (BASIC commands, error messages, memory map, character set, keyboard layout) are generated from the sources, so they match the firmware.
- **Technical Documentation.** Each chapter has the same parts: purpose, schematic, parts list, breadboard assembly, measurement. Schematics were redrawn from the 2014 Eagle sheets, breadboards are drawn hole by hole by Python scripts.
- **Checks instead of "looks right".**
  - The netlist of every schematic must match the netlist of its breadboard drawing, or the build stops.
  - Every example program is assembled with cc65 and run in a 6502 simulator before it goes into the book.
- **Oscilloscope pictures.** Calculated in a common style instead of mixed real screenshots. The book says openly that the curves are calculated.
- **English.** The pages, drawing labels and listing comments are translated. Both languages build from the same sources.

### Lessons

- The sources are the best documentation. Tables generated from them cannot drift.
- Choose a technique the agent can check: HTML and Python drawings can be built, viewed and corrected in a loop.
- Let the drawings prove themselves with netlist checks and a simulator.
- Taste stays with the human: the agent offers, you decide.

The effort for the author was about one or two hours of prompting and proofreading. That worked because all information already existed. Nothing had to be researched or invented.
