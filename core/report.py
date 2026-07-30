"""PrimeAIExplorer canonical scientific report implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
from typing import Any, Iterable, Mapping, Sequence


REPORT_SCHEMA_VERSION = "0.6.0"
PRIME_AI_EXPLORER_VERSION = "0.6.0"
REPORT_GENERATOR_VERSION = "0.6.0"


class ReportStatus(StrEnum):
    DRAFT = "draft"
    GENERATED = "generated"
    VALIDATION = "validation"
    REVIEW_REQUIRED = "review_required"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    RELEASED = "released"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def canonical_report_artifact_id(sequence: int) -> str:
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise TypeError("Report sequence must be an integer.")

    if sequence < 1 or sequence > 9_999_999_999:
        raise ValueError(
            "Report sequence must be between 1 and 9,999,999,999."
        )

    return f"RPT-{sequence:010d}"


@dataclass(frozen=True, slots=True)
class ReportSection:
    section_id: str
    title: str
    content: str

    def __post_init__(self) -> None:
        if not self.section_id.strip():
            raise ValueError("Section ID cannot be empty.")

        if not self.title.strip():
            raise ValueError("Section title cannot be empty.")

    def to_dict(self) -> dict[str, str]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "content": self.content,
        }


@dataclass(slots=True)
class ScientificReport:
    report_artifact_id: str
    report_definition: dict[str, Any]
    status: ReportStatus
    created_at_utc: str
    title: str
    authors: list[str]
    experiment: dict[str, str]
    sections: list[ReportSection]
    evidence: dict[str, Any]

    report_schema_version: str = REPORT_SCHEMA_VERSION
    integrity: dict[str, str] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def render_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"Report ID: {self.report_artifact_id}",
            f"Status: {self.status.value}",
            (
                "Experiment: "
                f"{self.experiment['experiment_id']} "
                f"v{self.experiment['experiment_version']}"
            ),
            "",
        ]

        if self.authors:
            lines.extend(
                [
                    "Authors: " + ", ".join(self.authors),
                    "",
                ]
            )

        for section in self.sections:
            lines.extend(
                [
                    f"## {section.title}",
                    "",
                    section.content.rstrip(),
                    "",
                ]
            )

        lines.extend(
            [
                "## Evidence",
                "",
                (
                    "Observations: "
                    f"{len(self.evidence['observation_ids'])}"
                ),
                (
                    "Evaluation results: "
                    f"{len(self.evidence['evaluation_result_ids'])}"
                ),
                (
                    "Statistical summaries: "
                    f"{len(self.evidence['statistical_summary_ids'])}"
                ),
                "",
                "Make observations first.",
                "",
                "Draw conclusions second.",
                "",
            ]
        )

        return "\n".join(lines)

    def to_dict(
        self,
        *,
        include_manifest_hash: bool = True,
    ) -> dict[str, Any]:
        value = {
            "report_artifact_id": self.report_artifact_id,
            "report_schema_version": self.report_schema_version,
            "report_definition": dict(self.report_definition),
            "status": self.status.value,
            "created_at_utc": self.created_at_utc,
            "title": self.title,
            "authors": list(self.authors),
            "experiment": dict(self.experiment),
            "sections": [
                section.to_dict()
                for section in self.sections
            ],
            "evidence": dict(self.evidence),
            "integrity": dict(self.integrity),
            "environment": dict(self.environment),
            "provenance": dict(self.provenance),
        }

        if not include_manifest_hash:
            value["integrity"] = {
                key: item
                for key, item in value["integrity"].items()
                if key != "report_manifest_sha256"
            }

        return value

    def finalize_integrity(self) -> None:
        markdown = self.render_markdown()

        self.integrity["algorithm"] = "SHA-256"
        self.integrity["markdown_sha256"] = sha256_text(markdown)

        manifest_payload = canonical_json(
            self.to_dict(include_manifest_hash=False)
        )

        self.integrity["report_manifest_sha256"] = sha256_text(
            manifest_payload
        )

    def to_json(self, *, pretty: bool = True) -> str:
        if not self.integrity.get("report_manifest_sha256"):
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

    def write_atomic(self, directory: str | Path) -> dict[str, Path]:
        output_directory = Path(directory)
        output_directory.mkdir(parents=True, exist_ok=True)

        self.finalize_integrity()

        markdown_path = output_directory / "scientific_report.md"
        manifest_path = output_directory / "report_manifest.json"

        artifacts = {
            markdown_path: self.render_markdown() + "\n",
            manifest_path: self.to_json(pretty=True) + "\n",
        }

        temporary_paths: list[Path] = []

        try:
            for final_path, payload in artifacts.items():
                temporary_path = final_path.with_name(
                    final_path.name + ".tmp"
                )
                temporary_paths.append(temporary_path)

                with temporary_path.open(
                    "w",
                    encoding="utf-8",
                    newline="\n",
                ) as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())

            for final_path in artifacts:
                temporary_path = final_path.with_name(
                    final_path.name + ".tmp"
                )
                temporary_path.replace(final_path)
        except Exception:
            for temporary_path in temporary_paths:
                temporary_path.unlink(missing_ok=True)
            raise

        return {
            "markdown": markdown_path,
            "manifest": manifest_path,
        }


def build_experiment_report(
    *,
    sequence: int,
    title: str,
    authors: Sequence[str],
    experiment_id: str,
    experiment_version: str,
    sections: Iterable[ReportSection],
    observation_ids: Iterable[str],
    evaluation_result_ids: Iterable[str],
    statistical_summary_ids: Iterable[str],
) -> ScientificReport:
    section_list = list(sections)

    if not section_list:
        raise ValueError("At least one report section is required.")

    observation_list = list(observation_ids)
    evaluation_list = list(evaluation_result_ids)
    statistical_list = list(statistical_summary_ids)

    evidence_payload = {
        "observation_ids": observation_list,
        "evaluation_result_ids": evaluation_list,
        "statistical_summary_ids": statistical_list,
    }

    timestamp = utc_now_iso()

    report = ScientificReport(
        report_artifact_id=canonical_report_artifact_id(sequence),
        report_definition={
            "report_definition_id": "REPORT-000001",
            "report_definition_version": "0.1.0",
            "report_type": "experiment",
        },
        status=ReportStatus.GENERATED,
        created_at_utc=timestamp,
        title=title,
        authors=list(authors),
        experiment={
            "experiment_id": experiment_id,
            "experiment_version": experiment_version,
        },
        sections=section_list,
        evidence={
            **evidence_payload,
            "evidence_manifest_sha256": sha256_text(
                canonical_json(evidence_payload)
            ),
        },
        integrity={
            "algorithm": "SHA-256",
            "report_manifest_sha256": "",
            "markdown_sha256": "",
        },
        environment={
            "primeaiexplorer_version": PRIME_AI_EXPLORER_VERSION,
            "python_version": platform.python_version(),
            "operating_system": platform.system(),
            "platform": platform.platform(),
        },
        provenance={
            "generated_at_utc": timestamp,
            "generator_version": REPORT_GENERATOR_VERSION,
        },
    )

    report.finalize_integrity()
    return report


__all__ = [
    "ReportSection",
    "ReportStatus",
    "ScientificReport",
    "build_experiment_report",
    "canonical_json",
    "canonical_report_artifact_id",
    "sha256_text",
    "utc_now_iso",
]
