"""Independently verify supplementary moments, contrast uncertainty and claims.

Reads completed checkpoints and tables only. No model fits, result selection or
statistical decisions occur. This complements the main raw-to-summary audit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t

p=argparse.ArgumentParser();p.add_argument('--root',default='.')
a=p.parse_args();root=Path(a.root).resolve();notes=root/('analysis' if (root/'code').exists() else 'notes')
folder=root/'results/diagnostics'
checks=0

def equal(a,b,label):
    global checks
    assert np.isclose(a,b,rtol=2e-9,atol=2e-11,equal_nan=True),(label,a,b)
    checks+=1

def moments(row,key,values):
    v=np.asarray(values,float);v=v[np.isfinite(v)]
    mean=v.mean() if len(v) else np.nan
    se=v.std(ddof=1)/np.sqrt(len(v)) if len(v)>1 else np.nan
    equal(row[key],mean,key)
    equal(row[key+'_mcse'],se,key+'_mcse')
    equal(row[key+'_n'],len(v),key+'_n')
    for suffix,sign in [('lo',-1),('hi',1)]:equal(row[key+'_'+suffix],mean+sign*1.96*se,key+suffix)

diagnostics=pd.read_csv(folder/'diagnostics_by_graph.csv')
coupling=pd.read_csv(folder/'support_coupling_by_graph.csv')
manifest=json.loads((folder/'diagnostics_manifest.json').read_text())
assert manifest['status']=='complete' and manifest['cells']==102
raw_rows=0
for item in manifest['inputs']:
    f=pd.read_parquet(root/item['path']);raw_rows+=len(f)
    q=diagnostics[(diagnostics.graph==f.graph.iloc[0])&(diagnostics.design==f.design.iloc[0])&
                  (diagnostics.p==f.p.iloc[0])&(diagnostics.rho==f.rho.iloc[0])]
    assert len(q)==72
    for (mechanism,model),g in f.groupby(['mechanism','model']):
        row=q[(q.mechanism==mechanism)&(q.model==model)].iloc[0]
        # Identity holds for every returned linear smoother, including finite
        # minimum-norm outputs whose policy contrast is nonestimable.
        if model not in ['ht','hajek']:
            assert np.allclose(g.conditional_mse,g.conditional_bias**2+g.oracle_variance,equal_nan=True)
        for name,values in [('assignment_bias_squared',g.conditional_bias**2),
                            ('oracle_variance',g.oracle_variance),
                            ('conditional_bias',g.conditional_bias),
                            ('mse_identity_residual',g.error**2-g.conditional_mse),
                            ('bias_identity_residual',g.error-g.conditional_bias),
                            ('weight_norm2',g.weight_norm2),
                            ('exposure_sd',g.exposure_sd),
                            ('prediction_mean_mse',g.prediction_mean_mse)]:moments(row,name,values)
        error=g.error.to_numpy(float);error=error[np.isfinite(error)]
        equal(row.error_sd,error.std(ddof=1) if len(error)>1 else np.nan,'error_sd')
    selected=coupling[(coupling.graph==f.graph.iloc[0])&(coupling.design==f.design.iloc[0])&
                     (coupling.p==f.p.iloc[0])&(coupling.rho==f.rho.iloc[0])]
    assert len(selected)==9
    for row in selected.itertuples():
        first=f[(f.mechanism=='linear')&(f.model==row.model)].set_index('pairing_id')
        second=f[(f.mechanism=='hidden_tail')&(f.model==row.model)].set_index('pairing_id').loc[first.index]
        event=first.tail_active.eq(0);finite=np.isfinite(first.estimate)&np.isfinite(second.estimate)
        equal(row.identical_data_fraction,event.mean(),'coupling event')
        equal(row.defined_pair_fraction,finite.mean(),'coupling finite')
        equal(row.finite_identical_data_replicates,(event&finite).sum(),'coupling denominator')
        if (event&finite).any():assert np.allclose(first.loc[event&finite,'estimate'],second.loc[event&finite,'estimate'],atol=1e-8,rtol=0)
        equal(row.empirical_two_risk_bound,event.mean()/4,'coupling bound')
        for label,g in [('linear',first),('tail',second)]:moments(row._asdict(),label+'_squared_error',g.loc[finite,'error']**2)

performance=pd.read_csv(root/'results/summary/performance_by_graph.csv')
contrasts=pd.read_csv(folder/'independent_contrasts_by_graph.csv')
for row in contrasts.itertuples():
    s=performance[(performance.graph==row.graph)&(performance.p==row.p)&
                  (performance.mechanism==row.mechanism)&(performance.model==row.model)]
    if row.contrast=='cluster_minus_node':
        s=s[s.rho==row.rho];x=s[s.design=='cluster'];y=s[s.design=='bernoulli']
    else:
        s=s[s.design==row.design];x=s[s.rho==1];y=s[s.rho==0]
    assert len(x)==len(y)==1
    x=x.iloc[0];y=y.iloc[0]
    for key,se_name in [('bias','bias_mcse'),('mse','mse_mcse'),('rmse','rmse_mcse'),
                        ('prediction_mse_mean','prediction_mse_mcse'),
                        ('prediction_mean_mse_mean','prediction_mean_mse_mcse'),
                        ('oracle_variance_mean','oracle_variance_mcse')]:
        value=x[key]-y[key];se=np.hypot(x[se_name],y[se_name])
        equal(getattr(row,'delta_'+key),value,key)
        equal(getattr(row,'delta_'+key+'_mcse'),se,key+'mcse')
        equal(getattr(row,'delta_'+key+'_lo'),value-1.96*se,key+'lo')
        equal(getattr(row,'delta_'+key+'_hi'),value+1.96*se,key+'hi')

# Verify each supplementary family metric directly against its graph summaries.
for name in ['diagnostics','prediction_gate_pairs','support_coupling','independent_contrasts']:
    g=pd.read_csv(folder/(name+'_by_graph.csv'));families=pd.read_csv(folder/(name+'_by_family.csv'))
    key_columns=[c for c in families if c in g and c not in ['graphs']]
    metrics=[c.removesuffix('_graph_mean') for c in families if c.endswith('_graph_mean')]
    for row in families.to_dict('records'):
        mask=np.ones(len(g),bool)
        for key in key_columns:mask &= g[key].isna() if pd.isna(row[key]) else g[key].eq(row[key])
        selected=g[mask];assert len(selected)==row['graphs']
        for key in metrics:
            v=selected[key].dropna().to_numpy(float);n=len(v)
            mean=v.mean() if n else np.nan;se=v.std(ddof=1)/np.sqrt(n) if n>1 else np.nan
            crit=t.ppf(.975,n-1) if n>1 else np.nan
            for suffix,value in [('mean',mean),('se',se),('lo',mean-crit*se),('hi',mean+crit*se)]:equal(row[key+'_graph_'+suffix],value,key+suffix)
            equal(row[key+'_graphs_defined'],n,key+'graphs')

claims=pd.read_csv(folder/'claim_evidence.csv');tables={}
for row in claims.itertuples():
    if row.table not in tables:
        file=root/row.table;assert hashlib.sha256(file.read_bytes()).hexdigest()==row.table_sha256
        tables[row.table]=pd.read_csv(file)
    selected=tables[row.table]
    for key,value in json.loads(row.selector).items():selected=selected[selected[key].isna()] if value is None else selected[selected[key]==value]
    assert len(selected)==1
    source=selected.iloc[0]
    equal(row.value,float(source[row.metric])*row.scale,'claim value')
    if row.metric.endswith('_graph_mean'):
        base=row.metric.removesuffix('_graph_mean')
        equal(row.lo,source[base+'_graph_lo']*row.scale,'claim lo')
        equal(row.hi,source[base+'_graph_hi']*row.scale,'claim hi')
        equal(row.denominator,source.get(base+'_graphs_defined',source['graphs']),'claim graph count')
    elif 'Monte Carlo' in row.uncertainty:
        equal(row.lo,source.get(row.metric+'_lo',np.nan)*row.scale,'claim lo')
        equal(row.hi,source.get(row.metric+'_hi',np.nan)*row.scale,'claim hi')
        equal(row.denominator,source.get(row.metric+'_denominator',source.get('defined_replicates',400)),'claim replicate count')
    elif 'measured mean interval width' in row.uncertainty:
        equal(row.denominator,source['defined_replicates'],'width denominator')
        assert np.isnan(row.lo) and np.isnan(row.hi)
    else:
        assert row.denominator==0 and np.isnan(row.lo) and np.isnan(row.hi)
report=dict(status='passed',raw_rows=raw_rows,raw_cells=102,numerical_comparisons=checks,
            independent_contrasts=len(contrasts),claim_routes=len(claims),
            script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            tables={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.glob('*.csv')},
            scope='Internal independent arithmetic on raw conditional decomposition, support coupling, all supplementary family moments, independent-stream contrasts and claim selectors; not independent research review.')
(notes/'diagnostics_audit.json').write_text(json.dumps(report,indent=2))
print(f'HUTIAN_WAKE: supplementary arithmetic audit passed checks={checks}',flush=True)
