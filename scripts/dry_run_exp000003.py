from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from sequence_plugins.builtin.prime_value import PrimeValueSequencePlugin
DEFAULT=ROOT/'experiments'/'EXP-000003'/'config'/'experiment.json'

def main()->int:
    parser=argparse.ArgumentParser(description='Read-only EXP-000003 Phase A validation.')
    parser.add_argument('--config',type=Path,default=DEFAULT)
    parser.add_argument('--required-count',type=int)
    parser.add_argument('--full-monotonic-check',action='store_true')
    args=parser.parse_args()
    path=args.config.resolve()
    config=json.loads(path.read_text(encoding='utf-8'))
    config['_experiment_root']=str(path.parents[1])
    if args.full_monotonic_check:
        config.setdefault('validation',{})['full_partition_monotonic_check']=True
    result=PrimeValueSequencePlugin(config).validate_source(Path(config['repository']['prime_root']),required_count=args.required_count)
    print('PrimeAIExplorer EXP-000003 Phase A Dry Run')
    print('='*80)
    for label,key in [
        ('Plugin','plugin_id'),('Plugin version','plugin_version'),('Prime root','prime_root'),
        ('Partitions','partition_count'),('Available primes','available_prime_count'),
        ('Required primes','required_prime_count'),('Sufficient','sufficient'),('First prime','first_prime'),
        ('Last available prime','last_available_prime'),('First partition','first_partition'),
        ('Last partition','last_partition'),('Manifest exists','source_manifest_exists'),
        ('Read-only','read_only'),('Full monotonic check','full_partition_monotonic_check')]:
        value=result[key]
        if isinstance(value,int) and not isinstance(value,bool): value=f'{value:,}'
        print(f'{label:<24}{value}')
    print('='*80)
    if not result['sufficient']:
        print('[FAIL] PrimeNet source does not contain the required prime count.')
        return 1
    print('[PASS] EXP-000003 source validation passed.')
    print('[PASS] No dataset or experiment output was written.')
    return 0
if __name__=='__main__': raise SystemExit(main())
