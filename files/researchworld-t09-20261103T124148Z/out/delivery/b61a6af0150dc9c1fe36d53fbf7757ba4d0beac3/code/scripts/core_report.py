"""Produce an analysis-owner core evidence memo from actual summary rows."""
import json
from pathlib import Path
import pandas as pd

root=Path(__file__).resolve().parents[1]
if root.name=='code':root=root.parent
notes=root/'analysis' if (root/'code').exists() else root/'notes'
folder=root/'results/core_summary'
f=pd.read_csv(folder/'performance_by_family.csv')
g=pd.read_csv(folder/'performance_by_graph.csv')
p=pd.read_csv(folder/'paired_by_family.csv')


def one(frame,**values):
    chosen=frame
    for key,value in values.items():chosen=chosen[chosen[key]==value]
    assert len(chosen)==1,values
    return chosen.iloc[0]


def family(n,d,design,mechanism,model):
    return one(f,graph_kind='regular',n=n,degree_target=d,design=design,mechanism=mechanism,model=model)


def ci(row,name):
    return f"{row[name+'_graph_mean']:.4g} [{row[name+'_graph_lo']:.4g}, {row[name+'_graph_hi']:.4g}]"


lines=['# Corrected completed core evidence memo',
       '',
       'Scope:72/72core cells,400repetitions/cell, all five synthetic graph seeds and the full SNAP graph. '
       'Noise and imbalance panels are outside this memo. Synthetic-family values below are equal-graph '
       'means with approximate95% t4 intervals; public-graph values have conditional Monte Carlo intervals. '
       'These are selected explanatory comparisons from complete tables, not multiplicity-adjusted discoveries '
       'or universal risk rankings. The complete raw/family/paired tables retain every planned core condition.',
       '', '## H1: conditional contrast variance and degree/size', '',
       'Linear DGP, correctly specified linear regression, node Bernoulli(.5): all fits are endpoint-estimable.', '',
       '|n|degree|Mean graph RMSE [95% graph CI]|sqrt(mean oracle variance)|',
       '|--:|--:|--:|--:|']
for n,d in [(2000,4),(2000,20),(2000,80),(8000,20)]:
    r=family(n,d,'bernoulli','linear','linear')
    lines.append(f"|{n}|{d}|{ci(r,'rmse')}|{r.oracle_variance_mean_graph_mean**.5:.4g}|")
lines+=['', 'Degree increases error at fixed n; increasing n at fixed degree reduces it. '
        'The oracle variance is explanatory simulation evidence, not a feasible certificate under misspecification. '
        'The first column averages RMSE across graphs; the last takes the square root after averaging variance.',
        '', '## H2: prediction and endpoint accuracy can disagree', '']
r=one(p,graph_kind='regular',n=2000,degree_target=20,design='cluster',mechanism='cubic',model='cubic',reference='linear')
lines += [f"Cubic-minus-linear regression on the cubic DGP, regular n2000/d20 under cluster assignment: "
          f"GATE MSE difference {ci(r,'delta_mse')}; fresh-assignment noisy-outcome prediction MSE "
          f"difference {ci(r,'delta_prediction_mse')}. Both contrasts use the same within-cell streams; "
          'positive means cubic is worse. Both methods are fully defined/estimable here. '
          'Improved interior prediction therefore does not certify improved GATE.', '']
for mechanism in ['quadratic','cubic']:
    r=family(2000,20,'bernoulli',mechanism,'linear')
    lines.append(f"Linear regression on {mechanism}: signed bias {ci(r,'bias')}, mean RMSE {ci(r,'rmse')}.")
lines += ['The near-zero signed quadratic bias agrees with complement cancellation; it does not imply that '
          'quadratic conditional biases or all forms of misspecification vanish. The imbalance check remains separate.',
          '', '## H3/H4: correct mapping and cluster support have conditional value', '',
          'Twohop DGP, twohop-minus-linear regression under node assignment:', '',
          '|n|degree|GATE MSE difference [95% graph CI]|linear mean RMSE|twohop mean RMSE|',
          '|--:|--:|--:|--:|--:|']
for n,d in [(2000,4),(2000,20),(8000,20)]:
    r=one(p,graph_kind='regular',n=n,degree_target=d,design='bernoulli',mechanism='twohop',model='twohop',reference='linear')
    a=family(n,d,'bernoulli','twohop','linear');b=family(n,d,'bernoulli','twohop','twohop')
    lines.append(f"|{n}|{d}|{ci(r,'delta_mse')}|{a.rmse_graph_mean:.4g}|{b.rmse_graph_mean:.4g}|")
lines += ['', 'The shape/mapping-aware model removes conditional mean bias when estimable, but it is not a risk '
          'lower bound: its larger endpoint noise variance can outweigh that repair. Keep the adverse degree20 '
          'n2000 result alongside the favorable sparse result and the larger-n comparison.', '',
          '|Threshold DGP, shape-aware oracle|Mean graph RMSE [95% graph CI]|Estimable fraction|',
          '|--|--:|--:|']
for d,design in [(4,'bernoulli'),(80,'bernoulli'),(80,'cluster')]:
    r=family(2000,d,design,'threshold','threshold_oracle')
    lines.append(f"|degree{d}, {design}|{ci(r,'rmse')}|{r.valid_fraction_graph_mean:.4g}|")
lines+=['', 'Correct response features can fail at unsupported endpoints. The operational RMSE above includes '
         'every finite minimum-norm estimate; estimable-only risk is a separate conditional metric. '
         'Cluster assignment raises threshold estimability in the dense case but does not make every fit identified.', '']
for design in ['bernoulli','cluster']:
    r=family(2000,80,design,'linear','spline')
    lines.append(f"Dense linear DGP, fixed spline under {design}: mean graph RMSE {ci(r,'rmse')}, "
                 f"estimable fraction {r.valid_fraction_graph_mean:.4g}.")
lines += ['This is an adverse flexible-fit example: greater support/estimability under clusters does not '
          'guarantee lower operational error. Very large, unstable spline risks and wide five-graph intervals '
          'must remain visible; unsupported minimum-norm returns are not endpoint recovery. Untruncated '
          'symmetric t intervals can extend below zero for unstable nonnegative metrics; that reflects poor '
          'precision and does not imply negative true risk.', '',
          '## Fixed public topology and rare-exposure tails', '']
for design in ['bernoulli','cluster']:
    r=one(g,graph_kind='facebook',design=design,mechanism='linear',model='linear')
    lines.append(f"Full SNAP, linear DGP/linear regression, {design}: RMSE {r.rmse:.4g} "
                 f"[{r.rmse_lo:.4g}, {r.rmse_hi:.4g}] (conditional MC95%), HC3 coverage "
                 f"{r.cover_hc3:.4g} [{r.cover_hc3_lo:.4g}, {r.cover_hc3_hi:.4g}], "
                 f"oracle coverage {r.cover_oracle:.4g} [{r.cover_oracle_lo:.4g}, {r.cover_oracle_hi:.4g}].")
risks=[]
for file in (root/'results/production_core/exact_ht').glob('*.json'):
    risks.extend(json.loads(file.read_text()))
for design in ['bernoulli','cluster']:
    r=one(g,graph_kind='facebook',design=design,mechanism='linear',model='ht')
    exact=next(x for x in risks if x['graph']=='snap_facebook' and x['design']==design and x['endpoint_family']=='linear')
    lines.append(f"SNAP one-hop HT, {design}: empirical R400 RMSE {r.rmse:.4g}; exact log10(RMSE) "
                 f"{exact['ht_exact_log10_rmse']:.6g}. The empirical number and its normal interval miss "
                 'rare-event risk and cannot be used as the true-risk comparison.')
lines += ['', 'The historical public graph has synthetic outcomes and fixed covariates/partition; it is a '
          'conditional topology case, not real-platform effect validation. Exact HT risk is one-hop/oracle '
          'evidence; twohop has an intentionally misspecified one-hop comparator and is excluded from that identity.',
          '', '## Provenance and limits', '',
          'Generated by code/scripts/core_report.py (scripts/core_report.py in the analysis repository) from '
          'results/core_summary/{performance_by_graph,performance_by_family,paired_by_family}.csv and '
          'production_core/exact_ht/*.json. Standard summary_manifest.json hashes all72raw inputs and its '
          'source. The complete corrected checkpoint and exact-input audit receipts are production_audit.json and summary_audit.json. '
          'The full102-cell summary audit includes every core row; v1 core-only receipts are archived under roundoff_v1/. '
          'The final complete-study claim map supersedes this stage memo; no noise/imbalance finding, complete '
          '102-cell assertion, universal best estimator, novel estimator/theorem or practical oracle inference '
          'claim is made here.']
(notes/'core_findings.md').write_text('\n'.join(lines)+'\n')
print(notes/'core_findings.md')
