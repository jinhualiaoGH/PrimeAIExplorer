"""Tests for PrimeAIExplorer v0.7 connector foundation."""

from __future__ import annotations

import json
import unittest

from connectors import (
    ConnectorMessage,
    ConnectorRequest,
    ConnectorStatus,
    DeterministicMockConnector,
    MessageRole,
    MockMode,
    canonical_request_id,
)
from core.connector_service import ConnectorService


def build_request(
    *,
    sequence: int = 1,
    user_content: str = "Prime gaps: 2, 4, 2, 4",
) -> ConnectorRequest:
    return ConnectorRequest(
        request_id=canonical_request_id(sequence),
        connector_id="CONNECTOR-000001",
        connector_version="0.1.0",
        subject_id="SUBJECT-000001",
        model_identifier="deterministic-mock",
        messages=(
            ConnectorMessage(
                role=MessageRole.SYSTEM,
                content="Return a deterministic response.",
            ),
            ConnectorMessage(
                role=MessageRole.USER,
                content=user_content,
            ),
        ),
        parameters={
            "seed": 20260725,
        },
        response_format={
            "type": "text",
        },
        timeout_seconds=30.0,
        metadata={
            "experiment_id": "EXP-000001",
        },
    )


class RequestIdentifierTests(unittest.TestCase):
    def test_first_identifier(self) -> None:
        self.assertEqual(
            canonical_request_id(1),
            "REQUEST-0000000001",
        )

    def test_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_request_id(0)

    def test_boolean_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_request_id(True)


class ConnectorRequestTests(unittest.TestCase):
    def test_request_hash_is_stable(self) -> None:
        first = build_request()
        second = build_request()

        self.assertEqual(
            first.request_sha256,
            second.request_sha256,
        )
        self.assertEqual(len(first.request_sha256), 64)

    def test_empty_message_list_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ConnectorRequest(
                request_id="REQUEST-0000000001",
                connector_id="CONNECTOR-000001",
                connector_version="0.1.0",
                subject_id="SUBJECT-000001",
                model_identifier="deterministic-mock",
                messages=(),
            )

    def test_nonpositive_timeout_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ConnectorRequest(
                request_id="REQUEST-0000000001",
                connector_id="CONNECTOR-000001",
                connector_version="0.1.0",
                subject_id="SUBJECT-000001",
                model_identifier="deterministic-mock",
                messages=(
                    ConnectorMessage(
                        role=MessageRole.USER,
                        content="Test",
                    ),
                ),
                timeout_seconds=0,
            )


class MockConnectorTests(unittest.TestCase):
    def test_echo_last_user(self) -> None:
        connector = DeterministicMockConnector(
            mode=MockMode.ECHO_LAST_USER,
        )
        response = connector.execute(build_request())

        self.assertEqual(
            response.status,
            ConnectorStatus.SUCCEEDED,
        )
        self.assertEqual(
            response.raw_text,
            "Prime gaps: 2, 4, 2, 4",
        )
        self.assertFalse(
            response.provider_metadata["external_access"]
        )
        self.assertFalse(
            response.provider_metadata["cost_incurred"]
        )

    def test_fixed_response(self) -> None:
        connector = DeterministicMockConnector(
            mode=MockMode.FIXED_RESPONSE,
            fixed_response='{"prediction": 6}',
        )
        response = connector.execute(build_request())

        self.assertEqual(
            response.raw_text,
            '{"prediction": 6}',
        )

    def test_hash_response_is_deterministic(self) -> None:
        connector = DeterministicMockConnector(
            mode=MockMode.DETERMINISTIC_HASH,
        )

        first = connector.execute(build_request())
        second = connector.execute(build_request())

        self.assertEqual(first.raw_text, second.raw_text)
        self.assertEqual(
            first.response_sha256,
            second.response_sha256,
        )

        payload = json.loads(first.raw_text)

        self.assertEqual(
            payload["request_sha256"],
            build_request().request_sha256,
        )
        self.assertTrue(payload["deterministic"])

    def test_structured_prediction(self) -> None:
        connector = DeterministicMockConnector(
            mode=MockMode.STRUCTURED_PREDICTION,
        )
        response = connector.execute(build_request())
        payload = json.loads(response.raw_text)

        self.assertIn("prediction", payload)
        self.assertIn("confidence", payload)
        self.assertFalse(payload["abstain"])
        self.assertEqual(
            payload["connector_mode"],
            "structured_prediction",
        )

    def test_different_input_changes_prediction(self) -> None:
        connector = DeterministicMockConnector(
            mode=MockMode.STRUCTURED_PREDICTION,
        )

        first = json.loads(
            connector.execute(
                build_request(user_content="Input A")
            ).raw_text
        )
        second = json.loads(
            connector.execute(
                build_request(user_content="Input B")
            ).raw_text
        )

        self.assertNotEqual(
            first["prediction"],
            second["prediction"],
        )

    def test_request_connector_mismatch_rejected(self) -> None:
        connector = DeterministicMockConnector()

        request = ConnectorRequest(
            request_id="REQUEST-0000000001",
            connector_id="CONNECTOR-999999",
            connector_version="0.1.0",
            subject_id="SUBJECT-000001",
            model_identifier="deterministic-mock",
            messages=(
                ConnectorMessage(
                    role=MessageRole.USER,
                    content="Test",
                ),
            ),
        )

        with self.assertRaises(ValueError):
            connector.execute(request)

    def test_usage_is_local_measurement(self) -> None:
        connector = DeterministicMockConnector()
        response = connector.execute(build_request())

        self.assertEqual(
            response.usage.usage_source,
            "local_character_count",
        )
        self.assertIsNone(response.usage.total_tokens)

    def test_capabilities(self) -> None:
        connector = DeterministicMockConnector()
        capabilities = connector.capabilities

        self.assertTrue(
            capabilities.supports_system_messages
        )
        self.assertTrue(
            capabilities.supports_structured_output
        )
        self.assertFalse(capabilities.supports_tools)
        self.assertFalse(connector.external_access)
        self.assertEqual(connector.cost_class, "free")


class ConnectorServiceTests(unittest.TestCase):
    def test_register_and_execute(self) -> None:
        service = ConnectorService()
        service.register(
            DeterministicMockConnector(
                mode=MockMode.ECHO_LAST_USER,
            )
        )

        response = service.execute(build_request())

        self.assertEqual(
            response.status,
            ConnectorStatus.SUCCEEDED,
        )

    def test_duplicate_registration_rejected(self) -> None:
        service = ConnectorService()
        service.register(DeterministicMockConnector())

        with self.assertRaises(ValueError):
            service.register(DeterministicMockConnector())

    def test_missing_connector_rejected(self) -> None:
        service = ConnectorService()

        with self.assertRaises(KeyError):
            service.get("CONNECTOR-000001")

    def test_registered_ids_are_sorted(self) -> None:
        service = ConnectorService()
        service.register(DeterministicMockConnector())

        self.assertEqual(
            service.registered_connector_ids(),
            ("CONNECTOR-000001",),
        )


if __name__ == "__main__":
    unittest.main()
