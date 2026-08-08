from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Protocol

from kernel.exceptions import ValidationError

from .analysis_contracts import (
    AnalysisDisposition,
    BehavioralAnalysisOutcome,
    CampaignAnalysisRecord,
    CampaignAnalysisReport,
    ProviderModelSummary,
)
from .identity import sha256_json
from .result_assembly import CampaignAssembly
from .results import CampaignResultRecord
from .runtime import JobExecutionStatus


class BehavioralAnalyzer(Protocol):
    def __call__(self, result: CampaignResultRecord) -> BehavioralAnalysisOutcome:
        ...


@dataclass(frozen=True, slots=True)
class CampaignAnalysisEngine:
    def analyze(
        self,
        *,
        assembly: CampaignAssembly,
        analyzer: BehavioralAnalyzer | Callable[[CampaignResultRecord], BehavioralAnalysisOutcome],
        metadata: dict | None = None,
    ) -> CampaignAnalysisReport:
        if not isinstance(assembly, CampaignAssembly):
            raise ValidationError("assembly must be CampaignAssembly.")
        if not callable(analyzer):
            raise ValidationError("analyzer must be callable.")

        analyses = tuple(
            self._analyze_result(result=result, analyzer=analyzer)
            for result in assembly.result_set.results
        )
        summaries = self._summarize(analyses)

        report_seed = {
            "schema_version": "h7.0",
            "result_set_sha256": assembly.result_set.result_set_sha256,
            "provenance_sha256": assembly.provenance.provenance_sha256,
            "analysis_sha256s": sorted(item.analysis_sha256 for item in analyses),
            "summaries": [item.to_dict() for item in summaries],
        }

        return CampaignAnalysisReport(
            report_id=f"ANALYSIS-{sha256_json(report_seed)[:20].upper()}",
            result_set_id=assembly.result_set.result_set_id,
            result_set_sha256=assembly.result_set.result_set_sha256,
            provenance_sha256=assembly.provenance.provenance_sha256,
            analyses=analyses,
            summaries=summaries,
            metadata=dict(metadata or {}),
        )

    @staticmethod
    def _analyze_result(
        *,
        result: CampaignResultRecord,
        analyzer: BehavioralAnalyzer | Callable[[CampaignResultRecord], BehavioralAnalysisOutcome],
    ) -> CampaignAnalysisRecord:
        if result.status != JobExecutionStatus.SUCCEEDED:
            outcome = BehavioralAnalysisOutcome(
                disposition=AnalysisDisposition.PROVIDER_ERROR,
                evaluator_id="h7.provider-status",
                metadata={
                    "execution_status": result.status.value,
                    "error_class": result.error_class,
                },
            )
        else:
            outcome = analyzer(result)
            if not isinstance(outcome, BehavioralAnalysisOutcome):
                raise ValidationError(
                    "analyzer must return BehavioralAnalysisOutcome."
                )

        digest = sha256_json(
            {
                "schema_version": "h7.0",
                "result_sha256": result.result_sha256,
                "outcome": outcome.identity_payload(),
            }
        )

        return CampaignAnalysisRecord(
            analysis_id=f"ANALYSIS-RECORD-{digest[:20].upper()}",
            result_id=result.result_id,
            result_sha256=result.result_sha256,
            job_id=result.job_id,
            case_id=result.case_id,
            provider=result.provider,
            model=result.model,
            outcome=outcome,
            metadata={
                "target_id": result.target_id,
                "lane_id": result.lane_id,
                "batch_id": result.batch_id,
            },
        )

    @staticmethod
    def _summarize(
        analyses: tuple[CampaignAnalysisRecord, ...],
    ) -> tuple[ProviderModelSummary, ...]:
        groups: dict[tuple[str, str], list[CampaignAnalysisRecord]] = defaultdict(list)
        for item in analyses:
            groups[(item.provider, item.model)].append(item)

        summaries: list[ProviderModelSummary] = []
        for (provider, model), items in sorted(groups.items()):
            dispositions = [item.outcome.disposition for item in items]
            scores = [
                item.outcome.score
                for item in items
                if item.outcome.score is not None
            ]
            confidences = [
                item.outcome.confidence
                for item in items
                if item.outcome.confidence is not None
            ]

            metric_values: dict[str, list[float]] = defaultdict(list)
            for item in items:
                for name, value in item.outcome.metrics.items():
                    metric_values[name].append(value)

            summaries.append(
                ProviderModelSummary(
                    provider=provider,
                    model=model,
                    observation_count=len(items),
                    passed_count=sum(
                        value == AnalysisDisposition.PASSED
                        for value in dispositions
                    ),
                    failed_count=sum(
                        value == AnalysisDisposition.FAILED
                        for value in dispositions
                    ),
                    indeterminate_count=sum(
                        value == AnalysisDisposition.INDETERMINATE
                        for value in dispositions
                    ),
                    provider_error_count=sum(
                        value == AnalysisDisposition.PROVIDER_ERROR
                        for value in dispositions
                    ),
                    mean_score=(
                        sum(scores) / len(scores)
                        if scores else None
                    ),
                    mean_confidence=(
                        sum(confidences) / len(confidences)
                        if confidences else None
                    ),
                    metrics={
                        name: sum(values) / len(values)
                        for name, values in sorted(metric_values.items())
                    },
                )
            )

        return tuple(summaries)
