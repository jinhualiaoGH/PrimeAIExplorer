from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from sequence_plugins.builtin.prime_value import PrimeValueSequencePlugin
def main():
 c=json.loads((ROOT/'experiments/EXP-000003/config/experiment.json').read_text()); checks=[('experiment version',c['experiment']['version']=='1.3.0-phase-b'),('atomic build',c['build']['atomic'] is True),('overwrite default',c['build']['overwrite'] is False),('sample count',c['validation']['sampled_primality_count']==1000),('plugin version',PrimeValueSequencePlugin.plugin_version=='1.3.0'),('installed version',(ROOT/'VERSION').read_text().strip()=='1.3.0-phase-b')]
 print('PrimeAIExplorer v1.3 Phase B Validator\n'+'='*72)
 for label,ok in checks:
  print(f"[{'PASS' if ok else 'FAIL'}] {label}")
  if not ok:return 1
 print('='*72+'\nPrimeAIExplorer v1.3 Phase B validation passed.');return 0
if __name__=='__main__':raise SystemExit(main())
