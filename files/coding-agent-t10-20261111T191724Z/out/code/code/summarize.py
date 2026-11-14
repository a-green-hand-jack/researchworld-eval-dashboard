"""Summarize Monte-Carlo results: coverage (Wilson 95% CI), mean width (+-SE), paired width ratio vs PPI++ (mean +- SE)."""
import sys, os, numpy as np, pandas as pd
from scipy import stats
METHODS = ['classical', 'ppi', 'ppipp', 'ppipp_u', 'lin', 'iso', 'bin10', 'spl', 'auto'] + [m + '_t' for m in ('ppipp_u', 'lin', 'iso', 'spl', 'auto', 'classical', 'ppi')]

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h

def add_t(df, methods=('ppipp_u', 'lin', 'iso', 'spl', 'auto', 'classical', 'ppi')):
    """Student-t variants: same center, half-width rescaled by t_{n-1,.975}/z_{.975} (df = number of labeled points - 1)."""
    df = df.copy(); fac = stats.t.ppf(0.975, df.n - 1) / stats.norm.ppf(0.975)
    for m in methods:
        if f'lo_{m}' in df:
            c = (df[f'lo_{m}'] + df[f'hi_{m}']) / 2; h = (df[f'hi_{m}'] - df[f'lo_{m}']) / 2 * fac
            df[f'lo_{m}_t'] = c - h; df[f'hi_{m}_t'] = c + h
    return df

def summarize(df, ref='ppipp'):
    rows = []
    for cell, g in df.groupby('cell', sort=False):
        R = len(g); base = dict(cell=cell, dgp=g.dgp.iloc[0], n=int(g.n.iloc[0]), N=int(g.N.iloc[0]), reps=R)
        for m in METHODS:
            if f'lo_{m}' not in g or g[f'lo_{m}'].isna().all(): continue
            w = (g[f'hi_{m}'] - g[f'lo_{m}']).values
            cov = ((g[f'lo_{m}'] <= g.truth) & (g.truth <= g[f'hi_{m}'])).values
            lo, hi = wilson(cov.sum(), R)
            r1, r2 = ('ppipp_u_t', 'ppipp_u_t') if m.endswith('_t') else (ref, 'ppipp_u')
            wr = w / (g[f'hi_{r1}'] - g[f'lo_{r1}']).values if f'lo_{r1}' in g else np.full(R, np.nan)
            wu = w / (g[f'hi_{r2}'] - g[f'lo_{r2}']).values if f'lo_{r2}' in g else np.full(R, np.nan)
            rows.append(dict(base, method=m, cover=cov.mean(), cover_lo=lo, cover_hi=hi, width=w.mean(), width_se=w.std(ddof=1) / np.sqrt(R),
                             ratio=wr.mean(), ratio_se=wr.std(ddof=1) / np.sqrt(R), ratio_u=wu.mean(), ratio_u_se=wu.std(ddof=1) / np.sqrt(R),
                             # coverage of the paired difference: P(method covers) - P(ref covers)
                             ))
    return pd.DataFrame(rows)

if __name__ == '__main__':
    for exp in sys.argv[1:]:
        df = add_t(pd.read_csv(f'/work/results/{exp}.csv.gz')); s = summarize(df); s.to_csv(f'/work/results/summary_{exp}.csv', index=False)
        print(exp, len(s))
