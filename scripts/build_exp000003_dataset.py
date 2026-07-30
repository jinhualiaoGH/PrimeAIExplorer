from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from sequence_plugins.builtin.prime_value import PrimeValueSequencePlugin
DEFAULT=ROOT/'experiments'/'EXP-000003'/'config'/'experiment.json'
def load(path):
    c=json.loads(path.read_text(encoding='utf-8')); c['_experiment_root']=str(path.resolve().parents[1]); return c
def main():
    p=argparse.ArgumentParser(description='Build or plan EXP-000003 Prime Value dataset.')
    p.add_argument('--config',type=Path,default=DEFAULT); p.add_argument('--count',type=int); p.add_argument('--overwrite',action='store_true'); p.add_argument('--dry-run',action='store_true')
    a=p.parse_args(); c=load(a.config.resolve()); count=a.count or int(c['sequence']['target_count']); c.setdefault('build',{})['overwrite']=a.overwrite
    plugin=PrimeValueSequencePlugin(c); source=Path(c['repository']['prime_root']); destination=Path(c['_experiment_root'])/c['sequence']['dataset_file']
    if a.dry_run:
        plan=plugin.plan_dataset(source,destination,count=count); print(json.dumps(plan,indent=2)); return 0 if plan['source_sufficient'] else 1
    print(f'Building {count:,} canonical prime values...'); metadata=plugin.build_dataset(source,destination,count=count,options=c)
    print(json.dumps(metadata.to_dict(),indent=2)); print('[PASS] Dataset built atomically.'); return 0
if __name__=='__main__': raise SystemExit(main())
