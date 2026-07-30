from __future__ import annotations

from pathlib import Path
import re


path = Path(
    r"C:\PrimeAIExplorer\tests\test_prime_value_phase_a.py"
)

text = path.read_text(encoding="utf-8")

if "import tempfile" not in text:
    future = "from __future__ import annotations\n"

    if future in text:
        text = text.replace(
            future,
            future + "\nimport tempfile\n",
            1,
        )
    else:
        text = "import tempfile\n" + text

replacement = '''    def test_phase_b_requires_valid_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prime_root = root / "ranges"
            prime_root.mkdir()

            destination = root / "prime_values.npy"

            plugin = PrimeValueSequencePlugin(
                {
                    "_experiment_root": str(root),
                    "repository": {
                        "prime_root": str(prime_root),
                        "read_only": True,
                    },
                    "sequence": {
                        "representation": "absolute",
                        "target_count": 1,
                    },
                    "validation": {
                        "full_partition_monotonic_check": True,
                    },
                }
            )

            with self.assertRaisesRegex(
                ValueError,
                "No canonical partitions found",
            ):
                plugin.build_dataset(
                    prime_root,
                    destination,
                    count=1,
                )

            self.assertFalse(destination.exists())

            metadata = destination.with_suffix(
                ".metadata.json"
            )
            self.assertFalse(metadata.exists())
'''

lines = text.splitlines(keepends=True)

start = None

for index, line in enumerate(lines):
    if "def test_phase_b_disabled" in line:
        start = index
        break

if start is None:
    if "def test_phase_b_requires_valid_repository" in text:
        print(
            "[PASS] Replacement test already exists."
        )
        raise SystemExit(0)

    raise RuntimeError(
        "Could not find test_phase_b_disabled."
    )

end = start + 1

while end < len(lines):
    line = lines[end]

    if re.match(
        r"^    def test_[A-Za-z0-9_]+\(",
        line,
    ):
        break

    if re.match(
        r"^class ",
        line,
    ):
        break

    end += 1

new_lines = (
    lines[:start]
    + [replacement + "\n"]
    + lines[end:]
)

path.write_text(
    "".join(new_lines),
    encoding="utf-8",
)

print(f"[PASS] Updated: {path}")
print(
    "[PASS] Replaced obsolete Phase A lifecycle test."
)
