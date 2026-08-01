
from __future__ import annotations

import sys
from pathlib import Path

# Make the repository root importable when this file is executed directly:
#
#   py .\examples\phase_e1\build_demo_spec.py
#
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from end_to_end_pipeline import PipelineStage, build_specification
from end_to_end_pipeline.io import write_json_atomic
root=Path(__file__).resolve().parents[2]
output_root=root/'pipeline_runs'
python=sys.executable
stages=(
 PipelineStage('fixture_responses',(python,str(root/'examples/phase_e1/write_fixture.py'),'{output_root}/responses.jsonl'),expected_outputs=('{output_root}/responses.jsonl',)),
 PipelineStage('metrics',(python,'-m','metrics_engine.cli','analyze','{output_root}/responses.jsonl','--output','{output_root}/analysis'),required_inputs=('{output_root}/responses.jsonl',),expected_outputs=('{output_root}/analysis/analysis.json',)),
 PipelineStage('report',(python,'-m','report_engine.cli','{output_root}/analysis','--output','{output_root}/report','--experiment-label','phase-e1-demo','--title','PrimeAIExplorer Phase E1 Demonstration'),required_inputs=('{output_root}/analysis/analysis.json',),expected_outputs=('{output_root}/report/report.html','{output_root}/report/report_manifest.json')),
)
spec=build_specification(name='PrimeAIExplorer Phase E1 Demonstration',description='Offline end-to-end metrics and report pipeline.',project_root=str(root),output_root=str(output_root),stages=stages,metadata={'mode':'offline-demo'})
destination=root/'examples/phase_e1/pipeline_specification.json'
write_json_atomic(destination,spec.to_dict())
print(destination)
print(spec.pipeline_id)
