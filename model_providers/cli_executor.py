from __future__ import annotations
import json, os
from pathlib import Path
from functools import partial
from .core import default_registry
from .bridge import ProviderExecutor, payload_prompt_builder

_EXECUTOR=None

def _load():
    path=os.getenv("PRIMEAIEXPLORER_PROVIDER_CONFIG")
    if not path: raise RuntimeError("PRIMEAIEXPLORER_PROVIDER_CONFIG is not set.")
    config=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    provider=default_registry().create(config["provider"],**config.get("options",{}))
    builder=partial(payload_prompt_builder,default_model=config["model"],
                    default_system_prompt=config.get("system_prompt"))
    return ProviderExecutor(provider,builder)

def execute(case):
    global _EXECUTOR
    if _EXECUTOR is None: _EXECUTOR=_load()
    return _EXECUTOR(case)
