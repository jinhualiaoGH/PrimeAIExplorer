from __future__ import annotations

import csv
import json

from report_engine import ReportBuilder, load_report_inputs
from report_engine.rendering import render_markdown
from report_engine.svg import bar_chart_svg, calibration_svg


def make_bundle(tmp_path):
    source = tmp_path / "analysis"
    source.mkdir()

    analysis = {
        "record_count": 10,
        "evaluable_count": 10,
        "accuracy": 0.7,
        "mean_absolute_error": 1.2,
        "root_mean_squared_error": 1.8,
        "expected_calibration_error": 0.1,
        "mean_latency_seconds": 0.25,
        "bootstrap_accuracy_lower": 0.5,
        "bootstrap_accuracy_upper": 0.9,
        "calibration": [
            {
                "lower_bound": 0.0,
                "upper_bound": 0.5,
                "count": 4,
                "mean_confidence": 0.3,
                "accuracy": 0.25,
                "calibration_gap": 0.05,
            },
            {
                "lower_bound": 0.5,
                "upper_bound": 1.0,
                "count": 6,
                "mean_confidence": 0.8,
                "accuracy": 0.8333333333,
                "calibration_gap": 0.0333333333,
            },
        ],
    }
    (source / "analysis.json").write_text(
        json.dumps(analysis),
        encoding="utf-8-sig",
    )

    with (source / "leaderboard.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["rank", "label", "accuracy"],
        )
        writer.writeheader()
        writer.writerow({"rank": 1, "label": "model-a", "accuracy": 0.7})

    with (source / "comparisons.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["model_a", "model_b", "wins_a", "wins_b"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "model_a": "model-a",
                "model_b": "model-b",
                "wins_a": 6,
                "wins_b": 4,
            }
        )

    return source


def test_load_report_inputs_accepts_utf8_bom(tmp_path):
    source = make_bundle(tmp_path)
    inputs = load_report_inputs(source)

    assert inputs.analysis["accuracy"] == 0.7
    assert inputs.leaderboard[0]["label"] == "model-a"


def test_bar_chart_svg_is_deterministic():
    first = bar_chart_svg(
        ["A", "B"],
        [0.5, 1.0],
        title="Test",
        y_label="Value",
    )
    second = bar_chart_svg(
        ["A", "B"],
        [0.5, 1.0],
        title="Test",
        y_label="Value",
    )

    assert first == second
    assert first.startswith("<svg")
    assert "<rect" in first


def test_calibration_svg_contains_reference_line():
    svg = calibration_svg(
        [
            {
                "count": 2,
                "mean_confidence": 0.5,
                "accuracy": 0.5,
            }
        ]
    )

    assert "stroke-dasharray" in svg
    assert "<circle" in svg


def test_report_builder_creates_complete_bundle(tmp_path):
    source = make_bundle(tmp_path)
    inputs = load_report_inputs(source)
    output = tmp_path / "report"

    manifest = ReportBuilder("Test Report").build(
        inputs,
        output,
        experiment_label="EXP-TEST",
    )

    assert (output / "report.html").exists()
    assert (output / "report.md").exists()
    assert (output / "summary.json").exists()
    assert (output / "report_manifest.json").exists()
    assert (output / "figures" / "core_metrics.svg").exists()
    assert (output / "figures" / "calibration.svg").exists()
    assert "report.html" in manifest.generated_files


def test_markdown_contains_summary_and_figures(tmp_path):
    source = make_bundle(tmp_path)
    inputs = load_report_inputs(source)
    output = tmp_path / "report"
    ReportBuilder("Test Report").build(
        inputs,
        output,
        experiment_label="EXP-TEST",
    )

    markdown = (output / "report.md").read_text(encoding="utf-8")

    assert "# Test Report" in markdown
    assert "70.00%" in markdown
    assert "figures/core_metrics.svg" in markdown


def test_report_build_is_reproducible(tmp_path):
    source = make_bundle(tmp_path)
    inputs = load_report_inputs(source)

    first = tmp_path / "first"
    second = tmp_path / "second"

    ReportBuilder("Test Report").build(
        inputs,
        first,
        experiment_label="EXP-TEST",
    )
    ReportBuilder("Test Report").build(
        inputs,
        second,
        experiment_label="EXP-TEST",
    )

    for relative in (
        "report.html",
        "report.md",
        "summary.json",
        "figures/core_metrics.svg",
        "figures/calibration.svg",
    ):
        assert (
            first / relative
        ).read_bytes() == (
            second / relative
        ).read_bytes()
