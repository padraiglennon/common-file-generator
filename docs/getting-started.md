# Getting started

Common File Generator creates realistic test files - PowerPoint, Word, Excel,
PDF, and Markdown - in two ways:

- **Generate** a file from scratch at a chosen complexity and length. Content is
  lorem-ipsum; the point is the *structure*, not the words.
- **Fill** a ready-made "Golden" template with your own data from a JSON file,
  without redrawing the layout.

There are three ways to drive it: the **command line**, the **web UI**, and a
**JSON API**. This page walks all three end to end.

## Install

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra web   # add the web UI; omit --extra web for CLI-only
```

## 1. Generate from the command line

The quickest first result - a 10-slide deck:

```bash
uv run generate deck --out output/deck.pptx --complexity standard --slides 10
```

Each slide is one designed type, picked at random (seeded) from a pool that grows
with complexity. Pass `--seed N` for reproducible output. The other file types
follow the same shape:

```bash
uv run generate doc   --out output/document.docx --complexity standard --sections 5
uv run generate sheet --out output/workbook.xlsx --complexity standard --sheets 3
uv run generate pdf   --out output/document.pdf  --complexity standard --sections 5
uv run generate md    --out output/document.md   --complexity standard --sections 5
```

See the [README](https://github.com/padraiglennon/common-file-generator#use) for
the full option reference.

## 2. Generate from the web UI

If you'd rather not use the command line:

```bash
make serve            # or: uv run gen-ui
```

Open <http://127.0.0.1:18990>, pick a tab, choose your options, and click
**Generate**. A download link appears when the file is ready. The
[Web UI walkthrough](ui-walkthrough.md) shows every tab.

## 3. Generate from the JSON API

The same generation is available programmatically. With the server running:

```bash
curl -X POST http://127.0.0.1:18990/api/generate/deck \
  -H "Content-Type: application/json" \
  -d '{"complexity": "standard", "slides": 10, "seed": 7}' \
  --output deck.pptx
```

Interactive API reference is served at `/docs` (Swagger) and `/redoc` while the
server runs.

## 4. Fill a Golden template

When you want a *polished* file with your own data, design the file once, mark
where data should go, and let the tool inject values:

1. Prepare a template - see [Preparing a Golden template](golden-file-guide.md).
2. Write the data file - see [The data file (JSON)](config-guide.md).
3. Upload both on the **Use a template** tab of the web UI, or POST them to the
   fill endpoint.

## Where to next

- [Web UI walkthrough](ui-walkthrough.md) - a screenshot tour of every screen.
- [How it works](how-it-works.md) - the modes, the complexity model, and the
  architecture.
