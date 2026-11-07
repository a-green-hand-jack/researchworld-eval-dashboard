#!/usr/bin/env python3
"""Closed-form large-n bias of the linear exposure regression OLS_f (Y ~ 1 + z + f1) under Bernoulli(p),
noiseless shape-h spillover, compared with the simulated noiseless bias from experiment e9.

Under Bernoulli(p) own treatment z_i is independent of f_i = Bin(d_i, p)/d_i, so the coefficient on z is tau and the
coefficient on f1 is the pooled least-squares slope s = Cov(h(f), f) / Var(f) over the node mixture (weights n_d / n).
OLS_f predicts tau + s for the GATE (f moves 0->1), the truth is tau + gamma*(h(1)-h(0)) => bias = gamma*(s - 1).
Large-degree limit: f -> p, s -> h'(p)  =>  bias ~ gamma*(1 - ... ) = gamma*(h'(p) - 1)."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import os, sys
import numpy as np, pandas as pd
from scipy.stats import binom
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from netgate import graphs
from netgate.experiments import ALL_G
from netgate.outcomes import Outcome, shape_deriv

ROOT = results_dir()


def slope(deg, p, h):
    d_vals, cnt = np.unique(deg.astype(int), return_counts=True)
    w = cnt / cnt.sum()
    Ef = Ef2 = Eh = Efh = 0.0
    for d, wi in zip(d_vals, w):
        k = np.arange(d + 1)
        pm = binom.pmf(k, d, p)
        f = k / d
        hv = h(f)
        Ef += wi * (pm * f).sum(); Ef2 += wi * (pm * f * f).sum()
        Eh += wi * (pm * hv).sum(); Efh += wi * (pm * f * hv).sum()
    return (Efh - Ef * Eh) / (Ef2 - Ef * Ef)


def predict(g, kind, curv, p, gamma=2.0):
    o = Outcome(kind=kind, curv=curv, gamma=gamma)
    s = slope(g.deg, p, o._h)
    return gamma * (s - 1), gamma * (float(shape_deriv(np.array([p]), kind)[0]) - 1) if curv is None else \
        gamma * (float((o._h(np.array([p + 1e-5])) - o._h(np.array([p - 1e-5])))[0] / 2e-5) - 1)


if __name__ == "__main__":
    S = pd.read_csv(os.path.join(ROOT, "summary", "e9.csv"))
    S = S[S.est_name == "OLS_f"].copy()
    rows = []
    cache = {}
    for _, r in S.iterrows():
        key = r.graph
        if key not in cache:
            cache[key] = graphs.make(r.graph, seed=0)  # degree sequence of a representative world (synthetic graphs: seed 0 of the family)
        pb, pb_inf = predict(cache[key], r.o_kind, r.o_curv, float(r.design.split(":")[1]))
        rows.append({**r[["graph", "o_kind", "o_curv", "design", "bias", "bias_se"]].to_dict(), "pred_exact": pb, "pred_largedeg": pb_inf})
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(ROOT, "summary", "theory_vs_sim_e9.csv"), index=False)
    print(T.groupby(["graph", "o_kind"]).apply(lambda d: pd.Series({"corr": np.corrcoef(d.bias, d.pred_exact)[0, 1],
          "mae_exact": (d.bias - d.pred_exact).abs().mean(), "mae_largedeg": (d.bias - d.pred_largedeg).abs().mean()}), include_groups=False))
