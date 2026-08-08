from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .analysis_contracts import CampaignAnalysisReport
from .identity import canonical_metadata, sha256_json
from .validation import require_text


@dataclass(frozen=True, slots=True)
class CampaignAnalysisManifest:
    report_id: str
    report_sha256: str
    result_set_id: str
    result_set_sha256: str
    provenance_sha256: str
    observation_count: int
    analysis_sha256s: tuple[str, ...]
    provider_models: tuple[str, ...]
    source: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "report_id",
            "report_sha256",
            "result_set_id",
            "result_set_sha256",
            "provenance_sha256",
            "source",
        ):
            object.__setattr__(self, name, require_text(name, getattr(self, name)))

        if (
            isinstance(self.observation_count, bool)
            or not isinstance(self.observation_count, int)
            or self.observation_count < 0
        ):
            raise ValidationError("observation_count must be a non-negative integer.")

        digests = tuple(
            require_text("analysis_sha256", item)
            for item in self.analysis_sha256s
        )
        if len(digests) != self.observation_count:
            raise ValidationError(
                "analysis_sha256s count must equal observation_count."
            )
        if len(set(digests)) != len(digests):
            raise ValidationError("analysis_sha256s contains duplicates.")
        object.__setattr__(self, "analysis_sha256s", tuple(sorted(digests)))

        provider_models = tuple(
            require_text("provider_model", item)
            for item in self.provider_models
        )
        if len(set(provider_models)) != len(provider_models):
            raise ValidationError("provider_models contains duplicates.")
        object.__setattr__(self, "provider_models", tuple(sorted(provider_models)))

        if not isinstance(self.metadata, Mapping):
            raise ValidationError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", canonical_metadata(self.metadata))

    @classmethod
    def from_report(
        cls,
        report: CampaignAnalysisReport,
        *,
        source: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "CampaignAnalysisManifest":
        if not isinstance(report, CampaignAnalysisReport):
            raise ValidationError("report must be CampaignAnalysisReport.")

        return cls(
            report_id=report.report_id,
            report_sha256=report.report_sha256,
            result_set_id=report.result_set_id,
            result_set_sha256=report.result_set_sha256,
            provenance_sha256=report.provenance_sha256,
            observation_count=report.observation_count,
            analysis_sha256s=tuple(
                item.analysis_sha256 for item in report.analyses
            ),
            provider_models=tuple(
                f"{item.provider}/{item.model}"
                for item in report.summaries
            ),
            source=source,
            metadata=dict(metadata or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h7.0",
            "report_id": self.report_id,
            "report_sha256": self.report_sha256,
            "result_set_id": self.result_set_id,
            "result_set_sha256": self.result_set_sha256,
            "provenance_sha256": self.provenance_sha256,
            "observation_count": self.observation_count,
            "analysis_sha256s": list(self.analysis_sha256s),
            "provider_models": list(self.provider_models),
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @property
    def manifest_sha256(self) -> str:
        return sha256_json(self.to_dict())
