"""Markdown and HTML rendering."""

from __future__ import annotations

from html import escape
from typing import Mapping, Sequence

from .models import ReportSummary


def render_markdown(
    summary: ReportSummary,
    *,
    leaderboard: Sequence[Mapping[str, str]],
    comparisons: Sequence[Mapping[str, str]],
) -> str:
    lines = [
        f"# {summary.title}",
        "",
        f"**Experiment:** `{summary.experiment_label}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Records | {summary.record_count} |",
        f"| Evaluable | {summary.evaluable_count} |",
        f"| Accuracy | {_percent(summary.accuracy)} |",
        f"| Mean absolute error | {_number(summary.mean_absolute_error)} |",
        f"| Root mean squared error | {_number(summary.root_mean_squared_error)} |",
        f"| Expected calibration error | {_number(summary.expected_calibration_error)} |",
        f"| Mean latency (seconds) | {_number(summary.mean_latency_seconds)} |",
        f"| Bootstrap accuracy interval | {_interval(summary.bootstrap_accuracy_lower, summary.bootstrap_accuracy_upper)} |",
        "",
        "## Figures",
        "",
        "![Core metrics](figures/core_metrics.svg)",
        "",
        "![Calibration](figures/calibration.svg)",
        "",
    ]

    if leaderboard:
        lines += [
            "## Leaderboard",
            "",
            _markdown_table(leaderboard),
            "",
        ]

    if comparisons:
        lines += [
            "## Paired Comparisons",
            "",
            _markdown_table(comparisons),
            "",
        ]

    lines += [
        "## Reproducibility",
        "",
        "This report was generated deterministically from the Phase C4 analysis bundle.",
        "",
    ]
    return "\n".join(lines)


def render_html(
    summary: ReportSummary,
    *,
    leaderboard: Sequence[Mapping[str, str]],
    comparisons: Sequence[Mapping[str, str]],
) -> str:
    leaderboard_html = _html_table(leaderboard) if leaderboard else "<p>No leaderboard data.</p>"
    comparisons_html = _html_table(comparisons) if comparisons else "<p>No comparison data.</p>"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(summary.title)}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 1100px; margin: 0 auto; padding: 32px; line-height: 1.45; }}
h1, h2 {{ color: #17324d; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; }}
.card {{ border: 1px solid #d6dee6; border-radius: 8px; padding: 16px; background: #f8fafc; }}
.card .value {{ font-size: 1.55rem; font-weight: bold; }}
figure {{ margin: 28px 0; }}
figure img {{ max-width: 100%; border: 1px solid #ddd; }}
table {{ border-collapse: collapse; width: 100%; margin: 14px 0 30px; }}
th, td {{ border: 1px solid #d9e0e6; padding: 8px; text-align: left; }}
th {{ background: #edf3f7; }}
code {{ background: #eef2f5; padding: 2px 5px; }}
.footer {{ margin-top: 40px; color: #59636e; }}
</style>
</head>
<body>
<h1>{escape(summary.title)}</h1>
<p><strong>Experiment:</strong> <code>{escape(summary.experiment_label)}</code></p>

<div class="grid">
{_card("Records", str(summary.record_count))}
{_card("Accuracy", _percent(summary.accuracy))}
{_card("Mean absolute error", _number(summary.mean_absolute_error))}
{_card("RMSE", _number(summary.root_mean_squared_error))}
{_card("Calibration error", _number(summary.expected_calibration_error))}
{_card("Mean latency", _number(summary.mean_latency_seconds))}
</div>

<h2>Figures</h2>
<figure>
<img src="figures/core_metrics.svg" alt="Core metrics">
<figcaption>Core error and performance metrics.</figcaption>
</figure>
<figure>
<img src="figures/calibration.svg" alt="Confidence calibration">
<figcaption>Reported confidence versus observed accuracy.</figcaption>
</figure>

<h2>Leaderboard</h2>
{leaderboard_html}

<h2>Paired Comparisons</h2>
{comparisons_html}

<h2>Reproducibility</h2>
<p>This report was generated deterministically from the Phase C4 analysis bundle.</p>

<p class="footer">PrimeAIExplorer Phase C5 Scientific Report Engine</p>
</body>
</html>
"""


def _card(label: str, value: str) -> str:
    return (
        f'<div class="card"><div>{escape(label)}</div>'
        f'<div class="value">{escape(value)}</div></div>'
    )


def _percent(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.2f}%"


def _number(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.6g}"


def _interval(lower: float | None, upper: float | None) -> str:
    if lower is None or upper is None:
        return "N/A"
    return f"[{lower:.4f}, {upper:.4f}]"


def _markdown_table(rows: Sequence[Mapping[str, str]]) -> str:
    if not rows:
        return "_No data._"

    columns = list(rows[0].keys())
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]

    for row in rows:
        lines.append(
            "| " + " | ".join(str(row.get(column, "")) for column in columns) + " |"
        )

    return "\n".join(lines)


def _html_table(rows: Sequence[Mapping[str, str]]) -> str:
    if not rows:
        return "<p>No data.</p>"

    columns = list(rows[0].keys())
    head = "".join(f"<th>{escape(column)}</th>" for column in columns)
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{escape(str(row.get(column, '')))}</td>"
            for column in columns
        )
        + "</tr>"
        for row in rows
    )

    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
