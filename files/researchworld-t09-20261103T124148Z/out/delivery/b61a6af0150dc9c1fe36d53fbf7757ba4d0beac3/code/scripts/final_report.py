"""Generate the final evidence handoff from audited stored numerical tables.

Produces analysis notes and a machine-readable claim/row/metric registry, not
manuscript prose or presentation assets. Does not rerun models or select a grid.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

root=Path(__file__).resolve().parents[1]
if root.name=='code': root=root.parent
notes=root/('analysis' if (root/'code').exists() else 'notes')
assert json.loads((notes/'summary_audit.json').read_text())['status']=='passed'
production_audit=json.loads((notes/'production_audit.json').read_text())
maximum_matched_bias=max(x['max_matched_bias'] for x in production_audit['stages'].values())
assert json.loads((notes/'boundary_audit.json').read_text())['status']=='passed'
assert json.loads((notes/'reproduction_audit.json').read_text())['status']=='passed'
paths={
    'f':'results/summary/performance_by_family.csv',
    'g':'results/summary/performance_by_graph.csv',
    'p':'results/summary/paired_by_family.csv',
    'd':'results/diagnostics/diagnostics_by_family.csv',
    'c':'results/diagnostics/support_coupling_by_family.csv',
    'i':'results/diagnostics/independent_contrasts_by_family.csv',
    'r':'results/diagnostics/exact_ht_risk.csv',
}
tables={k:pd.read_csv(root/v) for k,v in paths.items()}
hashes={k:hashlib.sha256((root/v).read_bytes()).hexdigest() for k,v in paths.items()}
registry=[]

def select(table, **selector):
    data=tables[table]
    for key,value in selector.items():
        data=data[data[key].isna()] if value is None else data[data[key]==value]
    assert len(data)==1,(table,selector,len(data))
    return data.iloc[0]


def value(claim,table,selector,metric,scope='graph',scale=1.):
    row=select(table,**selector)
    if scope=='family':
        key=metric+'_graph_mean';lo=metric+'_graph_lo';hi=metric+'_graph_hi'
        denominator=int(row.get(metric+'_graphs_defined',row.get('graphs_defined',row.graphs)))
        uncertainty='95% t interval across independent graph draws; n=1 has no population interval'
    elif scope=='graph':
        key=metric;lo=metric+'_lo';hi=metric+'_hi'
        denominator=int(row.get(metric+'_denominator',row.get('defined_replicates',400)))
        uncertainty='95% conditional Monte Carlo interval (Wilson for coverage)'
    else:
        key=metric;lo=hi='__absent__';denominator=0
        uncertainty='analytic evaluation; no sampling interval'
    point=float(row[key])*scale;low=float(row.get(lo,np.nan))*scale;high=float(row.get(hi,np.nan))*scale
    registry.append(dict(claim=claim,table=paths[table],table_sha256=hashes[table],
                         selector=json.dumps(selector,sort_keys=True),metric=key,scale=scale,
                         value=point,lo=low,hi=high,denominator=denominator,uncertainty=uncertainty))
    return f'{point:.5g} [{low:.5g}, {high:.5g}]' if np.isfinite(low) else f'{point:.5g}'


def regular(n=2000,degree=20,design='bernoulli',mechanism='linear',model='linear',rho=0,p=.5):
    return dict(graph_kind='regular',n=n,degree_target=degree,design=design,p=p,rho=rho,mechanism=mechanism,model=model)


def family(claim,selector,metric,table='f',scale=1):
    return value(claim,table,selector,metric,'family',scale)

lines=['# Final completed-study evidence and claim map','',
'Scope: all 102 planned cells, R400, 2,937,600 estimator-output rows; 36 fixed graph instances, including five independent draws for each of seven synthetic regimes and one full SNAP graph. Core/noise/imbalance have 72/22/8 cells. All statements below are measured outputs or explicitly analytic calculations. All conditions, including unfavorable and undefined results, remain in complete tables. The examples explain H1–H4; they are not multiplicity-adjusted discovery tests or universal estimator rankings.','',
'These are corrected count-before-division outputs. The original v1 execution is superseded as documented in exposure_boundary_correction.md; all empirical/exact-risk inputs, integer support checks and selected replay have been regenerated. The full graph/config metadata comparison is v2_dependency_audit.json.','',
'Numeric brackets below are approximate 95% uncertainty intervals. Synthetic family values average graph summaries equally and use t4 intervals over five independent graph draws. They include finite Monte Carlo variation; they are not isolated pure graph-generation variance estimates. SNAP and the one-seed imbalance slice use conditional-on-graph Monte Carlo intervals (normal/delta moments or Wilson coverage), not graph-population intervals. Full definitions and finite/estimable denominators are in methods.md.','',
'Every value selected by this script is registered with its exact source CSV SHA256, row selector, metric, scale, denominator and uncertainty in results/diagnostics/claim_evidence.csv. Operational risk retains finite minimum-norm fits even if their endpoint is nonestimable; partially defined methods have conditional-defined risk plus a failure rate. Oracle covariance/mean quantities are simulation-only diagnostics.','',
'## H1: degree, size and the conditional bias/variance diagnostic','',
'Linear DGP, matched linear model, node assignment, p=.5/rho0; all endpoint contrasts are estimable:','',
'|n|degree|Mean graph RMSE [graph CI]|Mean oracle variance [graph CI]|','|--:|--:|--:|--:|']
for n,d in [(2000,4),(2000,20),(2000,80),(8000,20)]:
    s=regular(n,d)
    lines.append(f"|{n}|{d}|{family('H1-degree-size',s,'rmse')}|{family('H1-degree-size',s,'oracle_variance_mean')}|")
lines += ['', f'At fixed n, error grows with degree; at fixed degree it decreases with n in these regular-graph slices. Matched-model conditional mean bias is at numerical roundoff when the contrast is estimable (full audit maximum absolute bias {maximum_matched_bias:.5g}). This does not make variance a sufficient diagnostic for a misspecified mean, or infer general rates across all graph laws. E[b(z)^2], rather than E[b(z)]^2, belongs in the MSE decomposition. Exact b²+v is checked by executable small-graph identities and retained in every regression output; simulation residual means have MCSE, not an asserted finite-sample exact zero.','',
'## H2: prediction is not global endpoint validation','']
s=regular(design='cluster',mechanism='cubic',model='cubic');s['reference']='linear'
lines.append('Regular n2000/d20, cubic DGP, cluster assignment: cubic-minus-linear GATE MSE '+family('H2-prediction-reversal',s,'delta_mse','p')+'; fresh-assignment noisy-outcome prediction MSE '+family('H2-prediction-reversal',s,'delta_prediction_mse','p')+'. Both fits are fully defined and estimable. Within-cell differences preserve shared assignments/noise. The better interior prediction model has worse GATE here.')
lines += ['', 'Linear regression on the quadratic DGP, regular n2000/d20/node/p=.5: signed bias '+family('H2-complement-cancellation',regular(mechanism='quadratic'),'bias')+'. This is consistent with the analytic complement cancellation of signed bias at .5, not proof of small assignment-conditional bias or general robustness. The focused independent imbalance panel breaks that symmetry:','',
'|fixed graph|design|p|Signed bias [conditional MC CI]|','|--|--|--:|--:|']
for kind in ['regular','facebook']:
    for design in ['bernoulli','cluster']:
        for probability in [.2,.8]:
            s=dict(graph_kind=kind,design=design,p=probability,rho=0,mechanism='quadratic',model='linear')
            lines.append(f"|{kind}|{design}|{probability}|{value('H2-imbalance','g',s,'bias')}|")
lines += ['', 'The regular imbalance graph is n2000/d20, seed201 only; SNAP is its one fixed topology. Signs reverse under both designs on these two graphs. These are not five-graph imbalance population results.','',
'## H2: hidden-tail nonidentification control','']
for degree in [20,80]:
    s=regular(degree=degree);s.pop('mechanism');s['panel']='core'
    lines.append(f"Regular n2000/d{degree}, node assignment: observed identical-data event probability "+family('H2-hidden-tail',s,'identical_data_fraction','c')+'; coupled linear-DGP MSE '+family('H2-hidden-tail',s,'linear_squared_error','c')+' and hidden-tail MSE '+family('H2-hidden-tail',s,'tail_squared_error','c')+'. The target gap is one; the estimator returns the same value on identical data.')
bounds=json.loads((root/'results/support_bounds.json').read_text())
for degree in [20,80]:
    b=next(x for x in bounds if x['n']==2000 and x['degree']==degree and x['p']==.5)
    lines.append(f"Analytic regular d{degree} union bound: P(identical data)>={b['event_identical_data_probability_lower']:.10g}, so the maximum of the two unconditional MSEs is at least {b['max_two_model_mse_lower_bound']:.10g}. This is computed by gatebench.support_bounds, not estimated from the R400 events.")
lines += ['', 'An empirical event fraction of1 with a degenerate between-graph interval[1,1]means every saved assignment met the event on each of five graphs; it does not establish probability one. Per-graph Wilson Monte Carlo bounds remain in support_coupling_by_graph.csv. The separate analytic bound, rather than the zero-width empirical t interval, controls the unobserved rare tail. The same caution applies to all-success/all-failure defined or estimable fractions.', '', 'The analytic statement concerns a shared, fully defined estimation rule. It cannot be applied to the conditional-success risk of a partially defined Hajek estimator. The same sparse-interior observations can have distinct endpoint truths; no choice among the implemented smoothers certifies robustness to this tail without additional response assumptions.','',
'## H3: design can help support without guaranteeing lower risk','']
for degree in [4,20,80]:
    s=regular(degree=degree);s.pop('design');s.pop('rho');s.update(panel='core',rho=0.,contrast='cluster_minus_node')
    lines.append(f"Regular d{degree}, matched linear DGP/model: cluster-minus-node RMSE "+family('H3-design',s,'delta_rmse','i')+'. This is an independent-stream contrast, then averaged over matched graphs; it is not replicate-paired.')
for design in ['bernoulli','cluster']:
    s=regular(degree=80,design=design,mechanism='threshold',model='threshold_oracle')
    lines.append(f"Dense threshold oracle, {design}: operational RMSE "+family('H3-support',s,'rmse')+'; estimable fraction '+family('H3-support',s,'valid_fraction')+'.')
for design in ['bernoulli','cluster']:
    s=regular(degree=80,design=design,model='spline')
    lines.append(f"Dense linear DGP/fixed spline, {design}: operational RMSE "+family('H3-adverse-flexibility',s,'rmse')+'; estimable fraction '+family('H3-adverse-flexibility',s,'valid_fraction')+'.')
lines += ['', 'Cluster assignment improves matched low-dimensional regression here, but fixed-spline risk can become much larger while estimability improves. The dense threshold example also fails often despite being given the correct response feature. Unsupported finite fits remain operational errors, never successful endpoint recovery. Untruncated graph t intervals may extend below zero for nonnegative metrics or outside[0,1]for fractions; these limits signal approximation/imprecision, not invalid parameter values. Fixed BFS partitions, their cluster counts/retained edges and exposure summaries are reported; this is not a cluster-optimization study. ER/SBM/BA contrasts change several structural properties and are descriptive, not isolated causal topology effects.','',
'## H4: correct mapping can trade bias for variance','',
'|n|degree|twohop-minus-linear GATE MSE [graph CI], twohop DGP/node|','|--:|--:|--:|']
for n,d in [(2000,4),(2000,20),(8000,20)]:
    s=regular(n,d,mechanism='twohop',model='twohop');s['reference']='linear'
    lines.append(f"|{n}|{d}|{family('H4-mapping',s,'delta_mse','p')}|")
lines += ['', 'The correctly mapped fit removes conditional mean bias when estimable, but its larger endpoint variance can dominate at n2000/d20. The adverse case and the reversal at n8000 are both retained; there is no universal correct-map risk lower bound. The twohop mechanism includes random-walk return paths, not solely distinct-distance-two neighbors.','',
'## H4: local covariance, uncertainty and conditional public-graph evidence','']
for kind in ['regular','sbm']:
    for design in ['bernoulli','cluster']:
        s=dict(graph_kind=kind,n=2000,degree_target=20,design=design,p=.5,rho=1.,mechanism='linear',model='linear')
        lines.append(f"rho1 {kind}/{design}, matched linear fit: RMSE "+family('H4-noise',s,'rmse')+'; HC3 coverage '+family('H4-coverage',s,'cover_hc3')+'; oracle coverage '+family('H4-coverage',s,'cover_oracle')+'.')
        c=s.copy();c.pop('rho');c['contrast']='rho1_minus_rho0'
        lines.append('Independent rho1-minus-rho0 RMSE '+family('H4-noise-contrast',c,'delta_rmse','i')+'.')
lines += ['', '|SNAP design/rho|RMSE [MC CI]|HC3 coverage [Wilson CI]|oracle coverage [Wilson CI]|Mean HC3 interval width|Mean oracle interval width|','|--|--:|--:|--:|--:|--:|']
for design in ['bernoulli','cluster']:
    for rho in [0.,1.]:
        s=dict(graph_kind='facebook',design=design,p=.5,rho=rho,mechanism='linear',model='linear')
        vals=[value('H4-fixed-SNAP','g',s,k) for k in ['rmse','cover_hc3','cover_oracle']]
        widths=[value('H4-interval-width','g',s,k,'analytic',3.92) for k in ['hc3_se_mean','oracle_se_mean']]
        # Widths are measured means transformed by 2*1.96, not analytic risks.
        for record in registry[-2:]:
            record['uncertainty']='measured mean interval width = 3.92 * stored mean SE; no interval supplied'
            record['denominator']=400
        lines.append(f"|{design}/{rho:g}|"+'|'.join(vals+widths)+'|')
lines += ['', 'All displayed matched-model coverage denominators are 400 per graph. The local row-normalized rho1 law has unit marginal variances and this particular network covariance. HC3 is working independence; the oracle uses the true covariance and conditional unbiasedness. Near-nominal oracle coverage does not provide a feasible network inference method or protect a misspecified mean. Positive rho does not establish the sign/magnitude of variance change for every possible contrast or noise law. All public-graph uncertainty is conditional on one historical topology, its fixed x and partition.','',
'## Baselines and negative controls','']
for mechanism in ['no_interference','linear']:
    for model in ['naive','linear','ht','hajek']:
        s=regular(degree=4,mechanism=mechanism,model=model)
        lines.append(f"Sparse regular/node/{mechanism}/{model}: mean graph RMSE "+family('baseline-control',s,'rmse')+'; defined fraction '+family('baseline-control',s,'defined_fraction')+'.')
lines += ['', 'Without interference, unnecessary exposure adjustment costs precision relative to DIM in this sparse control. With linear interference, DIM has substantial missing-spillover bias and matched regression improves accuracy. These examples do not assert that regression dominates all baselines under arbitrary outcome laws.','']
s=regular(degree=20,model='hajek')
lines.append('Regular n2000/d20/node/linear DGP Hajek defined fraction '+family('baseline-failure',s,'defined_fraction')+'. Its conditional-defined RMSE is missing when no return exists. Undefined estimates are not zero error. Full-exposure HT remains mathematically unbiased only for its one-hop mapping; in the twohop DGP it is a misspecified comparator.')
for design in ['bernoulli','cluster']:
    s=dict(panel='core',graph='snap_facebook',design=design,p=.5,rho=0.,endpoint_family='linear')
    lines.append(f"SNAP/rho0/{design} one-hop HT exact log10(RMSE) "+value('H4-rare-HT','r',s,'ht_exact_log10_rmse','analytic')+'. The R400 empirical risk and normal intervals can miss astronomically rare contributions. All306 exact endpoint-family rows remain in exact_ht_risk.csv; endpoint families reuse identical one-hop means/covariance, not the twohop identification.')
lines += ['', 'The exact risks are fixed-graph, fixed-covariate, known-DGP calculations, not population guarantees. No practical interval is implemented for HT/Hajek; nonempty-arm DIM has stored HC3/oracle intervals from its own-treatment regression.','',
'## Complete failure ledger and reproducibility scope','']
g=tables['g'];fail=g.groupby('model')[['replicates','undefined_count','unsupported_defined_count']].sum().reset_index()
fail.rename(columns={'replicates':'estimator_output_rows'},inplace=True)
# Counts repeat the same exposure/rank event across eight mechanisms.
for metric in ['undefined_count','unsupported_defined_count']:
    by=g.groupby(['model','mechanism'])[metric].sum().unstack()
    assert by.nunique(axis=1).eq(1).all()
    fail[metric+'_distinct_assignment_cells']=fail[metric]//8
fail.to_csv(root/'results/diagnostics/failure_inventory.csv',index=False)
failure_markdown='|'+ '|'.join(fail.columns)+'|\n|'+'|'.join(['--']*len(fail.columns))+'|\n'+'\n'.join('|'+ '|'.join(map(str,row))+'|' for row in fail.itertuples(index=False,name=None))
lines += [failure_markdown,'',
'Each estimator has 326400 output rows = 40800 graph/design/p/noise repetitions × 8 mechanisms. The failure inventory counts outputs for accounting and gives distinct assignment-cell events separately; repeated mechanisms are not independent failure observations. No DIM empty arm or nonfinite HT output occurred; the explicit failure policies are still implemented. Finite nonestimable spline/threshold outputs are counted separately from undefined Hajek. The 102-cell ledger has no unrun or failed cell. Selected replay exactly matched 115200 rows in four predeclared structural cells; this is not a full-study replay or independent implementation.','',
'No excluded scope was relabeled as a negative result: no second public graph, missing-edge/treatment-strength/cluster-size grid, adaptive feature selection or GNN was run. Five synthetic graph draws, one public topology, gamma1, fixed response/noise laws, and normal/delta finite-run risk intervals limit generalization and tail precision. All fitted bases/tuning are fixed; no estimator/grid was selected by its production accuracy.','',
'## Required evidence routes','',
'|Question / requirement|Actual evidence|','|--|--|',
'|H1 degree/size and b²+v|summary/performance_by_{graph,family}.csv; diagnostics/diagnostics_by_{graph,family}.csv, decomposition_check.csv, decomposition_selected_graphs.csv; code/tests/test_identities.py|',
'|H2 misspecification, prediction, allocation, tail coupling|summary/paired_by_*.csv; diagnostics/prediction_gate_pairs_by_*.csv, support_coupling_by_*.csv; production_imbalance/; support_bounds.json|',
'|H3 assignment/topology/support/failure|diagnostics/independent_contrasts_by_*.csv, graph_inventory.csv, failure_inventory.csv; complete performance/validity tables|',
'|H4 mapping/noise/coverage/rare risk|paired_by_*.csv; independent_contrasts_by_*.csv; diagnostics_by_*.csv; exact_ht_risk.csv and all102 exact_ht JSON checkpoints|',
'|Completeness/provenance|analysis/production_audit.json, summary_audit.json, diagnostics_audit.json, execution_manifest.json, final_execution.json, cell_ledger.csv; raw metadata/Parquet; summary and diagnostics manifests|',
'|Clean replay / environment / commands|analysis/reproduction_audit.json, postprocessing_timings.json, delivery_reproduction.md; code/environment.json, requirements-lock.txt; download_data.py, run_study.py, finalize_results.py, final_report.py|','',
'This handoff is the analysis owner’s evidence and validity record. Presentation owns final figures/tables, paper owns report integration, story owns protocol coverage, and internal review retains independent release judgement.']
(notes/'final_findings.md').write_text('\n'.join(lines)+'\n')
pd.DataFrame(registry).to_csv(root/'results/diagnostics/claim_evidence.csv',index=False)
receipt=dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             inputs=[dict(path=paths[k],sha256=hashes[k]) for k in paths],
             claims=len(registry),evidence_registry_sha256=hashlib.sha256((root/'results/diagnostics/claim_evidence.csv').read_bytes()).hexdigest())
(notes/'findings_manifest.json').write_text(json.dumps(receipt,indent=2))
print(notes/'final_findings.md')
