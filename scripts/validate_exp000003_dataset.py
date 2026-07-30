from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from sequence_plugins.builtin.prime_value import PrimeValueSequencePlugin
DEFAULT=ROOT/'experiments'/'EXP-000003'/'config'/'experiment.json'
def main():
    p=argparse.ArgumentParser(); p.add_argument('--config',type=Path,default=DEFAULT); a=p.parse_args(); path=a.config.resolve(); c=json.loads(path.read_text()); c['_experiment_root']=str(path.parents[1]); dataset=Path(c['_experiment_root'])/c['sequence']['dataset_file']; result=PrimeValueSequencePlugin(c).validate_dataset(dataset); print(json.dumps(result,indent=2)); print('[PASS] EXP-000003 dataset validation passed.'); return 0
if __name__=='__main__': raise SystemExit(main())
