from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


def _run(command: list[str], cwd: Path) -> dict[str, object]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        return {
            "command": command,
            "return_code": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "command": command,
            "return_code": None,
            "stdout": "",
            "stderr": str(exc),
        }


def capture_environment(project_root: Path) -> dict[str, object]:
    selected_environment = {
        key: value
        for key, value in sorted(os.environ.items())
        if key.startswith(("PRIMEAIEXPLORER_", "OPENAI_", "ANTHROPIC_", "GOOGLE_", "GEMINI_"))
        and not any(secret in key for secret in ("KEY", "TOKEN", "SECRET", "PASSWORD"))
    }

    return {
        "python": {
            "executable": sys.executable,
            "version": sys.version,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "git": {
            "head": _run(["git", "rev-parse", "HEAD"], project_root),
            "describe": _run(["git", "describe", "--tags", "--always"], project_root),
            "status": _run(["git", "status", "--short"], project_root),
        },
        "pip_freeze": _run([sys.executable, "-m", "pip", "freeze"], project_root),
        "selected_environment": selected_environment,
    }
