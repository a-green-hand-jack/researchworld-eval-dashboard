"""Produce all tables/figures of the paper from results/*.csv.gz.  Usage: python code/analyze.py
Writes paper/figs/*.pdf and paper/tables/*.tex plus results/summary_*.csv.
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

os.makedirs("paper/figs", exist_ok=True); os.makedirs("paper/tables", exist_ok=True)
Z = 1.959964
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "legend.fontsize": 6.5, "figure.dpi": 150})
COL = {"classical": "k", "ppi": "tab:gray", "ppi++py": "tab:brown", "ppi++": "tab:red", "poly2": "tab:blue",
       "spline": "tab:cyan", "strat5": "tab:green", "iso_cf": "tab:purple", "hgb_cf": "tab:orange",
       "oracle_m": "gold", "FP-f": "tab:red", "FP-classical": "k", "hgbX_cf": "tab:pink", "poly3": "tab:olive", "strat10": "lime"}
LAB = {"classical": "classical", "ppi": "PPI", "ppi++py": "PPI++ (ppi-python)", "ppi++": "PPI++ (unclipped)", "poly2": "poly2",
       "spline": "spline", "strat5": "strat-5", "iso_cf": "isotonic (CF)", "hgb_cf": "GBM (CF)", "oracle_m": "oracle $m(f)$"}


def load_groups(prefix, groups=("cheap", "exp")):
    fs = [f"results/{prefix}_{g}.csv.gz" for g in groups if os.path.exists(f"results/{prefix}_{g}.csv.gz")]
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)


def add_cols(d, tdist=True):
    d = d.copy()
    d["w"] = 2 * Z * d.sd
    d["cov"] = (np.abs(d.theta - d.truth) <= Z * d.sd).astype(float)
    if tdist:
        df = np.maximum(d.n - 1 - d.p, 1)
        q = stats.t.ppf(0.975, df)
        d["cov_t"] = (np.abs(d.theta - d.truth) <= q * d.sd).astype(float)
        d["w_t"] = 2 * q * d.sd
    return d


def wilson(k, n, z=Z):
    ph = k / n; den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den; h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def summarize(d, keys, ref="ppi++"):
    """Per (keys, method): coverage (+Wilson), mean width, paired log-width ratio to ref with 95% CI."""
    rows = []
    for k, g in d.groupby(keys + ["method"], sort=False):
        rows.append(dict(zip(keys + ["method"], k if isinstance(k, tuple) else (k,)),
                          reps=len(g), p=g.p.iloc[0], cov=g["cov"].mean(), cov_t=g["cov_t"].mean(), w=g.w.mean(), w_t=g.w_t.mean(),
                          rmse=np.sqrt(np.mean((g.theta - g.truth) ** 2))))
    s = pd.DataFrame(rows)
    s["cov_lo"], s["cov_hi"] = wilson(s["cov"] * s.reps, s.reps)
    # paired ratio vs ref
    key_cols = keys + ["rep"]
    base = d[d.method == ref].set_index(key_cols)["sd"]
    rr = []
    for k, g in d.groupby(keys + ["method"], sort=False):
        b = base.reindex(g.set_index(key_cols).index).values
        lr = np.log(g.sd.values / b)
        m, se = lr.mean(), lr.std(ddof=1) / np.sqrt(len(lr))
        rr.append(dict(zip(keys + ["method"], k if isinstance(k, tuple) else (k,)),
                       ratio=np.exp(m), ratio_lo=np.exp(m - Z * se), ratio_hi=np.exp(m + Z * se)))
    return s.merge(pd.DataFrame(rr), on=keys + ["method"])


# ------------------------------------------------------------------ REAL (iid)
def real_iid():
    d = add_cols(load_groups("real_iid"))
    s = summarize(d, ["dataset", "n"]); s.to_csv("results/summary_real_iid.csv", index=False)
    return s


def fig_real_width(s):
    dss = list(s.dataset.unique()); meths = ["ppi++py", "poly2", "strat5", "spline", "iso_cf", "hgb_cf"]
    fig, axs = plt.subplots(2, 4, figsize=(7.2, 3.6), sharex=True)
    for ax, ds in zip(axs.ravel(), dss):
        for m in meths:
            g = s[(s.dataset == ds) & (s.method == m)].sort_values("n")
            ax.errorbar(g.n, g.ratio, yerr=[g.ratio - g.ratio_lo, g.ratio_hi - g.ratio], color=COL[m], label=LAB[m], lw=1, capsize=1.5, marker=".", ms=3)
        ax.axhline(1, color="tab:red", lw=0.8, ls="--"); ax.set_xscale("log"); ax.set_title(ds.replace("_", " "))
        ax.set_ylim(0.9, 1.35)
    for ax in axs[-1]: ax.set_xlabel("labeled $n$")
    axs[0, 0].set_ylabel("width / PPI++ (unclipped)"); axs[1, 0].set_ylabel("width / PPI++ (unclipped)")
    axs.ravel()[-1].axis("off"); h, l = axs[0, 0].get_legend_handles_labels(); axs.ravel()[-1].legend(h, l, loc="center", frameon=False)
    fig.tight_layout(); fig.savefig("paper/figs/real_width.pdf"); plt.close(fig)


def fig_real_cov(s):
    dss = list(s.dataset.unique()); meths = ["classical", "ppi++", "poly2", "strat5", "iso_cf", "hgb_cf"]
    fig, axs = plt.subplots(2, 4, figsize=(7.2, 3.6), sharex=True)
    for ax, ds in zip(axs.ravel(), dss):
        for m in meths:
            g = s[(s.dataset == ds) & (s.method == m)].sort_values("n")
            ax.plot(g.n, g["cov"], color=COL[m], label=LAB.get(m, m), lw=1, marker=".", ms=3)
        ax.axhline(0.95, color="k", lw=0.6, ls=":"); ax.set_xscale("log"); ax.set_title(ds.replace("_", " ")); ax.set_ylim(0.88, 0.98)
    for ax in axs[-1]: ax.set_xlabel("labeled $n$")
    axs[0, 0].set_ylabel("coverage (z, nominal .95)"); axs[1, 0].set_ylabel("coverage")
    axs.ravel()[-1].axis("off"); h, l = axs[0, 0].get_legend_handles_labels(); axs.ravel()[-1].legend(h, l, loc="center", frameon=False)
    fig.tight_layout(); fig.savefig("paper/figs/real_cov.pdf"); plt.close(fig)


def tab_real(s, n_list=(100, 1000)):
    meths = ["classical", "ppi", "ppi++py", "ppi++", "poly2", "strat5", "spline", "iso_cf", "hgb_cf"]
    names = {"classical": "Classical", "ppi": "PPI", "ppi++py": "PPI++ (ppi-python)", "ppi++": "PPI++ (unclipped)",
             "poly2": "Poly-2", "strat5": "Strat-5", "spline": "Spline", "iso_cf": "Isotonic-CF", "hgb_cf": "GBM-CF"}
    L = []
    for n in n_list:
        L.append(f"\\multicolumn{{{2 + 7}}}{{l}}{{\\textbf{{$n={n}$ labeled, $N=10^4$ unlabeled}}}}\\\\")
        for m in meths:
            row = [names[m]]
            for ds in s.dataset.unique():
                g = s[(s.dataset == ds) & (s.n == n) & (s.method == m)].iloc[0]
                r = "1" if m == "ppi++" else f"{g.ratio:.3f}"
                bold = "\\textbf{" if g["cov"] < g.cov_lo * 0 + 0.94 else ""
                cv = f"{100*g['cov']:.1f}"
                row.append(f"{r}/{bold + cv + '}' if bold else cv}")
            L.append(" & ".join(row) + "\\\\")
        L.append("\\midrule")
    hdr = "Method & " + " & ".join(d.replace("_", "\\_") for d in s.dataset.unique()) + "\\\\\\midrule"
    open("paper/tables/real_table.tex", "w").write("\\begin{tabular}{l" + "r" * len(s.dataset.unique()) + "}\\toprule\n" + hdr + "\n" + "\n".join(L[:-1]) + "\n\\bottomrule\\end{tabular}\n")


# ------------------------------------------------------------------ REAL (finite population)
def real_fpop():
    d = load_groups("real_fpop"); d["frac"] = d.n / (d.n + d.N)
    d = add_cols(d)
    d["rho"] = d.n / (d.n + d.N)
    s = summarize(d.assign(n_=d.n), ["dataset", "n", "N"], ref="ppi++")
    s["rho"] = s.n / (s.n + s.N); s.to_csv("results/summary_real_fpop.csv", index=False)
    return s


def fig_fpop(s, oracle):
    dss = list(s.dataset.unique())
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.6))
    cm = plt.get_cmap("tab10")
    for i, ds in enumerate(dss):
        g = s[(s.dataset == ds) & (s.method == "FP-f")].sort_values("rho")
        axs[0].plot(g.rho, g.ratio, color=cm(i), marker="o", ms=3, lw=1, label=ds.replace("_", " "))
        r2 = oracle.loc[oracle.dataset == ds, "R2_affine"].iloc[0]
        rho = np.linspace(0.01, 0.45, 50)
        axs[0].plot(rho, np.sqrt((1 - rho) * (1 - r2) / (1 - r2 + rho * r2)), color=cm(i), lw=0.6, ls=":")
        g2 = s[(s.dataset == ds) & (s.method == "ppi++")].sort_values("rho")
        axs[1].plot(g2.rho, g2["cov"], color=cm(i), marker="o", ms=3, lw=1, ls="--")
        g3 = s[(s.dataset == ds) & (s.method == "FP-f")].sort_values("rho")
        axs[1].plot(g3.rho, g3["cov"], color=cm(i), marker="s", ms=3, lw=1)
    axs[0].set_xlabel(r"labeled fraction $\rho=n/(n+N)$"); axs[0].set_ylabel("width FP-regression / PPI++")
    axs[0].legend(ncol=2, frameon=False); axs[0].set_title("width (dotted: theory, Prop. 3)")
    axs[1].axhline(0.95, color="k", lw=0.6, ls=":"); axs[1].set_xlabel(r"$\rho$"); axs[1].set_ylabel("coverage of finite-pop. mean")
    axs[1].set_title("dashed/circle: PPI++; solid/square: FP-regression"); axs[1].set_ylim(0.9, 1.0)
    fig.tight_layout(); fig.savefig("paper/figs/fpop.pdf"); plt.close(fig)


# ------------------------------------------------------------------ SYNTHETIC
def pred_ratio(R2c, R2a, pc, pa, n, N):
    r = n / N
    f = lambda R2, p: (1 - R2 / (1 + r)) + (1 - R2) * p / (n * (1 + r))
    return np.sqrt(f(R2c, pc) / f(R2a, pa))


def synth():
    pop = pd.read_csv("results/synth_population.csv").set_index("scenario")
    d = add_cols(load_groups("synth")); d = d.rename(columns={"scenario": "dataset"})
    s = summarize(d, ["dataset", "n"]); s.to_csv("results/summary_synth.csv", index=False)
    dN = add_cols(load_groups("synth_N")).rename(columns={"scenario": "dataset"})
    sN = summarize(dN, ["dataset", "N"]); sN.to_csv("results/summary_synth_N.csv", index=False)
    return s, sN, pop


PBAS = {"poly2": 2, "ppi++": 1, "spline": 6, "strat5": 4, "poly3": 3, "strat10": 9}


def fig_synth(s, pop):
    scs = list(s.dataset.unique()); meths = ["ppi++", "poly2", "strat5", "spline", "iso_cf", "hgb_cf", "oracle_m"]
    fig, axs = plt.subplots(2, 3, figsize=(7.2, 3.8), sharex=True)
    for ax, sc in zip(axs.ravel(), scs):
        for m in meths:
            g = s[(s.dataset == sc) & (s.method == m)].sort_values("n")
            ax.errorbar(g.n, g.ratio, yerr=[g.ratio - g.ratio_lo, g.ratio_hi - g.ratio], color=COL[m], label=LAB.get(m, m), lw=1, capsize=1.2, marker=".", ms=3)
        ns = np.array(sorted(s.n.unique()))
        ax.plot(ns, pred_ratio(pop.loc[sc, "R2_cal"], pop.loc[sc, "R2_affine"], 2, 1, ns, 10000), "k:", lw=1, label="theory, $p{=}2$")
        ax.axhline(1, color="tab:red", lw=0.6, ls="--"); ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(sc.replace("_", " "))
        ax.set_ylim(0.4, 1.7)
    for ax in axs[-1]: ax.set_xlabel("labeled $n$ ($N=10^4$)")
    for ax in axs[:, 0]: ax.set_ylabel("width / PPI++")
    h, l = axs[0, 0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=8, frameon=False)
    fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig("paper/figs/synth_width.pdf"); plt.close(fig)
    fig, axs = plt.subplots(2, 3, figsize=(7.2, 3.8), sharex=True)
    for ax, sc in zip(axs.ravel(), scs):
        for m in ["classical", "ppi++", "poly2", "strat5", "iso_cf", "hgb_cf"]:
            g = s[(s.dataset == sc) & (s.method == m)].sort_values("n")
            ax.plot(g.n, g["cov"], color=COL[m], label=LAB.get(m, m), lw=1, marker=".", ms=3)
        ax.axhline(0.95, color="k", lw=0.6, ls=":"); ax.set_xscale("log"); ax.set_title(sc.replace("_", " ")); ax.set_ylim(0.88, 0.98)
    for ax in axs[-1]: ax.set_xlabel("labeled $n$")
    for ax in axs[:, 0]: ax.set_ylabel("coverage (z)")
    h, l = axs[0, 0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=6, frameon=False)
    fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig("paper/figs/synth_cov.pdf"); plt.close(fig)


def tab_theory_check(s, pop):
    """Theory-vs-empirical sd ratio (basis vs PPI++) for several bases; MC error given."""
    L = []
    for sc in pop.index:
        for m in ["poly2", "strat5", "spline"]:
            for n in (60, 200, 1000):
                g = s[(s.dataset == sc) & (s.method == m) & (s.n == n)].iloc[0]
                th = pred_ratio(pop.loc[sc, "R2_cal"], pop.loc[sc, "R2_affine"], g.p, 1, n, 10000)
                L.append(dict(scenario=sc, method=m, n=n, emp=g.ratio, emp_lo=g.ratio_lo, emp_hi=g.ratio_hi, theory=th))
    t = pd.DataFrame(L); t.to_csv("results/theory_check.csv", index=False); return t


CANDS = ["ppi++", "poly2", "strat5", "spline", "iso_cf"]


def selection(d, keys, tag):
    """Data-driven choice: per replicate pick the candidate with the smallest *estimated* sd (post-selection coverage)."""
    g = d[d.method.isin(CANDS)].copy()
    idx = g.groupby(keys + ["rep"])["sd"].idxmin()
    sel = g.loc[idx].assign(method="select_min_sd")
    base = g[g.method == "ppi++"]
    out = []
    for k, a in sel.groupby(keys):
        b = base.set_index(keys + ["rep"]).loc[[tuple(list(k if isinstance(k, tuple) else (k,)) + [r]) for r in a.rep]]
        lr = np.log(a.sd.values . b.sd.values)
        out.append(dict(zip(keys, k if isinstance(k, tuple) else (k,)), cov=a["cov"].mean(), cov_t=a.cov_t.mean(), ratio=np.exp(lr.mean()),
                        frac_ppipp=(a.theta.values == b.theta.values).mean(), reps=len(a)))
    o = pd.DataFrame(out); o.to_csv(f"results/summary_select_{tag}.csv", index=False); return o


if __name__ == "__main__":
    what = sys.argv[1:] or ["real", "fpop", "synth"]
    orc = pd.read_csv("results/oracle_R2.csv")
    if "real" in what:
        s = real_iid(); fig_real_width(s); fig_real_cov(s); tab_real(s)
    if "fpop" in what:
        fig_fpop(real_fpop(), orc)
    if "synth" in what:
        s, sN, pop = synth(); fig_synth(s, pop); tab_theory_check(s, pop)
