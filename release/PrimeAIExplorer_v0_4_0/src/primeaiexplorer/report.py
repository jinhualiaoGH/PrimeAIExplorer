from __future__ import annotations
import html, json


def _pct(x): return "n/a" if x is None else f"{100*x:.2f}%"
def _num(x, digits=2): return "n/a" if x is None else f"{x:.{digits}f}"

def _bar_svg(rows, label_key, a_key, b_key=None, width=720, height=260):
    if not rows: return '<p class="muted">No data.</p>'
    maxv=max([r.get(a_key,0) for r in rows]+([r.get(b_key,0) for r in rows] if b_key else [0])+[1])
    left=50; top=20; base=height-35; plotw=width-left-20; ploth=base-top; n=len(rows); group=plotw/max(n,1); bw=max(5,group*(0.32 if b_key else 0.55))
    parts=[f'<svg viewBox="0 0 {width} {height}" class="chart">',f'<line x1="{left}" y1="{base}" x2="{width-15}" y2="{base}" class="axis"/>']
    for i,r in enumerate(rows):
        x=left+i*group+group*0.18; a=r.get(a_key,0); ah=ploth*a/maxv
        parts.append(f'<rect x="{x:.1f}" y="{base-ah:.1f}" width="{bw:.1f}" height="{ah:.1f}" class="barA"><title>{a_key}: {a}</title></rect>')
        if b_key:
            b=r.get(b_key,0); bh=ploth*b/maxv
            parts.append(f'<rect x="{x+bw+2:.1f}" y="{base-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" class="barB"><title>{b_key}: {b}</title></rect>')
        parts.append(f'<text x="{x+bw:.1f}" y="{base+16}" text-anchor="middle" class="tick">{html.escape(str(r[label_key]))}</text>')
    parts.append('</svg>'); return ''.join(parts)

def _line_svg(rows, keys, width=720, height=260):
    if not rows: return '<p class="muted">No data.</p>'
    left=45; top=20; base=height-35; plotw=width-left-20; ploth=base-top; n=len(rows)
    parts=[f'<svg viewBox="0 0 {width} {height}" class="chart">',f'<line x1="{left}" y1="{base}" x2="{width-15}" y2="{base}" class="axis"/>']
    classes=['lineA','lineB','lineC','lineD']
    for k,cls in zip(keys,classes):
        vals=[float(r.get(k,0) or 0) for r in rows]; maxv=max(max(vals),1.0)
        pts=[]
        for i,v in enumerate(vals):
            x=left+(plotw*i/max(n-1,1)); y=base-ploth*v/maxv; pts.append(f'{x:.1f},{y:.1f}')
        parts.append(f'<polyline points="{" ".join(pts)}" class="{cls}" fill="none"><title>{k}</title></polyline>')
    parts.append('</svg>'); return ''.join(parts)

def markdown_report(summary, metadata):
    t=summary['timing']
    lines=["# PrimeAIExplorer v0.4.0 Observatory Report","",f"- Experiment: `{metadata['experiment_id']}`",f"- Pilot: `{metadata['pilot_id']}`",f"- Model: `{metadata['model']}`",f"- Completed: **{summary['record_count']} / {summary['ledger_entry_count']}**",f"- Accuracy: **{_pct(summary['accuracy'])}**",f"- Brier: **{summary['brier_score']:.6f}**",f"- ECE: **{summary['ece']:.6f}**","","## Prediction bias","","| Gap | Predicted | Truth | Bias |","|---:|---:|---:|---:|"]
    lines += [f"| {r['gap']} | {r['predicted']} | {r['truth']} | {r['bias']} |" for r in summary['prediction_bias']]
    lines += ["","## Timing","",f"- Recorded response durations: **{t['duration_count']}**",f"- Mean response seconds: **{_num(t['mean_response_seconds'])}**",f"- Median response seconds: **{_num(t['median_response_seconds'])}**",f"- Timestamped responses: **{t['timestamp_count']}**",f"- Mean collection interval: **{_num(t['mean_collection_interval_seconds'])} seconds**"]
    return '\n'.join(lines)+'\n'

def html_report(summary, metadata):
    bias_rows=''.join(f"<tr><td>{r['gap']}</td><td>{r['predicted']}</td><td>{r['truth']}</td><td class={'pos' if r['bias']>0 else 'neg' if r['bias']<0 else ''}>{r['bias']:+d}</td></tr>" for r in summary['prediction_bias'])
    labels=summary['confusion_labels']; cmap={(r['truth'],r['prediction']):r['count'] for r in summary['confusion_matrix']}
    confusion='<tr><th>Truth \\ Pred</th>'+''.join(f'<th>{x}</th>' for x in labels)+'</tr>'+''.join('<tr><th>'+str(t)+'</th>'+''.join(f'<td class="heat h{min(cmap.get((t,p),0),5)}">{cmap.get((t,p),0)}</td>' for p in labels)+'</tr>' for t in labels)
    cal_rows=''.join(f"<tr><td>{r['bin_low']:.1f}–{r['bin_high']:.1f}</td><td>{r['count']}</td><td>{_pct(r['accuracy'])}</td><td>{_pct(r['average_confidence'])}</td><td>{r['absolute_gap']:.3f}</td></tr>" for r in summary['calibration_bins'])
    timing=summary['timing']
    rec_rows=''.join(f"<tr><td>{html.escape(r['case_id'])}</td><td>{r['window']}</td><td>{r['prediction']}</td><td>{r['actual_gap']}</td><td>{r['confidence']}%</td><td>{'Yes' if r['correct'] else 'No'}</td></tr>" for r in summary['records'])
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>PrimeAIExplorer v0.4.0</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f4f6f8;color:#17202a}}header{{background:#152536;color:white;padding:30px 5%}}main{{max-width:1280px;margin:auto;padding:24px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:14px}}.card,.panel{{background:white;border-radius:12px;padding:18px;box-shadow:0 2px 9px #0001}}.big{{font-size:27px;font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:18px}}table{{border-collapse:collapse;width:100%;background:white;margin:10px 0 25px}}th,td{{padding:8px;border-bottom:1px solid #ddd;text-align:center}}th{{background:#e9eef3}}h2{{margin-top:34px}}.chart{{width:100%;max-height:280px}}.axis{{stroke:#789}}.barA{{fill:#356f9f}}.barB{{fill:#d08a3a}}.tick{{font-size:11px}}.lineA{{stroke:#2563eb;stroke-width:3}}.lineB{{stroke:#dc2626;stroke-width:3}}.lineC{{stroke:#16a34a;stroke-width:3}}.lineD{{stroke:#9333ea;stroke-width:3}}.pos{{color:#b91c1c;font-weight:700}}.neg{{color:#1d4ed8;font-weight:700}}.heat{{background:#f8fafc}}.h1{{background:#dbeafe}}.h2{{background:#bfdbfe}}.h3{{background:#93c5fd}}.h4{{background:#60a5fa}}.h5{{background:#2563eb;color:white}}.muted{{color:#64748b}}
</style></head><body><header><h1>PrimeAIExplorer v0.4.0</h1><p>{html.escape(metadata['experiment_id'])} · {html.escape(metadata['pilot_id'])} · {html.escape(metadata['model'])}</p></header><main>
<div class="cards"><div class="card"><div>Completed</div><div class="big">{summary['record_count']} / {summary['ledger_entry_count']}</div></div><div class="card"><div>Accuracy</div><div class="big">{_pct(summary['accuracy'])}</div></div><div class="card"><div>Brier</div><div class="big">{summary['brier_score']:.4f}</div></div><div class="card"><div>ECE</div><div class="big">{summary['ece']:.4f}</div></div><div class="card"><div>Entropy</div><div class="big">{summary['prediction_entropy_bits']:.3f}</div></div><div class="card"><div>Distinct predictions</div><div class="big">{summary['distinct_predictions']}</div></div></div>
<h2>Distribution observatory</h2><div class="grid"><div class="panel"><h3>Prediction vs truth distribution</h3>{_bar_svg(summary['prediction_bias'],'gap','predicted','truth')}<p class="muted">Blue = predicted; orange = truth.</p></div><div class="panel"><h3>Prediction bias</h3><table><tr><th>Gap</th><th>Predicted</th><th>Truth</th><th>Bias</th></tr>{bias_rows}</table></div></div>
<h2>Confusion matrix</h2><div class="panel"><table>{confusion}</table></div>
<h2>Confidence calibration</h2><div class="grid"><div class="panel">{_bar_svg(summary['calibration_bins'],'bin_high','accuracy','average_confidence')}</div><div class="panel"><table><tr><th>Bin</th><th>N</th><th>Accuracy</th><th>Confidence</th><th>Gap</th></tr>{cal_rows}</table></div></div>
<h2>Metric trends</h2><div class="panel">{_line_svg(summary['metric_trends'],['accuracy','brier','ece','entropy'])}<p class="muted">Cumulative metrics after each collected response.</p></div>
<h2>Timing and throughput</h2><div class="cards"><div class="card"><div>Duration records</div><div class="big">{timing['duration_count']}</div></div><div class="card"><div>Mean response seconds</div><div class="big">{_num(timing['mean_response_seconds'])}</div></div><div class="card"><div>Median response seconds</div><div class="big">{_num(timing['median_response_seconds'])}</div></div><div class="card"><div>Timestamped</div><div class="big">{timing['timestamp_count']}</div></div><div class="card"><div>Mean collection interval</div><div class="big">{_num(timing['mean_collection_interval_seconds'])}</div></div></div>
<h2>Individual responses</h2><table><tr><th>Case</th><th>Window</th><th>Prediction</th><th>Truth</th><th>Confidence</th><th>Correct</th></tr>{rec_rows}</table>
</main></body></html>'''
