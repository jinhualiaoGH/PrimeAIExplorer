from dataclasses import FrozenInstanceError
from pathlib import Path
from types import MappingProxyType
import tempfile,unittest
from kernel import *
from kernel.events import validate_event_sequence
from kernel.serialization import canonical_json,stable_sha256
UTC='2026-07-31T12:00:00Z'
class Tests(unittest.TestCase):
 def context(self,root): return ExecutionContext.create(benchmark_id='prime_value',benchmark_version='2.0.0',connector_id='mock',software_version='2.0.0-phase-b1.1',project_root=root,working_directory=root/'work',output_directory=root/'out',configuration={'x':1},session_id='RUN-TEST',created_utc=UTC)
 def event(self,t,n,s='RUN-TEST'): return KernelEvent('1.0',s,t,n,UTC,{})
 def test_context_creation(self):
  with tempfile.TemporaryDirectory() as t: self.assertEqual(self.context(Path(t)).benchmark_id,'prime_value')
 def test_context_frozen(self):
  with tempfile.TemporaryDirectory() as t:
   c=self.context(Path(t))
   with self.assertRaises(FrozenInstanceError): c.benchmark_id='x'
 def test_mapping_proxy(self):
  with tempfile.TemporaryDirectory() as t: self.assertIsInstance(self.context(Path(t)).configuration,MappingProxyType)
 def test_context_hash(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t); self.assertEqual(self.context(r).context_sha256,self.context(r).context_sha256)
 def test_empty_id_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(ConfigurationError): ExecutionContext.create(benchmark_id=' ',benchmark_version='2',connector_id='m',software_version='2',project_root=Path(t),working_directory=Path(t),output_directory=Path(t),session_id='RUN-X',created_utc=UTC)
 def test_success_result(self): self.assertEqual(ExecutionResult.success(session_id='RUN-X',elapsed_seconds=1).status,ExecutionStatus.SUCCESS)
 def test_failed_requires_error(self):
  with self.assertRaises(ValidationError): ExecutionResult('1.0','RUN-X',ExecutionStatus.FAILED,1)
 def test_success_rejects_error(self):
  with self.assertRaises(ValidationError): ExecutionResult('1.0','RUN-X',ExecutionStatus.SUCCESS,1,errors=('x',))
 def test_negative_elapsed(self):
  with self.assertRaises(ValidationError): ExecutionResult.success(session_id='RUN-X',elapsed_seconds=-1)
 def test_result_hash(self): self.assertEqual(ExecutionResult.success(session_id='RUN-X',elapsed_seconds=1).result_sha256,ExecutionResult.success(session_id='RUN-X',elapsed_seconds=1).result_sha256)
 def test_event_valid(self): validate_event_sequence([self.event(KernelEventType.RUN_CREATED,1),self.event(KernelEventType.RUN_FINISHED,2)])
 def test_event_created_first(self):
  with self.assertRaises(ValidationError): validate_event_sequence([self.event(KernelEventType.RUN_STARTED,1),self.event(KernelEventType.RUN_FINISHED,2)])
 def test_event_terminal(self):
  with self.assertRaises(ValidationError): validate_event_sequence([self.event(KernelEventType.RUN_CREATED,1)])
 def test_event_contiguous(self):
  with self.assertRaises(ValidationError): validate_event_sequence([self.event(KernelEventType.RUN_CREATED,1),self.event(KernelEventType.RUN_FINISHED,3)])
 def test_exception_hierarchy(self):
  self.assertTrue(issubclass(ConfigurationError,KernelError)); self.assertTrue(issubclass(BenchmarkError,RunnerError)); self.assertTrue(issubclass(ConnectorError,RunnerError))
 def test_canonical_json(self): self.assertEqual(canonical_json({'b':2,'a':1}),'{"a":1,"b":2}')
 def test_hash_order(self): self.assertEqual(stable_sha256({'b':2,'a':1}),stable_sha256({'a':1,'b':2}))
if __name__=='__main__': unittest.main()
