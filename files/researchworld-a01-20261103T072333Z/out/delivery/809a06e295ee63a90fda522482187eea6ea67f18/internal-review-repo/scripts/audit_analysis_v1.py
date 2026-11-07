"""Independent saved-result review; does not import study solvers."""
import json,itertools,sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import rankdata
ROOT=Path(sys.argv[1]); rng=np.random.default_rng(9182)
def scores(X,rule):
    if rule=='borda': return (rankdata(X,axis=0,method='average')-1).sum(axis=1)
    if rule=='mean':return X.mean(axis=1)
    if rule=='median':return np.median(X,axis=1)
    if rule=='minimum':return X.min(axis=1)
    return X.prod(axis=1)**(1/X.shape[1])
def succeeds(X,t,rule,strict):
    s=scores(X,rule)
    return bool(s[t]>=np.delete(s,t).max()+(1e-10 if strict else -1e-10))
report={'seed':9182,'witness_checks':0,'infeasible_all_up_checks':0,'independent_six_task_optima':0,'errors':[],'summaries':{}}
for dataset in ['helm','open_llm','open_llm_raw','open_llm_unique']:
    mat=pd.read_csv(ROOT/f'data/processed/{dataset}.csv',index_col=0);X=mat.to_numpy()
    rows=pd.concat([pd.read_csv(p) for p in (ROOT/'results').glob(f'attacks_{dataset}*.csv') if p.stem in [f'attacks_{dataset}',f'attacks_{dataset}_strict']])
    assert not rows.status.isin(['bounded','solver_failure']).any()
    sample=rows if dataset=='helm' else rows.sample(min(200,len(rows)),random_state=9182)
    for row in sample.itertuples():
        t=mat.index.get_loc(row.model);upper=np.ones(X.shape[1]) if row.ceiling=='unit' else X.max(axis=0)
        u=X[t]+row.alpha*(upper-X[t]);Y=X.copy()
        if pd.isna(row.k):
            Y[t]=u;assert not succeeds(Y,t,row.rule,row.strict),row
            report['infeasible_all_up_checks']+=1
        else:
            tasks=json.loads(row.selected_tasks);idx=mat.columns.get_indexer(tasks)
            assert len(tasks)==row.k and len(set(tasks))==len(tasks) and (idx>=0).all()
            Y[t,idx]=u[idx];assert succeeds(Y,t,row.rule,row.strict),row
            report['witness_checks']+=1
        if X.shape[1]==6:
            # Evaluate each budget in increasing order, reranking the FULL changed matrix.
            found=None
            for k in range(7):
                for idx in itertools.combinations(range(6),k):
                    Y=X.copy();Y[t,list(idx)]=u[list(idx)]
                    if succeeds(Y,t,row.rule,row.strict):found=k;break
                if found is not None:break
            assert found==(None if pd.isna(row.k) else int(row.k)),row
            report['independent_six_task_optima']+=1
    primary=rows[(rows.ceiling=='unit')&(rows.alpha==1)&(~rows.strict)]
    report['summaries'][dataset]={'n_targets':len(mat),'median_k':primary.groupby('rule').k.median().to_dict()}
print(json.dumps(report,indent=2),flush=True)
