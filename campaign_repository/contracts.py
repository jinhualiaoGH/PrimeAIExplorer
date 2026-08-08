from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
from kernel.exceptions import ValidationError
from experimental_campaign.identity import canonical_metadata, sha256_json

def _text(n,v):
    if not isinstance(v,str) or not v.strip(): raise ValidationError(f"{n} must be a non-empty string.")
    return v.strip()

class RepositoryObjectKind(str, Enum):
    EXPERIMENT="experiment"; MATERIALIZATION="materialization"; EXECUTION_PLAN="execution_plan"
    EXECUTION_RUN="execution_run"; RESULT_SET="result_set"; PROVENANCE="provenance"
    ANALYSIS_REPORT="analysis_report"; INTEGRATION_RECORD="integration_record"
    OBSERVATORY_PUBLICATION="observatory_publication"; MANIFEST="manifest"; ARTIFACT="artifact"

@dataclass(frozen=True, slots=True)
class ArtifactDescriptor:
    name:str; media_type:str; sha256:str; size_bytes:int; relative_path:str; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        for n in ('name','media_type','sha256','relative_path'): object.__setattr__(self,n,_text(n,getattr(self,n)))
        if isinstance(self.size_bytes,bool) or not isinstance(self.size_bytes,int) or self.size_bytes<0: raise ValidationError('size_bytes must be a non-negative integer.')
        if not isinstance(self.metadata,Mapping): raise ValidationError('metadata must be a mapping.')
        object.__setattr__(self,'metadata',canonical_metadata(self.metadata))
    def to_dict(self): return {'name':self.name,'media_type':self.media_type,'sha256':self.sha256,'size_bytes':self.size_bytes,'relative_path':self.relative_path,'metadata':dict(self.metadata)}

@dataclass(frozen=True, slots=True)
class CampaignRepositoryEntry:
    object_id:str; object_kind:RepositoryObjectKind; object_sha256:str; campaign_id:str; experiment_id:str; artifacts:tuple[ArtifactDescriptor,...]=(); metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        for n in ('object_id','object_sha256','campaign_id','experiment_id'): object.__setattr__(self,n,_text(n,getattr(self,n)))
        if not isinstance(self.object_kind,RepositoryObjectKind):
            try: object.__setattr__(self,'object_kind',RepositoryObjectKind(self.object_kind))
            except Exception as e: raise ValidationError('invalid repository object kind.') from e
        a=tuple(self.artifacts)
        if any(not isinstance(x,ArtifactDescriptor) for x in a): raise ValidationError('artifacts must contain ArtifactDescriptor values.')
        if len({x.name for x in a})!=len(a) or len({x.relative_path for x in a})!=len(a): raise ValidationError('artifact names and paths must be unique.')
        object.__setattr__(self,'artifacts',tuple(sorted(a,key=lambda x:(x.relative_path,x.name))))
        if not isinstance(self.metadata,Mapping): raise ValidationError('metadata must be a mapping.')
        object.__setattr__(self,'metadata',canonical_metadata(self.metadata))
    def identity_payload(self): return {'schema_version':'i1.0','object_id':self.object_id,'object_kind':self.object_kind.value,'object_sha256':self.object_sha256,'campaign_id':self.campaign_id,'experiment_id':self.experiment_id,'artifacts':[x.to_dict() for x in self.artifacts],'metadata':dict(self.metadata)}
    @property
    def entry_sha256(self): return sha256_json(self.identity_payload())
    def to_dict(self):
        d=self.identity_payload(); d['entry_sha256']=self.entry_sha256; return d

@dataclass(frozen=True, slots=True)
class CampaignRepositoryManifest:
    repository_id:str; entries:tuple[CampaignRepositoryEntry,...]; metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,'repository_id',_text('repository_id',self.repository_id)); e=tuple(self.entries)
        if any(not isinstance(x,CampaignRepositoryEntry) for x in e): raise ValidationError('entries must contain CampaignRepositoryEntry values.')
        if len({x.object_id for x in e})!=len(e): raise ValidationError('duplicate object IDs.')
        if len({(x.object_kind.value,x.object_sha256) for x in e})!=len(e): raise ValidationError('duplicate kind/SHA identities.')
        object.__setattr__(self,'entries',tuple(sorted(e,key=lambda x:(x.campaign_id,x.experiment_id,x.object_kind.value,x.object_id))))
        if not isinstance(self.metadata,Mapping): raise ValidationError('metadata must be a mapping.')
        object.__setattr__(self,'metadata',canonical_metadata(self.metadata))
    @property
    def entry_count(self): return len(self.entries)
    def identity_payload(self): return {'schema_version':'i1.0','repository_id':self.repository_id,'entry_sha256s':[x.entry_sha256 for x in self.entries],'metadata':dict(self.metadata)}
    @property
    def manifest_sha256(self): return sha256_json(self.identity_payload())
    def to_dict(self):
        d=self.identity_payload(); d.update({'manifest_sha256':self.manifest_sha256,'entry_count':self.entry_count,'entries':[x.to_dict() for x in self.entries]}); return d
