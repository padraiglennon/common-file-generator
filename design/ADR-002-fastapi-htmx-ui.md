# ADR-002: FastAPI + HTMX UI for the Office file generator

- **Status:** Done
- **Date:** 2026-06-24
- **Tracking issue:** #2
- **Builds on:** ADR-001
- **Deciders:** Padraig Lennon

## Context

The generator built in ADR-001 is CLI-only (`generate deck` and `generate fill`).
A user who is not comfortable on the command line still has to open a terminal,
remember flag names, and hand-edit JSON. A simple local web UI removes that
friction: pick a mode, fill in a form of all available options, click generate,
download the file.

ADR-001 deliberately kept the engine library-first (the CLI is a thin wrapper
over `generate_deck()` / `generate()`) precisely so a second front-end could
reuse the same core. This ADR adds that front-end. Issue #2 tracks it.

## Decision

Add a small **FastAPI + HTMX** web UI as an optional component over the existing
core. The web layer contains no generation logic; it parses requests, calls the
core, and renders results.

### Two modes, mirroring the CLI

- **Deck (generate mode):** a form for `complexity`, `slides`, `seed`,
  `video_url`, `background`, `background_color`, and an optional theme `.pptx`
  upload. Submitting calls `generate_deck(...)`.
- **Fill (inject mode):** upload a Golden template (`.pptx` / `.docx` / `.xlsx`)
  and a JSON config; submitting calls `generate(...)`, runs the validating
  config loader, and shows the plain-English report alongside the download.

### Dynamically determined form

Form fields are derived from the core by introspection, so new options appear in
the UI without editing templates:

- complexity choices from the `Complexity` enum,
- background-mode choices from `BackgroundMode`,
- defaults from `generate_deck`'s signature.

A small explicit field schema (built in `web/forms.py`) maps each introspected
option to a labelled input, so internals are not leaked verbatim and the HTML
stays a function of the core's public surface.

### Server-rendered HTMX

Pages are server-rendered Jinja2. Form submits are HTMX POSTs that swap in a
result partial (download link, and for fill mode the report text). HTMX is
**vendored** as a static JS file under `web/static/` (no CDN dependency, works
offline).

### Delivery via temp file + download link

On submit the server writes the generated file to a per-request temp directory
and returns a partial containing a download link to a `GET /download/{token}`
route. Temp files live under the system temp dir, are keyed by an opaque token,
and are swept on each request once older than a TTL (default one hour). Nothing
is persisted.

### Packaging and launch

Web dependencies (`fastapi`, `uvicorn`, `python-multipart`, `jinja2`) are an
**optional extra**: `uv sync --extra web`. The core CLI stays dependency-light.

A console script `gen-ui` starts uvicorn. It **binds `127.0.0.1:18990` by
default** so the UI is not exposed on the network by accident; `--host` (e.g.
`0.0.0.0`) and `--port` override this.

### Upload safety

Fill-mode uploads are constrained:

- only `.pptx` / `.docx` / `.xlsx` templates and `.json` configs are accepted;
  other types are rejected with a friendly message,
- total upload size is capped, **configurable** via `--max-upload-mb` and the
  `MOFG_MAX_UPLOAD_MB` env var (default 25 MB); uploads are streamed in chunks
  and aborted as soon as the cap is exceeded, so an oversized file is never fully
  buffered or written,
- uploads are written to a temp dir and never persisted,
- JSON is parsed through the existing validating loader, so malformed configs
  produce the same clear errors as the CLI.

### Project layout

```text
src/common_file_generator/web/
  __init__.py
  app.py            # FastAPI app + routes
  forms.py          # introspect core -> labelled form schema
  server.py         # gen-ui console-script entry (uvicorn launch)
  templates/        # Jinja2: index + HTMX result partials
  static/           # vendored htmx.min.js + minimal CSS
```

## Consequences

### Positive

- Non-technical users drive both modes from a browser, no terminal.
- The form tracks the core automatically; adding a complexity level or background
  mode needs no UI edit.
- Optional extra keeps the CLI install light.
- Library-first reuse means zero duplicated generation logic.

### Negative / trade-offs

- A web surface adds inputs to defend (uploads, form values); mitigated by type
  and size limits, temp-only handling, and the validating loader.
- No auth: the UI must stay local (default localhost bind). Exposing it on the
  network (`--host 0.0.0.0`) is unauthenticated and is the user's explicit choice.
- HTMX is vendored, so its version is pinned in-repo and updated manually.

### Follow-ups (future ADRs)

- Authentication and hosted/multi-user deployment.
- Live slide preview (thumbnail render).
- Async/background job queue for very large decks.

## Alternatives considered

- **Static hand-written form.** Rejected: drifts from the core every time an
  option is added; introspection keeps them in lockstep.
- **Stream the file directly as the POST response.** Rejected as the default: no
  room for the in-page report (fill mode) and awkward with HTMX partial swaps.
  The temp-file + download-link approach keeps the report and the file together.
- **FastAPI dependencies in the core install.** Rejected: every CLI user would
  pull the web stack; an optional extra is cleaner.
- **Default bind `0.0.0.0`.** Rejected as the default: unauthenticated network
  exposure by accident. Localhost default, opt in to `0.0.0.0` explicitly.

## Acceptance criteria

1. `uv sync --extra web` then `gen-ui` serves the UI on `127.0.0.1:18990`.
2. The deck form generates a `.pptx` with all options and offers it for download.
3. The fill form accepts a template + JSON, injects, and returns the file plus
   the plain-English report.
4. Form options are introspected from the core: adding a `Complexity` value shows
   up in the UI with no template edit.
5. Uploads are type-checked and size-capped (`--max-upload-mb` / env); oversized
   or wrong-type uploads are rejected gracefully.
6. Route tests (FastAPI `TestClient`) pass; secret, security, and
   anti-hallucination reviews per the ADR template are clean.
