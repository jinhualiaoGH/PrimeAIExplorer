from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
import numpy as np
from sequence_plugins.builtin.prime_value import PrimeValueSequencePlugin

def config(root,count,overwrite=False):
 return {'_experiment_root':str(root),'experiment':{'id':'EXP-000003-TEST'},'repository':{'prime_root':str(root/'ranges'),'read_only':True},'sequence':{'target_count':count,'metadata_file':'data/meta.json'},'build':{'overwrite':overwrite},'validation':{'full_partition_monotonic_check':True,'dataset_chunk_size':3,'sampled_primality_count':count,'primality_sampling_seed':130003}}
def source(root):
 d=root/'ranges';d.mkdir();np.save(d/'primes_1_10.npy',np.array([2,3,5,7],dtype=np.uint64));np.save(d/'primes_11_20.npy',np.array([11,13,17,19],dtype=np.uint64));return d
class PhaseBTests(unittest.TestCase):
 def test_plan_is_read_only(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=source(r);d=r/'data/values.npy';p=PrimeValueSequencePlugin(config(r,6));plan=p.plan_dataset(s,d,count=6);self.assertFalse(d.exists());self.assertFalse(plan['writes_performed']);self.assertEqual(plan['estimated_data_bytes'],48)
 def test_atomic_build_and_validation(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=source(r);d=r/'data/values.npy';p=PrimeValueSequencePlugin(config(r,6));m=p.build_dataset(s,d,count=6);self.assertEqual(m.count,6);np.testing.assert_array_equal(np.load(d),[2,3,5,7,11,13]);result=p.validate_dataset(d);self.assertTrue(result['valid']);self.assertEqual(result['sampled_primality_count'],6)
 def test_metadata_contract(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=source(r);d=r/'data/values.npy';p=PrimeValueSequencePlugin(config(r,6));p.build_dataset(s,d,count=6);m=json.loads((r/'data/meta.json').read_text());self.assertEqual(m['held_out_target_value'],13);self.assertEqual(m['held_out_target_index_1_based'],6);self.assertEqual(len(m['dataset_sha256']),64)
 def test_overwrite_protection(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=source(r);d=r/'data/values.npy';p=PrimeValueSequencePlugin(config(r,6));p.build_dataset(s,d,count=6)
   with self.assertRaises(FileExistsError):p.build_dataset(s,d,count=6)
 def test_explicit_overwrite(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=source(r);d=r/'data/values.npy';PrimeValueSequencePlugin(config(r,6)).build_dataset(s,d,count=6);p=PrimeValueSequencePlugin(config(r,5,True));p.build_dataset(s,d,count=5);self.assertEqual(len(np.load(d)),5)
 def test_insufficient_source_rejected_without_output(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=source(r);d=r/'data/values.npy';p=PrimeValueSequencePlugin(config(r,9))
   with self.assertRaises(ValueError):p.build_dataset(s,d,count=9)
   self.assertFalse(d.exists());self.assertFalse((r/'data/meta.json').exists())
 def test_hash_mismatch_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=source(r);d=r/'data/values.npy';p=PrimeValueSequencePlugin(config(r,6));p.build_dataset(s,d,count=6);m=json.loads((r/'data/meta.json').read_text());m['dataset_sha256']='0'*64;(r/'data/meta.json').write_text(json.dumps(m))
   with self.assertRaisesRegex(ValueError,'SHA-256'):p.validate_dataset(d)
 def test_composite_sample_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);s=source(r);d=r/'data/values.npy';p=PrimeValueSequencePlugin(config(r,6));p.build_dataset(s,d,count=6);a=np.load(d);a[3]=9;np.save(d,a);m=json.loads((r/'data/meta.json').read_text());import hashlib;m['dataset_sha256']=hashlib.sha256(d.read_bytes()).hexdigest();(r/'data/meta.json').write_text(json.dumps(m))
   with self.assertRaisesRegex(ValueError,'Composite'):p.validate_dataset(d)
if __name__=='__main__':unittest.main()
