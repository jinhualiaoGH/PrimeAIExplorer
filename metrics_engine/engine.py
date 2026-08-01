from __future__ import annotations
import csv,json,math,random,statistics
from pathlib import Path

def load_jsonl(path):
    out=[]
    with Path(path).open('r',encoding='utf-8-sig') as h:
        for n,line in enumerate(h,1):
            if not line.strip(): continue
            x=json.loads(line)
            if not isinstance(x,dict): raise ValueError(f'Expected object at line {n}')
            m=x.get('metadata') if isinstance(x.get('metadata'),dict) else {}
            out.append({'case_id':str(x['case_id']),'prediction':x.get('parsed_prediction'),
                'actual':x.get('actual_value'),'correct':x.get('is_correct'),
                'confidence':x.get('confidence'),'latency':x.get('latency_seconds'),
                'window_size':x.get('window_size'),'provider':m.get('provider'),
                'model':m.get('provider_model')})
    return out

def _eval(r): return isinstance(r.get('prediction'),int) and isinstance(r.get('actual'),int)
def _correct(r): return bool(r['correct']) if isinstance(r.get('correct'),bool) else (_eval(r) and r['prediction']==r['actual'])
def _mean(xs): return statistics.fmean(xs) if xs else None
def _median(xs): return statistics.median(xs) if xs else None

def _bootstrap_accuracy(records,samples=2000,seed=20260801,confidence=.95):
    e=[r for r in records if _eval(r)]
    if not e:return (None,None)
    rng=random.Random(seed); vals=[]; n=len(e)
    for _ in range(samples): vals.append(sum(_correct(e[rng.randrange(n)]) for _ in range(n))/n)
    vals.sort(); a=(1-confidence)/2
    lo=vals[max(0,min(samples-1,int(math.floor(a*samples))))]
    hi=vals[max(0,min(samples-1,int(math.ceil((1-a)*samples)-1)))]
    return lo,hi

def _calibration(records,bins=10):
    groups=[[] for _ in range(bins)]
    for r in records:
        c=r.get('confidence')
        if _eval(r) and isinstance(c,int): groups[min(bins-1,int(max(0,min(100,c))/100*bins))].append(r)
    result=[]
    for i,g in enumerate(groups):
        if not g: result.append({'lower_bound':i/bins,'upper_bound':(i+1)/bins,'count':0,'mean_confidence':None,'accuracy':None,'gap':None}); continue
        mc=_mean([r['confidence']/100 for r in g]); acc=_mean([1.0 if _correct(r) else 0.0 for r in g])
        result.append({'lower_bound':i/bins,'upper_bound':(i+1)/bins,'count':len(g),'mean_confidence':mc,'accuracy':acc,'gap':abs(mc-acc)})
    return result

def _groups(records,key):
    d={}
    for r in records:
        v=r.get(key)
        if v is None: continue
        d.setdefault(str(v),[]).append(r)
    out={}
    for k,g in d.items():
        e=[r for r in g if _eval(r)]; errs=[abs(r['prediction']-r['actual']) for r in e]
        out[k]={'record_count':len(g),'evaluable_count':len(e),'accuracy':sum(_correct(r) for r in e)/len(e) if e else None,'mean_absolute_error':_mean(errs)}
    return out

def analyze_records(records,bins=10,bootstrap_samples=2000,bootstrap_seed=20260801):
    e=[r for r in records if _eval(r)]; errs=[abs(r['prediction']-r['actual']) for r in e]; sq=[x*x for x in errs]
    conf=[r for r in e if isinstance(r.get('confidence'),int)]; lat=[float(r['latency']) for r in records if isinstance(r.get('latency'),(int,float))]
    cal=_calibration(conf,bins); total=sum(x['count'] for x in cal)
    ece=sum((x['count']/total)*x['gap'] for x in cal if x['gap'] is not None) if total else None
    brier=_mean([((r['confidence']/100)-(1.0 if _correct(r) else 0.0))**2 for r in conf])
    lo,hi=_bootstrap_accuracy(e,bootstrap_samples,bootstrap_seed)
    return {'record_count':len(records),'evaluable_count':len(e),'correct_count':sum(_correct(r) for r in e),
      'missing_prediction_count':sum(not isinstance(r.get('prediction'),int) for r in records),
      'accuracy':sum(_correct(r) for r in e)/len(e) if e else None,'mean_absolute_error':_mean(errs),
      'median_absolute_error':_median(errs),'root_mean_squared_error':math.sqrt(_mean(sq)) if sq else None,
      'mean_confidence':_mean([r['confidence']/100 for r in conf]),'brier_score':brier,
      'expected_calibration_error':ece,'mean_latency_seconds':_mean(lat),'median_latency_seconds':_median(lat),
      'bootstrap_accuracy_lower':lo,'bootstrap_accuracy_upper':hi,'calibration':cal,
      'by_window_size':_groups(records,'window_size'),'by_actual_value':_groups(records,'actual')}

def compare_models(label_a,a,label_b,b):
    A={r['case_id']:r for r in a if _eval(r)}; B={r['case_id']:r for r in b if _eval(r)}; common=sorted(set(A)&set(B))
    wa=wb=t=0; ea=[]; eb=[]
    for k in common:
        xa=abs(A[k]['prediction']-A[k]['actual']); xb=abs(B[k]['prediction']-B[k]['actual']); ea.append(xa); eb.append(xb)
        if xa<xb:wa+=1
        elif xb<xa:wb+=1
        else:t+=1
    n=len(common); aa=sum(x==0 for x in ea)/n if n else None; ab=sum(x==0 for x in eb)/n if n else None
    ma=_mean(ea); mb=_mean(eb)
    return {'model_a':label_a,'model_b':label_b,'common_case_count':n,'wins_a':wa,'wins_b':wb,'ties':t,
      'accuracy_a':aa,'accuracy_b':ab,'mean_absolute_error_a':ma,'mean_absolute_error_b':mb,
      'exact_match_difference':aa-ab if n else None,'mean_absolute_error_difference':ma-mb if n else None}

def build_leaderboard(datasets):
    rows=[]
    for label,recs in datasets.items():
        a=analyze_records(recs,bootstrap_samples=500); rows.append({'label':label,**{k:a[k] for k in ('record_count','evaluable_count','accuracy','mean_absolute_error','root_mean_squared_error','expected_calibration_error','mean_latency_seconds')}})
    def key(x): return (-(x['accuracy'] if x['accuracy'] is not None else -1),x['mean_absolute_error'] if x['mean_absolute_error'] is not None else float('inf'),x['label'])
    rows.sort(key=key)
    for i,r in enumerate(rows,1): r['rank']=i
    return rows

def _csv(path,rows):
    if not rows: Path(path).write_text('',encoding='utf-8'); return
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with Path(path).open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(rows)

def write_bundle(out,analysis,leaderboard=None,comparisons=None):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    (out/'analysis.json').write_text(json.dumps(analysis,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    _csv(out/'calibration.csv',analysis['calibration'])
    _csv(out/'metrics_by_window.csv',[{'window_size':k,**v} for k,v in analysis['by_window_size'].items()])
    _csv(out/'metrics_by_actual.csv',[{'actual_value':k,**v} for k,v in analysis['by_actual_value'].items()])
    _csv(out/'leaderboard.csv',leaderboard or []); _csv(out/'comparisons.csv',comparisons or [])
    return out
