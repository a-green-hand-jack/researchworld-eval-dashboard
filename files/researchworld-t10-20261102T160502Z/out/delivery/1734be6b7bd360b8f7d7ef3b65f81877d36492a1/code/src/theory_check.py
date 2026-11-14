"""Predicted vs observed width ratio (M4 candidates / M3 and / unclipped PPI++) on the synthetic grid.

Prediction = sqrt(V_floor / V_ref) from src/theory.py v_pred with population moments of the synthetic law
(4e6-draw Monte Carlo; E[Y|f] by 400 quantile bins => negligible overfit).  No cost for learning g is included, so
observed ratios are expected to exceed predictions by an O(df/n) amount.
usage: python src/theory_check.py <space>
"""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import data as D
from theory import v_pred


def synth_pop_stats(kind, kappa, snr, M=4_000_000, nb=400):
    s, th, _ = D.synth_sampler(kind, kappa, snr)
    y, f = s(np.random.default_rng(777), M)
    edges = np.quantile(f, np.linspace(0, 1, nb + 1)[1:-1]); idx = np.searchsorted(edges, f)
    g = (np.bincount(idx, y) / np.bincount(idx))[idx]
    s2, v = y.var(), f.var(); C = np.cov(y, f, bias=True)[0, 1]
    return dict(sigma2=s2, var_f=v, cov_yf=C, rho2=C ** 2 / (s2 * v), r2cal=g.var() / s2)


if __name__ == "__main__":
    space = sys.argv[1] if len(sys.argv) > 1 else "final"
    sm = pd.read_csv(f"results/summary_{space}_synth.csv")
    cache, rows = {}, []
    for pop, g0 in sm.groupby("population"):
        _, kind, kappa, snr, tail = pop.split(":")
        key = (kind, kappa, snr)
        cache.setdefault(key, synth_pop_stats(kind, float(kappa), float(snr)))
        st = cache[key]
        for (n, N, tag), g in g0.groupby(["n", "N", "tag"]):
            V = v_pred(st["sigma2"], st["rho2"], st["r2cal"], st["cov_yf"], st["var_f"], n, N)
            for me in ["cal_iso", "cal_bin", "cal_spl", "cal_lin"]:
                r = g[g.method == me].iloc[0]
                rows.append(dict(population=pop, kind=kind, kappa=float(kappa), snr=float(snr), tail=int(tail), n=n, N=N, tag=tag,
                                 omega=N / (n + N), method=me, pred_ratio_vs_M3=np.sqrt(V["V_floor"] / V["V_M3"]),
                                 pred_ratio_vs_nc=np.sqrt(V["V_floor"] / V["V_nc"]), obs_ratio_vs_M3=r.ratio_M3_geo,
                                 obs_lo_M3=r.ratio_M3_lo, obs_hi_M3=r.ratio_M3_hi, obs_ratio_vs_nc=r.ratio_nc_geo,
                                 obs_lo_nc=r.ratio_nc_lo, obs_hi_nc=r.ratio_nc_hi, rho2=st["rho2"], r2cal=st["r2cal"]))
    df = pd.DataFrame(rows); df.to_csv(f"results/theory_check_synth_{space}.csv", index=False)
    d = df[df.method == "cal_spl"]
    print(d[["population", "n", "N", "tag", "pred_ratio_vs_M3", "obs_ratio_vs_M3", "pred_ratio_vs_nc", "obs_ratio_vs_nc"]].round(3).to_string())
