"""Scientific report builder."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .loading import ReportInputs
from .models import ReportManifest, ReportSummary
from .rendering import render_html, render_markdown
from .svg import bar_chart_svg, calibration_svg


@dataclass(slots=True)
class ReportBuilder:
    title: str = "PrimeAIExplorer Scientific Experiment Report"

    def build(
        self,
        inputs: ReportInputs,
        output_directory: str | Path,
        *,
        experiment_label: str,
    ) -> ReportManifest:
        destination = Path(output_directory)
        figures = destination / "figures"
        tables = destination / "tables"
        destination.mkdir(parents=True, exist_ok=True)
        figures.mkdir(exist_ok=True)
        tables.mkdir(exist_ok=True)

        summary = _summary_from_analysis(
            self.title,
            experiment_label,
            inputs.analysis,
        )

        core_metrics = [
            ("Accuracy", _value(inputs.analysis, "accuracy")),
            ("MAE", _value(inputs.analysis, "mean_absolute_error")),
            ("RMSE", _value(inputs.analysis, "root_mean_squared_error")),
            ("ECE", _value(inputs.analysis, "expected_calibration_error")),
        ]
        (figures / "core_metrics.svg").write_text(
            bar_chart_svg(
                [item[0] for item in core_metrics],
                [item[1] or 0.0 for item in core_metrics],
                title="Core Experiment Metrics",
                y_label="Metric value",
            ),
            encoding="utf-8",
        )

        calibration = inputs.analysis.get("calibration", [])
        if not isinstance(calibration, list):
            calibration = []
        (figures / "calibration.svg").write_text(
            calibration_svg(calibration),
            encoding="utf-8",
        )

        markdown = render_markdown(
            summary,
            leaderboard=inputs.leaderboard,
            comparisons=inputs.comparisons,
        )
        html = render_html(
            summary,
            leaderboard=inputs.leaderboard,
            comparisons=inputs.comparisons,
        )

        (destination / "report.md").write_text(
            markdown + "\n",
            encoding="utf-8",
        )
        (destination / "report.html").write_text(
            html,
            encoding="utf-8",
        )
        (destination / "summary.json").write_text(
            json.dumps(
                summary.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )

        copied_sources = []
        for filename in (
            "leaderboard.csv",
            "comparisons.csv",
            "calibration.csv",
            "metrics_by_window.csv",
            "metrics_by_actual.csv",
        ):
            source = inputs.source_directory / filename
            if source.exists():
                target = tables / filename
                shutil.copyfile(source, target)
                copied_sources.append(str(source))

        generated_files = tuple(
            sorted(
                str(path.relative_to(destination)).replace("\\", "/")
                for path in destination.rglob("*")
                if path.is_file()
            )
        )
        manifest = ReportManifest(
            schema_version="1.0",
            title=self.title,
            experiment_label=experiment_label,
            generated_files=generated_files,
            source_files=tuple(
                sorted(
                    [
                        str(inputs.source_directory / "analysis.json"),
                        *copied_sources,
                    ]
                )
            ),
        )

        (destination / "report_manifest.json").write_text(
            json.dumps(
                manifest.to_dict(),
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )

        return manifest


def _summary_from_analysis(
    title: str,
    experiment_label: str,
    analysis: Mapping[str, Any],
) -> ReportSummary:
    return ReportSummary(
        title=title,
        experiment_label=experiment_label,
        record_count=int(analysis.get("record_count", 0) or 0),
        evaluable_count=int(analysis.get("evaluable_count", 0) or 0),
        accuracy=_optional_float(analysis.get("accuracy")),
        mean_absolute_error=_optional_float(
            analysis.get("mean_absolute_error")
        ),
        root_mean_squared_error=_optional_float(
            analysis.get("root_mean_squared_error")
        ),
        expected_calibration_error=_optional_float(
            analysis.get("expected_calibration_error")
        ),
        mean_latency_seconds=_optional_float(
            analysis.get("mean_latency_seconds")
        ),
        bootstrap_accuracy_lower=_optional_float(
            analysis.get("bootstrap_accuracy_lower")
        ),
        bootstrap_accuracy_upper=_optional_float(
            analysis.get("bootstrap_accuracy_upper")
        ),
    )


def _value(analysis: Mapping[str, Any], key: str) -> float | None:
    return _optional_float(analysis.get(key))


def _optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None
