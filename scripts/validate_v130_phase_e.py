from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.release_hardening import ReleaseHardening


def check(label, condition, detail):
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<30} {detail}")
    if not condition:
        raise SystemExit(1)


def main():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    print("PrimeAIExplorer v1.3 Phase E Validator")
    print("=" * 76)
    check("installed version", version == "1.3.0-rc1", version)
    check("release version", ReleaseHardening.release_version == "1.3.0", ReleaseHardening.release_version)
    check("release candidate", ReleaseHardening.release_candidate == "1.3.0-rc1", ReleaseHardening.release_candidate)
    check("required files", len(ReleaseHardening.required_files) >= 10, str(len(ReleaseHardening.required_files)))
    print("=" * 76)
    print("PrimeAIExplorer v1.3 Phase E validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
