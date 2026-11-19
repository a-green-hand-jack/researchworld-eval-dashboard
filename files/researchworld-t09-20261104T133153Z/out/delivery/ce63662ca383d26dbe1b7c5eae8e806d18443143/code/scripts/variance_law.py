#!/usr/bin/env python3
"""Post-freeze analysis for experiment-repo#10(a): is the SD of OLS_f ordered by the harmonic-mean degree d_h?
Prediction (linear exposure model, independent errors, Bernoulli(p)): Var(tau_hat) ~ sigma_r^2 (1 + d_h) / (n p (1-p)),
d_h = 1 / mean(1/deg) on the largest component. sigma_r^2 is taken as Var(baseline + noise) of the simulated worlds (z-independent, and the residual
variance of the true model at gamma = 0), averaged over the worlds of the cell (the graph and baselines are rebuilt with the seeds the cell used).
Inputs: results/summary/e1.csv (gamma = 0 .. 4, Bernoulli(0.5), OLS_f; for the linear truth the SD does not depend on gamma, so the five SDs are also pooled) and e3.csv (ER, BA).
Outputs: results/tables/t17_variance_law.csv (six graphs), t17b_variance_law_e3.csv (ER n x d, BA n x m)."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import os
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from netgate.experiments import EXPERIMENTS
from netgate.outcomes import Outcome
from netgate.runner import get_graph

R = results_dir(); S = lambda e: pd.read_csv(os.path.join(R, "summary", f"{e}.csv"))


def world_stats(cfg):
    """n, mean degree, harmonic-mean degree, sigma_r^2 averaged over the worlds of a cell (same seeds as run_cell)."""
    o = Outcome(**cfg["outcome"]); rows = []
    for w in range(cfg["worlds"]):
        seed = cfg["seed"] * 1000 + w
        rng = np.random.default_rng(seed); g = get_graph(cfg["graph"], seed)
        wd = o.world(g, rng)
        rows.append((g.n, g.mean_deg, 1 / np.mean(1 / g.deg), np.var(wd["base"] + wd["eps"])))
    return np.mean(rows, axis=0)


def predicted_sd(sig2, n, dd, p=0.5):
    return np.sqrt(sig2 * (1 + dd) / (n * p * (1 - p)))


def main():
    e1, e3 = S("e1"), S("e3")
    cells = EXPERIMENTS["e1"]()
    rows = []
    for gs in dict.fromkeys(c["graph"] for c in cells):
        pick = [c for c in cells if c["graph"] == gs and c["design"] == "bern:0.5" and c["outcome"]["gamma"] == 0.0][0]
        n, d, dh, sig2 = world_stats(pick)
        sub = e1[(e1.graph == gs) & (e1.design == "bern:0.5") & (e1.est_name == "OLS_f")]
        sd0 = sub[sub.o_gamma == 0.0].sd.iloc[0]
        sdp = float(np.sqrt((sub.sd ** 2).mean()))
        rows.append(dict(graph=gs, n=n, mean_deg=d, d_harm=dh, sigma_r2=sig2, sd_obs_gamma0=sd0, sd_obs_pooled_gammas=sdp,
                         sd_pred_dh=predicted_sd(sig2, n, dh), sd_pred_d=predicted_sd(sig2, n, d)))
    T = pd.DataFrame(rows)
    T["ratio_obs_over_pred_dh"] = T.sd_obs_pooled_gammas / T.sd_pred_dh
    T["ratio_obs_over_pred_d"] = T.sd_obs_pooled_gammas / T.sd_pred_d
    er = T[T.graph.str.startswith("er")].iloc[0]
    T["ratio_dh_relative_to_ER"] = T.ratio_obs_over_pred_dh / er.ratio_obs_over_pred_dh
    T["ratio_d_relative_to_ER"] = T.ratio_obs_over_pred_d / er.ratio_obs_over_pred_d
    T.to_csv(os.path.join(R, "tables", "t17_variance_law.csv"), index=False)
    pd.set_option("display.width", 250)
    print(T.round(4).to_string(index=False))
    for nm in ("dh", "d"):
        r = np.corrcoef(np.log(T["sd_pred_" + nm]), np.log(T.sd_obs_pooled_gammas))[0, 1]
        print(f"six graphs: corr(log pred[{nm}], log obs) = {r:.3f}; Spearman = {spearmanr(T['sd_pred_' + nm], T.sd_obs_pooled_gammas)[0]:.2f}; "
              f"max/min of obs/pred = {T['ratio_obs_over_pred_' + nm].max() / T['ratio_obs_over_pred_' + nm].min():.2f}")
    # e3: Bernoulli(0.5) ER (n x d) and BA (n x m), linear gamma = 1
    cells3 = EXPERIMENTS["e3"]()
    rows = []
    for i, c in enumerate(cells3):
        if not (c["graph"].startswith("er:") or c["graph"].startswith("ba:")):
            continue
        n, d, dh, sig2 = world_stats(c)
        r = e3[(e3.graph == c["graph"]) & (e3.design == "bern:0.5") & (e3.est_name == "OLS_f")].iloc[0]
        rows.append(dict(graph=c["graph"], n=n, mean_deg=d, d_harm=dh, sigma_r2=sig2, sd_obs=r.sd, sd_pred_dh=predicted_sd(sig2, n, dh), sd_pred_d=predicted_sd(sig2, n, d)))
    U = pd.DataFrame(rows)
    for nm in ("dh", "d"):
        U["ratio_" + nm] = U.sd_obs / U["sd_pred_" + nm]
    U.to_csv(os.path.join(R, "tables", "t17b_variance_law_e3.csv"), index=False)
    for fam in ("er", "ba"):
        V = U[U.graph.str.startswith(fam)]
        for nm in ("dh", "d"):
            lr = np.log(V["ratio_" + nm])
            print(f"e3 {fam}: {len(V)} cells; obs/pred[{nm}] mean {np.exp(lr.mean()):.3f}, range {np.exp(lr.min()):.3f}-{np.exp(lr.max()):.3f}, "
                  f"log-sd {lr.std():.3f}; corr(log pred, log obs) = {np.corrcoef(np.log(V['sd_pred_' + nm]), np.log(V.sd_obs))[0, 1]:.3f}")
    # e21: which baseline component breaks the independent-error law? same prediction with sigma_r^2 of each variant
    e21, c21 = S("e21"), EXPERIMENTS["e21"]()
    rows = []
    for i, c in enumerate(c21):
        n, d, dh, sig2 = world_stats(c)
        r = e21[(e21.cell == i) & (e21.est_name == "OLS_f")].iloc[0]
        rows.append(dict(graph=c["graph"], variant=c["tag"].split("|")[1], n=n, mean_deg=d, d_harm=dh, sigma_r2=sig2, sd_obs=r.sd,
                         sd_pred_dh=predicted_sd(sig2, n, dh), sd_pred_d=predicted_sd(sig2, n, d)))
    V = pd.DataFrame(rows)
    V["ratio_dh"] = V.sd_obs / V.sd_pred_dh; V["ratio_d"] = V.sd_obs / V.sd_pred_d
    V.to_csv(os.path.join(R, "tables", "t17c_variance_law_components.csv"), index=False)
    for v, g in V.groupby("variant"):
        print(f"e21 {v:13s}: obs/pred[d_h] by graph = {dict(zip(g.graph.str.split(':').str[0], g.ratio_dh.round(2)))}; max/min {g.ratio_dh.max() / g.ratio_dh.min():.2f}"
              f" | obs/pred[d] max/min {g.ratio_d.max() / g.ratio_d.min():.2f}")
    allr = {nm: np.log(U["ratio_" + nm]) for nm in ("dh", "d")}
    print("e3 ER+BA pooled log-ratio sd: d_h %.3f, d %.3f" % (allr["dh"].std(), allr["d"].std()))


if __name__ == "__main__":
    main()
