from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256
class ExecutionStatus(str,Enum): SUCCESS='success'; PARTIAL='partial'; FAILED='failed'
@dataclass(frozen=True)
class ExecutionResult:
    schema_version:str
    session_id:str
    status:ExecutionStatus
    elapsed_seconds:float
    response_count:int=0
    evaluation_count:int=0
    artifacts:tuple[str,...]=()
    warnings:tuple[str,...]=()
    errors:tuple[str,...]=()
    def __post_init__(self):
        if not isinstance(self.status,ExecutionStatus): object.__setattr__(self,'status',ExecutionStatus(self.status))
        if isinstance(self.elapsed_seconds,bool) or float(self.elapsed_seconds)<0: raise ValidationError('elapsed_seconds must be nonnegative')
        object.__setattr__(self,'elapsed_seconds',float(self.elapsed_seconds))
        for n in ('response_count','evaluation_count'):
            v=getattr(self,n)
            if isinstance(v,bool) or not isinstance(v,int) or v<0: raise ValidationError(f'invalid {n}')
        if self.status is ExecutionStatus.SUCCESS and self.errors: raise ValidationError('success cannot contain errors')
        if self.status is ExecutionStatus.FAILED and not self.errors: raise ValidationError('failed requires errors')
    @classmethod
    def success(cls,*,session_id,elapsed_seconds,response_count=0,evaluation_count=0,artifacts=(),warnings=()): return cls('1.0',session_id,ExecutionStatus.SUCCESS,elapsed_seconds,response_count,evaluation_count,tuple(map(str,artifacts)),tuple(warnings),())
    @classmethod
    def failed(cls,*,session_id,elapsed_seconds,errors,warnings=(),artifacts=()): return cls('1.0',session_id,ExecutionStatus.FAILED,elapsed_seconds,0,0,tuple(map(str,artifacts)),tuple(warnings),tuple(errors))
    def to_dict(self)->dict[str,Any]: return {'schema_version':self.schema_version,'session_id':self.session_id,'status':self.status.value,'elapsed_seconds':self.elapsed_seconds,'response_count':self.response_count,'evaluation_count':self.evaluation_count,'artifacts':list(self.artifacts),'warnings':list(self.warnings),'errors':list(self.errors)}
    @property
    def result_sha256(self): return stable_sha256(self.to_dict())
