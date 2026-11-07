"""Count main input tokens without generating answers or reading gold fields."""
import json,pathlib,time
import numpy as np
import pandas as pd
from llama_cpp import Llama
from prompt_bank import render
x=pd.read_parquet('data/raw/test.parquet');part=json.loads(pathlib.Path('provenance/real-partition-preferred.json').read_text())
llm=Llama(model_path='models/qwen2.5-1.5b-instruct-q4_k_m.gguf',vocab_only=True,n_ctx=8192,verbose=False)
rows=[];start=time.perf_counter()
for q in part['questions']:
 row=x.iloc[q['row_index']]
 for c in range(16):
  n=len(llm.tokenize(render(row,c).encode(),add_bos=True,special=True));rows.append(dict(question_id=q['question_id'],candidate_id=c,input_tokens=n))
r=pd.DataFrame(rows);r.to_csv('results/main-prompt-token-census.csv.gz',index=False)
summary=dict(n_prompts=len(r),input_tokens=r.input_tokens.describe(percentiles=[.5,.9,.95,.99]).to_dict(),over_context=int((r.input_tokens+8>8192).sum()),wall_seconds=time.perf_counter()-start,warning='Tokenizer-only input census; no main model answer or correctness inspected.')
pathlib.Path('results/main-prompt-token-census.summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('HUTIAN_WAKE: token census complete '+json.dumps(summary),flush=True)
