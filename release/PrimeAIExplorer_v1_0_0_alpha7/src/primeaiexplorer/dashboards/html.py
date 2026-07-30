"""Self-contained HTML dashboard generated from unified observatory results."""
from __future__ import annotations

import html
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from primeaiexplorer.observatories import ObservatoryResult


class HtmlDashboardEngine:
    """Render a dependency-free, self-contained observatory dashboard."""

    def render(
        self,
        results: Mapping[str, ObservatoryResult],
        output_path: str | Path,
        *,
        title: str = "PrimeAIExplorer Observatory Dashboard",
        context: Mapping[str, Any] | None = None,
    ) -> Path:
        if not results:
            raise ValueError("results must not be empty")
        cards = []
        sections = []
        for name, result in results.items():
            cards.append(
                f'<a class="card" href="#{html.escape(name)}"><strong>{html.escape(name.title())}</strong>'
                f'<span>{len(result.metrics)} metrics · {len(result.tables)} tables</span></a>'
            )
            metrics = "".join(
                f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(self._format(value))}</td></tr>"
                for key, value in result.metrics.items()
            )
            table_catalog = "".join(
                f"<li><code>{html.escape(table)}</code> — {len(rows)} rows</li>"
                for table, rows in result.tables.items()
            ) or "<li>No tables</li>"
            warnings = "".join(f"<li>{html.escape(item)}</li>" for item in result.warnings)
            warning_block = f"<h3>Warnings</h3><ul>{warnings}</ul>" if warnings else ""
            sections.append(f'''<section id="{html.escape(name)}">
<h2>{html.escape(name.title())} Observatory</h2>
<div class="meta">Version {html.escape(result.version)}</div>
<table><tbody>{metrics}</tbody></table>
<h3>Tables</h3><ul>{table_catalog}</ul>{warning_block}
</section>''')
        context_json = html.escape(json.dumps(dict(context or {}), indent=2, ensure_ascii=False))
        document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--bg:#0b1020;--panel:#121a2e;--text:#edf2ff;--muted:#aab6d3;--line:#2a3654;--accent:#78a6ff}}
*{{box-sizing:border-box}} body{{margin:0;font:15px/1.5 system-ui,Segoe UI,sans-serif;background:var(--bg);color:var(--text)}}
header,main{{max-width:1180px;margin:auto;padding:28px}} h1{{margin:0 0 6px}} .subtitle,.meta{{color:var(--muted)}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:24px 0}}
.card,section{{background:var(--panel);border:1px solid var(--line);border-radius:14px}} .card{{padding:16px;color:var(--text);text-decoration:none;display:flex;flex-direction:column}} .card span{{color:var(--muted);font-size:13px}}
section{{padding:22px;margin:18px 0}} table{{width:100%;border-collapse:collapse;margin-top:14px}} th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left}} th{{width:45%;color:var(--muted);font-weight:500}} code{{color:var(--accent)}} pre{{overflow:auto;background:#080d19;padding:14px;border-radius:10px}}
</style></head><body><header><h1>{html.escape(title)}</h1><div class="subtitle">Unified view of performance, behavior, calibration, distribution, and surprise.</div>
<div class="cards">{''.join(cards)}</div></header><main>{''.join(sections)}<section><h2>Analysis Context</h2><pre>{context_json}</pre></section></main></body></html>'''
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document, encoding="utf-8")
        return output

    @staticmethod
    def _format(value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, float):
            return f"{value:.12g}"
        return str(value)
