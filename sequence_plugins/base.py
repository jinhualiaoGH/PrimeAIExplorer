from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import hashlib
import json
import os
import tempfile


JsonMapping = Mapping[str, Any]


@dataclass(frozen=True)
class DatasetMetadata:
    plugin_id: str
    plugin_version: str
    count: int
    dtype: str
    representation: str
    source: str
    sha256: str
    minimum: int | None
    maximum: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaseRecord:
    case_id: str
    plugin_id: str
    representation: str
    observation: tuple[int, ...]
    target: int
    metadata: Mapping[str, Any]

    def to_dict(self, *, include_target: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {
            "case_id": self.case_id,
            "plugin_id": self.plugin_id,
            "representation": self.representation,
            "observation": list(self.observation),
            "metadata": dict(self.metadata),
        }
        if include_target:
            result["target"] = self.target
        return result


@dataclass(frozen=True)
class PredictionEvaluation:
    prediction: int | None
    target: int
    exact: bool
    absolute_error: int | None
    structurally_valid: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SequencePlugin(ABC):
    """Stable contract for deterministic numerical sequence plugins."""

    plugin_id: str
    plugin_version: str = "1.0.0"
    display_name: str
    supported_representations: tuple[str, ...] = ("absolute",)

    def describe(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "display_name": self.display_name,
            "supported_representations": list(
                self.supported_representations
            ),
            "module": self.__class__.__module__,
            "class": self.__class__.__name__,
        }

    def validate_representation(self, representation: str) -> None:
        if representation not in self.supported_representations:
            supported = ", ".join(self.supported_representations)
            raise ValueError(
                f"{self.plugin_id} does not support representation "
                f"{representation!r}; supported: {supported}"
            )

    @abstractmethod
    def validate_source(
        self,
        source: Path,
        *,
        required_count: int | None = None,
        options: JsonMapping | None = None,
    ) -> dict[str, Any]:
        """Validate source availability without mutating it."""

    @abstractmethod
    def build_dataset(
        self,
        source: Path,
        destination: Path,
        *,
        count: int,
        options: JsonMapping | None = None,
    ) -> DatasetMetadata:
        """Build a canonical dataset atomically."""

    @abstractmethod
    def load_values(
        self,
        dataset: Path,
        *,
        mmap_mode: str | None = "r",
    ) -> Sequence[int]:
        """Load values from a canonical dataset."""

    def validate_dataset(
        self,
        dataset: Path,
        *,
        representation: str = "absolute",
    ) -> dict[str, Any]:
        self.validate_representation(representation)
        values = self.load_values(dataset)
        count = len(values)
        if count == 0:
            raise ValueError(f"Dataset is empty: {dataset}")

        previous = int(values[0])
        for index in range(1, count):
            current = int(values[index])
            if current <= previous:
                raise ValueError(
                    f"Dataset is not strictly increasing at index {index}: "
                    f"{previous}, {current}"
                )
            previous = current

        return {
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "dataset": str(dataset),
            "count": count,
            "minimum": int(values[0]),
            "maximum": int(values[-1]),
            "representation": representation,
            "valid": True,
        }

    def transform_window(
        self,
        absolute_values: Sequence[int],
        representation: str,
    ) -> tuple[int, ...]:
        self.validate_representation(representation)
        values = tuple(int(value) for value in absolute_values)

        if representation == "absolute":
            return values
        if representation == "gaps":
            return tuple(
                values[index + 1] - values[index]
                for index in range(len(values) - 1)
            )
        if representation == "combined":
            gaps = tuple(
                values[index + 1] - values[index]
                for index in range(len(values) - 1)
            )
            return values + gaps

        raise ValueError(f"Unsupported representation: {representation}")

    def target_for_representation(
        self,
        absolute_values: Sequence[int],
        target_value: int,
        representation: str,
    ) -> int:
        self.validate_representation(representation)
        if representation in {"absolute", "combined"}:
            return int(target_value)
        if representation == "gaps":
            if not absolute_values:
                raise ValueError("Gap target requires an observed value.")
            return int(target_value) - int(absolute_values[-1])
        raise ValueError(f"Unsupported representation: {representation}")

    def generate_cases(
        self,
        values: Sequence[int],
        *,
        endpoints: Iterable[int],
        window_size: int,
        representation: str,
        experiment_id: str,
    ) -> list[CaseRecord]:
        self.validate_representation(representation)
        if window_size <= 0:
            raise ValueError("window_size must be positive.")

        cases: list[CaseRecord] = []
        for ordinal, endpoint in enumerate(endpoints, start=1):
            endpoint = int(endpoint)
            start = endpoint - window_size
            if start < 0:
                raise ValueError(
                    f"Endpoint {endpoint} is too small for window "
                    f"{window_size}."
                )
            if endpoint >= len(values):
                raise ValueError(
                    f"Endpoint {endpoint} requires target index {endpoint}, "
                    f"but dataset count is {len(values)}."
                )

            absolute = tuple(
                int(values[index]) for index in range(start, endpoint)
            )
            raw_target = int(values[endpoint])
            observation = self.transform_window(
                absolute,
                representation,
            )
            target = self.target_for_representation(
                absolute,
                raw_target,
                representation,
            )

            case_id = f"{experiment_id}-CASE-{ordinal:06d}"
            cases.append(
                CaseRecord(
                    case_id=case_id,
                    plugin_id=self.plugin_id,
                    representation=representation,
                    observation=observation,
                    target=target,
                    metadata={
                        "absolute_start_index_zero_based": start,
                        "absolute_target_index_zero_based": endpoint,
                        "window_size": window_size,
                        "absolute_last_value": absolute[-1],
                        "absolute_target_value": raw_target,
                    },
                )
            )
        return cases

    def render_prompt(
        self,
        case: CaseRecord,
        *,
        disclose_definition: bool = False,
    ) -> str:
        definition = (
            f"\nSequence: {self.display_name}."
            if disclose_definition
            else ""
        )
        observed = " ".join(str(value) for value in case.observation)
        return (
            "You are participating in a controlled numerical continuation "
            f"experiment.{definition}\n\n"
            f"Representation: {case.representation}\n"
            f"Observed values:\n{observed}\n\n"
            "Predict the next value.\n\n"
            "Return JSON only using this exact structure:\n"
            "{\n"
            '  "prediction": <integer>,\n'
            '  "confidence": <integer from 0 to 100>,\n'
            '  "explanation": "<brief explanation>"\n'
            "}\n"
        )

    def is_structurally_valid(self, value: int) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    def evaluate_prediction(
        self,
        prediction: Any,
        target: int,
    ) -> PredictionEvaluation:
        if isinstance(prediction, bool):
            parsed: int | None = None
        elif isinstance(prediction, int):
            parsed = prediction
        elif isinstance(prediction, str):
            try:
                parsed = int(prediction.strip())
            except ValueError:
                parsed = None
        else:
            parsed = None

        if parsed is None:
            return PredictionEvaluation(
                prediction=None,
                target=int(target),
                exact=False,
                absolute_error=None,
                structurally_valid=False,
                reason="prediction is not an integer",
            )

        structural = self.is_structurally_valid(parsed)
        return PredictionEvaluation(
            prediction=parsed,
            target=int(target),
            exact=parsed == int(target),
            absolute_error=abs(parsed - int(target)),
            structurally_valid=structural,
            reason="valid" if structural else "plugin structural check failed",
        )


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
