# ms-office-file-generator

Python tool for producing test MS Office sample files (PowerPoint, Word, Excel)
for testing purposes.

It works in two modes:

- **Generate** a complex deck from scratch at a chosen complexity level and slide
  count - the common "give me an N-slide deck" case. Content is lorem-ipsum.
- **Fill** a polished "Golden" template (template-driven): you design the file
  once, mark where data should go, and the tool injects values from a simple JSON
  data file without ever redrawing the layout.

## Who it's for

- **Anyone (non-technical)** supplies the *data* by editing a JSON file and
  preparing a Golden template - no programming needed.
- **Developers** install and run the tool.

## Install

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Use

### Generate a complex deck

```bash
uv run generate deck \
  --out output/deck.pptx \
  --complexity maximum \
  --slides 70
```

Each slide is one designed type, picked at random (seeded) from a pool that grows
with complexity:

| Level | Slide types in the pool |
| --- | --- |
| `minimal` | bullets |
| `simple` | bullets, chevron list |
| `standard` | + image-and-text, image-and-bullets, chart |
| `complex` | + table, section divider |
| `maximum` | + video |

Slide types include bullet lists, chevron lists, image-and-text, image-and-bullets
(image on a random side + a bullet list, like a typical content slide), charts,
tables, video links, and section dividers.

Because each slide has a single focal element, nothing overlaps or overflows.
Types are weighted, so content slides dominate and sparse section dividers stay
rare.

Options:

- `--seed N` - reproducible output (same seed => identical deck).
- `--video-url URL` - YouTube link used on video slides (default provided). Video
  slides show a poster with a play button that links to the video (python-pptx
  cannot author true inline-YouTube playback).
- `--theme path/to/design.pptx` - use a designed PowerPoint as the base so its
  slide-master backgrounds, colours, and layouts carry through. Without it, an
  in-code theme is applied.
- `--background {none,theme,random}` - slide background: `none` (white, default),
  `theme` (one consistent themed tint on every slide), or `random` (a different
  soft tint per slide). Tints are light so text stays readable.
- `--background-color HEX` - an explicit consistent colour (e.g. `EAF2F8`) that
  overrides `--background`.

### Fill a Golden template

```bash
uv run generate fill \
  --template templates/deck.pptx \
  --config  configs/sample-deck.json \
  --out     output/deck.pptx
```

Supported template types: `.pptx`, `.docx`, `.xlsx` (picked automatically by the
template's extension).

After every `fill` run a plain-English **report** is written next to the output
(e.g. `deck.report.txt`) listing anything that didn't fit so you can fix it.

## Guides

- [How to prepare a Golden template](docs/golden-file-guide.md) - marking text,
  tables, and picture spots in PowerPoint / Word / Excel.
- [The data file (JSON), field by field](docs/config-guide.md).

## Develop

```bash
uv sync
uv run pytest          # tests
uv run ruff check .    # lint
uv run pre-commit install   # enable pre-commit hooks
```

## Design

See [design/ADR-001](design/ADR-001-template-driven-office-file-generator.md) for
the architecture decision record.
