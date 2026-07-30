from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from sequence_plugins.loader import PluginRegistry
from sequence_plugins.builtin.prime_value import PrimeValueSequencePlugin

def check(label,condition,detail):
    print(f"[{'PASS' if condition else 'FAIL'}] {label:<32} {detail}")
    if not condition: raise SystemExit(1)

def main()->int:
    print('PrimeAIExplorer v1.3 Phase A Validator'); print('='*86)
    cfg_path=ROOT/'experiments'/'EXP-000003'/'config'/'experiment.json'
    check('EXP-000003 configuration',cfg_path.exists(),str(cfg_path))
    cfg=json.loads(cfg_path.read_text(encoding='utf-8'))
    check('Experiment ID',cfg['experiment']['id']=='EXP-000003','EXP-000003')
    check('Plugin ID',cfg['plugin']['id']=='prime_value','prime_value')
    check('Plugin version',cfg['plugin']['version']=='1.3.0','1.3.0')
    check('Repository read-only',cfg['repository']['read_only'] is True,'true')
    check('Representation',cfg['sequence']['representation']=='absolute','absolute')
    check('Target count',cfg['sequence']['target_count']==100000001,'100,000,001')
    csvr=PluginRegistry.from_path(ROOT/'registries'/'sequence_plugin_registry.csv')
    jsonr=PluginRegistry.from_path(ROOT/'registries'/'sequence_plugin_registry.json')
    check('Registry agreement',csvr.identifiers()==jsonr.identifiers(),str(len(csvr.identifiers())))
    record=csvr.get('prime_value'); plugin=csvr.create('prime_value')
    check('Registry version',record.version=='1.3.0',record.version)
    check('Plugin implementation',isinstance(plugin,PrimeValueSequencePlugin),plugin.__class__.__name__)
    check('Plugin version agreement',plugin.plugin_version==record.version,plugin.plugin_version)
    check('Prime validity',plugin.is_structurally_valid(101),'101')
    check('Composite rejection',not plugin.is_structurally_valid(105),'105')
    check('Boolean rejection',not plugin.is_structurally_valid(True),'True')
    version=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
    check('Installed version',version=='1.3.0-phase-a',version)
    print('='*86); print('PrimeAIExplorer v1.3 Phase A validation passed.'); return 0
if __name__=='__main__': raise SystemExit(main())
