"""Automatic campaign orchestration loop."""

from __future__ import annotations

import time
from pathlib import Path

from benchmark_campaign.manager import CampaignManager

from .executors import WorkItemExecutor
from .models import (
    OrchestratorConfiguration,
    OrchestratorSummary,
)
from .store import OrchestratorStore


class OrchestrationEngine:
    def __init__(
        self,
        *,
        campaign_database: str | Path,
        orchestrator_database: str | Path,
        executor: WorkItemExecutor,
        configuration: OrchestratorConfiguration,
    ) -> None:
        self.campaigns = CampaignManager(campaign_database)
        self.store = OrchestratorStore(orchestrator_database)
        self.executor = executor
        self.configuration = configuration

    def run(self) -> OrchestratorSummary:
        configuration = self.configuration
        recovered = len(
            self.store.recover_expired(configuration.campaign_id)
        )
        claimed = 0
        completed = 0
        failed = 0
        retried = 0
        stopped_reason = "campaign_exhausted"

        self.store.event(
            configuration.campaign_id,
            configuration.worker_id,
            "worker_started",
            None,
            {
                "max_attempts": configuration.max_attempts,
                "max_items": configuration.max_items,
            },
        )

        while True:
            stop_requested, reason = self.store.stop_state(
                configuration.campaign_id
            )
            if stop_requested:
                stopped_reason = reason or "stop_requested"
                break

            if (
                configuration.max_items is not None
                and claimed >= configuration.max_items
            ):
                stopped_reason = "max_items_reached"
                break

            item = self.campaigns.claim_next(
                configuration.campaign_id
            )
            if item is None:
                stopped_reason = "campaign_exhausted"
                break

            lease_acquired = self.store.acquire_lease(
                configuration.campaign_id,
                item,
                worker_id=configuration.worker_id,
                lease_seconds=configuration.lease_seconds,
            )

            if not lease_acquired:
                self.campaigns.fail(
                    configuration.campaign_id,
                    item.work_item_id,
                    error_message=(
                        "Unable to acquire D4 orchestration lease."
                    ),
                )
                failed += 1
                if configuration.stop_on_failure:
                    stopped_reason = "lease_failure"
                    break
                continue

            claimed += 1
            self.store.event(
                configuration.campaign_id,
                configuration.worker_id,
                "work_item_started",
                item.work_item_id,
                item.to_dict(),
            )

            try:
                outcome = self.executor.execute(item)
            except Exception as error:
                outcome = None
                error_message = (
                    f"{type(error).__name__}: {error}"
                )
            else:
                error_message = (
                    outcome.error_message if not outcome.success else None
                )

            if outcome is not None and outcome.success:
                self.campaigns.complete(
                    configuration.campaign_id,
                    item.work_item_id,
                    experiment_id=outcome.experiment_id or "",
                    catalog_record_id=outcome.catalog_record_id,
                )
                completed += 1
                self.store.event(
                    configuration.campaign_id,
                    configuration.worker_id,
                    "work_item_completed",
                    item.work_item_id,
                    outcome.to_dict(),
                )
            else:
                message = error_message or "Unknown execution failure."
                self.campaigns.fail(
                    configuration.campaign_id,
                    item.work_item_id,
                    error_message=message,
                )
                failed += 1
                self.store.event(
                    configuration.campaign_id,
                    configuration.worker_id,
                    "work_item_failed",
                    item.work_item_id,
                    {"error_message": message},
                )

                current_attempt = item.attempts
                if current_attempt < configuration.max_attempts:
                    reset_count = self.campaigns.reset_failed(
                        configuration.campaign_id
                    )
                    if reset_count:
                        retried += 1
                        self.store.event(
                            configuration.campaign_id,
                            configuration.worker_id,
                            "work_item_requeued",
                            item.work_item_id,
                            {
                                "attempt": current_attempt,
                                "max_attempts": configuration.max_attempts,
                            },
                        )
                        if configuration.retry_backoff_seconds:
                            time.sleep(
                                configuration.retry_backoff_seconds
                            )
                elif configuration.stop_on_failure:
                    stopped_reason = "max_attempts_failure"

            self.store.release_lease(
                configuration.campaign_id,
                item.work_item_id,
                worker_id=configuration.worker_id,
            )

            if (
                configuration.stop_on_failure
                and failed > 0
                and stopped_reason == "max_attempts_failure"
            ):
                break

            if configuration.poll_seconds:
                time.sleep(configuration.poll_seconds)

        summary = OrchestratorSummary(
            campaign_id=configuration.campaign_id,
            worker_id=configuration.worker_id,
            claimed=claimed,
            completed=completed,
            failed=failed,
            retried=retried,
            recovered_stale_leases=recovered,
            stopped_reason=stopped_reason,
        )
        self.store.event(
            configuration.campaign_id,
            configuration.worker_id,
            "worker_stopped",
            None,
            summary.to_dict(),
        )
        return summary
