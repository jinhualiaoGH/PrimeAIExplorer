from __future__ import annotations
from typing import Any,Mapping,Sequence
from .canonical import content_id
from .models import PipelineSpecification,PipelineStage

def build_specification(*,name:str,description:str,project_root:str,output_root:str,stages:Sequence[PipelineStage],metadata:Mapping[str,Any]|None=None,schema_version='1.0'):
    material={'name':name,'description':description,'schema_version':schema_version,'project_root':project_root,
      'output_root':output_root,'stages':[x.to_dict() for x in stages],'metadata':dict(metadata or {})}
    return PipelineSpecification(pipeline_id=content_id('PIPE',material),name=name,description=description,
      schema_version=schema_version,project_root=project_root,output_root=output_root,stages=tuple(stages),metadata=dict(metadata or {}))
