"""Command line entry point: ``python -m <package>``.

Reads BASIC source from a file (or stdin with ``-``), translates it, and can
write the diagnostics JSON report and a per-target batch summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import SUPPORTED_TARGETS, TranslationError, translate, translate_many


def _read_source(path: str | None) -> str:
    if path in (None, "-"):
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=f"python -m {__package__}",
        description="Translate a QuickBASIC subset to another language.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="BASIC file to read; '-' or omitted reads stdin",
    )
    parser.add_argument(
        "--target",
        default="python",
        choices=sorted(SUPPORTED_TARGETS),
        help="language to translate to (default: python)",
    )
    parser.add_argument(
        "--all-targets",
        action="store_true",
        help="attempt every supported target and print a summary",
    )
    parser.add_argument(
        "--out",
        help="write the generated code here instead of stdout",
    )
    parser.add_argument(
        "--diagnostics",
        help="write a JSON report of the run to this path",
    )
    return parser


def _write_batch_diagnostics(path: str, results) -> None:
    report = {
        "targets": [
            {"target": r.target, "ok": r.ok, "category": r.category, "error": r.error}
            for r in results
        ]
    }
    Path(path).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    source = _read_source(args.source)

    if args.all_targets:
        if args.out:
            print("error: --out does not apply to --all-targets", file=sys.stderr)
            return 2
        results = translate_many(source)
        for result in results:
            if result.ok:
                print(f"{result.target}: ok")
            else:
                print(f"{result.target}: failed ({result.category}) {result.error}")
        if args.diagnostics:
            _write_batch_diagnostics(args.diagnostics, results)
        return 0 if any(r.ok for r in results) else 1

    warnings = []
    try:
        code = translate(
            source,
            target=args.target,
            warnings=warnings,
            diagnostics=args.diagnostics,
        )
    except TranslationError as error:
        print(f"error ({error.category}): {error}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if args.out:
        Path(args.out).write_text(code, encoding="utf-8")
    else:
        sys.stdout.write(code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
