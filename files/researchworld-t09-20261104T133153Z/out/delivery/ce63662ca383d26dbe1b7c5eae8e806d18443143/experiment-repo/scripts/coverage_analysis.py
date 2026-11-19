#!/usr/bin/env python3
"""Post-freeze analysis for experiment-repo#12: coverage of the GATE and of the estimator's own expectation E[tau-hat].
For each cell (e6 as run; e15: same graphs plus the Louvain block bootstrap and HAC-2 on Stanford3) and each interval type, from the raw per-replicate files:
  cov_gate   : P(|est - GATE| <= 1.96 se)                      (interval = est +- 1.96 se; bootstrap: percentile interval [boot_lo, boot_hi])
  cov_exp    : P(|est - m_w| <= 1.96 se), m_w = mean of est over the replicates of the same world (the bias is removed, only the variance estimator is judged);
               for the percentile interval: boot_lo <= m_w <= boot_hi
  n_rep      : replicates behind each coverage; world-level 95% t-interval (df = worlds-1) of the world coverages, the honest interval when worlds
               share a graph/baseline (the replicate-level binomial SE is also given).
-> results/tables/t19_coverage_expectation.csv (per cell), t19b_coverage_by_se_type.csv (mean over graphs, with a bootstrap over the cells)"""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import glob, os
import numpy as np, pandas as pd
from scipy import stats

R = results_dir()
SE = {"HC0": "se", "cluster": "se_cl", "HAC1": "se_hac1", "HAC2": "se_hac2", "boot_sd": "se_boot"}


def world_ci(x):
    """mean of the per-world values with a t interval over worlds"""
    m, k = x.mean(), len(x)
    h = stats.t.ppf(0.975, k - 1) * x.std(ddof=1) / np.sqrt(k) if k > 1 else np.nan
    return m, h


def cell_rows(df, exp):
    rows = []
    for (cell, est), d in df.groupby(["cell", "est_name"]):
        d = d.dropna(subset=["est"]).copy()
        d["m_w"] = d.groupby("world").est.transform("mean")
        base = dict(exp=exp, cell=cell, est_name=est, graph=d.graph.iloc[0], design=d.design.iloc[0], tag=d.tag.iloc[0], kind=d.o_kind.iloc[0], gamma=d.o_gamma.iloc[0],
                    n_worlds=d.world.nunique(), n_rep=len(d), bias=(d.est - d.gate).mean(), sd=(d.est - d.gate).std())
        for nm, col in SE.items():
            if col not in d or d[col].isna().any():
                continue
            ig = ((d.est - d.gate).abs() <= 1.96 * d[col]).astype(float)
            ie = ((d.est - d.m_w).abs() <= 1.96 * d[col]).astype(float)
            rows.append({**base, "interval": nm, "mean_se": d[col].mean(), **_cov(d, ig, ie)})
        if "boot_lo" in d and d.boot_lo.notna().all():
            ig = ((d.boot_lo <= d.gate) & (d.gate <= d.boot_hi)).astype(float)
            ie = ((d.boot_lo <= d.m_w) & (d.m_w <= d.boot_hi)).astype(float)
            rows.append({**base, "interval": "boot_pct", "mean_se": ((d.boot_hi - d.boot_lo) / 3.92).mean(), **_cov(d, ig, ie)})
    return rows


def _cov(d, ig, ie):
    wg, we = ig.groupby(d.world).mean(), ie.groupby(d.world).mean()
    cg, hg = world_ci(wg)
    ce, he = world_ci(we)
    return dict(cov_gate=ig.mean(), cov_gate_world_halfwidth=hg, cov_gate_binom_se=np.sqrt(ig.mean() * (1 - ig.mean()) / len(ig)),
                cov_exp=ie.mean(), cov_exp_world_halfwidth=he, cov_exp_binom_se=np.sqrt(ie.mean() * (1 - ie.mean()) / len(ie)))


def main():
    rows = []
    for exp in ("e6", "e15"):
        files = sorted(glob.glob(os.path.join(R, "raw", exp, "*.csv.gz")))
        if not files:
            continue
        df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
        rows += cell_rows(df[df.est_name.isin(["OLS_f", "ORACLE_D", "OLS_fd", "OLS_quad"])], exp)
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(R, "tables", "t19_coverage_expectation.csv"), index=False)
    print(len(T), "rows")
    # by interval type, OLS_f, Bernoulli(0.5) analysis res 1 (e6 'acl1.0', e15) and Louvain design cells, mean over graphs
    sel = T[(T.est_name == "OLS_f") & ((T.tag.str.endswith("acl1.0") & (T.exp == "e6")) | (T.exp == "e15"))].copy()
    sel["design_type"] = np.where(sel.design.str.startswith("bern"), "Bernoulli(0.5)", "Louvain clusters")
    out = []
    rng = np.random.default_rng(0)
    for (exp, dt, interval), g in sel.groupby(["exp", "design_type", "interval"]):
        for what in ("cov_gate", "cov_exp"):
            v = g[what].values
            bs = [rng.choice(v, len(v)).mean() for _ in range(2000)]
            out.append(dict(exp=exp, design=dt, interval=interval, quantity=what, n_cells=len(v), graphs=g.graph.nunique(), mean_coverage=v.mean(),
                            boot_lo=np.percentile(bs, 2.5), boot_hi=np.percentile(bs, 97.5), min=v.min(), max=v.max()))
    U = pd.DataFrame(out)
    U.to_csv(os.path.join(R, "tables", "t19b_coverage_by_se_type.csv"), index=False)
    pd.set_option("display.width", 250)
    print(U.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
