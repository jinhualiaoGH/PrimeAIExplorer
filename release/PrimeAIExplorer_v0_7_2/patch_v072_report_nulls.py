from pathlib import Path

path = Path("src/primeaiexplorer/compare.py")
text = path.read_text(encoding="utf-8")

old = """def _pct(value: Any) -> str:
    return f"{float(value or 0):.2%}"
"""

new = """def _finite_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _fmt_number(value: Any, spec: str, missing: str = "—") -> str:
    number = _finite_number(value)
    return missing if number is None else format(number, spec)


def _fmt_percent(value: Any, missing: str = "—") -> str:
    return _fmt_number(value, ".2%", missing)


def _pct(value: Any) -> str:
    return _fmt_percent(value)
"""

if old not in text:
    raise SystemExit("Expected formatting block was not found.")

text = text.replace(old, new)

text = text.replace(
    "f\"{float(row.get('mean_absolute_error', 0)):.2f} | {float(row.get('switch_rate', 0)):.2%} | \"",
    "f\"{_fmt_number(row.get('mean_absolute_error'), '.2f')} | {_fmt_percent(row.get('switch_rate'))} | \"",
)

text = text.replace(
    "f\"<td>{float(row.get('mean_absolute_error', 0)):.2f}</td>\"",
    "f\"<td>{_fmt_number(row.get('mean_absolute_error'), '.2f')}</td>\"",
)

text = text.replace(
    "f\"<td>{float(row.get('mean_signed_error', 0)):+.2f}</td>\"",
    "f\"<td>{_fmt_number(row.get('mean_signed_error'), '+.2f')}</td>\"",
)

path.write_text(text, encoding="utf-8", newline="\n")
print("[PASS] Legacy-null report formatting patched")
print("[PASS]", path.resolve())
