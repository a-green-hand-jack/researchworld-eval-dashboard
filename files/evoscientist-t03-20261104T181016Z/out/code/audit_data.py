"""Ancillary data-leakage/provenance and distinct-fit audit, no explainer outcomes used."""
from pathlib import Path
import hashlib,json,joblib,numpy as np,pandas as pd
R=Path(__file__).resolve().parent
out={}; modelhash={}
for ds in ['german','acs','pima']:
    b=joblib.load(R/'data'/f'{ds}_bundle.joblib'); raw=pd.read_csv(R/'data'/f'{ds}_features.csv'); cats=b['meta']['categorical_indices']
    category_maps={str(raw.columns[j]):sorted(raw.iloc[b['train'],j].astype(str).unique().tolist()) for j in cats}
    trh=pd.util.hash_pandas_object(raw.iloc[b['train']],index=False).to_numpy(); teh=pd.util.hash_pandas_object(raw.iloc[b['test']],index=False).to_numpy()
    out[ds]=dict(selected_duplicate_features=int(raw.iloc[b['selected']].duplicated().sum()),test_feature_rows_seen_in_train=int(np.isin(teh,trh).sum()),selected_unique_ids=len(set(map(int,b['selected']))),category_maps=category_maps)
    for kind in ['lr','rf','hgb']:
        hh=[]
        for seed in [11,29,47]:
            p=R/'models'/f'{ds}_{kind}_{seed}.joblib'; m=joblib.load(p)
            if kind=='lr': state=(m.coef_,m.intercept_,m.classes_)
            elif kind=='rf': state=([t.tree_.__getstate__() for t in m.estimators_],m.classes_)
            else: state=([t.nodes for trees in m._predictors for t in trees],m._baseline_prediction,m._bin_mapper.bin_thresholds_,m.classes_)
            h=joblib.hash(state); hh.append(h); modelhash[p.name]=dict(file_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),function_state_hash=h)
        out[ds][kind+'_distinct_function_states']=len(set(hh))
(R/'artifacts/data_extra_audit.json').write_text(json.dumps(out,indent=2)); (R/'artifacts/model_hashes.json').write_text(json.dumps(modelhash,indent=2))
print({k:{a:b for a,b in v.items() if a!='category_maps'} for k,v in out.items()})
