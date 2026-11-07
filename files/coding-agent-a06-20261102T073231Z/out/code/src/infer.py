"""Frozen prompt grid and resumable real-model evaluation; no gold in prompts."""
import argparse, concurrent.futures, hashlib, json, os, pathlib, time, threading
import numpy as np
import pandas as pd
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = 20261102

def configurations():
    instructions = [
        "Answer the following multiple-choice question. Output only the letter of the correct option.",
        "You are an expert in this subject. Carefully compare all options and choose the best answer. Output only its letter.",
    ]
    return [dict(id=i*12+f*4+r, instruction=s, style=f, rotation=r)
            for i,s in enumerate(instructions) for f in range(3) for r in range(4)]

def prepare():
    df = pd.read_parquet(ROOT/'data/test.parquet')
    indices = np.random.default_rng(SEED).permutation(len(df))[:2048]
    records=[]
    for position, idx in enumerate(indices):
        row=df.iloc[int(idx)]
        records.append(dict(position=position, source_row=int(idx),
            split='development' if position<1024 else 'audit',
            question_id=int(row.question_id), question=row.question,
            options=list(row.options), answer_index=int(row.answer_index), category=row.category))
    for filename, value in [('questions.json',records),('candidates.json',configurations())]:
        target=ROOT/'data'/filename
        serialized=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
        if target.exists() and target.read_text()!=serialized:
            raise RuntimeError('Refusing to overwrite a different frozen design')
        target.write_text(serialized)
    return records

def make_prompt(q,c):
    m=len(q['options']); order=np.roll(np.arange(m),-c['rotation']).tolist()
    patterns=['{}. {}','({}) {}','{}: {}']
    choices='\n'.join(patterns[c['style']].format(chr(65+j),q['options'][k]) for j,k in enumerate(order))
    user=c['instruction']+'\n\n'+q['question']+'\n\n'+choices+'\n\nAnswer:'
    prompt='<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n'+user+'<|im_end|>\n<|im_start|>assistant\n'
    return prompt,order

def main():
    a=argparse.ArgumentParser();a.add_argument('--url',default='http://127.0.0.1:8080')
    a.add_argument('--workers',type=int,default=8);a.add_argument('--limit',type=int)
    a.add_argument('--prepare-only',action='store_true');args=a.parse_args()
    qs=prepare(); cs=configurations()
    if args.prepare_only:return
    target=ROOT/'data/responses.jsonl'
    done={}
    if target.exists():
        for line in target.read_text().splitlines():
            r=json.loads(line);done[(r['position'],r['candidate'])]=r
    tasks=[(q,c) for q in qs for c in cs if (q['position'],c['id']) not in done]
    if args.limit:tasks=tasks[:args.limit]
    start=time.time();completed=0;local=threading.local()
    def run(task):
        q,c=task;prompt,order=make_prompt(q,c)
        if not hasattr(local,'session'):
            local.session=requests.Session()
            if args.url.startswith(('http://127.0.0.1:','http://localhost:')):
                local.session.trust_env=False
        payload=dict(prompt=prompt,n_predict=1,temperature=0,seed=SEED,
            grammar='root ::= [A-'+chr(64+len(order))+']', cache_prompt=True,
            id_slot=-1)
        for attempt in range(4):
            try:
                r=local.session.post(args.url+'/completion',json=payload,timeout=600)
                r.raise_for_status();out=r.json();answer=out['content'].strip()
                if len(answer)!=1 or answer not in [chr(65+j) for j in range(len(order))]:
                    raise ValueError('Invalid constrained answer: '+repr(answer))
                pred=order[ord(answer)-65]
                return dict(position=q['position'],candidate=c['id'],answer=answer,
                    prediction_index=pred,correct=int(pred==q['answer_index']),
                    prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                    tokens_evaluated=out.get('tokens_evaluated'),tokens_predicted=out.get('tokens_predicted'),
                    truncated=out.get('truncated'),timings=out.get('timings'),
                    generation_settings=out.get('generation_settings',{}),
                    completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
            except Exception as e:
                with (ROOT/'logs/inference_errors.jsonl').open('a') as f:
                    f.write(json.dumps(dict(position=q['position'],candidate=c['id'],attempt=attempt,error=str(e)))+'\n')
                if attempt==3:raise
                time.sleep(2**attempt)
    with target.open('a',buffering=1) as f, concurrent.futures.ThreadPoolExecutor(args.workers) as ex:
        # executor.map yields in submission order, making the on-disk matrix stable.
        for r in ex.map(run,tasks):
            # Settings are common; save once, avoid unnecessarily large cache.
            settings=r.pop('generation_settings')
            if not (ROOT/'logs/generation_settings.json').exists():
                (ROOT/'logs/generation_settings.json').write_text(json.dumps(settings,indent=2))
            f.write(json.dumps(r,separators=(',',':'))+'\n');completed+=1
            if len(done)+completed>=128*24 and not (ROOT/'logs/locked_choice.json').exists():
                first=np.full((128,24),-1,dtype=np.int8)
                for line in target.open():
                    rr=json.loads(line)
                    if rr['position']<128:first[rr['position'],rr['candidate']]=rr['correct']
                if (first>=0).all():
                    score=first.mean(axis=0)
                    (ROOT/'logs/locked_choice.json').write_text(json.dumps(dict(
                        candidate=int(np.argmax(score)),tune_scores=score.tolist(),
                        frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                        audit_responses_observed=sum(1 for key in done if key[0]>=1024)
                            +max(0,len(done)+completed-1024*24)),indent=2))
            if completed%128==0:
                print(json.dumps(dict(new=completed,previous=len(done),seconds=round(time.time()-start,2),
                                     responses_per_second=round(completed/(time.time()-start),3))),flush=True)
    elapsed=time.time()-start
    with (ROOT/'logs/inference_runs.jsonl').open('a') as f:
        f.write(json.dumps(dict(start_unix=start,elapsed_seconds=elapsed,new_responses=completed,
                               previous_responses=len(done),workers=args.workers))+'\n')

if __name__=='__main__':main()
