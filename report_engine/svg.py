"""Deterministic SVG chart generation without external dependencies."""

from __future__ import annotations

from html import escape
from typing import Iterable, Mapping, Sequence


def bar_chart_svg(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    title: str,
    y_label: str,
    width: int = 900,
    height: int = 480,
) -> str:
    if len(labels) != len(values):
        raise ValueError("labels and values must have equal length.")

    margin_left = 80
    margin_right = 30
    margin_top = 60
    margin_bottom = 100
    chart_width = width - margin_left - margin_right
    chart_height = height - margin_top - margin_bottom
    maximum = max(values, default=1.0)
    if maximum <= 0:
        maximum = 1.0

    count = max(1, len(values))
    slot = chart_width / count
    bar_width = slot * 0.68

    elements = [
        _svg_header(width, height),
        f'<text x="{width/2}" y="30" text-anchor="middle" '
        f'font-size="22" font-weight="bold">{escape(title)}</text>',
        f'<line x1="{margin_left}" y1="{margin_top}" '
        f'x2="{margin_left}" y2="{margin_top + chart_height}" '
        f'stroke="black"/>',
        f'<line x1="{margin_left}" y1="{margin_top + chart_height}" '
        f'x2="{margin_left + chart_width}" y2="{margin_top + chart_height}" '
        f'stroke="black"/>',
        f'<text transform="translate(20,{margin_top + chart_height/2}) rotate(-90)" '
        f'text-anchor="middle" font-size="14">{escape(y_label)}</text>',
    ]

    for index, (label, value) in enumerate(zip(labels, values)):
        x = margin_left + index * slot + (slot - bar_width) / 2
        bar_height = chart_height * (value / maximum)
        y = margin_top + chart_height - bar_height
        elements.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" '
            f'height="{bar_height:.2f}" fill="#4b79a1"/>'
        )
        elements.append(
            f'<text x="{x + bar_width/2:.2f}" y="{y - 8:.2f}" '
            f'text-anchor="middle" font-size="12">{value:.4g}</text>'
        )
        elements.append(
            f'<text transform="translate({x + bar_width/2:.2f},'
            f'{margin_top + chart_height + 18}) rotate(35)" '
            f'text-anchor="start" font-size="12">{escape(label)}</text>'
        )

    elements.append("</svg>")
    return "\n".join(elements)


def calibration_svg(
    bins: Sequence[Mapping[str, object]],
    *,
    width: int = 700,
    height: int = 560,
) -> str:
    margin = 70
    chart = min(width, height) - 2 * margin
    elements = [
        _svg_header(width, height),
        f'<text x="{width/2}" y="30" text-anchor="middle" '
        f'font-size="22" font-weight="bold">Confidence Calibration</text>',
        f'<line x1="{margin}" y1="{height-margin}" '
        f'x2="{margin+chart}" y2="{height-margin}" stroke="black"/>',
        f'<line x1="{margin}" y1="{height-margin}" '
        f'x2="{margin}" y2="{height-margin-chart}" stroke="black"/>',
        f'<line x1="{margin}" y1="{height-margin}" '
        f'x2="{margin+chart}" y2="{height-margin-chart}" '
        f'stroke="#777" stroke-dasharray="6,6"/>',
        f'<text x="{margin+chart/2}" y="{height-18}" '
        f'text-anchor="middle">Mean confidence</text>',
        f'<text transform="translate(20,{height-margin-chart/2}) rotate(-90)" '
        f'text-anchor="middle">Observed accuracy</text>',
    ]

    points = []
    for item in bins:
        confidence = _number(item.get("mean_confidence"))
        accuracy = _number(item.get("accuracy"))
        count = int(item.get("count", 0) or 0)
        if confidence is None or accuracy is None or count <= 0:
            continue
        x = margin + confidence * chart
        y = height - margin - accuracy * chart
        radius = max(4, min(14, 3 + count ** 0.5))
        elements.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" '
            f'fill="#d95f02" opacity="0.8"/>'
        )
        points.append((x, y))

    if len(points) > 1:
        path = " ".join(
            ("M" if index == 0 else "L") + f" {x:.2f} {y:.2f}"
            for index, (x, y) in enumerate(points)
        )
        elements.append(
            f'<path d="{path}" fill="none" stroke="#d95f02" stroke-width="2"/>'
        )

    elements.append("</svg>")
    return "\n".join(elements)


def _svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    )


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None
