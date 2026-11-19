"""Verify correction without repeating the unchanged optimizer study."""
import io,json,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
repo=Path('/hutian/experiment-repo'); new=Path('work/correction')
oldrev='f558276d110ab218150edb4bc8e4d6a145998eb7'
report={'old_revision':oldrev,'new_revision':subprocess.check_output(['git','-C',str(repo),'rev-parse','origin/main'],text=True).strip(),'attack_files':0,'unchanged_optimization_rows':0,'corrected_infeasible_expectations':0}
allrows=[]
for path in sorted((new/'results').glob('attacks_*.csv')):
    old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','-C',str(repo),'show',f'{oldrev}:results/{path.name}'])))
    cur=pd.read_csv(path)
    cols=old.columns.difference(['random_expected_censored_k'])
    pd.testing.assert_frame_equal(old[cols],cur[cols])
    mask=cur.random_requested & cur.status.eq('infeasible')
    keep=~mask
    pd.testing.assert_series_equal(old.loc[keep,'random_expected_censored_k'],cur.loc[keep,'random_expected_censored_k'])
    assert (cur.loc[mask,'random_expected_censored_k']==cur.loc[mask,'n_tasks']+1).all()
    assert cur.loc[mask,'random_success_at_k'].isna().all()
    assert cur.loc[cur.random_requested,'random_expected_censored_k'].notna().all()
    report['attack_files']+=1;report['unchanged_optimization_rows']+=len(cur);report['corrected_infeasible_expectations']+=int(mask.sum());allrows.append(cur)
df=pd.concat(allrows,ignore_index=True);summary=pd.read_csv(new/'results/summary.csv')
for row in summary.itertuples():
    g=df[(df.dataset==row.dataset)&(df.rule==row.rule)&(df.ceiling==row.ceiling)&(df.alpha==row.alpha)&(df.strict==row.strict)]
    assert row.n==len(g)
    assert row.random_expected_censored_k_n==g.random_expected_censored_k.notna().sum()
    assert row.random_success_at_optimum_n==g.random_success_at_k.notna().sum()
    if row.random_expected_censored_k_n: assert np.isclose(row.random_expected_censored_k,g.random_expected_censored_k.mean())
# Independently define each design's challengers using original unchanged scores/ranks.
primary=df[(df.ceiling=='unit')&(df.alpha==1)&(~df.strict)]
cs=pd.read_csv(new/'results/challenger_summary.csv');curves=pd.read_csv(new/'results/challenger_budget_curves.csv')
report['challenger_counts']={}
for dataset,g in primary.groupby('dataset'):
    winners=set(g.loc[g.baseline_rank==1,'model']);selected=set(g.model)-winners
    report['challenger_counts'][dataset]=len(selected)
    assert cs[cs.dataset==dataset].n.eq(len(selected)).all()
    for key,rows in curves[curves.dataset==dataset].groupby(['rule','alpha','ceiling','strict']):
        rule,alpha,ceiling,strict=key
        a=df[(df.dataset==dataset)&df.model.isin(selected)&(df.rule==rule)&(df.alpha==alpha)&(df.ceiling==ceiling)&(df.strict==strict)]
        for row in rows.itertuples():
            assert row.n==len(a) and row.reached==int((a.k<=row.budget).sum())
            assert np.isclose(row.fraction,(a.k<=row.budget).mean())
report['summary_rows_verified']=len(summary);report['challenger_curve_rows_verified']=len(curves)
Path('reviews/correction-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
