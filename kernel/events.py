from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any,Mapping
from kernel.exceptions import ValidationError
from kernel.serialization import stable_sha256
class KernelEventType(str,Enum):
    RUN_CREATED='run_created'; RUN_STARTED='run_started'; BENCHMARK_LOADED='benchmark_loaded'; CONNECTOR_STARTED='connector_started'; CONNECTOR_COMPLETED='connector_completed'; RESULT_CREATED='result_created'; RUN_FINISHED='run_finished'; RUN_FAILED='run_failed'
ORDER={KernelEventType.RUN_CREATED:10,KernelEventType.RUN_STARTED:20,KernelEventType.BENCHMARK_LOADED:30,KernelEventType.CONNECTOR_STARTED:40,KernelEventType.CONNECTOR_COMPLETED:50,KernelEventType.RESULT_CREATED:60,KernelEventType.RUN_FINISHED:70,KernelEventType.RUN_FAILED:70}
@dataclass(frozen=True)
class KernelEvent:
    schema_version:str
    session_id:str
    event_type:KernelEventType
    sequence:int
    occurred_utc:str
    detail:Mapping[str,Any]
    def __post_init__(self):
        if not isinstance(self.event_type,KernelEventType): object.__setattr__(self,'event_type',KernelEventType(self.event_type))
        if isinstance(self.sequence,bool) or not isinstance(self.sequence,int) or self.sequence<1: raise ValidationError('invalid event sequence')
        p=datetime.fromisoformat(self.occurred_utc[:-1]+'+00:00' if self.occurred_utc.endswith('Z') else self.occurred_utc)
        if p.tzinfo is None: raise ValidationError('event timestamp requires timezone')
        if not isinstance(self.detail,Mapping): raise ValidationError('event detail must be mapping')
    @property
    def lifecycle_order(self): return ORDER[self.event_type]
    def to_dict(self): return {'schema_version':self.schema_version,'session_id':self.session_id,'event_type':self.event_type.value,'sequence':self.sequence,'occurred_utc':self.occurred_utc,'detail':dict(self.detail)}
    @property
    def event_sha256(self): return stable_sha256(self.to_dict())
def validate_event_sequence(events):
    if not events: raise ValidationError('events required')
    if len({e.session_id for e in events})!=1: raise ValidationError('one session required')
    if [e.sequence for e in events]!=list(range(1,len(events)+1)): raise ValidationError('sequences must be contiguous')
    if [e.lifecycle_order for e in events]!=sorted(e.lifecycle_order for e in events): raise ValidationError('lifecycle order invalid')
    if events[0].event_type is not KernelEventType.RUN_CREATED: raise ValidationError('first event must be RUN_CREATED')
    if events[-1].event_type not in {KernelEventType.RUN_FINISHED,KernelEventType.RUN_FAILED}: raise ValidationError('terminal event required')
