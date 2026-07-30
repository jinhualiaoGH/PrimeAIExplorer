"""PrimeAIExplorer canonical evaluation reference implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import platform
import re
from typing import Any, Iterable, Mapping
import unicodedata


EVALUATION_SCHEMA_VERSION = "0.4.0"
PRIME_AI_EXPLORER_VERSION = "0.4.0"
EVALUATOR_IMPLEMENTATION_VERSION = "0.4.0"


class EvaluationStatus(StrEnum):
    """Canonical evaluation lifecycle status."""

    PENDING = "pending"
    RUNNING = "running"
    VALID = "valid"
    INVALID = "invalid"
    SCORED = "scored"
    REVIEW_REQUIRED = "review_required"
    REVIEWED = "reviewed"
    FAILED = "failed"
    EXCLUDED_WITH_REASON = "excluded_with_reason"
    SUPERSEDED = "superseded"


class MetricStatus(StrEnum):
    """Canonical metric-computation status."""

    COMPUTED = "computed"
    NOT_APPLICABLE = "not_applicable"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


class MetricRole(StrEnum):
    """Scientific role of a metric."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    DIAGNOSTIC = "diagnostic"
    EXPLORATORY = "exploratory"
    QUALITY_CONTROL = "quality_control"


def utc_now_iso() -> str:
    """Return a stable UTC timestamp."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    """Serialize a value deterministically."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    """Return the SHA-256 digest of UTF-8 text."""

    return sha256(value.encode("utf-8")).hexdigest()


def canonical_evaluation_result_id(sequence: int) -> str:
    """Convert a positive integer to EVR-NNNNNNNNNN form."""

    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("Evaluation-result sequence must be an integer.")

    if sequence < 1 or sequence > 9_999_999_999:
        raise ValueError(
            "Evaluation-result sequence must be between 1 and 9,999,999,999."
        )

    return f"EVR-{sequence:010d}"


def normalize_text(
    value: str,
    *,
    strip: bool = True,
    casefold: bool = False,
    collapse_whitespace: bool = False,
    unicode_form: str = "NFC",
) -> str:
    """Normalize text under an explicit deterministic policy."""

    if not isinstance(value, str):
        raise TypeError("Text normalization requires a string.")

    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    normalized = unicodedata.normalize(unicode_form, normalized)

    if strip:
        normalized = normalized.strip()

    if collapse_whitespace:
        normalized = re.sub(r"\s+", " ", normalized)

    if casefold:
        normalized = normalized.casefold()

    return normalized


def parse_decimal(value: Any) -> Decimal:
    """Parse a finite numeric value into Decimal."""

    if isinstance(value, bool):
        raise TypeError("Boolean values are not numeric predictions.")

    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Numeric values must be finite.")
        result = Decimal(str(value))
    elif isinstance(value, str):
        text = value.strip()

        if not text:
            raise ValueError("Numeric text is empty.")

        try:
            result = Decimal(text)
        except InvalidOperation as error:
            raise ValueError(f"Invalid numeric value: {value!r}") from error
    else:
        raise TypeError(
            "Numeric values must be int, float, Decimal, or numeric text."
        )

    if not result.is_finite():
        raise ValueError("Numeric values must be finite.")

    return result


@dataclass(frozen=True, slots=True)
class MetricResult:
    """One canonical metric result."""

    metric_id: str
    name: str
    role: MetricRole
    value: int | float | str | bool | None
    unit: str | None
    higher_is_better: bool | None
    status: MetricStatus = MetricStatus.COMPUTED
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["role"] = self.role.value
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class EvaluationRecord:
    """Canonical evaluation result derived from one observation."""

    evaluation_result_id: str
    status: EvaluationStatus
    created_at_utc: str
    observation: dict[str, Any]
    evaluator: dict[str, Any]
    configuration: dict[str, Any]
    validity: dict[str, Any]
    metrics: list[MetricResult]

    evaluation_schema_version: str = EVALUATION_SCHEMA_VERSION
    started_at_utc: str | None = None
    completed_at_utc: str | None = None
    review: dict[str, Any] = field(default_factory=dict)
    exclusion: dict[str, Any] = field(default_factory=dict)
    integrity: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, include_result_hash: bool = True) -> dict[str, Any]:
        value = {
            "evaluation_result_id": self.evaluation_result_id,
            "evaluation_schema_version": self.evaluation_schema_version,
            "status": self.status.value,
            "created_at_utc": self.created_at_utc,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "observation": dict(self.observation),
            "evaluator": dict(self.evaluator),
            "configuration": dict(self.configuration),
            "validity": dict(self.validity),
            "metrics": [metric.to_dict() for metric in self.metrics],
            "review": dict(self.review),
            "exclusion": dict(self.exclusion),
            "integrity": dict(self.integrity),
            "environment": dict(self.environment),
            "provenance": dict(self.provenance),
        }

        if not include_result_hash:
            value["integrity"] = {
                key: item
                for key, item in value["integrity"].items()
                if key != "result_sha256"
            }

        return value

    def finalize_integrity(self) -> None:
        """Calculate a stable hash without recursively hashing itself."""

        payload = canonical_json(
            self.to_dict(include_result_hash=False)
        )

        self.integrity["algorithm"] = "SHA-256"
        self.integrity["result_sha256"] = sha256_text(payload)

    def to_json(self, *, pretty: bool = True) -> str:
        if not self.integrity.get("result_sha256"):
            self.finalize_integrity()

        value = self.to_dict()

        if pretty:
            return json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )

        return canonical_json(value)

    def write_atomic(self, path: str | Path) -> Path:
        """Write the evaluation atomically."""

        final_path = Path(path)
        final_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = final_path.with_name(final_path.name + ".tmp")
        payload = self.to_json(pretty=True) + "\n"

        try:
            with temporary_path.open(
                "w",
                encoding="utf-8",
                newline="\n",
            ) as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())

            temporary_path.replace(final_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        return final_path


def _base_record(
    *,
    sequence: int,
    observation_id: str,
    observation_schema_version: str,
    response_sha256: str | None,
    evaluator_id: str,
    evaluator_version: str,
    evaluator_name: str,
    configuration: Mapping[str, Any],
    validity: Mapping[str, Any],
    metrics: Iterable[MetricResult],
) -> EvaluationRecord:
    timestamp = utc_now_iso()
    configuration_value = dict(configuration)
    configuration_hash = sha256_text(
        canonical_json(configuration_value)
    )

    record = EvaluationRecord(
        evaluation_result_id=canonical_evaluation_result_id(sequence),
        status=EvaluationStatus.SCORED,
        created_at_utc=timestamp,
        started_at_utc=timestamp,
        completed_at_utc=timestamp,
        observation={
            "observation_id": observation_id,
            "observation_schema_version": observation_schema_version,
            "response_sha256": response_sha256,
        },
        evaluator={
            "evaluator_id": evaluator_id,
            "evaluator_version": evaluator_version,
            "name": evaluator_name,
            "evaluator_type": "deterministic",
            "implementation_version": EVALUATOR_IMPLEMENTATION_VERSION,
        },
        configuration={
            **configuration_value,
            "configuration_sha256": configuration_hash,
        },
        validity=dict(validity),
        metrics=list(metrics),
        review={
            "required": False,
            "completed": False,
        },
        exclusion={
            "excluded": False,
            "reason": None,
        },
        integrity={
            "algorithm": "SHA-256",
            "result_sha256": "",
        },
        environment={
            "primeaiexplorer_version": PRIME_AI_EXPLORER_VERSION,
            "python_version": platform.python_version(),
            "operating_system": platform.system(),
            "platform": platform.platform(),
        },
        provenance={
            "source_observation_id": observation_id,
            "evaluation_timestamp_utc": timestamp,
        },
    )

    record.finalize_integrity()
    return record


def evaluate_exact_match(
    *,
    sequence: int,
    observation_id: str,
    observation_schema_version: str,
    response_sha256: str | None,
    prediction: str,
    expected: str,
    casefold: bool = False,
    collapse_whitespace: bool = False,
) -> EvaluationRecord:
    """Evaluate normalized exact textual equality."""

    normalized_prediction = normalize_text(
        prediction,
        casefold=casefold,
        collapse_whitespace=collapse_whitespace,
    )
    normalized_expected = normalize_text(
        expected,
        casefold=casefold,
        collapse_whitespace=collapse_whitespace,
    )

    matched = normalized_prediction == normalized_expected

    metric = MetricResult(
        metric_id="METRIC-000001",
        name="exact_match_accuracy",
        role=MetricRole.PRIMARY,
        value=1.0 if matched else 0.0,
        unit="proportion",
        higher_is_better=True,
        details={
            "matched": matched,
            "normalized_prediction_sha256": sha256_text(
                normalized_prediction
            ),
            "normalized_expected_sha256": sha256_text(
                normalized_expected
            ),
        },
    )

    return _base_record(
        sequence=sequence,
        observation_id=observation_id,
        observation_schema_version=observation_schema_version,
        response_sha256=response_sha256,
        evaluator_id="EVAL-000001",
        evaluator_version="0.1.0",
        evaluator_name="Exact Match Evaluator",
        configuration={
            "strip": True,
            "unicode_form": "NFC",
            "casefold": casefold,
            "collapse_whitespace": collapse_whitespace,
        },
        validity={
            "is_valid": True,
            "reason": None,
        },
        metrics=[metric],
    )


def evaluate_numeric_error(
    *,
    sequence: int,
    observation_id: str,
    observation_schema_version: str,
    response_sha256: str | None,
    prediction: Any,
    expected: Any,
) -> EvaluationRecord:
    """Evaluate absolute and relative numeric error."""

    predicted_value = parse_decimal(prediction)
    expected_value = parse_decimal(expected)

    absolute_error = abs(predicted_value - expected_value)

    if expected_value == 0:
        relative_error: Decimal | None = (
            Decimal(0) if absolute_error == 0 else None
        )
        relative_status = (
            MetricStatus.COMPUTED
            if relative_error is not None
            else MetricStatus.NOT_APPLICABLE
        )
    else:
        relative_error = absolute_error / abs(expected_value)
        relative_status = MetricStatus.COMPUTED

    absolute_metric = MetricResult(
        metric_id="METRIC-000002",
        name="numeric_absolute_error",
        role=MetricRole.PRIMARY,
        value=float(absolute_error),
        unit=None,
        higher_is_better=False,
        details={
            "prediction": str(predicted_value),
            "expected": str(expected_value),
        },
    )

    relative_metric = MetricResult(
        metric_id="METRIC-000003",
        name="numeric_relative_error",
        role=MetricRole.SECONDARY,
        value=(
            float(relative_error)
            if relative_error is not None
            else None
        ),
        unit="proportion",
        higher_is_better=False,
        status=relative_status,
        details={
            "zero_target_policy": (
                "zero_when_exact_otherwise_not_applicable"
            ),
        },
    )

    return _base_record(
        sequence=sequence,
        observation_id=observation_id,
        observation_schema_version=observation_schema_version,
        response_sha256=response_sha256,
        evaluator_id="EVAL-000002",
        evaluator_version="0.1.0",
        evaluator_name="Numeric Error Evaluator",
        configuration={
            "parser": "decimal",
            "finite_values_required": True,
            "zero_target_policy": (
                "zero_when_exact_otherwise_not_applicable"
            ),
        },
        validity={
            "is_valid": True,
            "reason": None,
        },
        metrics=[absolute_metric, relative_metric],
    )


def evaluate_required_json_fields(
    *,
    sequence: int,
    observation_id: str,
    observation_schema_version: str,
    response_sha256: str | None,
    raw_text: str,
    required_fields: Iterable[str],
) -> EvaluationRecord:
    """Validate that JSON text is an object with required fields."""

    fields = tuple(required_fields)
    parsed: Any = None
    reason: str | None = None
    is_valid = False

    try:
        parsed = json.loads(raw_text)

        if not isinstance(parsed, dict):
            reason = "Response JSON must be an object."
        else:
            missing = [
                field_name
                for field_name in fields
                if field_name not in parsed
            ]

            if missing:
                reason = (
                    "Missing required fields: "
                    + ", ".join(sorted(missing))
                )
            else:
                is_valid = True
    except json.JSONDecodeError as error:
        reason = (
            f"Invalid JSON at line {error.lineno}, "
            f"column {error.colno}."
        )

    metric = MetricResult(
        metric_id="METRIC-000004",
        name="response_validity",
        role=MetricRole.QUALITY_CONTROL,
        value=1.0 if is_valid else 0.0,
        unit="proportion",
        higher_is_better=True,
        details={
            "required_fields": list(fields),
            "parsed_type": (
                type(parsed).__name__
                if parsed is not None
                else None
            ),
        },
    )

    record = _base_record(
        sequence=sequence,
        observation_id=observation_id,
        observation_schema_version=observation_schema_version,
        response_sha256=response_sha256,
        evaluator_id="EVAL-000003",
        evaluator_version="0.1.0",
        evaluator_name="Structured Response Validity Evaluator",
        configuration={
            "required_fields": list(fields),
            "root_type": "object",
        },
        validity={
            "is_valid": is_valid,
            "reason": reason,
        },
        metrics=[metric],
    )

    record.status = (
        EvaluationStatus.SCORED
        if is_valid
        else EvaluationStatus.INVALID
    )
    record.finalize_integrity()
    return record


__all__ = [
    "EvaluationRecord",
    "EvaluationStatus",
    "MetricResult",
    "MetricRole",
    "MetricStatus",
    "canonical_evaluation_result_id",
    "canonical_json",
    "evaluate_exact_match",
    "evaluate_numeric_error",
    "evaluate_required_json_fields",
    "normalize_text",
    "parse_decimal",
    "sha256_text",
    "utc_now_iso",
]
