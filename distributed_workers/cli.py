"""CLI for Phase D5 distributed worker execution."""
from __future__ import annotations
import argparse, json
from campaign_orchestrator import DemoExecutor
from campaign_orchestrator.store import OrchestratorStore
from .coordinator import DistributedCoordinator
from .models import DistributedConfiguration
from .store import WorkerStore

def parser():
    p=argparse.ArgumentParser(description='PrimeAIExplorer distributed workers.')
    s=p.add_subparsers(dest='command',required=True)
    r=s.add_parser('run')
    for name in ('campaign-id','campaign-database','orchestrator-database','worker-database'): r.add_argument('--'+name,required=True)
    r.add_argument('--worker-prefix',default='d5-worker'); r.add_argument('--workers',type=int,default=2)
    r.add_argument('--lease-seconds',type=int,default=900); r.add_argument('--heartbeat-seconds',type=float,default=5.0)
    r.add_argument('--stale-after-seconds',type=float,default=30.0); r.add_argument('--max-attempts',type=int,default=3)
    r.add_argument('--max-items-per-worker',type=int); r.add_argument('--fail-ordinal',action='append',type=int,default=[])
    for cmd in ('workers','events','pause','resume','recover-stale'):
        x=s.add_parser(cmd); x.add_argument('--campaign-id',required=True); x.add_argument('--worker-database',required=True)
        if cmd=='events': x.add_argument('--limit',type=int,default=1000)
        if cmd=='pause': x.add_argument('--reason')
        if cmd=='recover-stale': x.add_argument('--stale-after-seconds',type=float,default=30.0)
    return p

def out(v): print(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False))
def main():
    a=parser().parse_args(); store=WorkerStore(a.worker_database)
    if a.command=='workers': out(store.list_workers(a.campaign_id)); return 0
    if a.command=='events': out(store.list_events(a.campaign_id,a.limit)); return 0
    if a.command=='pause':
        store.pause(a.campaign_id,a.reason)
        # Cooperatively stop D4 workers after their current item.
        out({'paused':True,'reason':a.reason}); return 0
    if a.command=='resume': store.resume(a.campaign_id); out({'paused':False}); return 0
    if a.command=='recover-stale': out({'recovered':store.recover_stale(a.campaign_id,a.stale_after_seconds)}); return 0
    failures=set(a.fail_ordinal)
    cfg=DistributedConfiguration(campaign_id=a.campaign_id,worker_prefix=a.worker_prefix,worker_count=a.workers,
        lease_seconds=a.lease_seconds,heartbeat_seconds=a.heartbeat_seconds,stale_after_seconds=a.stale_after_seconds,
        max_attempts=a.max_attempts,max_items_per_worker=a.max_items_per_worker)
    coord=DistributedCoordinator(campaign_database=a.campaign_database,orchestrator_database=a.orchestrator_database,
        worker_database=a.worker_database,executor_factory=lambda _: DemoExecutor(fail_ordinals=failures),configuration=cfg)
    out(coord.run().to_dict()); return 0
if __name__=='__main__': raise SystemExit(main())
