from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, os, tempfile
from pathlib import Path
from typing import Any, Iterable
from kernel.exceptions import ValidationError
from .contracts import ArtifactDescriptor, CampaignRepositoryEntry, CampaignRepositoryManifest, RepositoryObjectKind

def _bytes(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def _sha(b): return hashlib.sha256(b).hexdigest()
def _safe(v):
    if not isinstance(v,str) or not v.strip() or v.strip() in {'.','..'} or any(c in v for c in ('/','\\','\0')): raise ValidationError('invalid repository path component.')
    return v.strip()

@dataclass(frozen=True,slots=True)
class RepositoryWriteResult:
    entry:CampaignRepositoryEntry; object_path:str; entry_path:str
    def to_dict(self): return {'entry':self.entry.to_dict(),'object_path':self.object_path,'entry_path':self.entry_path}

class CampaignRepository:
    def __init__(self,root):
        self.root=Path(root); self.objects_root=self.root/'objects'; self.entries_root=self.root/'entries'; self.manifests_root=self.root/'manifests'
    def initialize(self):
        for p in (self.objects_root,self.entries_root,self.manifests_root): p.mkdir(parents=True,exist_ok=True)
    def store_json(self,*,object_id,object_kind,campaign_id,experiment_id,payload,metadata=None,artifacts=()):
        self.initialize(); object_id=_safe(object_id); campaign_id=_safe(campaign_id); experiment_id=_safe(experiment_id)
        if not isinstance(object_kind,RepositoryObjectKind):
            try: object_kind=RepositoryObjectKind(object_kind)
            except Exception as e: raise ValidationError('invalid repository object kind.') from e
        data=_bytes(payload); digest=_sha(data); op=self.objects_root/object_kind.value/digest[:2]/f'{digest}.json'; self._write_immutable(op,data)
        e=CampaignRepositoryEntry(object_id,object_kind,digest,campaign_id,experiment_id,tuple(artifacts),dict(metadata or {}))
        ep=self.entries_root/campaign_id/experiment_id/object_kind.value/f'{object_id}.entry.json'; self._write_immutable(ep,_bytes(e.to_dict()))
        return RepositoryWriteResult(e,str(op.relative_to(self.root)),str(ep.relative_to(self.root)))
    def read_object(self,entry):
        if not isinstance(entry,CampaignRepositoryEntry): raise ValidationError('entry must be CampaignRepositoryEntry.')
        p=self.objects_root/entry.object_kind.value/entry.object_sha256[:2]/f'{entry.object_sha256}.json'
        if not p.is_file(): raise FileNotFoundError(p)
        data=p.read_bytes(); actual=_sha(data)
        if actual!=entry.object_sha256: raise ValidationError('stored object SHA-256 mismatch.')
        return json.loads(data.decode('utf-8'))
    def verify_entry(self,entry):
        self.read_object(entry); p=self.entries_root/entry.campaign_id/entry.experiment_id/entry.object_kind.value/f'{entry.object_id}.entry.json'
        if not p.is_file(): raise FileNotFoundError(p)
        if json.loads(p.read_text(encoding='utf-8')).get('entry_sha256')!=entry.entry_sha256: raise ValidationError('stored entry SHA-256 mismatch.')
        return True
    def build_manifest(self,*,repository_id,entries,metadata=None): return CampaignRepositoryManifest(repository_id,tuple(entries),dict(metadata or {}))
    def write_manifest(self,manifest):
        if not isinstance(manifest,CampaignRepositoryManifest): raise ValidationError('manifest must be CampaignRepositoryManifest.')
        self.initialize(); p=self.manifests_root/f'{_safe(manifest.repository_id)}-{manifest.manifest_sha256}.json'; self._write_immutable(p,_bytes(manifest.to_dict())); return str(p.relative_to(self.root))
    def verify_manifest(self,manifest):
        for e in manifest.entries: self.verify_entry(e)
        p=self.manifests_root/f'{manifest.repository_id}-{manifest.manifest_sha256}.json'
        if not p.is_file(): raise FileNotFoundError(p)
        if json.loads(p.read_text(encoding='utf-8')).get('manifest_sha256')!=manifest.manifest_sha256: raise ValidationError('stored repository manifest SHA-256 mismatch.')
        return True
    @staticmethod
    def _write_immutable(path,data):
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            if path.read_bytes()==data: return
            raise ValidationError(f'immutable repository path already exists with different content: {path}')
        fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=str(path.parent))
        try:
            with os.fdopen(fd,'wb') as h: h.write(data); h.flush(); os.fsync(h.fileno())
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
