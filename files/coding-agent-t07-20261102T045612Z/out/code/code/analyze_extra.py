"""Tables/figures for the coverage/unbiasedness experiment (raw_cover) and the ablations (raw_ablate)."""
import sys, os, glob, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze_lib import BENCH_LABEL
from analyze_main import BENCHES_ORDER
OUT_T = '/work/results/tables'; OUT_F = '/work/figs'


def cover():
    rows = []
    for f in sorted(glob.glob('/work/results/raw_cover/*.pkl')):
        b, reg, rep = os.path.basename(f)[:-4].rsplit('_', 2)
        d = pickle.load(open(f, 'rb'))
        for k, r in d['res'].items():
            E, SE = r['E'], r['SE']                      # M x T
            M = E['mean'].shape[0]
            for e in ['mean', 'cf', 'plugin', 'pirt']:
                err = E[e]
                bias_t = err.mean(0)                     # per target model
                sd_t = err.std(0, ddof=1)
                z = bias_t / (sd_t / np.sqrt(M) + 1e-12)  # z-score of the bias per target
                rmse = np.sqrt((err ** 2).mean())
                row = dict(bench=b, regime=reg, rep=int(rep), k=k, est=e, rmse=rmse * 100, bias=bias_t.mean() * 100,
                           mean_abs_bias=np.abs(bias_t).mean() * 100, frac_sig_bias=float((np.abs(z) > 3).mean()),
                           sd=np.sqrt((sd_t ** 2).mean()) * 100)
                if e in SE:
                    cov = (np.abs(err) <= 1.96 * SE[e]).mean()
                    row.update(coverage=cov, width=2 * 1.96 * SE[e].mean() * 100)
                rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv('/work/results/cover_rows.csv', index=False)
    g = df.groupby(['regime', 'k', 'est'])[['rmse', 'bias', 'mean_abs_bias', 'frac_sig_bias', 'sd', 'coverage', 'width']].mean()
    print(g.round(3).to_string())
    # bench-level CF/mean RMSE ratio
    piv = df.pivot_table(index=['regime', 'k', 'bench', 'rep'], columns='est', values='rmse').reset_index()
    piv['cf_ratio'] = piv['cf'] / piv['mean']; piv['pirt_ratio'] = piv['pirt'] / piv['mean']
    print(piv.groupby(['regime', 'k'])[['cf_ratio', 'pirt_ratio']].agg(lambda x: np.exp(np.log(x).mean())).round(3))
    g.reset_index().to_csv('/work/results/cover_summary.csv', index=False)
    with open(f'{OUT_T}/cover.tex', 'w') as fh:
        for reg in ['iid', 'up50']:
            for k in [25, 100]:
                for e, lab in [('mean', 'Random mean'), ('cf', 'CF'), ('plugin', 'cross-fit plug-in'), ('pirt', 'p-IRT')]:
                    r = g.loc[(reg, k, e)]
                    cov = f"{r.coverage*100:.1f}" if e in ('mean', 'cf') else '--'
                    wid = f"{r.width:.1f}" if e in ('mean', 'cf') else '--'
                    fh.write(f"{reg} & {k} & {lab} & {r.bias:+.2f} & {r.mean_abs_bias:.2f} & {r.frac_sig_bias*100:.0f}\\% & {r.rmse:.2f} & {cov} & {wid} \\\\\n")
    return df


def ablate():
    rows = []
    for f in sorted(glob.glob('/work/results/raw_ablate/*.pkl')):
        rows += pickle.load(open(f, 'rb'))
    df = pd.DataFrame(rows)
    for c in ['mae', 'rmse', 'bias']:
        df[c] *= 100
    df.to_csv('/work/results/ablate_rows.csv', index=False)
    out = {}
    for abl, g in df.groupby('abl'):
        piv = g.pivot_table(index=['regime', 'k', 'setting', 'bench', 'rep'], columns='est', values='rmse').reset_index()
        ests = [c for c in piv.columns if c not in ('regime', 'k', 'setting', 'bench', 'rep', 'mean')]
        # per-benchmark rep-averaged rel. RMSE vs random mean (same draws), geometric mean over benchmarks
        res = []
        for (reg, k, st), gg in piv.groupby(['regime', 'k', 'setting']):
            m = gg.groupby('bench')[ests + ['mean']].mean()
            rel = np.exp(np.log(m[ests].div(m['mean'], axis=0)).mean())
            sp = g[(g.regime == reg) & (g.k == k) & (g.setting == st)].groupby('est').spearman.mean()
            for e in ests:
                res.append(dict(regime=reg, k=k, setting=st, est=e, rel_rmse=rel[e], spearman=sp[e], spearman_mean=sp['mean']))
        out[abl] = pd.DataFrame(res)
        out[abl].to_csv(f'/work/results/ablate_{abl}.csv', index=False)
        print(abl); print(out[abl].round(3).to_string())
    return out


if __name__ == '__main__':
    if glob.glob('/work/results/raw_cover/*.pkl'): cover()
    if glob.glob('/work/results/raw_ablate/*.pkl'): ablate()
