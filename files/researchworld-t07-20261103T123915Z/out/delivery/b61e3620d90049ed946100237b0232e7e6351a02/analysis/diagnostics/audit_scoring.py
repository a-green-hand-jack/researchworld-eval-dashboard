"""Independently verify saved truth, raw baselines, and primary error metrics."""
import hashlib,json,pathlib
import numpy as np,pandas as pd
from benchsmall.data import load_benchmark
from benchsmall.pipeline import Study,check_freeze,write
root=pathlib.Path(__file__).resolve().parents[1];check_freeze(root);study=Study(root);out=study.out
for path,expected in json.load(open(out/'prescore_artifact_manifest.json')).items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==expected,path
metric=pd.read_parquet(out/'metrics.parquet');primary=metric[(metric.evaluation_subset=='primary')&(metric.scenario!='family_reference')]
rows=[]
for b,bb in study.splits.items():
 x,names,original=load_benchmark(root,b)
 frame=pd.read_parquet(out/'scored_predictions.parquet',filters=[('benchmark','==',b)],columns=['benchmark','scenario','budget','repeat','method','target_row','predicted_score','true_score'])
 np.testing.assert_allclose(frame.true_score.to_numpy(),x.mean(1)[frame.target_row],atol=0,rtol=0)
 for scenario,ss in bb['scenarios'].items():
  history=x[ss['history']];df=frame[frame.scenario==scenario]
  for (k,repeat),g in df[df.method=='random_mean'].groupby(['budget','repeat']):
   items=study.items[b]['final'][repeat]['items'][:k];expected=x[np.ix_(g.target_row.to_numpy(),items)].mean(1)
   np.testing.assert_allclose(g.predicted_score,expected,atol=1e-14,rtol=0)
   diff=df[(df.method=='source_difference')&(df.budget==k)&(df.repeat==repeat)].set_index('target_row').loc[g.target_row]
   np.testing.assert_allclose(diff.predicted_score,expected+history.mean()-history[:,items].mean(),atol=1e-14,rtol=0)
  cand=df[df.method=='crossfit_difference'].set_index(['budget','repeat','target_row']).predicted_score
  clipped=df[df.method=='crossfit_clipped'].set_index(['budget','repeat','target_row']).predicted_score
  np.testing.assert_allclose(clipped.loc[cand.index],np.clip(cand,0,1),atol=0,rtol=0)
  prior=df[df.method=='source_prior'].predicted_score
  np.testing.assert_allclose(prior,history.mean(),atol=0,rtol=0)
 error=(frame.predicted_score-frame.true_score)*100;frame['abs_error']=np.abs(error);frame['squared_error']=error**2;frame['signed_error']=error
 recalc=frame.groupby(['benchmark','scenario','budget','repeat','method']).agg(mae=('abs_error','mean'),mse=('squared_error','mean'),bias=('signed_error','mean'),n=('true_score','count')).reset_index()
 joined=primary[primary.benchmark==b].merge(recalc,on=['benchmark','scenario','budget','repeat','method'],validate='one_to_one')
 assert len(joined)==len(recalc)
 for observed,expected in [(joined.mae_pp,joined.mae),(joined.rmse_pp,np.sqrt(joined.mse)),(joined.bias_pp,joined.bias)]:np.testing.assert_allclose(observed,expected,atol=1e-12,rtol=0)
 assert np.array_equal(joined.n_targets,joined.n)
 rows.append({'benchmark':b,'n_predictions':len(frame),'n_primary_cells':len(recalc),'truth_exact':True,'raw_baselines_passed':True,'clipping_exact':True,'primary_errors_passed':True})
pd.DataFrame(rows).to_csv(out/'scoring_integrity.csv',index=False)
print('Independent full-truth/baseline/clipping/error-metric checks passed on all13 benchmarks.',flush=True)
