"""Influence descriptors of every claim pair of results/budgets_remove.csv at the base fit (second regressor next to z_gap).

For the claim pair (a, b) with contrast u (u.theta = theta_a - theta_b), removing one comparison in cell (p, o) changes the
gap by -g_po (linearised), g_po = (s_o - sigma_p) r_p, r = V H^-1 u. Over all N comparisons (cells weighted by count):
  infl_sd        = SD of g over comparisons (mean is ~0)          -> infl_snr = gap / infl_sd   (signal-to-noise of the influences)
  infl_top_mean  = mean of the k largest g, k = verified budget    -> infl_rho = infl_top_mean / infl_sd (influence-tail ratio)
  infl_pos_share = share of comparisons with g > 0
Writes results/s3_influence.csv. Usage: python code/s3_influence.py"""
import os

import numpy as np
import pandas as pd

from btlib import core, prov
from s1_run import build

OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def main():
    d = pd.read_csv(f"{OUT}/budgets_remove.csv")
    rows = []
    for unit, g in d.groupby("unit", sort=False):
        u = build(unit)
        c = u.c
        names = {n: i for i, n in enumerate(c.names)}
        xh, H = core.fit(c, u.lam, u.lam_h, theta0=u.x0, return_hess=True)
        Hinv_cache = {}
        for _, r in g.iterrows():
            a, b = names[r.a], names[r.b]
            cv = core.claim_vec(c, a, b)
            G = core.gains(c, xh, H, cv, "remove")
            w = c.n.ravel()
            x = np.where(w > 0, G.ravel(), 0.0)
            m = np.average(x, weights=w)
            sd = float(np.sqrt(np.average((x - m) ** 2, weights=w)))
            k = r.budget
            if np.isfinite(k) and k >= 1:
                o = np.argsort(-x)
                cum = np.cumsum(w[o])
                take = np.minimum(w[o], np.clip(k - (cum - w[o]), 0, None))
                top = float((x[o] * take).sum() / take.sum())
            else:
                top = np.nan
            rows.append(dict(unit=unit, claim=r.claim, infl_mean=m, infl_sd=sd, infl_snr=r.gap / sd if sd > 0 else np.nan,
                             infl_top_mean=top, infl_rho=top / sd if sd > 0 else np.nan, infl_pos_share=float(w[x > 0].sum() / w.sum())))
    pd.DataFrame(rows).to_csv(f"{OUT}/s3_influence.csv", index=False, float_format="%.6g")
    prov.write_meta(f"{OUT}/s3_influence.meta.json", script="code/s3_influence.py")


if __name__ == "__main__":
    main()
