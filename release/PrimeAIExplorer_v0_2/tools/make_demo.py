from __future__ import annotations
import argparse,csv,json,shutil
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument("--root",required=True);a=p.parse_args();root=Path(a.root)
 if root.exists(): shutil.rmtree(root)
 pilot=root/"pilot_001";pilot.mkdir(parents=True)
 rows=[("CASE-W004-0001",6,6,74,"A repeated small gap suggests six."),("CASE-W008-0001",8,6,62,"Six is locally frequent."),("CASE-W016-0001",6,6,70,"The recent pattern favors six."),("CASE-W032-0001",12,10,44,"Ten is plausible from the local mix."),("CASE-W064-0001",4,4,58,"Four follows a short-gap pattern.")]
 with (root/"truth.csv").open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.writer(f);w.writerow(["case_id","actual_gap"]);w.writerows((x[0],x[1]) for x in rows)
 for case,actual,pred,conf,exp in rows:
  (pilot/f"{case}.response.json").write_text(json.dumps({"prediction":pred,"confidence":conf,"explanation":exp},indent=2),encoding="utf-8")
 print(f"Demo created: {root.resolve()}")
if __name__=="__main__":main()
