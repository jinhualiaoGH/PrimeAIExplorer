from __future__ import annotations
import threading, time
from benchmark_campaign import CampaignManager, expand_campaign
from benchmark_campaign.specification import build_specification
from campaign_orchestrator import DemoExecutor
from campaign_orchestrator.executors import ExecutionOutcome
from distributed_workers import DistributedConfiguration, DistributedCoordinator, WorkerStore

def make_campaign(tmp_path,count=12):
    spec=build_specification(name='D5 Fixture',description='distributed',dataset_ids=['DS-AAAAAAAAAAAAAAAA'],
      providers=['manual'],models_by_provider={'manual':['fixture']},prompt_templates=['prompt-v1'],
      random_seeds=[1],window_sizes=list(range(1,count+1)),repeats=1)
    plan=expand_campaign(spec); db=tmp_path/'campaign.sqlite3'; manager=CampaignManager(db); manager.create(plan)
    return spec.campaign_id,db,manager

def coordinator(tmp_path,campaign_id,db,workers=3,factory=None):
    return DistributedCoordinator(campaign_database=db,orchestrator_database=tmp_path/'orch.sqlite3',
      worker_database=tmp_path/'workers.sqlite3',executor_factory=factory or (lambda _: DemoExecutor()),
      configuration=DistributedConfiguration(campaign_id=campaign_id,worker_count=workers,
        heartbeat_seconds=.02,stale_after_seconds=.05))

def test_multiple_workers_complete_without_duplicates(tmp_path):
    cid,db,m=make_campaign(tmp_path,24); seen=[]; lock=threading.Lock()
    class Recording:
      def execute(self,item):
        with lock: seen.append(item.work_item_id)
        time.sleep(.002)
        return ExecutionOutcome(True,f'EXP-D5-{item.ordinal}',f'XR-D5-{item.ordinal}')
    summary=coordinator(tmp_path,cid,db,4,lambda _:Recording()).run()
    assert summary.completed==24 and len(seen)==len(set(seen))==24
    assert m.status(cid).completed==24

def test_workers_are_registered_and_stopped(tmp_path):
    cid,db,_=make_campaign(tmp_path,4); coordinator(tmp_path,cid,db,2).run()
    workers=WorkerStore(tmp_path/'workers.sqlite3').list_workers(cid)
    assert len(workers)==2 and {w['status'] for w in workers}=={'stopped'}

def test_pause_prevents_claims_and_resume_allows_run(tmp_path):
    cid,db,m=make_campaign(tmp_path,3); store=WorkerStore(tmp_path/'workers.sqlite3'); store.pause(cid,'maintenance')
    first=coordinator(tmp_path,cid,db,2).run(); assert first.claimed==0 and m.status(cid).pending==3
    store.resume(cid); second=coordinator(tmp_path,cid,db,2).run(); assert second.completed==3

def test_stale_worker_recovery(tmp_path):
    cid,_,_=make_campaign(tmp_path,1); store=WorkerStore(tmp_path/'workers.sqlite3'); store.register(cid,'dead-worker')
    time.sleep(.03); recovered=store.recover_stale(cid,.01)
    assert recovered==['dead-worker'] and store.list_workers(cid)[0]['status']=='stale'

def test_structured_events_include_coordinator_and_worker_summaries(tmp_path):
    cid,db,_=make_campaign(tmp_path,2); coordinator(tmp_path,cid,db,2).run()
    types=[e['event_type'] for e in WorkerStore(tmp_path/'workers.sqlite3').list_events(cid)]
    assert types[0]=='coordinator_started' and 'worker_registered' in types
    assert 'worker_summary' in types and types[-1]=='coordinator_stopped'

def test_configuration_validation():
    try: DistributedConfiguration(campaign_id='bad')
    except ValueError: pass
    else: raise AssertionError('invalid campaign id accepted')
