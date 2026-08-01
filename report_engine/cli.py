"""CLI for Phase C5 report generation."""

from __future__ import annotations

import argparse
import json

from .builder import ReportBuilder
from .loading import load_report_inputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PrimeAIExplorer scientific report generator."
    )
    parser.add_argument(
        "source",
        help="C4 analysis bundle directory.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Report output directory.",
    )
    parser.add_argument(
        "--experiment-label",
        required=True,
    )
    parser.add_argument(
        "--title",
        default="PrimeAIExplorer Scientific Experiment Report",
    )
    return parser


def main() -> int:
    arguments = build_parser().parse_args()

    inputs = load_report_inputs(arguments.source)
    manifest = ReportBuilder(arguments.title).build(
        inputs,
        arguments.output,
        experiment_label=arguments.experiment_label,
    )

    print(
        json.dumps(
            manifest.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
