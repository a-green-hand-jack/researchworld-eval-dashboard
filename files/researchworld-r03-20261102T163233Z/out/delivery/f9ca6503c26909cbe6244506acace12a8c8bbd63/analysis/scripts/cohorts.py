"""Predefine coverage-only, revision-consistent cohorts; never inspect score values."""
import json,pathlib
import pandas as pd
ROOT=pathlib.Path(__file__).resolve().parents[1]
x=pd.read_csv(ROOT/'data/mteb_all.csv',index_col=0)
r=pd.read_parquet(ROOT/'data/mteb_records.parquet')
cov=r.groupby(['model','revision']).task.nunique().reset_index(name='coverage').sort_values(['model','coverage','revision'],ascending=[True,False,True])
r=r.merge(cov.drop_duplicates('model')[['model','revision']],on=['model','revision'])
# Exact per-task modal dataset revision; unknown/literal None is a distinct value.
revs=r.groupby('task').dataset_revision.agg(lambda a:a.value_counts().index[0] if len(a.value_counts()) else None)
r=r[r.dataset_revision==r.task.map(revs)]
valid=r[['model','task']].drop_duplicates().assign(valid=True).pivot(index='model',columns='task',values='valid').reindex(index=x.index,columns=x.columns).fillna(False)
strict=x.where(valid)
# Combined CQADupstack score overlaps its components and is not a separate budget unit.
x=x.drop(columns=['CQADupstackRetrieval'],errors='ignore');strict=strict.drop(columns=['CQADupstackRetrieval'],errors='ignore')
audit={}
for label,source,n_models,coverage in [('mteb',strict,75,.95),('mteb_wide',strict,75,.9),('mteb_mixed',x,100,.8)]:
 top=source.notna().sum(axis=1).sort_values(ascending=False,kind='stable').head(n_models).index
 tasks=source.columns[source.loc[top].notna().mean(axis=0)>=coverage]
 y=source[tasks];y=y[y.notna().sum(axis=1)>=max(5,int(.2*len(tasks)))]
 y.to_csv(ROOT/f'data/{label}.csv')
 audit[label]={'coverage_rule':{'top_models':n_models,'min_task_fraction':coverage,'min_row_observed_fraction':.2,'min_row_observed_absolute':5},'exact_modal_dataset_revision':label!='mteb_mixed','models':len(y),'tasks':len(tasks),'complete_models':int(y.notna().all(axis=1).sum()),'observed':int(y.notna().sum().sum()),'density':float(y.notna().to_numpy().mean()),'complete_model_names':y.index[y.notna().all(axis=1)].tolist(),'task_names':tasks.tolist(),'dataset_revisions':{t:revs[t] for t in tasks} if label!='mteb_mixed' else {}}
(ROOT/'results/cohorts.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({k:{q:v for q,v in a.items() if q not in ('complete_model_names','task_names','dataset_revisions')}for k,a in audit.items()},indent=2))
