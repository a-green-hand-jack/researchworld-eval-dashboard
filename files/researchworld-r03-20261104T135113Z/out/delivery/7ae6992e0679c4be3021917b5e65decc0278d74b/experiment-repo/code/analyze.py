"""Summaries from results/raw/*.parquet -> results/summary/*.csv

usage: python analyze.py <name> [<name> ...]     (name = file stem in results/raw, e.g. B_mteb_dense56)
Writes, per name:
  curves_<name>.csv   : selector, method, k -> nMSE (pooled squared z-error / n targets), RMSE in score points, MAE, 95% CI (bootstrap over test models)
  paired_<name>.csv   : paired difference (selector A - random) in nMSE with CI, per method,k   (negative = A better than random)
  kstar_<name>.csv    : smallest k whose CI upper bound meets each target (nMSE <= 0.5/0.25/0.15 or RMSE <= 3/2 points)
"""
import os, sys
import numpy as np, pandas as pd
from analysis_lib import per_model, boot_metric, paired_diff, gap_closed

RAW = os.path.join(os.path.dirname(__file__), '..', 'results', 'raw')
OUT = os.path.join(os.path.dirname(__file__), '..', 'results', 'summary')

def run(name, n_boot=500):
    os.makedirs(OUT, exist_ok=True)
    d = pd.read_parquet(os.path.join(RAW, name + '.parquet'))
    g = per_model(d)
    a = boot_metric(g, ['selector', 'method', 'k'], n_boot, metric='nmse').rename(columns={'est': 'nmse', 'lo': 'nmse_lo', 'hi': 'nmse_hi'})
    b = boot_metric(g, ['selector', 'method', 'k'], n_boot, metric='mse_pts').rename(columns={'est': 'rmse_pts', 'lo': 'rmse_lo', 'hi': 'rmse_hi'})
    c = boot_metric(g, ['selector', 'method', 'k'], n_boot, metric='mae_pts').rename(columns={'est': 'mae_pts', 'lo': 'mae_lo', 'hi': 'mae_hi'})
    cur = a.merge(b, on=['selector', 'method', 'k']).merge(c, on=['selector', 'method', 'k'])
    rp = os.path.join(RAW, name + '_rank.parquet')
    if os.path.exists(rp):
        r = pd.read_parquet(rp).groupby(['selector', 'method', 'k']).spearman.mean().reset_index()
        cur = cur.merge(r, on=['selector', 'method', 'k'], how='left')
    cur.to_csv(os.path.join(OUT, f'curves_{name}.csv'), index=False)
    pr = []
    for s in g.selector.unique():
        if s in ('random',) or 'random' not in set(g.selector):
            continue
        p = paired_diff(g, s, 'random', n_boot=n_boot)
        p.insert(0, 'selector', s)
        pr.append(p)
    if pr:
        pd.concat(pr).to_csv(os.path.join(OUT, f'paired_{name}.csv'), index=False)
    ks = []
    for (s, m), sub in cur.groupby(['selector', 'method']):
        sub = sub.sort_values('k')
        row = dict(selector=s, method=m)
        for lab, col, thr in [('nmse<=0.5', 'nmse_hi', .5), ('nmse<=0.25', 'nmse_hi', .25), ('nmse<=0.15', 'nmse_hi', .15), ('rmse<=3', 'rmse_hi', 3), ('rmse<=2', 'rmse_hi', 2)]:
            ok = sub[sub[col] <= thr]
            row[lab] = int(ok.k.min()) if len(ok) else np.nan
        ks.append(row)
    pd.DataFrame(ks).to_csv(os.path.join(OUT, f'kstar_{name}.csv'), index=False)
    fp = os.path.join(RAW, 'F_' + (name[2:] if name.startswith('B_') else name) + '.parquet')
    if fp and os.path.exists(fp):
        gf = per_model(pd.read_parquet(fp))
        G, fl = gap_closed(g, gf, n_boot=n_boot)
        G.to_csv(os.path.join(OUT, f'gapclosed_{name}.csv'), index=False)
        fl.to_csv(os.path.join(OUT, f'floor_{name}.csv'), index=False)
        gk = []
        for (s_, m_), sub in G.groupby(['selector', 'method']):
            sub = sub.sort_values('k')
            row = dict(selector=s_, method=m_)
            for tag in ('own', 'best'):
                for gg in (0.8, 0.9):
                    ok = sub[sub[f'G_{tag}_lo'] >= gg]
                    row[f'k*G_{tag}>={gg}'] = int(ok.k.min()) if len(ok) else np.nan
            gk.append(row)
        pd.DataFrame(gk).to_csv(os.path.join(OUT, f'kstar_gap_{name}.csv'), index=False)
    print(name, 'ok', len(cur))

if __name__ == '__main__':
    for n in sys.argv[1:]:
        run(n)
