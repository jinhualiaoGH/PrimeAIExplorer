from pathlib import Path


path = Path(r"src\primeaiexplorer\io.py")

text = path.read_text(
    encoding="utf-8",
)

old_constant = (
    'CASE_RE = re.compile('
    'r"CASE-W(?P<window>\\d+)-(?P<number>\\d+)", '
    're.IGNORECASE)\n'
)

new_constant = (
    'CASE_RE = re.compile('
    'r"CASE-W(?P<window>\\d+)-(?P<number>\\d+)", '
    're.IGNORECASE)\n'
    '\n'
    'IGNORED_RESPONSE_FILENAMES = {\n'
    '    "current_response.json",\n'
    '    "pilot_manifest.json",\n'
    '}\n'
)

old_function = '''def _individual_response_paths(folder: Path) -> list[Path]:
    patterns = ("*.response.json", "*_response.json")
    return sorted({p.resolve() for pattern in patterns for p in folder.rglob(pattern)})
'''

new_function = '''def _individual_response_paths(folder: Path) -> list[Path]:
    """Discover canonical individual response files.

    Operational working files and pilot metadata are deliberately excluded.
    In particular, ``current_response.json`` matches the broad
    ``*_response.json`` pattern but is not a committed response record.
    """

    patterns = ("*.response.json", "*_response.json")

    return sorted(
        {
            path.resolve()
            for pattern in patterns
            for path in folder.rglob(pattern)
            if path.name.lower() not in IGNORED_RESPONSE_FILENAMES
        }
    )
'''

if old_constant not in text:
    raise SystemExit(
        "[FAIL] Could not locate CASE_RE declaration. "
        "The source file was not changed."
    )

if old_function not in text:
    raise SystemExit(
        "[FAIL] Could not locate _individual_response_paths(). "
        "The source file was not changed."
    )

text = text.replace(
    old_constant,
    new_constant,
    1,
)

text = text.replace(
    old_function,
    new_function,
    1,
)

path.write_text(
    text,
    encoding="utf-8",
    newline="\n",
)

print("[PASS] Added ignored operational response filenames")
print("[PASS] Patched:", path.resolve())
