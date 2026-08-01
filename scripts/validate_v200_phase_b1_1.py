from pathlib import Path
import sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kernel import *
from kernel.events import validate_event_sequence
UTC='2026-07-31T12:00:00Z'
def check(label,ok,detail):
 print(f"[{'PASS' if ok else 'FAIL'}] {label:<30} {detail}")
 if not ok: raise SystemExit(1)
version=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
print('PrimeAIExplorer v2.0 Phase B1.1 Validator'); print('='*78)
check('installed version',version=='2.0.0-phase-b1.1',version)
with tempfile.TemporaryDirectory() as t:
 c=ExecutionContext.create(benchmark_id='prime_value',benchmark_version='2.0.0',connector_id='mock',software_version=version,project_root=ROOT,working_directory=Path(t),output_directory=Path(t)/'out',configuration={'window':8},session_id='RUN-VALIDATION',created_utc=UTC)
 check('context hash',len(c.context_sha256)==64,c.context_sha256[:16])
 r=ExecutionResult.success(session_id=c.session_id,elapsed_seconds=.1,response_count=1,evaluation_count=1)
 check('result status',r.status is ExecutionStatus.SUCCESS,r.result_sha256[:16])
 ev=[KernelEvent('1.0',c.session_id,KernelEventType.RUN_CREATED,1,UTC,{}),KernelEvent('1.0',c.session_id,KernelEventType.RUN_FINISHED,2,UTC,{'status':'success'})]
 validate_event_sequence(ev); check('event lifecycle',True,'created -> finished')
print('='*78); print('PrimeAIExplorer v2.0 Phase B1.1 validation passed.')
