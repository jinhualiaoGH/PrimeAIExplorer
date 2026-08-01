"""Executor wrappers that renew D4 leases during long-running work."""
from __future__ import annotations
import threading
from campaign_orchestrator.executors import ExecutionOutcome, WorkItemExecutor
from campaign_orchestrator.store import OrchestratorStore
from benchmark_campaign.models import CampaignWorkItem

class LeaseHeartbeatExecutor:
    def __init__(self, delegate: WorkItemExecutor, *, store: OrchestratorStore,
                 campaign_id: str, worker_id: str, lease_seconds: int,
                 heartbeat_seconds: float) -> None:
        self.delegate=delegate; self.store=store; self.campaign_id=campaign_id
        self.worker_id=worker_id; self.lease_seconds=lease_seconds
        self.heartbeat_seconds=heartbeat_seconds

    def execute(self, item: CampaignWorkItem) -> ExecutionOutcome:
        stop=threading.Event()
        def pulse() -> None:
            while not stop.wait(self.heartbeat_seconds):
                self.store.heartbeat(self.campaign_id,item.work_item_id,
                    worker_id=self.worker_id,lease_seconds=self.lease_seconds)
        thread=threading.Thread(target=pulse,name=f'lease-heartbeat-{self.worker_id}',daemon=True)
        thread.start()
        try: return self.delegate.execute(item)
        finally:
            stop.set(); thread.join(timeout=max(1.0,self.heartbeat_seconds*2))
