from __future__ import annotations
import json, shutil
from datetime import datetime, timezone
from pathlib import Path
from .io import sha256_file

def build_publication(analysis: str|Path, output: str|Path)->Path:
    src=Path(analysis); out=Path(output)
    required=['summary.json','observatories.json','metrics.csv','dashboard.html']
    missing=[x for x in required if not (src/x).is_file()]
    if missing: raise FileNotFoundError('Missing unified analysis artifacts: '+', '.join(missing))
    if out.exists(): shutil.rmtree(out)
    (out/'figures').mkdir(parents=True); (out/'tables').mkdir()
    for p in (src/'figures').glob('*') if (src/'figures').is_dir() else []:
        if p.is_file(): shutil.copy2(p,out/'figures'/p.name)
    for p in (src/'tables').glob('*.csv') if (src/'tables').is_dir() else []: shutil.copy2(p,out/'tables'/p.name)
    for n in required: shutil.copy2(src/n,out/n)
    summary=json.loads((src/'summary.json').read_text(encoding='utf-8'))
    md=['# PrimeAIExplorer Experiment Publication','',f"Generated: {datetime.now(timezone.utc).isoformat()}",'',f"Observatories: {summary.get('observatory_count','—')}",f"Metrics: {summary.get('metric_count','—')}",f"Tables: {summary.get('table_count','—')}",'','## Artifacts','','- `dashboard.html` — interactive report','- `figures/` — SVG figure set','- `tables/` — CSV table set','- `metrics.csv` — normalized metric catalog','']
    (out/'report.md').write_text('\n'.join(md),encoding='utf-8')
    files=[]
    for p in sorted(out.rglob('*')):
        if p.is_file(): files.append({'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha256_file(p)})
    manifest={'schema_version':'1.0','primeaiexplorer_version':'1.0.0rc3','created_utc':datetime.now(timezone.utc).isoformat(),'files':files}
    (out/'publication_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return out
