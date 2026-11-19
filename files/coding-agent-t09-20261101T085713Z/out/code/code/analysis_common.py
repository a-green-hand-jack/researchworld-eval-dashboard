import os, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RES, FIG, TAB = ROOT + '/results', ROOT + '/figs', ROOT + '/paper/tables'
OI = {'DM': '#999999', 'OLS-x': '#0072B2', 'OLS-quad': '#56B4E9', 'OLS-rich': '#CC79A7', 'OLS-oracle': '#009E73',
      'GBDT': '#D55E00', 'Hajek': '#E69F00', 'OLS-xd': '#0072B2', 'OLS-x2': '#CC79A7', 'OLS-cd': '#F0E442', 'OLS-c': '#000000'}
plt.rcParams.update({'font.size': 8, 'axes.titlesize': 8, 'axes.labelsize': 8, 'legend.fontsize': 7, 'xtick.labelsize': 7,
                     'ytick.labelsize': 7, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150,
                     'savefig.bbox': 'tight', 'lines.linewidth': 1.2})


def load(name):
    df = pd.read_csv(f'{RES}/{name}.csv.gz')
    df['err'] = df.tau_hat - df.tau
    df['errS'] = df.tau_S - df.tau
    df['errN'] = df.tau_hat - df.tau_S
    return df


def summarize(df, keys, B=300, seed=0):
    """Per group: bias, SD, RMSE (+ bootstrap 95% CI for RMSE), bias_S, sd_S, sd_N, mean w1/w2, failure rate."""
    rng = np.random.default_rng(seed)
    rows = []
    for k, g in df.groupby(keys, dropna=False):
        e = g.err.values; ok = ~np.isnan(e)
        eo = e[ok]
        r = dict(zip(keys, k if isinstance(k, tuple) else (k,)))
        r['R'] = len(e); r['fail'] = 1 - ok.mean()
        r['bias'] = eo.mean(); r['sd'] = eo.std(ddof=1); r['rmse'] = np.sqrt((eo ** 2).mean())
        idx = rng.integers(0, len(eo), (B, len(eo)))
        rm = np.sqrt((eo[idx] ** 2).mean(1)); r['rmse_lo'], r['rmse_hi'] = np.percentile(rm, [2.5, 97.5])
        r['bias_se'] = eo.std(ddof=1) / np.sqrt(len(eo))
        s = g.errS.dropna(); r['biasS'] = s.mean(); r['sdS'] = s.std(ddof=1)
        n_ = g.errN.dropna(); r['sdN'] = n_.std(ddof=1)
        for c in ('w1', 'w2', 'tau', 'n', 'dbar', 'K', 'cut'):
            if c in g: r[c] = g[c].mean()
        rows.append(r)
    return pd.DataFrame(rows)


def save(name):
    plt.savefig(f'{FIG}/{name}.pdf'); plt.savefig(f'/tmp/view_{name}.png', dpi=110); plt.close()


# ---- theory (Proposition 2): population OLS slope on x for g(x), Bernoulli(p), degrees d_i
from scipy.stats import binom


def g_fun(mech, kappa=4.0, theta=0.7, steep=10.0):
    if mech in ('linfrac', 'hetero'): return lambda x: x
    if mech == 'sat': return lambda x: (1 - np.exp(-kappa * x)) / (1 - np.exp(-kappa))
    if mech == 'quad': return lambda x: x ** 2
    if mech == 'thresh':
        s = lambda t: 1 / (1 + np.exp(-steep * (t - theta)))
        return lambda x: (s(x) - s(0.0)) / (s(1.0) - s(0.0))
    raise ValueError(mech)


def slope_pred(mech, p, degs):
    """Pooled OLS slope on x of g(x) when x_i = Bin(d_i,p)/d_i (large-n limit, independent neighbours).
    degs: array of node degrees (or a scalar d). Returns predicted bias = slope - (g(1)-g(0))."""
    g = g_fun(mech)
    degs = np.atleast_1d(degs).astype(int)
    vals, cnt = np.unique(degs, return_counts=True)
    num = den = 0.0
    for d, c in zip(vals, cnt):
        k = np.arange(d + 1); pk = binom.pmf(k, d, p); x = k / d
        num += c * np.sum(pk * g(x) * (x - p)); den += c * np.sum(pk * (x - p) ** 2)
    return num / den - (g(1.0) - g(0.0))


def slope_limit(mech, p):
    g = g_fun(mech); h = 1e-5
    return (g(p + h) - g(p - h)) / (2 * h) - (g(1.0) - g(0.0))


def plain_log(ax, ticks, axis='y'):
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
    ax_ = ax.yaxis if axis == 'y' else ax.xaxis
    ax_.set_major_locator(FixedLocator(ticks)); ax_.set_major_formatter(FixedFormatter([f'{t:g}' for t in ticks])); ax_.set_minor_locator(NullLocator())
