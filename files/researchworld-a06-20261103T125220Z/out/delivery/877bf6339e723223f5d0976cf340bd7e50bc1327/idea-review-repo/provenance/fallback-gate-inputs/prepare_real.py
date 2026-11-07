"""Freeze a question partition without inspecting generated model outcomes."""
import argparse,pathlib,json,hashlib
import pandas as pd
import numpy as np
from prompt_bank import BANK_SHA256
p=argparse.ArgumentParser();p.add_argument('--search',type=int,required=True);p.add_argument('--audit',type=int,required=True);p.add_argument('--seed',type=int,default=20261104);p.add_argument('--candidates',type=int,choices=[4,8,16],default=16);p.add_argument('--out',required=True);a=p.parse_args()
df=pd.read_parquet('data/raw/test.parquet')
assert df.question_id.is_unique
assert all(2<=len(opts)<=10 for opts in df.options)
assert a.search+a.audit<=len(df)
rng=np.random.default_rng(a.seed);order=rng.permutation(len(df));records=[]
for pool,indices in [('search',order[:a.search]),('audit',order[a.search:a.search+a.audit])]:
 for i in indices:
  row=df.iloc[i];records.append(dict(question_id=int(row.question_id),row_index=int(i),pool=pool,category=row.category))
candidate_order=[0]+np.random.default_rng(20261105).permutation(np.arange(1,16)).tolist()
result=dict(seed=a.seed,question_sampling='uniform_without_replacement_micro_accuracy',source_sha256=hashlib.sha256(pathlib.Path('data/raw/test.parquet').read_bytes()).hexdigest(),bank_sha256=BANK_SHA256,candidate_order=candidate_order,active_candidates=candidate_order[:a.candidates],n_search=a.search,n_audit=a.audit,questions=records)
f=pathlib.Path(a.out);f.parent.mkdir(parents=True,exist_ok=True)
if f.exists():assert json.loads(f.read_text())==result,'Refusing to replace different frozen partition'
else:f.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='questions'},indent=2))
