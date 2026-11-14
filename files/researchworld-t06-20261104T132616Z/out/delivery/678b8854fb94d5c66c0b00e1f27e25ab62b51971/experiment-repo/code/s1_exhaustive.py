"""Q6 validity check: exhaustive minimum flip budget on small instances vs the greedy+polish search.

Instances: random subsamples of m comparisons of the MT-Bench human data (K = 6 models, 15 pairs, 45 cells). For each
instance and each adjacent-pair claim (rank r vs r+1 of the base fit) the exact minimum number of removed comparisons
k* (<= KMAX) is found by enumerating all multisets of k removals (batched Newton fits) and compared with
(a) greedy, (b) greedy + polish, (c) one-shot influence ranking, (d) the linearised estimate.
Usage: python code/s1_exhaustive.py [--instances 60] [--m 60,100] [--kmax 5]"""
import argparse
import itertools
import os
import time

import numpy as np
import pandas as pd

from btlib import analysis as an, core, data, prov, units

OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def batch_gap(c, R, a, b, lam, x0, chunk=200_000):
    """Exact theta_a - theta_b after removing the count vectors R (M, cells); batched Newton (K small)."""
    P, K = c.P, c.K
    V = c.V.toarray()  # (P, K)
    n0 = c.n.ravel()
    out = np.empty(len(R))
    for s in range(0, len(R), chunk):
        Rm = R[s:s + chunk]
        n = (n0[None, :] - Rm).reshape(len(Rm), P, 3)
        Np = n.sum(2)
        Wp = n @ core.S_O
        th = np.tile(x0, (len(Rm), 1))
        for it in range(30):
            d = th @ V.T
            sg = core.sigmoid(d)
            g = (Np * sg - Wp) @ V + lam * th
            if np.abs(g).max() < 1e-9:
                break
            w = Np * sg * (1 - sg)
            H = np.einsum("mp,pi,pj->mij", w, V, V) + lam * np.eye(K)[None]
            th = th - np.linalg.solve(H, g[..., None])[..., 0]
        out[s:s + chunk] = th[:, a] - th[:, b]
    return out


def exact_min(c, pairs, lam, x0, kmax):
    """Smallest k <= kmax such that some removal of k comparisons reverses a claim pair; per pair, None if > kmax."""
    cells = np.where(c.n.ravel() > 0)[0]
    cap = c.n.ravel()
    res = {p: None for p in pairs}
    for k in range(1, kmax + 1):
        todo = [p for p in pairs if res[p] is None]
        if not todo:
            break
        it = itertools.combinations_with_replacement(range(len(cells)), k)
        while todo:
            block = list(itertools.islice(it, 150_000))
            if not block:
                break
            combos = np.array(block, dtype=np.int32)
            R = np.zeros((len(combos), len(cap)), dtype=np.float64)
            for t in range(k):
                np.add.at(R, (np.arange(len(combos)), cells[combos[:, t]]), 1.0)
            R = R[np.all(R <= cap[None, :], axis=1)]
            for p in list(todo):
                g = batch_gap(c, R, p[0], p[1], lam, x0)
                if np.any(g <= 0):
                    res[p] = k
                    todo.remove(p)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", type=int, default=60)
    ap.add_argument("--m", default="60,100")
    ap.add_argument("--kmax", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    ds = data.load_mt("human")
    rows = []
    t0 = time.time()
    for m in [int(v) for v in a.m.split(",")]:
        for s in range(a.instances):
            rng = np.random.default_rng([a.seed, m, s])
            idx = rng.choice(len(ds), m, replace=False)
            c = ds.counts(rows=idx)
            u = an.Unit(f"mt_human_sub{m}_{s}", "expert", c, None)
            pairs = [(int(u.order[r]), int(u.order[r + 1])) for r in range(u.E - 1)]
            ex = exact_min(c, pairs, u.lam, u.x0, a.kmax)
            for r, (p, q) in enumerate(pairs):
                g = core.adversarial_flip(c, p, q, u.lam, x0=u.x0, do_polish=False)
                gp = core.adversarial_flip(c, p, q, u.lam, x0=u.x0)
                o = core.adversarial_flip(c, p, q, u.lam, x0=u.x0, strategy="oneshot")
                rows.append(dict(m=m, instance=s, claim=f"c2_{r}", gap=u.base_gap(p, q), exact=ex[(p, q)] if ex[(p, q)] else np.nan,
                                 exact_censored_above=a.kmax if not ex[(p, q)] else np.nan, greedy=g["k"], greedy_polish=gp["k"],
                                 oneshot=o["k"], lin_est=g["est"]))
        print("m", m, "done", time.time() - t0, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "s1_exhaustive.csv"), index=False, float_format="%.6g")
    prov.write_meta(os.path.join(OUT, "s1_exhaustive.meta.json"), script="code/s1_exhaustive.py", args=vars(a))
    v = df[df.exact.notna()]
    print(len(df), "claims;", len(v), "with exact <= kmax")
    for col in ["greedy", "greedy_polish", "oneshot"]:
        print(col, "equal to exact:", np.mean(v[col] == v.exact), "mean excess:", np.mean(v[col] - v.exact), "max excess", (v[col] - v.exact).max(), "never below exact:", np.all(v[col] >= v.exact))


if __name__ == "__main__":
    main()
