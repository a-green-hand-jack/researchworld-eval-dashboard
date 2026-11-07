#!/usr/bin/env python3
"""Recompute every empirical table/macro from delivered raw simulation records."""
from pathlib import Path
import json, math
import numpy as np
import pandas as pd
from scipy.stats import binom
from audit_stats import ratio_mcse
from validate_results import validate_frame
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'artifacts'/'analysis'; OUT.mkdir(parents=True,exist_ok=True)
TABLE=ROOT/'paper'/'generated'; TABLE.mkdir(parents=True,exist_ok=True)
KEYS=['suite','graph','n','design','p','method','mechanism']

def wilson(k,n):
    if not n:return np.nan,np.nan
    z=1.959963984540054; p=k/n; den=1+z*z/n
    mid=(p+z*z/(2*n))/den; half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return mid-half,mid+half

def summarize(g):
    v=g[g.status=='ok']; N=len(v); total=len(g)
    a=dict(attempts=total,valid=N,availability=N/total)
    a['availability_lo'],a['availability_hi']=wilson(N,total)
    for status in ['rank_failure','empty_arm','empty_exposure','zero_numeric_propensity']:a[status]=int((g.status==status).sum())
    for key in ['bias','bias_mcse','sd','mse','mse_mcse','rmse','rmse_mcse','conditional_bias','conditional_bias_mcse','mean_squared_bias','mean_variance','mean_leverage','signal_fit_rmse','decomposition_gap','decomposition_mcse','max_abs_error','zero_estimate_fraction','coverage','coverage_n','coverage_lo','coverage_hi','known_coverage','known_coverage_n','known_coverage_lo','known_coverage_hi']: a[key]=np.nan
    a['precision_warning']='no_valid_outputs' if not N else ('sparse_valid_local_delta_only' if N<30 else 'ordinary_local_delta')
    if not N: return pd.Series(a)
    if (v.estimate==0).all():a['precision_warning']='all_zero_estimates_unseen_tails_not_certified'
    e=v.error.to_numpy(); sq=e*e; mse=sq.mean(); rmse=np.sqrt(mse)
    sd=np.std(e,ddof=1) if N>1 else np.nan
    def strat_se(column):
        strata=g.graph_seed.to_numpy() if 'graph_seed' in g.columns else np.zeros(total)
        return ratio_mcse(column,(g.status=='ok').to_numpy(),strata)
    mse_se=strat_se(sq)
    D=sq-v.conditional_bias.to_numpy()**2-v.variance.to_numpy()
    a.update(bias=e.mean(),bias_mcse=strat_se(e),sd=sd,mse=mse,mse_mcse=mse_se,rmse=rmse,
             rmse_mcse=mse_se/(2*rmse) if rmse else np.nan,conditional_bias=v.conditional_bias.mean(),conditional_bias_mcse=strat_se(v.conditional_bias.to_numpy()),
             mean_squared_bias=np.mean(v.conditional_bias**2),mean_variance=v.variance.mean(),
             mean_leverage=v.leverage.mean(),signal_fit_rmse=v.signal_fit_rmse.mean(),
             decomposition_gap=D.mean(),decomposition_mcse=strat_se(D),max_abs_error=np.max(abs(e)),
             zero_estimate_fraction=float((v.estimate==0).mean()))
    for label,col in [('coverage','cover'),('known_coverage','oracle_cover')]:
        vals=v[col].dropna(); den=len(vals); k=int(vals.sum())
        a[label]=k/den if den else np.nan; a[label+'_n']=den
        a[label+'_lo'],a[label+'_hi']=wilson(k,den)
    return pd.Series(a)

def read(suite):
    return pd.read_csv(ROOT/'artifacts'/suite/'runs.csv.gz',dtype={x:'category' for x in ['suite','graph','design','method','mechanism','status']})

def main():
    pooled=[]; per=[]; supports=[]; validation={}; main_d=None
    for suite in ['main','size','allocation']:
        if not (ROOT/'artifacts'/suite/'runtime.json').exists():raise RuntimeError('Suite incomplete: '+suite)
        d=read(suite); cfg=json.loads((ROOT/'artifacts'/suite/'config.json').read_text())
        n_assignments=validate_frame(d,cfg,suite)
        validation[suite]=dict(rows=len(d),assignments=n_assignments,complete=True,statuses=d.status.value_counts().to_dict())
        p=d.groupby(KEYS,observed=True).apply(summarize,include_groups=False).reset_index(); pooled.append(p)
        q=d.groupby(KEYS+['graph_seed'],observed=True).apply(summarize,include_groups=False).reset_index(); per.append(q)
        ss=pd.read_csv(ROOT/'artifacts'/suite/'support.csv'); supports.append(ss.groupby(['suite','graph','n','design','p']).agg(exposure_sd=('exposure_sd','mean'),endpoint_fraction=('endpoint_fraction','mean'),full_treated_mean=('treated_full','mean'),full_control_mean=('control_full','mean'),max_s=('max_s','max'),min_s=('min_s','min'),min_full_prob=('min_full_prob','min')).reset_index())
        if suite=='main': main_d=d
    s=pd.concat(pooled,ignore_index=True); ps=pd.concat(per,ignore_index=True)
    s.to_csv(OUT/'summary.csv',index=False); ps.to_csv(OUT/'per_seed.csv',index=False); pd.concat(supports).to_csv(OUT/'support_summary.csv',index=False)
    # Prespecified within-design paired contrasts (no cross-design fake pairing).
    paired=[]
    for graph in main_d.graph.unique():
        for design in ['bernoulli','cluster']:
            for mech,a,b in [('linear','Quad','Add'),('twohop','TwoHop','Add'),('count','Count','Add'),('threshold','Oracle','Add')]:
                t=main_d[(main_d.graph==graph)&(main_d.design==design)&(main_d.mechanism==mech)&(main_d.status=='ok')]
                aa=t[t.method==a].set_index(['graph_seed','rep']); bb=t[t.method==b].set_index(['graph_seed','rep']); ix=aa.index.intersection(bb.index)
                delta=aa.loc[ix].error.to_numpy()**2-bb.loc[ix].error.to_numpy()**2
                attempts=main_d[(main_d.graph==graph)&(main_d.design==design)&(main_d.mechanism==mech)&(main_d.method==a)].set_index(['graph_seed','rep'])
                mask=attempts.index.isin(ix); values=pd.Series(delta,index=ix).reindex(attempts.index[mask]).to_numpy()
                se=ratio_mcse(values,mask,attempts.index.get_level_values('graph_seed')) if len(ix) else np.nan
                paired.append(dict(graph=str(graph),design=design,mechanism=mech,method_a=a,method_b=b,n_attempted=len(attempts),n_common=len(ix),delta_mse=delta.mean() if len(ix) else np.nan,mcse=se))
    pd.DataFrame(paired).to_csv(OUT/'paired.csv',index=False)
    # Exact finite-support numbers, computed rather than manually transcribed.
    visibility={str(d):min(1.,1000*binom.sf(math.ceil(.8*d)-1,d,.5)) for d in [8,32,128]}
    validation['threshold_visibility_union_bound_n1000']=visibility
    validation['main_assignment_count']=int(len(main_d)//70)
    validation['total_assignment_count']=sum(x['assignments'] for x in validation.values() if isinstance(x,dict) and 'assignments' in x)
    (OUT/'validation.json').write_text(json.dumps(validation,indent=2))
    def row(graph,mechanism,method='Add',design='bernoulli',suite='main',p=.5,n=None):
        t=s[(s.graph==graph)&(s.mechanism==mechanism)&(s.method==method)&(s.design==design)&(s.suite==suite)&(s.p==p)]
        if n is not None:t=t[t.n==n]
        assert len(t)==1,(graph,mechanism,method,design,suite,p,n,len(t))
        return t.iloc[0]
    def cell(r,metric='rmse',se=True):
        if not r.valid:return '--'
        val=r[metric]; err=r.get(metric+'_mcse',np.nan)
        return f'${val:.3f}\\,({err:.3f})$' if se and np.isfinite(err) else f'${val:.3f}$'
    names={'regular8':'Regular 8','regular32':'Regular 32','regular128':'Regular 128','sbm32':'SBM','ba32':'BA','ws32':'WS','ego':'ego-Facebook','stanford':'Stanford3'}
    graphs=list(names)
    lines=['\\begin{tabular}{lrrrrr}\\toprule','Graph & Add: linear & Quad: linear & Add: 2-hop & TwoHop: 2-hop & Count: count \\\\ \\midrule']
    for g in graphs:
        vals=[cell(row(g,m,k)) for m,k in [('linear','Add'),('linear','Quad'),('twohop','Add'),('twohop','TwoHop'),('count','Count')]]
        lines.append(names[g]+' & '+' & '.join(vals)+r' \\')
    lines+=['\\bottomrule\\end{tabular}']; (TABLE/'rmse_table.tex').write_text('\n'.join(lines))
    lines=['\\begin{tabular}{llrrrr}\\toprule','Graph & Design & Add bias & Signal fit & Oracle valid & H80 valid \\\\ \\midrule']
    for g in ['regular32','regular128','ws32','ego','stanford']:
        for design in ['bernoulli','cluster']:
            r=row(g,'threshold',design=design); o=row(g,'threshold','Oracle',design); h=row(g,'threshold','Hajek80',design)
            lines.append(f"{names[g]} & {'B' if design=='bernoulli' else 'C'} & {cell(r,'bias')} & {cell(r,'signal_fit_rmse',False)} & {int(o.valid)}/{int(o.attempts)} & {int(h.valid)}/{int(h.attempts)} "+r'\\')
    lines+=['\\bottomrule\\end{tabular}']; (TABLE/'support_table.tex').write_text('\n'.join(lines))
    lines=['\\begin{tabular}{lrrrrr}\\toprule','Graph & $n$ & Mean $d$ & Max $d$ & Blocks & Edge cut \\\\ \\midrule']
    graphmeta=json.loads((ROOT/'artifacts/main/graphs.json').read_text())
    for g in graphs:
        m=[t for t in graphmeta if t['graph']==g][0]
        lines.append(f"{names[g]} & {m['n']} & {m['mean_degree']:.2f} & {m['max_degree']} & {m['clusters']} & {m['cut_fraction']:.3f} "+r'\\')
    lines+=['\\bottomrule\\end{tabular}'];(TABLE/'graph_table.tex').write_text('\n'.join(lines))
    # Frequently cited values are generated LaTeX macros: no manual numeric editing.
    macros={}
    for key,g,m,k,metric in [
        ('RegEightRMSE','regular8','linear','Add','rmse'),('RegDenseRMSE','regular128','linear','Add','rmse'),
        ('RegDenseQuad','regular128','linear','Quad','rmse'),('StanCountBias','stanford','count','Add','bias'),
        ('StanCountRMSE','stanford','count','Count','rmse'),('EgoCorrCoverage','ego','correlated','Add','coverage'),
        ('EgoKnownCoverage','ego','correlated','Add','known_coverage'),('RegDenseFit','regular128','threshold','Add','signal_fit_rmse'),
        ('RegDenseBias','regular128','threshold','Add','conditional_bias'),('WSClusterThresholdBias','ws32','threshold','Add','conditional_bias')]:
        r=row(g,m,k); macros[key]=f'{r[metric]:.3f}'
    macros['MainAssignments']=f"{validation['main_assignment_count']:,}"
    macros['AllAssignments']=f"{validation['total_assignment_count']:,}"
    macros['DenseVisibilityBound']=f"{visibility['128']:.2e}"
    macros['MainSeconds']=f"{json.loads((ROOT/'artifacts/main/runtime.json').read_text())['seconds']:.1f}"
    (TABLE/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in macros.items())+'\n')
    (OUT/'claims.json').write_text(json.dumps(macros,indent=2))
    # Decomposition diagnostics restricted to OLS correct linear model, not noisy support estimators.
    decomp=s[(s.suite=='main')&(s.method=='Add')&(s.mechanism=='linear')]
    decomp[['graph','design','mse','mean_variance','decomposition_gap','decomposition_mcse']].to_csv(OUT/'decomposition.csv',index=False)
    print(json.dumps(validation,indent=2)); print('Generated',len(s),'summary cells and',len(ps),'per-seed cells')
if __name__=='__main__':main()
