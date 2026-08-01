from __future__ import annotations

from benchmark_campaign import (
    CampaignManager,
    expand_campaign,
)
from benchmark_campaign.specification import build_specification


def make_specification():
    return build_specification(
        name="Fixture Campaign",
        description="D3 tests.",
        dataset_ids=[
            "DS-AAAAAAAAAAAAAAAA",
            "DS-BBBBBBBBBBBBBBBB",
        ],
        providers=["manual", "openai"],
        models_by_provider={
            "manual": ["manual-a"],
            "openai": ["model-x", "model-y"],
        },
        prompt_templates=["prompt-v1"],
        random_seeds=[1, 2],
        window_sizes=[4, 8],
        repeats=2,
        model_parameters={
            "openai": {"temperature": 0},
            "openai:model-y": {"max_output_tokens": 100},
        },
    )


def test_specification_and_plan_are_deterministic():
    first_specification = make_specification()
    second_specification = make_specification()

    first_plan = expand_campaign(first_specification)
    second_plan = expand_campaign(second_specification)

    assert (
        first_specification.campaign_id
        == second_specification.campaign_id
    )
    assert first_plan.plan_sha256 == second_plan.plan_sha256
    assert (
        [item.work_item_id for item in first_plan.work_items]
        == [item.work_item_id for item in second_plan.work_items]
    )


def test_expansion_cross_product_count():
    plan = expand_campaign(make_specification())

    # 2 datasets * (1 manual + 2 openai models)
    # * 1 prompt * 2 seeds * 2 windows * 2 repeats
    assert len(plan.work_items) == 48
    assert plan.work_items[0].ordinal == 0
    assert plan.work_items[-1].ordinal == 47


def test_model_parameters_merge():
    plan = expand_campaign(make_specification())
    model_y = next(
        item
        for item in plan.work_items
        if item.provider == "openai"
        and item.model == "model-y"
    )

    assert model_y.model_parameters == {
        "temperature": 0,
        "max_output_tokens": 100,
    }


def test_manager_creation_and_claim_are_resumable(tmp_path):
    plan = expand_campaign(make_specification())
    manager = CampaignManager(tmp_path / "campaigns.sqlite3")

    assert manager.create(plan) is True
    assert manager.create(plan) is False

    first = manager.claim_next(plan.campaign_id)
    second = manager.claim_next(plan.campaign_id)

    assert first is not None
    assert second is not None
    assert first.ordinal == 0
    assert second.ordinal == 1
    assert first.attempts == 1


def test_complete_fail_and_reset(tmp_path):
    plan = expand_campaign(make_specification())
    manager = CampaignManager(tmp_path / "campaigns.sqlite3")
    manager.create(plan)

    first = manager.claim_next(plan.campaign_id)
    assert first is not None
    completed = manager.complete(
        plan.campaign_id,
        first.work_item_id,
        experiment_id="EXP-TEST",
        catalog_record_id="XR-TEST",
    )

    second = manager.claim_next(plan.campaign_id)
    assert second is not None
    failed = manager.fail(
        plan.campaign_id,
        second.work_item_id,
        error_message="fixture failure",
    )

    assert completed.status == "completed"
    assert completed.experiment_id == "EXP-TEST"
    assert failed.status == "failed"

    assert manager.reset_failed(plan.campaign_id) == 1
    reset_items = manager.list_items(
        plan.campaign_id,
        status="pending",
    )
    assert any(
        item.work_item_id == second.work_item_id
        for item in reset_items
    )


def test_status_and_export_are_deterministic(tmp_path):
    plan = expand_campaign(make_specification())
    manager = CampaignManager(tmp_path / "campaigns.sqlite3")
    manager.create(plan)

    item = manager.claim_next(plan.campaign_id)
    assert item is not None
    manager.complete(
        plan.campaign_id,
        item.work_item_id,
        experiment_id="EXP-TEST",
    )

    status = manager.status(plan.campaign_id)

    assert status.total == 48
    assert status.completed == 1
    assert status.pending == 47
    assert status.progress_fraction == 1 / 48

    first = manager.export_plan_jsonl(
        plan.campaign_id,
        tmp_path / "first.jsonl",
    )
    second = manager.export_plan_jsonl(
        plan.campaign_id,
        tmp_path / "second.jsonl",
    )

    assert first.read_bytes() == second.read_bytes()
