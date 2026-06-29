# How it works

This page is a conceptual overview. For the *decisions* behind each piece, follow
the links to the
[Architecture Decision Records](https://github.com/padraiglennon/common-file-generator/tree/main/design).

## Two modes

Everything the tool does falls into one of two modes:

- **Generate (from scratch).** Build a file at a chosen complexity and length.
  The layout is drawn by code; the text is lorem-ipsum. Useful when you need a
  realistically *structured* file and don't care about the words. Started by
  `generate <kind>` on the CLI, the generation tabs in the UI, or the
  `/api/generate/<kind>` endpoints
  ([ADR-001](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-001-template-driven-office-file-generator.md),
  [ADR-007](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-007-json-api-file-generation.md)).
- **Fill (Golden template).** Take a file you designed once, with placeholders
  marking where data goes, and inject values from a JSON data file - without
  redrawing the layout. Started by the **Use a template** tab or the fill
  endpoint. See [Preparing a Golden template](golden-file-guide.md).

## The complexity model

Generate mode is driven by five named levels - `minimal`, `simple`, `standard`,
`complex`, `maximum`. Each level defines a **pool** of building blocks (slide
types, document blocks, spreadsheet features). Higher levels *add* richer blocks
to the pool rather than replacing simpler ones, so a deck at `maximum` still has
plenty of ordinary content slides among the charts, tables, and videos.

Blocks are picked at random from the pool, **weighted** so common content
dominates and sparse elements (section dividers, page breaks) stay rare. A
**seed** makes the random choices reproducible: the same seed and inputs always
produce the same file. Because each unit (a slide, a section) carries a single
focal element, nothing overlaps or overflows.

The per-kind pools and how they grow per level are documented in each generator's
ADR
([deck](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-001-template-driven-office-file-generator.md),
[Word](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-003-word-document-generator.md),
[Excel](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-004-excel-workbook-generator.md),
[PDF](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-005-pdf-generator.md),
[Markdown](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-006-markdown-generator.md)).

## The layering

The code is organised into three layers, each a package under
`src/common_file_generator/`:

- **`core/`** - the shared spine: complexity levels, the lorem-ipsum source, the
  config loader, the injection report, and the top-level `generate` /
  `generate_deck` entry points. Holds no file-format knowledge of its own.
- **`generators/`** - generate-from-scratch logic, one module per format
  (`pptx`, `docx`, `xlsx`, `pdf`, `markdown`), plus shared styling/theme/layout
  helpers. Each turns a complexity level and length into a finished file.
- **`injectors/`** - fill-mode logic, one module per format that supports Golden
  templates (`pptx`, `docx`, `xlsx`), reading placeholders and writing in the
  data without disturbing the design.

A separate **`web/`** package
([ADR-002](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-002-fastapi-htmx-ui.md))
hosts the FastAPI app, the HTMX UI, and the JSON API. It holds **no** generation
logic - it validates the request, calls into `core`, and delivers the result.
The same `core` calls back the CLI, the UI, and the API, so all three stay in
lockstep.

## Running surfaces

- **CLI** - `generate` console script
  ([ADR-001](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-001-template-driven-office-file-generator.md)).
- **Web UI + JSON API** - the `gen-ui` server, also packaged as a container
  ([ADR-002](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-002-fastapi-htmx-ui.md),
  [ADR-008](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-008-containerize-api-and-ui.md)).
  Hosted generation is bounded by resource and concurrency caps
  ([ADR-010](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-010-resource-caps-hosted-generation.md),
  [ADR-013](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-013-concurrency-cap-hosted-generation.md)).

## Documentation & screenshots

This site is built with mkdocs + mkdocs-material and published to GitHub Pages by
CI
([ADR-011](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-011-docs-github-pages.md)).
The UI screenshots in the [walkthrough](ui-walkthrough.md) are captured by a
Playwright script (`make screenshots`) that drives the live UI headless and
writes committed PNGs; CI only embeds them, never runs a browser
([ADR-014](https://github.com/padraiglennon/common-file-generator/blob/main/design/ADR-014-visual-docs-ui-screenshots.md)).
