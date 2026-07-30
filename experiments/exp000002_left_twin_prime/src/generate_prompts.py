from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import ensure_directories, experiment_root, load_config


SYSTEM_TEXT = """You are participating in a controlled numerical continuation experiment. Follow the response format exactly."""


def format_numbers(values: list[int], per_line: int = 16) -> str:
    lines = []
    for i in range(0, len(values), per_line):
        lines.append(" ".join(str(x) for x in values[i : i + per_line]))
    return "\n".join(lines)


def build_user_prompt(case: dict) -> str:
    definition = ""
    if case["definition_condition"] == "disclosed":
        definition = (
            "A left twin prime is a prime q such that q + 2 is also prime. "
            "ltp(i) denotes the i-th left twin prime.\n\n"
        )

    representation = case["representation"]
    if representation == "absolute":
        observations = (
            "Observed consecutive left twin primes:\n"
            + format_numbers(case["observed_left_twin_primes"])
        )
    elif representation == "gaps":
        observations = (
            "Observed consecutive gaps between left twin primes:\n"
            + format_numbers(case["observed_left_twin_prime_gaps"])
        )
    elif representation == "combined":
        observations = (
            f"Current left twin prime: {case['current_left_twin_prime']}\n\n"
            "Observed recent consecutive gaps between left twin primes:\n"
            + format_numbers(case["observed_left_twin_prime_gaps"])
        )
    else:
        raise ValueError(f"Unknown representation: {representation}")

    return f"""{definition}Observation window size: {case['window_size']}

{observations}

Predict the next left twin prime.

Return JSON only using this exact structure:

{{
  "prediction": <integer>,
  "confidence": <integer from 0 to 100>,
  "explanation": "<brief explanation>"
}}"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate text prompts for all public cases.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    ensure_directories(config)
    root = experiment_root(config)

    public_dir = root / "cases" / "public"
    prompts_dir = root / "prompts" / "text"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for case_path in sorted(public_dir.glob("CASE-*.json")):
        with case_path.open("r", encoding="utf-8") as f:
            case = json.load(f)

        prompt_text = (
            "SYSTEM\n"
            + SYSTEM_TEXT
            + "\n\nUSER\n"
            + build_user_prompt(case)
            + "\n"
        )
        (prompts_dir / f"{case['case_id']}.txt").write_text(
            prompt_text, encoding="utf-8"
        )
        count += 1

    print("PROMPT GENERATION PASSED")
    print(f"Prompts: {count:,}")
    print(f"Output:  {prompts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
