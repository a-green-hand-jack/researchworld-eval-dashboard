"""Summaries of the xrun.py runs (X_<name>): nMSE with 95% CI, gap closed G (same-rule floor where the rule has a full-information partner run, best-rule
floor otherwise), paired contrasts against random and against gv_fa (model bootstrap and organisation / strict-family cluster bootstrap).
usage: python x_table.py <name> [<name> ...]      (X_<name>.parquet must exist)  ->  results/summary/xcurves_<name>.csv, xpaired_<name>.csv
"""
import os, sys, json
import numpy as np, pandas as pd
from analysis_lib import per_model, boot_metric, paired_diff, paired_diff_cl, gap_closed
from cluster_analysis import cluster_labels

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, '..', 'results', 'raw'); OUT = os.path.join(HERE, '..', 'results', 'summary')


def run(name, n_boot=1000):
    xj = json.load(open(os.path.join(RAW, f'X_{name}.json'))); base = xj['base_run']
    d = pd.read_parquet(os.path.join(RAW, f'X_{name}.parquet'))
    cfg = json.load(open(os.path.join(RAW, base + '.json')))
    b = pd.read_parquet(os.path.join(RAW, base + '.parquet'))
    # reference rows from the base run (same folds/targets): mean predictor and the static selectors already evaluated there
    ref = b[(b.method == 'mean') | (b.selector.isin(['dopt', 'central']) & b.method.isin(['fa', 'krr', 'ridge']))]
    ref = ref[ref.k.isin(d.k.unique()) | (ref.method == 'mean')]
    ref = ref.assign(selector=np.where(ref.method == 'mean', 'random', ref.selector))
    ref = ref[(ref.method != 'mean') | ref.k.isin(d.k.unique())]
    allr = pd.concat([d[['rep', 'fold', 'model', 'selector', 'method', 'k', 'n_t', 'sse_z', 'sse_pts', 'sae_pts']], ref[['rep', 'fold', 'model', 'selector', 'method', 'k', 'n_t', 'sse_z', 'sse_pts', 'sae_pts']].assign(selector=lambda x: np.where(x.method == 'mean', 'random', x.selector))])
    g = per_model(allr.fillna(0))
    gc = boot_metric(g[g.method != 'mean'], ['selector', 'method', 'k'], n_boot=n_boot).rename(columns={'est': 'nmse', 'lo': 'nmse_lo', 'hi': 'nmse_hi'})
    gc['source'] = np.where(gc.selector.isin(['dopt', 'central']), 'base_run', 'xrun')
    fname = base[2:] if base.startswith('B_') else base
    fp = os.path.join(RAW, 'F_' + fname + '.parquet')
    if os.path.exists(fp):
        gf = per_model(pd.read_parquet(fp))
        G, fl = gap_closed(g, gf, n_boot=n_boot)
        gc = gc.merge(G.drop(columns='nmse'), on=['selector', 'method', 'k'], how='left')
        fl.to_csv(os.path.join(OUT, f'xfloor_{name}.csv'), index=False)
    gc.insert(0, 'run', base)
    gc.to_csv(os.path.join(OUT, f'xcurves_{name}.csv'), index=False)
    # paired contrasts: every selector in X vs random (X's own draws) and vs gv_fa; org / family cluster bootstrap where labels exist
    ids, org, fam = cluster_labels(cfg['data'])
    labs = {'org': dict(enumerate(org)), 'family': dict(enumerate(fam))}
    gg = g[g.method != 'mean']
    rows = []
    for a in sorted(set(gg.selector)):
        for bb in ('random', 'gv_fa'):
            if a == bb or bb not in set(gg.selector):
                continue
            for cl in ('model', 'org', 'family'):
                p = paired_diff(gg, a, bb, n_boot=n_boot) if cl == 'model' else paired_diff_cl(gg, a, bb, labs[cl], n_boot=n_boot)
                p.insert(0, 'cluster', cl); p.insert(0, 'b', bb); p.insert(0, 'a', a); rows.append(p)
    pd.concat(rows).to_csv(os.path.join(OUT, f'xpaired_{name}.csv'), index=False)
    print(name, 'ok')


if __name__ == '__main__':
    for n in sys.argv[1:]:
        run(n)
