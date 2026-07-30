from __future__ import annotations
import importlib.util, json, os, platform, sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str
    required: bool = True
    def to_dict(self): return asdict(self)

def doctor_checks(base_dir: Path | None = None):
    base=(base_dir or Path.cwd()).resolve(); rows=[]
    rows += [CheckResult("Python", sys.version_info >= (3,10), platform.python_version()), CheckResult("Operating system", True, platform.platform()), CheckResult("Working directory", base.is_dir(), str(base)), CheckResult("Writable directory", os.access(base, os.W_OK), str(base))]
    for name in ["primeaiexplorer.observatories","primeaiexplorer.exporters","primeaiexplorer.dashboards","primeaiexplorer.visualizations"]:
        ok=importlib.util.find_spec(name) is not None; rows.append(CheckResult(f"Import {name}",ok,"available" if ok else "missing"))
    ok=importlib.util.find_spec("prompt_toolkit") is not None; rows.append(CheckResult("Optional prompt-toolkit",ok,"available" if ok else "not installed; basic input remains available",False))
    return rows

def required_release_paths():
    return ("README.md","CHANGELOG.md","ROADMAP.md","CONTRIBUTING.md","LICENSE","CITATION.cff","pyproject.toml","install.ps1","run_tests.ps1","run_demo.ps1","src/primeaiexplorer/__init__.py","src/primeaiexplorer/observatories/manager.py","src/primeaiexplorer/exporters/unified.py","src/primeaiexplorer/dashboards/html.py","src/primeaiexplorer/visualizations/svg.py")

def release_checks(root: Path):
    root=root.resolve(); rows=[CheckResult("Release root",root.is_dir(),str(root))]
    for rel in required_release_paths():
        p=root/rel; rows.append(CheckResult(rel,p.is_file(),"present" if p.is_file() else "missing"))
    pp=root/'pyproject.toml'
    if pp.is_file(): rows.append(CheckResult("RC2 version metadata", 'version = "1.0.0rc2"' in pp.read_text(encoding="utf-8-sig"), "1.0.0rc2"))
    n=len(list((root/'tests').glob('test_*.py'))) if (root/'tests').is_dir() else 0
    rows.append(CheckResult("Regression test modules",n>=10,str(n)))
    return rows

def all_required_pass(rows: Iterable[CheckResult]): return all(x.passed for x in rows if x.required)

def write_check_report(path: Path, rows: Iterable[CheckResult], *, kind: str):
    rows=list(rows); payload={"schema_version":"1.0","kind":kind,"created_utc":datetime.now(timezone.utc).isoformat(),"passed":all_required_pass(rows),"checks":[r.to_dict() for r in rows]}
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
