# ADR-014: Visual & narrative documentation with automated UI screenshots

- **Status:** Done
- **Date:** 2026-06-29
- **Tracking issue:** #23
- **Builds on:** ADR-011 (docs site via GitHub Pages), ADR-002 (FastAPI + HTMX UI)
- **Deciders:** Padraig Lennon

## Context

ADR-011 established a hosted documentation site (mkdocs + mkdocs-material on
GitHub Pages, built in CI) with a landing page and two reference guides
(Golden templates, the JSON data file). The README is thorough on the CLI. What
the docs do **not** have:

1. **A visual walkthrough of the web UI.** A new user cannot see what the app
   looks like before installing and running it. The UI (ADR-002) is a
   single-page HTMX app with six tabs (deck / document / spreadsheet / PDF /
   Markdown / fill-a-template), but nothing in the docs shows them.
2. **An end-to-end usage tutorial.** The three entry points - CLI, web UI, and
   JSON API (ADR-007) - are each documented in isolation. There is no narrative
   "start here, generate something, then fill a template" path tying them
   together.
3. **A conceptual "how it works" page.** The architecture lives only in the ADRs
   (one decision per file) and in the code. There is no single prose overview of
   the generate-vs-fill split, the complexity model, or the
   generators/injectors/core layering.

Two constraints shape the solution:

- **mkdocs builds in CI with `--strict` (ADR-011).** Any broken link or
  out-of-`docs_dir` reference is a hard failure. Screenshots must live under
  `docs/` and be referenced with in-tree relative paths.
- **The docs toolchain is deliberately kept out of the runtime container
  (ADR-011).** Any new dependency for documentation must follow the same rule -
  an optional extra, never a runtime dependency.

## Decision

### Three new documentation pages

Add three pages under `docs/`, wired into `mkdocs.yml` `nav`:

- **`docs/ui-walkthrough.md`** - a screenshot tour of the web UI: the landing
  page, each of the six generation tabs, and a completed-generation result with
  its download link. Each shot is captioned and cross-links to the relevant
  guide or ADR.
- **`docs/getting-started.md`** - a narrative end-to-end tutorial covering the
  three entry points: install + first CLI generation, the same via the web UI
  (illustrated with the walkthrough screenshots), and the JSON API. It ends by
  pointing at the Golden-template flow for the "fill" use case.
- **`docs/how-it-works.md`** - a conceptual overview: the two modes
  (generate-from-scratch vs. fill-a-Golden-template), the complexity model
  (how the slide/section/block pool grows per level), and the
  generators / injectors / core layering. It links out to the relevant ADRs for
  the decisions behind each piece rather than restating them.

### Automated screenshot capture

A capture script - `scripts/capture_screenshots.py` - produces the UI
screenshots deterministically using **Playwright** driving headless Chromium:

- Starts the existing `gen-ui` server in a subprocess on an ephemeral localhost
  port (not the default 18990, to avoid clashing with a dev instance), polling
  `/health` until ready.
- Navigates to `/`, then for each tab clicks its stable selector
  (`#tab-deck`, `#tab-doc`, `#tab-sheet`, `#tab-pdf`, `#tab-md`, `#tab-fill`)
  and screenshots the corresponding panel / full page.
- Drives one **seeded** generation on the deck tab (fixed seed, fixed inputs)
  and waits for the HTMX result partial to swap into `#deck-result`, then
  screenshots the result + download link.
- Writes PNGs to `docs/assets/screenshots/` with stable filenames
  (`ui-deck.png`, `ui-doc.png`, ..., `ui-result.png`).
- Tears the server subprocess down in a `finally` block.

The script is invoked through a new **`make screenshots`** target and is **not**
run in CI. The produced PNGs are **committed** to the repo. This keeps the CI
docs build deterministic and free of any browser toolchain: CI only embeds
already-committed images.

### Dependency placement

Playwright goes into its own **`shots`** optional-dependency group in
`pyproject.toml`, kept separate from both `docs` (mkdocs/mkdocs-material) and
`web` so a plain docs build never pulls the browser toolchain. It stays out of
the `web` extra and therefore out of the runtime container image (the Dockerfile
builds with `--extra web` only - unchanged by this ADR). Capturing drives the
live UI, so `make screenshots` syncs `--extra shots --extra web`, and requires a
one-time `playwright install chromium` to fetch the browser binary.

### Determinism

Screenshots use fixed inputs (fixed seed, fixed complexity, fixed counts) and a
fixed viewport size so re-running `make screenshots` yields visually stable
images, keeping diffs meaningful when the UI genuinely changes.

## Consequences

### Positive

- New users see the app before installing it; the UI, the end-to-end flow, and
  the architecture are all documented.
- The CI docs build stays deterministic and browser-free - images are committed
  artifacts, reviewable in diffs.
- Playwright never enters the runtime container; the docs/runtime separation
  from ADR-011 is preserved.

### Negative / trade-offs

- Committed screenshots can drift from the live UI if a maintainer changes the
  UI and forgets to re-run `make screenshots`. Mitigated by stable filenames and
  a documented target, but not enforced.
- Capturing requires a local Chromium download (`playwright install chromium`),
  a one-time per-machine cost for maintainers.
- Binary PNGs add weight to the repository.

### Follow-ups (future ADRs)

- **Optional CI screenshot-drift guard (#24).** Re-capture headless in CI and
  diff against the committed PNGs to catch UI drift at PR time. Deferred because
  it reintroduces the browser-in-CI cost this ADR deliberately avoids; needs its
  own ADR to weigh that against the protection.
- A sample-output gallery (rendering generated files to thumbnails) would also
  warrant its own ADR.

## Alternatives considered

- **Capture screenshots in CI on every docs build.** Rejected: adds Playwright +
  a running server to CI, makes the docs build heavier and flakier, and removes
  the reviewability of committed image diffs. The screenshots change rarely;
  paying that cost on every build is not justified.
- **Manual one-time screenshots.** Rejected: goes stale silently and gives no
  repeatable path to refresh. A scripted capture is barely more work and is
  re-runnable.
- **Autogenerated API docs (mkdocstrings) for the how-it-works page.** Rejected
  as out of scope: a conceptual overview linking to ADRs is what was asked for;
  per-module API reference is a heavier toolchain for a different need.
- **A sample-output gallery (render generated files to images).** Rejected as
  out of scope: it documents the *output*, not the *app*, and needs a separate
  rendering pipeline (LibreOffice/headless conversion). Candidate for a future
  ADR.

## Acceptance criteria

1. `make screenshots` deterministically produces PNGs for all six tabs plus a
   result view into `docs/assets/screenshots/`.
2. `mkdocs build --strict` exits 0 with the three new pages in `nav` and the
   embedded images resolving.
3. Playwright stays out of the runtime container image (Dockerfile unchanged;
   the new dependency is in the `shots` optional extra only).
4. The three pages render and cross-link to the existing guides and ADRs.
5. Secret, security, and anti-hallucination reviews are clean.
