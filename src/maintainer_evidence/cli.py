"""Command-line entry point for maintainer-evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .core import collect_evidence, write_evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maintainer-evidence",
        description="Generate a local, reproducible open-source maintenance evidence pack.",
    )
    parser.add_argument("--repo", default=".", help="Path to a Git checkout (default: current directory).")
    parser.add_argument("--out", default="evidence", help="Output directory (default: ./evidence).")
    parser.add_argument("--since-days", type=int, default=180, help="Lookback window for Git activity.")
    parser.add_argument(
        "--redact-authors",
        action="store_true",
        help="Replace author names in the report with [redacted] before sharing it.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        evidence = collect_evidence(
            Path(args.repo),
            since_days=args.since_days,
            redact_authors=args.redact_authors,
        )
        json_path, markdown_path = write_evidence(evidence, args.out)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {json_path}")
    print(f"wrote {markdown_path}")
    return 0
  
