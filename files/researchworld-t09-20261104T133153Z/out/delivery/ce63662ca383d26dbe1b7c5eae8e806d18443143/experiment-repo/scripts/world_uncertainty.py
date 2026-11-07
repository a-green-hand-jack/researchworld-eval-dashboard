#!/usr/bin/env python3
"""Post-freeze analysis for experiment-repo#15(1,2): uncertainty with few worlds per cell.
(A) variance components of the error (est - GATE) of OLS_f, DM and ORACLE_D in the Bernoulli(0.5), gamma = 2 cells of e2 (4 worlds x 100) and e18 (20 worlds x 25):
    between-world variance of the world-mean error, within-world variance, ICC, the SE of the bias at replicate level (naive), at world level (SD of
    world means / sqrt(W)) and the t-interval half-width; the aggregate.py rule is max(replicate-level, world-level).
(B) how many worlds are needed: from the 20 worlds of e18, every subset of W worlds (W = 4, 6, 8, 12) gives a bias estimate and an SE (aggregate.py rule,
    and world-level only); we report the median SE against the SE implied by all 20 worlds and how often bias_W +- 2 SE_W (and +- t SE_W) contains the 20-world mean.
(C) hierarchical bootstrap (resample worlds, then replicates inside each world) intervals for the averaged headline numbers: SD(OLS_f)/SD(DM) per graph (e1, gamma = 0)
    and the max/min RMSE ratios of the factor ranking (t11).
-> results/tables/t20_variance_components.csv, t20b_worlds_needed.csv, t20c_headline_intervals.csv"""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import glob, itertools, os
import numpy as np, pandas as pd
from scipy import stats

R = results_dir(); T_ = os.path.join(R, "tables")
SBM = "sbm:5000,50,20,0.8"


def load(exp, cells=None, ests=None):
    out = []
    for f in sorted(glob.glob(os.path.join(R, "raw", exp, "*.csv.gz"))):
        c = int(os.path.basename(f).split(".")[0])
        if cells is not None and c not in cells:
            continue
        d = pd.read_csv(f, usecols=["world", "rep", "est_name", "gate", "est", "graph", "design", "o_kind", "o_gamma", "cell"])
        if ests is not None:
            d = d[d.est_name.isin(ests)]
        out.append(d)
    return pd.concat(out, ignore_index=True)


def components(d):
    d = d.dropna(subset=["est"]).assign(err=lambda x: x.est - x.gate)
    wm = d.groupby("world").err.mean()
    W, N = len(wm), len(d)
    k = N / W
    within = d.groupby("world").err.var(ddof=1).mean()
    sb2 = max(wm.var(ddof=1) - within / k, 0.0)
    se_rep, se_w = d.err.std() / np.sqrt(N), wm.std(ddof=1) / np.sqrt(W)
    return dict(n_worlds=W, reps_per_world=k, bias=d.err.mean(), var_within=within, var_between=sb2, icc=sb2 / (sb2 + within) if sb2 + within > 0 else np.nan,
                se_replicate=se_rep, se_world=se_w, se_aggregate_rule=max(se_rep, se_w), t_halfwidth=stats.t.ppf(0.975, W - 1) * se_w, design_effect=(se_w / se_rep) ** 2)


def part_a():
    from netgate.experiments import EXPERIMENTS
    c2 = [i for i, c in enumerate(EXPERIMENTS["e2"]()) if c["design"] == "bern:0.5"]
    rows = []
    for exp, cells in (("e2", set(c2)), ("e18", None)):
        d = load(exp, cells, ["OLS_f", "DM", "ORACLE_D", "OLS_zf"])
        if exp == "e2":
            d = d[d.o_kind.isin(["linear", "concave"])]
        for (cell, est), g in d.groupby(["cell", "est_name"]):
            rows.append(dict(exp=exp, cell=cell, est_name=est, graph=g.graph.iloc[0], kind=g.o_kind.iloc[0], **components(g)))
    A = pd.DataFrame(rows)
    A.to_csv(os.path.join(T_, "t20_variance_components.csv"), index=False)
    return A


def part_b():
    d = load("e18", None, ["OLS_f"])
    rows = []
    rng = np.random.default_rng(0)
    for cell, g in d.groupby("cell"):
        g = g.dropna(subset=["est"]).assign(err=lambda x: x.est - x.gate)
        st = g.groupby("world").err.agg(n="size", s="sum", ss=lambda x: (x ** 2).sum())
        n, s1, s2 = st.n.values.astype(float), st.s.values, st.ss.values
        nw = len(n); wm = s1 / n
        for W in (4, 6, 8, 12):
            subs = list(itertools.combinations(range(nw), W))
            if len(subs) > 4000:
                subs = [tuple(rng.choice(nw, W, replace=False)) for _ in range(4000)]
            for sub in subs:
                ix = np.array(sub); rest = np.setdiff1d(np.arange(nw), ix)
                N, m = n[ix].sum(), s1[ix].sum() / n[ix].sum()
                var = (s2[ix].sum() - N * m * m) / (N - 1)
                se_rep, se_w = np.sqrt(var / N), wm[ix].std(ddof=1) / np.sqrt(W)
                ref = s1[rest].sum() / n[rest].sum()           # the other 20 - W worlds: disjoint from the subset
                infl = np.sqrt(1 + W / (nw - W))                 # the reference has its own error: var(m - ref) = var(m) (1 + W / (20 - W)) if the SE is right
                rows.append(dict(cell=cell, graph=g.graph.iloc[0], W=W, bias=m, ref=ref, se_rule=max(se_rep, se_w), se_world=se_w, se_rep=se_rep, infl=infl))
    B = pd.DataFrame(rows)
    B["tcrit"] = stats.t.ppf(0.975, B.W - 1)
    for nm in ("rule", "world", "rep"):
        B["z_" + nm] = (B.bias - B.ref) / (B["se_" + nm] * B.infl)
    out = B.groupby("W").agg(n_cells=("cell", "nunique"), median_se_rule=("se_rule", "median"), median_se_world=("se_world", "median"), median_se_rep=("se_rep", "median"),
                             p10_se_world=("se_world", lambda x: x.quantile(.1)), p90_se_world=("se_world", lambda x: x.quantile(.9)),
                             p10_se_rep=("se_rep", lambda x: x.quantile(.1)), p90_se_rep=("se_rep", lambda x: x.quantile(.9))).reset_index()
    for nm in ("rule", "world", "rep"):
        out["cover_1.96_" + nm] = [(B[B.W == W]["z_" + nm].abs() <= 1.96).mean() for W in out.W]
        out["cover_t_" + nm] = [(B[B.W == W]["z_" + nm].abs() <= B[B.W == W].tcrit.iloc[0]).mean() for W in out.W]
    out.to_csv(os.path.join(T_, "t20b_worlds_needed.csv"), index=False)
    return out


def hboot_stat(d, stat, B=400, rng=None):
    """resample worlds with replacement, then replicates within each sampled world"""
    rng = rng or np.random.default_rng(1)
    worlds = {w: g for w, g in d.groupby("world")}
    ks = list(worlds)
    vals = []
    for _ in range(B):
        parts = []
        for w in rng.choice(ks, len(ks)):
            g = worlds[w]
            parts.append(g.iloc[rng.integers(0, len(g), len(g))])
        vals.append(stat(pd.concat(parts)))
    return np.array(vals)


def part_c():
    from netgate.experiments import EXPERIMENTS
    rows = []
    c1 = EXPERIMENTS["e1"]()
    for gs in dict.fromkeys(c["graph"] for c in c1):
        i = [i for i, c in enumerate(c1) if c["graph"] == gs and c["design"] == "bern:0.5" and c["outcome"]["gamma"] == 0.0][0]
        d = load("e1", {i}, ["OLS_f", "DM"])
        d = d.assign(err=d.est - d.gate)
        p = d.pivot_table(index=["world", "rep"], columns="est_name", values="err").reset_index()
        ratio = lambda x: x.OLS_f.std() / x.DM.std()
        bs = hboot_stat(p, ratio)
        rows.append(dict(quantity="SD(OLS_f)/SD(DM), e1 gamma=0 bern0.5", graph=gs, value=ratio(p), lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5),
                         note="hierarchical bootstrap: worlds then replicates, B=400"))
    C = pd.DataFrame(rows)
    rr = C[C.quantity.str.startswith("SD(")].value
    rows2 = [dict(quantity="range of SD ratios over the 6 graphs", graph="all", value=np.nan, lo=rr.min(), hi=rr.max(), note="min and max of the six point values (see rows above for their intervals)")]
    C = pd.concat([C, pd.DataFrame(rows2)], ignore_index=True)
    C.to_csv(os.path.join(T_, "t20c_headline_intervals.csv"), index=False)
    return C


if __name__ == "__main__":
    pd.set_option("display.width", 250, "display.max_columns", 30)
    A = part_a()
    print(A[A.est_name.isin(["OLS_f", "DM", "ORACLE_D"])].groupby(["exp", "est_name"])[["var_within", "var_between", "icc", "se_replicate", "se_world", "se_aggregate_rule", "t_halfwidth", "design_effect"]].median().round(4))
    print(part_b().round(4).to_string(index=False))
    print(part_c().round(3).to_string(index=False))
