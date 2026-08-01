"""Thread-based distributed worker coordinator built on the D4 atomic queue."""
from __future__ import annotations
import threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable
from campaign_orchestrator import OrchestrationEngine, OrchestratorConfiguration
from campaign_orchestrator.executors import WorkItemExecutor
from campaign_orchestrator.store import OrchestratorStore
from .executor import LeaseHeartbeatExecutor
from .models import DistributedConfiguration, DistributedSummary
from .store import WorkerStore

ExecutorFactory = Callable[[str], WorkItemExecutor]

class DistributedCoordinator:
    def __init__(self, *, campaign_database: str | Path, orchestrator_database: str | Path,
                 worker_database: str | Path, executor_factory: ExecutorFactory,
                 configuration: DistributedConfiguration) -> None:
        self.campaign_database=Path(campaign_database)
        self.orchestrator_database=Path(orchestrator_database)
        self.store=WorkerStore(worker_database)
        self.executor_factory=executor_factory
        self.configuration=configuration
        self._shutdown=threading.Event()

    def request_shutdown(self) -> None: self._shutdown.set()

    def run(self) -> DistributedSummary:
        started=time.monotonic(); c=self.configuration
        recovered=len(self.store.recover_stale(c.campaign_id,c.stale_after_seconds))
        paused, reason=self.store.pause_state(c.campaign_id)
        if paused:
            self.store.event(c.campaign_id,None,'coordinator_skipped_paused',{'reason':reason})
            return DistributedSummary(c.campaign_id,0,0,0,0,0,recovered,0,time.monotonic()-started)
        self.store.event(c.campaign_id,None,'coordinator_started',{'worker_count':c.worker_count})
        totals={'claimed':0,'completed':0,'failed':0,'retried':0,'stopped':0}
        lock=threading.Lock()
        def run_worker(index: int):
            worker_id=f"{c.worker_prefix}-{index+1:02d}"
            self.store.register(c.campaign_id,worker_id,{'slot':index+1})
            beat_stop=threading.Event()
            def worker_heartbeat():
                while not beat_stop.wait(c.heartbeat_seconds): self.store.heartbeat(c.campaign_id,worker_id)
            beat=threading.Thread(target=worker_heartbeat,daemon=True); beat.start()
            try:
                delegate=self.executor_factory(worker_id)
                wrapped=LeaseHeartbeatExecutor(delegate,store=OrchestratorStore(self.orchestrator_database),
                    campaign_id=c.campaign_id,worker_id=worker_id,lease_seconds=c.lease_seconds,
                    heartbeat_seconds=c.heartbeat_seconds)
                summary=OrchestrationEngine(campaign_database=self.campaign_database,
                    orchestrator_database=self.orchestrator_database,executor=wrapped,
                    configuration=OrchestratorConfiguration(campaign_id=c.campaign_id,worker_id=worker_id,
                        lease_seconds=c.lease_seconds,heartbeat_seconds=max(1,int(c.heartbeat_seconds)),
                        max_attempts=c.max_attempts,max_items=c.max_items_per_worker,
                        retry_backoff_seconds=c.retry_backoff_seconds)).run()
                return worker_id, summary
            finally:
                beat_stop.set(); beat.join(timeout=max(1.0,c.heartbeat_seconds*2))
                self.store.stop(c.campaign_id,worker_id)
        with ThreadPoolExecutor(max_workers=c.worker_count,thread_name_prefix='primeai-d5') as pool:
            futures=[pool.submit(run_worker,i) for i in range(c.worker_count)]
            for future in as_completed(futures):
                worker_id, summary=future.result()
                with lock:
                    totals['claimed']+=summary.claimed; totals['completed']+=summary.completed
                    totals['failed']+=summary.failed; totals['retried']+=summary.retried; totals['stopped']+=1
                self.store.event(c.campaign_id,worker_id,'worker_summary',summary.to_dict())
        elapsed=time.monotonic()-started
        result=DistributedSummary(c.campaign_id,c.worker_count,totals['claimed'],totals['completed'],
            totals['failed'],totals['retried'],recovered,totals['stopped'],elapsed)
        self.store.event(c.campaign_id,None,'coordinator_stopped',result.to_dict())
        return result
