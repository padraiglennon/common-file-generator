# How it works

This page is a conceptual overview.

## Two modes

Everything the tool does falls into one of two modes:

- **Generate (from scratch).** Build a file at a chosen complexity and length.
  The layout is drawn by code; the text is lorem-ipsum. Useful when you need a
  realistically *structured* file and don't care about the words. Started by
  `generate <kind>` on the CLI, the generation tabs in the UI, or the
  `/api/generate/<kind>` endpoints.
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

A separate **`web/`** package hosts the FastAPI app, the HTMX UI, and the JSON
API. It holds **no** generation logic - it validates the request, calls into
`core`, and delivers the result. The same `core` calls back the CLI, the UI, and
the API, so all three stay in lockstep.

## Running surfaces

- **CLI** - `generate` console script.
- **Web UI + JSON API** - the `gen-ui` server, also packaged as a container.
  Hosted generation is bounded by resource and concurrency caps.

## Documentation & screenshots

This site is built with mkdocs + mkdocs-material and published to GitHub Pages by
CI. The UI screenshots in the [walkthrough](ui-walkthrough.md) are captured by a
Playwright script (`make screenshots`) that drives the live UI headless and
writes committed PNGs; CI only embeds them, never runs a browser.
