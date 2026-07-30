from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    root = Path(args.root)
    if root.exists():
        shutil.rmtree(root)
    pilot = root / "pilot_001"
    pilot.mkdir(parents=True)

    rows = [
        ("CASE-W004-0001", "PAIR-0001", 4, 6, 6, 74, "A repeated small gap suggests six."),
        ("CASE-W008-0001", "PAIR-0002", 8, 8, 6, 62, "Six is locally frequent."),
        ("CASE-W016-0001", "PAIR-0003", 16, 6, 6, 70, "The recent pattern favors six."),
        ("CASE-W032-0001", "PAIR-0004", 32, 12, 10, 44, "Ten is plausible from the local mix."),
        ("CASE-W064-0001", "PAIR-0005", 64, 4, 4, 58, "Four follows a short-gap pattern."),
    ]

    with (root / "cases.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case_id", "pair_id", "experiment_id", "dataset_id", "dataset_version", "window_size", "observed_gaps", "ground_truth"])
        for case, pair, window, actual, *_ in rows:
            writer.writerow([case, pair, "EXP-000001", "DS-DEMO", "0.2.1", window, "2 4 6 8", actual])

    for case, _pair, _window, _actual, prediction, confidence, explanation in rows:
        (pilot / f"{case}.response.json").write_text(
            json.dumps({"prediction": prediction, "confidence": confidence, "explanation": explanation}, indent=2),
            encoding="utf-8",
        )
    print(f"Demo created: {root.resolve()}")


if __name__ == "__main__":
    main()
