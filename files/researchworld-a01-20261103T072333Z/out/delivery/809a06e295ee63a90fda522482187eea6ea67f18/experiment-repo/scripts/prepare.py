"""Audit frozen tables and create complete-case score matrices on [0, 1]."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
TASKS=['IFEval','BBH','MATH Lvl 5','GPQA','MUSR','MMLU-PRO']

def main():
    out=ROOT/'data/processed';out.mkdir(exist_ok=True)
    records=[]
    for path in sorted((ROOT/'data/raw/helm').glob('*.json')):
        obj=json.loads(path.read_text());subject=obj['title'].split(': ',1)[1]
        headers=[x['value'] for x in obj['header']]
        for row in obj['rows']:
            specs=row[0].get('run_spec_names',[])
            assert len(specs)==1,(subject,row[0])
            model=specs[0].split(',model=')[1].split(',')[0]
            records.append(dict(model=model,label=row[0]['value'],task=subject,score=row[headers.index('EM')]['value'],n_eval=row[headers.index('# eval')]['value'],run_spec=specs[0]))
    long=pd.DataFrame(records);assert not long.duplicated(['model','task']).any()
    matrix=long.pivot(index='model',columns='task',values='score').sort_index()
    complete=matrix.dropna()
    complete.to_csv(out/'helm.csv',float_format='%.17g')
    long.to_csv(out/'helm_cells.csv',index=False,float_format='%.17g')
    df=pd.read_parquet(ROOT/'data/raw/open_llm.parquet')
    # eval_name identifies model+precision evaluations; duplicate model names remain distinct evaluations.
    valid=np.isfinite(df[TASKS]).all(axis=1) & ~df.Flagged
    oll=df.loc[valid].set_index('eval_name')[TASKS]/100
    oll.sort_index().to_csv(out/'open_llm.csv',float_format='%.17g')
    raw=df.loc[valid].set_index('eval_name')[[t+' Raw' for t in TASKS]]
    raw.columns=TASKS;raw.sort_index().to_csv(out/'open_llm_raw.csv',float_format='%.17g')
    df.loc[valid,['eval_name','fullname','Precision','Model sha','Architecture','#Params (B)','Flagged']].to_csv(out/'open_llm_metadata.csv',index=False)
    # Sensitivity cohort: one evaluation per model name, lexicographically first eval_name; avoid cherry picking best score.
    unique=df.loc[valid].sort_values('eval_name').drop_duplicates('fullname').set_index('eval_name')[TASKS]/100
    unique.sort_index().to_csv(out/'open_llm_unique.csv',float_format='%.17g')
    for name,mat in [('helm',complete),('open_llm',oll),('open_llm_raw',raw),('open_llm_unique',unique)]:
        assert np.isfinite(mat.to_numpy()).all() and mat.min().min()>=0 and mat.max().max()<=1,name
    audit=dict(helm=dict(subjects=matrix.shape[1],union_models=matrix.shape[0],complete_models=complete.shape[0],excluded_incomplete=matrix.index[matrix.isna().any(axis=1)].tolist(),cells=len(long),n_eval_min=float(long.n_eval.min()),n_eval_max=float(long.n_eval.max()),zeros=int((complete==0).sum().sum())),
        open_llm=dict(rows=len(df),complete_finite=int(np.isfinite(df[TASKS]).all(axis=1).sum()),flagged_excluded=int(df.Flagged.sum()),retained=len(oll),unique_model_cohort=len(unique),duplicate_fullnames=int(df.fullname.duplicated().sum()),zeros=int((oll==0).sum().sum()),normalization='Published normalized task columns divided by 100; raw-column sensitivity unscaled.',max_published_average_discrepancy=float(np.abs(df[TASKS].mean(axis=1)-df['Average ⬆️']).max())))
    (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
