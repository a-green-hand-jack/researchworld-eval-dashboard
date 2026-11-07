"""Build score matrices without extracting the large MTEB archive."""
import argparse,collections,hashlib,json,pathlib,tarfile,time
import numpy as np
import pandas as pd
ROOT=pathlib.Path(__file__).resolve().parents[1]
def mteb():
 rows=[]; audit=collections.Counter();start=time.time()
 with tarfile.open(ROOT/'data/raw/mteb.tar.gz','r|gz') as tar:
  for member in tar:
   parts=member.name.split('/')
   if len(parts)!=5 or parts[1]!='results' or not parts[-1].endswith('.json'):continue
   audit['json_files']+=1
   try:d=json.load(tar.extractfile(member))
   except (ValueError,UnicodeDecodeError):audit['invalid_json']+=1;continue
   scores=d.get('scores',{}); split=next((s for s in ('test','validation','dev') if s in scores),None)
   if split is None:audit['no_supported_split']+=1;continue
   entries=scores[split]
   if isinstance(entries,dict):entries=[entries]
   for e in entries:
    if not isinstance(e,dict):continue
    value=e.get('main_score'); langs=e.get('languages',[])
    if not isinstance(value,(int,float)) or not np.isfinite(value):audit['no_numeric_main_score']+=1;continue
    # English is explicitly labelled; no score-based language inference.
    if not any(s in ('eng','eng-Latn','en','en-Latn') for s in langs):audit['non_english_or_unlabelled']+=1;continue
    if not -1.000001<=value<=1.000001:audit['out_of_unit_range']+=1;continue
    task=d.get('task_name',parts[-1][:-5]);subset=e.get('hf_subset','default')
    rows.append(dict(model=parts[2],revision=parts[3],task=task,subset=subset,score=value,split=split,dataset_revision=d.get('dataset_revision'),source=member.name))
   if audit['json_files']%25000==0:print('parsed',audit['json_files'],'files',round(time.time()-start,1),'seconds',flush=True)
 raw=pd.DataFrame(rows);raw.to_parquet(ROOT/'data/mteb_records.parquet',index=False)
 # One model revision: greatest labelled-English task coverage, lexical revision tie-break.
 coverage=raw.groupby(['model','revision']).task.nunique().reset_index(name='coverage').sort_values(['model','coverage','revision'],ascending=[True,False,True])
 chosen=coverage.drop_duplicates('model')[['model','revision']]
 raw=raw.merge(chosen,on=['model','revision'])
 # Keep a single, most common subset signature per task, then average its English subsets.
 agg=[];taskmeta=[]
 for task,g in raw.groupby('task'):
  sig=g.groupby('model')['subset'].agg(lambda a:tuple(sorted(a)))
  common=sig.value_counts().index[0]; models=sig.index[sig==common]
  gg=g[g.model.isin(models)]
  taskmeta.append(dict(task=task,subsets=list(common),models=len(models),dataset_revisions=sorted(gg.dataset_revision.dropna().unique().tolist())))
  agg.extend(dict(model=model,task=task,score=float(h.score.mean())) for model,h in gg.groupby('model'))
 matrix=pd.DataFrame(agg).pivot(index='model',columns='task',values='score').sort_index().sort_index(axis=1)
 matrix.to_csv(ROOT/'data/mteb_all.csv')
 (ROOT/'data/mteb_tasks.json').write_text(json.dumps(taskmeta,indent=2)+'\n')
 audit.update(models=len(matrix),tasks=len(matrix.columns),observed=int(matrix.notna().sum().sum()))
 audit['elapsed_seconds']=time.time()-start
 (ROOT/'results/mteb_parse_audit.json').write_text(json.dumps(dict(audit),indent=2)+'\n');print(dict(audit),flush=True)
def open_llm():
 x=pd.read_parquet(ROOT/'data/raw/open_llm.parquet');audit={'original_rows':len(x)}
 x=x[~x.Flagged.fillna(False)].copy();x['model']=x.fullname
 x['priority']=x.Precision.map({'bfloat16':0,'float16':1,'float32':2}).fillna(3)
 x=x.sort_values(['model','priority','eval_name']).drop_duplicates('model')
 # Identical nonempty commit SHA aliases must not occur in different model splits.
 valid_sha=x['Model sha'].str.fullmatch('[0-9a-f]{40}',na=False)
 x['identity']=x['model'].where(~valid_sha,'sha:'+x['Model sha'])
 audit['distinct_names_before_sha_dedup']=len(x)
 x=x.drop_duplicates('identity')
 cols=[c for c in x if c.endswith(' Raw')]
 x=x[np.isfinite(x[cols]).all(axis=1)]
 matrix=x.set_index('model')[cols].rename(columns=lambda c:c[:-4]);matrix.to_csv(ROOT/'data/open_llm.csv')
 x.set_index('model')[['Architecture','Base Model','Submission Date','Precision','Model sha']].to_csv(ROOT/'data/open_llm_metadata.csv')
 audit.update(final_models=len(x),tasks=len(cols),observed=int(matrix.notna().sum().sum()))
 (ROOT/'results/open_llm_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(audit)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('dataset',choices=['mteb','open_llm']);a=p.parse_args();globals()[a.dataset]()
