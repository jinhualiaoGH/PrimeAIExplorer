from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .analyzer import analyze
from .io import (
    commit_pilot_response,
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
        "collected_at", "response_seconds",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})


def write_csv_rows(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


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
    write_csv_rows(output / "prediction_bias.csv", summary["prediction_bias"])
    write_csv_rows(output / "confusion_matrix.csv", summary["confusion_matrix"])
    write_csv_rows(output / "metric_trends.csv", summary["metric_trends"])
    write_csv_rows(output / "calibration_bins.csv", summary["calibration_bins"])
    write_csv_rows(output / "gap_spectrum.csv", summary["gap_spectrum"])
    write_csv_rows(output / "window_observatory.csv", summary["window_observatory"])
    write_csv_rows(output / "confidence_histogram.csv", summary["confidence_histogram"])
    write_csv_rows(output / "confidence_error.csv", summary["confidence_error"])
    write_csv_rows(output / "error_distribution.csv", summary["error_distribution"])
    write_csv_rows(output / "prediction_transitions.csv", summary["prediction_transitions"])
    write_csv_rows(output / "gap_families.csv", summary["gap_families"])
    write_csv_rows(output / "timeline.csv", summary["timeline"])
    write_csv_rows(output / "prediction_popularity.csv", summary["prediction_popularity"])
    write_csv_rows(output / "persistence_runs.csv", summary["persistence_runs"])
    write_csv_rows(output / "confidence_realism.csv", summary["confidence_realism"])
    write_csv_rows(output / "surprise_index.csv", summary["surprise_index"])
    write_csv_rows(output / "model_fingerprint.csv", summary["model_fingerprint"])
    (output / "report.md").write_text(markdown_report(summary, metadata), encoding="utf-8")
    (output / "report.html").write_text(html_report(summary, metadata), encoding="utf-8")

    manifest = {
        "schema_version": "0.6.0",
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

    print("PrimeAIExplorer v0.6.0 analysis complete")
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



def _load_collection_payload(args: argparse.Namespace, pilot: Path) -> tuple[dict, Path | None]:
    """Load one response payload from --response-json or a working JSON file."""
    if args.response_json is not None:
        try:
            value = json.loads(args.response_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"--response-json is invalid JSON: {exc.msg}") from exc
        source_path = None
    else:
        source_path = Path(args.response_file) if args.response_file else pilot / "current_response.json"
        if not source_path.is_file():
            raise FileNotFoundError(
                f"Working response file not found: {source_path}. "
                "Create it or pass --response-json."
            )
        value = json.loads(source_path.read_text(encoding="utf-8-sig"))

    if isinstance(value, dict) and isinstance(value.get("response"), dict):
        value = value["response"]
    if not isinstance(value, dict):
        raise ValueError("Collected response must be a JSON object")
    return value, source_path


def cmd_collect(args: argparse.Namespace) -> int:
    pilot = Path(args.responses)
    dataset = Path(args.dataset)
    payload, working_path = _load_collection_payload(args, pilot)
    case_id, ledger_path, backup_path = commit_pilot_response(
        pilot,
        dataset,
        payload,
        case_id=args.case_id,
        model=args.model,
        collection_mode=args.collection_mode,
        dry_run=args.dry_run,
    )

    action = "validated (dry run)" if args.dry_run else "committed"
    print("PrimeAIExplorer Collection Assistant")
    print("=" * 72)
    print(f"[PASS] Case:     {case_id}")
    print(f"[PASS] Response: {action}")
    print(f"[PASS] Ledger:   {ledger_path}")
    if backup_path is not None:
        print(f"[PASS] Backup:   {backup_path}")

    if working_path is not None and not args.keep_working_file and not args.dry_run:
        working_path.write_text("{}\n", encoding="utf-8", newline="\n")
        print(f"[PASS] Cleared:  {working_path.resolve()}")

    status = inspect_ledger_status(pilot)
    completion = status.completed_entries / status.ledger_entries if status.ledger_entries else 0.0
    print(f"[PASS] Completed: {status.completed_entries}")
    print(f"[PASS] Pending:   {status.pending_entries}")
    print(f"[PASS] Progress:  {completion:.2%}")

    records = load_records(pilot, dataset, prompts=Path(args.prompts) if args.prompts else None)
    completed_ids = {record.case_id for record in records}
    prompt_ids = discover_prompt_case_ids(pilot, Path(args.prompts) if args.prompts else None)
    next_ids = [item for item in prompt_ids if item not in completed_ids]
    print(f"[PASS] Next case: {next_ids[0] if next_ids else 'none — pilot is complete'}")
    if not args.dry_run:
        _refresh_analysis_after_collect(args, pilot, dataset)
    return 0



def _progress_bar(completed: int, total: int, width: int = 30) -> str:
    if total <= 0:
        return "[" + ("-" * width) + "]"
    filled = round(width * completed / total)
    return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"


def _case_window(case_id: str) -> int | None:
    import re
    match = re.search(r"CASE-W(\d+)-", case_id, re.IGNORECASE)
    return int(match.group(1)) if match else None


def cmd_progress(args: argparse.Namespace) -> int:
    source = Path(args.responses)
    dataset = Path(args.dataset)
    prompts = Path(args.prompts) if args.prompts else None
    status = inspect_ledger_status(source)
    records = load_records(source, dataset, prompts=prompts)
    completed_ids = {record.case_id for record in records}
    prompt_ids = discover_prompt_case_ids(source, prompts)
    total = status.ledger_entries
    completed = len(records)
    pending = status.pending_entries

    by_window: dict[int | None, dict[str, int]] = {}
    for case_id in prompt_ids:
        window = _case_window(case_id)
        bucket = by_window.setdefault(window, {"total": 0, "completed": 0})
        bucket["total"] += 1
        if case_id in completed_ids:
            bucket["completed"] += 1

    print("PrimeAIExplorer Collection Progress")
    print("=" * 72)
    print(_progress_bar(completed, total))
    print(f"Completed: {completed} / {total}")
    print(f"Pending:   {pending}")
    print(f"Progress:  {(completed / total if total else 0.0):.2%}")
    print()
    print("By window")
    for window, counts in sorted(by_window.items(), key=lambda item: (-1 if item[0] is None else item[0])):
        print(
            f"  W{window:03d}: {counts['completed']:>2}/{counts['total']:<2} "
            f"{_progress_bar(counts['completed'], counts['total'], width=12)}"
            if window is not None
            else f"  Unknown: {counts['completed']}/{counts['total']}"
        )
    pending_ids = [case_id for case_id in prompt_ids if case_id not in completed_ids]
    print()
    print(f"Next case: {pending_ids[0] if pending_ids else 'none — pilot is complete'}")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    source = Path(args.responses)
    dataset = Path(args.dataset)
    prompts = Path(args.prompts) if args.prompts else None
    records = load_records(source, dataset, prompts=prompts)
    ordered = sorted(records, key=lambda record: record.case_id)
    limit = args.limit if args.limit and args.limit > 0 else len(ordered)
    selected = ordered[-limit:]
    print("PrimeAIExplorer Response History")
    print("=" * 96)
    print(f"{'Case':<18} {'Window':>6} {'Prediction':>10} {'Truth':>7} {'Confidence':>11} {'Correct':>8}")
    print("-" * 96)
    for record in selected:
        print(
            f"{record.case_id:<18} {str(record.window):>6} {record.prediction:>10} "
            f"{record.actual_gap:>7} {record.confidence:>10}% {str(record.correct):>8}"
        )
    print("-" * 96)
    print(f"Shown: {len(selected)} of {len(ordered)} completed responses")
    return 0


def _next_prompt_path(source: Path, prompts: Path | None, completed_ids: set[str]) -> Path | None:
    root = prompts if prompts else (source if source.is_dir() else source.parent)
    paths = sorted(root.rglob("CASE-*.txt"), key=lambda p: p.name)
    prompt_order = discover_prompt_case_ids(source, prompts)
    order = {case_id: index for index, case_id in enumerate(prompt_order)}
    paths.sort(key=lambda p: order.get(p.stem.upper(), 10**9))
    for path in paths:
        if path.stem.upper() not in completed_ids:
            return path
    return None


def cmd_resume(args: argparse.Namespace) -> int:
    source = Path(args.responses)
    dataset = Path(args.dataset)
    prompts = Path(args.prompts) if args.prompts else None
    records = load_records(source, dataset, prompts=prompts)
    status = inspect_ledger_status(source)
    completed_ids = {record.case_id for record in records}
    next_path = _next_prompt_path(source, prompts, completed_ids)
    working_file = source / "current_response.json" if source.is_dir() else source.parent / "current_response.json"

    print("PrimeAIExplorer Resume Collection")
    print("=" * 72)
    print(f"Completed: {len(records)}")
    print(f"Pending:   {status.pending_entries}")
    print(f"Progress:  {(len(records) / status.ledger_entries if status.ledger_entries else 0.0):.2%}")
    if next_path is None:
        print("Next case: none — pilot is complete")
        return 0
    print(f"Next case: {next_path.stem.upper()}")
    print(f"Prompt:    {next_path.resolve()}")
    print(f"Working:   {working_file.resolve()}")
    print()
    print(next_path.read_text(encoding="utf-8-sig"))
    if args.open_editor:
        working_file.parent.mkdir(parents=True, exist_ok=True)
        if not working_file.exists():
            working_file.write_text("{}\n", encoding="utf-8", newline="\n")
        if os.name == "nt":
            os.startfile(str(working_file.resolve()))
            print(f"[PASS] Opened editor: {working_file.resolve()}")
        else:
            raise ValueError("--open-editor is currently supported on Windows only")
    return 0


def _refresh_analysis_after_collect(args: argparse.Namespace, pilot: Path, dataset: Path) -> None:
    if not args.refresh_analysis:
        return
    output = Path(args.analysis_output) if args.analysis_output else pilot.parent / "analysis_v060" / pilot.name
    namespace = argparse.Namespace(
        responses=str(pilot),
        dataset=str(dataset),
        prompts=args.prompts,
        output=str(output),
        model=args.model,
        experiment_id=args.experiment_id,
        pilot_id=args.pilot_id or pilot.name,
        bins=args.bins,
    )
    cmd_analyze(namespace)
    print(f"[PASS] Analysis refreshed: {output.resolve()}")



def _workspace_header(args: argparse.Namespace) -> None:
    source = Path(args.responses)
    dataset = Path(args.dataset)
    prompts = Path(args.prompts) if args.prompts else None
    status = inspect_ledger_status(source)
    records = load_records(source, dataset, prompts=prompts)
    completed_ids = {record.case_id for record in records}
    prompt_ids = discover_prompt_case_ids(source, prompts)
    pending_ids = [case_id for case_id in prompt_ids if case_id not in completed_ids]
    print()
    print("=" * 72)
    print("PrimeAIExplorer v0.6.0 Interactive Workspace")
    print("=" * 72)
    print(f"Experiment: {args.experiment_id}")
    print(f"Pilot:      {args.pilot_id or source.name}")
    print(f"Model:      {args.model}")
    print(f"Completed:  {len(records)} / {status.ledger_entries}")
    print(f"Pending:    {status.pending_entries}")
    print(f"Progress:   {(len(records) / status.ledger_entries if status.ledger_entries else 0.0):.2%}")
    print(f"Next case:  {pending_ids[0] if pending_ids else 'none — pilot is complete'}")
    print()


def _workspace_collect_namespace(args: argparse.Namespace, *, dry_run: bool) -> argparse.Namespace:
    return argparse.Namespace(
        responses=args.responses,
        dataset=args.dataset,
        prompts=args.prompts,
        response_json=None,
        response_file=None,
        case_id=None,
        model=args.model,
        collection_mode=args.collection_mode,
        keep_working_file=False,
        dry_run=dry_run,
        refresh_analysis=(args.auto_refresh and not dry_run),
        analysis_output=args.analysis_output,
        experiment_id=args.experiment_id,
        pilot_id=args.pilot_id,
        bins=args.bins,
    )


def _workspace_refresh_namespace(args: argparse.Namespace) -> argparse.Namespace:
    output = args.analysis_output or str(Path(args.responses).parent / "analysis_v060" / Path(args.responses).name)
    return argparse.Namespace(
        responses=args.responses,
        dataset=args.dataset,
        prompts=args.prompts,
        output=output,
        model=args.model,
        experiment_id=args.experiment_id,
        pilot_id=args.pilot_id or Path(args.responses).name,
        bins=args.bins,
    )


def _workspace_open_report(args: argparse.Namespace) -> None:
    output = Path(args.analysis_output or (Path(args.responses).parent / "analysis_v060" / Path(args.responses).name))
    report = output / "report.html"
    if not report.is_file():
        raise FileNotFoundError(f"Analysis report not found: {report}. Refresh analysis first.")
    if os.name != "nt":
        raise ValueError("Opening the report is currently supported on Windows only")
    os.startfile(str(report.resolve()))
    print(f"[PASS] Opened report: {report.resolve()}")


def _normalize_workspace_selection(value: str) -> str:
    """Normalize forgiving numeric and named workspace commands.

    Accepts values such as ``4``, ``4)``, ``4.``, ``(4)``, ``validate``,
    and mixed-case command names.
    """

    normalized = value.strip().lower()
    # Remove common menu punctuation without disturbing command names.
    normalized = normalized.strip(" \t\r\n()[]{}<>.:;,-=+>|")
    return normalized


def _workspace_input(prompt: str = "Selection (1-9 or command): ") -> str:
    """Read one workspace command with optional arrow-key history.

    ``prompt_toolkit`` is optional.  When unavailable, use the standard
    built-in input function with no loss of functionality.
    """

    try:
        from prompt_toolkit import prompt as toolkit_prompt  # type: ignore
        from prompt_toolkit.history import InMemoryHistory  # type: ignore
    except ImportError:
        return input(prompt)

    history = getattr(_workspace_input, "_history", None)
    if history is None:
        history = InMemoryHistory()
        setattr(_workspace_input, "_history", history)
    return toolkit_prompt(prompt, history=history)


def _workspace_menu() -> None:
    print("1) Show progress")
    print("2) Show next prompt")
    print("3) Open response editor")
    print("4) Validate current response")
    print("5) Commit response")
    print("6) Show response history")
    print("7) Refresh analysis")
    print("8) Open HTML report")
    print("9) Exit")


def _run_workspace_action(choice: str, args: argparse.Namespace) -> bool:
    normalized = _normalize_workspace_selection(choice)
    aliases = {
        "progress": "1", "p": "1",
        "prompt": "2", "next": "2", "n": "2",
        "editor": "3", "edit": "3", "e": "3",
        "validate": "4", "v": "4",
        "commit": "5", "c": "5",
        "history": "6", "h": "6",
        "refresh": "7", "r": "7",
        "report": "8", "o": "8",
        "exit": "9", "quit": "9", "q": "9",
    }
    normalized = aliases.get(normalized, normalized)
    common = argparse.Namespace(responses=args.responses, dataset=args.dataset, prompts=args.prompts)
    if normalized == "1":
        cmd_progress(common)
    elif normalized == "2":
        cmd_next_case(common)
    elif normalized == "3":
        cmd_resume(argparse.Namespace(**vars(common), open_editor=True))
    elif normalized == "4":
        cmd_collect(_workspace_collect_namespace(args, dry_run=True))
    elif normalized == "5":
        cmd_collect(_workspace_collect_namespace(args, dry_run=False))
    elif normalized == "6":
        cmd_history(argparse.Namespace(**vars(common), limit=args.history_limit))
    elif normalized == "7":
        cmd_analyze(_workspace_refresh_namespace(args))
    elif normalized == "8":
        _workspace_open_report(args)
    elif normalized == "9":
        print("[PASS] Workspace closed")
        return False
    else:
        print(f"[WARN] Unknown selection: {choice!r}")
    return True


def cmd_workspace(args: argparse.Namespace) -> int:
    scripted = [item.strip() for item in (args.commands or "").split(",") if item.strip()]
    _workspace_header(args)
    if scripted:
        for command in scripted:
            print(f"\n[WORKSPACE] {command}")
            if not _run_workspace_action(command, args):
                break
        return 0

    while True:
        _workspace_menu()
        try:
            choice = _workspace_input()
            normalized = _normalize_workspace_selection(choice)
            if not _run_workspace_action(choice, args):
                return 0
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            print(f"[ERROR] {exc}")
            normalized = ""

        print()
        # Smart redraw: only refresh the full status header when state or
        # analysis may have changed.  Read-only actions return directly to
        # the compact menu.
        if normalized in {"5", "commit", "c", "7", "refresh", "r"}:
            _workspace_header(args)

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
        description="PrimeAIExplorer v0.6.0 collection workflow and response observatory",
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

    collect_parser = sub.add_parser(
        "collect",
        help="Validate and atomically commit the next response into a partial pilot ledger",
    )
    add_common_response_args(collect_parser)
    source_group = collect_parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--response-json",
        help="Response object supplied directly as JSON text",
    )
    source_group.add_argument(
        "--response-file",
        help="Working response JSON file; defaults to PILOT/current_response.json",
    )
    collect_parser.add_argument("--case-id", help="Specific pending case; defaults to the first pending entry")
    collect_parser.add_argument("--model", default="GPT-5.6 Thinking")
    collect_parser.add_argument("--collection-mode", default="manual_chat")
    collect_parser.add_argument("--keep-working-file", action="store_true")
    collect_parser.add_argument("--dry-run", action="store_true")
    collect_parser.add_argument("--refresh-analysis", action="store_true", help="Rebuild analysis after a successful commit")
    collect_parser.add_argument("--analysis-output", help="Analysis output directory used with --refresh-analysis")
    collect_parser.add_argument("--experiment-id", default="EXP-UNKNOWN")
    collect_parser.add_argument("--pilot-id", help="Pilot identifier for refreshed analysis; defaults to pilot folder name")
    collect_parser.add_argument("--bins", type=int, default=10)
    collect_parser.set_defaults(func=cmd_collect)

    progress_parser = sub.add_parser("progress", help="Show a progress bar and completion by observation window")
    add_common_response_args(progress_parser)
    progress_parser.set_defaults(func=cmd_progress)

    history_parser = sub.add_parser("history", help="Show completed response history")
    add_common_response_args(history_parser)
    history_parser.add_argument("--limit", type=int, default=0, help="Show only the most recent N completed responses")
    history_parser.set_defaults(func=cmd_history)

    resume_parser = sub.add_parser("resume", help="Show the next prompt and working response file")
    add_common_response_args(resume_parser)
    resume_parser.add_argument("--open-editor", action="store_true", help="Open current_response.json in the default Windows editor")
    resume_parser.set_defaults(func=cmd_resume)


    workspace_parser = sub.add_parser(
        "workspace",
        help="Open the interactive research cockpit for collection and analysis",
    )
    add_common_response_args(workspace_parser)
    workspace_parser.add_argument("--model", default="GPT-5.6 Thinking")
    workspace_parser.add_argument("--experiment-id", default="EXP-UNKNOWN")
    workspace_parser.add_argument("--pilot-id", help="Pilot identifier; defaults to pilot folder name")
    workspace_parser.add_argument("--analysis-output", help="Dashboard output directory")
    workspace_parser.add_argument("--collection-mode", default="manual_chat")
    workspace_parser.add_argument("--bins", type=int, default=10)
    workspace_parser.add_argument("--history-limit", type=int, default=10)
    workspace_parser.add_argument(
        "--no-auto-refresh",
        action="store_false",
        dest="auto_refresh",
        help="Do not rebuild analysis automatically after a successful commit",
    )
    workspace_parser.set_defaults(auto_refresh=True)
    workspace_parser.add_argument(
        "--commands",
        help="Comma-separated scripted menu actions for automation or demonstrations",
    )
    workspace_parser.set_defaults(func=cmd_workspace)

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
