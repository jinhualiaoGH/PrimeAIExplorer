from __future__ import annotations

import html


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100*x:.2f}%"


def markdown_report(summary: dict, metadata: dict) -> str:
    lines = [
        "# PrimeAIExplorer v0.2.5 Analysis Report", "",
        f"- Experiment: `{metadata['experiment_id']}`",
        f"- Pilot: `{metadata['pilot_id']}`",
        f"- Model: `{metadata['model']}`",
        f"- Ledger entries: **{summary.get('ledger_entry_count', summary['record_count'])}**",
        f"- Completed: **{summary['record_count']}**",
        f"- Pending: **{summary.get('pending_entry_count', 0)}**",
        f"- Pilot completion: **{_pct(summary.get('pilot_completion'))}**",
        f"- Dataset cases: **{summary['dataset_case_count']}**",
        f"- Dataset coverage: **{_pct(summary['dataset_coverage'])}**", "",
        "## Core metrics", "",
        "| Metric | Value |", "|---|---:|",
        f"| Exact accuracy | {_pct(summary['accuracy'])} |",
        f"| Mean confidence | {summary['mean_confidence']:.2f} |",
        f"| Brier score | {summary['brier_score']:.6f} |",
        f"| ECE | {summary['ece']:.6f} |",
        f"| Prediction entropy | {summary['prediction_entropy_bits']:.6f} bits |",
        f"| Distinct predictions | {summary['distinct_predictions']} |", "",
        "## Results by window", "", "| Window | Count | Accuracy | Mean confidence | Brier |", "|---:|---:|---:|---:|---:|"
    ]
    for w, row in summary["by_window"].items():
        lines.append(f"| {w} | {row['count']} | {_pct(row['accuracy'])} | {row['mean_confidence']:.2f} | {row['brier_score']:.6f} |")
    lines += ["", "## Prediction distribution", "", "| Gap | Count |", "|---:|---:|"]
    for row in summary["prediction_distribution"]:
        lines.append(f"| {row['prediction']} | {row['count']} |")
    lines += ["", "## Explanation observatory", "",
              f"Unique explanation ratio: **{_pct(summary['explanations']['unique_explanation_ratio'])}**  ",
              f"Average explanation length: **{summary['explanations']['average_words']:.2f} words**", "",
              "### Reasoning categories", ""]
    categories = summary["explanations"]["reasoning_categories"]
    if categories:
        for name, count in sorted(categories.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- `{name}`: {count}")
    else:
        lines.append("No keyword-based reasoning categories were detected.")
    return "\n".join(lines) + "\n"


def html_report(summary: dict, metadata: dict) -> str:
    dist_rows = "".join(f"<tr><td>{x['prediction']}</td><td>{x['count']}</td></tr>" for x in summary['prediction_distribution'])
    window_rows = "".join(f"<tr><td>{html.escape(w)}</td><td>{r['count']}</td><td>{_pct(r['accuracy'])}</td><td>{r['mean_confidence']:.2f}</td><td>{r['brier_score']:.6f}</td></tr>" for w,r in summary['by_window'].items())
    record_rows = "".join(f"<tr><td>{html.escape(r['case_id'])}</td><td>{r['prediction']}</td><td>{r['actual_gap']}</td><td>{r['confidence']}</td><td>{'Yes' if r['correct'] else 'No'}</td><td>{html.escape(r['explanation'])}</td></tr>" for r in summary['records'])
    category_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>" for k,v in sorted(summary['explanations']['reasoning_categories'].items(), key=lambda item: (-item[1], item[0])))
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>PrimeAIExplorer v0.2.5</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f4f6f8;color:#17202a}}header{{background:#152536;color:white;padding:28px 5%}}main{{max-width:1200px;margin:auto;padding:24px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px}}.card{{background:white;border-radius:10px;padding:18px;box-shadow:0 2px 9px #0001}}.big{{font-size:26px;font-weight:700}}table{{border-collapse:collapse;width:100%;background:white;margin:12px 0 28px}}th,td{{padding:9px;border-bottom:1px solid #ddd;text-align:left}}th{{background:#e9eef3}}h2{{margin-top:32px}}</style></head>
<body><header><h1>PrimeAIExplorer v0.2.5</h1><p>{html.escape(metadata['experiment_id'])} · {html.escape(metadata['pilot_id'])} · {html.escape(metadata['model'])}</p></header><main>
<div class="cards"><div class="card"><div>Ledger entries</div><div class="big">{summary.get('ledger_entry_count', summary['record_count'])}</div></div><div class="card"><div>Completed</div><div class="big">{summary['record_count']}</div></div><div class="card"><div>Pending</div><div class="big">{summary.get('pending_entry_count', 0)}</div></div><div class="card"><div>Pilot completion</div><div class="big">{_pct(summary.get('pilot_completion'))}</div></div><div class="card"><div>Dataset coverage</div><div class="big">{_pct(summary['dataset_coverage'])}</div></div><div class="card"><div>Accuracy</div><div class="big">{_pct(summary['accuracy'])}</div></div><div class="card"><div>Brier</div><div class="big">{summary['brier_score']:.4f}</div></div><div class="card"><div>ECE</div><div class="big">{summary['ece']:.4f}</div></div><div class="card"><div>Entropy</div><div class="big">{summary['prediction_entropy_bits']:.3f}</div></div></div>
<h2>Window comparison</h2><table><tr><th>Window</th><th>N</th><th>Accuracy</th><th>Mean confidence</th><th>Brier</th></tr>{window_rows}</table>
<h2>Prediction distribution</h2><table><tr><th>Gap</th><th>Count</th></tr>{dist_rows}</table>
<h2>Reasoning categories</h2><table><tr><th>Category</th><th>Mentions</th></tr>{category_rows}</table>
<h2>Individual responses</h2><table><tr><th>Case</th><th>Prediction</th><th>Actual</th><th>Confidence</th><th>Correct</th><th>Explanation</th></tr>{record_rows}</table>
</main></body></html>'''
