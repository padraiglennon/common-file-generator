# ADR-009: Rename the project to common-file-generator

- **Status:** Done
- **Date:** 2026-06-27
- **Tracking issue:** #14
- **Builds on:** ADR-001, ADR-005, ADR-006
- **Deciders:** Padraig Lennon

## Context

The project began as a generator for **MS Office** files only (PPTX/DOCX/XLSX,
ADR-001) and was named accordingly: the repo, the published package, and the
Python import package are all `ms_office_file_generator` / `ms-office-file-generator`.

Its scope has since widened beyond Office. ADR-005 added a PDF generator and
ADR-006 a Markdown generator; the web UI already advertises "Create test
PowerPoint, Word, Excel, PDF, and Markdown files". The name now misrepresents
what the tool produces - PDF and Markdown are not MS Office formats - and will
keep drifting further from reality as more formats are added.

A rename is a cross-cutting change (package directory, ~41 files of imports,
packaging metadata, container image names, docs, the GitHub repo slug), so it is
recorded here before the mechanical change lands.

## Decision

Rename the project to **`common-file-generator`**. This is a **full** rename: the
Python import package is renamed too, so the import name stays consistent with the
project name rather than leaving a stale `ms_office_file_generator` module behind.

| Surface | Old | New |
| --- | --- | --- |
| Repo slug / kebab name | `ms-office-file-generator` | `common-file-generator` |
| Python import package | `ms_office_file_generator` | `common_file_generator` |
| Human-readable title | "Office file generator" | "Common File Generator" |
| CLI entry points | `generate`, `gen-ui` | unchanged |

The entry-point command names (`generate`, `gen-ui`) are **not** renamed - they
are scoped to file generation generally, already format-agnostic, and renaming
them would break every existing invocation for no benefit.

### Python package + imports

- `git mv src/ms_office_file_generator/ src/common_file_generator/` (preserve
  history).
- Replace every `ms_office_file_generator` import across source and the test
  suite (~41 files) with `common_file_generator`. After the sweep,
  `grep -rn ms_office_file_generator .` must return nothing.

### Packaging

In `pyproject.toml`:

- `name = "common-file-generator"`
- `[project.scripts]` module paths → `common_file_generator.cli:main`,
  `common_file_generator.web.server:main`
- `[tool.hatch.build.targets.wheel]` `packages` and `artifacts` globs →
  `src/common_file_generator/...`
- `[tool.ruff.lint.isort]` `known-first-party = ["common_file_generator"]`

`.pre-commit-config.yaml` exclude paths → `src/common_file_generator/web/static/...`.

`uv.lock` pins the project's own `name`; it is **regenerated** with `uv lock`
after `pyproject.toml` changes - never hand-edited - and committed alongside the
rename.

### Container / build

- `Makefile` and `docker-compose.yml` image names → `common-file-generator:local`.
- README Docker example → `ghcr.io/padraiglennon/common-file-generator:latest`.
- `.github/workflows/publish-image.yml` derives the image from
  `${{ github.repository }}`, so it follows the GitHub repo rename automatically -
  no string change.

### UI and self-description

- `web/templates/index.html` `<title>` and `<h1>` → "Common File Generator".
- Package docstrings and CLI help text that say "MS Office files" are reworded to
  "office and document files" so the package self-description matches the widened
  scope. This is minimal de-scoping wording, not a copy rewrite.

### Documentation

- README heading, path references, Docker image.
- `design/README.md`: the eight GitHub issue URLs and a new ADR-009 row.
- `design/ADR-008` container image URLs; `design/ADR-001`/`ADR-002` package path
  references.
- Existing ADR **titles** (e.g. ADR-001 "...Office file generator") are left as
  historical records - they describe the project as it was at the time.

### Manual steps (outside the committed diff)

These cannot be done from the working tree and are handed to the maintainer:

1. GitHub → repo Settings → rename to `common-file-generator` (GitHub keeps a
   redirect from the old slug).
2. `git remote set-url origin git@github.com:padraiglennon/common-file-generator.git`
3. `uv sync` to re-register the renamed console scripts in the local environment.

## Consequences

### Positive

- The name matches what the tool does, and stays accurate as more non-Office
  formats are added.
- Import name and project name stay consistent (no stale `ms_office_*` module).
- GitHub's slug redirect means existing clones and links keep working until
  remotes are updated.

### Negative / trade-offs

- Large mechanical diff (~50 files) and a forced re-install (`uv sync`) for any
  existing checkout, since the console-script package path changes.
- The published image name on ghcr changes; any consumer pinning the old image
  path must update it (no images have been published yet, so impact is minimal).
- The old PyPI/package name is abandoned; not yet published, so no release
  breakage.

### Follow-ups (future ADRs)

- None required. Future format generators inherit the generic name without a
  further rename.

## Alternatives considered

- **`test-file-generator`.** Leads with the *why* (test fixtures) over the *what*.
  Rejected: "common" was preferred as the maintainer's pick; "test" over-narrows
  to the testing use case when the tool is a general file generator.
- **`doc-file-generator` / `sample-doc-generator`.** Scope to "documents".
  Rejected: "doc" reads as Word `.doc` to some, and "document" is arguably
  narrower than the arbitrary-file future the tool is heading toward.
- **Metadata-only rename (keep `ms_office_file_generator` as the import package).**
  Far smaller diff, no import churn. Rejected: leaves the import name permanently
  inconsistent with the project name - a lasting smell - for a one-time saving.
- **Keep the current name.** Rejected: actively misleading now that PDF and
  Markdown are first-class outputs.

## Acceptance criteria

1. `grep -rn 'ms_office_file_generator' .` and `grep -rn 'ms-office-file-generator' .`
   return nothing (including `uv.lock`; historical ADR title text excepted).
2. `uv sync` regenerates `uv.lock` with the new name and `uv run pytest` passes
   the full suite (imports resolve, entry points register).
3. `uv run generate --help` and `uv run gen-ui` start under the new package; a
   built wheel is named `common_file_generator-0.1.0-*.whl` and ships the web
   templates/static artifacts.
4. `docker compose build` succeeds with image `common-file-generator:local`; the
   UI `<title>`/`<h1>` read "Common File Generator".
5. Secret, security, and anti-hallucination reviews are clean.

<!--
Status lifecycle: Proposed -> Accepted -> Done (or Superseded by ADR-XXX).
-->
