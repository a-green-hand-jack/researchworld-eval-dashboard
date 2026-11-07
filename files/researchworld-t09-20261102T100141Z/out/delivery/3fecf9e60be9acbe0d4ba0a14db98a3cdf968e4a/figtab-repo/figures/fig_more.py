"""Graph families (E5_graphs), model class (E7_model), noise (E9_noise) and the check of the closed-form predictions
(theory_check_*.csv). Usage: python3 fig_more.py [name ...]  (names: graphs, model, noise, theory; default all).
Inputs: results/replicates.parquet, results/theory_check_{bias,var}.csv. Metrics as in common.py."""
import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import common as C
import re
from fig_sweeps import data, err, legend, logticks, theory_sd, _curv, CURV, CURV_ORDER

C.setup_style()
W = C.TEXTWIDTH


def fig_graphs():
    """Fig. 14 (RQ3, H5): ten graph families, linear exposure (M1), Bernoulli(0.5), n=4000 (real graphs: 3000-node subsample, see Table 1).
    (a) rel. RMSE of difference in means / OLS(z,f) / degree-interacted OLS, (b) coverage of the nominal-95% cluster-robust CI of OLS(z,f)."""
    d = data("E5_graphs")
    agg = C.aggregate(d, ["tag", "estimator"])
    order = ["er_", "ba_", "geo_", "ws_0.1", "ws_0.5", "sbm_0.02", "sbm_0.1", "sbm_0.4", "fb_ego", "fb_stanford"]
    lab = ["ER", "BA", "geometric", "WS β=.1", "WS β=.5", "SBM μ=.02", "SBM μ=.1", "SBM μ=.4", "ego-FB", "Stanford3"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(W, 2.5), gridspec_kw=dict(width_ratios=[1.6, 1]))
    ests = ["dm", "ols_f", "ols_f_deg", "ols_poly"]
    for j, e in enumerate(ests):
        st = C.EST_STYLE[e]
        r = agg[agg.estimator == e].set_index("tag").reindex(order)
        x = np.arange(len(order)) + (j - 1.5) * 0.15
        a.errorbar(x, r.rel_rmse, yerr=[(r.rel_rmse - r.rel_rmse_lo).clip(lower=0), (r.rel_rmse_hi - r.rel_rmse).clip(lower=0)],
                   fmt=st["marker"], color=st["color"], ms=3.2, lw=0.7, capsize=0, label=st["label"])
    a.set_yscale("log"); logticks(a, [0.1, 0.2, 0.5, 1])
    a.set_xticks(range(len(order))); a.set_xticklabels(lab, rotation=40, ha="right", fontsize=6); a.grid(axis="x", visible=False)
    a.set_ylabel("rel. RMSE"); a.set_title("(a) accuracy", fontsize=7.5)
    r = agg[agg.estimator == "ols_f"].set_index("tag").reindex(order)
    b.errorbar(np.arange(len(order)), r.coverage, yerr=1.96 * r.cov_se, fmt="o", color=C.EST_STYLE["ols_f"]["color"], ms=3.2, lw=0.8, capsize=0)
    b.axhline(0.95, color="#555", lw=0.7, ls=":")
    b.set_xticks(range(len(order))); b.set_xticklabels(lab, rotation=40, ha="right", fontsize=6); b.grid(axis="x", visible=False)
    b.set_ylim(0.7, 1.0); b.set_ylabel("coverage of 95% CI"); b.set_title("(b) OLS(z,f) CI coverage", fontsize=7.5)
    legend(fig, a, ncol=4, rows=1)
    print("E5 R (min over plotted):", int(agg[agg.estimator.isin(ests)].R.min()))
    C.save(fig, "fig14_graph_families")
    print(agg[agg.estimator == "ols_f"].set_index("tag").reindex(order)[["rel_rmse", "bias", "coverage"]].round(3).to_string())


def fig_model():
    """Fig. 15 (RQ2/H2): model class (E7), SBM n=3000 Bernoulli(0.5): OLS(z,f), quadratic and cubic OLS, ridge on rich features, gradient boosting;
    three exposure responses (linear, convex f^2, threshold at 0.5), mean degree 10 (open) and 40 (filled). Top: rel. RMSE, bottom: bias."""
    d = data("E7_model")
    t = d.tag.str.extract(r"(lin_frac|pow2\.0|thresh)_d(\d+)")
    d["resp"], d["deg"] = t[0], t[1].astype(int)
    agg = C.aggregate(d, ["resp", "deg", "estimator"])
    resp = [("lin_frac", "linear in fraction"), ("pow2.0", r"convex $f^2$"), ("thresh", "threshold at 0.5")]
    ests = ["ols_f", "ols_poly", "ols_poly3", "ridge_rich", "gbm"]
    fig, axes = plt.subplots(2, 3, figsize=(W, 3.2), sharex=True)
    for j, (k, lab) in enumerate(resp):
        for i, e in enumerate(ests):
            st = C.EST_STYLE[e]
            for dg, fill, off in ((10, False, -0.08), (40, True, 0.08)):
                r = agg[(agg.resp == k) & (agg.deg == dg) & (agg.estimator == e)]
                if r.empty:
                    continue
                r = r.iloc[0]
                for ax, key in ((axes[0, j], "rel_rmse"), (axes[1, j], "bias")):
                    ax.errorbar(i + off, r[key], yerr=[[max(r[key] - r[key + "_lo"], 0)], [max(r[key + "_hi"] - r[key], 0)]], fmt=st["marker"],
                                color=st["color"], mfc=st["color"] if fill else "white", ms=3.5, lw=0.7, capsize=0)
        axes[0, j].set_yscale("log"); logticks(axes[0, j], [0.1, 0.2, 0.5, 1, 2])
        axes[1, j].axhline(0, color="#999", lw=0.6)
        axes[0, j].set_title(lab, fontsize=7.5)
        axes[1, j].set_xticks(range(len(ests))); axes[1, j].set_xticklabels(["OLS", "quad.", "cubic", "ridge", "GBM"], fontsize=6)
    axes[0, 0].set_ylabel("rel. RMSE"); axes[1, 0].set_ylabel(r"bias / $|\tau|$")
    for ax in axes.flat:
        ax.grid(axis="x", visible=False)
    h = [Line2D([], [], color="#777", marker="o", mfc="w", ls="", ms=3.5, label="mean degree 10 (open)"), Line2D([], [], color="#777", marker="o", ls="", ms=3.5, label="mean degree 40 (filled)")]
    h = [Line2D([], [], color=C.EST_STYLE[e]["color"], marker=C.EST_STYLE[e]["marker"], ls="", ms=3.5, label=n)
         for e, s, n in zip(ests, ("OLS", "quad.", "cubic", "ridge", "GBM"), ("OLS(z, f)", "quadratic OLS", "cubic OLS", "ridge, rich features", "gradient boosting"))] + h
    fig.tight_layout(rect=(0, 0.17, 1, 1))
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, fontsize=6.5, columnspacing=0.8, handletextpad=0.2)
    print("E7 R (min):", int(agg.R.min()))
    C.save(fig, "fig15_model_class")


def fig_noise():
    """Fig. 16 (appendix): noise sensitivity (E9), SBM d=20 n=3000, linear exposure. rel. RMSE vs idiosyncratic noise sigma_e,
    one panel per cluster-level noise sigma_c; covariate-adjusted OLS included."""
    d = data("E9_noise")
    t = d.tag.str.extract(r"sigE([\d.]+)_sigC([\d.]+)")
    d["se"], d["sc"] = t[0].astype(float), t[1].astype(float)
    agg = C.aggregate(d, ["se", "sc", "estimator"])
    ests = [e for e in ("dm", "ols_f", "ols_f_adj", "ols_f_deg", "ols_poly") if e in set(agg.estimator)]
    scs = sorted(agg.sc.unique())
    fig, axes = plt.subplots(1, len(scs), figsize=(W, 2.1), sharey=True)
    ses = sorted(agg.se.unique())
    for ax, sc in zip(axes, scs):
        for e in ests:
            st = C.EST_STYLE[e]
            r = agg[(agg.sc == sc) & (agg.estimator == e)].sort_values("se")
            err(ax, [ses.index(v) for v in r.se], r, "rel_rmse", st, label=st["label"])
        ax.set_yscale("log"); logticks(ax, [0.1, 0.2, 0.5, 1])
        ax.set_xticks(range(len(ses))); ax.set_xticklabels([f"{v:g}" for v in ses])
        ax.set_xlabel(r"idiosyncratic noise $\sigma_e$"); ax.set_title(rf"cluster noise $\sigma_c={sc:g}$", fontsize=7.5)
    axes[0].set_ylabel("rel. RMSE")
    legend(fig, axes[0], ncol=3, rows=2)
    print("E9 R (min):", int(agg[agg.estimator.isin(ests)].R.min()))
    C.save(fig, "fig16_noise")


def fig_theory():
    """Fig. 17: closed-form predictions (code/docs/THEORY.md) against simulation. (a) P2: empirical SD of OLS(z,f) vs predicted sandwich SD,
    one point per graph draw (colour = experiment). (b) P1/P3: population bias of OLS(z,f) vs predicted bias, one point per graph draw."""
    v = pd.read_csv(os.path.join(C.RESULTS, "theory_check_var.csv"))
    b = pd.read_csv(os.path.join(C.RESULTS, "theory_check_bias.csv"))
    fig, (a, c) = plt.subplots(1, 2, figsize=(W, 2.5))
    cols = dict(zip(sorted(v.exp.unique()), plt.cm.tab10.colors))
    for e, g in v.groupby("exp"):
        a.plot(g.th_sd, g.emp_sd, ls="", marker="o", ms=2.2, alpha=0.7, color=cols[e], label=e)
    lim = [v[["th_sd", "emp_sd"]].min().min() * 0.8, v[["th_sd", "emp_sd"]].max().max() * 1.25]
    a.plot(lim, lim, color="#888", lw=0.6)
    a.set(xscale="log", yscale="log", xlim=lim, ylim=lim, xlabel="predicted SD (P2)", ylabel="empirical SD over assignments")
    a.set_title(f"(a) variance, {len(v)} graph draws; median ratio {v.ratio.median():.3f}", fontsize=7)
    a.legend(frameon=False, fontsize=6, loc="lower right", ncol=2, handletextpad=0.2, columnspacing=0.6)
    lab = {("pow", "P1"): "E4 power $f^q$ (P1)", ("thresh", "P1"): "E4 threshold (P1)", ("lin_frac", "P1"): "MAIN M1 (P1)",
           ("sat", "P1"): "MAIN M3 saturating (P1)", ("lin_frac", "P3"): "MAIN M1 + het. (P3)", ("lin_2hop", "P3"): "MAIN M4 2-hop (P3)"}
    mk = dict(zip(lab, "osD^v<"))
    for i, ((k, f), g) in enumerate(b.groupby(["kind", "formula"])):
        c.plot(g.th_pop_bias, g.emp_pop_bias, ls="", marker=mk[(k, f)], ms=2.6, alpha=0.7, color=plt.cm.Dark2.colors[i], label=lab[(k, f)])
    lim = [b[["th_pop_bias", "emp_pop_bias"]].min().min() - 0.1, b[["th_pop_bias", "emp_pop_bias"]].max().max() + 0.1]
    c.plot(lim, lim, color="#888", lw=0.6)
    c.set(xlim=lim, ylim=lim, xlabel="predicted population bias (outcome units)", ylabel="population-fit bias (outcome units)")
    c.set_title(f"(b) bias, {len(b)} graph draws; max |diff| {np.abs(b.emp_pop_bias - b.th_pop_bias).max():.2f}", fontsize=7)
    c.legend(frameon=False, fontsize=6, loc="upper left")
    fig.tight_layout()
    print("theory: var ratio IQR", v.ratio.quantile([.25, .5, .75]).round(3).tolist(), " bias corr", float(np.corrcoef(b.th_pop_bias, b.emp_pop_bias)[0, 1]))
    C.save(fig, "fig17_theory_check")


def fig_curv_bias():
    """Fig. 9b (H2/H3): finite-sample bias vs the population-fit bias. E4_curv, mean degree 40, n=3000: observed bias of OLS(z,f), quadratic and cubic OLS
    (points, bootstrap 95% CI over replicates) against the noise-free population fit of the same estimator (dashed line)."""
    o, p = data("E4_curv"), data("E4_curv", "population")
    out = []
    for d in (o, p):
        d[["kind", "deg", "p"]] = d.tag.apply(lambda t: pd.Series(_curv(t)))
        out.append(C.aggregate(d[(d.deg == 40) & d.estimator.isin(["ols_f", "ols_poly", "ols_poly3"])], ["kind", "p", "estimator"]))
    ao, ap = out
    kinds = [k for k in CURV_ORDER if k in set(ao.kind) and k != "powq1.0"]
    fig, axes = plt.subplots(2, 3, figsize=(W, 3.6), sharex=True)
    for ax, k in zip(axes.flat, kinds):
        for e in ("ols_f", "ols_poly", "ols_poly3"):
            st = C.EST_STYLE[e]
            r, q = ao[(ao.kind == k) & (ao.estimator == e)].sort_values("p"), ap[(ap.kind == k) & (ap.estimator == e)].sort_values("p")
            ax.plot(q.p, q.bias, "--", color=st["color"], lw=0.8)
            err(ax, r.p, r, "bias", st, ls="", label=st["label"])
        ax.axhline(0, color="#999", lw=0.6)
        ax.set_yscale("symlog", linthresh=1, linscale=0.8)
        ax.set_title(CURV[k], fontsize=7.5)
    for ax in axes[1]:
        ax.set_xlabel("design p")
    for ax in axes[:, 0]:
        ax.set_ylabel(r"bias / $|\tau|$ (symlog)")
    for ax in axes.flat[len(kinds):]:
        ax.axis("off")
    fig.tight_layout()
    h, l = axes[0, 0].get_legend_handles_labels()
    h.append(Line2D([], [], color="#555", ls="--", lw=0.8)); l.append("population fit (dashed)")
    axes.flat[-1].legend(h, l, loc="center", frameon=False, fontsize=6.5)
    C.save(fig, "fig9b_curvature_bias_observed")
    m = ao.merge(ap, on=["kind", "p", "estimator"], suffixes=("_obs", "_pop"))
    print("observed - population bias: max |diff| by estimator\n", (m.bias_obs - m.bias_pop).abs().groupby(m.estimator).max().round(3).to_string())


def fig_spec_bias():
    """Fig. 11b (H2): signed relative bias of every feature set (rows) for five forms of interference (columns), per graph (SBM, ER, BA; E6_spec, d=20, n~3000).
    Cell text: bias / |tau|; bold = 95% bootstrap CI over replicates excludes 0."""
    d = data("E6_spec")
    t = d.tag.str.extract(r"(\w+?)_d(\d+)_(.+)")
    d["gname"], d["kind"] = t[0], t[2]
    agg = C.aggregate(d, ["gname", "kind", "estimator"])
    kinds = [("lin_frac", "lin. frac."), ("lin_count", "lin. count"), ("lin_2hop", "+2-hop"), ("het", "het. mild"), ("het_big", "het. strong")]
    ests = [e for e in ("dm", "ols_f", "ols_cnt", "ols_f_both", "ols_f_deg", "ols_f2", "ols_poly", "ols_f_adj", "ols_cnt_adj") if e in set(agg.estimator)]
    gs = [("sbm", "SBM"), ("er", "ER"), ("ba", "BA")]
    fig, axes = plt.subplots(1, 3, figsize=(W, 2.9), sharey=True)
    for ax, (g, gl) in zip(axes, gs):
        M = np.full((len(ests), len(kinds)), np.nan); sig = np.zeros_like(M, bool)
        for i, e in enumerate(ests):
            for j, (k, _) in enumerate(kinds):
                r = agg[(agg.gname == g) & (agg.kind == k) & (agg.estimator == e)]
                if len(r):
                    r = r.iloc[0]; M[i, j] = r.bias; sig[i, j] = (r.bias_lo > 0) or (r.bias_hi < 0)
        ax.imshow(M, cmap="RdBu_r", vmin=-0.6, vmax=0.6, aspect="auto")
        for i in range(len(ests)):
            for j in range(len(kinds)):
                if np.isfinite(M[i, j]):
                    ax.text(j, i, f"{M[i, j]:+.2f}", ha="center", va="center", fontsize=6, fontweight="bold" if sig[i, j] else "normal",
                            color="w" if abs(M[i, j]) > 0.4 else "k")
        ax.set_xticks(range(len(kinds))); ax.set_xticklabels([x[1] for x in kinds], rotation=50, ha="right", fontsize=6)
        ax.set_yticks(range(len(ests))); ax.set_yticklabels([C.EST_STYLE[e]["label"] for e in ests], fontsize=6)
        ax.set_title(gl, fontsize=7.5); ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
    fig.tight_layout()
    C.save(fig, "fig11b_specification_bias")
    print("E6 bias heat map: |bias|<=0.05 cells (non-DM):", int((np.abs(agg[agg.estimator != "dm"].bias) <= 0.05).sum()), "of", int((agg.estimator != "dm").sum()))


def fig_main():
    """Fig. M (main text): rel. RMSE of DM and the OLS estimators vs sample size n (E1), interference ratio rho (E3) and mean degree (E2, SBM),
    with the closed-form P2 prediction of the OLS(z,f) SD (crosses; equals its RMSE when bias is ~0)."""
    fig, axes = plt.subplots(1, 3, figsize=(W, 2.1))
    ests = ["dm", "ols_f", "ols_f_adj", "ols_f2"]
    spec = [("E1_size", lambda t: float(re.search(r"n=(\d+)", t).group(1)), "n", "sample size n", {"n": lambda t: int(re.search(r"n=(\d+)", t).group(1))}),
            ("E3_gamma", lambda t: float(t.split("=")[1]), "rho", r"interference ratio $\rho=\gamma/b$", {"rho": lambda t: float(t.split("=")[1])}),
            ("E2_degree", lambda t: float(t.split("d=")[1]), "deg", "mean degree", {"deg": lambda t: int(t.split("d=")[1])})]
    for ax, (exp, f, x, xl, keys) in zip(axes, spec):
        d = data(exp)
        if exp == "E2_degree":
            d = d[d.graph == "sbm"]
        d[x] = d.tag.map(f)
        agg = C.aggregate(d, [x, "estimator"])
        xs = sorted(agg[x].unique())
        for e in ests:
            st = C.EST_STYLE[e]
            r = agg[agg.estimator == e].sort_values(x)
            err(ax, r[x] if x != "rho" else [xs.index(v) for v in r[x]], r, "rel_rmse", st, label=st["label"])
        th = theory_sd(exp, keys if exp != "E2_degree" else {**keys, "graph": lambda t: t.split("_")[0]})
        if exp == "E2_degree":
            th = th[th.graph == "sbm"]
        th = th.sort_values(x)
        ax.plot(th[x] if x != "rho" else [xs.index(v) for v in th[x]], th.th, "x", color="k", ms=4, mew=0.8, label="P2 prediction, OLS(z,f)")
        ax.set_yscale("log"); logticks(ax, [0.05, 0.1, 0.2, 0.5, 1, 2])
        if x == "rho":
            ax.set_xticks(range(len(xs))); ax.set_xticklabels([f"{v:g}" for v in xs])
        else:
            ax.set_xscale("log"); ax.set_xticks(xs); ax.set_xticklabels([f"{v/1000:g}k" if v >= 1000 else f"{v:g}" for v in xs]); ax.minorticks_off()
            if x == "deg":
                ax.set_xticks([5, 20, 80, 160]); ax.set_xticklabels(["5", "20", "80", "160"])
        ax.set_xlabel(xl)
    axes[0].set_ylabel("rel. RMSE")
    for ax, t in zip(axes, ("(a) n (SBM, d=20)", r"(b) $\rho$ (SBM, n=3000)", "(c) degree (SBM, n=4000)")):
        ax.set_title(t, fontsize=7)
    legend(fig, axes[0], ncol=3, rows=2)
    C.save(fig, "figM_rmse_sweeps")


ALL = dict(main=fig_main, curv_bias=fig_curv_bias, spec_bias=fig_spec_bias, graphs=fig_graphs, model=fig_model, noise=fig_noise, theory=fig_theory)
if __name__ == "__main__":
    for k in (sys.argv[1:] or ALL):
        print("==", k)
        ALL[k]()
