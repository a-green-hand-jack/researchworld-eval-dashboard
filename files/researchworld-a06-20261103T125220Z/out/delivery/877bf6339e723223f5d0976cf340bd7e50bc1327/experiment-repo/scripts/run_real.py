"""Generate and cache real responses, with a frozen bank/partition and resumable shards."""
import argparse, datetime, hashlib, json, os, pathlib, platform, re, resource, time
import pandas as pd
from llama_cpp import Llama,__version__ as llama_version
from prompt_bank import BANK, BANK_SHA256, render


def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()


def parse_answer(text):
 # Strict direct-answer metric: explanations/extra answers are invalid and incorrect.
 m=re.fullmatch(r'\s*[\[(]?([A-J])[\])]?[.)]?\s*',text)
 return m.group(1) if m else None


def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--partition',required=True);p.add_argument('--out',required=True);p.add_argument('--shards',type=int,default=1);p.add_argument('--shard',type=int,default=0);p.add_argument('--threads',type=int,default=2);a=p.parse_args()
 assert 0<=a.shard<a.shards
 partition=json.loads(pathlib.Path(a.partition).read_text());assert partition['bank_sha256']==BANK_SHA256
 active=partition.get('active_candidates',list(range(16)));bank=[c for c in BANK if c['id'] in active]
 assert sha('data/raw/test.parquet')==partition['source_sha256']
 config=dict(model_sha256=sha(a.model),partition_sha256=sha(a.partition),bank_sha256=BANK_SHA256,script_sha256=sha(__file__),prompt_code_sha256=sha(pathlib.Path(__file__).with_name('prompt_bank.py')),llama_cpp_python=llama_version,python=platform.python_version(),n_ctx=8192,max_tokens=8,temperature=0,top_k=1,seed=20261103,threads=a.threads,shard=a.shard,shards=a.shards,active_candidates=active)
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);meta=out.with_suffix('.config.json')
 if meta.exists():assert json.loads(meta.read_text())==config,'Refusing resume with different inference configuration'
 else:meta.write_text(json.dumps(config,indent=2)+'\n')
 done=set()
 if out.exists():
  for line in out.read_text().splitlines():
   r=json.loads(line);key=(r['question_id'],r['candidate_id']);assert key not in done,'Duplicate cached pair';done.add(key)
 questions=partition['questions'][a.shard::a.shards];expected={(q['question_id'],c['id']) for q in questions for c in bank};assert done<=expected
 df=pd.read_parquet('data/raw/test.parquet');t0=time.perf_counter();cpu0=time.process_time()
 sessions=out.with_suffix('.sessions.jsonl')
 with sessions.open('a') as sf:sf.write(json.dumps(dict(event='start',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),previous_cached=len(done),config=config))+'\n')
 llm=Llama(model_path=a.model,n_ctx=8192,n_threads=a.threads,n_threads_batch=a.threads,n_batch=512,seed=20261103,verbose=False)
 # Validate every context length up front; no question is silently dropped/truncated.
 max_input=0
 for q in questions:
  row=df.iloc[q['row_index']];assert int(row.question_id)==q['question_id']
  for c in bank:
   n=len(llm.tokenize(render(row,c['id']).encode(),add_bos=True,special=True));max_input=max(max_input,n)
   assert n+8<=8192,(q['question_id'],c['id'],n,'Context too long; do not truncate')
 print(json.dumps(dict(event='preflight',remaining=len(expected-done),max_prompt_tokens=max_input,config=config)),flush=True)
 added=0
 with out.open('a') as f:
  for q in questions:
   row=df.iloc[q['row_index']]
   for c in bank:
    if (q['question_id'],c['id']) in done:continue
    prompt=render(row,c['id']);start=time.perf_counter();cstart=time.process_time()
    response=llm(prompt,max_tokens=8,temperature=0,top_k=1,stop=['<|im_end|>','\n'],echo=False)
    raw=response['choices'][0]['text'];pred=parse_answer(raw)
    out_of_range=pred is not None and ord(pred)-65>=len(row.options)
    rec=dict(question_id=q['question_id'],pool=q['pool'],category=q['category'],candidate_id=c['id'],prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),raw_output=raw,prediction=pred,answer=row.answer,correct=bool(pred==row.answer),invalid=pred is None or out_of_range,invalid_format=pred is None,out_of_range=out_of_range,option_count=len(row.options),usage=response['usage'],finish_reason=response['choices'][0]['finish_reason'],wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cstart)
    f.write(json.dumps(rec)+'\n');f.flush();added+=1
    if added%100==0:print(json.dumps(dict(event='progress',new_responses=added,total_cached=len(done)+added,target=len(expected),wall_seconds=time.perf_counter()-t0)),flush=True)
    if added%4000==0:print(f'HUTIAN_WAKE: inference shard {a.shard} reached {len(done)+added}/{len(expected)} responses; cache flushed',flush=True)
 summary=dict(config=config,added_responses=added,total_responses=len(done)+added,wall_seconds=time.perf_counter()-t0,cpu_seconds=time.process_time()-cpu0,maxrss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,max_input_tokens=max_input)
 with sessions.open('a') as sf:sf.write(json.dumps(dict(event='end',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**summary))+'\n')
 # Cumulative generation cost survives resumption; session totals retain startup/preflight.
 records=[json.loads(line) for line in out.read_text().splitlines()]
 summary['cumulative_response_wall_seconds']=sum(r['wall_seconds'] for r in records)
 summary['cumulative_response_cpu_seconds']=sum(r['cpu_seconds'] for r in records)
 summary['cumulative_prompt_tokens']=sum(r['usage']['prompt_tokens'] for r in records)
 summary['cumulative_completion_tokens']=sum(r['usage']['completion_tokens'] for r in records)
 summary['cumulative_invalid_format']=sum(r['invalid_format'] for r in records)
 summary['cumulative_out_of_range']=sum(r['out_of_range'] for r in records)
 summary['cumulative_max_token_endings']=sum(r['finish_reason']=='length' for r in records)
 out.with_suffix('.summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('HUTIAN_WAKE: inference complete '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
