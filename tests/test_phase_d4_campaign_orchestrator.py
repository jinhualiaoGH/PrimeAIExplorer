from __future__ import annotations

from benchmark_campaign import CampaignManager, expand_campaign
from benchmark_campaign.specification import build_specification
from campaign_orchestrator import (
    DemoExecutor,
    OrchestrationEngine,
    OrchestratorConfiguration,
)
from campaign_orchestrator.store import OrchestratorStore


def make_campaign(tmp_path, *, item_count=3):
    specification = build_specification(
        name="D4 Fixture",
        description="Automatic orchestration test.",
        dataset_ids=["DS-AAAAAAAAAAAAAAAA"],
        providers=["manual"],
        models_by_provider={"manual": ["fixture"]},
        prompt_templates=["prompt-v1"],
        random_seeds=[1],
        window_sizes=list(range(1, item_count + 1)),
        repeats=1,
    )
    plan = expand_campaign(specification)
    database = tmp_path / "campaigns.sqlite3"
    manager = CampaignManager(database)
    manager.create(plan)
    return specification.campaign_id, database, manager


def test_demo_orchestrator_completes_campaign(tmp_path):
    campaign_id, campaign_database, manager = make_campaign(
        tmp_path,
        item_count=3,
    )
    engine = OrchestrationEngine(
        campaign_database=campaign_database,
        orchestrator_database=tmp_path / "orchestrator.sqlite3",
        executor=DemoExecutor(),
        configuration=OrchestratorConfiguration(
            campaign_id=campaign_id,
            worker_id="worker-a",
        ),
    )

    summary = engine.run()
    status = manager.status(campaign_id)

    assert summary.completed == 3
    assert summary.failed == 0
    assert status.completed == 3
    assert status.pending == 0


def test_max_items_supports_resumption(tmp_path):
    campaign_id, campaign_database, manager = make_campaign(
        tmp_path,
        item_count=4,
    )
    configuration = OrchestratorConfiguration(
        campaign_id=campaign_id,
        worker_id="worker-a",
        max_items=2,
    )
    engine = OrchestrationEngine(
        campaign_database=campaign_database,
        orchestrator_database=tmp_path / "orchestrator.sqlite3",
        executor=DemoExecutor(),
        configuration=configuration,
    )

    first = engine.run()
    second = OrchestrationEngine(
        campaign_database=campaign_database,
        orchestrator_database=tmp_path / "orchestrator.sqlite3",
        executor=DemoExecutor(),
        configuration=configuration,
    ).run()

    assert first.completed == 2
    assert second.completed == 2
    assert manager.status(campaign_id).completed == 4


def test_failure_is_retried_up_to_limit(tmp_path):
    campaign_id, campaign_database, manager = make_campaign(
        tmp_path,
        item_count=2,
    )
    engine = OrchestrationEngine(
        campaign_database=campaign_database,
        orchestrator_database=tmp_path / "orchestrator.sqlite3",
        executor=DemoExecutor(fail_ordinals={0}),
        configuration=OrchestratorConfiguration(
            campaign_id=campaign_id,
            worker_id="worker-a",
            max_attempts=2,
            max_items=3,
        ),
    )

    summary = engine.run()
    items = manager.list_items(campaign_id)

    failed_item = next(item for item in items if item.ordinal == 0)
    completed_item = next(item for item in items if item.ordinal == 1)

    assert failed_item.attempts == 2
    assert failed_item.status == "failed"
    assert completed_item.status == "completed"
    assert summary.retried >= 1


def test_stop_control_prevents_claims(tmp_path):
    campaign_id, campaign_database, manager = make_campaign(
        tmp_path,
        item_count=2,
    )
    orchestrator_database = tmp_path / "orchestrator.sqlite3"
    store = OrchestratorStore(orchestrator_database)
    store.request_stop(
        campaign_id,
        reason="maintenance",
    )

    summary = OrchestrationEngine(
        campaign_database=campaign_database,
        orchestrator_database=orchestrator_database,
        executor=DemoExecutor(),
        configuration=OrchestratorConfiguration(
            campaign_id=campaign_id,
            worker_id="worker-a",
        ),
    ).run()

    assert summary.claimed == 0
    assert summary.stopped_reason == "maintenance"
    assert manager.status(campaign_id).pending == 2


def test_events_are_structured_and_ordered(tmp_path):
    campaign_id, campaign_database, _ = make_campaign(
        tmp_path,
        item_count=1,
    )
    orchestrator_database = tmp_path / "orchestrator.sqlite3"

    OrchestrationEngine(
        campaign_database=campaign_database,
        orchestrator_database=orchestrator_database,
        executor=DemoExecutor(),
        configuration=OrchestratorConfiguration(
            campaign_id=campaign_id,
            worker_id="worker-a",
        ),
    ).run()

    events = OrchestratorStore(
        orchestrator_database
    ).list_events(campaign_id)

    event_types = [event["event_type"] for event in events]

    assert event_types[0] == "worker_started"
    assert "lease_acquired" in event_types
    assert "work_item_completed" in event_types
    assert event_types[-1] == "worker_stopped"


def test_clear_stop_allows_execution(tmp_path):
    campaign_id, campaign_database, manager = make_campaign(
        tmp_path,
        item_count=1,
    )
    orchestrator_database = tmp_path / "orchestrator.sqlite3"
    store = OrchestratorStore(orchestrator_database)
    store.request_stop(campaign_id, reason="pause")
    store.clear_stop(campaign_id)

    summary = OrchestrationEngine(
        campaign_database=campaign_database,
        orchestrator_database=orchestrator_database,
        executor=DemoExecutor(),
        configuration=OrchestratorConfiguration(
            campaign_id=campaign_id,
            worker_id="worker-a",
        ),
    ).run()

    assert summary.completed == 1
    assert manager.status(campaign_id).completed == 1
