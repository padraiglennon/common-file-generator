# ADR-001: Template-driven Office file generator (Golden-file data injection)

- **Status:** Done
- **Date:** 2026-06-24
- **Tracking issue:** #1
- **Deciders:** Padraig Lennon

## Context

Users need complex, production-ready Microsoft Office files
(PowerPoint, Word, Excel) to use as test data. The tool is general-purpose -
the data supplier could be anyone (a tester, an analyst, an ops person, a
marketer); no particular team or role is assumed. Two properties matter:

1. The files must look **professionally designed** - real layouts, branded
   themes, charts, and tables - not something obviously assembled by code.
2. The people who supply the *content* are typically **non-technical**.
   They should not need programming knowledge to drive the data into the files.

A naive "generate everything in code" approach fails property (1): hand-drawing
slides/shapes with `python-pptx` produces flat, unconvincing files and couples
visual design to code. It also concentrates all design effort in the codebase,
which non-technical users cannot review or adjust.

We therefore want a **template-driven** system: designers build polished
"Golden" template files once in PowerPoint/Word/Excel, and the tool only
**injects data** into the existing shapes, placeholders, and tables. The data
comes from a JSON configuration that a non-programmer can edit by example.

The repository is greenfield (only `README`, `LICENSE`, `.gitignore`). This ADR
also establishes the project's Python tooling baseline.

## Decision

Build a modular Python toolset that supports **two modes** over a shared core:

1. **Inject mode (template-driven)** - fill a pre-designed Golden template from a
   JSON config; never generate layout. This is the original decision below.
2. **Generate mode (complexity-driven)** - build a deck from scratch at a chosen
   complexity level and slide count, with seeded lorem-ipsum content. Added by
   the scope correction recorded below.

### Scope correction (added during implementation)

The clarification loop settled on *template-driven only*. During implementation
the user clarified that the **most common usage** is "generate me an N-slide deck
at a given complexity" (e.g. a 70-slide maximum-complexity deck) - i.e. the tool
must *generate* layout, the original "different configurations of complexity"
requirement from the very first prompt. That cannot be served by injection into a
hand-made template.

Rather than silently rewrite the architecture, the decision was widened: generate
mode was **added alongside** inject mode (not replacing it) on the same core
(config, reporting, lorem, complexity profiles). The two compose - generate mode
can produce rich templates that inject mode then personalizes.

### Core principle for inject mode: inject, never generate layout

In **inject mode**, the code **never creates layout components**. Golden template
files are the sole source of visual design. The engine's only job is to populate
pre-existing elements: text placeholders, tables, chart series, and picture
placeholders.

### Named-tag mapping

Golden files carry **named markers** that the JSON config references by name
(order-independent, robust to reordering):

- **Shape names** - set via PowerPoint/Word's *Selection Pane* (no code).
- **`{{token}}` text placeholders** - literal double-brace tokens typed into
  text boxes / runs.
- **Named tables** - tables identified by their containing shape's name.

A non-technical *Golden-file preparation guide* (deliverable) explains how to set
these names with screenshots, requiring no programming, so any user can prepare
a template.

### Modular, format-agnostic core + per-format injectors

A shared `Injector` interface/base encapsulates the inject workflow
(load template -> validate config -> populate elements -> write report -> save).
Concrete injectors implement the per-format mechanics:

- `PptxInjector` - `python-pptx`
- `DocxInjector` - `python-docx`
- `XlsxInjector` - `openpyxl`

New document formats or new templates plug in **without rewriting the core
engine** (scalability requirement). Format selection is by file extension.

### JSON configuration schema

A JSON config maps data keys to named template elements: text values, table
row-sets (multi-row/multi-column dynamic data), chart series, and media
(picture) placeholders. A **heavily-commented sample config** ships as the
canonical example users copy and edit, backed by a field-by-field guide
and schema validation with friendly messages.

Media assets are referenced by **local file paths** (relative to an assets dir);
no network access.

### Library-first, CLI as a thin wrapper

All logic lives in the library (`generate(...)` API + `Injector` classes).
`cli.py` is a thin wrapper containing **no business logic**, so a future UI
front-end (#2) can drive the same core. Developers run the CLI; non-technical
users only supply data.

```text
generate fill --template templates/deck.pptx --config configs/q3-deck.json --out out/q3-deck.pptx
```

### Generate mode: complexity-driven decks

`generate_deck(...)` builds a PowerPoint deck from scratch. Each slide is **one
designed slide type** with a single focal element - bullets, a chevron list, an
image-and-text pane, a chart, a fit-to-slot table, a video link, or a section
divider. The named **complexity** level (`minimal`...`maximum`) selects which slide
types are in the pool; `--slides N` sets the count; each slide's type is drawn at
random from the pool with the seeded RNG, using per-type **weights** so content
slides dominate and sparse section dividers stay rare.

The single-focal-element rule is deliberate: an earlier grid design crammed many
large elements onto each slide, which overlapped and (for tables, whose rendered
height grows with content) overflowed the slide. One element per slide, with
tables capped to the rows that fit their box, eliminates both. A geometry test
asserts no shape extends past the slide and no table overflows.

Content is seeded **lorem-ipsum**, and placeholder images and the video poster are
generated in memory, so a deck needs no external assets and is reproducible for a
given `(complexity, slides, seed)`.

Video slides embed a generated poster (with a play button) hyperlinked to a
YouTube URL (`--video-url`, default provided). python-pptx cannot author true
inline-YouTube playback or `add_movie` from a URL, so the poster-plus-hyperlink is
the portable approximation. `--theme path.pptx` uses a designed deck as the base
so its master/layouts/colours carry through; otherwise an in-code theme is applied.

```text
generate deck --out output/deck.pptx --complexity maximum --slides 70 --seed 0
```

New formats (DOCX/XLSX generators) and new slide types plug in without changing
the core, mirroring the injector design.

### Error handling: log + best-effort + plain-English report

Data-fit mismatches (e.g. dataset has more rows than the table holds, a named
shape is missing, a media file is absent) **never crash** the run. The engine:

1. Logs a technical warning (standard `logging`), and
2. Fills what fits / skips or truncates the rest, and
3. Writes a **plain-English report file** any user can act on, e.g.
   *"Slide 3 table: you gave 12 rows but the template holds 10 - kept the first 10."*

### Project tooling & layout

Python **3.14**, managed by **uv** with virtual environments, **PEP 8**
throughout, `src/` layout, tests under `tests/`.

```text
pyproject.toml                       # uv project; [project.scripts] entry point
src/common_file_generator/
  core/                              # config, JSON schema, validation, reporting,
                                     #   base Injector, complexity pool, lorem
  injectors/                         # inject mode: pptx.py, docx.py, xlsx.py
  generators/                        # generate mode: pptx.py + slides.py (slide
                                     #   types), style.py, theme.py, layout.py
  cli.py                             # thin wrapper over core (fill / deck)
templates/                           # Golden template files (.pptx/.docx/.xlsx)
configs/                             # commented sample JSON configs
assets/                              # sample media (images) referenced by configs
output/                              # generated files (git-ignored)
tests/                               # pytest
docs/                                # Golden-file prep guide + JSON field guide
design/                              # ADRs
```

## Consequences

### Positive

- Files look professionally designed because designers own the templates.
- Non-technical users edit approachable JSON by example; never touch code.
- The format-agnostic core makes adding DOCX/XLSX/future formats cheap.
- Library-first design lets a future UI (#2) reuse the engine unchanged.
- Best-effort + plain-English reporting makes failures self-serviceable.

### Negative / trade-offs

- Golden templates must be prepared and named correctly up front; a missing or
  mis-named marker is a class of error the prep guide must mitigate.
- Three engines (`python-pptx`, `python-docx`, `openpyxl`) are dependencies with
  differing capabilities; some features are format-specific.
- Positional fallbacks are deliberately excluded (named-tag only), so templates
  authored without names cannot be targeted until named.

### Follow-ups

- **#2** - optional UI front-end for the generator (builds on this ADR; requires
  its own ADR before implementation).

## Alternatives considered

- **Code-generated layout (`python-pptx` draws slides).** Rejected: produces
  unconvincing files and couples design to code; contradicts the core need.
- **Positional / index-based mapping.** Rejected: brittle - reordering shapes
  silently breaks mappings. Named-tag chosen instead.
- **YAML config.** Rejected: friendlier syntactically but contradicts the
  explicit JSON requirement; approachability is met via comments + validation.
- **PPTX-only first delivery.** Rejected: all three formats are needed; the
  shared `Injector` interface keeps the multi-format scope manageable.
- **Fail-fast error policy.** Rejected as the default for bulk test-file
  generation; log + best-effort + report is more forgiving.

## Acceptance criteria

1. `generate --template ... --config ... --out ...` injects JSON data into a Golden
   PPTX/DOCX/XLSX and produces a valid file that opens with layout intact.
2. Dynamic tables, text placeholders, and media insertion all work via named tags.
3. Data-fit mismatches produce a plain-English report and a best-effort file
   (no crash).
4. A new format/template can be added without modifying the core engine.
5. A commented sample JSON config and a non-technical Golden-file prep guide exist.
6. `pytest` covers each injector and the error/report path.
7. Standard ADR review gates: security review, documentation updated,
   anti-hallucination review.
