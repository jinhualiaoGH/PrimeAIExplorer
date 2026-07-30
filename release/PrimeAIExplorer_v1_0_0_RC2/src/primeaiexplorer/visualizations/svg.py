"""Generate publication-friendly SVG charts from observatory results."""
from __future__ import annotations

import html
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from primeaiexplorer.observatories import ObservatoryResult


class SvgVisualizationEngine:
    """Create deterministic, dependency-free SVG visualizations."""

    ACCENTS = {
        "performance": "#78a6ff",
        "behavior": "#4fd1c5",
        "calibration": "#68d391",
        "distribution": "#f6ad55",
        "surprise": "#b794f4",
    }

    def render_all(
        self,
        results: Mapping[str, ObservatoryResult],
        output_dir: str | Path | None = None,
    ) -> dict[str, str]:
        if not results:
            raise ValueError("results must not be empty")
        charts: dict[str, str] = {}
        performance = results.get("performance")
        behavior = results.get("behavior")
        calibration = results.get("calibration")
        distribution = results.get("distribution")
        surprise = results.get("surprise")

        if performance:
            charts["performance_overview"] = self._metric_bars(
                "Performance Overview",
                [
                    ("Accuracy", performance.metrics.get("accuracy")),
                    ("Coverage", performance.metrics.get("dataset_coverage")),
                    ("Completion", performance.metrics.get("pilot_completion")),
                ],
                accent=self.ACCENTS["performance"],
            )
        if behavior:
            charts["prediction_popularity"] = self._table_bars(
                "Prediction Popularity",
                behavior.tables.get("prediction_popularity", []),
                label_keys=("prediction",), value_keys=("count",),
                accent=self.ACCENTS["behavior"],
                x_label="Prediction", y_label="Count",
            )
            charts["run_lengths"] = self._table_bars(
                "Persistence Run Lengths",
                behavior.tables.get("persistence_runs", []),
                label_keys=("run_index", "prediction"), value_keys=("length", "run_length"),
                accent=self.ACCENTS["behavior"],
                x_label="Run", y_label="Length",
            )
        if calibration:
            charts["reliability_diagram"] = self._reliability(
                calibration.tables.get("reliability_bins", []),
                accent=self.ACCENTS["calibration"],
            )
        if distribution:
            charts["prediction_distribution"] = self._table_bars(
                "Prediction Distribution",
                distribution.tables.get("prediction_distribution", []),
                label_keys=("prediction", "value"), value_keys=("count", "probability"),
                accent=self.ACCENTS["distribution"],
                x_label="Prediction", y_label="Count",
            )
            charts["truth_distribution"] = self._table_bars(
                "Truth Distribution",
                distribution.tables.get("truth_distribution", []),
                label_keys=("truth", "actual_gap", "value"), value_keys=("count", "probability"),
                accent=self.ACCENTS["distribution"],
                x_label="Truth", y_label="Count",
            )
            charts["confusion_heatmap"] = self._confusion(
                distribution.tables.get("confusion_matrix", []),
                accent=self.ACCENTS["distribution"],
            )
        if surprise:
            charts["surprise_timeline"] = self._timeline(
                "Surprise Timeline",
                surprise.tables.get("surprise_timeline", []),
                value_keys=("surprise_index", "cumulative_mean_surprise"),
                accent=self.ACCENTS["surprise"],
                x_label="Case order", y_label="Surprise index",
            )

        if output_dir is not None:
            folder = Path(output_dir)
            folder.mkdir(parents=True, exist_ok=True)
            for name, svg in charts.items():
                (folder / f"{name}.svg").write_text(svg, encoding="utf-8")
            catalog = [{"name": name, "file": f"{name}.svg"} for name in charts]
            (folder / "figures.json").write_text(
                json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        return charts

    @staticmethod
    def _number(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _nice_max(value: float) -> float:
        if value <= 0:
            return 1.0
        exponent = math.floor(math.log10(value))
        fraction = value / (10**exponent)
        nice = 1 if fraction <= 1 else 2 if fraction <= 2 else 5 if fraction <= 5 else 10
        return nice * (10**exponent)

    @staticmethod
    def _svg(
        title: str,
        body: str,
        *,
        width: int = 800,
        height: int = 450,
        accent: str = "#78a6ff",
    ) -> str:
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
<style>text{{font-family:system-ui,Segoe UI,sans-serif;fill:#dbe7ff}} .muted{{fill:#9fb0d0}} .axis{{stroke:#526487;stroke-width:1.2}} .grid{{stroke:#263552;stroke-width:1}} .bar{{fill:{accent}}} .line{{fill:none;stroke:{accent};stroke-width:3}} .ideal{{fill:none;stroke:#9aa8c1;stroke-width:2;stroke-dasharray:7 7}} .dot{{fill:#e2ebff;stroke:{accent};stroke-width:2}} .cell{{stroke:#0b1020;stroke-width:2}}</style>
<rect width="100%" height="100%" rx="14" fill="#0f172a"/><text x="32" y="42" font-size="24" font-weight="700">{html.escape(title)}</text>{body}</svg>'''

    def _metric_bars(self, title: str, items: Sequence[tuple[str, Any]], *, accent: str) -> str:
        valid = [(label, max(0.0, min(1.0, self._number(value)))) for label, value in items if value is not None]
        body = ''
        for index, (label, value) in enumerate(valid):
            y = 108 + index * 82
            body += (
                f'<text class="muted" x="42" y="{y}" font-size="16">{html.escape(label)}</text>'
                f'<rect x="205" y="{y-24}" width="500" height="30" rx="7" fill="#25324d"/>'
                f'<rect class="bar" x="205" y="{y-24}" width="{500*value:.2f}" height="30" rx="7"/>'
                f'<text x="720" y="{y}" font-size="16">{value:.3f}</text>'
            )
        return self._svg(title, body, height=max(300, 145 + 82 * len(valid)), accent=accent)

    def _table_bars(
        self,
        title: str,
        rows: Sequence[Mapping[str, Any]],
        *,
        label_keys: Sequence[str],
        value_keys: Sequence[str],
        accent: str,
        x_label: str,
        y_label: str,
    ) -> str:
        values = []
        for i, row in enumerate(rows[:12]):
            label = next((row.get(k) for k in label_keys if row.get(k) is not None), i + 1)
            value = next((row.get(k) for k in value_keys if row.get(k) is not None), 0)
            values.append((str(label), max(0.0, self._number(value))))
        if not values:
            return self._svg(title, '<text class="muted" x="32" y="100">No chart data available</text>', accent=accent)

        maximum = self._nice_max(max(v for _, v in values))
        left, right, top, bottom = 90, 755, 78, 360
        plot_h = bottom - top
        body = ''
        for tick in range(6):
            value = maximum * tick / 5
            y = bottom - plot_h * tick / 5
            body += (
                f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}"/>'
                f'<text class="muted" x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11">{value:.3g}</text>'
            )
        body += (
            f'<line class="axis" x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}"/>'
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{bottom}"/>'
            f'<text class="muted" x="{(left+right)/2:.1f}" y="420" text-anchor="middle">{html.escape(x_label)}</text>'
            f'<text class="muted" x="24" y="{(top+bottom)/2:.1f}" transform="rotate(-90 24 {(top+bottom)/2:.1f})" text-anchor="middle">{html.escape(y_label)}</text>'
        )
        gap = (right - left) / len(values)
        bar_w = max(20, min(58, gap * 0.62))
        for i, (label, value) in enumerate(values):
            h = plot_h * value / maximum if maximum else 0
            x = left + i * gap + (gap - bar_w) / 2
            body += (
                f'<rect class="bar" x="{x:.1f}" y="{bottom-h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="4"/>'
                f'<text class="muted" x="{x+bar_w/2:.1f}" y="382" font-size="11" text-anchor="middle">{html.escape(label[:10])}</text>'
                f'<text x="{x+bar_w/2:.1f}" y="{bottom-h-8:.1f}" font-size="11" text-anchor="middle">{value:.3g}</text>'
            )
        return self._svg(title, body, accent=accent)

    def _reliability(self, rows: Sequence[Mapping[str, Any]], *, accent: str) -> str:
        left, right, top, bottom = 95, 750, 78, 365
        body = ''
        for tick in range(6):
            value = tick / 5
            x = left + (right-left) * value
            y = bottom - (bottom-top) * value
            body += (
                f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}"/>'
                f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}"/>'
                f'<text class="muted" x="{x:.1f}" y="390" text-anchor="middle" font-size="11">{value:.1f}</text>'
                f'<text class="muted" x="{left-12}" y="{y+4:.1f}" text-anchor="end" font-size="11">{value:.1f}</text>'
            )
        body += (
            f'<line class="axis" x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}"/>'
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{bottom}"/>'
            f'<path class="ideal" d="M{left} {bottom} L{right} {top}"/>'
            f'<text class="muted" x="{(left+right)/2:.1f}" y="425" text-anchor="middle">Mean confidence</text>'
            f'<text class="muted" x="28" y="{(top+bottom)/2:.1f}" transform="rotate(-90 28 {(top+bottom)/2:.1f})" text-anchor="middle">Observed accuracy</text>'
        )
        points = []
        for row in rows:
            conf = self._number(row.get("average_confidence"))
            acc = self._number(row.get("accuracy"))
            if conf > 1.0:
                conf /= 100.0
            if acc > 1.0:
                acc /= 100.0
            conf, acc = max(0, min(1, conf)), max(0, min(1, acc))
            points.append((left + (right-left) * conf, bottom - (bottom-top) * acc))
        points.sort(key=lambda point: point[0])
        if points:
            path = ' '.join(("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}" for i, (x, y) in enumerate(points))
            body += f'<path class="line" d="{path}"/>' + ''.join(
                f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="6"/>' for x, y in points
            )
        else:
            body += '<text class="muted" x="235" y="220">No calibration-bin data available</text>'
        return self._svg("Reliability Diagram", body, accent=accent)

    def _timeline(
        self,
        title: str,
        rows: Sequence[Mapping[str, Any]],
        *,
        value_keys: Sequence[str],
        accent: str,
        x_label: str,
        y_label: str,
    ) -> str:
        values = []
        for row in rows:
            value = next((row.get(k) for k in value_keys if row.get(k) is not None), None)
            if value is not None:
                values.append(self._number(value))
        if not values:
            return self._svg(title, '<text class="muted" x="32" y="100">No timeline data available</text>', accent=accent)
        left, right, top, bottom = 95, 750, 78, 365
        minimum = min(0.0, min(values))
        maximum = self._nice_max(max(values))
        span = maximum - minimum or 1.0
        body = ''
        for tick in range(6):
            value = minimum + span * tick / 5
            y = bottom - (bottom-top) * tick / 5
            body += (
                f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}"/>'
                f'<text class="muted" x="{left-12}" y="{y+4:.1f}" text-anchor="end" font-size="11">{value:.2f}</text>'
            )
        body += (
            f'<line class="axis" x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}"/>'
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{bottom}"/>'
            f'<text class="muted" x="{(left+right)/2:.1f}" y="425" text-anchor="middle">{html.escape(x_label)}</text>'
            f'<text class="muted" x="28" y="{(top+bottom)/2:.1f}" transform="rotate(-90 28 {(top+bottom)/2:.1f})" text-anchor="middle">{html.escape(y_label)}</text>'
        )
        pts = []
        for i, value in enumerate(values):
            x = left + ((right-left) * i / max(1, len(values)-1))
            y = bottom - (bottom-top) * (value-minimum)/span
            pts.append((x, y))
            body += f'<text class="muted" x="{x:.1f}" y="390" text-anchor="middle" font-size="10">{i+1}</text>'
        path = ' '.join(("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts))
        body += f'<path class="line" d="{path}"/>' + ''.join(
            f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="5"/>' for x, y in pts
        )
        return self._svg(title, body, accent=accent)

    def _confusion(self, rows: Sequence[Mapping[str, Any]], *, accent: str) -> str:
        if not rows:
            return self._svg("Confusion Heatmap", '<text class="muted" x="32" y="100">No confusion data available</text>', accent=accent)
        preds = sorted({str(r.get("prediction")) for r in rows}, key=lambda value: self._number(value))
        truths = sorted({str(r.get("truth", r.get("actual_gap"))) for r in rows}, key=lambda value: self._number(value))
        counts = {
            (str(r.get("prediction")), str(r.get("truth", r.get("actual_gap")))): self._number(r.get("count", 1))
            for r in rows
        }
        maximum = max(counts.values()) or 1
        cell = min(62, 500 / max(1, max(len(preds), len(truths))))
        ox, oy = 150, 92
        row_totals = {p: sum(counts.get((p, t), 0) for t in truths) for p in preds}
        col_totals = {t: sum(counts.get((p, t), 0) for p in preds) for t in truths}
        total = sum(row_totals.values()) or 1
        body = (
            f'<text class="muted" x="{ox + len(truths)*cell/2:.1f}" y="425" text-anchor="middle">Truth</text>'
            f'<text class="muted" x="35" y="{oy + len(preds)*cell/2:.1f}" transform="rotate(-90 35 {oy + len(preds)*cell/2:.1f})" text-anchor="middle">Prediction</text>'
            f'<text class="muted" x="{ox + len(truths)*cell + 34:.1f}" y="{oy-16}">Σ</text>'
        )
        for i, p in enumerate(preds):
            body += (
                f'<text class="muted" x="{ox-14}" y="{oy+i*cell+cell*.58:.1f}" text-anchor="end">{html.escape(p)}</text>'
                f'<text class="muted" x="{ox+len(truths)*cell+28:.1f}" y="{oy+i*cell+cell*.58:.1f}" text-anchor="middle">{row_totals[p]:g}</text>'
            )
        for j, t in enumerate(truths):
            body += (
                f'<text class="muted" x="{ox+j*cell+cell/2:.1f}" y="{oy-14}" text-anchor="middle">{html.escape(t)}</text>'
                f'<text class="muted" x="{ox+j*cell+cell/2:.1f}" y="{oy+len(preds)*cell+24:.1f}" text-anchor="middle">{col_totals[t]:g}</text>'
            )
        body += f'<text class="muted" x="{ox-14}" y="{oy+len(preds)*cell+24:.1f}" text-anchor="end">Σ</text>'
        body += f'<text class="muted" x="{ox+len(truths)*cell+28:.1f}" y="{oy+len(preds)*cell+24:.1f}" text-anchor="middle">{total:g}</text>'
        for i, p in enumerate(preds):
            for j, t in enumerate(truths):
                value = counts.get((p, t), 0)
                opacity = 0.10 + 0.90 * value / maximum
                percent = 100 * value / total
                body += (
                    f'<rect class="cell" x="{ox+j*cell:.1f}" y="{oy+i*cell:.1f}" width="{cell:.1f}" height="{cell:.1f}" fill="{accent}" fill-opacity="{opacity:.3f}"/>'
                    f'<text x="{ox+j*cell+cell/2:.1f}" y="{oy+i*cell+cell*.45:.1f}" text-anchor="middle" font-size="14">{value:g}</text>'
                    f'<text class="muted" x="{ox+j*cell+cell/2:.1f}" y="{oy+i*cell+cell*.72:.1f}" text-anchor="middle" font-size="9">{percent:.0f}%</text>'
                )
        return self._svg("Confusion Heatmap", body, accent=accent)
