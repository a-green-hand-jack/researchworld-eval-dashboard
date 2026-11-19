"""Write paper/numbers.tex: every number quoted in the running text, computed from results/tidy/*.csv.

Usage: python3 paper/make_numbers.py [tidy_dir] [out.tex]
Macro names: \\n<Dataset><Cell><Quantity><Min|Max>, ranges are over the four models of the dataset.
"""
import sys, os
import numpy as np, pandas as pd

here = os.path.dirname(os.path.abspath(__file__))
tidy = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, '..', 'results', 'tidy')
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, 'numbers.tex')

DS = {'german': 'Ger', 'acs_employment': 'Acs'}
CELL = {'kernel_q': 'Q', 'kernel_1': 'One', 'kernel_4': 'Four', 'kernel_16': 'Sixteen',
        'perm_1': 'PermOne', 'perm_4': 'PermFour', 'kernel_1_l1default': 'Lone'}
MET = {'top3_hit': 'TopHit', 'top1_jaccard': 'TopOneJac', 'spearman_abs': 'Spear',
       'rel_l2_err': 'RelErr', 'top3_jaccard': 'TopThreeJac', 'rbo': 'Rbo', 'rel_l2_pair_dist': 'PairDist'}
lines = []

seen = set()
vals = {}


def emit(name, val, fmt='{:.3f}'):
    assert name not in seen, name
    seen.add(name)
    vals[name] = val
    lines.append('\\newcommand{\\n%s}{%s}' % (name, fmt.format(val)))

s = pd.read_csv(os.path.join(tidy, 'summary_ci.csv'))
s = s[s.arm != 'none']
for ds, dn in DS.items():
    for cell, cn in CELL.items():
        for met, mn in MET.items():
            stat = 'median' if met == 'rel_l2_err' else 'mean'
            d = s[(s.dataset == ds) & (s.cell == cell) & (s.metric == met) & (s.stat == stat)]
            if len(d) == 0:
                continue
            for q, col in (('Est', 'est'), ('Lo', 'lo'), ('Hi', 'hi')):
                emit(f'{dn}{cn}{mn}{q}Min', d[col].min(), '{:.4f}' if met == 'rel_l2_err' else '{:.3f}')
                emit(f'{dn}{cn}{mn}{q}Max', d[col].max(), '{:.4f}' if met == 'rel_l2_err' else '{:.3f}')
            if met == 'top3_hit':
                emit(f'{dn}{cn}NModels', d.model.nunique(), '{:d}')
                emit(f'{dn}{cn}NRuns', d.R.min(), '{:d}')


# the one model class for which sampling is the practical option: MLP (LR is additive, XGBoost/RF have exact tree algorithms)
for ds, dn in DS.items():
    for cell, cn in (('kernel_q', 'Q'), ('kernel_1', 'One'), ('kernel_4', 'Four')):
        for met, mn, stat in (('top3_hit', 'TopHit', 'mean'), ('rel_l2_err', 'RelErr', 'median'), ('spearman_abs', 'Spear', 'mean')):
            d = s[(s.dataset == ds) & (s.cell == cell) & (s.model == 'mlp') & (s.metric == met) & (s.stat == stat)]
            for q, col in (('Est', 'est'), ('Lo', 'lo'), ('Hi', 'hi')):
                emit(f'{dn}Mlp{cn}{mn}{q}', d[col].iloc[0], '{:.4f}' if met == 'rel_l2_err' else '{:.3f}')
        d = s[(s.dataset == ds) & (s.cell == cell) & (s.model == 'mlp') & (s.metric == 'top3_hit')]
        emit(f'{dn}Mlp{cn}NInst', d.n_instances.iloc[0], '{:d}')

# verdict counts
v = pd.read_csv(os.path.join(tidy, 'verdicts.csv'))
v = v[v.dataset.isin(DS)]
for ds, dn in DS.items():
    for cell, cn in CELL.items():
        d = v[(v.dataset == ds) & (v.cell == cell)]
        if len(d):
            emit(f'{dn}{cn}VerRel', (d.verdict == 'reliable').sum(), '{:d}')
            emit(f'{dn}{cn}VerCond', (d.verdict == 'conditional').sum(), '{:d}')
            emit(f'{dn}{cn}VerUnrel', (d.verdict == 'unreliable').sum(), '{:d}')
emit('VerTotal', len(v[v.dataset.isin(DS)]), '{:d}')
emit('VerTotalAll', len(pd.read_csv(os.path.join(tidy, 'verdicts.csv'))), '{:d}')
va = pd.read_csv(os.path.join(tidy, 'verdicts.csv'))
emit('VerAllCond', (va.verdict == 'conditional').sum(), '{:d}')
emit('VerAllUnrel', (va.verdict == 'unreliable').sum(), '{:d}')
emit('VerAllRel', (va.verdict == 'reliable').sum(), '{:d}')

# per-instance spread at the library default (kernel_1), non-additive models only
r = pd.read_csv(os.path.join(tidy, 'runs_metrics.csv'))
for ds, dn in DS.items():
    d = r[(r.dataset == ds) & (r.cell == 'kernel_1') & (r.metric == 'top3_jaccard') & (r.model != 'lr')]
    emit(f'{dn}FracInstBelowNine', (d.value < 0.9).mean())
    emit(f'{dn}MinInstJac', d.value.min())
    d = r[(r.dataset == ds) & (r.cell == 'kernel_1') & (r.metric == 'top3_hit') & (r.model != 'lr')]
    g = d.groupby('stratum').value.mean()
    emit(f'{dn}HitNear', g['near_boundary']); emit(f'{dn}HitRand', g['random'])

# N3
g = pd.read_csv(os.path.join(tidy, 'gap_to_noise.csv'))
g = g[(g.cell == 'kernel_1') & g.dataset.isin(DS) & (g.model != 'lr')]
g = g[g.sd_diff > 1e-9].assign(ok=lambda x: x.ratio > 2)
for ds, dn in DS.items():
    d = g[g.dataset == ds]
    by = d.groupby('model').ok.mean()
    emit(f'{dn}PairsResMin', by.min()); emit(f'{dn}PairsResMax', by.max())
    by = d[d.pair_rank == 1].groupby('model').ok.mean()
    emit(f'{dn}TopPairResMin', by.min()); emit(f'{dn}TopPairResMax', by.max())
    by = d[d.pair_rank >= 4].groupby('model').ok.mean()
    emit(f'{dn}LowPairsResMin', by.min()); emit(f'{dn}LowPairsResMax', by.max())
    by = d.groupby('model').p_order_reproduced.mean()
    emit(f'{dn}POrderMin', by.min()); emit(f'{dn}POrderMax', by.max())

# N4
vc = pd.read_csv(os.path.join(tidy, 'variance_components_summary.csv'))
vc = vc[~vc.explainer_at_machine_eps.astype(bool)]
for fac, fn in (('background', 'Bg'), ('refit', 'Refit')):
    for ds, dn in DS.items():
        d = vc[(vc.factor == fac) & (vc.dataset == ds)]
        if len(d):
            emit(f'{dn}{fn}RatioMin', d.ratio_factor_to_explainer.min(), '{:.0f}')
            emit(f'{dn}{fn}RatioMax', d.ratio_factor_to_explainer.max(), '{:.0f}')
            emit(f'{dn}{fn}RatioLoMin', d.ratio_lo.min(), '{:.0f}')
            emit(f'{dn}{fn}RelSdFacMin', 100 * d.rel_sd_factor.min(), '{:.1f}')
            emit(f'{dn}{fn}RelSdFacMax', 100 * d.rel_sd_factor.max(), '{:.1f}')
            emit(f'{dn}{fn}RelSdExpMin', 100 * d.rel_sd_explainer.min(), '{:.1f}')
            emit(f'{dn}{fn}RelSdExpMax', 100 * d.rel_sd_explainer.max(), '{:.1f}')
            emit(f'{dn}{fn}NInst', d.n_instances.min(), '{:d}')

# equal total budget: g runs at B/g averaged vs one run at B
e = pd.read_csv(os.path.join(tidy, 'equal_budget.csv'))
e = e[e.dataset.isin(DS) & (e.model != 'lr') & (e.metric == 'rel_l2_err') & (e.single_cell == 'kernel_1')]
emit('EqBudRelErrDiffMin', e.diff_avg_minus_single.min(), '{:.4f}')
emit('EqBudRelErrDiffMax', e.diff_avg_minus_single.max(), '{:.4f}')
e4 = pd.read_csv(os.path.join(tidy, 'equal_budget.csv'))
e4 = e4[e4.dataset.isin(DS) & (e4.model != 'lr') & (e4.metric == 'rel_l2_err') & (e4.single_cell == 'kernel_4')]
emit('EqBudFourRelErrDiffMin', e4.diff_avg_minus_single.min(), '{:.4f}')
emit('EqBudFourRelErrDiffMax', e4.diff_avg_minus_single.max(), '{:.4f}')
emit('EqBudFourAllLoPos', int((e4.lo > 0).all()), '{:d}')
emit('EqBudG', e.g.iloc[0], '{:d}')
t3 = pd.read_csv(os.path.join(tidy, 'equal_budget.csv'))
t3 = t3[t3.dataset.isin(DS) & (t3.model != 'lr') & (t3.metric == 'top3_hit')]
emit('EqBudTopHitAbsMax', t3.diff_avg_minus_single.abs().max(), '{:.3f}')
emit('EqBudAllLoPos', int((e.lo > 0).all()), '{:d}')

# value-function sensitivity (ACSEmployment, kernel_1)
vf = pd.read_csv(os.path.join(tidy, 'valfn_sensitivity.csv'))
for met, mn in (('top3_hit', 'TopHit'), ('spearman_abs', 'Spear'), ('rel_l2_err', 'RelErr')):
    d = vf[(vf.metric == met) & (vf.model != 'lr')]
    emit(f'VfLog{mn}Min', d.est_logodds.min()); emit(f'VfLog{mn}Max', d.est_logodds.max())
    emit(f'VfProb{mn}Min', d.est_probability.min()); emit(f'VfProb{mn}Max', d.est_probability.max())
d = vf[(vf.metric == 'spearman_abs') & (vf.model == 'lr')]
emit('VfLrProbSpear', d.est_probability.iloc[0]); emit('VfLrProbSpearLo', d.lo_probability.iloc[0])

# explained models' held-out performance
mo = pd.read_csv(os.path.join(tidy, 'models.csv'))
for ds, dn in DS.items():
    d = mo[mo.dataset == ds]
    emit(f'{dn}AucMin', d.test_auc.min()); emit(f'{dn}AucMax', d.test_auc.max())
    emit(f'{dn}NTrain', d.n_train.iloc[0], '{:d}'); emit(f'{dn}NTest', d.n_test.iloc[0], '{:d}')
    emit(f'{dn}Dim', d.d.iloc[0], '{:d}')

# cost
b = pd.read_csv(os.path.join(tidy, 'budget_levels.csv'))
for ds, dn in DS.items():
    for cell, cn in (('kernel_1', 'One'), ('kernel_16', 'Sixteen'), ('perm_1', 'PermOne')):
        d = b[(b.dataset == ds) & (b.cell == cell)]
        if len(d):
            emit(f'{dn}{cn}Sec', d.sec_per_explanation_mean.mean(), '{:.2f}')
            emit(f'{dn}{cn}Evals', d.budget_evals.iloc[0], '{:d}')

# bias of shap default l1 arm: exact zeros are verified by experiment-repo; here only the error
# rounded variants for the abstract (precision the intervals justify): 2 decimals, or 2 significant figures for ratios
for n in ('GerLoneRelErrEstMin', 'GerLoneRelErrEstMax', 'GerPairsResMin', 'GerPairsResMax', 'GerPOrderMin', 'GerPOrderMax',
          'GerOneTopHitEstMin', 'GerMlpOneTopHitEst', 'AcsMlpOneTopHitEst', 'GerMlpOneRelErrEst', 'AcsMlpOneRelErrEst'):
    emit(n + 'R', vals[n], '{:.2f}')
for n in ('GerBgRatioMin', 'GerBgRatioMax', 'AcsBgRatioMin', 'AcsBgRatioMax'):
    emit(n + 'R', float('%.2g' % vals[n]), '{:.0f}')

# verdict sensitivity: recount "reliable" cells (l1 off, German and ACS Employment) under stricter thresholds
vs = va[va.dataset.isin(['german', 'acs_employment']) & (va.cell != 'kernel_1_l1default')]
THR = {'Base': (.9, .1, .95), 'StrictA': (.95, .05, .99), 'StrictB': (.99, .02, .99)}
for gn, ms in [('Mlp', ['mlp']), ('Tree', ['xgb', 'rf']), ('Lr', ['lr'])]:
    d = vs[vs.model.isin(ms)]
    emit(f'Sens{gn}N', len(d), '{:d}')
    for tn, (h, e, sg) in THR.items():
        ok = (d.top3_hit_lo >= h) & (d.rel_l2_median <= e) & (d.sign_top3_lo >= sg)
        emit(f'Sens{gn}{tn}', ok.sum(), '{:d}')
        if tn == 'Base':
            assert (ok == (d.verdict == 'reliable')).all()
dm = vs[(vs.model == 'mlp') & (vs.dataset == 'german')]
emit('SensGerMlpHitLoMin', dm.top3_hit_lo.min())
emit('SensGerMlpRelErrMax', dm.rel_l2_median.max())

with open(out, 'w') as f:
    f.write('% Generated by paper/make_numbers.py from results/tidy; do not edit.\n')
    f.write('\n'.join(sorted(set(lines))) + '\n')
print(len(lines), 'macros ->', out)
