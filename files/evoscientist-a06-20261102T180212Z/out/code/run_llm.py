"""Resumable genuine API inference. All artifacts stay beside this script.
Usage: python run_llm.py prepare|pilot|selection|audit
No answer/rationale fields are ever included in the request.
"""
import argparse,concurrent.futures,hashlib,itertools,json,os,re,threading,time,platform
from pathlib import Path
import numpy as np
import pandas as pd
import requests
ROOT=Path(__file__).resolve().parent
SEED=20261102
LOCK=threading.Lock()
def dump(name,obj): (ROOT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False))
def read(name):return json.loads((ROOT/name).read_text())
def normalize(s):return ' '.join(str(s).casefold().split())
def load_data(split='test'):
    return pd.read_parquet(ROOT/f'mmlu_{split}-00000-of-00001.parquet')
def make_prompts():
    out=[]
    for j,(expert,reason,verify,order) in enumerate(itertools.product([0,1],repeat=4)):
        parts=[]
        if expert: parts.append('You are a careful subject-matter expert taking a difficult academic examination.')
        parts.append('Choose the single best answer to the multiple-choice question.')
        if reason: parts.append('Reason through the problem before deciding; after the answer provide a brief justification of at most 80 words.')
        else: parts.append('Give the answer directly; do not provide an explanation.')
        if verify:parts.append('Check the wording and compare the alternatives carefully; avoid being distracted by plausible but incorrect choices.')
        fmt='Your response must START with FINAL: X, replacing X with exactly one uppercase option letter.'
        text='\n'.join(([fmt]+parts) if order else (parts+[fmt]))
        out.append({'id':j,'expert':expert,'reason':reason,'verify':verify,'order':order,'instruction':text,'sha256':hashlib.sha256(text.encode()).hexdigest()})
    return out

def prepare():
    if (ROOT/'split_manifest.json').exists():print('Frozen manifest already exists.');return
    df=load_data(); val=load_data('validation'); norms=df.question.map(normalize)
    eligible=np.flatnonzero(~norms.duplicated().to_numpy())
    rng=np.random.default_rng(SEED); sel=rng.choice(eligible,size=360,replace=False)
    left=np.setdiff1d(eligible,sel); aud=rng.choice(left,size=400,replace=True)
    assert set(sel).isdisjoint(set(aud))
    assert len(set(norms.iloc[sel])&set(norms.iloc[aud]))==0
    assert np.all(df.answer_index.to_numpy()==np.array([ord(x)-65 for x in df.answer]))
    manifest={'seed':SEED,'selection_indices':sel.tolist(),'audit_indices':aud.tolist(),'eligible_n':len(eligible),'selection_n':len(sel),'audit_n':len(aud),'audit_unique_n':len(set(aud)),'normalized_duplicates_removed':len(df)-len(eligible),'test_rows':len(df),'validation_rows':len(val),'category_counts':df.category.value_counts().to_dict(),'options_counts':{str(k):int(v) for k,v in df.options.map(len).value_counts().items()},'population':'first representative of each normalized question string, uniform rows; audit excludes selection questions','created_unix':time.time()}
    dump('prompts.json',make_prompts());dump('split_manifest.json',manifest)
    env={'python':platform.python_version(),'platform':platform.platform(),'cpu_count':os.cpu_count(),'model_requested':os.environ.get('RWE_MODEL'),'endpoint':os.environ.get('OPENAI_BASE_URL'),'concurrency':int(os.environ.get('LLM_CONCURRENCY','32')),'temperature':0,'max_tokens':256,'seed_control':'not supplied; API support not assumed'}
    dump('inference_environment.json',env)
    print('Prepared',manifest['eligible_n'],'unique questions; selection',len(sel),'audit',len(aud))

def parse(text,nopts):
    m=re.match(r'^\s*FINAL\s*:\s*([A-J])\b',text or '',re.I)
    if m and ord(m[1].upper())-65<nopts:return ord(m[1].upper())-65
    return -1

def cached(path):
    if not path.exists():return {}
    lines=path.read_text().splitlines(); out={}
    for k,line in enumerate(lines):
        try:r=json.loads(line)
        except json.JSONDecodeError:
            if k==len(lines)-1:raise RuntimeError('Truncated last JSONL line: repair explicitly, never silently discard')
            raise
        out[r['job_id']]=r
    return out

def worker(job,df,prompts,path,errorpath):
    t=time.time(); row=df.iloc[job['row_index']]; prompt=prompts[job['prompt_id']]
    question=row['question']+'\n\n'+'\n'.join(f'{chr(65+i)}. {x}' for i,x in enumerate(row['options']))
    messages=[{'role':'system','content':prompt['instruction']},{'role':'user','content':question}]
    payload={'model':os.environ['RWE_MODEL'],'messages':messages,'temperature':0,'max_tokens':256}
    attempts=[]; response=None
    for trial in range(5):
        try:
            rr=requests.post(os.environ['OPENAI_BASE_URL'].rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+os.environ['OPENAI_API_KEY']},json=payload,timeout=180)
            rr.raise_for_status();response=rr.json()
            text=response['choices'][0]['message'].get('content','') or ''
            break
        except Exception as e:
            attempts.append({'attempt':trial+1,'error_type':type(e).__name__,'error':str(e)[:500],'at':time.time()})
            with LOCK:
                with errorpath.open('a') as f:f.write(json.dumps({'job_id':job['job_id'],**attempts[-1]})+'\n')
            if trial==4:raise RuntimeError(f"Transport failed {job['job_id']}: {type(e).__name__}") from e
            time.sleep(min(30,2**trial))
    pred=parse(text,len(row['options']))
    rec={**job,'question_id':int(row.question_id),'category':row.category,'true_answer_index':int(row.answer_index),'parsed_answer_index':pred,'valid':pred>=0,'correct':int(pred==int(row.answer_index)),'elapsed_seconds':time.time()-t,'started_unix':t,'finished_unix':time.time(),'attempt_errors':attempts,'request':payload,'response':response}
    with LOCK:
        with path.open('a') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n');f.flush()
    return rec

def run_phase(phase):
    prompts=read('prompts.json'); manifest=read('split_manifest.json')
    df=load_data('validation' if phase=='pilot' else 'test')
    if phase=='pilot':
        jobs=[{'job_id':f'pilot:{p}','prompt_id':p,'row_index':p%8,'draw_index':p%8} for p in range(16)]
    elif phase=='selection':
        jobs=[{'job_id':f'select:{i}:{p}','prompt_id':p,'row_index':row,'draw_index':i} for i,row in enumerate(manifest['selection_indices']) for p in range(16)]
    else:
        src=cached(ROOT/'selection_raw.jsonl')
        if len(src)!=360*16:raise RuntimeError('Selection incomplete; cannot unseal audit')
        mat=np.zeros((360,16),dtype=int)
        for r in src.values():mat[r['draw_index'],r['prompt_id']]=r['correct']
        winner=int(mat.mean(0).argmax()); split=int(mat[:180].mean(0).argmax())
        decision={'full_winner':winner,'split_winner':split,'baseline':0,'selection_scores':mat.mean(0).tolist(),'split_selection_scores':mat[:180].mean(0).tolist(),'locked_unix':time.time(),'selection_sha256':hashlib.sha256((ROOT/'selection_raw.jsonl').read_bytes()).hexdigest()}
        if (ROOT/'selection_decision.json').exists():
            old=read('selection_decision.json');assert old['selection_sha256']==decision['selection_sha256'];decision=old
        else:dump('selection_decision.json',decision)
        chosen=sorted(set([winner,split,0]))
        jobs=[{'job_id':f'audit:{i}:{p}','prompt_id':p,'row_index':row,'draw_index':i} for i,row in enumerate(manifest['audit_indices']) for p in chosen]
        print('LOCKED',decision,flush=True)
    path=ROOT/f'{phase}_raw.jsonl'; done=cached(path)
    jobs=[j for j in jobs if j['job_id'] not in done]
    np.random.default_rng(SEED+{'pilot':1,'selection':2,'audit':3}[phase]).shuffle(jobs)
    print(phase,'pending',len(jobs),'cached',len(done),flush=True);start=time.time()
    elapsed=[]; failed=[]
    concurrency=int(os.environ.get('LLM_CONCURRENCY','32'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs={ex.submit(worker,j,df,prompts,path,ROOT/'transport_errors.jsonl'):j for j in jobs}
        for z,f in enumerate(concurrent.futures.as_completed(futs)):
            try:r=f.result();elapsed.append(r['elapsed_seconds'])
            except Exception as e:failed.append({'job':futs[f],'error':str(e)});print('FAILED',str(e),flush=True)
            if (z+1)%50==0 or z+1==len(jobs):print(phase,'completed',z+1,'/',len(jobs),'wall_s',round(time.time()-start,1),'failures',len(failed),flush=True)
    allr=cached(path);usage={k:sum(r['response'].get('usage',{}).get(k,0) for r in allr.values()) for k in ['prompt_tokens','completion_tokens','total_tokens']}
    summary={'phase':phase,'cached_n':len(allr),'new_n':len(elapsed),'phase_wall_seconds':time.time()-start,'request_seconds_sum':sum(r['elapsed_seconds'] for r in allr.values()),'invalid':sum(not r['valid'] for r in allr.values()),'finish_reasons':pd.Series([r['response']['choices'][0].get('finish_reason','') for r in allr.values()]).value_counts().to_dict(),'models':sorted(set(r['response'].get('model','unknown') for r in allr.values())),'usage':usage,'failures':failed}
    dump(f'{phase}_summary.json',summary);print(json.dumps(summary,indent=2),flush=True)
    if failed:raise RuntimeError('Phase incomplete; rerun to resume')
    if phase=='selection':
        a=np.zeros((360,16),dtype=np.int8)
        for r in allr.values():a[r['draw_index'],r['prompt_id']]=r['correct']
        np.savez_compressed(ROOT/'selection_matrix.npz',correct=a)
    if phase=='pilot':
        invalid=summary['invalid'];assert invalid==0,'Pilot syntax issue: review before selection'
        print('PILOT PARSING PASS',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','pilot','selection','audit']);a=p.parse_args()
    prepare() if a.phase=='prepare' else run_phase(a.phase)
