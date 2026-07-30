"""Self-contained RC3 HTML dashboard generated from observatory results."""
from __future__ import annotations
import html, json
from datetime import datetime, timezone
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from primeaiexplorer.observatories import ObservatoryResult
from primeaiexplorer.visualizations import SvgVisualizationEngine

ACCENTS={"performance":"#78a6ff","behavior":"#4fd1c5","calibration":"#68d391","distribution":"#f6ad55","surprise":"#b794f4"}
KEYS={"performance":["accuracy","brier_score","ece","dataset_coverage"],"behavior":["favorite_prediction","switch_rate","prediction_entropy_bits"],"calibration":["ece","maximum_calibration_error","mean_confidence"],"distribution":["mean_absolute_error","exact_rate","jensen_shannon_divergence_bits"],"surprise":["mean_surprise_index","maximum_surprise_index","novel_prediction_rate"]}
class HtmlDashboardEngine:
    def render(self,results:Mapping[str,ObservatoryResult],output_path:str|Path,*,title:str="PrimeAIExplorer Observatory Dashboard",context:Mapping[str,Any]|None=None)->Path:
        if not results: raise ValueError("results must not be empty")
        context=dict(context or {}); charts=SvgVisualizationEngine().render_all(results)
        nav=[]; overview=[]; sections=[]; figure_no=0
        for name,result in results.items():
            accent=ACCENTS.get(name,"#78a6ff")
            nav.append(f'<a href="#{html.escape(name)}">{html.escape(name.title())}</a>')
            mini=[]
            for key in KEYS.get(name,[])[:3]:
                if key in result.metrics: mini.append(f'<div><span>{html.escape(key.replace("_"," ").title())}</span><strong>{html.escape(self._format(result.metrics[key]))}</strong></div>')
            overview.append(f'<a class="card" style="--accent:{accent}" href="#{name}"><h3>{name.title()}</h3>{"".join(mini)}<small>{len(result.metrics)} metrics · {len(result.tables)} tables</small></a>')
            metrics=''.join(f'<tr><th>{html.escape(str(k))}</th><td>{html.escape(self._format(v))}</td></tr>' for k,v in result.metrics.items())
            table_catalog=''.join(f'<li><code>{html.escape(t)}</code> — {len(rows)} rows</li>' for t,rows in result.tables.items()) or '<li>No tables</li>'
            chart_parts=[]
            allowed=lambda c: c.startswith(name) or (name=='behavior' and c in {'prediction_popularity','run_lengths'}) or (name=='calibration' and c=='reliability_diagram') or (name=='distribution' and c in {'prediction_distribution','truth_distribution','confusion_heatmap'}) or (name=='surprise' and c=='surprise_timeline')
            for cname,svg in charts.items():
                if allowed(cname):
                    figure_no+=1; caption=cname.replace('_',' ').title()
                    chart_parts.append(f'<figure><div class="figure-label">Figure {figure_no}</div>{svg}<figcaption>{html.escape(caption)} — generated from the {name.title()} Observatory.</figcaption></figure>')
            warnings=''.join(f'<li>{html.escape(w)}</li>' for w in result.warnings)
            sections.append(f'<section id="{name}" style="--accent:{accent}"><h2>{name.title()} Observatory</h2><div class="meta">Version {html.escape(result.version)}</div><div class="charts">{"".join(chart_parts)}</div><details><summary>Metrics</summary><table>{metrics}</table></details><details><summary>Tables</summary><ul>{table_catalog}</ul></details>{f"<h3>Warnings</h3><ul>{warnings}</ul>" if warnings else ""}</section>')
        generated=datetime.now(timezone.utc).isoformat()
        context_json=html.escape(json.dumps(context,indent=2,ensure_ascii=False))
        footer=' · '.join(f'{html.escape(str(k))}: {html.escape(str(v))}' for k,v in context.items() if v not in (None,''))
        doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>
:root{{--bg:#0b1020;--panel:#121a2e;--text:#edf2ff;--muted:#aab6d3;--line:#2a3654}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;font:15px/1.5 system-ui,Segoe UI,sans-serif;background:var(--bg);color:var(--text)}}nav{{position:sticky;top:0;z-index:10;background:#080d19eF;border-bottom:1px solid var(--line);padding:10px 24px;display:flex;gap:18px;flex-wrap:wrap}}nav a{{color:#c9d7ff;text-decoration:none;font-weight:700}}header,main,footer{{max-width:1240px;margin:auto;padding:28px}}h1{{margin:0}}.subtitle,.meta,small,figcaption{{color:var(--muted)}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:24px 0}}.card,section{{background:var(--panel);border:1px solid var(--line);border-radius:16px}}.card{{padding:18px;text-decoration:none;color:var(--text);border-top:4px solid var(--accent)}}.card h3{{margin:0 0 12px}}.card div{{display:flex;justify-content:space-between;gap:8px;margin:5px 0}}.card span{{color:var(--muted)}}section{{padding:26px;margin:22px 0;border-top:4px solid var(--accent);scroll-margin-top:60px}}.charts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:18px;margin:18px 0}}figure{{margin:0;background:#0b1223;border:1px solid var(--line);border-radius:12px;padding:12px}}figure svg{{width:100%;height:auto;display:block}}.figure-label{{font-weight:800;color:var(--accent);margin:2px 0 8px}}figcaption{{padding:8px 4px 2px}}details{{margin:12px 0}}summary{{cursor:pointer;font-weight:800;color:var(--accent)}}table{{width:100%;border-collapse:collapse;margin-top:12px}}th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left}}th{{width:45%;color:var(--muted);font-weight:500}}code{{color:var(--accent)}}pre{{overflow:auto;background:#080d19;padding:14px;border-radius:10px}}footer{{color:var(--muted);border-top:1px solid var(--line);font-size:13px}}
</style></head><body><nav><a href="#overview">Overview</a>{''.join(nav)}<a href="#metadata">Metadata</a></nav><header id="overview"><h1>{html.escape(title)}</h1><div class="subtitle">Unified scientific view of performance, behavior, calibration, distribution, and surprise.</div><div class="cards">{''.join(overview)}</div></header><main>{''.join(sections)}<section id="metadata" style="--accent:#78a6ff"><h2>Analysis Metadata</h2><pre>{context_json}</pre></section></main><footer>PrimeAIExplorer v1.0.0 RC3 · Generated {generated}{(' · '+footer) if footer else ''}</footer></body></html>'''
        out=Path(output_path); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(doc,encoding='utf-8'); return out
    @staticmethod
    def _format(value:Any)->str:
        if value is None:return '—'
        if isinstance(value,float):
            if 0<=value<=1:return f'{value:.3f}'
            return f'{value:.6g}'
        return str(value)
