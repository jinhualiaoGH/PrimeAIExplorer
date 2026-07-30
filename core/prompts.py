from __future__ import annotations

from typing import Any

from core.config import experiment_root
from core.io import read_json
from core.plugin import SequencePlugin


SYSTEM_TEXT = (
    "You are participating in a controlled numerical continuation experiment. "
    "Follow the response format exactly."
)


def _format(values: list[int], per_line: int = 16) -> str:
    return "\n".join(
        " ".join(str(x) for x in values[i : i + per_line])
        for i in range(0, len(values), per_line)
    )


def generate_prompts(config: dict[str, Any], plugin: SequencePlugin) -> int:
    root = experiment_root(config)
    public_dir = root / "cases" / "public"
    output_dir = root / "prompts" / "text"
    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for case_path in sorted(public_dir.glob("CASE-*.json")):
        case = read_json(case_path)

        definition = ""
        if case["definition_condition"] == "disclosed":
            definition = plugin.definition + "\n\n"

        representation = case["representation"]
        if representation == "absolute":
            observed = "Observed values:\n" + _format(case["observed_values"])
        elif representation == "gaps":
            observed = "Observed consecutive gaps:\n" + _format(case["observed_gaps"])
        elif representation == "combined":
            observed = (
                f"Current value: {case['current_value']}\n\n"
                "Observed recent consecutive gaps:\n"
                + _format(case["observed_gaps"])
            )
        else:
            raise ValueError(f"Unsupported representation: {representation}")

        target_label = config["prompt"]["target_label"]
        user_text = f"""{definition}Observation window size: {case['window_size']}

{observed}

Predict the next {target_label}.

Return JSON only using this exact structure:

{{
  "prediction": <integer>,
  "confidence": <integer from 0 to 100>,
  "explanation": "<brief explanation>"
}}"""

        text = f"SYSTEM\n{SYSTEM_TEXT}\n\nUSER\n{user_text}\n"
        (output_dir / f"{case['case_id']}.txt").write_text(text, encoding="utf-8")
        count += 1

    return count
