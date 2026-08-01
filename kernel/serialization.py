from __future__ import annotations
from dataclasses import asdict,is_dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any
import json

def normalize(v:Any)->Any:
    if is_dataclass(v): return normalize(asdict(v))
    if isinstance(v,Enum): return v.value
    if isinstance(v,Path): return v.as_posix()
    if isinstance(v,dict): return {str(k):normalize(x) for k,x in sorted(v.items(),key=lambda p:str(p[0]))}
    if isinstance(v,(list,tuple)): return [normalize(x) for x in v]
    if isinstance(v,set): return sorted(normalize(x) for x in v)
    return v

def canonical_json(v:Any)->str:
    return json.dumps(normalize(v),ensure_ascii=False,sort_keys=True,separators=(",",":"))

def stable_sha256(v:Any)->str:
    return sha256(canonical_json(v).encode("utf-8")).hexdigest()
