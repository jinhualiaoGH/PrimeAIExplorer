import argparse,json
from .engine import *
def main():
 p=argparse.ArgumentParser(); s=p.add_subparsers(dest='cmd',required=True)
 a=s.add_parser('analyze'); a.add_argument('records'); a.add_argument('--output',required=True); a.add_argument('--bins',type=int,default=10); a.add_argument('--bootstrap-samples',type=int,default=2000)
 c=s.add_parser('compare'); c.add_argument('--model',action='append',required=True); c.add_argument('--output',required=True)
 x=p.parse_args()
 if x.cmd=='analyze':
  r=load_jsonl(x.records); z=analyze_records(r,bins=x.bins,bootstrap_samples=x.bootstrap_samples); write_bundle(x.output,z); print(json.dumps(z,indent=2,sort_keys=True)); return
 d={}
 for item in x.model:
  label,sep,path=item.partition('=')
  if not sep: raise ValueError('--model must use LABEL=PATH')
  d[label]=load_jsonl(path)
 lb=build_leaderboard(d); labels=sorted(d); comps=[compare_models(a,d[a],b,d[b]) for i,a in enumerate(labels) for b in labels[i+1:]]
 z=analyze_records([r for rs in d.values() for r in rs]); write_bundle(x.output,z,lb,comps); print(json.dumps({'leaderboard':lb,'comparisons':comps},indent=2,sort_keys=True))
if __name__=='__main__': main()
