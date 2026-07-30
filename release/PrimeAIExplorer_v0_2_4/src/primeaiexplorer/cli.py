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
from .io import (
    discover_prompt_case_ids,
    inspect_ledger_status,
    load_dataset,
    load_records,
    sha256_file,
)
from .report import html_report, markdown_report


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "case_id", "window", "prediction", "actual_gap", "confidence", "correct",
        "explanation", "response_path", "collection_sha256", "entry_sha256", "response_sha256",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fields})


def cmd_analyze(args: argparse.Namespace) -> int:
    responses = Path(args.responses)
    dataset = Path(args.dataset)
    prompts = Path(args.prompts) if args.prompts else None
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    dataset_rows = load_dataset(dataset)
    status = inspect_ledger_status(responses)
    records = load_records(responses, dataset, prompts=prompts)
    if not records:
        raise ValueError("No completed responses are available for analysis")
    summary = analyze(
        records,
        bins=args.bins,
        dataset_case_count=len(dataset_rows),
        ledger_entries=status.ledger_entries,
        pending_entries=status.pending_entries,
    )
    metadata = {"experiment_id": args.experiment_id, "pilot_id": args.pilot_id, "model": args.model}

    summary_path = output / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(output / "records.csv", summary["records"])
    (output / "report.md").write_text(markdown_report(summary, metadata), encoding="utf-8")
    (output / "report.html").write_text(html_report(summary, metadata), encoding="utf-8")

    manifest = {
        "schema_version": "0.2.4",
        "primeaiexplorer_version": __version__,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        **metadata,
        "python": sys.version,
        "platform": platform.platform(),
        "responses_source": str(responses.resolve()),
        "prompts_source": str(prompts.resolve()) if prompts else None,
        "dataset_path": str(dataset.resolve()),
        "dataset_sha256": sha256_file(dataset),
        "dataset_case_count": len(dataset_rows),
        "ledger_entry_count": status.ledger_entries,
        "completed_entry_count": len(records),
        "pending_entry_count": status.pending_entries,
        "response_count": len(records),
        "collection_sha256_values": sorted({record.collection_sha256 for record in records}),
        "summary_sha256": sha256_file(summary_path),
        "command": " ".join(sys.argv),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("PrimeAIExplorer v0.2.4 analysis complete")
    print(f"  Dataset:     {dataset.resolve()}")
    print(f"  Ledger:      {status.ledger_entries}")
    print(f"  Completed:   {len(records)}")
    print(f"  Pending:     {status.pending_entries}")
    print(f"  Completion:  {summary['pilot_completion']:.2%}")
    print(f"  Coverage:    {summary['dataset_coverage']:.2%}")
    print(f"  Accuracy:    {summary['accuracy']:.2%}")
    print(f"  Brier:       {summary['brier_score']:.6f}")
    print(f"  ECE:         {summary['ece']:.6f}")
    print(f"  Output:      {output.resolve()}")
    return 0


def cmd_response_check(args: argparse.Namespace) -> int:
    source = Path(args.responses)
    dataset = Path(args.dataset)
    prompts = Path(args.prompts) if args.prompts else None
    status = inspect_ledger_status(source)
    records = load_records(source, dataset, prompts=prompts)
    windows: dict[int | None, int] = {}
    for record in records:
        windows[record.window] = windows.get(record.window, 0) + 1
    print("[PASS] Response ledger is valid")
    print(f"[PASS] Ledger entries: {status.ledger_entries}")
    print(f"[PASS] Completed: {len(records)}")
    print(f"[PASS] Pending: {status.pending_entries}")
    completion = len(records) / status.ledger_entries if status.ledger_entries else 0.0
    print(f"[PASS] Pilot completion: {completion:.2%}")
    print(f"[PASS] Collections: {status.collection_count}")
    print(f"[PASS] Unique entry hashes: {len({record.entry_sha256 for record in records})}")
    for window, count in sorted(windows.items(), key=lambda item: (-1 if item[0] is None else item[0])):
        print(f"[PASS] Window {window}: {count} completed responses")
    return 0


def cmd_pilot_status(args: argparse.Namespace) -> int:
    source = Path(args.responses)
    dataset = Path(args.dataset)
    prompts = Path(args.prompts) if args.prompts else None
    status = inspect_ledger_status(source)
    records = load_records(source, dataset, prompts=prompts)
    completed_ids = {record.case_id for record in records}
    prompt_ids = discover_prompt_case_ids(source, prompts)
    pending_ids = [case_id for case_id in prompt_ids if case_id not in completed_ids]
    completion = len(records) / status.ledger_entries if status.ledger_entries else 0.0
    print("PrimeAIExplorer Pilot Status")
    print("=" * 72)
    print(f"Ledger entries: {status.ledger_entries}")
    print(f"Completed:      {len(records)}")
    print(f"Pending:        {status.pending_entries}")
    print(f"Completion:     {completion:.2%}")
    if pending_ids:
        print(f"Next case:      {pending_ids[0]}")
    else:
        print("Next case:      none — pilot is complete")
    return 0


def cmd_next_case(args: argparse.Namespace) -> int:
    source = Path(args.responses)
    dataset = Path(args.dataset)
    prompts = Path(args.prompts) if args.prompts else None
    records = load_records(source, dataset, prompts=prompts)
    completed_ids = {record.case_id for record in records}
    root = prompts if prompts else (source if source.is_dir() else source.parent)
    prompt_paths = sorted(
        (p for p in root.rglob("CASE-*.txt")),
        key=lambda p: discover_prompt_case_ids(root).index(p.stem) if p.stem in discover_prompt_case_ids(root) else 10**9,
    )
    for path in prompt_paths:
        case_id = path.stem.upper()
        if case_id not in completed_ids:
            print("Next unfinished case")
            print("=" * 72)
            print(f"Case: {case_id}")
            print(f"Prompt: {path.resolve()}")
            print()
            print(path.read_text(encoding="utf-8-sig"))
            return 0
    print("[PASS] Pilot is complete; no unfinished case remains")
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
    print(f"[PASS] Pending: {summary.get('pending_entry_count', 0)}")
    return 0


def add_common_response_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--responses", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument(
        "--prompts",
        help="Optional pilot prompt directory; auto-discovered when omitted",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paiexp",
        description="PrimeAIExplorer v0.2.4 partial-pilot manager and response observatory",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_parser = sub.add_parser("analyze", help="Analyze completed entries in a full or partial pilot ledger")
    add_common_response_args(analyze_parser)
    analyze_parser.add_argument("--output", required=True)
    analyze_parser.add_argument("--model", default="unknown-model")
    analyze_parser.add_argument("--experiment-id", default="EXP-UNKNOWN")
    analyze_parser.add_argument("--pilot-id", default="pilot_unknown")
    analyze_parser.add_argument("--bins", type=int, default=10)
    analyze_parser.set_defaults(func=cmd_analyze)

    response_parser = sub.add_parser("response-check", help="Validate a full or partial response ledger")
    add_common_response_args(response_parser)
    response_parser.set_defaults(func=cmd_response_check)

    status_parser = sub.add_parser("pilot-status", help="Show completed, pending, completion, and next case")
    add_common_response_args(status_parser)
    status_parser.set_defaults(func=cmd_pilot_status)

    next_parser = sub.add_parser("next-case", help="Print the next unfinished prompt")
    add_common_response_args(next_parser)
    next_parser.set_defaults(func=cmd_next_case)

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
