# ADR-006: Complexity-driven Markdown generator

- **Status:** Done
- **Date:** 2026-06-24
- **Tracking issue:** #7
- **Builds on:** ADR-003
- **Deciders:** Padraig Lennon

## Context

The tool generates PowerPoint, Word, Excel (ADR-001/003/004) and PDF (ADR-005)
files from scratch. This ADR adds the other format requested when widening the
tool's purpose beyond MS Office: **Markdown**.

Markdown only fits generate mode. It is plaintext with no binary template to
inject into, so fill mode is intentionally out of scope. Unlike every other
format, it needs **no third-party library** - output is assembled as a string
with the standard library.

ADR-003 factored the shared generate-mode pieces (the seeded `Lorem`, the
`Complexity` enum, the `generate_<format>()` + CLI subcommand + UI tab pattern)
so this format plugs in without rewriting the core.

## Decision

Add a complexity-driven Markdown generator with no new dependency.

### MarkdownComplexityGenerator

`generators/markdown.py` builds a `.md` from scratch by string assembly. A
document is a sequence of **sections**; each section is a heading and a paragraph
followed by a run of content blocks. `build()` returns the Markdown string;
`save()` writes it UTF-8.

### Complexity scales content, sections set length

The named **complexity** levels (`minimal`...`maximum`) are reused from the core
and share the **same Word block vocabulary** (`doc_block_pool`). `--sections N`
is the length dial.

### Content blocks (Markdown rendering)

The shared block *vocabulary* renders in format-appropriate Markdown:

- **Headings + paragraphs** as `#` / `##` / `###` headings and plain text.
- **Bullet and numbered lists** as `- item` and `1. item` lines.
- **Tables** as GitHub-flavoured pipe tables with a `| --- |` separator row.
- **Block quotes** as `> ...` lines.
- **Images** render as a **fenced code block** with lorem text. Markdown has no
  image bytes, and emitting a `![alt](file.png)` reference would either break the
  single-file contract (a sidecar PNG) or render as a broken-image icon. A fenced
  code block is real, visible, self-contained content - the output stays one
  portable `.md` file.
- **Page breaks** render as a **horizontal rule** (`---`); a hard page break is
  meaningless in Markdown, and a rule is the closest section-divider equivalent.

### Deterministic

The same `(complexity, sections, seed)` yields byte-for-byte identical Markdown:
unlike PDF, there is no embedded timestamp, so output is fully reproducible.

### Surfaces

- **CLI:** a new `markdown` subcommand (alias `md`):
  `generate markdown --out file.md --complexity <level> --sections N --seed N`.
  Word, PDF, and Markdown share one argument shape via `_add_section_parser`.
- **Web UI:** a new **"Generate Markdown"** tab with an introspected form
  (complexity, sections, seed) reusing the Word form metadata, posting to a new
  `/generate/md` route and returning the same timestamped download partial.
- **Core:** a `generate_markdown(...)` function next to `generate_doc(...)`.

## Consequences

### Positive

- Widens the tool to Markdown, a ubiquitous plaintext test/document format, with
  zero new dependencies.
- Reuses the complexity model, lorem helper, and the Word block vocabulary, so
  there is little new surface to learn.
- Output is fully deterministic (no embedded timestamp), the strongest
  reproducibility of any format.

### Negative / trade-offs

- Markdown has no native image or page-break concept; both are represented by
  the closest equivalent (fenced code block, horizontal rule) rather than a true
  one-to-one mapping.
- Rendering fidelity depends on the viewer's Markdown flavour; GFM pipe tables
  and fenced code blocks are widely but not universally supported.

### Follow-ups (future ADRs)

- None planned. PDF (ADR-005) is the sibling format from the same request.

## Alternatives considered

- **A Markdown rendering library (e.g. `markdown`).** Rejected: that library
  renders Markdown *to HTML*; generating Markdown *text* needs only string
  assembly, so a dependency would add nothing.
- **Image block as a sidecar PNG + `![alt](file.png)`.** Rejected: it breaks the
  single, self-contained `.md` contract and complicates the web download (one
  artifact per token). A fenced code block keeps one portable file.
- **Markdown fill (inject) mode.** Rejected: Markdown is plaintext with no
  template-injection surface; generate mode is the only sensible fit.

## Acceptance criteria

1. `generate markdown --complexity maximum --sections 20 --out x.md` produces a
   valid `.md` that renders with headings, lists, a GFM table, a block quote, and
   a fenced code block.
2. Each complexity level yields visibly different richness (minimal =
   headings + paragraphs; maximum = all block types).
3. `--seed` makes output byte-for-byte reproducible.
4. The `md` alias works identically to `markdown`.
5. The web UI "Generate Markdown" tab generates and downloads a `.md`.
6. Tests cover each level, byte determinism, block presence, and the CLI / UI
   routes; secret, security, and anti-hallucination reviews per the ADR template
   are clean.
