from dataclasses import replace
import pytest

from campaign_repository import (
    CampaignCheckpoint,
    CampaignCheckpointStore,
    CheckpointStatus,
    JobCheckpoint,
    ResumePlanner,
    audit_checkpoint_lineage,
    next_checkpoint,
)
from kernel.exceptions import ValidationError


def jobs():
    return (
        JobCheckpoint("JOB-1", True, 1, result_sha256="a" * 64),
        JobCheckpoint("JOB-2", False, 1, last_error_class="ProviderError"),
        JobCheckpoint("JOB-3", False, 0),
    )


def cp0(status=CheckpointStatus.INTERRUPTED):
    return CampaignCheckpoint(
        "CP-0", "CAMPAIGN-1", "EXP-1", "p" * 64, 0, status, jobs()
    )


def cp1():
    p = cp0()
    return next_checkpoint(
        p,
        status=CheckpointStatus.RUNNING,
        jobs=(
            p.jobs[0],
            JobCheckpoint("JOB-2", True, 2, result_sha256="b" * 64),
            p.jobs[2],
        ),
    )


def cp2():
    p = cp1()
    return next_checkpoint(
        p,
        status=CheckpointStatus.COMPLETED,
        jobs=(
            p.jobs[0],
            p.jobs[1],
            JobCheckpoint("JOB-3", True, 1, result_sha256="c" * 64),
        ),
    )


def test_job_checkpoint_complete():
    assert jobs()[0].completed


def test_completed_requires_sha():
    with pytest.raises(ValidationError):
        JobCheckpoint("J", True, 1)


def test_attempts_nonnegative():
    with pytest.raises(ValidationError):
        JobCheckpoint("J", False, -1)


def test_counts():
    c = cp0()
    assert (c.total_jobs, c.completed_jobs, c.pending_jobs) == (3, 1, 2)


def test_checkpoint_identity_stable():
    assert cp0().checkpoint_sha256 == cp0().checkpoint_sha256


def test_string_status():
    assert replace(cp0(), status="interrupted").status == CheckpointStatus.INTERRUPTED


def test_bad_status():
    with pytest.raises(ValidationError):
        replace(cp0(), status="bad")


def test_duplicate_jobs():
    with pytest.raises(ValidationError):
        replace(cp0(), jobs=(jobs()[0], jobs()[0]))


def test_seq_zero_parent_rejected():
    with pytest.raises(ValidationError):
        replace(cp0(), parent_checkpoint_sha256="x" * 64)


def test_seq_gt_zero_requires_parent():
    with pytest.raises(ValidationError):
        replace(cp0(), checkpoint_sequence=1, parent_checkpoint_sha256=None)


def test_next_sequence():
    assert cp1().checkpoint_sequence == 1


def test_next_parent():
    p = cp0()
    c = next_checkpoint(p, status="running", jobs=p.jobs)
    assert c.parent_checkpoint_sha256 == p.checkpoint_sha256


def test_store_initialize(tmp_path):
    s = CampaignCheckpointStore(tmp_path)
    s.initialize()
    assert (tmp_path / "checkpoints").is_dir()


def test_store_write(tmp_path):
    s = CampaignCheckpointStore(tmp_path)
    path = s.write(cp0())
    assert (tmp_path / path).is_file()


def test_store_idempotent(tmp_path):
    s = CampaignCheckpointStore(tmp_path)
    assert s.write(cp0()) == s.write(cp0())


def test_latest_pointer(tmp_path):
    s = CampaignCheckpointStore(tmp_path)
    s.write(cp0())
    assert s.read_latest(campaign_id="CAMPAIGN-1", experiment_id="EXP-1")["checkpoint_sequence"] == 0


def test_latest_moves(tmp_path):
    s = CampaignCheckpointStore(tmp_path)
    s.write(cp0())
    s.write(cp1())
    assert s.read_latest(campaign_id="CAMPAIGN-1", experiment_id="EXP-1")["checkpoint_sequence"] == 1


def test_list_files(tmp_path):
    s = CampaignCheckpointStore(tmp_path)
    s.write(cp0())
    s.write(cp1())
    assert len(s.list_checkpoint_files(campaign_id="CAMPAIGN-1", experiment_id="EXP-1")) == 2


def test_missing_latest(tmp_path):
    with pytest.raises(FileNotFoundError):
        CampaignCheckpointStore(tmp_path).read_latest(campaign_id="C", experiment_id="E")


def decision(checkpoint=None, campaign="CAMPAIGN-1", experiment="EXP-1", plan=None, job_ids=None):
    return ResumePlanner().evaluate(
        checkpoint=checkpoint or cp0(),
        expected_campaign_id=campaign,
        expected_experiment_id=experiment,
        expected_execution_plan_sha256=plan or ("p" * 64),
        expected_job_ids=job_ids or ("JOB-1", "JOB-2", "JOB-3"),
    )


def test_resume_allowed():
    d = decision()
    assert d.resumable
    assert d.completed_job_ids == ("JOB-1",)
    assert d.pending_job_ids == ("JOB-2", "JOB-3")


def test_campaign_mismatch():
    d = decision(campaign="OTHER")
    assert not d.resumable and d.reason == "campaign_id_mismatch"


def test_experiment_mismatch():
    d = decision(experiment="OTHER")
    assert not d.resumable and d.reason == "experiment_id_mismatch"


def test_plan_mismatch():
    d = decision(plan="q" * 64)
    assert not d.resumable and d.reason == "execution_plan_sha256_mismatch"


def test_job_set_mismatch():
    d = decision(job_ids=("JOB-1", "JOB-2"))
    assert not d.resumable and d.reason == "job_set_mismatch"


def test_completed_not_resumable():
    d = decision(checkpoint=cp2())
    assert not d.resumable and d.reason == "campaign_already_completed"


def test_empty_lineage():
    a = audit_checkpoint_lineage(())
    assert a.valid and a.checked_count == 0


def test_one_lineage():
    assert audit_checkpoint_lineage((cp0(),)).valid


def test_three_lineage():
    a = audit_checkpoint_lineage((cp0(), cp1(), cp2()))
    assert a.valid and a.checked_count == 3


def test_bad_parent():
    bad = replace(cp1(), parent_checkpoint_sha256="z" * 64)
    assert not audit_checkpoint_lineage((cp0(), bad)).valid


def test_noncontiguous():
    bad = replace(cp1(), checkpoint_sequence=2)
    assert not audit_checkpoint_lineage((cp0(), bad)).valid


def test_campaign_lineage_mismatch():
    bad = replace(cp1(), campaign_id="OTHER")
    assert not audit_checkpoint_lineage((cp0(), bad)).valid


def test_experiment_lineage_mismatch():
    bad = replace(cp1(), experiment_id="OTHER")
    assert not audit_checkpoint_lineage((cp0(), bad)).valid


def test_plan_lineage_mismatch():
    bad = replace(cp1(), execution_plan_sha256="q" * 64)
    assert not audit_checkpoint_lineage((cp0(), bad)).valid


def test_job_set_lineage_mismatch():
    bad = replace(cp1(), jobs=cp1().jobs[:-1])
    assert not audit_checkpoint_lineage((cp0(), bad)).valid


def test_completed_regression():
    c = cp1()
    bad_jobs = list(c.jobs)
    bad_jobs[0] = JobCheckpoint("JOB-1", False, 2)
    bad = replace(c, jobs=tuple(bad_jobs))
    audit = audit_checkpoint_lineage((cp0(), bad))
    assert not audit.valid
    assert any("completed_job_regressed" in e for e in audit.errors)


def test_completed_result_change():
    c = cp1()
    bad_jobs = list(c.jobs)
    bad_jobs[0] = JobCheckpoint("JOB-1", True, 2, result_sha256="x" * 64)
    bad = replace(c, jobs=tuple(bad_jobs))
    audit = audit_checkpoint_lineage((cp0(), bad))
    assert not audit.valid
    assert any("completed_job_result_changed" in e for e in audit.errors)


def test_checkpoint_to_dict():
    p = cp0().to_dict()
    assert p["schema_version"] == "i3.0" and p["completed_jobs"] == 1


def test_resume_to_dict():
    assert decision().to_dict()["resumable"] is True


def test_audit_to_dict():
    assert audit_checkpoint_lineage((cp0(),)).to_dict()["schema_version"] == "i3.0"


def test_missing_checkpoint_target(tmp_path):
    s = CampaignCheckpointStore(tmp_path)
    path = s.write(cp0())
    (tmp_path / path).unlink()
    with pytest.raises(FileNotFoundError):
        s.read_latest(campaign_id="CAMPAIGN-1", experiment_id="EXP-1")


def test_no_latest_publish(tmp_path):
    s = CampaignCheckpointStore(tmp_path)
    s.write(cp0(), publish_latest=False)
    with pytest.raises(FileNotFoundError):
        s.read_latest(campaign_id="CAMPAIGN-1", experiment_id="EXP-1")


def test_pending_attempt_state():
    j = next(x for x in cp0().jobs if x.job_id == "JOB-2")
    assert j.attempts_completed == 1 and j.last_error_class == "ProviderError"
