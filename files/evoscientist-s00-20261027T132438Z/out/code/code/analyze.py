"""Fit and evaluate cover-time predictors from graph statistics.

Usage: python3 code/analyze.py --csv results/graphs.csv --out results/
Predictors use only n, m, max degree, diameter (no hitting times).
Evaluation: repeated 5-fold CV and leave-one-family-out (LOFO); bootstrap CIs over graphs.
"""
import argparse
import csv
import os

import numpy as np


def load(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    d = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    out = {
        "family": d["family"], "name": d["name"],
        "n": d["n"].astype(float), "m": d["m"].astype(float),
        "dmax": d["dmax"].astype(float), "diam": d["diam"].astype(float),
        "C": d["mc_mean"].astype(float), "se": d["mc_se"].astype(float),
        "exact": d["exact"].astype(float),
    }
    return out


def feats(D, kind):
    cols = [np.ones(len(D["n"]))]
    if kind == "reg_nmD":
        cols += [np.log(D["n"]), np.log(D["m"]), np.log(D["diam"])]
    elif kind == "reg_nmDd":
        cols += [np.log(D["n"]), np.log(D["m"]), np.log(D["diam"]), np.log(D["dmax"])]
    elif kind == "reg_nm":
        cols += [np.log(D["n"]), np.log(D["m"])]
    return np.column_stack(cols)


# Each model: (name, fit(train)->params, predict(params, D)->C_hat)
def fit_loglin(kind):
    def fit(T):
        X = feats(T, kind)
        y = np.log(T["C"])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return beta
    def pred(beta, D):
        return np.exp(feats(D, kind) @ beta)
    return fit, pred


def fit_scale(stat):
    """One-parameter model C = kappa * stat(D); kappa = median ratio in log space."""
    def f(T):
        return np.exp(np.median(np.log(T["C"]) - np.log(stat(T))))
    def p(k, D):
        return k * stat(D)
    return f, p


MODELS = {
    "scale: kappa*n*m": fit_scale(lambda D: D["n"] * D["m"]),
    "scale: kappa*m*diam": fit_scale(lambda D: D["m"] * D["diam"]),
    "scale: kappa*n*m*diam": fit_scale(lambda D: D["n"] * D["m"] * D["diam"]),
    "loglin: n,m,diam": fit_loglin("reg_nmD"),
    "loglin: n,m,diam,dmax": fit_loglin("reg_nmDd"),
}


def subset(D, idx):
    return {k: v[idx] for k, v in D.items()}


def ape(pred, true):
    return np.abs(pred - true) / true


def run_split(D, train_idx, test_idx):
    res = {}
    T, Te = subset(D, train_idx), subset(D, test_idx)
    for name, (fit, pred) in MODELS.items():
        par = fit(T)
        res[name] = pred(par, Te)
    res["bound 2m(n-1) (no fit)"] = 2 * Te["m"] * (Te["n"] - 1)
    return res


def cv_errors(D, reps=20, k=5, seed=0):
    rng = np.random.default_rng(seed)
    N = len(D["n"])
    errs = {}
    for _ in range(reps):
        perm = rng.permutation(N)
        folds = np.array_split(perm, k)
        for f in range(k):
            test = folds[f]
            train = np.concatenate([folds[g] for g in range(k) if g != f])
            res = run_split(D, train, test)
            for name, p in res.items():
                errs.setdefault(name, []).append((test, ape(p, D["C"][test])))
    return errs


def lofo_errors(D):
    errs = {}
    for fam in np.unique(D["family"]):
        test = np.where(D["family"] == fam)[0]
        train = np.where(D["family"] != fam)[0]
        if len(train) < 10:
            continue
        res = run_split(D, train, test)
        for name, p in res.items():
            errs.setdefault(name, []).append((test, ape(p, D["C"][test])))
    return errs


def summarize(errs, N, rng, B=2000):
    """Per-graph out-of-fold error (median over repetitions), then aggregate."""
    out = {}
    for name, lst in errs.items():
        per = [[] for _ in range(N)]
        for idx, e in lst:
            for i, v in zip(idx, e):
                per[i].append(v)
        g = np.array([np.median(p) if p else np.nan for p in per])
        g = g[~np.isnan(g)]
        boots = [np.median(g[rng.integers(0, len(g), len(g))]) for _ in range(B)]
        out[name] = dict(medAPE=float(np.median(g)),
                         ci=(float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))),
                         p90=float(np.percentile(g, 90)), per_graph=g, mean=float(np.mean(g)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/graphs.csv")
    ap.add_argument("--out", default="results/")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    D = load(args.csv)
    N = len(D["n"])
    rng = np.random.default_rng(1)
    lines = []
    lines.append(f"# Results summary\n\nGraphs: {N} (n in [{int(D['n'].min())},{int(D['n'].max())}]), "
                 f"MC walks per graph: 2000.\n")
    # MC noise
    rel_se = D["se"] / D["C"]
    lines.append(f"Monte Carlo relative standard error: median {np.median(rel_se):.4f}, "
                 f"max {rel_se.max():.4f}.\n")
    ex = ~np.isnan(D["exact"])
    if ex.any():
        mc_err = np.abs(D["C"][ex] - D["exact"][ex]) / D["exact"][ex]
        lines.append(f"Validation vs exact (n<=8, {ex.sum()} graphs): max |MC-exact|/exact = {mc_err.max():.4f}; "
                     f"all within 3 SE: {bool(np.all(np.abs(D['C'][ex]-D['exact'][ex]) <= 3*D['se'][ex]+1e-9))}.\n")

    # Bound tightness
    bnd = 2 * D["m"] * (D["n"] - 1)
    ratio = D["C"] / bnd
    lines.append(f"Ratio C / (2m(n-1)): median {np.median(ratio):.3f}, min {ratio.min():.3f}, max {ratio.max():.3f}.\n")

    for label, errs in [("Repeated 5-fold CV (20 repeats)", cv_errors(D)),
                        ("Leave-one-family-out", lofo_errors(D))]:
        s = summarize(errs, N, rng)
        lines.append(f"\n## {label}\n\n| predictor | median APE | 95% bootstrap CI | 90th pct APE |\n|---|---|---|---|")
        for name, v in s.items():
            lines.append(f"| {name} | {v['medAPE']:.3f} | [{v['ci'][0]:.3f}, {v['ci'][1]:.3f}] | {v['p90']:.3f} |")
        if label.startswith("Leave"):
            fams = np.unique(D["family"])
            lines.append("\nPer-family median APE under LOFO (loglin n,m,diam vs bound):\n")
            lines.append("| family | count | loglin APE | scale n*m APE | bound APE | median C/bound |\n|---|---|---|---|---|---|")
            lof = lofo_errors(D)
            for fam in fams:
                idx = np.where(D["family"] == fam)[0]
                def med(name):
                    vals = [e for t, e in lof[name] if len(t) == len(idx) and np.all(t == idx)]
                    return np.median(vals[0]) if vals else float("nan")
                lines.append(f"| {fam} | {len(idx)} | {med('loglin: n,m,diam'):.3f} | {med('scale: kappa*n*m'):.3f} | "
                             f"{np.median(ratio[idx] ** 0 * np.abs(bnd[idx]-D['C'][idx])/D['C'][idx]):.3f} | {np.median(ratio[idx]):.3f} |")

    # full-data fit coefficients
    lines.append("\n## Full-data fits (all graphs)\n")
    for name, (fit, pred) in MODELS.items():
        par = fit(D)
        if name.startswith("loglin"):
            lines.append(f"- {name}: coefficients {np.round(par, 3).tolist()} (intercept, then log-features)")
        else:
            lines.append(f"- {name}: kappa = {float(par):.4f}")
    with open(os.path.join(args.out, "summary.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fit, pred = MODELS["loglin: n,m,diam"]
        par = fit(D)
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.8))
        fams = np.unique(D["family"])
        for fam in fams:
            i = D["family"] == fam
            ax[0].scatter(D["C"][i], pred(par, subset(D, np.where(i)[0])) if False else
                          np.exp(feats(subset(D, np.where(i)[0]), "reg_nmD") @ par), s=8, label=fam)
        lim = [D["C"].min() * 0.5, D["C"].max() * 2]
        ax[0].plot(lim, lim, "k--", lw=0.8)
        ax[0].set_xscale("log"); ax[0].set_yscale("log")
        ax[0].set_xlabel("MC cover time"); ax[0].set_ylabel("in-sample loglin prediction")
        ax[0].legend(fontsize=5, ncol=2)
        g = summarize(cv_errors(D, reps=5), N, rng, B=200)
        order = list(g.keys())
        ax[1].boxplot([g[k]["per_graph"] for k in order], vert=False)
        ax[1].set_yticks(range(1, len(order) + 1))
        ax[1].set_yticklabels([k.replace(" (no fit)", "") for k in order], fontsize=6)
        ax[1].set_xscale("log"); ax[1].set_xlabel("per-graph CV APE")
        plt.tight_layout()
        plt.savefig(os.path.join(args.out, "fig_predictions.pdf"))
        print("figure saved")
    except Exception as e:  # matplotlib optional
        print("figure skipped:", e)


if __name__ == "__main__":
    main()
