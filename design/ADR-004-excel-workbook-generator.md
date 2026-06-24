# ADR-004: Complexity-driven Excel workbook generator

- **Status:** Done
- **Date:** 2026-06-24
- **Tracking issue:** #4
- **Builds on:** ADR-003
- **Deciders:** Padraig Lennon

## Context

The tool generates PowerPoint decks (ADR-001) and Word documents (ADR-003) from
scratch, and injects into Excel templates (ADR-001 fill mode). The missing piece
is *generating* an Excel workbook from scratch. This ADR adds it and completes
the generate-mode trio (PPTX / DOCX / XLSX). It is the follow-up tracked by #4.

ADR-003 deliberately factored the shared generate-mode pieces (the seeded
`Lorem`, the `Complexity` enum, the `generate_<format>()` + CLI subcommand + UI
tab pattern) so this format plugs in without rewriting the core.

## Decision

Add a complexity-driven Excel generator built on `openpyxl`.

### XlsxComplexityGenerator

`generators/xlsx.py` builds a `.xlsx` from scratch. A workbook is a set of
**sheets**; each sheet is a titled area holding one or more data tables. The
generator never injects into a template (that is fill mode).

### Complexity scales sheet content, sheets set length

The named **complexity** levels (`minimal`...`maximum`) are reused. They decide
what each sheet contains:

- `minimal`: one small data table (a header row plus typed rows),
- rising levels add **formula total rows** (`=SUM`, `=AVERAGE`) and computed
  columns, then **charts** (bar / line / pie from the table data), then
  **styling** (header fills and bold, column widths, number formats) and
  **multiple tables per sheet**,
- `maximum`: all features.

`--sheets N` is the length dial (the analogue of `--slides` / `--sections`).

### Rows per table

Rows per table scale with complexity (smaller at `minimal`, larger at
`maximum`), with an optional `--rows N` override, consistent with Word's
`--blocks-per-section`.

### Typed data and live formulas

Cell data is typed: numbers (seeded RNG), text (`Lorem`), and dates. Formula
cells contain formula strings (`=SUM(B2:B11)`, `=AVERAGE(...)`) that reference
the generated ranges, so the workbook is "live" when opened.

### Charts and formulas via openpyxl

Charts use openpyxl's native `BarChart` / `LineChart` / `PieChart` over
`Reference` cell ranges; formulas are written as strings into total cells. These
APIs are verified against the installed openpyxl before coding, as with prior
ADRs.

### Deterministic

`--seed` makes output reproducible: the same `(complexity, sheets, seed)` yields
the identical workbook. The seeded `Lorem` drives text and a seeded RNG drives
numeric data.

### Surfaces

- **CLI:** a new `sheet` subcommand:
  `generate sheet --out file.xlsx --complexity <level> --sheets N --rows N --seed N`.
- **Web UI:** a new **"Generate a spreadsheet"** tab alongside the deck, document,
  and template tabs, with an introspected form (complexity, sheets, seed),
  posting to a new `/generate/sheet` route and returning the same timestamped,
  flashing download partial.
- **Core:** a `generate_sheet(...)` function next to `generate_deck(...)` and
  `generate_doc(...)`.

### Reuse

A new `sheet_feature_pool` lives in the complexity module beside `slide_pool`
and `doc_block_pool`. The seeded `Lorem`, the `Complexity` levels, and the
generate-mode pattern are reused. With Excel done, the trio is complete and the
pattern is proven across all three formats.

## Consequences

### Positive

- Completes generate mode: the tool can now generate PPTX, DOCX, and XLSX.
- Reuses the complexity model, lorem helper, and the generate-mode wiring, so
  there is little new surface to learn.
- Live formulas and charts make the generated workbooks realistic test files.

### Negative / trade-offs

- openpyxl writes formula *strings*; it does not compute values, so a generated
  workbook shows formulas that the spreadsheet app evaluates on open (expected
  for test files, but values are not embedded).
- Chart and styling APIs add a little per-feature wiring; kept in one module so a
  new `Complexity` level is wired in one place.
- Workbook styling is basic (fills, fonts, widths, number formats); rich themed
  styling is out of scope.

### Follow-ups (future ADRs)

- None required to complete the trio. Pivot tables, conditional formatting,
  cross-sheet formula graphs, and themed workbook styling are possible future
  enhancements (each its own ADR).

## Alternatives considered

- **Single worksheet, complexity scales features on it.** Rejected: a workbook of
  sheets is more workbook-like and gives a natural length dial (`--sheets`),
  matching how the deck and document generators are structured.
- **Skip charts, formulas only.** Rejected: the confirmed feature set includes
  charts, and openpyxl supports them natively; dropping them would make the
  Excel generator visibly thinner than the PPTX one.
- **Excel-specific complexity levels.** Rejected: reusing the shared levels keeps
  the mental model consistent; per-format feature weighting lives in the
  generator, not in new enum values.

## Acceptance criteria

1. `generate sheet --complexity maximum --sheets 5 --out x.xlsx` produces a valid
   `.xlsx` that opens in Excel / LibreOffice with data tables, working formulas,
   and charts.
2. Each complexity level yields visibly different richness (minimal = one plain
   table; maximum = formulas + charts + styling + multiple tables).
3. `--seed` makes output reproducible; `--rows N` overrides table size.
4. The web UI "Generate a spreadsheet" tab generates and downloads an `.xlsx`.
5. Tests cover each level, determinism, formula and chart presence, the rows
   override, and the CLI / UI routes; secret, security, and anti-hallucination
   reviews per the ADR template are clean.
