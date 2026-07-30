from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo" / "exp000001"
DATASET = DEMO / "dataset"
PILOT = DEMO / "pilot_001"

DATASET.mkdir(parents=True, exist_ok=True)
PILOT.mkdir(parents=True, exist_ok=True)

windows = [4, 8, 16, 32, 64]
rows = ["case_id,ground_truth,window_size,pair_id"]
for window in windows:
    case_id = f"CASE-W{window:03d}-0001"
    rows.append(f"{case_id},6,{window},PAIR-0001")
    (PILOT / f"{case_id}.txt").write_text("Demo prompt\n", encoding="utf-8")
(DATASET / "cases.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")

responses = [
    (6, 18, "Prime gaps are irregular; 6 is a common small gap."),
    (6, 18, "A common even gap is selected."),
    (6, 18, "The local sequence suggests 6."),
    (6, 100, "The sequence is recognized exactly."),
    (6, 18, "A low-confidence frequency prior selects 6."),
]
text = "\ufeff" + "\n\n".join(
    '{"prediction":%d,"confidence":%d,"explanation":%s}' % (
        prediction, confidence, __import__("json").dumps(explanation)
    )
    for prediction, confidence, explanation in responses
) + "\n"
(PILOT / "responses.json").write_text(text, encoding="utf-8")
print(f"Demo created: {DEMO}")
