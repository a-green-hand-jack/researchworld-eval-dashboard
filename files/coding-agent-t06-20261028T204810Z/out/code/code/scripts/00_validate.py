"""Correctness checks (results/validation.json):
 1. BT fit agrees with scipy L-BFGS on the raw (un-aggregated) likelihood.
 2. First-order influence predicts the exact change from deleting one comparison.
 3. Greedy-with-refit budgets vs exhaustive search on small random subsamples
    (drop: exact up to k<=3, flip: exact up to k<=2)."""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
from scipy.optimize import minimize

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lbstab import data, bt, attacks
from lbstab.bt import cells_from_frame

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results")
KD, KF = 3, 2
SRCS = ["mtbench_human", "mtbench_gpt4", "webdev10k", "nba2012"]


def check_fit():
    out = {}
    for nm in ["mtbench_human", "nba2010", "arena55k"]:
        df, names, home = data.load(nm)
        c = cells_from_frame(df, names, home)
        th = bt.fit(c, 1e-2)
        a, b, y = df.a.values, df.b.values, df.y.values
        h = df.h.values if "h" in df else np.zeros(len(df))
        m = len(names)
        pen = np.full(c.dim, 1e-2)
        if home:
            pen[m] = 1e-8

        def nll(t):
            z = t[a] - t[b] + (t[m] * h if home else 0)
            p = 1 / (1 + np.exp(-z))
            r = y - p
            g = np.bincount(a, r, minlength=len(t)) - np.bincount(b, r, minlength=len(t))
            if home:
                g[m] = (r * h).sum()
            f = -(y * np.log(p) + (1 - y) * np.log(1 - p)).sum() + 0.5 * (pen * t * t).sum()
            return f, -(g - pen * t)
        o = minimize(nll, np.zeros(c.dim), jac=True, method="L-BFGS-B", options=dict(maxiter=10000, gtol=1e-10))
        out[nm] = float(np.abs(o.x - th).max())
    return out


def check_influence():
    inf = {}
    for nm in ["arena55k", "nba2010", "mtbench_human"]:
        c = data.load_cells(nm)
        th = bt.fit(c)
        r = bt.ranking(th, c)
        i, j = r[0], r[1]
        _, H, p = bt.grad_hess(c, th, 1e-2)
        cv = np.zeros(c.dim)
        cv[i], cv[j] = 1, -1
        u = np.linalg.solve(H, cv)
        s = u[c.a] - u[c.b] + (u[c.m] * c.h if c.home else 0)
        pred = -s * (c.y - p)
        nz = np.where(c.w > 0)[0]
        sel = nz[np.argsort(pred[nz])[:30]]
        act = []
        for n in sel:
            w = c.w.copy()
            w[n] -= 1
            t2 = bt.fit(c.copy(w), 1e-2, th)
            act.append((t2[i] - t2[j]) - (th[i] - th[j]))
        act = np.array(act)
        rel = np.abs(act - pred[sel]) / np.abs(act)
        inf[nm] = dict(rel_err_median=float(np.median(rel)), rel_err_max=float(rel.max()))
    return inf


def one_trial(seed):
    rng = np.random.default_rng(seed)
    nm = SRCS[seed % len(SRCS)]
    df, names, home = data.load(nm)
    while True:
        nsub = int(rng.integers(30, 100))
        sub = df.sample(nsub, random_state=int(rng.integers(1 << 30)))
        c = cells_from_frame(sub, names, home)
        th = bt.fit(c)
        present = set(np.r_[sub.a.values, sub.b.values].tolist())
        rr = [x for x in bt.ranking(th, c) if x in present]
        pos = int(rng.integers(0, len(rr) - 1))
        i, j = rr[pos], rr[pos + 1]
        if th[i] - th[j] > 1e-6:
            break
    out = {"ds": nm, "n": nsub}
    g = attacks.min_budget(c, i, j, "drop", prune=True)["k"]
    g = int(g) if np.isfinite(g) else 10 ** 9
    out["drop"] = (g, int(attacks.exhaustive_drop_min(c, i, j, kmax=min(KD, g))))
    allow_tie = bool((c.w[c.y == 0.5]).sum() > 0)
    g2 = attacks.min_budget(c, i, j, "flip", prune=True)["k"]
    g2 = int(g2) if np.isfinite(g2) else 10 ** 9
    out["flip"] = (g2, int(attacks.exhaustive_flip_min(c, i, j, kmax=min(KF, g2), allow_tie=allow_tie)))
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    res = {"fit_maxabsdiff_vs_lbfgs": check_fit(), "influence_top30_relerr": check_influence()}
    t0 = time.time()
    with Pool(36) as pool:
        trials = pool.map(one_trial, range(144))
    summ = {}
    for kind, kmax in [("drop", KD), ("flip", KF)]:
        L = [t[kind] for t in trials]
        # exhaustive answer e<=kmax is exact; e=kmax+1 means "more than kmax" (not decided)
        decided = [(g, e) for g, e in L if e <= kmax]
        summ[kind] = dict(n_trials=len(L), kmax=kmax, n_exact_decided=len(decided),
                          greedy_equals_exact=int(sum(g == e for g, e in decided)),
                          greedy_minus_exact_max=int(max([g - e for g, e in decided] + [0])),
                          n_both_exceed_kmax=int(sum(e > kmax for g, e in L)))
    res["greedy_vs_exhaustive"] = summ
    res["greedy_vs_exhaustive_raw"] = trials
    res["seconds_exhaustive"] = time.time() - t0
    json.dump(res, open(os.path.join(OUT, "validation.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "greedy_vs_exhaustive_raw"}, indent=1))
