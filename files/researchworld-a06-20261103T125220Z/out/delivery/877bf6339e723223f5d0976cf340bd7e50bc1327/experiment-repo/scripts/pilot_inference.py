"""Time actual greedy generated answers on validation only; never use test labels."""
import argparse, json, time, re, pathlib, resource, platform, hashlib
import numpy as np
import pandas as pd
from llama_cpp import Llama, __version__ as llama_version

p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--out',required=True);p.add_argument('--n',type=int,default=14);a=p.parse_args()
df=pd.read_parquet('data/raw/validation.parquet')
# First example of each category gives coverage without tuning to answers.
rows=df.groupby('category',sort=True).head(1).iloc[:a.n]
t0=time.perf_counter(); c0=time.process_time()
llm=Llama(model_path=a.model,n_ctx=4096,n_threads=2,n_threads_batch=2,n_batch=512,seed=20261103,verbose=False)
path=pathlib.Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
with path.open('w') as f:
 for _,row in rows.iterrows():
  question=row['question']+'\n'+'\n'.join(f'{chr(65+i)}. {x}' for i,x in enumerate(row['options']))+'\nAnswer:'
  prompt='<|im_start|>system\nYou are a helpful assistant. Solve the multiple-choice question. Respond with only the letter of the correct answer.<|im_end|>\n<|im_start|>user\n'+question+'<|im_end|>\n<|im_start|>assistant\n'
  start=time.perf_counter(); cpu=time.process_time()
  response=llm(prompt,max_tokens=8,temperature=0,top_k=1,stop=['<|im_end|>','\n'],echo=False)
  answer=response['choices'][0]['text'];m=re.fullmatch(r'\s*\(?([A-J])\)?[.)]?\s*',answer)
  rec=dict(question_id=int(row.question_id),category=row.category,prompt=prompt,raw_output=answer,prediction=m.group(1) if m else None,correct=bool(m and m.group(1)==row.answer),usage=response['usage'],wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu)
  f.write(json.dumps(rec)+'\n');f.flush();print(json.dumps({k:v for k,v in rec.items() if k not in ['prompt']}),flush=True)
summary=dict(model=a.model,model_sha256=hashlib.sha256(pathlib.Path(a.model).read_bytes()).hexdigest(),n=len(rows),wall_seconds=time.perf_counter()-t0,cpu_seconds=time.process_time()-c0,maxrss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,llama_cpp_python=llama_version,numpy=np.__version__,python=platform.python_version(),threads=2,n_ctx=4096)
path.with_suffix('.summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('HUTIAN_WAKE: pilot complete '+json.dumps(summary),flush=True)
