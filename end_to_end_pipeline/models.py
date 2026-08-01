from __future__ import annotations
from dataclasses import dataclass,field,asdict
from typing import Any,Mapping

_ALLOWED={'pending','running','completed','failed','skipped'}
@dataclass(frozen=True,slots=True)
class PipelineStage:
    name:str
    command:tuple[str,...]=()
    required_inputs:tuple[str,...]=()
    expected_outputs:tuple[str,...]=()
    environment_variables:tuple[str,...]=()
    continue_on_error:bool=False
    metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.name.strip(): raise ValueError('stage name must not be empty')
        if not self.command: raise ValueError(f"stage '{self.name}' requires a command")
    def to_dict(self):
        return {'name':self.name,'command':list(self.command),'required_inputs':list(self.required_inputs),
          'expected_outputs':list(self.expected_outputs),'environment_variables':list(self.environment_variables),
          'continue_on_error':self.continue_on_error,'metadata':dict(self.metadata)}

@dataclass(frozen=True,slots=True)
class PipelineSpecification:
    pipeline_id:str
    name:str
    description:str
    schema_version:str
    project_root:str
    output_root:str
    stages:tuple[PipelineStage,...]
    metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        if not self.pipeline_id.startswith('PIPE-'): raise ValueError("pipeline_id must begin with 'PIPE-'")
        if not self.stages: raise ValueError('pipeline must contain stages')
        names=[x.name for x in self.stages]
        if len(names)!=len(set(names)): raise ValueError('stage names must be unique')
    def to_dict(self):
        return {'pipeline_id':self.pipeline_id,'name':self.name,'description':self.description,
          'schema_version':self.schema_version,'project_root':self.project_root,'output_root':self.output_root,
          'stages':[x.to_dict() for x in self.stages],'metadata':dict(self.metadata)}

@dataclass(frozen=True,slots=True)
class StageState:
    name:str
    status:str='pending'
    attempts:int=0
    started_at_utc:str|None=None
    completed_at_utc:str|None=None
    return_code:int|None=None
    error_message:str|None=None
    output_hashes:Mapping[str,str]=field(default_factory=dict)
    def __post_init__(self):
        if self.status not in _ALLOWED: raise ValueError(f'invalid stage status: {self.status}')
    def to_dict(self): return asdict(self)

@dataclass(frozen=True,slots=True)
class PipelineSummary:
    pipeline_id:str
    status:str
    stage_count:int
    completed_count:int
    failed_count:int
    skipped_count:int
    output_directory:str
    manifest_path:str|None
    def to_dict(self): return asdict(self)
