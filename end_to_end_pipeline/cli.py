from __future__ import annotations
import argparse,json
from .engine import PipelineEngine
from .io import load_specification,write_json_atomic
from .models import PipelineStage
from .specification import build_specification

def parser():
    p=argparse.ArgumentParser(description='PrimeAIExplorer end-to-end pipeline')
    s=p.add_subparsers(dest='command',required=True)
    r=s.add_parser('run'); r.add_argument('specification'); r.add_argument('--no-resume',action='store_true'); r.add_argument('--force',action='store_true'); r.add_argument('--dry-run',action='store_true')
    v=s.add_parser('validate'); v.add_argument('specification')
    return p

def main():
    a=parser().parse_args(); spec=load_specification(a.specification)
    if a.command=='validate': print(json.dumps({'valid':True,'pipeline_id':spec.pipeline_id,'stage_count':len(spec.stages)},indent=2)); return 0
    summary=PipelineEngine(spec).run(resume=not a.no_resume,force=a.force,dry_run=a.dry_run)
    print(json.dumps(summary.to_dict(),indent=2,sort_keys=True)); return 0 if summary.status=='completed' else 1
if __name__=='__main__': raise SystemExit(main())
