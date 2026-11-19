"""Representative validation-only inference timing at the main context setting."""
import pathlib,json,hashlib,time,resource,platform
import numpy as np
import pandas as pd
from llama_cpp import Llama,__version__ as llama_version
from prompt_bank import render,BANK_SHA256
from run_real import parse_answer
model='models/qwen2.5-1.5b-instruct-q4_k_m.gguf';out=pathlib.Path('results/real-pilot-scope.jsonl')
df=pd.read_parquet('data/raw/validation.parquet')
# Category-first plus longest validation question/options by characters (not labels).
length=df.apply(lambda r:len(r.question)+sum(map(len,r.options)),axis=1)
indices=[]
for cat in sorted(df.category.unique()):
 g=df[df.category==cat];indices.extend([int(g.index[0]),int(length.loc[g.index].idxmax())])
indices=list(dict.fromkeys(indices));candidates=[0,5,10,15]
llm=Llama(model_path=model,n_ctx=8192,n_threads=2,n_threads_batch=2,n_batch=512,seed=20261103,verbose=False)
t0=time.perf_counter();c0=time.process_time();records=[]
with out.open('w') as f:
 for i in indices:
  row=df.loc[i]
  for candidate in candidates:
   prompt=render(row,candidate);n=len(llm.tokenize(prompt.encode(),add_bos=True,special=True));assert n+8<=8192
   t=time.perf_counter();cpu=time.process_time()
   response=llm(prompt,max_tokens=8,temperature=0,top_k=1,stop=['<|im_end|>','\n'],echo=False)
   raw=response['choices'][0]['text'];pred=parse_answer(raw);oor=pred is not None and ord(pred)-65>=len(row.options)
   rec=dict(question_id=int(row.question_id),category=row.category,candidate_id=candidate,input_tokens=n,raw_output=raw,prediction=pred,invalid_format=pred is None,out_of_range=oor,finish_reason=response['choices'][0]['finish_reason'],usage=response['usage'],wall_seconds=time.perf_counter()-t,cpu_seconds=time.process_time()-cpu)
   f.write(json.dumps(rec)+'\n');f.flush();records.append(rec)
   print(json.dumps(rec),flush=True)
x=pd.DataFrame(records)
summary=dict(model=model,model_sha256=hashlib.sha256(pathlib.Path(model).read_bytes()).hexdigest(),bank_sha256=BANK_SHA256,llama_cpp_python=llama_version,python=platform.python_version(),n_ctx=8192,threads=2,max_tokens=8,n_questions=len(indices),n_responses=len(x),candidate_ids=candidates,wall_seconds=time.perf_counter()-t0,cpu_seconds=time.process_time()-c0,maxrss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,wall_per_response=x.wall_seconds.describe(percentiles=[.5,.9,.95,.99]).to_dict(),cpu_per_response=x.cpu_seconds.describe(percentiles=[.5,.9,.95,.99]).to_dict(),input_tokens=x.input_tokens.describe(percentiles=[.5,.9,.95,.99]).to_dict(),output_tokens=[int(r['usage']['completion_tokens']) for r in records],invalid_format=int(x.invalid_format.sum()),out_of_range=int(x.out_of_range.sum()),max_token_endings=int((x.finish_reason=='length').sum()))
out.with_suffix('.summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('HUTIAN_WAKE: representative pilot complete '+json.dumps(summary),flush=True)
