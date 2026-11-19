"""Read-only independent audit of frozen saved outputs; never calls estimators."""
from pathlib import Path
import hashlib
import itertools
import json
import joblib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau

ROOT=Path('/work'); OUT=ROOT/'artifacts/analysis'
raw=pd.read_csv(OUT/'all_metrics.csv')
macro=pd.read_csv(OUT/'macro_summary.csv')
diag=pd.read_csv(OUT/'repeated_mask_summary.csv')
records=[]; manifests=[]; hashes=[]
for path in sorted((ROOT/'artifacts/runs').glob('*.json')):
    d=json.loads(path.read_text()); records.extend(d['records']); manifests.append(d)
    for f,h in d['code_hashes'].items():
        hashes.append(hashlib.sha256((ROOT/'src'/f).read_bytes()).hexdigest()==h)
r=pd.DataFrame(records); g=r[r.weighting=='group']
keys=['benchmark','regime','seed','budget','method','weighting']
joined=raw.merge(r,on=keys,suffixes=('_csv','_json'),validate='one_to_one')
report={'core_cells':sum(d['regime'] in ['iid','frontier'] for d in manifests),
        'gap_cells':sum(d['regime']=='gap' for d in manifests),
        'json_records':len(r),'summary_matches_json_rows':len(joined),
        'max_csv_json_mae_discrepancy':float(abs(joined.mae_csv-joined.mae_json).max()),
        'all_saved_code_hashes_match_current':all(hashes),'files_excluded':'artifacts/irt_runs/**'}
# Independently compute selected raw-array metrics, including all seeds and budgets.
verified=[]; qc=[]
for name in ['gsm','mmlu_pro']:
    x=np.asarray(joblib.load(ROOT/f'vendor/benchmark-prediction/data/scores/{name}.jbl'))
    _, raw_groups=np.unique(x,axis=0,return_inverse=True)
    for regime in ['iid','frontier']:
        for seed in range(5):
            p=ROOT/f'artifacts/runs/{name}__{regime}__s{seed}.npz'
            z=np.load(p,allow_pickle=False); true=z['true']; gids=z['group_ids']
            assert np.array_equal(gids,raw_groups[z['target_rows']])
            assert not np.intersect1d(raw_groups[z['source_rows']],raw_groups[z['target_rows']]).size
            _, independent_rep=np.unique(raw_groups[z['target_rows']],return_index=True)
            qc.append({'bank':name,'regime':regime,'seed':seed,
                       'true_max_error':float(abs(true-x[z['target_rows']].mean(1)).max()),
                       'rep_matches':bool(np.array_equal(independent_rep,z['rep'])),
                       'disjoint_rows':not bool(np.intersect1d(z['source_rows'],z['target_rows']).size),
                       'unique_target_groups':len(independent_rep)})
            for b in [10,25,50,100]:
                u,s,pp,aa=[z[f'{a}_{b}'] for a in ['u','s','sp','sa']]
                assert len(u)==len(np.unique(u))==len(s)==len(np.unique(s))==b
                assert not np.intersect1d(pp,aa).size and len(pp)+len(aa)==b
                for k in z.files:
                    if not k.endswith(f'__b{b}') or k.startswith('aux'): continue
                    method=k.split('__')[0]; pred=z[k]
                    for weighting,ix in [('group',independent_rep),('row',np.arange(len(true)))]:
                        e=pred[ix]-true[ix]
                        saved=r[(r.benchmark==name)&(r.regime==regime)&(r.seed==seed)&(r.budget==b)&(r.method==method)&(r.weighting==weighting)].iloc[0]
                        vals={'mae':float(np.mean(np.abs(e))),'mse':float(np.mean(e**2)),
                              'rmse':float(np.sqrt(np.mean(e**2))),'bias':float(np.mean(e))}
                        verified.append(dict(benchmark=name,regime=regime,seed=seed,budget=b,method=method,weighting=weighting,
                                             targets=len(ix),**vals,max_saved_error=max(abs(v-saved[k]) for k,v in vals.items())))
v=pd.DataFrame(verified); v.to_csv(OUT/'independent_metric_verification.csv',index=False)
report['npz_verification']={'banks':['gsm','mmlu_pro'],'core_npz_files':20,'metric_rows':len(v),
 'max_saved_error':float(v.max_saved_error.max()),'max_raw_truth_error':max(q['true_max_error'] for q in qc),
 'all_rep_matches':all(q['rep_matches'] for q in qc),'all_source_target_disjoint':all(q['disjoint_rows'] for q in qc),
 'all_selected_budgets_unique_disjoint_and_exact':True,'all_raw_response_groups_match_and_source_target_groups_disjoint':True}
# Independent summaries and contrasts, exact enumeration of sign flips.
bank=g.groupby(['regime','budget','method','benchmark'])[['mae','mse','bias','rho','tau','pair_agreement']].mean().reset_index()
agg=bank.groupby(['regime','budget','method']).agg(mae=('mae','mean'),mse=('mse','mean'),bias=('bias','mean'),rho=('rho','mean')).reset_index()
agg['rmse']=np.sqrt(agg.mse)
a=agg.merge(macro,on=['regime','budget','method'],suffixes=('_audit','_saved'),validate='one_to_one')
report['max_macro_discrepancy']={k:float(abs(a[k+'_audit']-a[k+'_saved']).max()) for k in ['mae','rmse','bias','rho']}
effects=[]
for regime in ['iid','frontier']:
    p=bank[(bank.regime==regime)&(bank.budget==50)].pivot(index='benchmark',columns='method',values='mae')
    for baseline in ['uniform','stratified_mean']:
        delta=(p.scfd-p[baseline]).to_numpy(); n=len(delta)
        rng=np.random.default_rng(701)
        boot=np.mean(delta[rng.integers(0,n,size=(10000,n))],axis=1)
        ci=np.quantile(boot,[.025,.975]); signs=np.array(list(itertools.product([-1,1],repeat=n)))
        pv=float(np.mean(np.abs(signs@delta/n)>=abs(delta.mean())-1e-14))
        seed=g[(g.regime==regime)&(g.budget==50)].groupby(['seed','method']).mae.mean().unstack()
        ds=seed.scfd-seed[baseline]
        e=dict(regime=regime,baseline=baseline,delta=float(delta.mean()),lo=float(ci[0]),hi=float(ci[1]),
               p_signflip=pv,better_banks=int((delta<0).sum()),relative_reduction_pct=float(-100*delta.mean()/p[baseline].mean()),
               seed_delta_sd=float(ds.std(ddof=1)),seed_deltas=ds.tolist(),
               delta_without_seed2=float(ds.drop(2).mean()),
               leave_one_bank_out_range=[float((np.sum(delta)-delta).min()/(n-1)),float((np.sum(delta)-delta).max()/(n-1))],
               losing_banks={str(k):float(v) for k,v in (p.scfd-p[baseline]).items() if v>0})
        effects.append(e)
order=np.argsort([e['p_signflip'] for e in effects]); mx=0
for rank,ix in enumerate(order):
    mx=max(mx,min(1,(len(effects)-rank)*effects[ix]['p_signflip'])); effects[ix]['p_holm']=mx
report['effects']=effects
saved_effects=json.loads((OUT/'primary_effects.json').read_text())
report['max_effect_discrepancy']=max(abs(e[k]-s[k]) for e,s in zip(effects,saved_effects) for k in ['delta','lo','hi','p_signflip','p_holm'])
# Repeated-mask independent decomposition and covariance-aware MCSE.
repeated=[]; paired=[]; individual=[]; discrepancies=[]
for path in sorted((ROOT/'artifacts/diagnostics').glob('*.npz')):
    name,regime,b=path.stem.split('__'); budget=int(b[1:]); z=np.load(path,allow_pickle=False)
    true=z['true']; R=len(z['scfd']); J=len(true)
    for method in z.files:
        if method in ['true','target_rows']:continue
        e=z[method]-true[None,:]; mb=e.mean(axis=1); ma=np.abs(e).mean(axis=1); mi=np.square(e).mean(axis=1)
        vpop=e.var(axis=0,ddof=0).mean(); b2=np.square(e.mean(axis=0)).mean(); mse=np.square(e).mean()
        vals=dict(bias=mb.mean(),bias_mcse=mb.std(ddof=1)/np.sqrt(R),mae=ma.mean(),mae_mcse=ma.std(ddof=1)/np.sqrt(R),mse=mse,
                  variance=vpop,bias_squared=b2,max_abs_individual_bias=np.abs(e.mean(axis=0)).max(),out_of_range=((z[method]<0)|(z[method]>1)).mean())
        sv=diag[(diag.benchmark==name)&(diag.regime==regime)&(diag.budget==budget)&(diag.method==method)].iloc[0]
        discrepancies.extend(abs(float(val)-float(sv[k])) for k,val in vals.items())
        repeated.append(dict(benchmark=name,regime=regime,budget=budget,method=method,**vals,rmse=np.sqrt(mse),mse_mcse=mi.std(ddof=1)/np.sqrt(R),
                            decomposition_error=abs(mse-vpop-b2),
                            mc_corrected_bias_squared=b2-vpop/(R-1),
                            aggregate_bias_squared=mb.mean()**2,
                            naive_independent_target_bias_mcse=np.sqrt(e.var(axis=0,ddof=1).sum()/(R*J*J))))
        for j in range(J):
            individual.append(dict(benchmark=name,regime=regime,budget=budget,method=method,target_row=int(z['target_rows'][j]),
                bias=float(e[:,j].mean()),bias_mcse=float(e[:,j].std(ddof=1)/np.sqrt(R))))
    for baseline in ['uniform','stratified_mean','stratified_difference','aipw_population','scfd_no_audit','scfd_contaminated','scfd_one']:
        e=z['scfd']-true; f=z[baseline]-true
        for loss in ['mae','mse']:
            diff=(np.abs(e)-np.abs(f) if loss=='mae' else e**2-f**2).mean(axis=1)
            sd=diff.std(ddof=1)/np.sqrt(R)
            paired.append(dict(benchmark=name,regime=regime,budget=budget,baseline=baseline,loss=loss,
                               delta=float(diff.mean()),mcse=float(sd),lo=float(diff.mean()-1.96*sd),hi=float(diff.mean()+1.96*sd)))
rd=pd.DataFrame(repeated);rd.to_csv(OUT/'independent_mask_verification.csv',index=False)
pd.DataFrame(paired).to_csv(OUT/'independent_mask_paired_differences.csv',index=False)
pd.DataFrame(individual).to_csv(OUT/'independent_mask_target_bias.csv',index=False)
report['repeated_verification']={'npz_files':8,'records':len(rd),'max_saved_discrepancy':max(discrepancies),
 'max_decomposition_error':float(rd.decomposition_error.max()),
 'max_abs_scfd_bias_over_mcse':float((rd[rd.method=='scfd'].bias.abs()/rd[rd.method=='scfd'].bias_mcse).max())}
report['frontier_splits_identical_across_seeds']=all(all(d['source_rows']==ds[0]['source_rows'] and d['target_rows']==ds[0]['target_rows'] for d in ds) for name in g.benchmark.unique() if (ds:=[d for d in manifests if d['benchmark']==name and d['regime']=='frontier']))
report['main_out_of_range']=g[g.regime.isin(['iid','frontier'])].groupby('method').out_of_range.agg(['mean','max']).to_dict('index')
report['frontier_b50_out_of_range']=g[(g.regime=='frontier')&(g.budget==50)].groupby('method').out_of_range.agg(['mean','max']).to_dict('index')
(OUT/'independent_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
print('\nFRONTIER MASK PANEL')
print(rd[(rd.regime=='frontier')&rd.method.isin(['scfd','aipw_population','scfd_no_audit','scfd_contaminated','stratified_mean'])][['benchmark','budget','method','mae','bias','bias_mcse','mse','variance','bias_squared','mc_corrected_bias_squared']].to_string(index=False))
print('\nTWO BANK B50')
print(v[(v.budget==50)&(v.weighting=='group')&v.method.isin(['uniform','stratified_mean','scfd','aipw_population'])].groupby(['benchmark','regime','method'])[['mae','mse']].mean().to_string())
