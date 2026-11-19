"""E5: the literal fixed-sets setting on 'ballots' (n=1027 labeled, N=78150 unlabeled, binary Yhat). No ground truth for the
unlabeled set exists, so only intervals/widths are reported (no coverage claim). Cross-fit seeds are varied to show stability."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ppi_py
from cppi import crossfit_mean, ci_from, ppi_pp_unclipped_ci
d = np.load('/work/data/ballots.npz'); Y = d['Y'].astype(float); F = d['Yhat'].astype(float); Fu = d['Yhat_unlabeled'].astype(float)
rows = []
def add(name, lo, hi, est=np.nan): rows.append(dict(method=name, lo=lo, hi=hi, width=hi - lo, est=est))
lo, hi = ppi_py.classical_mean_ci(Y, alpha=0.05); add('classical', float(lo[0]) if np.ndim(lo) else float(lo), float(hi[0]) if np.ndim(hi) else float(hi), Y.mean())
for nm, lam in [('ppi', 1.0), ('ppipp', None)]:
    lo, hi = ppi_py.ppi_mean_ci(Y, F, Fu, alpha=0.05, lam=lam); add(nm, float(np.ravel(lo)[0]), float(np.ravel(hi)[0]))
lo, hi = ppi_pp_unclipped_ci(Y, F, Fu); add('ppipp_u', lo, hi)
for k in ['lin', 'iso', 'bin10', 'spl', 'auto']:
    ws = []; ests = []
    for s in range(20):
        th, se = crossfit_mean(Y, F, Fu, k, rng=np.random.default_rng(s)); lo, hi = ci_from(th, se); ws.append(hi - lo); ests.append(th)
    add(k, th - (hi - lo) / 2, th + (hi - lo) / 2, np.mean(ests)); rows[-1]['width'] = float(np.mean(ws)); rows[-1]['width_sd_over_seeds'] = float(np.std(ws))
df = pd.DataFrame(rows); df.to_csv('/work/results/E5_ballots.csv', index=False); print(df.round(5).to_string())
print('P(Yhat=1) labeled/unlabeled:', F.mean(), Fu.mean(), ' P(Y=1|Yhat=1), P(Y=1|Yhat=0):', Y[F == 1].mean(), Y[F == 0].mean())
