"""H1 on a real dense matrix: forecast of error(k) from the history-fitted spectrum vs the measured held-out error.
Forecasts (all from history-fit only, selection = the greedyAcomp order of that fit): naive plug-in (formula (a)),
fm_noinfl (BBP de-biased, unrecoverable factors folded into noise), fm (adds the (d1) inflation), floor (c).
python exp/analyze_h1.py SETTING [--sel greedyAcomp] -> results/SETTING/h1.csv, h1_summary.json"""
import sys, os, json, glob, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
import analysis as A, bselect as SEL, theory as TH

ap = argparse.ArgumentParser(); ap.add_argument('setting'); ap.add_argument('--sel', default='greedyAcomp')
ap.add_argument('--dir', default='results'); a = ap.parse_args()
d = f"{a.dir}/{a.setting}"
KS = [1, 2, 3, 5, 8, 12, 20]
crit = dict(greedyAcomp='A_comp', greedyA='A_all')[a.sel]
df = A.load(d); df = df[(df.selector == a.sel) & (df.method == 'fa')]
info = {(i['rep'], i['fold']): i for f in sorted(glob.glob(f"{d}/info_rep*.json")) for i in json.load(open(f))}
rows = []
for (rep, fold), g in df.groupby(['rep', 'fold']):
    z = np.load(f"{d}/fit_rep{rep}_fold{fold}.npz"); Lam, psi = z['Lam'], z['psi']
    N = len(psi); M = info[(rep, fold)]['M']; par = dict(Lam=Lam, psi=psi)
    ks = [k for k in KS if k in set(g.k) and k < N]
    order = SEL.greedy_design(par, np.arange(N), max(ks), crit)
    for k in ks:
        S = order[:k]
        meas = g[g.k == k].mse.mean()
        rows.append(dict(rep=rep, fold=fold, k=k, M=M, N=N, r=Lam.shape[1], measured=meas,
                         naive=TH.bayes_error(Lam, psi, S), fm_noinfl=TH.forecast_finite_m(Lam, psi, M, S, inflate=False),
                         fm=TH.forecast_finite_m(Lam, psi, M, S), floor=TH.tail_floor(Lam, psi, S)))
R = pd.DataFrame(rows); R.to_csv(f"{d}/h1.csv", index=False)
# pooled: average over folds/reps per k, bootstrap over (rep, fold) units for the gap
P = R.groupby('k')[['measured', 'naive', 'fm_noinfl', 'fm', 'floor']].mean()
summ = {}
for f in ('naive', 'fm_noinfl', 'fm'):
    gap = (np.sqrt(P[f]) - np.sqrt(P.measured)).abs() / np.sqrt(P.measured)
    gap_f = R.assign(g=(np.sqrt(R[f]) - np.sqrt(R.measured)).abs() / np.sqrt(R.measured)).groupby(['rep', 'fold']).g.median()
    summ[f] = dict(median_rel_rmse_gap_pooled=float(gap.median()), max_gap=float(gap.max()),
                   signed_gap_by_k={int(k): float((np.sqrt(P[f][k]) - np.sqrt(P.measured[k])) / np.sqrt(P.measured[k])) for k in P.index},
                   median_gap_per_fold_median=float(gap_f.median()), fold_gap_q=[float(x) for x in gap_f.quantile([.1, .9])])
# measured below the floor by more than its bootstrap CI?
cur = A.curve(A.per_model(df), a.sel, 'fa', 'mse'); cur = cur.set_index('k')
below = {int(k): bool(cur.loc[k, 'hi'] ** 2 < P.floor[k]) for k in P.index}
summ['measured_below_floor_beyond_CI'] = below
# effective rank: likelihood-selected r vs BBP count from the de-biased spectrum of the same fit
er = []
for (rep, fold), g in R.groupby(['rep', 'fold']):
    z = np.load(f"{d}/fit_rep{rep}_fold{fold}.npz"); Lam, psi = z['Lam'], z['psi']; M = g.M.iloc[0]; N = len(psi)
    Lc, psic, rho, rho_fit = TH.debias_spikes(Lam, psi, M)
    er.append(dict(rep=rep, fold=fold, r_sel=Lam.shape[1], rank_eff_debiased=Lc.shape[1], thr=float(np.sqrt(N / M))))
er = pd.DataFrame(er); er['diff'] = er.r_sel - er.rank_eff_debiased
summ['rank'] = dict(mean_r_sel=float(er.r_sel.mean()), mean_rank_eff=float(er.rank_eff_debiased.mean()),
                    frac_within2=float((er['diff'].abs() <= 2).mean()))
er.to_csv(f"{d}/h1_rank.csv", index=False)
json.dump(summ, open(f"{d}/h1_summary.json", 'w'), indent=1)
pd.set_option('display.width', 200); print(P.round(4)); print(json.dumps({k: v for k, v in summ.items() if k != 'measured_below_floor_beyond_CI'}, indent=1))
