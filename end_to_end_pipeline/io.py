from __future__ import annotations
import json,os,tempfile
from pathlib import Path
from typing import Any,Mapping
from .models import PipelineSpecification,PipelineStage

def load_json(path):
    with Path(path).open('r',encoding='utf-8-sig') as h: value=json.load(h)
    if not isinstance(value,dict): raise ValueError('expected JSON object')
    return value

def write_json_atomic(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n'
    fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as h: h.write(text)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return path

def specification_from_document(d:Mapping[str,Any])->PipelineSpecification:
    stages=tuple(PipelineStage(name=str(s['name']),command=tuple(str(x) for x in s['command']),
      required_inputs=tuple(str(x) for x in s.get('required_inputs',[])),
      expected_outputs=tuple(str(x) for x in s.get('expected_outputs',[])),
      environment_variables=tuple(str(x) for x in s.get('environment_variables',[])),
      continue_on_error=bool(s.get('continue_on_error',False)),metadata=dict(s.get('metadata',{}))) for s in d['stages'])
    return PipelineSpecification(pipeline_id=str(d['pipeline_id']),name=str(d['name']),description=str(d.get('description','')),
      schema_version=str(d.get('schema_version','1.0')),project_root=str(d['project_root']),output_root=str(d['output_root']),
      stages=stages,metadata=dict(d.get('metadata',{})))

def load_specification(path): return specification_from_document(load_json(path))
