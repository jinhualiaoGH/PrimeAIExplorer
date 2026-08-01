from __future__ import annotations
import os,platform,shutil,sqlite3,subprocess,sys
from pathlib import Path

def collect_diagnostics(project_root):
    root=Path(project_root).resolve(); checks=[]
    checks.append({'name':'project_root_exists','success':root.is_dir(),'detail':str(root)})
    checks.append({'name':'project_root_writable','success':os.access(root,os.W_OK),'detail':str(root)})
    checks.append({'name':'python','success':True,'detail':sys.version})
    checks.append({'name':'platform','success':True,'detail':platform.platform()})
    strict_modules=(root/'.git').exists() or (root/'dataset_registry').exists()
    for module in ('dataset_registry','benchmark_campaign','distributed_workers','experiment_catalog','metrics_engine','report_engine'):
        exists=(root/module).is_dir()
        checks.append({'name':f'module_{module}','success':exists if strict_modules else True,'detail':str(root/module) if exists else 'not required for generic pipeline root'})
    for db in root.rglob('*.sqlite3'):
        try:
            with sqlite3.connect(db) as c: result=c.execute('PRAGMA integrity_check').fetchone()[0]
            checks.append({'name':f'sqlite:{db.relative_to(root)}','success':result=='ok','detail':result})
        except sqlite3.Error as e: checks.append({'name':f'sqlite:{db.relative_to(root)}','success':False,'detail':str(e)})
    git=shutil.which('git')
    if git and (root/'.git').exists():
        p=subprocess.run([git,'status','--porcelain'],cwd=root,text=True,capture_output=True)
        checks.append({'name':'git_status','success':p.returncode==0,'detail':p.stdout.strip()})
    return {'success':all(x['success'] for x in checks),'checks':checks}
