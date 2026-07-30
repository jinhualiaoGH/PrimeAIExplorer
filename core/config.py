from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    config["_config_path"] = str(config_path)
    return config


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def experiment_root(config: dict[str, Any]) -> Path:
    relative = config["paths"]["experiment_root"]
    return (project_root() / relative).resolve()


def resolve_experiment_path(config: dict[str, Any], relative: str) -> Path:
    return experiment_root(config) / relative
