"""Freeze outcome-blind cohort, prompt family, and acquisition contract."""
import json, hashlib, pathlib, datetime
import numpy as np
import pandas as pd
ROOT=pathlib.Path(__file__).resolve().parents[1]
REV='b189ec765aa7ed75c8acfea42df31fdae71f97be'
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    raw=pd.read_parquet(ROOT/'data/test-00000-of-00001.parquet')
    raw['key']=raw.apply(lambda r: ' '.join((r.question+' '+ ' '.join(r.options)).lower().split()),axis=1)
    duplicate_rows=int(raw.duplicated('key',keep=False).sum())
    conflicts=raw.groupby('key').answer_index.nunique(); bad=set(conflicts[conflicts>1].index)
    eligible=raw[~raw.key.isin(bad)].drop_duplicates('key').copy()
    cats=sorted(eligible.category.unique()); counts=eligible.category.value_counts()
    N=600; left=N-2*len(cats); quotas=np.array([counts[c] for c in cats])*left/len(eligible)
    alloc=np.floor(quotas).astype(int)+2
    order=np.argsort(-(quotas-np.floor(quotas)),kind='stable')
    alloc[order[:N-int(alloc.sum())]]+=1
    rng=np.random.default_rng(2201); rows=[]
    for c,k in zip(cats,alloc):
        sub=eligible[eligible.category==c]; rows.extend(rng.choice(sub.index,k,replace=False).tolist())
    rng.shuffle(rows)
    records=[]
    for ix in rows:
        r=eligible.loc[ix];records.append({'question_id':int(r.question_id),'category':r.category,'question':r.question,'options':list(r.options),'answer':r.answer,'answer_index':int(r.answer_index)})
    prompts=[]
    for explain in [False,True]:
      for eliminate in [False,True]:
       for expert in [False,True]:
        prefix=('You are a careful subject-matter expert in {category}. ' if expert else 'Answer the following multiple-choice question. ')
        prefix+=('Compare the options and eliminate incorrect alternatives. ' if eliminate else 'Choose the single best answer. ')
        prefix+=('Give a brief explanation (at most 50 words), then your final answer. ' if explain else 'Return only your final answer. ')
        prefix+='End with exactly one final line in this format: ANSWER: <letter>.'
        prompts.append({'id':len(prompts),'expert':expert,'eliminate':eliminate,'explain':explain,'instruction':prefix})
    cfg={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dataset':'TIGER-Lab/MMLU-Pro','revision':REV,'N':N,'K':8,'model':'gpt-5.6-luna','model_identity':'Unverified model alias served by supplied API; not an authenticated model release','temperature':0,'max_tokens':192,'repetitions':2000,'multiplier_draws':999,'n_grid':[16,32,64,128],'audit_m':128,'seed_namespaces':{'cohort':2201,'simulation':1101,'replay':3301,'final':4401,'multiplier':5501,'request_order':6601},'parser':'Exactly one ANSWER: <A-J> marker on the last nonblank line, case insensitive; invalid/missing/conflicting markers score incorrect; no content retries.','prompts':prompts,'allocation':dict(zip(cats,map(int,alloc))),'eligible':len(eligible),'duplicate_rows':duplicate_rows,'conflicting_keys':len(bad),'budget':{'scored_calls':4800,'max_attempts_per_cell':4,'max_tokens_per_response':192,'concurrency':8,'currency':'Endpoint provides neither tariff nor balance; dollar expenditure is unobservable. Hard call/output caps used instead. See deviations.md.'}}
    for name,obj in [('cohort.json',records),('config.json',cfg)]:
        p=ROOT/'data'/name;p.write_text(json.dumps(obj,indent=2,ensure_ascii=False))
    manifest={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [ROOT/'plan.md',ROOT/'data/cohort.json',ROOT/'data/config.json',ROOT/'data/test-00000-of-00001.parquet',pathlib.Path(__file__)]}
    (ROOT/'data/freeze_sha256.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({k:v for k,v in cfg.items() if k!='prompts'},indent=2))
if __name__=='__main__': main()
