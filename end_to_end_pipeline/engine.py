from __future__ import annotations
import hashlib,json,os,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from .diagnostics import collect_diagnostics
from .io import write_json_atomic
from .models import PipelineSpecification,PipelineSummary

def _utc(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def _hash(path):
    d=hashlib.sha256()
    with Path(path).open('rb') as h:
        for block in iter(lambda:h.read(1024*1024),b''): d.update(block)
    return d.hexdigest()

class PipelineEngine:
    def __init__(self,specification:PipelineSpecification):
        self.spec=specification; self.project=Path(specification.project_root).resolve()
        self.output=Path(specification.output_root).resolve()/specification.pipeline_id
        self.logs=self.output/'logs'; self.state_path=self.output/'pipeline_state.json'
    def run(self,*,resume=True,force=False,dry_run=False):
        self.logs.mkdir(parents=True,exist_ok=True)
        diagnostics=collect_diagnostics(self.project)
        write_json_atomic(self.output/'preflight.json',diagnostics)
        if not diagnostics['success']: raise RuntimeError('pipeline preflight failed')
        state=self._load_state() if resume else self._new_state()
        if force: state=self._new_state()
        state['status']='running'; state['updated_at_utc']=_utc(); self._save(state)
        for index,stage in enumerate(self.spec.stages):
            current=state['stages'][index]
            if resume and current['status']=='completed' and self._outputs_valid(stage,current): continue
            missing=[str(self._resolve(x)) for x in stage.required_inputs if not self._resolve(x).exists()]
            if missing:
                current.update(status='failed',error_message='Missing inputs: '+', '.join(missing),completed_at_utc=_utc())
                self._save(state)
                if not stage.continue_on_error: break
                continue
            if dry_run:
                current.update(status='skipped',error_message='dry-run',completed_at_utc=_utc()); self._save(state); continue
            current.update(status='running',attempts=current['attempts']+1,started_at_utc=_utc(),error_message=None)
            self._save(state)
            env=os.environ.copy(); env.update({'PRIMEAI_PIPELINE_ID':self.spec.pipeline_id,'PRIMEAI_PIPELINE_OUTPUT':str(self.output)})
            absent=[v for v in stage.environment_variables if not env.get(v)]
            if absent:
                current.update(status='failed',error_message='Missing environment variables: '+', '.join(absent),completed_at_utc=_utc())
                self._save(state)
                if not stage.continue_on_error: break
                continue
            command=[self._expand(x) for x in stage.command]
            result=subprocess.run(command,cwd=self.project,env=env,text=True,capture_output=True,check=False)
            (self.logs/f'{index:02d}_{stage.name}.stdout.log').write_text(result.stdout,encoding='utf-8')
            (self.logs/f'{index:02d}_{stage.name}.stderr.log').write_text(result.stderr,encoding='utf-8')
            outputs={str(self._resolve(x)): _hash(self._resolve(x)) for x in stage.expected_outputs if self._resolve(x).is_file()}
            missing_outputs=[str(self._resolve(x)) for x in stage.expected_outputs if not self._resolve(x).exists()]
            success=result.returncode==0 and not missing_outputs
            current.update(status='completed' if success else 'failed',return_code=result.returncode,
              error_message=None if success else ('Missing outputs: '+', '.join(missing_outputs) if missing_outputs else result.stderr.strip() or result.stdout.strip()),
              output_hashes=outputs,completed_at_utc=_utc())
            self._save(state)
            if not success and not stage.continue_on_error: break
        failed=sum(x['status']=='failed' for x in state['stages']); completed=sum(x['status']=='completed' for x in state['stages']); skipped=sum(x['status']=='skipped' for x in state['stages'])
        state['status']='completed' if failed==0 and completed+skipped==len(state['stages']) else 'failed'
        state['completed_at_utc']=_utc(); self._save(state)
        manifest=self._manifest(state); write_json_atomic(self.output/'pipeline_manifest.json',manifest)
        summary=PipelineSummary(self.spec.pipeline_id,state['status'],len(state['stages']),completed,failed,skipped,str(self.output),str(self.output/'pipeline_manifest.json'))
        write_json_atomic(self.output/'pipeline_summary.json',summary.to_dict()); return summary
    def _resolve(self,value):
        p=Path(self._expand(value)); return p if p.is_absolute() else self.project/p
    def _expand(self,value): return value.replace('{project_root}',str(self.project)).replace('{output_root}',str(self.output)).replace('{pipeline_id}',self.spec.pipeline_id)
    def _new_state(self):
        return {'pipeline_id':self.spec.pipeline_id,'status':'pending','created_at_utc':_utc(),'updated_at_utc':_utc(),
          'stages':[{'name':x.name,'status':'pending','attempts':0,'started_at_utc':None,'completed_at_utc':None,'return_code':None,'error_message':None,'output_hashes':{}} for x in self.spec.stages]}
    def _load_state(self):
        if not self.state_path.exists(): return self._new_state()
        return json.loads(self.state_path.read_text(encoding='utf-8-sig'))
    def _save(self,state): state['updated_at_utc']=_utc(); write_json_atomic(self.state_path,state)
    def _outputs_valid(self,stage,current):
        for item in stage.expected_outputs:
            p=self._resolve(item)
            if not p.exists(): return False
            if p.is_file() and current['output_hashes'].get(str(p))!=_hash(p): return False
        return True
    def _manifest(self,state):
        files=[]
        for p in sorted(self.output.rglob('*')):
            if p.is_file() and p.name!='pipeline_manifest.json': files.append({'path':p.relative_to(self.output).as_posix(),'size_bytes':p.stat().st_size,'sha256':_hash(p)})
        return {'schema_version':'1.0','pipeline_id':self.spec.pipeline_id,'specification':self.spec.to_dict(),'state':state,'artifacts':files}
