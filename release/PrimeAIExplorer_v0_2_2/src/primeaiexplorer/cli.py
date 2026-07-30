from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .analyzer import analyze
from .io import load_dataset, load_records, sha256_file
from .report import html_report, markdown_report


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = ["case_id", "window", "prediction", "actual_gap", "confidence", "correct", "explanation", "response_path", "response_sha256"]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fields})


def cmd_analyze(args: argparse.Namespace) -> int:
    responses = Path(args.responses)
    dataset = Path(args.dataset)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    dataset_rows = load_dataset(dataset)
    records = load_records(responses, dataset)
    summary = analyze(records, bins=args.bins, dataset_case_count=len(dataset_rows))
    metadata = {"experiment_id": args.experiment_id, "pilot_id": args.pilot_id, "model": args.model}

    summary_path = output / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(output / "records.csv", summary["records"])
    (output / "report.md").write_text(markdown_report(summary, metadata), encoding="utf-8")
    (output / "report.html").write_text(html_report(summary, metadata), encoding="utf-8")

    manifest = {
        "schema_version": "0.2.2",
        "primeaiexplorer_version": __version__,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        **metadata,
        "python": sys.version,
        "platform": platform.platform(),
        "responses_source": str(responses.resolve()),
        "dataset_path": str(dataset.resolve()),
        "dataset_sha256": sha256_file(dataset),
        "dataset_case_count": len(dataset_rows),
        "response_count": len(records),
        "summary_sha256": sha256_file(summary_path),
        "command": " ".join(sys.argv),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("PrimeAIExplorer v0.2.2 analysis complete")
    print(f"  Dataset:   {dataset.resolve()}")
    print(f"  Responses: {len(records)}")
    print(f"  Coverage:  {summary['dataset_coverage']:.2%}")
    print(f"  Accuracy:  {summary['accuracy']:.2%}")
    print(f"  Brier:     {summary['brier_score']:.6f}")
    print(f"  ECE:       {summary['ece']:.6f}")
    print(f"  Output:    {output.resolve()}")
    return 0


def cmd_response_check(args: argparse.Namespace) -> int:
    source = Path(args.responses)
    dataset = Path(args.dataset)
    records = load_records(source, dataset)
    windows: dict[int | None, int] = {}
    for record in records:
        windows[record.window] = windows.get(record.window, 0) + 1
    print("[PASS] Response collection is valid")
    print(f"[PASS] Responses: {len(records)}")
    for window, count in sorted(windows.items(), key=lambda item: (-1 if item[0] is None else item[0])):
        print(f"[PASS] Window {window}: {count} responses")
    return 0


def cmd_dataset_check(args: argparse.Namespace) -> int:
    path = Path(args.dataset)
    dataset = load_dataset(path)
    windows: dict[int | None, int] = {}
    for case in dataset.values():
        windows[case.window_size] = windows.get(case.window_size, 0) + 1
    print("[PASS] Canonical dataset is valid")
    print(f"[PASS] Cases: {len(dataset)}")
    print(f"[PASS] SHA-256: {sha256_file(path)}")
    for window, count in sorted(windows.items(), key=lambda item: (-1 if item[0] is None else item[0])):
        print(f"[PASS] Window {window}: {count} cases")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    folder = Path(args.analysis)
    required = ["records.csv", "summary.json", "manifest.json", "report.md", "report.html"]
    missing = [name for name in required if not (folder / name).is_file()]
    if missing:
        print("[FAIL] Missing: " + ", ".join(missing))
        return 1
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("summary_sha256") != sha256_file(folder / "summary.json"):
        print("[FAIL] summary.json hash mismatch")
        return 1
    dataset_path = Path(manifest.get("dataset_path", ""))
    if dataset_path.is_file() and manifest.get("dataset_sha256") != sha256_file(dataset_path):
        print("[FAIL] source dataset hash mismatch")
        return 1
    print("[PASS] Analysis artifact set is complete and internally consistent")
    print(f"[PASS] Records: {summary['record_count']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paiexp", description="PrimeAIExplorer v0.2.2 native response observatory")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_parser = sub.add_parser("analyze", help="Analyze cases.csv with aggregate responses.json or individual response files")
    analyze_parser.add_argument("--responses", required=True, help="Pilot folder or direct responses.json path")
    analyze_parser.add_argument("--dataset", required=True)
    analyze_parser.add_argument("--output", required=True)
    analyze_parser.add_argument("--model", default="unknown-model")
    analyze_parser.add_argument("--experiment-id", default="EXP-UNKNOWN")
    analyze_parser.add_argument("--pilot-id", default="pilot_unknown")
    analyze_parser.add_argument("--bins", type=int, default=10)
    analyze_parser.set_defaults(func=cmd_analyze)

    response_parser = sub.add_parser("response-check", help="Validate aggregate or individual responses against cases.csv")
    response_parser.add_argument("--responses", required=True)
    response_parser.add_argument("--dataset", required=True)
    response_parser.set_defaults(func=cmd_response_check)

    dataset_parser = sub.add_parser("dataset-check", help="Validate a canonical cases.csv dataset")
    dataset_parser.add_argument("--dataset", required=True)
    dataset_parser.set_defaults(func=cmd_dataset_check)

    verify_parser = sub.add_parser("verify", help="Verify an analysis artifact set")
    verify_parser.add_argument("--analysis", required=True)
    verify_parser.set_defaults(func=cmd_verify)
    return parser


def main() -> None:
    try:
        parser = build_parser()
        args = parser.parse_args()
        raise SystemExit(args.func(args))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
