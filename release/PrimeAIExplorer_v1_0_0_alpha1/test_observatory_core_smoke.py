from collections.abc import Mapping, Sequence
from typing import Any

from primeaiexplorer.observatories import (
    Observatory,
    ObservatoryManager,
    ObservatoryResult,
)


class RecordCountObservatory(Observatory):
    name = "record_count"

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Mapping[str, Any],
    ) -> ObservatoryResult:
        return ObservatoryResult(
            name=self.name,
            summary={
                "message": "Canonical records counted successfully.",
            },
            metrics={
                "record_count": len(records),
            },
            metadata={
                "experiment_id": context.get("experiment_id"),
            },
        )


manager = ObservatoryManager()
manager.register(RecordCountObservatory())

results = manager.run(
    records=[
        {"case_id": "CASE-001"},
        {"case_id": "CASE-002"},
    ],
    context={
        "experiment_id": "EXP-000001",
    },
)

print(results["record_count"].to_dict())
