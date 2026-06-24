# ADR-003: Complexity-driven Word document generator

- **Status:** Done
- **Date:** 2026-06-24
- **Tracking issue:** #3
- **Builds on:** ADR-001
- **Deciders:** Padraig Lennon

## Context

The tool has two generate-mode capabilities so far, both for PowerPoint:

- generate a deck from scratch (`generate deck`, ADR-001), and
- inject data into a Golden template (`generate fill`, ADR-001), which already
  supports `.docx` via `DocxInjector`.

What is missing is the ability to *generate* a Word document from scratch, the
direct analogue of the PPTX deck generator. This ADR adds that. A spreadsheet
(`.xlsx`) generator is the natural next step and is tracked separately (#4).

ADR-001 kept the generator library-first and the content helpers (the seeded
`Lorem`, the `Complexity` enum) reusable, precisely so a second format could be
added without rewriting the core.

## Decision

Add a complexity-driven Word generator built on `python-docx`.

### DocxComplexityGenerator

`generators/docx.py` builds a `.docx` from scratch. A document is a sequence of
**sections**; each section is a heading followed by a run of content blocks. The
generator never injects into a template (that is fill mode) and never depends on
the renderer for layout decisions.

### Complexity scales content, sections set length

The named **complexity** levels (`minimal`...`maximum`) are reused from the core.
They decide **which content blocks appear and how rich** each section is:

- `minimal`: headings + paragraphs only,
- rising levels add bullet and numbered lists, then native tables, then inline
  placeholder images, block quotes, and page/section breaks,
- `maximum`: all block types.

`--sections N` is the length dial (the analogue of `--slides N`).

### Content blocks

- **Headings + paragraphs** (baseline) using Word's built-in `Heading 1` /
  `Heading 2` styles and lorem-ipsum body text.
- **Bullet and numbered lists** using the built-in `List Bullet` /
  `List Number` styles.
- **Tables** with a header row and data rows, sized to the page width so they do
  not overflow the margins.
- **Images** (generated placeholder PNGs, in memory), **block quotes**
  (`Intense Quote` style), and **page breaks** at higher complexity.

### Deterministic

`--seed` makes output reproducible: the same `(complexity, sections, seed)`
yields the identical `.docx`. The existing seeded `Lorem` helper drives all text;
placeholder images are generated in memory.

### Surfaces

- **CLI:** a new `doc` subcommand:
  `generate doc --out file.docx --complexity <level> --sections N --seed N`.
- **Web UI:** a new **"Generate a document"** tab alongside "Generate a deck" and
  "Use a template", with an introspected form (complexity, sections, seed),
  consistent with the existing tabbed UI. It posts to a new `/generate/doc`
  route and returns the same timestamped, flashing download partial.
- **Core:** a `generate_doc(...)` function next to `generate_deck(...)`, so a
  future UI or caller reuses it.

### Reuse and the path to Excel

Shared pieces are factored so the Excel generator (#4) plugs in without
rewriting the core: the seeded `Lorem`, the `Complexity` levels, and the
generate-mode entry pattern (`generate_<format>()` plus a CLI subcommand and a UI
tab). Excel is not built here.

## Consequences

### Positive

- Completes Word support: the tool can now both fill Word templates and generate
  Word documents.
- Reuses the complexity model and lorem helper, so behaviour is consistent with
  the PPTX generator and there is little new surface to learn.
- The generate-mode pattern is now proven across two formats, making the Excel
  follow-up mechanical.

### Negative / trade-offs

- Word pagination is the renderer's job, so "length" is expressed in sections,
  not exact pages; a section count is predictable, a page count is not.
- `python-docx` styling is limited to the built-in style set; rich themed design
  (like a designed PPTX theme) is out of scope.
- Another format means another place a new `Complexity` level must be wired into
  block selection; mitigated by keeping the selection table in one module.

### Follow-ups (future ADRs)

- **#4** Complexity-driven Excel generator (builds on this ADR).
- **#5** Themed styling for the Word generator (built-in styles only today).

## Alternatives considered

- **Drive length by page or paragraph count.** Rejected: page count is only ever
  approximate in `.docx`; a flat paragraph count loses the section structure that
  makes documents look real. Sections give predictable, structured length.
- **A format selector on the existing deck tab.** Rejected: it mixes two
  different option sets (slides vs sections) in one form. A dedicated tab is
  clearer and matches the existing tab-per-task UI.
- **Word-specific complexity levels.** Rejected for now: reusing the shared
  levels keeps the mental model consistent; per-format block weighting lives in
  the generator, not in new enum values.

## Acceptance criteria

1. `generate doc --complexity maximum --sections 20 --out x.docx` produces a
   valid `.docx` that opens in Word / LibreOffice with varied content that fits
   the page.
2. Each complexity level yields visibly different richness (minimal =
   headings + paragraphs; maximum = all block types).
3. `--seed` makes output reproducible.
4. The web UI "Generate a document" tab generates and downloads a `.docx`.
5. A new format (Excel) can be added without rewriting the core, demonstrated by
   the shared generate-mode pieces.
6. Tests cover each level, determinism, block presence, and the CLI / UI routes;
   secret, security, and anti-hallucination reviews per the ADR template are
   clean.
