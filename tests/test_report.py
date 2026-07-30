"""Tests for the PrimeAIExplorer report foundation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from core.report import (
    ReportSection,
    ReportStatus,
    build_experiment_report,
    canonical_report_artifact_id,
)


class ReportIdentifierTests(unittest.TestCase):
    def test_first_identifier(self) -> None:
        self.assertEqual(
            canonical_report_artifact_id(1),
            "RPT-0000000001",
        )

    def test_larger_identifier(self) -> None:
        self.assertEqual(
            canonical_report_artifact_id(1_234_567),
            "RPT-0001234567",
        )

    def test_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_report_artifact_id(0)

    def test_boolean_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_report_artifact_id(True)


class ReportSectionTests(unittest.TestCase):
    def test_empty_title_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ReportSection(
                section_id="results",
                title="",
                content="Evidence.",
            )


class ScientificReportTests(unittest.TestCase):
    def build_report(self):
        return build_experiment_report(
            sequence=1,
            title="EXP-000001 Pilot Scientific Report",
            authors=["Jinhua Liao"],
            experiment_id="EXP-000001",
            experiment_version="0.1.0",
            sections=[
                ReportSection(
                    section_id="scientific_question",
                    title="Scientific Question",
                    content=(
                        "How does observational memory influence "
                        "generalization?"
                    ),
                ),
                ReportSection(
                    section_id="results",
                    title="Results",
                    content=(
                        "This synthetic report validates the "
                        "report-generation pipeline."
                    ),
                ),
                ReportSection(
                    section_id="limitations",
                    title="Limitations",
                    content=(
                        "No external model call was performed."
                    ),
                ),
            ],
            observation_ids=[
                "OBS-0000000001",
                "OBS-0000000002",
            ],
            evaluation_result_ids=[
                "EVR-0000000001",
                "EVR-0000000002",
            ],
            statistical_summary_ids=[
                "SSR-0000000001",
            ],
        )

    def test_report_identity(self) -> None:
        report = self.build_report()

        self.assertEqual(
            report.report_artifact_id,
            "RPT-0000000001",
        )
        self.assertEqual(
            report.status,
            ReportStatus.GENERATED,
        )

    def test_markdown_rendering(self) -> None:
        report = self.build_report()
        markdown = report.render_markdown()

        self.assertIn(
            "# EXP-000001 Pilot Scientific Report",
            markdown,
        )
        self.assertIn("## Results", markdown)
        self.assertIn("Observations: 2", markdown)
        self.assertIn(
            "Draw conclusions second.",
            markdown,
        )

    def test_evidence_hash_is_stable(self) -> None:
        report = self.build_report()

        first_hash = report.evidence[
            "evidence_manifest_sha256"
        ]

        second_report = self.build_report()
        second_hash = second_report.evidence[
            "evidence_manifest_sha256"
        ]

        self.assertEqual(first_hash, second_hash)
        self.assertEqual(len(first_hash), 64)

    def test_report_hash_is_stable_after_refinalize(self) -> None:
        report = self.build_report()

        first_manifest_hash = report.integrity[
            "report_manifest_sha256"
        ]
        first_markdown_hash = report.integrity[
            "markdown_sha256"
        ]

        report.finalize_integrity()

        self.assertEqual(
            first_manifest_hash,
            report.integrity["report_manifest_sha256"],
        )
        self.assertEqual(
            first_markdown_hash,
            report.integrity["markdown_sha256"],
        )

    def test_json_round_trip(self) -> None:
        report = self.build_report()
        payload = json.loads(report.to_json())

        self.assertEqual(
            payload["report_artifact_id"],
            "RPT-0000000001",
        )
        self.assertEqual(payload["status"], "generated")
        self.assertEqual(
            payload["experiment"]["experiment_id"],
            "EXP-000001",
        )

    def test_atomic_write(self) -> None:
        report = self.build_report()

        with tempfile.TemporaryDirectory() as directory:
            paths = report.write_atomic(directory)

            self.assertTrue(paths["markdown"].exists())
            self.assertTrue(paths["manifest"].exists())

            self.assertFalse(
                Path(str(paths["markdown"]) + ".tmp").exists()
            )
            self.assertFalse(
                Path(str(paths["manifest"]) + ".tmp").exists()
            )

            payload = json.loads(
                paths["manifest"].read_text(encoding="utf-8")
            )

            self.assertEqual(
                payload["report_artifact_id"],
                "RPT-0000000001",
            )

    def test_sections_required(self) -> None:
        with self.assertRaises(ValueError):
            build_experiment_report(
                sequence=2,
                title="Invalid Report",
                authors=[],
                experiment_id="EXP-000001",
                experiment_version="0.1.0",
                sections=[],
                observation_ids=[],
                evaluation_result_ids=[],
                statistical_summary_ids=[],
            )


if __name__ == "__main__":
    unittest.main()
