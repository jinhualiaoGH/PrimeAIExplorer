import json
from metrics_engine import *
def r(cid,p,a,c,lat=.1,w=8): return {'case_id':cid,'prediction':p,'actual':a,'correct':(p==a if isinstance(p,int) else None),'confidence':c,'latency':lat,'window_size':w,'provider':'x','model':'x'}
def test_analysis():
 z=analyze_records([r('A',6,6,80),r('B',8,6,60),r('C',None,10,None)],bootstrap_samples=100,bootstrap_seed=1)
 assert z['record_count']==3 and z['evaluable_count']==2 and z['accuracy']==.5 and z['mean_absolute_error']==1.0
def test_calibration():
 z=analyze_records([r('A',6,6,100),r('B',8,6,100)],bins=2,bootstrap_samples=20)
 assert z['brier_score']==.5 and z['expected_calibration_error']==.5
def test_bootstrap_deterministic():
 a=[r('A',6,6,80),r('B',8,6,60),r('C',10,10,90)]
 assert analyze_records(a,bootstrap_samples=100,bootstrap_seed=9)['bootstrap_accuracy_lower']==analyze_records(a,bootstrap_samples=100,bootstrap_seed=9)['bootstrap_accuracy_lower']
def test_compare():
 z=compare_models('a',[r('A',6,6,80),r('B',8,6,60)],'b',[r('A',8,6,70),r('B',6,6,70)])
 assert z['wins_a']==1 and z['wins_b']==1 and z['ties']==0
def test_leaderboard():
 z=build_leaderboard({'weak':[r('A',8,6,50)],'strong':[r('A',6,6,90)]}); assert z[0]['label']=='strong' and z[0]['rank']==1
def test_load_and_export(tmp_path):
 src=tmp_path/'r.jsonl'; src.write_text(json.dumps({'case_id':'A','parsed_prediction':6,'actual_value':6,'is_correct':True,'confidence':80,'latency_seconds':.1,'window_size':8,'metadata':{'provider':'manual','provider_model':'pilot'}})+'\n',encoding='utf-8-sig')
 recs=load_jsonl(src); z=analyze_records(recs,bootstrap_samples=20); out=write_bundle(tmp_path/'out',z)
 assert recs[0]['provider']=='manual' and (out/'analysis.json').exists() and (out/'calibration.csv').exists()
