"""Generate the first real PrimeAIExplorer experimental dataset.

EXP-000001
Memory-Limited Numerical Continuation using consecutive prime gaps.

The generator uses a deterministic local sieve so the first experiment can run
without external services, API calls, or access to the large PrimeNet repository.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import random
import sys
from typing import Any, Sequence


EXPERIMENT_ID = "EXP-000001"
DATASET_ID = "DS-EXP000001-001"
DATASET_VERSION = "0.1.0"

DEFAULT_WINDOWS = (4, 8, 16, 32, 64)
DEFAULT_CASES_PER_WINDOW = 20
DEFAULT_SIEVE_LIMIT = 200_000
DEFAULT_SEED = 20260725


def utc_now_iso() -> str:
    """Return an ISO 8601 UTC timestamp."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize JSON deterministically for integrity hashing."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_json(value: Any) -> str:
    """Return the SHA-256 hash of canonical JSON."""

    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def generate_primes(limit: int) -> list[int]:
    """Generate all primes less than or equal to limit."""

    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError("Sieve limit must be an integer.")

    if limit < 100:
        raise ValueError("Sieve limit must be at least 100.")

    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"

    upper = int(limit**0.5)

    for candidate in range(2, upper + 1):
        if not sieve[candidate]:
            continue

        start = candidate * candidate
        count = ((limit - start) // candidate) + 1
        sieve[start : limit + 1 : candidate] = b"\x00" * count

    return [
        value
        for value, is_prime in enumerate(sieve)
        if is_prime
    ]


def calculate_gaps(primes: Sequence[int]) -> list[int]:
    """Calculate consecutive outgoing prime gaps."""

    if len(primes) < 2:
        raise ValueError("At least two primes are required.")

    return [
        right - left
        for left, right in zip(primes, primes[1:])
    ]


@dataclass(frozen=True, slots=True)
class ExperimentCase:
    """One memory-limited numerical-continuation case."""

    case_id: str
    pair_id: str
    experiment_id: str
    dataset_id: str
    dataset_version: str
    window_size: int
    observed_gaps: list[int]
    ground_truth: int
    target_gap_index_zero_based: int
    target_prime_index_one_based: int
    target_left_prime: int
    target_right_prime: int
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def select_target_indices(
    *,
    number_of_gaps: int,
    maximum_window: int,
    count: int,
    seed: int,
) -> list[int]:
    """Select reproducible shared targets for paired window comparisons."""

    first_valid_target = maximum_window
    last_valid_target = number_of_gaps - 1

    available = list(
        range(first_valid_target, last_valid_target + 1)
    )

    if len(available) < count:
        raise ValueError(
            "The generated prime sequence is too short for the requested "
            "number of cases."
        )

    generator = random.Random(seed)
    selected = generator.sample(available, count)
    return sorted(selected)


def build_cases(
    *,
    primes: Sequence[int],
    gaps: Sequence[int],
    windows: Sequence[int],
    cases_per_window: int,
    seed: int,
) -> list[ExperimentCase]:
    """Build paired cases for every requested memory window."""

    if not windows:
        raise ValueError("At least one window size is required.")

    if any(window < 1 for window in windows):
        raise ValueError("Window sizes must be positive.")

    maximum_window = max(windows)

    target_indices = select_target_indices(
        number_of_gaps=len(gaps),
        maximum_window=maximum_window,
        count=cases_per_window,
        seed=seed,
    )

    cases: list[ExperimentCase] = []

    for pair_number, target_index in enumerate(
        target_indices,
        start=1,
    ):
        pair_id = f"PAIR-{pair_number:04d}"

        for window_size in windows:
            observed = list(
                gaps[target_index - window_size : target_index]
            )

            case_id = (
                f"CASE-W{window_size:03d}-{pair_number:04d}"
            )

            cases.append(
                ExperimentCase(
                    case_id=case_id,
                    pair_id=pair_id,
                    experiment_id=EXPERIMENT_ID,
                    dataset_id=DATASET_ID,
                    dataset_version=DATASET_VERSION,
                    window_size=window_size,
                    observed_gaps=observed,
                    ground_truth=gaps[target_index],
                    target_gap_index_zero_based=target_index,
                    target_prime_index_one_based=target_index + 1,
                    target_left_prime=primes[target_index],
                    target_right_prime=primes[target_index + 1],
                    source="local_deterministic_sieve",
                )
            )

    return sorted(
        cases,
        key=lambda case: (
            case.window_size,
            case.pair_id,
        ),
    )


def write_json_atomic(path: Path, value: Any) -> None:
    """Write a JSON artifact atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(path.name + ".tmp")

    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )

    try:
        temporary_path.write_text(
            payload,
            encoding="utf-8",
            newline="\n",
        )
        temporary_path.replace(path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def write_cases_csv(
    path: Path,
    cases: Sequence[ExperimentCase],
) -> None:
    """Write a compact tabular case index."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(path.name + ".tmp")

    fieldnames = [
        "case_id",
        "pair_id",
        "experiment_id",
        "dataset_id",
        "dataset_version",
        "window_size",
        "observed_gaps",
        "ground_truth",
        "target_gap_index_zero_based",
        "target_prime_index_one_based",
        "target_left_prime",
        "target_right_prime",
        "source",
    ]

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=fieldnames,
            )
            writer.writeheader()

            for case in cases:
                row = case.to_dict()
                row["observed_gaps"] = " ".join(
                    str(gap)
                    for gap in case.observed_gaps
                )
                writer.writerow(row)

        temporary_path.replace(path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def validate_cases(
    cases: Sequence[ExperimentCase],
    *,
    windows: Sequence[int],
    cases_per_window: int,
) -> None:
    """Validate the generated experimental design."""

    expected_count = len(windows) * cases_per_window

    if len(cases) != expected_count:
        raise AssertionError(
            f"Expected {expected_count} cases; found {len(cases)}."
        )

    case_ids = [case.case_id for case in cases]

    if len(case_ids) != len(set(case_ids)):
        raise AssertionError("Duplicate case identifiers detected.")

    for window in windows:
        window_cases = [
            case
            for case in cases
            if case.window_size == window
        ]

        if len(window_cases) != cases_per_window:
            raise AssertionError(
                f"Window {window} has {len(window_cases)} cases."
            )

        for case in window_cases:
            if len(case.observed_gaps) != window:
                raise AssertionError(
                    f"{case.case_id} contains the wrong window length."
                )

            actual_gap = (
                case.target_right_prime
                - case.target_left_prime
            )

            if actual_gap != case.ground_truth:
                raise AssertionError(
                    f"Ground truth mismatch in {case.case_id}."
                )

    pair_groups: dict[str, list[ExperimentCase]] = {}

    for case in cases:
        pair_groups.setdefault(case.pair_id, []).append(case)

    if len(pair_groups) != cases_per_window:
        raise AssertionError("Unexpected number of paired targets.")

    for pair_id, pair_cases in pair_groups.items():
        target_indices = {
            case.target_gap_index_zero_based
            for case in pair_cases
        }

        truths = {
            case.ground_truth
            for case in pair_cases
        }

        if len(target_indices) != 1 or len(truths) != 1:
            raise AssertionError(
                f"Paired design is inconsistent for {pair_id}."
            )


def generate_dataset(
    *,
    output_directory: Path,
    sieve_limit: int,
    windows: Sequence[int],
    cases_per_window: int,
    seed: int,
) -> dict[str, Any]:
    """Generate and preserve the complete experimental dataset."""

    primes = generate_primes(sieve_limit)
    gaps = calculate_gaps(primes)

    cases = build_cases(
        primes=primes,
        gaps=gaps,
        windows=windows,
        cases_per_window=cases_per_window,
        seed=seed,
    )

    validate_cases(
        cases,
        windows=windows,
        cases_per_window=cases_per_window,
    )

    case_payload = [
        case.to_dict()
        for case in cases
    ]

    cases_sha256 = sha256_json(case_payload)

    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "title": (
            "Memory-Limited Numerical Continuation: "
            "Consecutive Prime Gaps"
        ),
        "generated_at_utc": utc_now_iso(),
        "generator": "experiments.exp000001.generate_dataset",
        "generator_version": "0.1.0",
        "source": {
            "type": "local_deterministic_sieve",
            "sieve_limit": sieve_limit,
            "prime_count": len(primes),
            "gap_count": len(gaps),
            "minimum_prime": primes[0],
            "maximum_prime": primes[-1],
        },
        "design": {
            "window_sizes": list(windows),
            "cases_per_window": cases_per_window,
            "total_cases": len(cases),
            "paired_targets": True,
            "shared_target_count": cases_per_window,
            "random_seed": seed,
        },
        "integrity": {
            "algorithm": "SHA-256",
            "cases_sha256": cases_sha256,
        },
        "scientific_note": (
            "Every pair uses the same prediction target across all "
            "window sizes. Only the visible observation history changes."
        ),
    }

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_json_atomic(
        output_directory / "cases.json",
        case_payload,
    )
    write_cases_csv(
        output_directory / "cases.csv",
        cases,
    )
    write_json_atomic(
        output_directory / "metadata.json",
        metadata,
    )

    return metadata


def parse_windows(value: str) -> tuple[int, ...]:
    """Parse a comma-separated list of positive window sizes."""

    try:
        windows = tuple(
            int(item.strip())
            for item in value.split(",")
            if item.strip()
        )
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "Window sizes must be comma-separated integers."
        ) from error

    if not windows or any(window < 1 for window in windows):
        raise argparse.ArgumentTypeError(
            "Window sizes must contain positive integers."
        )

    if len(windows) != len(set(windows)):
        raise argparse.ArgumentTypeError(
            "Window sizes must be unique."
        )

    return tuple(sorted(windows))


def run_self_test() -> None:
    """Verify deterministic generation before writing scientific artifacts."""

    primes = generate_primes(10_000)
    gaps = calculate_gaps(primes)

    first = build_cases(
        primes=primes,
        gaps=gaps,
        windows=(4, 8),
        cases_per_window=5,
        seed=12345,
    )
    second = build_cases(
        primes=primes,
        gaps=gaps,
        windows=(4, 8),
        cases_per_window=5,
        seed=12345,
    )

    validate_cases(
        first,
        windows=(4, 8),
        cases_per_window=5,
    )

    if [case.to_dict() for case in first] != [
        case.to_dict()
        for case in second
    ]:
        raise AssertionError(
            "Dataset generation is not deterministic."
        )

    print("[PASS] Generator self-test passed")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate EXP-000001 paired prime-gap continuation cases."
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("datasets") / "EXP-000001",
        help="Output directory.",
    )
    parser.add_argument(
        "--sieve-limit",
        type=int,
        default=DEFAULT_SIEVE_LIMIT,
        help="Upper bound for deterministic local prime generation.",
    )
    parser.add_argument(
        "--windows",
        type=parse_windows,
        default=DEFAULT_WINDOWS,
        help="Comma-separated observation windows.",
    )
    parser.add_argument(
        "--cases-per-window",
        type=int,
        default=DEFAULT_CASES_PER_WINDOW,
        help="Number of paired targets.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Deterministic target-selection seed.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run internal validation before generation.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    if arguments.cases_per_window < 1:
        parser.error("--cases-per-window must be positive.")

    if arguments.self_test:
        run_self_test()

    metadata = generate_dataset(
        output_directory=arguments.output,
        sieve_limit=arguments.sieve_limit,
        windows=arguments.windows,
        cases_per_window=arguments.cases_per_window,
        seed=arguments.seed,
    )

    print()
    print("=" * 72)
    print("PrimeAIExplorer EXP-000001 Dataset Generator")
    print("=" * 72)
    print(f"Experiment:       {metadata['experiment_id']}")
    print(f"Dataset:          {metadata['dataset_id']}")
    print(
        "Window sizes:     "
        + ", ".join(
            str(value)
            for value in metadata["design"]["window_sizes"]
        )
    )
    print(
        f"Paired targets:   "
        f"{metadata['design']['shared_target_count']}"
    )
    print(
        f"Total cases:      "
        f"{metadata['design']['total_cases']}"
    )
    print(
        f"Prime count:      "
        f"{metadata['source']['prime_count']:,}"
    )
    print(
        f"Cases SHA-256:    "
        f"{metadata['integrity']['cases_sha256']}"
    )
    print(f"Output:           {arguments.output.resolve()}")
    print()
    print("EXP-000001 DATASET GENERATION PASSED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())