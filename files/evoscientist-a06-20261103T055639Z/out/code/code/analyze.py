"""Aggregate result CSVs into paper tables (LaTeX + CSV) and figures. Usage: python code/analyze.py"""
import sys, glob, os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
os.makedirs("paper/figs", exist_ok=True); os.makedirs("paper/tabs", exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.grid": True, "grid.alpha": .3, "figure.dpi": 150})
MCOL = {"naive": "k", "holdout50": "tab:blue", "holdout75": "tab:cyan", "boot_opt": "tab:green", "replay": "tab:olive",
        "maxT": "tab:red", "cond": "tab:purple", "ladder_n13": "tab:orange", "ladder_n12": "tab:brown"}


def mc_se(x):
    return x.std(ddof=1) / np.sqrt(len(x))


def prep(df):
    df = df.copy()
    df["err"] = df.est - df.mu_sel
    df["cov"] = ((df.lo <= df.mu_sel) & (df.mu_sel <= df.hi)).astype(float)
    df.loc[df.lo.isna(), "cov"] = np.nan
    df["width"] = df.hi - df.lo
    return df


def summ(df, by):
    g = df.groupby(by)
    out = g.agg(bias=("err", "mean"), bias_se=("err", mc_se), rmse=("err", lambda x: np.sqrt((x ** 2).mean())),
                cov=("cov", "mean"), width=("width", "mean"), mu_sel=("mu_sel", "mean"), est=("est", "mean"), N=("err", "size")).reset_index()
    return out


def tex(df, path, floatfmt="%.3f"):
    df.to_latex(path, index=False, float_format=lambda x: floatfmt % x, escape=True)


def real():
    fs = sorted(glob.glob("results/main_*.csv"))
    if not fs: return
    D = prep(pd.concat([pd.read_csv(f) for f in fs]))
    D.to_pickle("results/main_all.pkl")
    S = summ(D, ["model", "parser", "alg", "K", "n", "method"]); S.to_csv("results/main_summary.csv", index=False)
    # Fig 1: naive optimism vs n, per algorithm
    for (mo, pa), d in D[D.method == "naive"].groupby(["model", "parser"]):
        if pa != "strict" and mo != "claude-opus-4-5": continue
        fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.5))
        for (a, K), dd in d.groupby(["alg", "K"]):
            s = summ(dd, ["n"]); ax[0].errorbar(s.n, s.bias, 1.96 * s.bias_se, marker="o", ms=3, label=f"{a}-{K}", capsize=2)
        ax[0].set_xscale("log"); ax[0].set_xlabel("search-set size n"); ax[0].set_ylabel("naive report - true acc. of selected"); ax[0].legend(fontsize=6)
        ax[0].axhline(0, c="k", lw=.6)
        dd = d[(d.alg == "grid")]
        for n, d3 in dd.groupby("n"): pass
        s = summ(d[d.alg == "random"], ["K", "n"])
        for n, d3 in s.groupby("n"): ax[1].plot(d3.K, d3.bias, marker="o", ms=3, label=f"n={n}")
        ax[1].set_xscale("log"); ax[1].set_xlabel("# configs visited (random search)"); ax[1].legend(fontsize=6)
        fig.tight_layout(); fig.savefig(f"paper/figs/gap_{mo}_{pa}.pdf"); plt.close(fig)
    # Fig 2: coverage + bias by method, grid search, per model
    for (mo, pa), d in D[D.alg == "grid"].groupby(["model", "parser"]):
        fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.4))
        for m, dd in d.groupby("method"):
            s = summ(dd, ["n"])
            ax[0].plot(s.n, s.bias, marker="o", ms=3, label=m, c=MCOL.get(m))
            if s["cov"].notna().any(): ax[1].plot(s.n, s["cov"], marker="o", ms=3, c=MCOL.get(m))
            ax[2].plot(s.n, s.rmse, marker="o", ms=3, c=MCOL.get(m))
        ax[1].axhline(.9, c="gray", ls="--"); ax[0].axhline(0, c="k", lw=.6)
        for a, t in zip(ax, ["bias (report - true)", "coverage of 90% interval", "RMSE"]): a.set_xscale("log"); a.set_title(t); a.set_xlabel("n")
        ax[0].legend(fontsize=5); fig.tight_layout(); fig.savefig(f"paper/figs/methods_{mo}_{pa}.pdf"); plt.close(fig)
    # Table: main
    for (mo, pa), d in D[(D.alg == "grid")].groupby(["model", "parser"]):
        s = summ(d, ["n", "method"])
        t = s.pivot(index="n", columns="method", values="bias")
        c = s.pivot(index="n", columns="method", values="cov")
        t.to_csv(f"paper/tabs/bias_grid_{mo}_{pa}.csv"); c.to_csv(f"paper/tabs/cov_grid_{mo}_{pa}.csv")


def gain():
    fs = sorted(glob.glob("results/gain_*.csv"))
    if not fs: return
    D = pd.concat([pd.read_csv(f) for f in fs])
    D["false_claim"] = D.claim & (D.true_gain <= 0)
    s = D.groupby(["model", "parser", "base", "alg", "n", "method"]).agg(claim=("claim", "mean"), false_claim=("false_claim", "mean"),
        cover=("covered", "mean"), est=("est", "mean"), true=("true_gain", "mean")).reset_index()
    s.to_csv("results/gain_summary.csv", index=False)


def synth():
    f = "results/synth.csv"
    if not os.path.exists(f): return
    D = prep(pd.read_csv(f)); S = summ(D, ["K", "n", "spread", "rho", "method"]); S.to_csv("results/synth_summary.csv", index=False)
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.4), sharey=True)
    for a, sp in zip(ax, [0.0, 0.02, 0.08]):
        for m in ["naive", "holdout50", "boot_opt", "maxT", "cond"]:
            s = S[(S.method == m) & (S.spread == sp) & (S.n == 100) & (S.rho == 0.5)]
            a.errorbar(s.K, s.bias, 1.96 * s.bias_se, marker="o", ms=3, label=m, c=MCOL[m], capsize=2)
        a.set_xscale("log"); a.set_title(f"spread={sp}"); a.set_xlabel("K configs"); a.axhline(0, c="k", lw=.6)
    ax[0].set_ylabel("bias (report - true), n=100"); ax[0].legend(fontsize=6); fig.tight_layout(); fig.savefig("paper/figs/synth_bias.pdf"); plt.close(fig)
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.4), sharey=True)
    for a, sp in zip(ax, [0.0, 0.02, 0.08]):
        for m in ["naive", "holdout50", "boot_opt", "maxT", "cond"]:
            s = S[(S.method == m) & (S.spread == sp) & (S.n == 100) & (S.rho == 0.5)]
            a.plot(s.K, s["cov"], marker="o", ms=3, label=m, c=MCOL[m])
        a.axhline(.9, c="gray", ls="--"); a.set_xscale("log"); a.set_title(f"spread={sp}"); a.set_xlabel("K configs")
    ax[0].set_ylabel("coverage (nominal 0.90), n=100"); fig.tight_layout(); fig.savefig("paper/figs/synth_cov.pdf"); plt.close(fig)


if __name__ == "__main__":
    real(); gain(); synth(); print("ok")
