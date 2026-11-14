"""LaTeX tables for the paper from results/*.csv -> paper/tables/*.tex"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import RULES, CARDINAL
SH = {'mean': 'Mean', 'geo': 'Geometric', 'harm': 'Harmonic', 'min': 'Minimum', 'median': 'Median', 'borda': 'Borda', 'copeland': 'Copeland', 'plurality': 'Plurality'}
BN = [('HELM-MMLU', 'HELM'), ('OLLB-6', 'OLLB-6'), ('OLLB-BBH24', 'BBH24')]
T = pd.read_csv('results/common_tests.csv')
os.makedirs('paper/tables', exist_ok=True)

def fmt(x, ns=False):
    s = f'{x:.2f}' if x < 10 else f'{x:.1f}'
    return s + ('$^{\\dagger}$' if ns else '')

# ---- main paired-ratio table: median (rule / mean) over common targets; dagger = not significant after Holm (alpha=.05)
with open('paper/tables/paired_ratio.tex', 'w') as f:
    f.write('\\begin{tabular}{l' + 'ccc' * 3 + '}\\toprule\n')
    f.write(' & \\multicolumn{3}{c}{Magnitude $L^*$ ($g{=}100$)} & \\multicolumn{3}{c}{Breadth $K^*$ ($g{=}100$)} & \\multicolumn{3}{c}{Depth $g^*$}\\\\\n')
    f.write('\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\\cmidrule(lr){8-10}\nRule & ' + ' & '.join([b for _, b in BN] * 3) + '\\\\\\midrule\n')
    for r in RULES[1:]:
        cells = []
        for metric in ['L1_100', 'K_100', 'gstar']:
            for bn, _ in BN:
                x = T[(T.bench == bn) & (T.metric == metric) & (T.rule == r)].iloc[0]
                cells.append(fmt(x.median_ratio, ns=x.p_holm >= 0.05))
        f.write(SH[r] + ' & ' + ' & '.join(cells) + '\\\\\n')
    # reference row: median absolute value for the mean rule
    cells = []
    for metric in ['L1_100', 'K_100', 'gstar']:
        for bn, _ in BN:
            x = T[(T.bench == bn) & (T.metric == metric)].iloc[0]; cells.append(f'{x.median_mean:.1f}')
    f.write('\\midrule\nMean (abs., ref.) & ' + ' & '.join(cells) + '\\\\\n\\bottomrule\\end{tabular}\n')

# ---- full appendix tables (one per metric)
for metric, name, fn in [('L1_100', 'Magnitude', 'L'), ('K_100', 'Breadth', 'K'), ('gstar', 'Depth', 'g')]:
    with open(f'paper/tables/paired_full_{fn}.tex', 'w') as f:
        f.write('\\begin{tabular}{llrccc}\\toprule\nBenchmark & Rule & pairs & median ratio [95\\% CI] & share lower . higher & $p_{\\rm Holm}$\\\\\\midrule\n')
        for bn, _ in BN:
            for r in RULES[1:]:
                x = T[(T.bench == bn) & (T.metric == metric) & (T.rule == r)].iloc[0]
                p = '<0.001' if x.p_holm < 0.001 else f'{x.p_holm:.3f}'
                f.write(f'{bn if r == "geo" else ""} & {SH[r]} & {int(x.n_pairs)} & {x.median_ratio:.2f} [{x.ratio_lo:.2f}, {x.ratio_hi:.2f}] & {x.frac_rule_lower:.2f} . {x.frac_rule_higher:.2f} & {p}\\\\\n')
            f.write('\\midrule\n' if bn != BN[-1][0] else '')
        f.write('\\bottomrule\\end{tabular}\n')

# ---- descriptives
D = pd.read_csv('results/descriptives.csv'); Wn = pd.read_csv('results/winners.csv')
with open('paper/tables/descriptives.tex', 'w') as f:
    f.write('\\begin{tabular}{lrrrrr}\\toprule\nBoard & Models & Tasks & Ordinal pool & SD of model means & Add. resid. SD\\\\\\midrule\n')
    for _, r in D.iterrows():
        f.write(f"{r.bench} & {int(r.models)} & {int(r.tasks)} & {int(r.pool_ordinal)} & {r.sd_across_models_of_mean:.1f} & {r.additive_resid_sd:.1f}\\\\\n")
    f.write('\\bottomrule\\end{tabular}\n')

# ---- calibrated caps
Q = pd.read_csv('results/finetune_gain_quantiles.csv').rename(columns={'Unnamed: 0': 'task'})
Qp = Q[Q.pairs.str.startswith('tuned')]
CFa = pd.read_csv('results/calibrated_feasibility_ollb6.csv'); CF = CFa[CFa.pairs == 'tuned_to_tuned'].groupby('rule', sort=False)[['feasible_q90', 'feasible_q99', 'feasible_max']].mean(); CFall = CFa[CFa.pairs == 'all_pairs'].groupby('rule', sort=False)[['feasible_q90', 'feasible_q99', 'feasible_max']].mean()
with open('paper/tables/calib.tex', 'w') as f:
    f.write('\\begin{tabular}{lrrrr}\\toprule\nTask & frac.\\ gain$>0$ & q90 & q99 & max\\\\\\midrule\n')
    for _, r in Qp.iterrows(): f.write(f"{r.task} & {r.frac_positive:.2f} & {r.q90:.1f} & {r.q99:.1f} & {r['max']:.1f}\\\\\n")
    f.write('\\bottomrule\\end{tabular}\n')
with open('paper/tables/calib_feas.tex', 'w') as f:
    f.write('\\begin{tabular}{lcccccc}\\toprule\n & \\multicolumn{3}{c}{tuned$\\to$tuned pairs (88)} & \\multicolumn{3}{c}{all pairs (480)}\\\\\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\nRule & q90 & q99 & max & q90 & q99 & max\\\\\\midrule\n')
    for r in RULES: f.write(f"{SH[r]} & {CF.loc[r,'feasible_q90']:.2f} & {CF.loc[r,'feasible_q99']:.2f} & {CF.loc[r,'feasible_max']:.2f} & {CFall.loc[r,'feasible_q90']:.2f} & {CFall.loc[r,'feasible_q99']:.2f} & {CFall.loc[r,'feasible_max']:.2f}\\\\\n")
    f.write('\\bottomrule\\end{tabular}\n')

# ---- case study
C = pd.read_csv('results/case_study_benchmaxx.csv'); O = pd.read_csv('results/case_study_observed.csv').iloc[0]
with open('paper/tables/case.tex', 'w') as f:
    f.write('\\begin{tabular}{lrr}\\toprule\n & Breadth $K$ & Magnitude $L$ (points)\\\\\\midrule\n')
    f.write(f'Observed parent$\\to$child gain & {int(O.K)} & {O.L1:.0f}\\\\\\midrule\n')
    for _, r in C.iterrows(): f.write(f"Minimum needed, {SH[r.rule]} & {int(r.K_min)} & {r.L1_min:.0f}\\\\\n")
    f.write('\\bottomrule\\end{tabular}\n')

# ---- noise summary table
dr = pd.read_csv('results/noise_helm_draws.csv'); wn = pd.read_csv('results/noise_helm_winner.csv')
M = pd.read_csv('results/main_helm.csv'); M = M[M['rank'] <= 11].groupby('rule').median(numeric_only=True)
with open('paper/tables/noise.tex', 'w') as f:
    f.write('\\begin{tabular}{lcccc}\\toprule\nRule & $K^*$ observed & $K^*$ bootstrap median [95\\%] & $L^*$ bootstrap median [95\\%] & P(winner unchanged)\\\\\\midrule\n')
    for r in RULES:
        k = dr[dr.rule == r]['K_100']; l = dr[dr.rule == r]['L1_100']; w = wn[wn.rule == r]['same'].mean()
        f.write(f"{SH[r]} & {M.loc[r,'K_100']:.1f} & {k.median():.1f} [{k.quantile(.025):.1f}, {k.quantile(.975):.1f}] & {l.median():.1f} [{l.quantile(.025):.1f}, {l.quantile(.975):.1f}] & {w:.2f}\\\\\n")
    f.write('\\bottomrule\\end{tabular}\n')
# ---- winners
Wn = pd.read_csv('results/winners.csv'); BNm = {'HELM-MMLU': 'HELM', 'OLLB-6': 'OLLB-6', 'OLLB-BBH24': 'BBH24'}
with open('paper/tables/winners.tex', 'w') as f:
    f.write('\\begin{tabular}{llp{9.5cm}}\\toprule\nBoard & Rule & Incumbent\\\\\\midrule\n')
    for b in Wn.bench.unique():
        for _, r in Wn[Wn.bench == b].iterrows(): f.write(f"{BNm[b]} & {SH[r.rule]} & \\texttt{{{r.winner.replace('_', chr(92) + '_')}}}\\\\\n")
        f.write('\\midrule\n')
    f.write('\\bottomrule\\end{tabular}\n')
print('tables ok')
