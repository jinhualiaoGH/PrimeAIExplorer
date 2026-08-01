from __future__ import annotations
import json,sys
from pathlib import Path
from end_to_end_pipeline import PipelineEngine,PipelineStage,build_specification
from end_to_end_pipeline.io import write_json_atomic,load_specification

def spec(tmp_path,stages):
    return build_specification(name='fixture',description='e1',project_root=str(tmp_path),output_root=str(tmp_path/'out'),stages=stages)

def test_id_deterministic(tmp_path):
    stages=[PipelineStage('a',(sys.executable,'-c','print(1)'))]
    assert spec(tmp_path,stages).pipeline_id==spec(tmp_path,stages).pipeline_id

def test_run_creates_manifest(tmp_path):
    s=spec(tmp_path,[PipelineStage('write',(sys.executable,'-c',"from pathlib import Path;Path(r'{output_root}/x.txt').parent.mkdir(parents=True,exist_ok=True);Path(r'{output_root}/x.txt').write_text('x')"),expected_outputs=('{output_root}/x.txt',))])
    summary=PipelineEngine(s).run()
    assert summary.status=='completed'; assert Path(summary.manifest_path).exists()

def test_resume_skips_valid_completed_stage(tmp_path):
    counter=tmp_path/'counter.txt'
    code=f"from pathlib import Path;p=Path(r'{counter}');p.write_text(str(int(p.read_text())+1) if p.exists() else '1')"
    s=spec(tmp_path,[PipelineStage('count',(sys.executable,'-c',code),expected_outputs=(str(counter),))])
    engine=PipelineEngine(s); engine.run(); engine.run()
    assert counter.read_text()=='1'

def test_changed_output_reexecutes(tmp_path):
    target=tmp_path/'x.txt'; code=f"from pathlib import Path;p=Path(r'{target}');p.write_text('good')"
    s=spec(tmp_path,[PipelineStage('write',(sys.executable,'-c',code),expected_outputs=(str(target),))])
    e=PipelineEngine(s); e.run(); target.write_text('bad'); e.run()
    assert target.read_text()=='good'

def test_failure_stops_later_stage(tmp_path):
    marker=tmp_path/'later.txt'
    s=spec(tmp_path,[PipelineStage('fail',(sys.executable,'-c','raise SystemExit(2)')),PipelineStage('later',(sys.executable,'-c',f"from pathlib import Path;Path(r'{marker}').write_text('x')"))])
    summary=PipelineEngine(s).run(); assert summary.status=='failed'; assert not marker.exists()

def test_specification_bom_roundtrip(tmp_path):
    s=spec(tmp_path,[PipelineStage('a',(sys.executable,'-c','print(1)'))]); p=tmp_path/'spec.json'
    p.write_text(json.dumps(s.to_dict()),encoding='utf-8-sig'); assert load_specification(p).pipeline_id==s.pipeline_id
