from __future__ import annotations
import json,sys
from pathlib import Path
out=Path(sys.argv[1]); out.parent.mkdir(parents=True,exist_ok=True)
rows=[
 {'case_id':'E1-001','parsed_prediction':6,'actual_value':6,'is_correct':True,'confidence':80,'latency_seconds':0.1,'window_size':8,'metadata':{'provider':'manual','provider_model':'e1-demo'}},
 {'case_id':'E1-002','parsed_prediction':8,'actual_value':6,'is_correct':False,'confidence':60,'latency_seconds':0.1,'window_size':8,'metadata':{'provider':'manual','provider_model':'e1-demo'}},
]
out.write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
