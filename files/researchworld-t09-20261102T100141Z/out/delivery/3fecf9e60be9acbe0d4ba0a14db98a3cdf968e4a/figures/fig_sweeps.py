"""One-factor sweeps (experiments E1_size, E3_gamma, E4_curv, E2_degree, E6_spec, E8_design, E10_coverage) and the
seed-replication check (MAIN vs MAIN_s2). Usage: python3 fig_sweeps.py [name ...]  (default: all).
Inputs: results/replicates.parquet (+ diagnostics via population-fit rows). Metrics as in common.py
(relative = divided by |tau_true| of the cell; tau_true varies in E3 because it equals 1 + gamma)."""
import os, re, sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import common as C

C.setup_style()
W = C.TEXTWIDTH
_cache = {}


def data(exp, fit="observed"):
    if "obs" not in _cache:
        _cache["obs"] = C.load_replicates()
        _cache["pop"] = C.load_replicates(fit_data="population")
    return _cache["obs" if fit == "observed" else "pop"].query("experiment == @exp").copy()


def err(ax, x, r, key, st, ls="-", **kw):
    lo, hi = r[key + "_lo"], r[key + "_hi"]
    ax.errorbar(x, r[key], yerr=[np.clip(r[key] - lo, 0, None), np.clip(hi - r[key], 0, None)],
                fmt=ls + st["marker"], color=st["color"], ms=3, lw=0.9, capsize=0, **kw)


def theory_sd(exp, keys):
    """P2 predicted SD of OLS(z,f) / |tau| (theory_check_var.csv, `th_sd`), pooled over graph draws as the root mean square,
    for the cells of `exp`; `keys` maps the tag to the plotted coordinate(s). Returns a frame with `keys` columns and `th`."""
    v = pd.read_csv(os.path.join(C.RESULTS, "theory_check_var.csv"))
    v = v[v.exp == exp].copy()
    tau = data(exp).groupby("tag").abs_tau.first()
    v["th"] = v.th_sd / v.tag.map(tau)
    for k, f in keys.items():
        v[k] = v.tag.map(f)
    return v.groupby(list(keys)).th.apply(lambda x: np.sqrt((x ** 2).mean())).reset_index()


def legend(fig, ax=None, ncol=3, handles=None, labels=None, rows=1, fs=6.5):
    """Legend in a strip reserved below the axes (call last, instead of tight_layout)."""
    if handles is None:
        handles, labels = ax.get_legend_handles_labels()
    h_in = fig.get_figheight()
    fig.tight_layout(rect=(0, (0.17 * rows + 0.06) / h_in, 1, 1))
    fig.legend(handles, labels, loc="lower center", ncol=ncol, frameon=False, bbox_to_anchor=(0.5, 0.0), columnspacing=1.0,
               handletextpad=0.3, fontsize=fs)


def logticks(ax, ticks, axis="y"):
    """Plain-number ticks on a log axis (default log labels are sparse)."""
    a = ax.yaxis if axis == "y" else ax.xaxis
    (ax.set_yticks if axis == "y" else ax.set_xticks)(ticks)
    a.set_major_formatter(plt.FormatStrFormatter("%g")); a.set_minor_formatter(plt.NullFormatter())


def fig_size():
    """Fig. 6 (RQ2, H1): rel. RMSE, signed bias and SD vs n; correctly specified linear exposure (M1), SBM d=20, Bernoulli(0.5)."""
    d = data("E1_size")
    d["n"] = d.tag.str.extract(r"n=(\d+)")[0].astype(int)
    agg = C.aggregate(d, ["n", "estimator"])
    ests = [e for e in ("dm", "ols_f", "ols_f_adj", "ols_f2", "ols_poly") if e in set(agg.estimator)]
    fig, axes = plt.subplots(1, 3, figsize=(W, 2.2), sharex=True)
    ns = sorted(agg.n.unique())
    for e in ests:
        st = C.EST_STYLE[e]
        r = agg[agg.estimator == e].sort_values("n")
        err(axes[0], r.n, r, "rel_rmse", st, label=st["label"])
        if e != "dm":
            err(axes[1], r.n, r, "bias", st)
        err(axes[2], r.n, r, "sd", st)
    dmb = agg[agg.estimator == "dm"].bias.mean()
    axes[1].axhline(0, color="#999", lw=0.6)
    axes[1].text(0.97, 0.95, f"difference in means: {dmb:+.2f}\n(off scale, constant in n)", transform=axes[1].transAxes, fontsize=6, ha="right", va="top", color="#555")
    ref = agg[(agg.estimator == "ols_f")].set_index("n").sd
    nn = np.array(ns, float)
    axes[2].plot(nn, ref.iloc[0] * (nn / nn[0]) ** -0.5, color="#888", ls=":", lw=0.8)
    axes[2].text(nn[-1], ref.iloc[0] * (nn[-1] / nn[0]) ** -0.5 * 0.55, r"$\propto n^{-1/2}$", fontsize=6.5, color="#666", ha="right")
    th = theory_sd("E1_size", {"n": lambda t: int(re.search(r"n=(\d+)", t).group(1))}).sort_values("n")
    axes[2].plot(th.n, th.th, "x", color="k", ms=4, mew=0.8, label="P2 prediction, OLS(z,f)")
    for ax, t in zip(axes, ("rel. RMSE", r"bias / $|\tau|$ (OLS)", r"SD / $|\tau|$")):
        ax.set(xscale="log", xlabel="n", title=t)
        ax.set_xticks(ns); ax.set_xticklabels([f"{v/1000:g}k" for v in ns]); ax.minorticks_off()
    for ax in (axes[0], axes[2]):
        ax.set_yscale("log"); logticks(ax, [0.05, 0.1, 0.2, 0.5, 1, 2, 5])
    h, l = axes[0].get_legend_handles_labels(); h2, l2 = axes[2].get_legend_handles_labels()
    legend(fig, handles=h + h2, labels=l + l2, ncol=3, rows=2)
    print("E1_size R per cell (plotted estimators):", int(agg[agg.estimator.isin(ests)].R.min()))
    C.save(fig, "fig6_size")


def fig_gamma():
    """Fig. 7 (H1): rel. RMSE and signed bias vs interference strength rho = gamma/b (x categorical)."""
    d = data("E3_gamma")
    d["rho"] = d.tag.str.extract(r"gamma=([\d.]+)")[0].astype(float)
    agg = C.aggregate(d, ["rho", "estimator"])
    rhos = sorted(agg.rho.unique())
    ests = [e for e in ("dm", "hajek", "ols_cnt", "ols_f", "ols_f_adj", "ols_f2", "ols_poly") if e in set(agg.estimator)]
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.3))
    for e in ests:
        st = C.EST_STYLE[e]
        r = agg[(agg.estimator == e) & (agg.frac_undefined < 0.05)].sort_values("rho")
        if r.empty:
            print("E3: not drawn (undefined in >5% of replicates):", e)
            continue
        x = [rhos.index(v) for v in r.rho]
        err(axes[0], x, r, "rel_rmse", st, label=st["label"])
        err(axes[1], x, r, "bias", st)
    axes[1].axhline(0, color="#999", lw=0.6)
    th = theory_sd("E3_gamma", {"rho": lambda t: float(t.split("=")[1])}).sort_values("rho")
    axes[0].plot([rhos.index(v) for v in th.rho], th.th, "x", color="k", ms=4, mew=0.8, label="P2 prediction, OLS(z,f)")
    axes[0].set_yscale("log"); logticks(axes[0], [0.05, 0.1, 0.2, 0.5, 1, 2])
    for ax, t in zip(axes, ("rel. RMSE", r"bias / $|\tau|$")):
        ax.set(xlabel=r"interference-to-direct ratio $\rho=\gamma/b$", title=t)
        ax.set_xticks(range(len(rhos))); ax.set_xticklabels([f"{v:g}" for v in rhos])
    legend(fig, axes[0], ncol=3, rows=2)
    print("E3 R per cell (plotted estimators):", int(agg[agg.estimator.isin(ests)].R.min()))
    C.save(fig, "fig7_gamma")


def _curv(tag):
    m = re.match(r"(powq[\d.]+|threshsteep10.0_thr[\d.]+)_d(\d+)_p([\d.]+)", tag)
    return m.group(1), int(m.group(2)), float(m.group(3))


CURV = {"powq0.5": r"concave $f^{0.5}$", "powq2.0": r"convex $f^{2}$", "powq4.0": r"convex $f^{4}$",
        "powq1.0": r"linear $f$", "threshsteep10.0_thr0.5": "threshold at 0.5", "threshsteep10.0_thr0.9": "threshold at 0.9"}
CURV_ORDER = ["powq0.5", "powq2.0", "powq4.0", "threshsteep10.0_thr0.5", "threshsteep10.0_thr0.9", "powq1.0"]


def fig_curv_pop():
    """Fig. 8 (H2/H3): approximation (population) bias of OLS(z,f) [solid] and the quadratic OLS [dashed] vs design p,
    for convex/concave/threshold exposure responses; colour = mean degree. Noise- and baseline-free fits, so no sampling error."""
    d = data("E4_curv", "population")
    d[["kind", "deg", "p"]] = d.tag.apply(lambda t: __import__("pandas").Series(_curv(t)))
    d = d[d.estimator.isin(["ols_f", "ols_poly"])]
    agg = C.aggregate(d, ["kind", "deg", "p", "estimator"])
    kinds = [k for k in CURV_ORDER if k in set(agg.kind) and k != "powq1.0"]
    fig, axes = plt.subplots(2, 3, figsize=(W, 3.6), sharex=True)
    degcol = {10: "#0072B2", 40: "#009E73", 160: "#D55E00"}
    tb = pd.read_csv(os.path.join(C.RESULTS, "theory_check_bias.csv")); tb = tb[tb.exp == "E4_curv"].copy()
    tb[["kind", "deg", "p"]] = tb.tag.apply(lambda t: pd.Series(_curv(t)))
    tau = d.groupby("tag").abs_tau.first()  # theory_check_bias.csv is in outcome units; divide by the cell's |tau|
    tb["th"] = tb.th_pop_bias / tb.tag.map(tau)
    tb = tb.groupby(["kind", "deg", "p"]).th.mean().reset_index()
    for ax, k in zip(axes.flat, kinds):
        for dg, c in degcol.items():
            for e, ls in (("ols_f", "-"), ("ols_poly", "--")):
                r = agg[(agg.kind == k) & (agg.deg == dg) & (agg.estimator == e)].sort_values("p")
                ax.plot(r.p, r.bias, ls, color=c, marker="o" if e == "ols_f" else "s", ms=2.5, lw=0.9, mfc=c if e == "ols_f" else "white")
        for dg, c in degcol.items():
            q = tb[(tb.kind == k) & (tb.deg == dg)].sort_values("p")
            ax.plot(q.p, q.th, "x", color="k", ms=3.5, mew=0.7, zorder=5)
        ax.axhline(0, color="#999", lw=0.6)
        ax.set_title(CURV[k], fontsize=7.5)
    for ax in axes[1]:
        ax.set_xlabel("design p")
    for ax in axes[:, 0]:
        ax.set_ylabel(r"population bias / $|\tau|$")
    h = [Line2D([], [], color=c, label=f"mean degree {dg}") for dg, c in degcol.items()]
    h += [Line2D([], [], color="k", ls="-", marker="o", ms=2.5, label="OLS(z,f)"), Line2D([], [], color="k", ls="--", marker="s", mfc="w", ms=2.5, label="OLS(z,f,f$^2$,zf)"),
          Line2D([], [], color="k", marker="x", ls="", ms=3.5, label="P1 prediction, OLS(z,f)")]
    for ax in axes.flat[len(kinds):]:
        ax.axis("off")
    fig.tight_layout()
    axes.flat[-1].legend(handles=h, loc="center", frameon=False, fontsize=6.5)
    C.save(fig, "fig8_curvature_population_bias")


def fig_curv_obs():
    """Fig. 9 (H2/H4): observed rel. RMSE vs design p at mean degree 40, same curvature grid as Fig. 8."""
    d = data("E4_curv")
    d[["kind", "deg", "p"]] = d.tag.apply(lambda t: __import__("pandas").Series(_curv(t)))
    d = d[d.deg == 40]
    agg = C.aggregate(d, ["kind", "p", "estimator"])
    print("E4 observed R per cell (d=40):", int(agg[agg.estimator.isin(["dm", "ols_f", "ols_poly", "ols_poly3"])].R.min()))
    kinds = [k for k in CURV_ORDER if k in set(agg.kind) and k != "powq1.0"]
    fig, axes = plt.subplots(2, 3, figsize=(W, 3.6), sharex=True, sharey=True)
    for ax, k in zip(axes.flat, kinds):
        for e in ("dm", "ols_f", "ols_poly", "ols_poly3"):
            st = C.EST_STYLE[e]
            r = agg[(agg.kind == k) & (agg.estimator == e)].sort_values("p")
            err(ax, r.p, r, "rel_rmse", st, label=st["label"])
        ax.set_yscale("log"); ax.axhline(1, color="#999", lw=0.6, ls=":")
        logticks(ax, [0.5, 1, 2, 5, 10, 20, 50])
        ax.set_title(CURV[k], fontsize=7.5)
    for ax in axes[1]:
        ax.set_xlabel("design p")
    for ax in axes[:, 0]:
        ax.set_ylabel("rel. RMSE")
    for ax in axes.flat[len(kinds):]:
        ax.axis("off")
    fig.tight_layout()
    h, l = axes[0, 0].get_legend_handles_labels()
    axes.flat[-1].legend(h, l, loc="center", frameon=False, fontsize=6.5)
    C.save(fig, "fig9_curvature_rmse")


def fig_degree():
    """Fig. 10 (H3): rel. RMSE, |bias| and SD vs mean degree (n~4000), SBM and ER, linear exposure (M1)."""
    d = data("E2_degree")
    d["deg"] = d.tag.str.extract(r"d=(\d+)")[0].astype(int)
    agg = C.aggregate(d, ["graph", "deg", "estimator"])
    ests = [e for e in ("dm", "ols_f", "ols_f_adj", "ols_f2", "ols_poly") if e in set(agg.estimator)]
    fig, axes = plt.subplots(1, 3, figsize=(W, 2.1), sharex=True)
    for e in ests:
        st = C.EST_STYLE[e]
        for g, ls in (("sbm", "-"), ("er", "--")):
            r = agg[(agg.graph == g) & (agg.estimator == e)].sort_values("deg")
            if r.empty:
                continue
            err(axes[0], r.deg, r, "rel_rmse", st, ls=ls, label=st["label"] if g == "sbm" else None)
            if e != "dm":
                err(axes[1], r.deg, r, "bias", st, ls=ls)
            err(axes[2], r.deg, r, "sd", st, ls=ls)
    for ax, t in zip(axes, ("rel. RMSE", r"bias / $|\tau|$ (OLS)", r"SD / $|\tau|$")):
        ax.set(xscale="log", xlabel="mean degree", title=t)
    for ax in (axes[0], axes[2]):
        ax.set_yscale("log"); logticks(ax, [0.03, 0.1, 0.3, 1, 3])
    axes[1].axhline(0, color="#999", lw=0.6)
    dmb = agg[agg.estimator == "dm"].bias.mean()
    axes[1].text(0.97, 0.95, f"difference in means: {dmb:+.2f}\n(off scale)", transform=axes[1].transAxes, fontsize=6, ha="right", va="top", color="#555")
    th = theory_sd("E2_degree", {"graph": lambda t: t.split("_")[0], "deg": lambda t: int(t.split("d=")[1])})
    for g, ls in (("sbm", "-"), ("er", "--")):
        r = th[th.graph == g].sort_values("deg")
        axes[2].plot(r.deg, r.th, "x", color="k", ms=4, mew=0.8)
    h, l = axes[0].get_legend_handles_labels()
    h += [Line2D([], [], color="#777", ls="-"), Line2D([], [], color="#777", ls="--"), Line2D([], [], color="k", marker="x", ls="", ms=4)]
    l += ["SBM", "ER", "P2 prediction, OLS(z,f)"]
    legend(fig, handles=h, labels=l, ncol=4, rows=2)
    print("E2 R per cell (plotted estimators):", int(agg[agg.estimator.isin(ests)].R.min()))
    C.save(fig, "fig10_degree")


def fig_spec():
    """Fig. 11 (H2): feature set vs kind of interference (E6): rel. RMSE per estimator for five interference forms; marker = graph."""
    d = data("E6_spec")
    t = d.tag.str.extract(r"(\w+?)_d(\d+)_(.+)")
    d["gname"], d["kind"] = t[0], t[2]
    agg = C.aggregate(d, ["gname", "kind", "estimator"])
    kinds = [("lin_frac", "linear in fraction"), ("lin_count", "linear in count"), ("lin_2hop", "+ 2-hop"),
             ("het", "heterogeneous (mild)"), ("het_big", "heterogeneous (strong)")]
    ests = [e for e in ("dm", "ols_f", "ols_cnt", "ols_f_both", "ols_f_deg", "ols_f2", "ols_poly", "ols_f_adj", "ols_cnt_adj") if e in set(agg.estimator)]
    mk = {"sbm": "o", "ba": "s", "er": "^"}
    fig, axes = plt.subplots(len(kinds), 1, figsize=(W, 0.95 * len(kinds) + 1.0), sharex=True, sharey=True)
    for ax, (k, lab) in zip(axes, kinds):
        for i, e in enumerate(ests):
            st = C.EST_STYLE[e]
            for g, m in mk.items():
                r = agg[(agg.kind == k) & (agg.gname == g) & (agg.estimator == e)]
                if r.empty:
                    continue
                r = r.iloc[0]
                ax.errorbar(i + (list(mk).index(g) - 1) * 0.2, r.rel_rmse, yerr=[[r.rel_rmse - r.rel_rmse_lo], [r.rel_rmse_hi - r.rel_rmse]],
                            fmt=m, color=st["color"], ms=3, lw=0.7, capsize=0)
        ax.set_yscale("log"); ax.set_title(lab, loc="left", fontsize=7, pad=1); ax.set_ylabel("rel. RMSE"); ax.grid(axis="x", visible=False)
    axes[-1].set_xticks(range(len(ests)))
    axes[-1].set_xticklabels([C.EST_STYLE[e]["label"] for e in ests], rotation=40, ha="right", fontsize=6)
    h = [Line2D([], [], color="#777", marker=m, ls="", ms=3.5, label=g.upper()) for g, m in mk.items()]
    fig.legend(handles=h, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.0), fontsize=6.5)
    fig.subplots_adjust(top=0.93, hspace=0.6)
    C.save(fig, "fig11_specification")


def fig_design():
    """Fig. 12 (H3): rel. RMSE of dm / OLS(z,f) / OLS poly / Hajek under Bernoulli vs graph-cluster randomisation
    (Louvain resolution 0.3, 1, 3), for SBM with weak (mu=0.05) and strong (mu=0.3) mixing; three exposure responses."""
    d = data("E8_design")
    t = d.tag.str.extract(r"(lin_frac|pow2\.0|thresh)_(bernoulli|cluster[\d.]+)_mu([\d.]+)")
    d["resp"], d["dsg2"], d["mu"] = t[0], t[1], t[2].astype(float)
    agg = C.aggregate(d, ["resp", "dsg2", "mu", "estimator"])
    resp = [("lin_frac", "linear in fraction"), ("pow2.0", r"convex $f^2$"), ("thresh", "threshold")]
    order = ["bernoulli", "cluster0.3", "cluster1.0", "cluster3.0"]
    ests = ["dm", "hajek", "ols_f", "ols_poly"]
    fig, axes = plt.subplots(1, 3, figsize=(W, 2.3), sharey=True)
    for ax, (k, lab) in zip(axes, resp):
        for j, e in enumerate(ests):
            st = C.EST_STYLE[e]
            for mu, fill in ((0.05, True), (0.3, False)):
                for i, o in enumerate(order):
                    r = agg[(agg.resp == k) & (agg.dsg2 == o) & (agg.mu == mu) & (agg.estimator == e)]
                    if r.empty or r.iloc[0].frac_undefined > 0.05:
                        continue
                    r = r.iloc[0]
                    ax.errorbar(i + (j - 1.5) * 0.17 + (0.04 if fill else -0.04), r.rel_rmse, yerr=[[r.rel_rmse - r.rel_rmse_lo], [r.rel_rmse_hi - r.rel_rmse]],
                                fmt=st["marker"], color=st["color"], mfc=st["color"] if fill else "white", ms=3.2, lw=0.7, capsize=0)
        ax.set_yscale("log"); ax.set_title(lab, fontsize=7.5)
        ax.set_xticks(range(len(order))); ax.set_xticklabels(["Bern.", "cl. 0.3", "cl. 1", "cl. 3"], fontsize=6)
    axes[1].set_xlabel("design (Louvain resolution of the clusters)")
    axes[0].set_ylabel("rel. RMSE"); logticks(axes[0], [0.15, 0.2, 0.3, 0.5])
    h = [Line2D([], [], color=C.EST_STYLE[e]["color"], marker=C.EST_STYLE[e]["marker"], ls="", ms=3.5, label=C.EST_STYLE[e]["label"]) for e in ests]
    h += [Line2D([], [], color="#777", marker="o", ls="", ms=3.5, label=r"filled: weak mixing ($\mu=0.05$)"), Line2D([], [], color="#777", marker="o", mfc="w", ls="", ms=3.5, label=r"open: strong mixing ($\mu=0.3$)")]
    legend(fig, handles=h, labels=[x.get_label() for x in h], ncol=3, rows=2)
    print("E8 R per cell (plotted estimators):", int(agg[agg.estimator.isin(ests)].R.min()))
    C.save(fig, "fig12_design")


def fig_cover():
    """Fig. 13 (H6): coverage of the nominal-95% CI for OLS(z,f), n=1000 vs 4000, cluster-robust (cl) vs HC (hc) variance, three graph families
    (SBM weak/strong mixing, ER, BA); linear exposure (correct specification). Error bars: binomial 95% interval; dotted: nominal."""
    d = data("E10_coverage")
    d = d[d.estimator == "ols_f"]
    t = d.tag.str.extract(r"(.+)_n(\d+)_(cl|hc)")
    d["gk"], d["n2"], d["se"] = t[0], t[1].astype(int), t[2]
    agg = C.aggregate(d, ["gk", "n2", "se", "estimator"])
    gks = ["sbm0.05", "sbm0.3", "er", "ba"]
    fig, ax = plt.subplots(figsize=(3.4, 2.4))  # natural width 3.4 in: include at this size (about 0.6 linewidth)
    for i, g in enumerate(gks):
        for n2, mk in ((1000, "o"), (4000, "s")):
            for se, col, off in (("cl", "#0072B2", -0.12), ("hc", "#D55E00", 0.12)):
                r = agg[(agg.gk == g) & (agg.n2 == n2) & (agg.se == se)]
                if r.empty:
                    continue
                r = r.iloc[0]
                x = i + off + (0.0 if n2 == 1000 else 0.07)
                ax.errorbar(x, r.coverage, yerr=1.96 * r.cov_se, fmt=mk, color=col, ms=3.5, lw=0.8, capsize=0, mfc=col if n2 == 1000 else "white")
    ax.axhline(0.95, color="#555", lw=0.7, ls=":")
    ax.set_xticks(range(len(gks))); ax.set_xticklabels([r"SBM $\mu$=0.05", r"SBM $\mu$=0.3", "ER", "BA"], fontsize=6.5)
    ax.set_ylabel("coverage of 95% CI"); ax.set_ylim(0.6, 1.0)
    h = [Line2D([], [], color="#0072B2", marker="o", ls="", ms=3.5, label="cluster-robust"), Line2D([], [], color="#D55E00", marker="o", ls="", ms=3.5, label="HC (independent)"),
         Line2D([], [], color="#777", marker="o", ls="", ms=3.5, label="n=1000 (filled)"), Line2D([], [], color="#777", marker="s", mfc="w", ls="", ms=3.5, label="n=4000 (open)")]
    ax.legend(handles=h, frameon=False, fontsize=6.5, loc="lower left", ncol=2)
    print("E10 R per cell:", int(agg.R.min()))
    C.save(fig, "fig13_coverage_n")


def fig_seed():
    """Fig. A2: replication across independent seeds: rel. RMSE of every synthetic main-grid cell/estimator, MAIN vs MAIN_s2 (new graph draws and assignments)."""
    a = C.aggregate(data("MAIN"), ["tag", "estimator"])
    b = C.aggregate(data("MAIN_s2"), ["tag", "estimator"])
    m = a.merge(b, on=["tag", "estimator"], suffixes=("_1", "_2"))
    m = m[(m.frac_undefined_1 < 0.05) & (m.frac_undefined_2 < 0.05)]
    fig, ax = plt.subplots(figsize=(3.3, 3.1))  # natural width 3.3 in
    for e in m.estimator.unique():
        st = C.EST_STYLE[e]; r = m[m.estimator == e]
        ax.plot(r.rel_rmse_1, r.rel_rmse_2, ls="", marker=st["marker"], color=st["color"], ms=3, alpha=0.8, label=st["label"])
    lim = (m[["rel_rmse_1", "rel_rmse_2"]].min().min() * 0.8, m[["rel_rmse_1", "rel_rmse_2"]].max().max() * 1.2)
    ax.plot(lim, lim, color="#888", lw=0.6)
    ax.set(xscale="log", yscale="log", xlim=lim, ylim=lim, xlabel="rel. RMSE, seed set 1 (MAIN)", ylabel="rel. RMSE, seed set 2 (MAIN_s2)")
    ax.legend(frameon=False, fontsize=6, loc="upper left", handletextpad=0.2, labelspacing=0.25)
    print("pairs:", len(m), " max |log ratio|:", float(np.abs(np.log(m.rel_rmse_1 / m.rel_rmse_2)).max()))
    C.save(fig, "figA2_seed_replication")


ALL = dict(size=fig_size, gamma=fig_gamma, curv_pop=fig_curv_pop, curv_obs=fig_curv_obs, degree=fig_degree,
           spec=fig_spec, design=fig_design, cover=fig_cover, seed=fig_seed)
if __name__ == "__main__":
    for k in (sys.argv[1:] or ALL):
        print("==", k)
        ALL[k]()
