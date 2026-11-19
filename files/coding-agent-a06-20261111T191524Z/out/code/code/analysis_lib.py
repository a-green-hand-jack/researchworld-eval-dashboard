import numpy as np, pandas as pd

def mean_se(x):
    x = np.asarray(x, float); return x.mean(), x.std(ddof=1) / np.sqrt(len(x))

def cov_rate(lo, hi, t):
    c = ((lo <= t) & (t <= hi)).astype(float); return c.mean(), c.std(ddof=1) / np.sqrt(len(c))

METHODS = {  # name: (estimate, target, lo, hi)
    'Naive (dev score)':        ('naive', 'theta', 'naive_lo', 'naive_hi'),
    'Holdout split (50/50)':    ('split0.5_est', 'split0.5_k_theta', 'split0.5_lo', 'split0.5_hi'),
    '5-fold cross-fit':         ('cv_est', 'theta', None, None),
    'Replay bootstrap (opt.)':  ('boot_opt', 'theta', None, None),
    'Replay bootstrap (.632)':  ('boot632', 'theta', None, None),
    'Empirical Bayes':          ('eb_est', 'theta', 'ebw_lo', 'ebw_hi'),
    'Max-t simultaneous':       ('naive', 'theta', 'maxt_lo', 'maxt_hi'),
    'Conditional (winner)':     ('cond_med', 'theta', 'cond_lo', 'cond_hi'),
    'Ladder ($n^{-1/2}$)':      ('ladder_n12_est', 'ladder_n12_k_theta', None, None),
}

def method_table(df):
    rows = []
    for name, (e, t, lo, hi) in METHODS.items():
        if e not in df or df[e].isna().all(): continue
        d = df.dropna(subset=[e] + ([lo, hi] if lo else [])); err = d[e] - d[t]
        if len(d) < 30: continue
        r = dict(method=name, bias=err.mean(), bias_se=err.std(ddof=1) / np.sqrt(len(err)), rmse=np.sqrt((err ** 2).mean()))
        if lo and lo in d:
            c, cse = cov_rate(d[lo], d[hi], d[t]); r.update(cover=c, cover_se=cse, width=(d[hi] - d[lo]).clip(upper=1).mean())
        rows.append(r)
    return pd.DataFrame(rows)
