#!/usr/bin/env python3
"""Fetch only the pinned official dataset; freeze the sample and prompt family."""
import hashlib, json, pathlib, sys, time
import numpy as np
import pandas as pd
import requests
ROOT = pathlib.Path(__file__).resolve().parents[1]
REV = 'b189ec765aa7ed75c8acfea42df31fdae71f97be'
SEED = 20261102

def prompts():
    out=[]
    instructions=[
        'Answer the multiple-choice question. Return only the single letter of the correct option, with no explanation.',
        'Carefully determine which option is correct. Check the alternatives before deciding. Output only its letter, without explanation.',
        'You are a subject-matter expert taking a knowledge exam. Choose the best answer and respond with its letter only. Do not explain.'
    ]
    for instruction in instructions:
        for header in ['plain', 'xml']:
            for delimiter in ['dot','parentheses']:
                out.append(dict(id=f'p{len(out):02d}',instruction=instruction,header=header,delimiter=delimiter))
    return out

def render(item,p):
    opts='\n'.join((f'{chr(65+i)}. {v}' if p['delimiter']=='dot' else f'({chr(65+i)}) {v}') for i,v in enumerate(item['options']))
    if p['header']=='plain':
        text=f"Question: {item['question']}\nOptions:\n{opts}\nAnswer:"
    else:
        text=f"<question>\n{item['question']}\n</question>\n<options>\n{opts}\n</options>\n<answer>"
    return p['instruction']+'\n\n'+text

def main():
    start=time.time()
    for p in ['data','configs','artifacts/raw','artifacts/results','artifacts/figures','logs','tests']:
        (ROOT/p).mkdir(parents=True,exist_ok=True)
    manifest={'revision':REV,'sample_seed':SEED,'per_subject':80,'files':{},'source':'https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro','license':'MIT (dataset card)'}
    for name in ['test-00000-of-00001.parquet','validation-00000-of-00001.parquet']:
        path=ROOT/'data'/name
        url=f'https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/resolve/{REV}/data/{name}'
        if not path.exists():
            r=requests.get(url,timeout=120); r.raise_for_status(); path.write_bytes(r.content)
        manifest['files'][name]={'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
    df=pd.read_parquet(ROOT/'data/test-00000-of-00001.parquet')
    expected='0e24a191921c2f453518a537a8b2117bd137e7714d4ef1565e9ba06c1ecb9ad8'
    assert manifest['files']['test-00000-of-00001.parquet']['sha256']==expected
    assert len(df)==12032, len(df)
    rng=np.random.default_rng(SEED)
    items=[]
    for category,group in df.groupby('category',sort=True):
        rows=rng.choice(group.index.to_numpy(),80,replace=False)
        for row in rows:
            r=df.loc[row]
            items.append({'row':int(row),'question_id':int(r['question_id']),'category':str(category),'question':str(r['question']),'options':list(r['options']),'answer_index':int(r['answer_index']),'answer':str(r['answer'])})
    assert len(items)==1120
    assert all(0<=x['answer_index']<len(x['options'])<=10 for x in items)
    qids=[x['question_id'] for x in items]; assert len(set(qids))==len(items)
    out=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in items)
    (ROOT/'data/items.jsonl').write_text(out)
    ps=prompts(); (ROOT/'configs/prompts.json').write_text(json.dumps(ps,indent=2))
    manifest.update({'n_total':len(df),'n_sample':len(items),'categories':df['category'].value_counts().sort_index().to_dict(),'sample_categories':pd.Series([x['category'] for x in items]).value_counts().sort_index().to_dict(),'duplicate_question_texts':int(pd.Series([x['question'] for x in items]).duplicated().sum()),'option_counts':pd.Series([len(x['options']) for x in items]).value_counts().sort_index().to_dict(),'sample_sha256':hashlib.sha256(out.encode()).hexdigest(),'prompts_sha256':hashlib.sha256((ROOT/'configs/prompts.json').read_bytes()).hexdigest(),'seconds':time.time()-start})
    (ROOT/'data/manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps(manifest,indent=2))
if __name__=='__main__': main()
