from __future__ import annotations

import argparse
import json

import numpy as np

from common import load_config, load_ltp_dataset, resolve_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated left twin prime dataset.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    data = load_ltp_dataset(config)

    if len(data) < 2:
        raise ValueError("Dataset must contain at least two values.")
    if int(data[0]) != 3:
        raise ValueError(f"Expected first left twin prime 3, found {int(data[0])}")
    if np.any(data[1:] <= data[:-1]):
        raise ValueError("Dataset is not strictly increasing.")
    if np.any(data % 2 == 0):
        raise ValueError("Unexpected even value in left twin prime dataset.")

    sample_expected = np.array([3, 5, 11, 17, 29, 41, 59, 71, 101], dtype=np.uint64)
    if len(data) >= len(sample_expected) and not np.array_equal(
        data[: len(sample_expected)], sample_expected
    ):
        raise ValueError(
            f"Initial sequence mismatch.\nExpected: {sample_expected}\nFound: {data[:len(sample_expected)]}"
        )

    metadata_path = resolve_output(config, config["dataset_metadata_file"])
    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)

    if int(metadata["count"]) != len(data):
        raise ValueError("Metadata count does not match dataset length.")

    print("LTP DATASET VALIDATION PASSED")
    print(f"Count:             {len(data):,}")
    print(f"First value:       {int(data[0]):,}")
    print(f"Last source value: {int(data[-2]):,}")
    print(f"Held-out target:   {int(data[-1]):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
