#!/usr/bin/env python3
"""Create complete-case matrices without imputation or rounded-score parsing."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
TASKS=['IFEval','BBH','MATH Lvl 5','GPQA','MUSR','MMLU-PRO']

def save(name,frame):
    assert frame.index.is_unique
    a=frame.to_numpy(float)
    assert np.isfinite(a).all() and (a>=0).all() and (a<=1).all()
    frame.index.name='model';frame.to_csv(ROOT/f'data/processed/{name}.csv',float_format='%.17g')

def main():
    (ROOT/'data/processed').mkdir(parents=True,exist_ok=True)
    (ROOT/'artifacts').mkdir(parents=True,exist_ok=True)
    tables={}; counts={};configs={}; subjects={}
    for p in sorted((ROOT/'data/raw/helm').glob('*.json')):
        j=json.loads(p.read_text());sub=p.stem.split('subject:')[1];v={};ev={}
        for row in j['rows']:
            model=row[0]['value'];assert model not in v
            v[model]=row[1].get('value',np.nan);ev[model]=row[3].get('value',np.nan)
            configs.setdefault(model,[]).extend(row[0].get('run_spec_names',[]))
        tables[sub]=pd.Series(v,dtype=float);counts[sub]=ev;subjects[sub]=j['title']
    h=pd.DataFrame(tables);assert h.shape[1]==57
    hc=h.dropna();valid=((hc>=0)&(hc<=1)).all(axis=1);hc=hc.loc[valid]
    save('helm',hc)
    df=pd.read_parquet(ROOT/'data/raw/contents.parquet')
    # Raw is already a fraction in the pinned export; do NOT divide it by 100.
    raw=df[[t+' Raw' for t in TASKS]].apply(pd.to_numeric,errors='coerce');raw.columns=TASKS
    norm=df[TASKS].apply(pd.to_numeric,errors='coerce')/100
    good=np.isfinite(raw).all(axis=1)&((raw>=0)&(raw<=1)).all(axis=1)
    # Preserve each configuration, including repeated model names and duplicate score rows.
    ids=df['eval_name'].astype(str)+'|row='+df.index.astype(str)
    raw.index=ids;norm.index=ids
    save('open_raw',raw.loc[good.to_numpy()])
    ngood=np.isfinite(norm).all(axis=1)&((norm>=0)&(norm<=1)).all(axis=1)&good.to_numpy()
    save('open_norm',norm.loc[ngood])
    df.assign(row_id=ids).to_csv(ROOT/'data/processed/open_metadata.csv',index=False)
    raw_valid=raw.loc[good.to_numpy()]
    stats={'helm':{'union_models':len(h),'complete_valid':len(hc),'tasks':57,'excluded_models':h.index.difference(hc.index).tolist(),'duplicate_score_rows':int(hc.duplicated().sum()),'unique_configs':len(configs)},'open_raw':{'total_rows':len(df),'complete_valid':int(good.sum()),'tasks':6,'excluded_rows':np.where(~good)[0].tolist(),'duplicate_score_rows':int(raw_valid.duplicated().sum()),'flagged':int(df.loc[good.to_numpy(),'Flagged'].sum()),'unavailable':int((~df.loc[good.to_numpy(),'Available on the hub']).sum())},'open_norm':{'complete_valid':int(ngood.sum()),'excluded_rows':np.where(~ngood)[0].tolist()},'helm_configs':configs,'helm_eval_counts':counts}
    for name in ['helm','open_raw','open_norm']:
        frame=pd.read_csv(ROOT/f'data/processed/{name}.csv',index_col=0)
        stats[name]['min']=float(frame.min().min());stats[name]['max']=float(frame.max().max())
        stats[name]['tied_pair_fraction']=float(np.mean([sum(v*(v-1) for v in frame[c].value_counts())/(len(frame)*(len(frame)-1)) for c in frame]))
    stats['official_average_max_abs_error']=float(np.max(np.abs(norm.mean(axis=1).to_numpy()-df['Average ⬆️'].to_numpy()/100)))
    (ROOT/'artifacts/data_audit.json').write_text(json.dumps(stats,indent=2))
    print(json.dumps({k:{kk:vv for kk,vv in stats[k].items() if kk not in ['excluded_rows','excluded_models']} for k in ['helm','open_raw','open_norm']},indent=2));print('official mean reconstruction error',stats['official_average_max_abs_error'])
if __name__=='__main__':main()
