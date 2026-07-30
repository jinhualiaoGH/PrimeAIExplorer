from __future__ import annotations

import argparse, csv, json, platform, sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .analyzer import analyze
from .io import load_records, sha256_file
from .report import html_report, markdown_report


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = ["case_id","window","prediction","actual_gap","confidence","correct","explanation","response_path","response_sha256"]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer=csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for row in rows: writer.writerow({k: row[k] for k in fields})


def cmd_analyze(args: argparse.Namespace) -> int:
    responses, truth, output = Path(args.responses), Path(args.truth), Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    records = load_records(responses, truth)
    summary = analyze(records, bins=args.bins)
    metadata = {"experiment_id":args.experiment_id,"pilot_id":args.pilot_id,"model":args.model}
    summary_path=output/"summary.json"
    summary_path.write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    write_csv(output/"records.csv", summary["records"])
    (output/"report.md").write_text(markdown_report(summary,metadata),encoding="utf-8")
    (output/"report.html").write_text(html_report(summary,metadata),encoding="utf-8")
    manifest={
      "schema_version":"0.2.0","primeaiexplorer_version":__version__,
      "created_utc":datetime.now(timezone.utc).isoformat(), **metadata,
      "python":sys.version,"platform":platform.platform(),"responses_root":str(responses.resolve()),
      "truth_path":str(truth.resolve()),"truth_sha256":sha256_file(truth),"response_count":len(records),
      "summary_sha256":sha256_file(summary_path),"command":" ".join(sys.argv),
    }
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("PrimeAIExplorer v0.2 analysis complete")
    print(f"  Responses: {len(records)}")
    print(f"  Accuracy:  {summary['accuracy']:.2%}")
    print(f"  Brier:     {summary['brier_score']:.6f}")
    print(f"  ECE:       {summary['ece']:.6f}")
    print(f"  Output:    {output.resolve()}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    folder=Path(args.analysis); required=["records.csv","summary.json","manifest.json","report.md","report.html"]
    missing=[x for x in required if not (folder/x).is_file()]
    if missing: print("[FAIL] Missing: "+", ".join(missing)); return 1
    summary=json.loads((folder/"summary.json").read_text(encoding="utf-8"))
    manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    expected=manifest.get("summary_sha256")
    actual=sha256_file(folder/"summary.json")
    if expected != actual: print("[FAIL] summary.json hash mismatch"); return 1
    print("[PASS] Analysis artifact set is complete and internally consistent")
    print(f"[PASS] Records: {summary['record_count']}")
    return 0


def build_parser():
    p=argparse.ArgumentParser(prog="paiexp",description="PrimeAIExplorer v0.2 response observatory")
    p.add_argument("--version",action="version",version=__version__)
    sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("analyze",help="Analyze response JSON files")
    a.add_argument("--responses",required=True); a.add_argument("--truth",required=True); a.add_argument("--output",required=True)
    a.add_argument("--model",default="unknown-model"); a.add_argument("--experiment-id",default="EXP-UNKNOWN"); a.add_argument("--pilot-id",default="pilot_unknown")
    a.add_argument("--bins",type=int,default=10); a.set_defaults(func=cmd_analyze)
    v=sub.add_parser("verify",help="Verify an analysis artifact set"); v.add_argument("--analysis",required=True); v.set_defaults(func=cmd_verify)
    return p

def main():
    try:
        parser = build_parser()
        args = parser.parse_args()
        raise SystemExit(args.func(args))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr); raise SystemExit(2)

if __name__ == "__main__":
    main()
