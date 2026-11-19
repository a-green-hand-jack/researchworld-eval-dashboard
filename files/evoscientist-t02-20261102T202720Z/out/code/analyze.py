"""Analysis + figures + tables for all sweeps.  Usage: python analyze.py   (reads results/*.jsonl, writes figures/ tables/)"""
import json, os, math, glob
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)
os.makedirs("tables", exist_ok=True)
RNG = np.random.RandomState(0)
TAUS = (0.5, 0.9, 0.99)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 6.5,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "figure.dpi": 150})


def first_reach(curve, tau):
    for c in curve:
        if c[4] >= tau:
            return c[0]
    return None


def load(name):
    path = f"results/{name}.jsonl"
    rows = []
    for l in open(path):
        r = json.loads(l)
        if "error" in r:
            continue
        for t in TAUS:
            r[f"tv{t}"] = first_reach(r["curve"], t)
        rows.append(r)
    df = pd.DataFrame(rows)
    df["N"] = df["n_train"]
    df["rho"] = df["n_params"] / (df["N"] * np.log2(df["p"]))
    df["budget"] = df["max_steps"]
    # delay ratios; censored (never reached) -> lower bound budget / t_fit, flag
    for t in TAUS:
        obs = df[f"tv{t}"].notna() & df["t_fit"].notna()
        df[f"D{t}"] = np.where(obs, df[f"tv{t}"] / df["t_fit"], np.nan)
        df[f"Dlb{t}"] = np.where(df["t_fit"].notna(), np.where(df[f"tv{t}"].notna(), df[f"tv{t}"], df["budget"]) / df["t_fit"], np.nan)
    return df.drop(columns=["curve"]).assign(_c=[r["curve"] for r in rows])


def boot_ci(x, f=np.median, B=2000):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return (np.nan, np.nan)
    bs = [f(x[RNG.randint(0, len(x), len(x))]) for _ in range(B)]
    return tuple(np.percentile(bs, [2.5, 97.5]))


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def cell_table(df, by):
    rows = []
    for key, g in df.groupby(by):
        key = key if isinstance(key, tuple) else (key,)
        r = dict(zip(by, key))
        r["n_params"] = int(g.n_params.iloc[0]); r["N"] = int(g.N.iloc[0]); r["runs"] = len(g)
        r["fit"] = f"{g.t_fit.notna().sum()}/{len(g)}"
        r["Tfit_med"] = g.t_fit.median()
        for t in (0.9, 0.99):
            k = g[f"tv{t}"].notna().sum()
            r[f"reach{t}"] = f"{k}/{len(g)}"
            r[f"Tv{t}_med"] = g[f"tv{t}"].median() if k * 2 > len(g) else np.nan  # median undefined if >=50% censored
            r[f"D{t}_med"] = g[f"D{t}"].median() if k * 2 > len(g) else np.nan
            r[f"Dlb{t}_med"] = g[f"Dlb{t}"].median()
        r["maxval_med"] = g.max_val_acc.median()
        r["finalval_med"] = g.final_val_acc.median()
        rows.append(r)
    return pd.DataFrame(rows)


def spearman_boot(x, y, B=2000):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 5:
        return np.nan, np.nan, (np.nan, np.nan), len(x)
    rho, pv = stats.spearmanr(x, y)
    bs = []
    for _ in range(B):
        i = RNG.randint(0, len(x), len(x))
        if len(set(x[i])) > 1 and len(set(y[i])) > 1:
            bs.append(stats.spearmanr(x[i], y[i])[0])
    return rho, pv, tuple(np.percentile(bs, [2.5, 97.5])), len(x)


def holm(pvals):
    k = len(pvals); order = np.argsort(pvals); adj = np.empty(k); run = 0
    for rank, i in enumerate(order):
        run = max(run, (k - rank) * pvals[i]); adj[i] = min(1, run)
    return adj


def binned_r2(x, y, nb=8):
    """fraction of variance of y explained by quantile bins of x (non-parametric 'collapse' score)."""
    x = np.asarray(x); y = np.asarray(y)
    edges = np.quantile(x, np.linspace(0, 1, nb + 1)); edges[-1] += 1e-9
    b = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, nb - 1)
    ss_tot = ((y - y.mean()) ** 2).sum(); ss_res = 0
    for k in range(nb):
        if (b == k).any():
            ss_res += ((y[b == k] - y[b == k].mean()) ** 2).sum()
    return 1 - ss_res / ss_tot


def fmt(v, d=0):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "--"
    return f"{v:.{d}f}"


def main():
    out = {}
    M = load("main")
    M.drop(columns=["_c"]).to_csv("tables/main_runs.csv", index=False)
    T = cell_table(M, ["frac", "d"])
    T.to_csv("tables/main_cells.csv", index=False)
    out["main_runs"] = len(M)

    # ---------- P1: D(0.9) vs width, per fraction ----------
    p1 = []
    for f, g in M.groupby("frac"):
        # (a) observed-only; (b) lower-bound including censored runs
        for lab, col in (("obs", "D0.9"), ("lb", "Dlb0.9")):
            rho, pv, ci, n = spearman_boot(np.log(g.d), np.log(g[col]))
            p1.append(dict(frac=f, variant=lab, rho=rho, p=pv, lo=ci[0], hi=ci[1], n=n))
    # pooled across fractions: partial via rank within fraction
    P1 = pd.DataFrame(p1)
    P1["p_holm"] = np.nan
    prim = P1[P1.variant == "obs"].index
    P1.loc[prim, "p_holm"] = holm(P1.loc[prim, "p"].values)
    P1.to_csv("tables/p1_spearman.csv", index=False)

    # ---------- P2: slopes of log T vs log d ----------
    p2 = []
    for f, g in M.groupby("frac"):
        sl = {}
        for lab, col in (("T_fit", "t_fit"), ("T_v0.99", "tv0.99"), ("T_v0.9", "tv0.9")):
            h = g[g[col].notna() & g["tv0.99"].notna() & g.t_fit.notna()]  # common support
            if len(h) < 6:
                sl[lab] = (np.nan, np.nan, np.nan); continue
            x, y = np.log(h.d.values), np.log(h[col].values)
            s = stats.linregress(x, y).slope
            bs = []
            for _ in range(2000):
                i = RNG.randint(0, len(h), len(h))
                if len(set(x[i])) > 1:
                    bs.append(stats.linregress(x[i], y[i]).slope)
            sl[lab] = (s, *np.percentile(bs, [2.5, 97.5]))
        # difference of slopes with paired bootstrap on runs
        h = g[g["tv0.99"].notna() & g.t_fit.notna()]
        diffs = []
        if len(h) >= 6:
            x = np.log(h.d.values); yf = np.log(h.t_fit.values); yg = np.log(h["tv0.99"].values)
            d0 = stats.linregress(x, yg).slope - stats.linregress(x, yf).slope
            for _ in range(2000):
                i = RNG.randint(0, len(h), len(h))
                if len(set(x[i])) > 1:
                    diffs.append(stats.linregress(x[i], yg[i]).slope - stats.linregress(x[i], yf[i]).slope)
            dci = np.percentile(diffs, [2.5, 97.5])
        else:
            d0, dci = np.nan, (np.nan, np.nan)
        p2.append(dict(frac=f, n=len(h), slope_Tfit=sl["T_fit"][0], lo_fit=sl["T_fit"][1], hi_fit=sl["T_fit"][2],
                       slope_Tv99=sl["T_v0.99"][0], lo_v99=sl["T_v0.99"][1], hi_v99=sl["T_v0.99"][2],
                       slope_Tv90=sl["T_v0.9"][0], diff_v99_minus_fit=d0, diff_lo=dci[0], diff_hi=dci[1]))
    pd.DataFrame(p2).to_csv("tables/p2_slopes.csv", index=False)

    # ---------- P3: threshold n* (D0.9>=3 via median-of-lower-bound) & collapse ----------
    def collect(df, groupcols):
        rows = []
        for key, g in df.groupby(groupcols):
            c = g.groupby("d").agg(n=("n_params", "first"), Dm=("Dlb0.9", "median")).reset_index().sort_values("d")
            rows.append((key, c))
        return rows

    def nstar(c, thr=3.0):
        # smallest width whose median lower-bound D0.9 >= thr; interpolate log n between that and the previous width
        n = c.n.values.astype(float); D = c.Dm.values
        for i in range(len(D)):
            if D[i] >= thr:
                if i == 0:
                    return float("nan")  # threshold already exceeded at smallest width -> not identified
                x0, x1 = math.log(n[i - 1]), math.log(n[i]); y0, y1 = math.log(D[i - 1]), math.log(D[i])
                return math.exp(x0 + (math.log(thr) - y0) * (x1 - x0) / (y1 - y0))
        return float("nan")

    P = load("pscan")
    P.drop(columns=["_c"]).to_csv("tables/pscan_runs.csv", index=False)
    P5 = M[M.frac == 0.5]
    Aall = pd.concat([M, P], ignore_index=True)
    # settings: (p, frac)
    sets = []
    for (p, f), g in Aall.groupby(["p", "frac"]):
        sets.append((p, f, g))
    ns_rows = []
    for p, f, g in sets:
        c = g.groupby("d").agg(n=("n_params", "first"), Dm=("Dlb0.9", "median"), N=("N", "first")).reset_index().sort_values("d")
        ns_rows.append(dict(p=p, frac=f, N=int(c.N.iloc[0]), nstar=nstar(c), widths=len(c)))
    NS = pd.DataFrame(ns_rows)
    # bootstrap over seeds for n*: resample runs within each (d) cell
    def nstar_boot(g, B=500):
        vals = []
        for _ in range(B):
            parts = [h.iloc[RNG.randint(0, len(h), len(h))] for _, h in g.groupby("d")]
            gb = pd.concat(parts)
            c = gb.groupby("d").agg(n=("n_params", "first"), Dm=("Dlb0.9", "median")).reset_index().sort_values("d")
            vals.append(nstar(c))
        v = np.array(vals); return np.nanpercentile(v, [2.5, 97.5]) if np.isfinite(v).sum() > B * 0.5 else (np.nan, np.nan), np.isfinite(v).mean()
    lo, hi, okf = [], [], []
    for p, f, g in sets:
        ci, ok = nstar_boot(g); lo.append(ci[0]); hi.append(ci[1]); okf.append(ok)
    NS["lo"], NS["hi"], NS["frac_boot_ident"] = lo, hi, okf
    NS.to_csv("tables/p3_nstar.csv", index=False)
    ok = NS.dropna(subset=["nstar"])
    if len(ok) >= 3:
        sl = stats.linregress(np.log(ok.N), np.log(ok.nstar))
        bs = []
        for _ in range(2000):
            i = RNG.randint(0, len(ok), len(ok))
            if len(set(ok.N.values[i])) > 1:
                bs.append(stats.linregress(np.log(ok.N.values[i]), np.log(ok.nstar.values[i])).slope)
        out["P3_slope"] = (sl.slope, *np.percentile(bs, [2.5, 97.5]), len(ok))
    # collapse score: how well does a function of x explain log Dlb0.9, x in {n, rho, N-only-not-meaningful}
    A = Aall[Aall["Dlb0.9"].notna() & (Aall.d >= 8)]
    y = np.log(A["Dlb0.9"].values)
    r2n = binned_r2(np.log(A.n_params.values), y); r2r = binned_r2(np.log(A.rho.values), y)
    bsd = []
    idx = np.arange(len(A))
    for _ in range(500):
        i = RNG.randint(0, len(A), len(A))
        bsd.append(binned_r2(np.log(A.rho.values[i]), y[i]) - binned_r2(np.log(A.n_params.values[i]), y[i]))
    out["collapse"] = dict(R2_n=r2n, R2_rho=r2r, diff=r2r - r2n, diff_ci=tuple(np.percentile(bsd, [2.5, 97.5])), runs=len(A))
    out["collapse_note"] = "binned R2 on log D_lb(0.9) pooled over main+pscan"

    # ---------- figures ----------
    # Fig 1: example curves, frac 0.5, seed 1, selected widths
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 1.9), sharey=True)
    for ax, d in zip(axs, (8, 32, 128)):
        r = M[(M.frac == 0.5) & (M.d == d) & (M.seed == 1)].iloc[0]
        c = np.array(r._c)
        ax.plot(c[:, 0], c[:, 2], label="train", color="C0")
        ax.plot(c[:, 0], c[:, 4], label="val", color="C3")
        if not np.isnan(r.t_fit):
            ax.axvline(r.t_fit, color="C0", ls=":", lw=0.8)
        ax.set_xscale("log"); ax.set_title(f"d={d} ({r.n_params:,} params)"); ax.set_xlabel("step")
    axs[0].set_ylabel("accuracy"); axs[0].legend(loc="center right")
    plt.tight_layout(); plt.savefig("figures/fig_curves.pdf"); plt.close()

    # Fig 2: times vs width per fraction
    fig, axs = plt.subplots(1, 4, figsize=(7.0, 2.0), sharey=True)
    for ax, (f, g) in zip(axs, M.groupby("frac")):
        for col, lab, c in (("t_fit", "$T_{fit}$ (train 99%)", "C0"), ("tv0.9", "$T_v$(0.9)", "C1"), ("tv0.99", "$T_v$(0.99)", "C3")):
            ds = sorted(g.d.unique()); med = []; lo = []; hi = []
            for d in ds:
                h = g[g.d == d]
                k = h[col].notna().sum()
                if k * 2 > len(h):  # median defined only if majority observed
                    med.append(h[col].median()); a, b = boot_ci(h[col].fillna(1e9).values)
                    lo.append(a); hi.append(min(b, 2e4))
                else:
                    med.append(np.nan); lo.append(np.nan); hi.append(np.nan)
            ax.plot(ds, med, "o-", ms=3, lw=1, color=c, label=lab)
            ax.fill_between(ds, lo, hi, color=c, alpha=0.2, lw=0)
            # censored markers
            for d in ds:
                h = g[g.d == d]; nc = h[col].isna().sum()
                if nc > 0 and col != "t_fit":
                    ax.plot([d], [2.0e4], "v", color=c, ms=2 + nc, alpha=0.5)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(f"train fraction {f}"); ax.set_xlabel("width d")
    axs[0].set_ylabel("steps"); axs[0].legend(loc="lower left")
    plt.tight_layout(); plt.savefig("figures/fig_times.pdf"); plt.close()

    # Fig 3: delay ratio vs d and vs rho
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.1))
    cm = {0.4: "C0", 0.5: "C1", 0.6: "C2", 0.7: "C3"}
    for f, g in M.groupby("frac"):
        c = g.groupby("d").agg(Dm=("Dlb0.9", "median"), q1=("Dlb0.9", lambda x: x.quantile(.25)), q3=("Dlb0.9", lambda x: x.quantile(.75))).reset_index()
        axs[0].errorbar(c.d, c.Dm, yerr=[c.Dm - c.q1, c.q3 - c.Dm], fmt="o-", ms=3, lw=1, color=cm[f], label=f"frac {f}", capsize=1.5)
        rho = g.groupby("d").rho.first().values
        axs[1].plot(rho, c.Dm, "o-", ms=3, lw=1, color=cm[f], label=f"frac {f}")
        nn = g.groupby("d").n_params.first().values
        axs[2].plot(nn, c.Dm, "o-", ms=3, lw=1, color=cm[f])
    for ax, xl in zip(axs, ("width d", r"$\rho=n/(N\log_2 p)$", "parameters $n$")):
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel(xl); ax.axhline(3, color="k", lw=0.5, ls="--")
    axs[0].set_ylabel(r"$D(0.9)=T_v(0.9)/T_{fit}$ (median, IQR)"); axs[0].legend()
    plt.tight_layout(); plt.savefig("figures/fig_delay.pdf"); plt.close()

    # Fig 4: pscan collapse
    fig, axs = plt.subplots(1, 2, figsize=(4.8, 2.1))
    cmp_ = {31: "C4", 43: "C5", 53: "C1", 67: "C6"}
    for p, g in Aall[Aall.frac == 0.5].groupby("p"):
        g = g[g.d.isin([8, 16, 32, 64, 128])]
        c = g.groupby("d").agg(Dm=("Dlb0.9", "median"), n=("n_params", "first"), rho=("rho", "first")).reset_index()
        axs[0].plot(c.n, c.Dm, "o-", ms=3, lw=1, color=cmp_[p], label=f"p={p} (N={g.N.iloc[0]})")
        axs[1].plot(c.rho, c.Dm, "o-", ms=3, lw=1, color=cmp_[p])
    for ax, xl in zip(axs, ("parameters $n$", r"$\rho=n/(N\log_2 p)$")):
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel(xl); ax.axhline(3, color="k", lw=0.5, ls="--")
    axs[0].set_ylabel("median $D_{lb}(0.9)$"); axs[0].legend()
    plt.tight_layout(); plt.savefig("figures/fig_pscan.pdf"); plt.close()

    # ---------- secondary sweeps: MLP, robustness ----------
    sec = {}
    for name in ("mlp", "robust"):
        if os.path.exists(f"results/{name}.jsonl"):
            S = load(name); S.drop(columns=["_c"]).to_csv(f"tables/{name}_runs.csv", index=False); sec[name] = S
    if "mlp" in sec:
        S = sec["mlp"]; cell_table(S, ["frac", "d"]).to_csv("tables/mlp_cells.csv", index=False)
        rows = []
        for f, g in S.groupby("frac"):
            for lab, col in (("obs", "D0.9"), ("lb", "Dlb0.9")):
                rho, pv, ci, n = spearman_boot(np.log(g.d), np.log(g[col])); rows.append(dict(frac=f, variant=lab, rho=rho, p=pv, lo=ci[0], hi=ci[1], n=n))
        pd.DataFrame(rows).to_csv("tables/mlp_spearman.csv", index=False)
        fig, axs = plt.subplots(1, 2, figsize=(4.8, 2.0), sharey=True)
        for ax, (f, g) in zip(axs, S.groupby("frac")):
            for col, lab, c in (("t_fit", "$T_{fit}$", "C0"), ("tv0.9", "$T_v$(0.9)", "C1"), ("tv0.99", "$T_v$(0.99)", "C3")):
                ds = sorted(g.d.unique()); med = [g[g.d == d][col].median() if g[g.d == d][col].notna().sum() * 2 > len(g[g.d == d]) else np.nan for d in ds]
                ax.plot(ds, med, "o-", ms=3, lw=1, color=c, label=lab)
                for d in ds:
                    nc = g[g.d == d][col].isna().sum()
                    if nc and col != "t_fit": ax.plot([d], [2e4], "v", color=c, ms=2 + nc, alpha=.5)
            ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(f"MLP, train fraction {f}"); ax.set_xlabel("width d")
        axs[0].set_ylabel("steps"); axs[0].legend()
        plt.tight_layout(); plt.savefig("figures/fig_mlp.pdf"); plt.close()
    if "robust" in sec:
        S = sec["robust"].copy()
        S["cond"] = np.where(S.wd != 1.0, "wd=" + S.wd.astype(str), np.where(S.init_scale != 1.0, "init=" + S.init_scale.astype(str), "op=" + S.op))
        cell_table(S, ["cond", "d"]).to_csv("tables/robust_cells.csv", index=False)
        base_ = M[(M.frac == 0.5) & M.d.isin([16, 32, 64, 128]) & M.seed.isin([1, 2, 3])].copy(); base_["cond"] = "baseline"
        S2 = pd.concat([S, base_], ignore_index=True)
        rows = []
        for cnd, g in S2.groupby("cond"):
            for lab, col in (("obs", "D0.9"), ("lb", "Dlb0.9")):
                rho, pv, ci, n = spearman_boot(np.log(g.d), np.log(g[col])); rows.append(dict(cond=cnd, variant=lab, rho=rho, p=pv, lo=ci[0], hi=ci[1], n=n))
        pd.DataFrame(rows).to_csv("tables/robust_spearman.csv", index=False)
        conds = ["baseline", "wd=0.3", "wd=3.0", "init=0.5", "init=2.0", "op=sub", "op=mul"]
        fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.0), sharey=True)
        for ax, (col, lab) in zip(axs, (("t_fit", "$T_{fit}$"), ("tv0.9", "$T_v$(0.9)"), ("tv0.99", "$T_v$(0.99)"))):
            for i, cnd in enumerate(conds):
                g = S2[S2.cond == cnd]; ds = [16, 32, 64, 128]
                med = [g[g.d == d][col].median() if g[g.d == d][col].notna().sum() * 2 > len(g[g.d == d]) else np.nan for d in ds]
                ax.plot(ds, med, "o-", ms=3, lw=1, color=f"C{i}", label=cnd)
            ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(lab); ax.set_xlabel("width d")
        axs[0].set_ylabel("steps (frac 0.5)"); axs[2].legend(ncol=1, loc="upper right")
        plt.tight_layout(); plt.savefig("figures/fig_robust.pdf"); plt.close()

    json.dump(out, open("tables/summary.json", "w"), indent=1, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
    print(json.dumps(out, indent=1, default=str))
    print(T.to_string())
    print(P1.to_string())
    print(pd.DataFrame(p2).to_string())
    print(NS.to_string())


if __name__ == "__main__":
    main()
