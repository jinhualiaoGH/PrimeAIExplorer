from __future__ import annotations
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "demo" / "exp000001"
dataset_dir = root / "dataset"
pilot_dir = root / "pilot_001"
dataset_dir.mkdir(parents=True, exist_ok=True)
pilot_dir.mkdir(parents=True, exist_ok=True)

cases = [
    ("CASE-W004-0001", "PAIR-0001", 4, 6),
    ("CASE-W008-0001", "PAIR-0001", 8, 6),
    ("CASE-W016-0001", "PAIR-0001", 16, 6),
    ("CASE-W032-0001", "PAIR-0001", 32, 6),
    ("CASE-W064-0001", "PAIR-0001", 64, 6),
]
(dataset_dir / "cases.csv").write_text(
    "case_id,pair_id,window_size,ground_truth\n" +
    "".join(f"{c},{p},{w},{g}\n" for c,p,w,g in cases),
    encoding="utf-8",
)
responses = {"responses": [
    {"case_id": cases[0][0], "prediction": 6, "confidence": 80, "explanation": "The local sequence repeats a common gap."},
    {"case_id": cases[1][0], "response": {"prediction": 6, "confidence": 72, "explanation": "Six is a frequent prime gap."}},
    {"case_id": cases[2][0], "prediction": 4, "confidence": 61, "explanation": "The continuation is uncertain."},
    {"case_id": cases[3][0], "prediction": 6, "confidence": 74, "explanation": "Recent local values favor six."},
    {"case_id": cases[4][0], "prediction": 8, "confidence": 55, "explanation": "A small even gap is likely."},
]}
(pilot_dir / "responses.json").write_text(json.dumps(responses, indent=2) + "\n", encoding="utf-8")
print(f"Demo created: {root}")
