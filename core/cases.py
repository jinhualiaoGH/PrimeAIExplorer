from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config import experiment_root
from core.io import write_csv, write_json
from core.models import CaseRecord
from core.plugin import SequencePlugin


def generate_cases(config: dict[str, Any], plugin: SequencePlugin) -> list[CaseRecord]:
    root = experiment_root(config)
    public_dir = root / "cases" / "public"
    answer_dir = root / "cases" / "answer_keys"
    public_dir.mkdir(parents=True, exist_ok=True)
    answer_dir.mkdir(parents=True, exist_ok=True)

    windows = [int(x) for x in config["sampling"]["window_sizes"]]
    endpoints = [int(x) for x in config["sampling"]["endpoints"]]
    representations = list(config["sampling"]["representations"])
    conditions = list(config["sampling"]["definition_conditions"])

    cases: list[CaseRecord] = []
    counter = 0

    for endpoint in endpoints:
        for window_size in windows:
            if endpoint < window_size:
                continue
            for representation in representations:
                sequence_window = plugin.make_window(endpoint, window_size, representation)
                for condition in conditions:
                    counter += 1
                    case_id = f"CASE-{counter:06d}"

                    payload: dict[str, Any] = {
                        "experiment_id": config["experiment"]["id"],
                        "case_id": case_id,
                        "sequence_plugin": plugin.plugin_name,
                        "window_size": window_size,
                        "representation": representation,
                        "definition_condition": condition,
                        "endpoint_index_1_based": sequence_window.endpoint_index_1_based,
                        "target_index_1_based": sequence_window.target_index_1_based,
                    }

                    if representation == "absolute":
                        payload["observed_values"] = sequence_window.observed
                    elif representation == "gaps":
                        payload["observed_gaps"] = sequence_window.observed
                    elif representation == "combined":
                        payload["current_value"] = sequence_window.current_value
                        payload["observed_gaps"] = sequence_window.observed
                    else:
                        raise ValueError(f"Unsupported representation: {representation}")

                    answer = {
                        "case_id": case_id,
                        "target_value": sequence_window.target_value,
                        "current_value": sequence_window.current_value,
                    }

                    write_json(public_dir / f"{case_id}.json", payload)
                    write_json(answer_dir / f"{case_id}.answer.json", answer)

                    cases.append(
                        CaseRecord(
                            case_id=case_id,
                            experiment_id=config["experiment"]["id"],
                            sequence_plugin=plugin.plugin_name,
                            endpoint_index_1_based=sequence_window.endpoint_index_1_based,
                            target_index_1_based=sequence_window.target_index_1_based,
                            window_size=window_size,
                            representation=representation,
                            definition_condition=condition,
                            payload=payload,
                            target_value=sequence_window.target_value,
                        )
                    )

    rows = [
        {
            "case_id": c.case_id,
            "experiment_id": c.experiment_id,
            "sequence_plugin": c.sequence_plugin,
            "endpoint_index_1_based": c.endpoint_index_1_based,
            "target_index_1_based": c.target_index_1_based,
            "window_size": c.window_size,
            "representation": c.representation,
            "definition_condition": c.definition_condition,
        }
        for c in cases
    ]
    write_csv(root / "cases" / "case_manifest.csv", rows)
    return cases
