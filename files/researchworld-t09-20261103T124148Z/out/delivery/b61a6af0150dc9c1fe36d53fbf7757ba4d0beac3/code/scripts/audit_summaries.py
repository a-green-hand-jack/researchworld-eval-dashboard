"""Audit final numerical tables against raw checkpoints and configured counts.

Uses direct array moments rather than calling the table-generating functions.
This is an internal arithmetic/provenance audit, not an independent statistical
implementation or a replacement for independent review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t


def close(actual, expected, label):
    if not np.isclose(actual, expected, rtol=2e-9, atol=2e-11, equal_nan=True):
        raise AssertionError((label, actual, expected))


def direct_moments(values):
    a=np.asarray(values,dtype=float);a=a[np.isfinite(a)]
    return (float(a.mean()) if len(a) else np.nan,
            float(np.std(a,ddof=1)/np.sqrt(len(a))) if len(a)>1 else np.nan)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.')
    p.add_argument('--core-only',action='store_true',help='Audit the complete core panel before stress panels finish')
    a=p.parse_args();root=Path(a.root).resolve()
    code=root/'code' if (root/'code/configs').exists() else root
    notes=root/'analysis' if code!=root else root/'notes'
    summary=root/('results/core_summary' if a.core_only else 'results/summary');diagnostics=root/'results/diagnostics'
    cells=72 if a.core_only else 102
    family_rows=1152 if a.core_only else 2160
    manifest=json.loads((summary/'summary_manifest.json').read_text())
    assert manifest['cells']==cells and manifest['rows']==cells*28800
    source_hash=hashlib.sha256((code/'src/gatebench/summarize.py').read_bytes()).hexdigest()
    assert manifest['summary_source_sha256']==source_hash
    performance=pd.read_csv(summary/'performance_by_graph.csv')
    paired=pd.read_csv(summary/'paired_by_graph.csv')
    assert len(performance)==cells*72 and len(paired)==cells*120
    scalar_checks=0;pair_checks=0;undefined_groups=0
    for item in manifest['inputs']:
        file=root/item['path']
        assert hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256']
        frame=pd.read_parquet(file)
        graph=frame.graph.iloc[0]
        cell=performance[(performance.graph==graph)&(performance.design==frame.design.iloc[0])&
                         (performance.p==frame.p.iloc[0])&(performance.rho==frame.rho.iloc[0])&
                         (performance.gamma==frame.gamma.iloc[0])]
        assert len(cell)==72
        for (mechanism,model),g in frame.groupby(['mechanism','model']):
            q=cell[(cell.mechanism==mechanism)&(cell.model==model)]
            assert len(q)==1;q=q.iloc[0]
            error=g.error.to_numpy(float);finite=np.isfinite(error)
            supported=finite&g.valid.to_numpy(bool)
            assert q.replicates==400 and q.defined_replicates==finite.sum()
            assert q.undefined_count==(~finite).sum()
            assert q.unsupported_defined_count==(finite&~supported).sum()
            assert q.estimable_replicates==supported.sum()
            close(q.defined_fraction,finite.mean(),'defined fraction')
            close(q.valid_fraction,g.valid.mean(),'valid fraction')
            for prefix,selected in [('',error[finite]),('estimable_',error[supported])]:
                bias,bias_se=direct_moments(selected)
                mse,mse_se=direct_moments(selected**2)
                for key,value in [('bias',bias),('bias_mcse',bias_se),('mse',mse),('mse_mcse',mse_se),('rmse',np.sqrt(mse))]:
                    close(q[prefix+key],value,(graph,mechanism,model,prefix+key));scalar_checks+=1
            if not finite.any():
                assert np.isnan(q.rmse_lo) and np.isnan(q.rmse_hi);undefined_groups+=1
            for metric in ['cover_hc3','cover_oracle']:
                selected=g[metric].dropna().to_numpy(float)
                assert q[metric+'_denominator']==len(selected)
                close(q[metric],selected.mean() if len(selected) else np.nan,metric)
                selected=g.loc[supported,metric].dropna().to_numpy(float)
                assert q['estimable_'+metric+'_denominator']==len(selected)
                close(q['estimable_'+metric],selected.mean() if len(selected) else np.nan,'estimable '+metric)
        pairs=paired[(paired.graph==graph)&(paired.design==frame.design.iloc[0])&
                     (paired.p==frame.p.iloc[0])&(paired.rho==frame.rho.iloc[0])&
                     (paired.gamma==frame.gamma.iloc[0])]
        assert len(pairs)==120
        for _,q in pairs.iterrows():
            subset=frame[frame.mechanism==q.mechanism]
            fa=subset[subset.model==q.model].set_index('pairing_id')
            fb=subset[subset.model==q.reference].set_index('pairing_id')
            fa,fb=fa.align(fb,axis=0,join='inner')
            finite=np.isfinite(fa.error)&np.isfinite(fb.error)
            assert q.total_pairs==400 and q.pairs==finite.sum()
            assert q.valid_pairs==(finite&fa.valid&fb.valid).sum()
            for name,values in [('delta_mse',fa.loc[finite,'error']**2-fb.loc[finite,'error']**2),
                                ('delta_prediction_mse',fa.loc[finite,'prediction_mse']-fb.loc[finite,'prediction_mse'])]:
                value,se=direct_moments(values)
                close(q[name],value,name);close(q[name+'_mcse'],se,name+' mcse');pair_checks+=2
    # Configured family counts ensure no float-truth split or silent omission.
    family=pd.read_csv(summary/'performance_by_family.csv')
    pair_family=pd.read_csv(summary/'paired_by_family.csv')
    assert len(family)==family_rows and len(pair_family)==family_rows//72*120
    for frame in [family,pair_family]:
        public=frame.graph_kind=='facebook'
        single=public|(frame.p!=.5)
        assert (frame.loc[single,'graphs']==1).all()
        assert (frame.loc[~single,'graphs']==5).all()
        if 'rmse_graph_lo' in frame:
            assert frame.loc[single,'rmse_graph_lo'].isna().all()
    keys=['graph_kind','n','degree_target','cluster_size','mixing','design','p','rho','gamma','mechanism','model']
    # Independently recalculate equal-graph means, t intervals and pooled RMSE.
    for key,g in performance.groupby(keys,dropna=False):
        match=np.ones(len(family),dtype=bool)
        for name,value in zip(keys,key):
            match &= family[name].isna().to_numpy() if pd.isna(value) else (family[name]==value).to_numpy()
        q=family.loc[match]
        assert len(q)==1;q=q.iloc[0]
        assert q.graphs==len(g)
        for metric in ['bias','mse','rmse','defined_fraction','valid_fraction','cover_hc3','cover_oracle']:
            value,se=direct_moments(g[metric]);count=int(np.isfinite(g[metric]).sum())
            critical=t.ppf(.975,count-1) if count>1 else np.nan
            close(q[metric+'_graph_mean'],value,metric+' family mean')
            close(q[metric+'_graph_se'],se,metric+' family SE')
            close(q[metric+'_graph_lo'],value-critical*se,metric+' family low')
            close(q[metric+'_graph_hi'],value+critical*se,metric+' family high')
        close(q.pooled_rmse,np.sqrt(g.mse.mean()),'pooled family RMSE')
    expected={}
    if not a.core_only:
        extra=json.loads((diagnostics/'diagnostics_manifest.json').read_text())
        assert extra['status']=='complete' and extra['cells']==102 and extra['rows']==2937600
        assert extra['script_sha256']==hashlib.sha256((code/'scripts/analyze_results.py').read_bytes()).hexdigest()
        assert {x['sha256'] for x in extra['inputs']}=={x['sha256'] for x in manifest['inputs']}
        expected={'diagnostics_by_graph':7344,'prediction_gate_pairs_by_graph':4896,
                  'support_coupling_by_graph':918,'exact_ht_risk':306,
                  'independent_contrasts_by_graph':5256,'graph_inventory':36,
                  'diagnostics_by_family':2160,'prediction_gate_pairs_by_family':1440,
                  'support_coupling_by_family':270,'independent_contrasts_by_family':1512}
        for name,count in expected.items():
            actual=len(pd.read_csv(diagnostics/(name+'.csv')))
            assert actual==count,(name,actual,count)
        risk=pd.read_csv(diagnostics/'exact_ht_risk.csv')
        assert not risk.duplicated(['panel','cell_id','endpoint_family']).any()
        assert risk.groupby(['panel','cell_id']).size().eq(3).all()
        assert np.isfinite(risk.ht_exact_log10_variance).all()
        assert np.allclose(risk.ht_exact_log10_rmse,risk.ht_exact_log10_variance/2)
        assert len(extra['exact_ht_inputs'])==102
        for item in extra['exact_ht_inputs']:
            assert hashlib.sha256((root/item['path']).read_bytes()).hexdigest()==item['sha256']
    report=dict(status='passed',scope='core' if a.core_only else 'complete',raw_cells=cells,raw_rows=cells*28800,
                scalar_moment_checks=scalar_checks,paired_moment_checks=pair_checks,
                all_undefined_groups=undefined_groups,graph_groups=len(performance),
                family_groups=len(family),supplementary_counts=expected,
                summary_source_sha256=source_hash,
                audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (notes/('core_summary_audit.json' if a.core_only else 'summary_audit.json')).write_text(json.dumps(report,indent=2))
    print('HUTIAN_WAKE: final raw-to-summary audit passed',flush=True)


if __name__=='__main__':
    main()
