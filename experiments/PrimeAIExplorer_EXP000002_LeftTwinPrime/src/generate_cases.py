from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from common import ensure_directories, experiment_root, load_config, load_ltp_dataset, write_json


def choose_endpoints(
    dataset_length: int,
    scales: list[int],
    cases_per_scale: int,
    largest_window: int,
    rng: np.random.Generator,
) -> list[tuple[int, int]]:
    selected: list[tuple[int, int]] = []

    for scale in scales:
        target_index = int(scale)
        if target_index >= dataset_length:
            continue

        lower = max(largest_window + 1, target_index - max(1000, target_index // 100))
        upper = min(dataset_length - 1, target_index + max(1000, target_index // 100))

        candidates = np.arange(lower, upper + 1, dtype=np.int64)
        count = min(cases_per_scale, len(candidates))
        picks = rng.choice(candidates, size=count, replace=False)

        for endpoint_1_based in sorted(int(x) for x in picks):
            selected.append((scale, endpoint_1_based))

    canonical_endpoint = dataset_length - 1
    if canonical_endpoint > largest_window:
        selected.append((dataset_length - 1, canonical_endpoint))

    # Preserve order while removing duplicates.
    seen = set()
    unique = []
    for item in selected:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate controlled LTP continuation cases.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    ensure_directories(config)
    data = load_ltp_dataset(config)

    windows = [int(x) for x in config["window_sizes"]]
    representations = list(config["representations"])
    definition_conditions = list(config["definition_conditions"])
    largest_window = max(windows)

    rng = np.random.default_rng(int(config["random_seed"]))
    endpoints = choose_endpoints(
        dataset_length=len(data),
        scales=[int(x) for x in config["evaluation_scales"]],
        cases_per_scale=int(config["random_cases_per_scale"]),
        largest_window=largest_window,
        rng=rng,
    )

    cases_dir = experiment_root(config) / "cases"
    public_dir = cases_dir / "public"
    answers_dir = cases_dir / "answer_keys"
    public_dir.mkdir(parents=True, exist_ok=True)
    answers_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    case_counter = 0

    for scale, endpoint_1_based in endpoints:
        endpoint0 = endpoint_1_based - 1
        target0 = endpoint0 + 1
        if target0 >= len(data):
            continue

        for window in windows:
            if endpoint_1_based < window:
                continue

            absolute_values = np.asarray(
                data[endpoint0 - window + 1 : endpoint0 + 1], dtype=np.uint64
            )
            gap_values = np.diff(
                np.asarray(data[endpoint0 - window : endpoint0 + 1], dtype=np.int64)
            )

            for representation in representations:
                for definition_condition in definition_conditions:
                    case_counter += 1
                    case_id = (
                        f"CASE-{case_counter:06d}"
                        f"-S{scale}"
                        f"-I{endpoint_1_based}"
                        f"-W{window:04d}"
                        f"-{representation.upper()}"
                        f"-{definition_condition.upper()}"
                    )

                    public_case = {
                        "experiment_id": config["experiment_id"],
                        "case_id": case_id,
                        "scale": scale,
                        "endpoint_index_1_based": endpoint_1_based,
                        "target_index_1_based": endpoint_1_based + 1,
                        "window_size": window,
                        "representation": representation,
                        "definition_condition": definition_condition,
                    }

                    if representation == "absolute":
                        public_case["observed_left_twin_primes"] = [
                            int(x) for x in absolute_values
                        ]
                    elif representation == "gaps":
                        public_case["observed_left_twin_prime_gaps"] = [
                            int(x) for x in gap_values
                        ]
                    elif representation == "combined":
                        public_case["current_left_twin_prime"] = int(data[endpoint0])
                        public_case["observed_left_twin_prime_gaps"] = [
                            int(x) for x in gap_values
                        ]
                    else:
                        raise ValueError(f"Unknown representation: {representation}")

                    answer = {
                        "case_id": case_id,
                        "current_left_twin_prime": int(data[endpoint0]),
                        "target_left_twin_prime": int(data[target0]),
                        "target_gap": int(data[target0]) - int(data[endpoint0]),
                    }

                    write_json(public_dir / f"{case_id}.json", public_case)
                    write_json(answers_dir / f"{case_id}.answer.json", answer)

                    manifest_rows.append(
                        {
                            "case_id": case_id,
                            "scale": scale,
                            "endpoint_index_1_based": endpoint_1_based,
                            "target_index_1_based": endpoint_1_based + 1,
                            "window_size": window,
                            "representation": representation,
                            "definition_condition": definition_condition,
                        }
                    )

    manifest_path = cases_dir / "case_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_rows[0].keys())
        writer.writeheader()
        writer.writerows(manifest_rows)

    print("CASE GENERATION PASSED")
    print(f"Cases:    {len(manifest_rows):,}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
