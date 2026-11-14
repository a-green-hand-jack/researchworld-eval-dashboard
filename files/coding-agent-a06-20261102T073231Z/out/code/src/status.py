"""Compact machine-readable progress of the unattended experiment."""
import json,pathlib,time
root=pathlib.Path(__file__).resolve().parents[1];p=root/'data/responses.jsonl'
n=sum(1 for _ in p.open()) if p.exists() else 0
out=dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),responses=n,total=49152,percent=round(100*n/49152,2))
q=root/'logs/locked_choice.json'
if q.exists():out['primary_choice_frozen']=True
q=root/'logs/pipeline_complete.json'
if q.exists():out['pipeline_complete']=True
q=root/'logs/auto_pipeline.log'
if q.exists() and q.stat().st_size and not out.get('pipeline_complete'):
    out['pipeline_diagnostics']=q.read_text()[-2000:]
print(json.dumps(out))
