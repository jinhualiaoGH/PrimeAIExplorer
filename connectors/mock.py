"""Deterministic free connector for PrimeAIExplorer pipeline validation."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
import json
import time
from typing import Any

from connectors.base import BaseConnector, ConnectorCapabilities
from connectors.models import (
    ConnectorError,
    ConnectorRequest,
    ConnectorResponse,
    ConnectorStatus,
    ConnectorTiming,
    ConnectorUsage,
    MessageRole,
    canonical_json,
    sha256_text,
)


class MockMode(StrEnum):
    ECHO_LAST_USER = "echo_last_user"
    FIXED_RESPONSE = "fixed_response"
    DETERMINISTIC_HASH = "deterministic_hash"
    STRUCTURED_PREDICTION = "structured_prediction"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DeterministicMockConnector(BaseConnector):
    connector_id = "CONNECTOR-000001"
    connector_version = "0.1.0"
    title = "Deterministic Mock Connector"
    connector_type = "deterministic_mock"
    external_access = False
    cost_class = "free"

    def __init__(
        self,
        *,
        mode: MockMode = MockMode.ECHO_LAST_USER,
        fixed_response: str = "",
    ) -> None:
        self.mode = MockMode(mode)
        self.fixed_response = fixed_response

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_system_messages=True,
            supports_developer_messages=True,
            supports_structured_output=True,
            supports_seed=True,
            supports_temperature=False,
            supports_tools=False,
            supports_streaming=False,
            supports_usage_reporting=True,
            supports_exact_model_revision=True,
            maximum_context_tokens=1_000_000,
            maximum_output_tokens=100_000,
        )

    def execute(
        self,
        request: ConnectorRequest,
    ) -> ConnectorResponse:
        self.validate_request(request)

        started_at = utc_now_iso()
        start_clock = time.perf_counter()

        try:
            raw_text = self._generate_response(request)
            status = ConnectorStatus.SUCCEEDED
            finish_reason = "completed"
            refusal = None
            error = ConnectorError()
        except Exception as exception:
            raw_text = None
            status = ConnectorStatus.FAILED
            finish_reason = "error"
            refusal = None
            error = ConnectorError(
                category="mock_connector_error",
                message=str(exception),
                retryable=False,
            )

        latency = time.perf_counter() - start_clock
        completed_at = utc_now_iso()

        input_characters = sum(
            len(message.content)
            for message in request.messages
        )
        output_characters = len(raw_text or "")

        response_hash = (
            sha256_text(raw_text)
            if raw_text is not None
            else None
        )

        return ConnectorResponse(
            request_id=request.request_id,
            connector_id=self.connector_id,
            connector_version=self.connector_version,
            subject_id=request.subject_id,
            model_identifier=request.model_identifier,
            status=status,
            raw_text=raw_text,
            finish_reason=finish_reason,
            refusal=refusal,
            usage=ConnectorUsage(
                input_characters=input_characters,
                output_characters=output_characters,
                input_tokens=None,
                output_tokens=None,
                total_tokens=None,
                usage_source="local_character_count",
            ),
            timing=ConnectorTiming(
                latency_seconds=latency,
                started_at_utc=started_at,
                completed_at_utc=completed_at,
            ),
            provider_metadata={
                "provider": "PrimeAIExplorer",
                "connector_mode": self.mode.value,
                "external_access": False,
                "cost_incurred": False,
                "deterministic_baseline": True,
            },
            error=error,
            request_sha256=request.request_sha256,
            response_sha256=response_hash,
        )

    def _generate_response(
        self,
        request: ConnectorRequest,
    ) -> str:
        if self.mode is MockMode.ECHO_LAST_USER:
            return self._last_user_content(request)

        if self.mode is MockMode.FIXED_RESPONSE:
            return self.fixed_response

        if self.mode is MockMode.DETERMINISTIC_HASH:
            return json.dumps(
                {
                    "request_sha256": request.request_sha256,
                    "connector_mode": self.mode.value,
                    "deterministic": True,
                },
                ensure_ascii=False,
                sort_keys=True,
            )

        if self.mode is MockMode.STRUCTURED_PREDICTION:
            user_content = self._last_user_content(request)
            digest = sha256_text(user_content)
            prediction = int(digest[:8], 16) % 1000

            return json.dumps(
                {
                    "prediction": prediction,
                    "confidence": 1.0,
                    "abstain": False,
                    "explanation": (
                        "Deterministic mock prediction derived from "
                        "the SHA-256 hash of the final user message."
                    ),
                    "connector_mode": self.mode.value,
                },
                ensure_ascii=False,
                sort_keys=True,
            )

        raise RuntimeError(f"Unsupported mock mode: {self.mode}")

    @staticmethod
    def _last_user_content(
        request: ConnectorRequest,
    ) -> str:
        for message in reversed(request.messages):
            if message.role is MessageRole.USER:
                return message.content

        raise ValueError(
            "Echo and structured mock modes require a user message."
        )


__all__ = [
    "DeterministicMockConnector",
    "MockMode",
]
