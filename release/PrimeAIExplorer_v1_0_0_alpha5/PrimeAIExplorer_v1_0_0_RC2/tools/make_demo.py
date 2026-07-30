from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo" / "exp000001"
DATASET = DEMO / "dataset"
PILOT = DEMO / "pilot_002"
TEXT = PILOT / "text"

DATASET.mkdir(parents=True, exist_ok=True)
TEXT.mkdir(parents=True, exist_ok=True)

windows = [4, 8, 16, 32, 64]
rows = ["case_id,ground_truth,window_size,pair_id"]
ledger = []
for window in windows:
    case_id = f"CASE-W{window:03d}-0002"
    rows.append(f"{case_id},6,{window},PAIR-0002")
    (TEXT / f"{case_id}.txt").write_text(f"Demo prompt for {case_id}\n", encoding="utf-8")
    ledger.append({
        "case_id": case_id,
        "pair_id": "PAIR-0002",
        "window_size": window,
        "collection_mode": "manual_chat",
        "response": None,
    })
ledger[0]["response"] = {
    "prediction": 4,
    "confidence": 18,
    "explanation": "Prime gaps are irregular; 4 is a common small gap after this short pattern.",
}
(DATASET / "cases.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
(PILOT / "responses.json").write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
print(f"Demo created: {DEMO}")
(PILOT / "current_response.json").write_text(
    json.dumps({
        "prediction": 6,
        "confidence": 60,
        "explanation": "A valid response committed by the Collection Assistant.",
    }, indent=2) + "\n",
    encoding="utf-8",
)
