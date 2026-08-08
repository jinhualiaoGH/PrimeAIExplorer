from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from kernel.exceptions import ValidationError

from .contracts import ExperimentDefinition
from .execution_plan import CampaignExecutionPlan
from .identity import sha256_json
from .materialization import ExperimentMaterialization
from .provenance import ProvenanceLink, ScientificProvenance
from .results import CampaignResultRecord, CampaignResultSet
from .runtime import CampaignExecutionRun


@dataclass(frozen=True, slots=True)
class CampaignAssembly:
    result_set: CampaignResultSet
    provenance: ScientificProvenance

    @property
    def assembly_sha256(self) -> str:
        return sha256_json(
            {
                "schema_version": "h6.0",
                "result_set_sha256": self.result_set.result_set_sha256,
                "provenance_sha256": self.provenance.provenance_sha256,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "h6.0",
            "assembly_sha256": self.assembly_sha256,
            "result_set": self.result_set.to_dict(),
            "provenance": self.provenance.to_dict(),
        }


class CampaignResultAssembler:
    def assemble(
        self,
        *,
        experiment: ExperimentDefinition,
        materialization: ExperimentMaterialization,
        plan: CampaignExecutionPlan,
        run: CampaignExecutionRun,
        metadata: Mapping[str, Any] | None = None,
    ) -> CampaignAssembly:
        self._validate_chain(
            experiment=experiment,
            materialization=materialization,
            plan=plan,
            run=run,
        )

        results = tuple(
            CampaignResultRecord.from_execution_record(record)
            for record in run.records
        )

        result_set_seed = {
            "schema_version": "h6.0",
            "experiment_sha256": experiment.experiment_sha256,
            "materialization_sha256": materialization.materialization_sha256,
            "plan_sha256": plan.plan_sha256,
            "run_sha256": run.run_sha256,
            "result_sha256s": sorted(item.result_sha256 for item in results),
        }
        result_set_id = f"RESULTSET-{sha256_json(result_set_seed)[:20].upper()}"

        result_set = CampaignResultSet(
            result_set_id=result_set_id,
            experiment_id=experiment.experiment_id,
            experiment_sha256=experiment.experiment_sha256,
            materialization_sha256=materialization.materialization_sha256,
            plan_id=plan.plan_id,
            plan_sha256=plan.plan_sha256,
            run_id=run.run_id,
            run_sha256=run.run_sha256,
            results=results,
            metadata=dict(metadata or {}),
        )

        links = self._build_links(
            experiment=experiment,
            materialization=materialization,
            plan=plan,
            run=run,
            result_set=result_set,
        )

        provenance_seed = {
            "schema_version": "h6.0",
            "result_set_sha256": result_set.result_set_sha256,
            "link_sha256s": sorted(item.link_sha256 for item in links),
        }

        provenance = ScientificProvenance(
            provenance_id=f"PROV-{sha256_json(provenance_seed)[:20].upper()}",
            experiment_id=experiment.experiment_id,
            experiment_sha256=experiment.experiment_sha256,
            materialization_sha256=materialization.materialization_sha256,
            plan_id=plan.plan_id,
            plan_sha256=plan.plan_sha256,
            run_id=run.run_id,
            run_sha256=run.run_sha256,
            result_set_id=result_set.result_set_id,
            result_set_sha256=result_set.result_set_sha256,
            links=links,
            metadata={
                "phase": "H6",
            },
        )

        return CampaignAssembly(
            result_set=result_set,
            provenance=provenance,
        )

    @staticmethod
    def _validate_chain(
        *,
        experiment: ExperimentDefinition,
        materialization: ExperimentMaterialization,
        plan: CampaignExecutionPlan,
        run: CampaignExecutionRun,
    ) -> None:
        if not isinstance(experiment, ExperimentDefinition):
            raise ValidationError("experiment must be ExperimentDefinition.")
        if not isinstance(materialization, ExperimentMaterialization):
            raise ValidationError("materialization must be ExperimentMaterialization.")
        if not isinstance(plan, CampaignExecutionPlan):
            raise ValidationError("plan must be CampaignExecutionPlan.")
        if not isinstance(run, CampaignExecutionRun):
            raise ValidationError("run must be CampaignExecutionRun.")

        if materialization.experiment_id != experiment.experiment_id:
            raise ValidationError("materialization experiment_id mismatch.")
        if materialization.experiment_sha256 != experiment.experiment_sha256:
            raise ValidationError("materialization experiment_sha256 mismatch.")
        if plan.materialization_sha256 != materialization.materialization_sha256:
            raise ValidationError("plan materialization_sha256 mismatch.")
        if run.plan_id != plan.plan_id:
            raise ValidationError("run plan_id mismatch.")
        if run.plan_sha256 != plan.plan_sha256:
            raise ValidationError("run plan_sha256 mismatch.")

        plan_job_ids = {job.job_id for job in plan.jobs}
        run_job_ids = {record.job_id for record in run.records}
        if plan_job_ids != run_job_ids:
            raise ValidationError("run job set does not match execution plan.")

        jobs = {job.job_id: job for job in plan.jobs}
        for record in run.records:
            job = jobs[record.job_id]
            if record.job_sha256 != job.job_sha256:
                raise ValidationError(f"job_sha256 mismatch for {record.job_id}.")
            if record.case_id != job.case_id:
                raise ValidationError(f"case_id mismatch for {record.job_id}.")
            if record.case_sha256 != job.case_sha256:
                raise ValidationError(f"case_sha256 mismatch for {record.job_id}.")

    @staticmethod
    def _build_links(
        *,
        experiment: ExperimentDefinition,
        materialization: ExperimentMaterialization,
        plan: CampaignExecutionPlan,
        run: CampaignExecutionRun,
        result_set: CampaignResultSet,
    ) -> tuple[ProvenanceLink, ...]:
        links = [
            ProvenanceLink(
                relation="materialized_from",
                subject_type="experiment_materialization",
                subject_id=f"MATERIALIZATION-{materialization.materialization_sha256[:20].upper()}",
                subject_sha256=materialization.materialization_sha256,
                object_type="experiment",
                object_id=experiment.experiment_id,
                object_sha256=experiment.experiment_sha256,
            ),
            ProvenanceLink(
                relation="planned_from",
                subject_type="campaign_execution_plan",
                subject_id=plan.plan_id,
                subject_sha256=plan.plan_sha256,
                object_type="experiment_materialization",
                object_id=f"MATERIALIZATION-{materialization.materialization_sha256[:20].upper()}",
                object_sha256=materialization.materialization_sha256,
            ),
            ProvenanceLink(
                relation="executed_from",
                subject_type="campaign_execution_run",
                subject_id=run.run_id,
                subject_sha256=run.run_sha256,
                object_type="campaign_execution_plan",
                object_id=plan.plan_id,
                object_sha256=plan.plan_sha256,
            ),
            ProvenanceLink(
                relation="assembled_from",
                subject_type="campaign_result_set",
                subject_id=result_set.result_set_id,
                subject_sha256=result_set.result_set_sha256,
                object_type="campaign_execution_run",
                object_id=run.run_id,
                object_sha256=run.run_sha256,
            ),
        ]

        jobs = {job.job_id: job for job in plan.jobs}
        for result in result_set.results:
            job = jobs[result.job_id]
            links.append(
                ProvenanceLink(
                    relation="result_of",
                    subject_type="campaign_result_record",
                    subject_id=result.result_id,
                    subject_sha256=result.result_sha256,
                    object_type="execution_job",
                    object_id=job.job_id,
                    object_sha256=job.job_sha256,
                    metadata={
                        "case_id": job.case_id,
                        "case_sha256": job.case_sha256,
                    },
                )
            )

        return tuple(links)
