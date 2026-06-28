# ADR-012: Themed styling for the Word document generator

- **Status:** Done
- **Date:** 2026-06-28
- **Tracking issue:** #5
- **Builds on:** ADR-003
- **Deciders:** Padraig Lennon

## Context

The Word generator (ADR-003, #3) builds a `.docx` from scratch using only
python-docx's built-in styles: `Heading 0/1/2`, `List Bullet`, `List Number`,
`Intense Quote`, and `Table Grid`. The result is structurally correct but looks
generic - there is no branded colour or typography, unlike the PPTX generator,
which applies an in-code `Theme` (colours + fonts) to give designed slides a
consistent look. ADR-003 listed this as an explicit follow-up.

The PPTX `Theme` (`generators/theme.py`) cannot be reused directly: its colour
fields are `pptx.dml.color.RGBColor`, a different type from python-docx's
`docx.shared.RGBColor`. Reusing it would force either a refactor of working
PPTX code or a brittle cross-format conversion. Word also has no slide-master or
gradient model, so a Word theme is a smaller surface: it restyles the built-in
paragraph, table, and run styles rather than drawing shapes.

This ADR adds programmatic theming to the Word generator: format-native theme
objects that restyle the built-in styles in code, with a small set of named
themes selectable from every surface (CLI, web UI, JSON API).

## Decision

Add programmatic Word theming via a new format-native `DocxTheme` and apply a
default theme to all generated documents.

### DocxTheme

A new `DocxTheme` dataclass (frozen) holds the palette and typography a Word
document needs, using `docx.shared.RGBColor` and font-name strings:

- `name`
- `heading_color`, `body_color`, `accent_color`
- `table_header_fill`, `table_header_text`
- `title_font`, `body_font`

It lives alongside the Word generator (a `docx_theme` module, mirroring how
`theme.py` sits beside the PPTX code) and does **not** import or depend on the
PPTX `Theme`. The two theme types stay independent; no shared base type is
introduced in this ADR.

### Three named themes, ocean is the default

Three themes ship as module-level constants:

- **ocean** - blue / teal headings and accents. It reuses the exact PPTX
  `OCEAN` hex values so the two generators read as the same palette, not merely
  the same family: `heading_color` / accent share `0x2E86C1` (primary) and
  `0x2EB88A` (accent), `body_color` shares `0x333333`. These values are
  mirrored, not imported (the PPTX `Theme` is `RGBColor`-typed), so the two
  definitions must be kept in sync - a drift test asserts the ocean hexes match
  `OCEAN`. This is `DEFAULT_DOCX_THEME`.
- **slate** - cool grey / charcoal headings, muted accent.
- **sand** - warm cream / brown headings, warm accent.

A `THEMES` lookup maps each name to its `DocxTheme`. The default (`ocean`) is
applied whenever no theme is named, so existing callers get a styled document
without changing their call.

### What a theme restyles

Theming sets attributes on the document's built-in styles and on the runs the
generator already creates - it does not introduce new block types:

- **Headings** - `Heading 0/1/2` get the theme's `heading_color` and
  `title_font`.
- **Body text** - the `Normal` style gets the theme's `body_color` and
  `body_font`, so paragraphs and list items inherit it.
- **Tables** - the header row gets a `table_header_fill` shading and
  `table_header_text` colour; cell text uses `body_font` (analogous to the PPTX
  `style_table` helper).
- **Quotes / accents** - the `Intense Quote` block is recoloured to the theme's
  `accent_color`.

Styles are mutated once on the `Document` before sections are added, so every
section inherits them.

### Surfaces

- **Core:** `generate_doc(...)` gains a `theme: str = "ocean"` keyword. It
  resolves the name to a `DocxTheme` via `THEMES` and passes it to the
  generator.
- **Generator:** `DocxComplexityGenerator` takes a `theme: DocxTheme` and
  applies it in `build()` before drawing sections.
- **CLI:** the `doc` subcommand gains `--theme {ocean,slate,sand}` (default
  `ocean`). Because `doc` is built by the shared `_add_section_parser`, the
  theme argument is added to `doc` specifically, not to the other
  section-based subcommands.
- **Web UI:** the Word form is derived from `generate_doc`'s signature plus
  `_DOC_FIELD_META`. A `theme` select field is added to the Word metadata, with
  friendly labels for the three themes. The introspected form picks it up
  automatically.
- **API:** `DocRequest` gains `theme: str = "ocean"`; `api_doc` forwards it.

### Unknown theme names fail clearly

An unrecognised theme name is a user error, not a silent fallback to the
default. Each surface rejects it in its own idiom:

- **Core:** `generate_doc` raises `ValueError` listing the valid names when the
  theme is not in `THEMES`.
- **CLI:** `--theme` is constrained to `choices={ocean, slate, sand}`, so
  argparse rejects an invalid value before the core runs.
- **Web UI:** the theme select offers only the three valid options.
- **API:** `DocRequest.theme` validates against the allowed set and a bad value
  returns a 4xx (not a 500 from a downstream raise).

### Accessibility

Each theme's text-on-fill pairings - heading and body text on the page, and
table-header text on `table_header_fill` - must stay comfortably legible. The
palettes are chosen so every text/background pairing clears a readable contrast
bar (WCAG AA, 4.5:1 for body text), so `slate` and `sand` do not ship
low-contrast combinations.

### PDF and Markdown stay unthemed

PDF and Markdown currently reuse the Word form's `_DOC_FIELD_META`. To keep
theming Word-only, the shared metadata is split: the theme field is added to a
Word-specific metadata dict, and the PDF/Markdown forms continue to use the
section/complexity/seed shape without it. PDF and Markdown theming, if wanted,
are separate decisions.

### Determinism

Theming is a pure styling pass with no randomness, so determinism is preserved:
the same `(theme, complexity, sections, seed)` yields identical document
*content*. Determinism is over content, not raw bytes - a `.docx` is a zip whose
entries carry a save-time timestamp, so two runs straddling a clock tick can
differ in those timestamps while every zip member's bytes are identical. Tests
assert on content (text and zip-member bytes), matching the existing
ADR-003-era determinism tests.

## Consequences

### Positive

- Generated Word documents look designed, closing the gap with the PPTX
  generator and resolving the ADR-003 follow-up.
- `DocxTheme` is format-native and self-contained: no external `.docx` assets,
  no cross-format coupling, no change to working PPTX code.
- Adding a fourth theme later is a one-constant change plus a label and a CLI
  choice.

### Negative / trade-offs

- The default Word output changes appearance, so existing fixtures need a
  one-time update. Mitigated by determinism: the new default is still stable.
- A second theme vocabulary (`DocxTheme` beside `Theme`) means two palettes to
  keep visually aligned if "ocean" should match across formats. Mitigated by
  sharing the same hex values for the ocean palette.
- python-docx table-cell shading is set via low-level XML (`w:shd`), which is
  more verbose than the PPTX fill API.

### Follow-ups (future ADRs)

- A themed base-`.docx`-template path (designed templates whose styles are
  inherited), if richer design than programmatic styling is later needed.
- PDF / Markdown theming, if the same branding should extend to those formats.

## Alternatives considered

- **Themed base `.docx` template** (ship designed `.docx` files inherited as
  the base, like deck's `--theme .pptx`). Rejected for this cut: it adds binary
  assets to the repo and a file-path surface, and programmatic styling covers
  the headings/body/tables/quotes the issue calls for without either.
- **Reuse the PPTX `Theme` dataclass.** Rejected: its `RGBColor` fields are the
  pptx type, not python-docx's, so it would force a refactor of working PPTX
  code or a brittle conversion. A separate `DocxTheme` is cleaner and stays in
  scope.
- **Theme opt-in only (plain default unchanged).** Rejected: the confirmed
  decision is for the default themed look so the feature is visible without
  callers opting in; determinism makes the fixture update safe.
- **Extend theming to PDF and Markdown now.** Rejected: out of this issue's
  scope; Markdown has no colour model and PDF styling is its own design pass.

## Acceptance criteria

1. `generate doc --theme slate --out x.docx` (and `ocean` / `sand`) produces a
   valid `.docx` that opens in Word / LibreOffice with the theme's heading
   colour, body font, table header fill, and quote accent applied.
2. The three themes are visibly distinct across headings, body font, table
   header, and quote accent.
3. The same `(theme, complexity, sections, seed)` yields identical document
   content (determinism preserved). Determinism is over content, not raw bytes:
   the `.docx` zip stamps each entry with the save time, so the assertion
   compares zip-member bytes, not the whole file.
4. The CLI `--theme`, the web Word form select, and the API `DocRequest.theme`
   all select a theme; omitting it applies `ocean`.
5. The PDF and Markdown forms are unchanged - no theme field appears on them.
6. An unknown theme name fails clearly: `generate_doc` raises a `ValueError`
   listing valid names, the CLI rejects it via `choices`, and the API returns a
   4xx (not a 500).
7. Each theme's heading, body, and table-header text clears a readable contrast
   bar (WCAG AA 4.5:1 for body text) against its background / fill.
8. The `ocean` theme's hex values match the PPTX `OCEAN` palette, guarded by a
   drift test so the mirrored constants cannot silently diverge.
9. Tests cover each theme, determinism, table-header shading, and the
   CLI / UI / API surfaces; secret, security, and anti-hallucination reviews
   are clean.
