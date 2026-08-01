from __future__ import annotations
import hashlib,json
from typing import Any,Mapping

def canonical_json_bytes(value: Mapping[str,Any])->bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def content_id(prefix:str,value:Mapping[str,Any],length:int=16)->str:
    return f"{prefix}-{hashlib.sha256(canonical_json_bytes(value)).hexdigest()[:length].upper()}"
