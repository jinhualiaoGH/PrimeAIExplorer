from __future__ import annotations

import unittest
from collections.abc import Mapping, Sequence
from typing import Any

from primeaiexplorer.observatories import (
    Observatory,
    ObservatoryManager,
    ObservatoryResult,
)


class CountingObservatory(Observatory):
    name = "counting"

    def analyze(
        self,
        records: Sequence[Mapping[str, Any]],
        context: Mapping[str, Any],
    ) -> ObservatoryResult:
        return ObservatoryResult(
            name=self.name,
            version=self.version,
            summary={"record_count": len(records)},
            metrics={"record_count": len(records)},
            metadata={"experiment_id": context.get("experiment_id")},
        )


class SecondObservatory(Observatory):
    name = "second"

    def analyze(self, records, context):
        return ObservatoryResult(name=self.name, metrics={"ok": True})


class WrongNameObservatory(Observatory):
    name = "expected"

    def analyze(self, records, context):
        return ObservatoryResult(name="unexpected")


class WrongTypeObservatory(Observatory):
    name = "wrong_type"

    def analyze(self, records, context):
        return {"name": self.name}


class BlankNameObservatory(Observatory):
    name = "   "

    def analyze(self, records, context):
        return ObservatoryResult(name="blank")


class ObservatoryCoreTests(unittest.TestCase):
    def test_register_observatory(self) -> None:
        manager = ObservatoryManager()
        observatory = CountingObservatory()
        manager.register(observatory)
        self.assertEqual(manager.names(), ("counting",))
        self.assertIs(manager.get("counting"), observatory)

    def test_duplicate_name_rejected(self) -> None:
        manager = ObservatoryManager([CountingObservatory()])
        with self.assertRaisesRegex(ValueError, "already registered"):
            manager.register(CountingObservatory())

    def test_empty_name_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty"):
            ObservatoryManager([BlankNameObservatory()])

    def test_deterministic_execution_order(self) -> None:
        manager = ObservatoryManager([CountingObservatory(), SecondObservatory()])
        results = manager.run([{"case_id": "A"}], {})
        self.assertEqual(tuple(results), ("counting", "second"))

    def test_result_validation(self) -> None:
        result = ObservatoryResult(
            name="sample",
            summary={"status": "ok"},
            metrics={"accuracy": 1.0},
            tables={"rows": [{"x": 1}]},
            metadata={"source": "test"},
            warnings=["small sample"],
        )
        self.assertEqual(result.to_dict()["tables"]["rows"], [{"x": 1}])
        with self.assertRaises(TypeError):
            ObservatoryResult(name="sample", metrics=[])

    def test_invalid_result_type_rejected(self) -> None:
        manager = ObservatoryManager([WrongTypeObservatory()])
        with self.assertRaisesRegex(TypeError, "expected ObservatoryResult"):
            manager.run([], {})

    def test_invalid_result_name_rejected(self) -> None:
        manager = ObservatoryManager([WrongNameObservatory()])
        with self.assertRaisesRegex(ValueError, "returned result name"):
            manager.run([], {})

    def test_manager_runs_multiple_observatories(self) -> None:
        manager = ObservatoryManager([CountingObservatory(), SecondObservatory()])
        results = manager.run(
            [{"case_id": "A"}, {"case_id": "B"}],
            {"experiment_id": "EXP-000001"},
        )
        self.assertEqual(results["counting"].metrics["record_count"], 2)
        self.assertEqual(
            results["counting"].metadata["experiment_id"],
            "EXP-000001",
        )
        self.assertTrue(results["second"].metrics["ok"])


if __name__ == "__main__":
    unittest.main()
