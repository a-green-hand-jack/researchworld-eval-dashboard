#!/usr/bin/env python3
"""Single-question real API generation. Resume cached, integrity-checked requests."""
import argparse, concurrent.futures, hashlib, json, os, pathlib, re, threading, time
import requests
from prepare_data import ROOT, render

MODEL='gpt-5.6-luna'
SYSTEM='You answer multiple-choice examination questions accurately. Follow the requested output format.'

def parse(text, n_options):
    s=text.strip()
    # Fixed before generation: single letter, optionally one punctuation mark.
    m=re.fullmatch(r'\(?([A-J])\)?[\.!]?',s)
    return ord(m.group(1))-65 if m and ord(m.group(1))-65<n_options else -1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--workers',type=int,default=20); ap.add_argument('--pilot',action='store_true'); args=ap.parse_args()
    items=[json.loads(s) for s in (ROOT/'data/items.jsonl').read_text().splitlines()]
    prompts=json.loads((ROOT/'configs/prompts.json').read_text())
    dest=ROOT/'artifacts/raw/responses.jsonl'; errors=ROOT/'artifacts/raw/errors.jsonl'
    done={}; lock=threading.Lock(); start=time.time(); counters={'success':0,'errors':0}
    if dest.exists():
        for line in dest.read_text().splitlines():
            r=json.loads(line); key=(r['question_id'],r['prompt_id']); assert key not in done; done[key]=r
    jobs=[]
    for item in items:
        for p in prompts:
            key=(item['question_id'],p['id'])
            body={'model':MODEL,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':render(item,p)}],'temperature':0,'max_tokens':16}
            h=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
            if key in done:
                assert done[key]['request_sha256']==h
                continue
            jobs.append((item,p,body,h))
    if args.pilot: jobs=jobs[:12]
    print(f'pending={len(jobs)} cached={len(done)} workers={args.workers}',flush=True)
    base=os.environ['OPENAI_BASE_URL'].rstrip('/'); secret=os.environ['OPENAI_API_KEY']
    headers={'Authorization':'Bearer '+secret,'Content-Type':'application/json'}
    def work(job):
        item,p,body,h=job; t=time.time()
        for attempt in range(5):
            try:
                r=requests.post(base+'/chat/completions',json=body,headers=headers,timeout=120); r.raise_for_status(); o=r.json()
                choice=o['choices'][0]; text=choice['message'].get('content') or ''
                pred=parse(text,len(item['options']))
                row={'question_id':item['question_id'],'prompt_id':p['id'],'category':item['category'],'request_sha256':h,'requested_model':MODEL,'returned_model':o.get('model'),'api_id':o.get('id'),'created':o.get('created'),'content':text,'prediction':pred,'answer_index':item['answer_index'],'correct':int(pred==item['answer_index']),'valid':pred>=0,'finish_reason':choice.get('finish_reason'),'usage':o.get('usage',{}),'elapsed_seconds':time.time()-t,'attempts':attempt+1}
                with lock:
                    with dest.open('a') as f: f.write(json.dumps(row,ensure_ascii=False)+'\n')
                    counters['success']+=1
                    if counters['success']%120==0: print(f"success={counters['success']} elapsed={time.time()-start:.1f}s",flush=True)
                return
            except Exception as e:
                err={'question_id':item['question_id'],'prompt_id':p['id'],'attempt':attempt+1,'error':str(e)[:1000],'elapsed_seconds':time.time()-t}
                with lock:
                    with errors.open('a') as f: f.write(json.dumps(err)+'\n')
                    counters['errors']+=1
                time.sleep(min(2**attempt,16))
        print('FAILED',item['question_id'],p['id'],flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(work,jobs))
    result={**counters,'seconds':time.time()-start,'workers':args.workers,'pilot':args.pilot,'cached_before':len(done),'jobs':len(jobs),'model':MODEL,'base_url_host_disclosed_in_README':False}
    (ROOT/('logs/inference_pilot.json' if args.pilot else 'logs/inference_run.json')).write_text(json.dumps(result,indent=2)); print(json.dumps(result),flush=True)
if __name__=='__main__': main()
