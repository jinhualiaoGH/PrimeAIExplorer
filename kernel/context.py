from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any,Mapping
import json,re,uuid
from kernel.exceptions import ConfigurationError
from kernel.serialization import stable_sha256
ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
def ident(name,v):
    if not isinstance(v,str) or not v.strip() or ID.fullmatch(v.strip()) is None: raise ConfigurationError(f"invalid {name}")
    return v.strip()
def timestamp(v):
    try: p=datetime.fromisoformat(v[:-1]+"+00:00" if v.endswith("Z") else v)
    except Exception as e: raise ConfigurationError("invalid created_utc") from e
    if p.tzinfo is None: raise ConfigurationError("created_utc requires timezone")
    return v
def freeze(m):
    if not isinstance(m,Mapping): raise ConfigurationError("configuration must be mapping")
    copied=json.loads(json.dumps(dict(m),sort_keys=True))
    return MappingProxyType(copied)
@dataclass(frozen=True)
class ExecutionContext:
    schema_version:str
    session_id:str
    benchmark_id:str
    benchmark_version:str
    connector_id:str
    software_version:str
    created_utc:str
    project_root:Path
    working_directory:Path
    output_directory:Path
    git_commit:str|None=None
    configuration:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        for n in ('schema_version','session_id','benchmark_id','benchmark_version','connector_id','software_version'): object.__setattr__(self,n,ident(n,getattr(self,n)))
        object.__setattr__(self,'created_utc',timestamp(self.created_utc))
        for n in ('project_root','working_directory','output_directory'): object.__setattr__(self,n,Path(getattr(self,n)).expanduser().resolve())
        object.__setattr__(self,'configuration',freeze(self.configuration))
    @classmethod
    def create(cls,*,benchmark_id,benchmark_version,connector_id,software_version,project_root,working_directory,output_directory,configuration=None,git_commit=None,session_id=None,created_utc=None):
        return cls('1.0',session_id or 'RUN-'+uuid.uuid4().hex.upper(),benchmark_id,benchmark_version,connector_id,software_version,created_utc or datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z'),project_root,working_directory,output_directory,git_commit,configuration or {})
    def to_dict(self):
        return {'schema_version':self.schema_version,'session_id':self.session_id,'benchmark_id':self.benchmark_id,'benchmark_version':self.benchmark_version,'connector_id':self.connector_id,'software_version':self.software_version,'created_utc':self.created_utc,'project_root':str(self.project_root),'working_directory':str(self.working_directory),'output_directory':str(self.output_directory),'git_commit':self.git_commit,'configuration':dict(self.configuration)}
    @property
    def context_sha256(self): return stable_sha256(self.to_dict())
