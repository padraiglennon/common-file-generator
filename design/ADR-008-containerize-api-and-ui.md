# ADR-008: Containerize the API + UI for CI and local development

- **Status:** Done
- **Date:** 2026-06-27
- **Tracking issue:** #13
- **Builds on:** ADR-002, ADR-007
- **Deciders:** Padraig Lennon

## Context

The generator is reachable three ways: the CLI (`generate ...`, ADR-001), the
HTMX form UI (ADR-002), and the JSON API (ADR-007). The UI and API are the **same
FastAPI app** (`create_app()` mounts the UI routes and includes the API router),
served by the `gen-ui` console script on a single port.

Other projects' CI builds want to use this generator as a black-box service to
produce transient test files, without installing Python 3.14, `uv`, and the
native dependency chain (pillow, reportlab) into their own runners. There is no
packaged, runnable artifact today; a consumer must clone the repo and `uv sync`.

We also want the same container to be buildable and runnable locally with one
command, so local testing exercises exactly what CI consumes rather than a
divergent `uv run` setup.

## Decision

Ship a container image that runs the existing FastAPI app (UI + API) as a single
long-running service, publish it to GitHub Container Registry, and provide local
build/run affordances.

### Image

A multi-stage `Dockerfile`:

- **Build stage** - a `uv`-bearing base; copy the project, run
  `uv sync --extra web` (the `web` extra carries fastapi, uvicorn,
  python-multipart, jinja2) into a virtual environment.
- **Runtime stage** - `python:3.14-slim`; copy only the resolved virtual
  environment and the application source. No build toolchain in the final image.

The container runs the existing `gen-ui` entry point. Host and port come from the
`MOFG_HOST` / `MOFG_PORT` environment variables, which the image sets to
`0.0.0.0` and `18990`:

```text
gen-ui            # reads MOFG_HOST=0.0.0.0, MOFG_PORT=18990 from the image env
```

`gen-ui` gained `MOFG_HOST` / `MOFG_PORT` env defaults (mirroring the existing
`MOFG_MAX_UPLOAD_MB`); explicit `--host` / `--port` flags still win. This lets a
consumer remap the in-container port with `-e MOFG_PORT=...` (plus the matching
`-p`) without rebuilding. Binding `0.0.0.0` is required for the port to be
reachable from the host / CI network (the script still defaults to `127.0.0.1`
when run directly outside the container). The service is **unauthenticated**: it
is a throwaway generator on an isolated CI network, and adding auth is explicitly
out of scope.

A `.dockerignore` excludes `.venv/`, `.git/`, caches, tests, and design docs so
the build context stays small.

### Health endpoint

Add a lightweight `GET /health` route to the FastAPI app returning
`200 {"status": "ok"}`. The `Dockerfile` declares a `HEALTHCHECK` that probes it,
so CI (and `docker compose`) can wait for `healthy` before sending requests
rather than polling the full HTML index page. The route holds no generation
logic and is covered by a unit test alongside the existing web tests.

### Local development

A `docker-compose.yml` at the repo root builds from the local `Dockerfile` and
runs the service on `18990`, mapping the port and wiring the healthcheck. It runs
the **baked-in copy** of the code (no source bind-mount), so a locally built
container is byte-for-byte the artifact CI consumes. Picking up code changes
requires a rebuild; live-reload is intentionally out of scope to avoid divergence
from the published image.

### Makefile

The clarification loop assumed no `Makefile` existed and proposed creating one.
Implementation found a comprehensive self-documenting `Makefile` already in place
(default `make help`; targets for `install`/`install-web`, `serve`, `deck`/`doc`/
`sheet`, `test`, `lint`, `format`, `check`, `build`, `clean`). It already covered
the dev and CLI common actions; only the Docker actions were missing. So rather
than create a new file, this ADR **adds Docker targets to the existing Makefile**:

- `docker-build` - `docker build -t $(IMAGE) .`
- `docker-up` - `docker compose up --build` (UI + API in the foreground)
- `docker-down` - `docker compose down`

These wrap existing commands; they introduce no new behaviour and are not a build
dependency.

### Publishing

A GitHub Actions workflow builds and pushes to
`ghcr.io/padraiglennon/ms-office-file-generator` using the repo's built-in
`GITHUB_TOKEN` (no extra secrets):

- push to `main` -> `:latest`
- push of a `vX.Y.Z` semver tag -> `:vX.Y.Z` (plus `:X.Y`, `:X`)

Consumers pin a tag for reproducible CI. The image is built for **linux/amd64
and linux/arm64** (via QEMU) so it runs on both CI runners and Apple-silicon dev
machines. After build/push, a **Trivy scan** of the image fails the workflow on
fixable HIGH/CRITICAL CVEs (`ignore-unfixed: true`), so a vulnerable base or
dependency surfaces in CI rather than in a consumer's pipeline.

## Consequences

### Positive

- Consuming projects run the generator with `docker run -p 18990:18990
  ghcr.io/padraiglennon/ms-office-file-generator` and hit both surfaces; no Python
  toolchain on their runners.
- Local `docker compose up` (or `make docker-up`) reproduces the CI artifact
  exactly.
- The `Makefile` makes the everyday dev loop discoverable in one place.
- `/health` gives CI a cheap, stable readiness signal.

### Negative / trade-offs

- A new published artifact and CI workflow to maintain (image size, base-image
  CVE updates, tag hygiene).
- No auth means the container must only ever run on a trusted/isolated network.
- Baked-in copy means local code changes need a rebuild to appear in the
  container.

### Follow-ups (future ADRs)

- Token auth or network policy if the container is ever exposed beyond an
  isolated CI network.
- A one-shot CLI container mode (`docker run ... generate ...`) writing to a
  mounted volume, if a non-service consumption pattern is needed.

## Alternatives considered

- **Alpine base image.** Rejected: musl + native wheels (pillow, reportlab) risk
  build/runtime breakage for marginal size savings.
- **One-shot CLI container.** Rejected: loses the UI, which is an explicit
  requirement.
- **Bind-mount source + `uvicorn --reload` for local dev.** Rejected: diverges
  from the published image and needs a dev-only override; fidelity to the CI
  artifact was chosen over hot-reload convenience.
- **Dockerfile-only, no registry.** Rejected: consumers would have to build
  locally, defeating the "pull and run in CI" goal.

## Acceptance criteria

1. `docker compose up` (and `make docker-up`) builds the image and serves `/`
   (200 HTML) and `POST /api/generate/deck` (streams a `.pptx`) on port 18990.
2. `GET /health` returns `200`; the container reports `healthy`.
3. The publish workflow pushes a pullable image to ghcr on push to `main` and on
   a `vX.Y.Z` tag.
4. `make help` lists all targets; `make test` / `lint` / `format` run the
   existing uv-backed commands.
5. Secret, security, and anti-hallucination reviews are clean.

<!--
Status lifecycle: Proposed -> Accepted -> Done (or Superseded by ADR-XXX).
-->
