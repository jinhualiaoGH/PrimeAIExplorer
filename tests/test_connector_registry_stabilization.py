from __future__ import annotations

from pathlib import Path
import unittest

from core.registry_loader import RegistryLoader


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ConnectorRegistryStabilizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connectors = RegistryLoader(PROJECT_ROOT).connectors()

    def test_canonical_mock_exists(self) -> None:
        self.assertIn("CONNECTOR-000001", self.connectors)

    def test_canonical_mock_is_free_and_local(self) -> None:
        record = self.connectors["CONNECTOR-000001"]
        self.assertEqual(record["status"], "Active")
        self.assertEqual(record["cost_class"], "free")
        self.assertEqual(record["external_access"], "false")
        self.assertEqual(record["implementation_module"], "connectors.mock")

    def test_hosted_connector_is_disabled(self) -> None:
        record = self.connectors["CONNECTOR-000003"]
        self.assertEqual(record["status"], "Disabled")
        self.assertEqual(record["cost_class"], "paid")
        self.assertEqual(record["external_access"], "true")


if __name__ == "__main__":
    unittest.main()
