from __future__ import annotations

import sys
from pathlib import Path


def add_project_root(script_file: str) -> Path:
    root = Path(script_file).resolve().parents[1]
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    return root
