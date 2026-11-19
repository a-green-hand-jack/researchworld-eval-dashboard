"""Experiment 5: robustness checks and validation of the greedy adversary.
 (a) ridge strength lam  (b) ties dropped  (c) question-clustered bootstrap for MT-Bench
 (d) greedy vs exhaustive search on tiny instances
-> results/robust_*.csv      Run from code/: python run_robust.py"""
import os, itertools
import numpy as np, pandas as pd
import bt
from data import *
from common import *

SEED = 5


def units():
    return {"arena": load_arena(), "mt_human": load_mt_human(), "mt_gpt4": load_mt_gpt4(),
            "nba2010": load_nba_season(2010), "nba2015": load_nba_season(2015)}


def table(cells, rng, B=100, **kw):
    rows, th, order = pair_table(cells, rng, B=B, modes=("remove", "relabel"), **kw)
    return pd.DataFrame(rows)


def cluster_boot_factory(ds):
    g = ds["g"]
    ug, inv = np.unique(g, return_inverse=True)

    def boot(cells, rng):
        # rebuild per-group cell counts from the original votes (cells argument only used for shape)
        G = len(ug)
        pick = rng.integers(0, G, G)
        w = np.bincount(pick, minlength=G)               # multiplicity of each question
        wv = w[inv]                                      # per-vote multiplicity
        n = len(ds["names"])
        a, b, y = ds["a"], ds["b"], ds["y"]
        keep = wv > 0
        return Cells.from_votes(n, np.repeat(a[keep], wv[keep]), np.repeat(b[keep], wv[keep]), np.repeat(y[keep], wv[keep]))
    return boot


def exhaustive_remove(cells, i, j, kmax):
    th0, _ = fit(cells)
    cells_idx = [(p, o) for p in range(len(cells.pa)) for o in range(3) if cells.C[p, o] > 0]
    for k in range(1, kmax + 1):
        for comb in itertools.combinations_with_replacement(range(len(cells_idx)), k):
            C = cells.C.copy(); ok = True
            for t in comb:
                p, o = cells_idx[t]; C[p, o] -= 1
                if C[p, o] < 0: ok = False; break
            if not ok: continue
            t2, _ = fit(Cells(cells.n, cells.pa, cells.pb, C), th0)
            if t2[i] < t2[j]:
                return k
    return np.inf


def exhaustive_relabel(cells, i, j, kmax):
    th0, _ = fit(cells)
    frontier = {cells.C.tobytes(): cells.C}
    seen = set(frontier)
    for k in range(1, kmax + 1):
        new = {}
        for C in frontier.values():
            for p in range(C.shape[0]):
                for o in range(3):
                    if C[p, o] == 0: continue
                    for o2 in range(3):
                        if o2 == o: continue
                        D = C.copy(); D[p, o] -= 1; D[p, o2] += 1
                        key = D.tobytes()
                        if key in seen: continue
                        seen.add(key); new[key] = D
        for D in new.values():
            t2, _ = fit(Cells(cells.n, cells.pa, cells.pb, D), th0)
            if t2[i] < t2[j]:
                return k
        frontier = new
    return np.inf


if __name__ == "__main__":
    U = units()
    # (a) ridge
    out = []
    for lam in (1e-5, 1e-3, 1e-1, 1.0):
        bt.LAM = lam
        for u, ds in U.items():
            rng = np.random.default_rng([SEED, 1, sum(map(ord, u))])
            t = table(cells_of(ds), rng, B=60); t["unit"] = u; t["lam"] = lam; out.append(t)
    bt.LAM = 1e-3
    pd.concat(out).to_csv(os.path.join(RES, "robust_lambda.csv"), index=False)
    # (b) ties dropped
    out = []
    for u in ("arena", "mt_human", "mt_gpt4"):
        ds = U[u]; m = ds["y"] != 0.5
        d2 = dict(names=ds["names"], a=ds["a"][m], b=ds["b"][m], y=ds["y"][m])
        rng = np.random.default_rng([SEED, 2, sum(map(ord, u))])
        t = table(cells_of(d2), rng, B=100); t["unit"] = u; out.append(t)
        t["a"] = [ds["names"][q] for q in t.i]; t["b"] = [ds["names"][q] for q in t.j]
    pd.concat(out).to_csv(os.path.join(RES, "robust_noties.csv"), index=False)
    # (c) cluster bootstrap
    out = []
    for u in ("mt_human", "mt_gpt4"):
        ds = U[u]
        rng = np.random.default_rng([SEED, 3, sum(map(ord, u))])
        t = table(cells_of(ds), rng, B=300, boot_fn=cluster_boot_factory(ds)); t["unit"] = u; out.append(t)
    pd.concat(out).to_csv(os.path.join(RES, "robust_cluster.csv"), index=False)
    # (d) greedy vs exhaustive on tiny random instances
    rng = np.random.default_rng([SEED, 4])
    rows = []
    tries = 0
    while len([r for r in rows if r["mode"] == "remove"]) < 150 and tries < 20000:
        tries += 1
        n = 3
        N = int(rng.integers(20, 40))
        a = rng.integers(0, n, N); b = rng.integers(0, n, N)
        m = a != b; a, b = a[m], b[m]
        y = rng.choice([0.0, 0.5, 1.0], size=len(a), p=[0.4, 0.2, 0.4])
        th_true = np.array([0.5, 0.2, 0.0])
        y = np.where(rng.random(len(a)) < 0.7, (rng.random(len(a)) < bt.sigmoid(th_true[a] - th_true[b])).astype(float), y)
        cells = Cells.from_votes(n, a, b, y)
        if len(cells.pa) < 3: continue
        th, _ = fit(cells); order = ranking(th)
        i, j = order[0], order[1]
        if th[i] - th[j] < 1e-6: continue
        for mode, ex, kmax in (("remove", exhaustive_remove, 6), ("relabel", exhaustive_relabel, 4)):
            kg, _ = greedy_flip(cells, i, j, mode, theta0=th)
            ke = ex(cells, i, j, kmax)
            if np.isfinite(ke):
                rows.append(dict(mode=mode, greedy=kg, exact=ke, N=len(a)))
    pd.DataFrame(rows).to_csv(os.path.join(RES, "robust_greedy_exact.csv"), index=False)
    print(pd.DataFrame(rows).groupby("mode").apply(lambda g: pd.Series(dict(n=len(g), equal=(g.greedy == g.exact).mean(), max_ratio=(g.greedy / g.exact).max(), greedy_lt_exact=(g.greedy < g.exact).sum()))))
