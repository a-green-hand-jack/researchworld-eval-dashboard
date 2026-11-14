#!/usr/bin/env python3
"""Descriptive derived summaries of completed trials; no new fitted procedures.

The predeclared trial unit and interval policies are inherited from summarize.py.
Cross-cell area contrasts are descriptive and do not receive a ranking decision:
the frozen numerical allowance was defined for method pairs within a cell.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd

ANALYSIS=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('study_intervals',ANALYSIS/'scripts/summarize.py')
intervals=importlib.util.module_from_spec(spec);spec.loader.exec_module(intervals)
interval=intervals.interval

SENSITIVITIES={
    'interior_ncal99':'interior_k3','interior_ncal1999':'interior_k3',
    'interior_alpha05':'interior_k3','heterogeneous_ncal99':'heterogeneous_k3',
    'heterogeneous_ncal1999':'heterogeneous_k3','heterogeneous_alpha05':'heterogeneous_k3',
    'heterogeneous_shift':'heterogeneous_k3',
    'zeros_eps1e-06':'zeros_k3','zeros_eps0.01':'zeros_k3'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--summary',required=True)
    p.add_argument('--config',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    df=pd.read_json(a.input,lines=True)
    required={'input_hashes','location_coefficients','repeat','seed','method','group','status'}
    if not required.issubset(df.columns):raise ValueError(f'Missing immutable-trial provenance: {sorted(required-set(df.columns))}; exploratory pilot is ineligible')
    ok=df[df.status=='ok'].copy();summary=pd.read_csv(Path(a.summary)/'summary.csv')
    cfg=json.load(open(a.config));cells={c['id']:c for c in cfg['cells']}
    # A coverage interval describes resampling the full procedure; it is not a
    # guarantee conditional on one calibration sample or a test of the theorem.
    coverage=summary[summary.metric=='coverage'].copy()
    coverage['nominal']=coverage.cell.map(lambda c:1-cells[c]['alpha'])
    for col in ['mean','ci_low','ci_high','bootstrap_ci_low','bootstrap_ci_high']:
        coverage['gap_'+col]=coverage[col]-coverage.nominal
    coverage['ci_halfwidth']=(coverage.ci_high-coverage.ci_low)/2
    coverage['minority_imprecise_for_fine_ranking']=(coverage.group=='minority')&(coverage.ci_halfwidth>.02)
    coverage['interval_intersects_nominal']=(coverage.gap_ci_low<=0)&(coverage.gap_ci_high>=0)
    coverage.to_csv(out/'coverage_gaps_and_precision.csv',index=False)
    components=[]
    for (cell,method,group),g in ok[ok.method.str.startswith('coordinate')].groupby(['id','method','group']):
        for j in range(cells[cell]['k']):
            vals=g.component_coverage.map(lambda s:json.loads(s)[j] if isinstance(s,str) and s else np.nan)-g.coverage
            if vals.notna().any():components.append(dict(cell=cell,method=method,group=group,component=j,
                metric='component_minus_joint_coverage',**interval(vals)))
    pd.DataFrame(components).to_csv(out/'coordinate_component_joint_gaps.csv',index=False)
    denominators=[]
    for (cell,group),g in ok[ok.method=='tv'].groupby(['id','group']):
        for metric in ['n','cal_n_majority','cal_n_minority','test_zero_rate','fit_scale_majority','fit_scale_minority','n_volume_centers']:
            values=g[metric].dropna()
            if len(values):denominators.append(dict(cell=cell,group=group,metric=metric,minimum=float(values.min()),maximum=float(values.max()),**interval(values)))
    pd.DataFrame(denominators).to_csv(out/'group_denominators_and_fits.csv',index=False)
    worst=[]
    for (cell,method),g in ok[ok.group.isin(['majority','minority'])].groupby(['id','method']):
        wide=g.pivot(index='repeat',columns='group',values='coverage')
        values=wide.min(axis=1,skipna=False)
        worst.append(dict(cell=cell,method=method,metric='minimum_of_two_empirical_group_coverages',**interval(values)))
    pd.DataFrame(worst).to_csv(out/'fixed_group_minimum_coverage.csv',index=False)
    sensitivity=[]
    for cell,base in SENSITIVITIES.items():
        if cell not in set(ok.id) or base not in set(ok.id):continue
        aa=ok[ok.id==cell];bb=ok[ok.id==base]
        joined=aa.merge(bb,on=['repeat','method','group'],suffixes=('_arm','_base'),validate='one_to_one')
        assert (joined.seed_arm==joined.seed_base).all()
        same_test=True
        for ar,br in zip(joined.input_hashes_arm,joined.input_hashes_base):
            ar,br=json.loads(ar),json.loads(br)
            assert ar['train']==br['train']
            if ar['test']!=br['test']:same_test=False
        if cell!='heterogeneous_shift':assert same_test
        for (method,group),g in joined.groupby(['method','group']):
            for metric in ['coverage','mean_volume','infinite_threshold_rate']:
                diff=g[metric+'_arm']-g[metric+'_base']
                if diff.notna().any():
                    result=dict(cell=cell,reference_cell=base,method=method,group=group,metric=metric,
                        same_test_arrays=same_test,direction='arm minus reference',area_ranking_allowed=False,**interval(diff))
                    if metric=='coverage':
                        # Nominal-level arm changes the target as well as its
                        # realized coverage. Preserve both quantities.
                        result['nominal_difference']=cells[base]['alpha']-cells[cell]['alpha']
                        result['coverage_gap_difference']=result['mean']-result['nominal_difference']
                    sensitivity.append(result)
    pd.DataFrame(sensitivity).to_csv(out/'paired_sensitivity_contrasts.csv',index=False)
    # Summarize interval sensitivity directly; no repeated test-point bootstrap.
    checks=[]
    for metric,g in summary.groupby('metric'):
        checks.append({'metric':metric,'rows':len(g),'max_endpoint_difference':float(max((g.ci_low-g.bootstrap_ci_low).abs().max(),(g.ci_high-g.bootstrap_ci_high).abs().max())),
                       'trial_unit':'independently regenerated/refitted trial'})
    pd.DataFrame(checks).to_csv(out/'bootstrap_interval_sensitivity.csv',index=False)
    paths=[Path(a.input),Path(a.summary)/'summary.csv',Path(a.config),Path(__file__),ANALYSIS/'scripts/summarize.py']
    meta={'inputs_and_code_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
          'interpretation':'Derived descriptive summaries; t95 and bootstrap5000 seed90210 over independent trials; paired cross-cell common-random-number differences. No cross-cell area ranking without its own audit.',
          'sensitivity_cells':list(SENSITIVITIES),'new_scientific_runs':0,
          'multiplicity':'Exploratory descriptive intervals, not simultaneous familywise inference or selection by p value'}
    (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(f'Derived coverage, coordinate, group, sensitivity and interval diagnostics from {df.id.nunique()} cells')

if __name__=='__main__':main()
