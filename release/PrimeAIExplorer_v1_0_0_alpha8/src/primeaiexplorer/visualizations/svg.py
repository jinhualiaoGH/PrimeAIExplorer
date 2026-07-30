"""Generate publication-friendly SVG charts from observatory results."""
from __future__ import annotations

import html
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from primeaiexplorer.observatories import ObservatoryResult


class SvgVisualizationEngine:
    """Create deterministic, dependency-free SVG visualizations."""

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
            )
        if behavior:
            charts["prediction_popularity"] = self._table_bars(
                "Prediction Popularity",
                behavior.tables.get("prediction_popularity", []),
                label_keys=("prediction",), value_keys=("count",),
            )
            charts["run_lengths"] = self._table_bars(
                "Persistence Run Lengths",
                behavior.tables.get("persistence_runs", []),
                label_keys=("run_index", "prediction"), value_keys=("length", "run_length"),
            )
        if calibration:
            charts["reliability_diagram"] = self._reliability(
                calibration.tables.get("reliability_bins", [])
            )
        if distribution:
            charts["prediction_distribution"] = self._table_bars(
                "Prediction Distribution",
                distribution.tables.get("prediction_distribution", []),
                label_keys=("prediction", "value"), value_keys=("count", "probability"),
            )
            charts["truth_distribution"] = self._table_bars(
                "Truth Distribution",
                distribution.tables.get("truth_distribution", []),
                label_keys=("truth", "actual_gap", "value"), value_keys=("count", "probability"),
            )
            charts["confusion_heatmap"] = self._confusion(
                distribution.tables.get("confusion_matrix", [])
            )
        if surprise:
            charts["surprise_timeline"] = self._timeline(
                "Surprise Timeline",
                surprise.tables.get("surprise_timeline", []),
                value_keys=("surprise_index", "cumulative_mean_surprise"),
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
    def _svg(title: str, body: str, *, width: int = 760, height: int = 360) -> str:
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
<style>text{{font-family:system-ui,Segoe UI,sans-serif;fill:#dbe7ff}} .muted{{fill:#9fb0d0}} .axis{{stroke:#405174;stroke-width:1}} .bar{{fill:#78a6ff}} .line{{fill:none;stroke:#78a6ff;stroke-width:3}} .ideal{{fill:none;stroke:#8793aa;stroke-width:2;stroke-dasharray:6 6}} .dot{{fill:#d6e4ff}} .cell{{stroke:#0b1020;stroke-width:2}}</style>
<rect width="100%" height="100%" rx="14" fill="#0f172a"/><text x="28" y="36" font-size="22" font-weight="700">{html.escape(title)}</text>{body}</svg>'''

    def _metric_bars(self, title: str, items: Sequence[tuple[str, Any]]) -> str:
        valid = [(label, max(0.0, min(1.0, self._number(value)))) for label, value in items if value is not None]
        body = ''
        for index, (label, value) in enumerate(valid):
            y = 82 + index * 72
            body += f'<text class="muted" x="28" y="{y}">{html.escape(label)}</text><rect x="180" y="{y-18}" width="500" height="24" rx="6" fill="#25324d"/><rect class="bar" x="180" y="{y-18}" width="{500*value:.2f}" height="24" rx="6"/><text x="690" y="{y}">{value:.3f}</text>'
        return self._svg(title, body, height=max(220, 100 + 72 * len(valid)))

    def _table_bars(self, title: str, rows: Sequence[Mapping[str, Any]], *, label_keys: Sequence[str], value_keys: Sequence[str]) -> str:
        values = []
        for i, row in enumerate(rows[:12]):
            label = next((row.get(k) for k in label_keys if row.get(k) is not None), i + 1)
            value = next((row.get(k) for k in value_keys if row.get(k) is not None), 0)
            values.append((str(label), self._number(value)))
        if not values:
            return self._svg(title, '<text class="muted" x="28" y="90">No chart data available</text>')
        maximum = max(v for _, v in values) or 1.0
        plot_w, base_y = 650, 300
        bar_w = max(18, min(52, plot_w / max(1, len(values)) - 10))
        gap = plot_w / len(values)
        body = f'<line class="axis" x1="70" y1="{base_y}" x2="720" y2="{base_y}"/>'
        for i, (label, value) in enumerate(values):
            h = 190 * value / maximum
            x = 75 + i * gap
            body += f'<rect class="bar" x="{x:.1f}" y="{base_y-h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="4"/><text class="muted" x="{x+bar_w/2:.1f}" y="322" font-size="11" text-anchor="middle">{html.escape(label[:9])}</text><text x="{x+bar_w/2:.1f}" y="{base_y-h-7:.1f}" font-size="11" text-anchor="middle">{value:.3g}</text>'
        return self._svg(title, body)

    def _reliability(self, rows: Sequence[Mapping[str, Any]]) -> str:
        body = '<line class="axis" x1="80" y1="300" x2="700" y2="300"/><line class="axis" x1="80" y1="60" x2="80" y2="300"/><path class="ideal" d="M80 300 L700 60"/><text class="muted" x="340" y="338">Mean confidence</text><text class="muted" x="18" y="180" transform="rotate(-90 18 180)">Observed accuracy</text>'
        points = []
        for row in rows:
            conf = self._number(row.get("average_confidence"))
            acc = self._number(row.get("accuracy"))
            if conf > 1.0: conf /= 100.0
            if acc > 1.0: acc /= 100.0
            x, y = 80 + 620 * conf, 300 - 240 * acc
            points.append((x, y))
        if points:
            path = ' '.join(("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}" for i, (x, y) in enumerate(points))
            body += f'<path class="line" d="{path}"/>' + ''.join(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="5"/>' for x, y in points)
        else:
            body += '<text class="muted" x="210" y="180">No calibration-bin data available</text>'
        return self._svg("Reliability Diagram", body)

    def _timeline(self, title: str, rows: Sequence[Mapping[str, Any]], *, value_keys: Sequence[str]) -> str:
        values = []
        for row in rows:
            value = next((row.get(k) for k in value_keys if row.get(k) is not None), None)
            if value is not None: values.append(self._number(value))
        if not values:
            return self._svg(title, '<text class="muted" x="28" y="90">No timeline data available</text>')
        maximum = max(values) or 1.0
        minimum = min(values)
        span = maximum - minimum or 1.0
        pts = []
        for i, value in enumerate(values):
            x = 80 + (620 * i / max(1, len(values)-1))
            y = 300 - 220 * (value-minimum)/span
            pts.append((x,y))
        path = ' '.join(("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}" for i,(x,y) in enumerate(pts))
        body = '<line class="axis" x1="80" y1="300" x2="700" y2="300"/><line class="axis" x1="80" y1="60" x2="80" y2="300"/>' + f'<path class="line" d="{path}"/>' + ''.join(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="4"/>' for x,y in pts)
        return self._svg(title, body)

    def _confusion(self, rows: Sequence[Mapping[str, Any]]) -> str:
        if not rows:
            return self._svg("Confusion Heatmap", '<text class="muted" x="28" y="90">No confusion data available</text>')
        preds = sorted({str(r.get("prediction")) for r in rows})
        truths = sorted({str(r.get("truth", r.get("actual_gap"))) for r in rows})
        counts = {(str(r.get("prediction")), str(r.get("truth", r.get("actual_gap")))): self._number(r.get("count", 1)) for r in rows}
        maximum = max(counts.values()) or 1
        cell = min(54, 500 / max(1, max(len(preds), len(truths))))
        ox, oy = 150, 80
        body = '<text class="muted" x="330" y="338">Truth</text><text class="muted" x="35" y="190" transform="rotate(-90 35 190)">Prediction</text>'
        for i,p in enumerate(preds):
            body += f'<text class="muted" x="{ox-12}" y="{oy+i*cell+cell*.65:.1f}" text-anchor="end">{html.escape(p)}</text>'
        for j,t in enumerate(truths):
            body += f'<text class="muted" x="{ox+j*cell+cell/2:.1f}" y="{oy-10}" text-anchor="middle">{html.escape(t)}</text>'
        for i,p in enumerate(preds):
            for j,t in enumerate(truths):
                value = counts.get((p,t),0)
                opacity = 0.12 + 0.88 * value/maximum
                body += f'<rect class="cell" x="{ox+j*cell:.1f}" y="{oy+i*cell:.1f}" width="{cell:.1f}" height="{cell:.1f}" fill="#78a6ff" fill-opacity="{opacity:.3f}"/><text x="{ox+j*cell+cell/2:.1f}" y="{oy+i*cell+cell*.64:.1f}" text-anchor="middle">{value:g}</text>'
        return self._svg("Confusion Heatmap", body)
