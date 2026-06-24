"""Command-line entry point: a thin wrapper over the core library.

Two modes:

* ``fill`` - inject JSON data into a Golden template (template-driven).
* ``deck`` - generate a complex PowerPoint deck from scratch at a chosen
  complexity level (generate mode; the common "give me an N-slide deck" case).

All real work lives in the core library so a future UI (see ADR-001) can reuse
it unchanged.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ms_office_file_generator.core import (
    DEFAULT_VIDEO_URL,
    Complexity,
    ConfigError,
    generate,
    generate_deck,
    generate_doc,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate",
        description="Produce test MS Office files by injection or generation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fill = sub.add_parser(
        "fill", help="Inject JSON data into a Golden template (.pptx/.docx/.xlsx)."
    )
    fill.add_argument("--template", required=True, type=Path)
    fill.add_argument("--config", required=True, type=Path)
    fill.add_argument("--out", required=True, type=Path)
    fill.add_argument("--report", type=Path, default=None)
    fill.add_argument("-v", "--verbose", action="store_true")
    fill.set_defaults(func=_run_fill)

    deck = sub.add_parser(
        "deck", help="Generate a complex PowerPoint deck from scratch."
    )
    deck.add_argument("--out", required=True, type=Path)
    deck.add_argument(
        "--complexity",
        choices=[level.value for level in Complexity],
        default=Complexity.STANDARD.value,
    )
    deck.add_argument("--slides", type=int, default=10)
    deck.add_argument("--seed", type=int, default=0)
    deck.add_argument(
        "--video-url",
        default=DEFAULT_VIDEO_URL,
        help="YouTube URL used on video slides.",
    )
    deck.add_argument(
        "--theme",
        type=Path,
        default=None,
        help="Designed .pptx whose master/layouts are used as the base.",
    )
    deck.add_argument(
        "--background",
        choices=["none", "theme", "random"],
        default="none",
        help="Slide background: none (white), theme (one tint), random (per slide).",
    )
    deck.add_argument(
        "--background-color",
        default=None,
        help="Explicit background hex (e.g. EAF2F8); overrides --background.",
    )
    deck.add_argument("-v", "--verbose", action="store_true")
    deck.set_defaults(func=_run_deck)

    doc = sub.add_parser("doc", help="Generate a complex Word document from scratch.")
    doc.add_argument("--out", required=True, type=Path)
    doc.add_argument(
        "--complexity",
        choices=[level.value for level in Complexity],
        default=Complexity.STANDARD.value,
    )
    doc.add_argument("--sections", type=int, default=5)
    doc.add_argument("--seed", type=int, default=0)
    doc.add_argument(
        "--blocks-per-section",
        type=int,
        default=None,
        help="Content blocks per section (default scales with complexity).",
    )
    doc.add_argument("-v", "--verbose", action="store_true")
    doc.set_defaults(func=_run_doc)

    return parser


def _run_fill(args: argparse.Namespace) -> int:
    try:
        report = generate(
            template=args.template,
            config=args.config,
            out=args.out,
            report_path=args.report,
        )
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        print(f"Could not generate the file: {exc}", file=sys.stderr)
        return 2

    print(f"Created {args.out}")
    if report.has_problems:
        print(report.render())
        return 1
    print("No issues found.")
    return 0


def _run_deck(args: argparse.Namespace) -> int:
    try:
        out = generate_deck(
            str(args.out),
            complexity=args.complexity,
            slides=args.slides,
            seed=args.seed,
            video_url=args.video_url,
            theme_path=str(args.theme) if args.theme else None,
            background=args.background,
            background_color=args.background_color,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"Could not generate the deck: {exc}", file=sys.stderr)
        return 2
    print(f"Created {out} ({args.slides} slides, {args.complexity} complexity).")
    return 0


def _run_doc(args: argparse.Namespace) -> int:
    try:
        out = generate_doc(
            str(args.out),
            complexity=args.complexity,
            sections=args.sections,
            seed=args.seed,
            blocks_per_section=args.blocks_per_section,
        )
    except ValueError as exc:
        print(f"Could not generate the document: {exc}", file=sys.stderr)
        return 2
    print(f"Created {out} ({args.sections} sections, {args.complexity} complexity).")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
