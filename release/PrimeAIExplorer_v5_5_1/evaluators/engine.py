
from __future__ import annotations
import math, re
from typing import Any

class EvaluationEngine:
    def evaluate(self, case: dict[str,Any], parsed: dict[str,Any] | None) -> dict[str,Any]:
        if parsed is None:
            return self._r(False,0,"unavailable","No parsed model output.",{})
        kind=case.get("evaluator") or self._infer(case)
        answer=parsed.get("answer")
        if kind=="numeric_exact": return self._numeric(case,answer)
        if kind=="json_semantic": return self._json(case,answer)
        if kind=="sql_semantic": return self._sql(case,answer)
        if kind=="time_exact": return self._time(case,answer)
        if kind=="contains": return self._contains(case,answer)
        return self._exact(case,answer)

    def _infer(self,case):
        cat=str(case.get("category","")).lower(); exp=case.get("expected_answer")
        if cat=="sql": return "sql_semantic"
        if isinstance(exp,dict): return "json_semantic"
        if cat=="numerical reasoning": return "numeric_exact"
        if cat=="logical reasoning": return "time_exact"
        if "expected_contains" in case: return "contains"
        return "exact"

    def _r(self,passed,score,evaluator,reason,details):
        return {"passed":bool(passed),"score":int(max(0,min(100,score))),"evaluator":evaluator,"reason":reason,"details":details}

    def _exact(self,case,answer):
        exp=case.get("expected_answer"); ok=answer==exp
        return self._r(ok,100 if ok else 0,"exact","Exact answer match." if ok else "Answer differs from expected value.",{"expected":exp,"observed":answer})

    def _numeric(self,case,answer):
        exp=case.get("expected_answer")
        try: ok=math.isfinite(float(answer)) and float(answer)==float(exp)
        except (TypeError,ValueError): ok=False
        return self._r(ok,100 if ok else 0,"numeric_exact","Numerical value matches." if ok else "Numerical value differs.",{"expected":exp,"observed":answer})

    @staticmethod
    def _norm(v):
        s=str(v).strip().lower(); s=re.sub(r"[_\-]+"," ",s); s=re.sub(r"\s+"," ",s)
        return s.strip(" .,:;!?")

    def _status(self,v):
        s=self._norm(v)
        if s in {"success","successful","successfully completed","completed successfully","completed","complete","succeeded","processed successfully"} or "success" in s or "succeed" in s: return "success"
        if s in {"failure","failed","error","unsuccessful","completed unsuccessfully"} or "fail" in s or "error" in s: return "failure"
        return s

    def _scalar(self,key,exp,obs,tol):
        if isinstance(exp,bool): return obs is exp
        if isinstance(exp,(int,float)) and not isinstance(exp,bool):
            try:return math.isclose(float(obs),float(exp),rel_tol=0.0,abs_tol=tol)
            except (TypeError,ValueError):return False
        if key.lower() in {"status","state","result"}: return self._status(obs)==self._status(exp)
        return self._norm(obs)==self._norm(exp)

    def _json(self,case,answer):
        exp=case.get("expected_answer")
        if not isinstance(exp,dict) or not isinstance(answer,dict):
            return self._r(False,0,"json_semantic","Expected and observed answers must both be JSON objects.",{"expected_type":type(exp).__name__,"observed_type":type(answer).__name__})
        tol=float(case.get("numeric_tolerance",1e-9)); fr={}
        for k,v in exp.items(): fr[k]=k in answer and self._scalar(k,v,answer[k],tol)
        matched=sum(fr.values()); score=round(100*matched/len(exp)) if exp else 100; ok=matched==len(exp)
        return self._r(ok,score,"json_semantic","All required JSON fields are semantically equivalent." if ok else f"{matched}/{len(exp)} required fields are semantically equivalent.",{"field_results":fr,"missing_fields":sorted(set(exp)-set(answer)),"extra_fields":sorted(set(answer)-set(exp))})

    @staticmethod
    def _norm_sql(sql):
        s=str(sql); s=re.sub(r"--.*?$"," ",s,flags=re.M); s=re.sub(r"/\*.*?\*/"," ",s,flags=re.S)
        s=s.replace("[","").replace("]","").replace('"',""); return re.sub(r"\s+"," ",s).strip().rstrip(";").lower()

    def _sql(self,case,answer):
        s=self._norm_sql(answer)
        checks={
            "select_customer_id":bool(re.search(r"\bselect\b.*\bcustomer_id\b",s,re.S)),
            "sum_aggregate":bool(re.search(r"\bsum\s*\(\s*[a-z_][a-z0-9_]*\s*\)",s)),
            "from_sales":bool(re.search(r"\bfrom\s+(?:[a-z_][a-z0-9_]*\.)?sales\b",s)),
            "group_by_customer_id":bool(re.search(r"\bgroup\s+by\s+(?:[a-z_][a-z0-9_]*\.)?customer_id\b",s)),
            "having_total_gt_1000":bool(re.search(r"\bhaving\b.*\bsum\s*\(\s*[a-z_][a-z0-9_]*\s*\)\s*>\s*1000(?:\.0+)?\b",s,re.S)),
            "descending_order":bool(re.search(r"\border\s+by\b.*\bdesc\b",s,re.S)),
        }
        matched=sum(checks.values()); score=round(100*matched/len(checks)); ok=matched==len(checks)
        return self._r(ok,score,"sql_semantic","SQL satisfies all required structural semantics." if ok else f"SQL satisfies {matched}/{len(checks)} required structural semantics.",{"checks":checks,"normalized_sql":s})

    def _time(self,case,answer):
        def norm(v):
            s=str(v).strip().lower().replace(".","")
            m=re.match(r"^(\d{1,2}):(\d{2})(?:\s*(am|pm))?$",s)
            if not m:return None
            h=int(m.group(1)); minute=int(m.group(2)); ap=m.group(3)
            if ap=="pm" and h!=12:h+=12
            if ap=="am" and h==12:h=0
            return f"{h:02d}:{minute:02d}" if 0<=h<24 and 0<=minute<60 else None
        exp=norm(case.get("expected_answer")); obs=norm(answer); ok=exp is not None and obs==exp
        return self._r(ok,100 if ok else 0,"time_exact","Normalized time matches." if ok else "Normalized time differs.",{"expected":exp,"observed":obs})

    def _contains(self,case,answer):
        req=[self._norm(x) for x in case.get("expected_contains",[])]; obs=self._norm(answer); matched=[x for x in req if x in obs]
        score=round(100*len(matched)/len(req)) if req else 100; ok=len(matched)==len(req)
        return self._r(ok,score,"contains",f"Matched {len(matched)}/{len(req)} required semantic fragments.",{"required":req,"matched":matched})
