# ADR-005: Complexity-driven PDF generator

- **Status:** Done
- **Date:** 2026-06-24
- **Tracking issue:** #6
- **Builds on:** ADR-003
- **Deciders:** Padraig Lennon

## Context

The tool generates PowerPoint decks (ADR-001), Word documents (ADR-003), and
Excel workbooks (ADR-004) from scratch, and injects into Office templates
(ADR-001 fill mode). This ADR widens the tool's purpose beyond MS Office to a
common test-file format that has no generate-mode support yet: **PDF**.

PDF only fits generate mode. Unlike `.docx`/`.pptx`/`.xlsx`, there is no
practical "Golden template" to inject into - a PDF is effectively write-only via
a layout library - so fill mode is intentionally out of scope for this format.

ADR-003 deliberately factored the shared generate-mode pieces (the seeded
`Lorem`, the `Complexity` enum, the `generate_<format>()` + CLI subcommand + UI
tab pattern) so this format plugs in without rewriting the core.

## Decision

Add a complexity-driven PDF generator built on `reportlab` (its `platypus`
layout engine).

### PdfComplexityGenerator

`generators/pdf.py` builds a `.pdf` from scratch. A document is a sequence of
**sections**; each section is a heading and a paragraph followed by a run of
content blocks. The generator never injects into a template (there is no PDF
fill mode) and owns all layout decisions.

### Complexity scales content, sections set length

The named **complexity** levels (`minimal`...`maximum`) are reused from the core
and share the **same Word block vocabulary** (`doc_block_pool`): the document
block types (`paragraph / bullets / numbered / table / image / quote /
page_break`) map onto reportlab flowables. `--sections N` is the length dial.

### Content blocks (flowable mapping)

- **Headings + paragraphs** using the sample stylesheet's `Title` / `Heading1` /
  `Heading2` / `BodyText` styles and lorem-ipsum body text.
- **Bullet and numbered lists** as `ListFlowable` (`bulletType="bullet"` / `"1"`).
- **Tables** as `Table` with a shaded header row and an explicit `colWidths`
  fitted to the usable page width so they never overflow the margins.
- **Images** as `Image` from an in-memory placeholder PNG (same PIL helper as the
  Word generator), with explicit width/height preserving aspect ratio.
- **Block quotes** (italic style) and **page breaks** (`PageBreak`) at higher
  complexity.

### Deterministic content

`--seed` makes the *content* reproducible: the same `(complexity, sections,
seed)` yields the same text, tables, and image colours, driven by the existing
seeded `Lorem`. reportlab embeds a creation timestamp in the PDF, so the bytes
are not identical between runs; determinism is asserted on extracted text, not
raw bytes.

### Surfaces

- **CLI:** a new `pdf` subcommand:
  `generate pdf --out file.pdf --complexity <level> --sections N --seed N`.
  Word, PDF, and Markdown share one argument shape via `_add_section_parser`.
- **Web UI:** a new **"Generate a PDF"** tab with an introspected form
  (complexity, sections, seed) reusing the Word form metadata, posting to a new
  `/generate/pdf` route and returning the same timestamped download partial.
- **Core:** a `generate_pdf(...)` function next to `generate_doc(...)`.

## Consequences

### Positive

- Widens the tool beyond MS Office to PDF, a ubiquitous test-file format.
- Reuses the complexity model, lorem helper, and the Word block vocabulary, so
  there is little new surface to learn and behaviour is consistent.
- The generate-mode pattern now spans five formats, confirming it generalises.

### Negative / trade-offs

- reportlab embeds a creation timestamp, so PDFs are not byte-identical between
  runs; the generated *content* is deterministic, which is what tests assert.
- PDF pagination is the layout engine's job, so "length" is expressed in
  sections, not exact pages (same trade-off as Word).
- `reportlab` is a new runtime dependency.

### Follow-ups (future ADRs)

- **#7** Complexity-driven Markdown generator (sibling format, separate ADR-006).

## Alternatives considered

- **Render a `.docx` then convert to PDF (LibreOffice / docx2pdf).** Rejected: it
  adds a heavy external dependency or platform limits, and couples PDF output to
  Word's styling. A native `reportlab` build is self-contained and gives full
  layout control.
- **`fpdf2` instead of `reportlab`.** Rejected: lighter but with weaker table /
  flowable support; `reportlab`'s platypus maps cleanly onto the existing block
  vocabulary.
- **PDF fill (inject) mode.** Rejected: PDFs have no practical template-injection
  surface analogous to Office placeholders; generate mode is the right fit.

## Acceptance criteria

1. `generate pdf --complexity maximum --sections 20 --out x.pdf` produces a valid
   `%PDF` file that opens cleanly with varied content that fits the page.
2. Each complexity level yields visibly different richness (minimal =
   headings + paragraphs; maximum = all block types).
3. `--seed` makes the extracted content reproducible.
4. The web UI "Generate a PDF" tab generates and downloads a `.pdf`.
5. Tables fit the usable page width (no overflow); images keep their aspect ratio.
6. Tests cover each level, structural determinism, the `%PDF` magic bytes, and the
   CLI / UI routes; secret, security, and anti-hallucination reviews per the ADR
   template are clean.
