from __future__ import annotations

import argparse, csv, json, math, os, re, statistics, sys, threading, time, webbrowser
from collections import Counter
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from evaluators import EvaluationEngine
from providers import DeepSeekConnector, MockConnector, OpenAIConnector, ProviderConnector, ProviderResult

ROOT = Path(__file__).resolve().parent
LIBRARY_PATH = ROOT / "benchmarks" / "library.json"
RESULTS_DIR = ROOT / "results"
RUNS_DIR = RESULTS_DIR / "runs"
DASHBOARD_DIR = ROOT / "dashboard"
ENV_PATH = ROOT / ".env"
DEFAULT_PORT = 8765
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_MAX_ATTEMPTS = 2
DEFAULT_TRIALS = 3
STAGES = ["Benchmark Library","Trial Scheduler","Prompt Loader","Provider Router","AI Provider","JSON Validator","Evaluation","Statistical Engine","Dashboard"]

def utc_now(): return datetime.now(timezone.utc).isoformat()
def stamp(): return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def load_dotenv():
    if not ENV_PATH.exists(): return
    for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
        s=raw.strip()
        if not s or s.startswith("#") or "=" not in s: continue
        k,v=s.split("=",1); k=k.strip(); v=v.strip().strip('"').strip("'")
        if k and k not in os.environ: os.environ[k]=v

def load_library():
    x=json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    if not isinstance(x,list) or not x: raise ValueError("Benchmark library must be a non-empty JSON array.")
    return x

def write_json(path:Path,obj:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def write_csv(path:Path,rows:list[dict[str,Any]]):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text("",encoding="utf-8"); return
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def parse_output(text:str):
    try: p=json.loads(text)
    except json.JSONDecodeError as e: return None,[f"Invalid JSON: {e}"]
    if not isinstance(p,dict): return None,["Output must be a JSON object."]
    errs=[]
    if set(p)!={"answer","confidence","explanation"}: errs.append("Keys must be exactly answer, confidence, explanation.")
    c=p.get("confidence")
    if not isinstance(c,int) or isinstance(c,bool): errs.append("confidence must be an integer.")
    elif not 0<=c<=100: errs.append("confidence must be between 0 and 100.")
    if not isinstance(p.get("explanation"),str) or not p.get("explanation","").strip(): errs.append("explanation must be non-empty.")
    return p,errs

SEMANTIC_EVALUATOR=EvaluationEngine()
def evaluate(case,parsed): return SEMANTIC_EVALUATOR.evaluate(case,parsed)

def classify_provider_error(msg:str):
    low=msg.lower(); code=None
    for c in (400,401,402,403,404,408,409,422,429,500,502,503,504):
        if f"http {c}" in low: code=c; break
    if code==401: cat="AUTHENTICATION"
    elif code==402 or "insufficient balance" in low: cat="BILLING"
    elif code==429: cat="RATE_LIMIT"
    elif code in (408,504) or "timed out" in low: cat="TIMEOUT"
    elif code in (400,422): cat="REQUEST"
    elif code and code>=500: cat="PROVIDER_SERVER"
    elif any(x in low for x in ("unable to reach","connection","urlerror")): cat="NETWORK"
    else: cat="PROVIDER_ERROR"
    return {"category":cat,"http_status":code,"message":msg}

def registry(): return {"openai":OpenAIConnector(),"deepseek":DeepSeekConnector(),"mock":MockConnector()}
def choose_provider_names(req,reg):
    if req=="all":
        out=[]
        for n in ("openai","deepseek"):
            try: reg[n].validate(); out.append(n)
            except Exception: pass
        return out or ["mock"]
    reg[req].validate(); return [req]

def mean(v): return round(statistics.mean(v),3) if v else None
def median(v): return round(statistics.median(v),3) if v else None
def stdev(v): return round(statistics.stdev(v),3) if len(v)>=2 else (0.0 if v else None)

def percentile(v,q):
    if not v:return None
    x=sorted(float(i) for i in v)
    if len(x)==1:return round(x[0],3)
    p=(len(x)-1)*q; lo=math.floor(p); hi=math.ceil(p)
    return round(x[lo] if lo==hi else x[lo]+(x[hi]-x[lo])*(p-lo),3)

def answer_entropy(ans):
    if not ans:return None
    c=Counter(ans); n=len(ans); h=0.0
    for k in c.values():
        p=k/n; h-=p*math.log2(p)
    return round(h,6)

def normalized_entropy(ans):
    if not ans:return None
    k=len(set(ans))
    if k<=1:return 0.0
    return round(answer_entropy(ans)/math.log2(k),6)

def calibration_error(rows):
    x=[]
    for r in rows:
        p=r.get("parsed_output") or {}; e=r.get("evaluation") or {}
        conf=p.get("confidence"); passed=e.get("passed")
        if isinstance(conf,int) and passed in (True,False):
            x.append(abs(conf/100-(1 if passed else 0)))
    return round(100*statistics.mean(x),3) if x else None

def canonicalize_answer(case, answer):
    evaluator=case.get("evaluator","exact")
    if evaluator=="numeric_exact":
        try:
            n=float(answer); return str(int(n)) if n.is_integer() else format(n,".12g")
        except Exception:return str(answer).strip().lower()
    if evaluator=="time_exact":
        s=str(answer).strip().lower().replace(".",""); m=re.match(r"^(\d{1,2}):(\d{2})(?:\s*(am|pm))?$",s)
        if not m:return s
        h=int(m.group(1)); minute=int(m.group(2)); ap=m.group(3)
        if ap=="pm" and h!=12:h+=12
        if ap=="am" and h==12:h=0
        return f"{h:02d}:{minute:02d}" if 0<=h<24 and 0<=minute<60 else s
    if evaluator=="json_semantic":
        if not isinstance(answer,dict):return str(answer).strip().lower()
        obj={}
        for k,v in sorted(answer.items(),key=lambda kv:str(kv[0]).lower()):
            kk=str(k).strip().lower()
            if isinstance(v,str):
                vv=re.sub(r"\s+"," ",v.strip().lower())
                if kk in {"status","state","result"}:
                    if "success" in vv or "succeed" in vv or vv in {"complete","completed"}:vv="success"
                    elif "fail" in vv or "error" in vv:vv="failure"
                obj[kk]=vv
            elif isinstance(v,(int,float,bool)) or v is None:obj[kk]=v
            else:obj[kk]=str(v)
        return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    if evaluator=="sql_semantic":
        s=str(answer); s=re.sub(r"--.*?$"," ",s,flags=re.M); s=re.sub(r"/\*.*?\*/"," ",s,flags=re.S); s=s.replace("[","").replace("]","").replace('"',""); s=re.sub(r"\s+"," ",s).strip().rstrip(";").lower()
        checks={"select_customer_id":bool(re.search(r"\bselect\b.*\bcustomer_id\b",s,re.S)),"sum_aggregate":bool(re.search(r"\bsum\s*\(\s*[a-z_][a-z0-9_]*\s*\)",s)),"from_sales":bool(re.search(r"\bfrom\s+(?:[a-z_][a-z0-9_]*\.)?sales\b",s)),"group_by_customer_id":bool(re.search(r"\bgroup\s+by\s+(?:[a-z_][a-z0-9_]*\.)?customer_id\b",s)),"having_total_gt_1000":bool(re.search(r"\bhaving\b.*\bsum\s*\(\s*[a-z_][a-z0-9_]*\s*\)\s*>\s*1000(?:\.0+)?\b",s,re.S)),"descending_order":bool(re.search(r"\border\s+by\b.*\bdesc\b",s,re.S))}
        return json.dumps(checks,sort_keys=True,separators=(",",":"))
    if isinstance(answer,(dict,list)):
        try:return json.dumps(answer,sort_keys=True,separators=(",",":"),ensure_ascii=False)
        except Exception:pass
    return re.sub(r"\s+"," ",str(answer).strip().lower())

def surface_form(answer):
    if isinstance(answer,(dict,list)):
        try:return json.dumps(answer,sort_keys=False,ensure_ascii=False)
        except Exception:pass
    return str(answer)

def agreement(results,cases_by_id,a,b,semantic=False):
    ra=[r for r in results if r["provider"]==a and r["job_status"]=="EVALUATED"]; rb=[r for r in results if r["provider"]==b and r["job_status"]=="EVALUATED"]
    def val(r):
        ans=(r.get("parsed_output") or {}).get("answer"); return canonicalize_answer(cases_by_id[r["case_id"]],ans) if semantic else surface_form(ans)
    aa={(r["case_id"],r["trial"]):val(r) for r in ra}; bb={(r["case_id"],r["trial"]):val(r) for r in rb}; keys=set(aa)&set(bb)
    if not keys:return None
    return round(100*sum(1 for k in keys if aa[k]==bb[k])/len(keys),3)

def weighted_case_mean(rows,field):
    vals=[(r.get(field),r.get("trials_evaluated",0)) for r in rows if r.get(field) is not None and r.get("trials_evaluated",0)>0]
    if not vals:return None
    total=sum(w for _,w in vals); return round(sum(float(v)*w for v,w in vals)/total,6) if total else None

def token_efficiency(mean_tokens,pass_rate):
    if mean_tokens in (None,0) or pass_rate is None:return None
    return round((float(pass_rate)/float(mean_tokens))*1000,6)

def latency_tail_ratio(p95,median_v):
    if p95 is None or median_v in (None,0):return None
    return round(float(p95)/float(median_v),6)

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control","no-store, no-cache, must-revalidate, max-age=0"); self.send_header("Pragma","no-cache"); self.send_header("Expires","0"); super().end_headers()
    def log_message(self,*args): return

def launch(port):
    h=lambda *a,**k: Handler(*a,directory=str(DASHBOARD_DIR),**k)
    try: s=ThreadingHTTPServer(("127.0.0.1",port),h)
    except OSError as e: raise RuntimeError(f"Port {port} is unavailable. Stop previous PrimeAIExplorer process with Ctrl+C.") from e
    threading.Thread(target=s.serve_forever,daemon=True).start(); return s

def status_template(cases,providers,trials):
    return {"schema_version":"5.5.1","state":"starting","message":"Preparing semantic behavior fingerprinting...","updated_at_utc":utc_now(),"providers":providers,"trials_per_case":trials,"current_provider":None,"current_case":None,"current_trial":None,"completed_jobs":0,"total_jobs":len(cases)*len(providers)*trials,"pipeline":[{"name":n,"state":"pending","detail":""} for n in STAGES]}

def update_status(s,stage=None,stage_state=None,detail="",state=None,message=None,**extra):
    if state is not None:s["state"]=state
    if message is not None:s["message"]=message
    if stage:
        for x in s["pipeline"]:
            if x["name"]==stage: x["state"]=stage_state or x["state"]; x["detail"]=detail; break
    s.update(extra); s["updated_at_utc"]=utc_now(); write_json(DASHBOARD_DIR/"status.json",s)

def execute(connector,case,timeout,max_attempts,s):
    errs=[]
    for a in range(1,max_attempts+1):
        update_status(s,stage="AI Provider",stage_state="running",detail=f"{connector.name} attempt {a}/{max_attempts}")
        try:return connector.execute(case,timeout_seconds=timeout)
        except Exception as e:
            errs.append(str(e))
            if a<max_attempts: time.sleep(min(2**a,8))
    raise RuntimeError(" | ".join(errs))

def build_stats(results,providers,cases,trials):
    cases_by_id={c["case_id"]:c for c in cases}; provider_rows=[]; case_rows=[]
    for case in cases:
        for provider in providers:
            subset=[r for r in results if r["provider"]==provider and r["case_id"]==case["case_id"]]; done=[r for r in subset if r["job_status"]=="EVALUATED"]
            answers=[(r.get("parsed_output") or {}).get("answer") for r in done if r.get("parsed_output")]; sa=[surface_form(a) for a in answers]; ma=[canonicalize_answer(case,a) for a in answers]; sc=Counter(sa); mc=Counter(ma); sm,sn=(sc.most_common(1)[0] if sc else (None,0)); mm,mn=(mc.most_common(1)[0] if mc else (None,0))
            scores=[float(r["evaluation"]["score"]) for r in done]; lats=[float(r["latency_ms"]) for r in done]; conf=[float(r["parsed_output"]["confidence"]) for r in done if r.get("parsed_output") and isinstance(r["parsed_output"].get("confidence"),int)]; toks=[int(r["usage"]["total_tokens"]) for r in done if isinstance(r.get("usage",{}).get("total_tokens"),int)]; passes=sum(1 for r in done if r["evaluation"]["passed"]); pr=round(100*passes/len(done),1) if done else None; med=median(lats); p95=percentile(lats,.95); mt=mean([float(x) for x in toks])
            case_rows.append({"provider":provider,"case_id":case["case_id"],"title":case["title"],"category":case["category"],"evaluator":case.get("evaluator"),"trials_requested":trials,"trials_evaluated":len(done),"provider_errors":len(subset)-len(done),"pass_rate":pr,"mean_score":mean(scores),"score_stddev":stdev(scores),"mean_latency_ms":mean(lats),"median_latency_ms":med,"p95_latency_ms":p95,"latency_stddev_ms":stdev(lats),"latency_tail_ratio":latency_tail_ratio(p95,med),"mean_tokens":mt,"token_efficiency":token_efficiency(mt,pr),"mean_confidence":mean(conf),"confidence_calibration_error_pct":calibration_error(done),"surface_modal_answer":sm,"surface_consistency":round(100*sn/len(sa),1) if sa else None,"surface_distinct_answers":len(sc),"surface_entropy_bits":answer_entropy(sa),"surface_normalized_entropy":normalized_entropy(sa),"semantic_modal_answer":mm,"semantic_consistency":round(100*mn/len(ma),1) if ma else None,"semantic_distinct_answers":len(mc),"semantic_entropy_bits":answer_entropy(ma),"semantic_normalized_entropy":normalized_entropy(ma)})
    for provider in providers:
        subset=[r for r in results if r["provider"]==provider]; done=[r for r in subset if r["job_status"]=="EVALUATED"]; errors=[r for r in subset if r["job_status"]=="PROVIDER_ERROR"]; scores=[float(r["evaluation"]["score"]) for r in done]; lats=[float(r["latency_ms"]) for r in done]; conf=[float(r["parsed_output"]["confidence"]) for r in done if r.get("parsed_output") and isinstance(r["parsed_output"].get("confidence"),int)]; toks=[int(r["usage"]["total_tokens"]) for r in done if isinstance(r.get("usage",{}).get("total_tokens"),int)]; passes=sum(1 for r in done if r["evaluation"]["passed"]); pr=round(100*passes/len(done),1) if done else None; med=median(lats); p95=percentile(lats,.95); mt=mean([float(x) for x in toks]); pc=[r for r in case_rows if r["provider"]==provider]
        provider_rows.append({"provider":provider,"model":subset[0]["model"] if subset else "unknown","jobs_total":len(subset),"jobs_evaluated":len(done),"provider_errors":len(errors),"pass_rate":pr,"mean_score":mean(scores),"median_score":median(scores),"score_stddev":stdev(scores),"mean_latency_ms":mean(lats),"median_latency_ms":med,"p95_latency_ms":p95,"latency_stddev_ms":stdev(lats),"latency_tail_ratio":latency_tail_ratio(p95,med),"total_tokens":sum(toks) if toks else None,"mean_tokens":mt,"token_efficiency":token_efficiency(mt,pr),"mean_confidence":mean(conf),"confidence_calibration_error_pct":calibration_error(done),"mean_case_surface_entropy_bits":weighted_case_mean(pc,"surface_entropy_bits"),"mean_case_semantic_entropy_bits":weighted_case_mean(pc,"semantic_entropy_bits"),"mean_case_surface_consistency":weighted_case_mean(pc,"surface_consistency"),"mean_case_semantic_consistency":weighted_case_mean(pc,"semantic_consistency")})
    lead=sorted(provider_rows,key=lambda r:(r["jobs_evaluated"]==0,-(r["pass_rate"] if r["pass_rate"] is not None else -1),-(r["mean_case_semantic_consistency"] if r["mean_case_semantic_consistency"] is not None else -1),(r["confidence_calibration_error_pct"] if r["confidence_calibration_error_pct"] is not None else float("inf")),(r["median_latency_ms"] if r["median_latency_ms"] is not None else float("inf"))))
    for i,r in enumerate(lead,1):r["rank"]=i
    pairs=[]
    for i in range(len(providers)):
        for j in range(i+1,len(providers)):
            a,b=providers[i],providers[j]; pairs.append({"provider_a":a,"provider_b":b,"surface_agreement_pct":agreement(results,cases_by_id,a,b,False),"semantic_agreement_pct":agreement(results,cases_by_id,a,b,True)})
    return {"schema_version":"5.5.1","generated_at_utc":utc_now(),"trials_per_case":trials,"leaderboard":lead,"case_statistics":case_rows,"cross_model_agreement":pairs,"fingerprint_dimensions":["accuracy","semantic_stability","surface_stability","calibration","median_latency","p95_latency","latency_tail_ratio","token_efficiency","cross_model_semantic_agreement"]}

def load_run_results(run_id):
    run_dir=RUNS_DIR/run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run not found: {run_dir}")
    rows=[]
    for path in sorted(run_dir.glob("*/*/trial_*.json")):
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    if not rows:
        raise ValueError(f"No trial JSON files found under {run_dir}")
    return rows

def rebuild_run(run_id,cases):
    results=load_run_results(run_id)
    providers=list(dict.fromkeys(r["provider"] for r in results))
    trials=max(int(r.get("trial",1)) for r in results)
    stats=build_stats(results,providers,cases,trials)
    stats["source_run_id"]=run_id
    stats["analysis_schema_version"]="5.5.1"
    run_dir=RUNS_DIR/run_id
    write_json(run_dir/"statistics_v5_5_1.json",stats)
    write_csv(run_dir/"case_statistics_v5_5_1.csv",stats["case_statistics"])
    write_csv(run_dir/"leaderboard_v5_5_1.csv",stats["leaderboard"])
    write_json(DASHBOARD_DIR/"results.json",results)
    write_json(DASHBOARD_DIR/"statistics.json",stats)
    status=status_template(cases,providers,trials)
    status.update({"schema_version":"5.5.1","state":"complete","message":f"Rebuilt v5.5.1 analysis from stored run {run_id}.","completed_jobs":len(results),"total_jobs":len(results)})
    for x in status["pipeline"]: x["state"]="complete"
    write_json(DASHBOARD_DIR/"status.json",status)
    return results,stats

def flat_rows(results):
    out=[]
    for r in results:
        p=r.get("parsed_output") or {}; e=r.get("evaluation") or {}; pe=r.get("provider_error") or {}
        out.append({"run_id":r["run_id"],"provider":r["provider"],"model":r["model"],"case_id":r["case_id"],"category":r["category"],"trial":r["trial"],"job_status":r["job_status"],"passed":e.get("passed"),"score":e.get("score"),"evaluator":e.get("evaluator"),"latency_ms":r["latency_ms"],"total_tokens":r.get("usage",{}).get("total_tokens"),"confidence":p.get("confidence"),"answer":p.get("answer"),"provider_error_category":pe.get("category"),"provider_error_http_status":pe.get("http_status")})
    return out

def run(cases,providers,reg,s,trials):
    timeout=int(os.getenv("PROVIDER_TIMEOUT_SECONDS",os.getenv("OPENAI_TIMEOUT_SECONDS",str(DEFAULT_TIMEOUT_SECONDS)))); attempts=int(os.getenv("PROVIDER_MAX_ATTEMPTS",os.getenv("OPENAI_MAX_ATTEMPTS",str(DEFAULT_MAX_ATTEMPTS)))); run_id=stamp(); run_dir=RUNS_DIR/run_id; results=[]; done=0
    update_status(s,state="running",stage="Benchmark Library",stage_state="complete",detail=f"{len(cases)} cases"); update_status(s,stage="Trial Scheduler",stage_state="complete",detail=f"{trials} trial(s)/case")
    for pn in providers:
        conn=reg[pn]; update_status(s,stage="Provider Router",stage_state="complete",detail=pn,current_provider=pn)
        for ci,case in enumerate(cases,1):
            for tr in range(1,trials+1):
                update_status(s,stage="Prompt Loader",stage_state="complete",detail=case["case_id"],current_case={"index":ci,"case_id":case["case_id"],"title":case["title"],"category":case["category"]},current_trial=tr,message=f"{pn}: {case['title']} trial {tr}/{trials}")
                pe=None
                try: pr=execute(conn,case,timeout,attempts,s)
                except Exception as e:
                    pe=classify_provider_error(str(e)); pr=ProviderResult(provider=pn,model=getattr(conn,"model","unknown"),text="",latency_ms=0,usage={"input_tokens":None,"output_tokens":None,"total_tokens":None})
                if pe:
                    parsed=None; verr=[]; ev={"passed":None,"score":None,"evaluator":"provider_error","reason":"Not evaluated because provider execution failed.","details":{"provider_error":pe}}; job="PROVIDER_ERROR"; update_status(s,stage="JSON Validator",stage_state="warning",detail=pe["category"]); update_status(s,stage="Evaluation",stage_state="warning",detail="not scored")
                else:
                    parsed,verr=parse_output(pr.text); update_status(s,stage="JSON Validator",stage_state="complete" if not verr else "warning",detail="Valid JSON" if not verr else "Validation error"); ev={"passed":False,"score":0,"evaluator":"schema_validation","reason":"; ".join(verr),"details":{"validation_errors":verr}} if verr else evaluate(case,parsed); job="EVALUATED"; update_status(s,stage="Evaluation",stage_state="complete" if ev["passed"] else "warning",detail=f"score={ev['score']}")
                r={"schema_version":"5.5.1","run_id":run_id,"benchmark_id":case["benchmark_id"],"case_id":case["case_id"],"category":case["category"],"title":case["title"],"trial":tr,"executed_at_utc":utc_now(),"provider":pr.provider,"model":pr.model,"job_status":job,"provider_error":pe,"latency_ms":pr.latency_ms,"usage":pr.usage,"raw_output":pr.text,"parsed_output":parsed,"validation_errors":verr,"evaluation":ev,"evaluator":ev.get("evaluator")}; results.append(r); write_json(run_dir/pn/case["case_id"]/f"trial_{tr:03d}.json",r); done+=1; update_status(s,completed_jobs=done); write_json(DASHBOARD_DIR/"results.json",results)
    update_status(s,stage="Statistical Engine",stage_state="running",message="Computing repeated-trial statistics..."); stats=build_stats(results,providers,cases,trials); write_json(run_dir/"statistics.json",stats); write_json(DASHBOARD_DIR/"statistics.json",stats); write_csv(run_dir/"trials.csv",flat_rows(results)); write_csv(run_dir/"case_statistics.csv",stats["case_statistics"]); write_csv(run_dir/"leaderboard.csv",stats["leaderboard"])
    manifest={"schema_version":"5.5.1","run_id":run_id,"generated_at_utc":utc_now(),"providers":providers,"cases_total":len(cases),"trials_per_case":trials,"jobs_total":len(results),"jobs_evaluated":sum(r["job_status"]=="EVALUATED" for r in results),"provider_errors":sum(r["job_status"]=="PROVIDER_ERROR" for r in results),"outputs":["statistics.json","trials.csv","case_statistics.csv","leaderboard.csv"]}; write_json(run_dir/"run_manifest.json",manifest); write_json(RESULTS_DIR/"latest_run.json",manifest); update_status(s,state="complete",message="Semantic behavior fingerprinting run completed.",current_provider=None,current_case=None,current_trial=None,stage="Statistical Engine",stage_state="complete",detail=f"{len(providers)} providers"); update_status(s,stage="Dashboard",stage_state="complete",detail="Statistics ready")
    true_fail=sum(r["job_status"]=="EVALUATED" and r["evaluation"]["passed"] is False for r in results); return (0 if true_fail==0 and manifest["provider_errors"]==0 else 2),results,stats

def args():
    p=argparse.ArgumentParser(description="PrimeAIExplorer v5.5.1 fingerprint contract repair engine."); p.add_argument("--provider",choices=["openai","deepseek","mock","all"],default="all"); p.add_argument("--trials",type=int,default=int(os.getenv("BENCHMARK_TRIALS",str(DEFAULT_TRIALS)))); p.add_argument("--no-browser",action="store_true"); p.add_argument("--exit-after-run",action="store_true"); p.add_argument("--rebuild-run",metavar="RUN_ID",help="Rebuild v5.5.1 statistics/dashboard from stored trial JSON files without calling providers."); return p.parse_args()

def main():
    a=args();
    if a.trials<1: raise ValueError("--trials must be >= 1")
    load_dotenv(); cases=load_library(); DASHBOARD_DIR.mkdir(exist_ok=True); RESULTS_DIR.mkdir(exist_ok=True); RUNS_DIR.mkdir(exist_ok=True); port=int(os.getenv("DASHBOARD_PORT",str(DEFAULT_PORT))); server=launch(port); url=f"http://127.0.0.1:{port}/?run={stamp()}"
    if a.rebuild_run:
        results,stats=rebuild_run(a.rebuild_run,cases); print("="*80); print("PrimeAIExplorer v5.5.1 - Offline Fingerprint Contract Repair"); print("="*80); print(f"Source run         : {a.rebuild_run}"); print(f"Jobs loaded        : {len(results)}"); print(f"Dashboard          : {url}"); print("No provider/API calls were made.");
        if not a.no_browser: webbrowser.open(url)
        if a.exit_after_run: server.shutdown(); return 0
        print("Press Ctrl+C to stop the dashboard.")
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt: server.shutdown(); print("\nDashboard stopped."); return 0
    reg=registry(); providers=choose_provider_names(a.provider,reg); write_json(DASHBOARD_DIR/"results.json",[]); write_json(DASHBOARD_DIR/"statistics.json",{"schema_version":"5.5.1","leaderboard":[],"case_statistics":[]}); s=status_template(cases,providers,a.trials); write_json(DASHBOARD_DIR/"status.json",s)
    print("="*80); print("PrimeAIExplorer v5.5.1 - Fingerprint Contract Repair"); print("="*80); print(f"Providers          : {', '.join(providers)}"); print(f"Benchmark cases    : {len(cases)}"); print(f"Trials per case    : {a.trials}"); print(f"Total jobs         : {len(cases)*len(providers)*a.trials}"); print(f"Dashboard          : {url}"); print("-"*80)
    if not a.no_browser: webbrowser.open(url)
    code,results,stats=run(cases,providers,reg,s,a.trials); print(f"Jobs completed     : {len(results)}")
    for r in stats["leaderboard"]:
        pr="N/A" if r["pass_rate"] is None else f"{r['pass_rate']:.1f}%"; sc="N/A" if r["mean_score"] is None else f"{r['mean_score']:.1f}"; lat="N/A" if r["mean_latency_ms"] is None else f"{r['mean_latency_ms']:.0f} ms"; print(f"#{r['rank']} {r['provider']:<10} evaluated={r['jobs_evaluated']}/{r['jobs_total']} errors={r['provider_errors']} pass={pr} score={sc} latency={lat}")
    print("="*80)
    if a.exit_after_run: server.shutdown(); return code
    print("Press Ctrl+C to stop the dashboard.")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt: server.shutdown(); print("\nDashboard stopped.")
    return code

if __name__=="__main__":
    try: raise SystemExit(main())
    except KeyboardInterrupt: print("\nDemo stopped.",file=sys.stderr); raise SystemExit(130)
    except Exception as e: print(f"\nDEMO FAILED: {e}",file=sys.stderr); raise SystemExit(1)
