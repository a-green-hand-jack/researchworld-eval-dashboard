"""E2: how good is the influence-guided search?  Compares, for dropping data, the verified
perturbation sizes found by
  * naive adversaries: (H2H) dropping head-to-head comparisons favourable to the leader of the
    pair in random order; (FAV) dropping any comparison favourable to i or unfavourable to j
    (i's wins, j's losses) in random order (5 seeds, median);
  * one-shot AMIP (influences at the full-data fit, verified by refits);
  * iterative AMIP (influences recomputed after each batch, verified, prefix-pruned) [main];
  * 1-opt local search started from the iterative-AMIP solution (can it be shrunk?);
  * exact exhaustive search, wherever affordable (proves optimality of small k), plus a
    validation on random MT-Bench / NBA sub-instances small enough for exhaustive search.
Output: artifacts/results/e2_search.csv, e2_exact_subinstances.csv
"""
import os
import time
import zlib

import numpy as np
import pandas as pd

from common import LAM, RES, bt, D, pool_map, table

TABLES = {}
SEED = 20261028


def heuristic_k(tt, f0, i, j, which, rng):
    T = len(tt.n)
    ids = []
    for t in np.where(tt.n > 0)[0]:
        a, b, y = tt.a[t], tt.b[t], tt.y[t]
        if which == "h2h":
            if (a == i and b == j and y == 1.0) or (a == j and b == i and y == 0.0):
                ids += [t] * int(tt.n[t])
        else:
            fav = ((a == i and y == 1.0) or (b == i and y == 0.0) or (a == j and y == 0.0) or (b == j and y == 1.0))
            if fav:
                ids += [t] * int(tt.n[t])
    if not ids:
        return None
    ids = np.array(ids)
    rng.shuffle(ids)
    moves = [(int(t), -1, 1.0) for t in ids]
    return bt._min_prefix(tt, tt.n, moves, len(moves), i, j, LAM, f0.theta, lo_hint=0)


def flips(tt, n, i, j, f0):
    f = bt.fit_bt(tt, n, lam=LAM, theta0=f0.theta)
    return f.theta[i] - f.theta[j] < 0


def one_opt(tt, f0, moves, i, j):
    """Backward elimination: try to un-drop one comparison of each used type while keeping the flip."""
    cnt = {}
    for s, d, c in moves:
        cnt[s] = cnt.get(s, 0) + c
    improved = True
    while improved:
        improved = False
        for t in sorted(cnt, key=lambda x: cnt[x]):
            if cnt[t] <= 0:
                continue
            cnt[t] -= 1
            n2 = tt.n.copy()
            for s, c in cnt.items():
                n2[s] -= c
            if flips(tt, n2, i, j, f0):
                improved = True
            else:
                cnt[t] += 1
    return int(sum(cnt.values()))


def exact_check(tt, f0, i, j, k_greedy, max_combos=3_000_000):
    """Return (k_exact or None, status). Exhaustively searches all drop multisets of size < k_greedy
    when affordable; status in {'optimal', 'improved', 'skipped'}."""
    if k_greedy is None:
        return None, "skipped"
    if k_greedy == 1:
        return 1, "optimal"
    from math import comb
    nt = int(np.sum(tt.n > 0))
    kmax = k_greedy - 1
    if comb(nt + kmax - 1, kmax) > max_combos:
        return None, "skipped"
    ex = bt.exact_min_drop(tt, i, j, kmax=kmax, lam=LAM, fit0=f0)
    if ex is None:
        return k_greedy, "optimal"
    return ex, "improved"


def pair_job(args):
    key, i, j, ptype = args
    tt = TABLES[key]
    f0 = bt.fit_bt(tt, lam=LAM)
    t0 = time.time()
    res = bt.min_perturbation(tt, i, j, kind="drop", lam=LAM, fit0=f0)
    t_amip = time.time() - t0
    rng = np.random.default_rng(SEED + zlib.crc32(f"{key}|{i}|{j}".encode()) % 10**6)
    h2h = heuristic_k(tt, f0, i, j, "h2h", rng)
    favs = [heuristic_k(tt, f0, i, j, "fav", rng) for _ in range(5)]
    favs_ok = [x for x in favs if x is not None]
    k1 = one_opt(tt, f0, res["moves"], i, j) if res["moves"] else None
    kex, status = exact_check(tt, f0, i, j, res["k"], max_combos=200_000 if tt.N > 5000 else 3_000_000)
    return dict(dataset=key, pair_type=ptype, i=tt.players[i], j=tt.players[j], N=tt.N,
                k_iter_amip=res["k_iter"], k_oneshot_amip=res["k_oneshot"], k_best=res["k"], k_pred=res["k_pred"],
                k_h2h=h2h, k_fav_median=float(np.median(favs_ok)) if favs_ok else None,
                k_fav_min=min(favs_ok) if favs_ok else None, fav_fail=len(favs) - len(favs_ok),
                k_1opt=k1, k_exact=kex, exact_status=status, sec_amip=t_amip, sec_total=time.time() - t0)


def sub_job(args):
    """Random sub-instance small enough for exact search."""
    src, N_sub, rep = args
    d = SUBSRC[src]
    rng = np.random.default_rng(SEED + zlib.crc32(f"sub|{src}|{N_sub}|{rep}".encode()) % 10**6)
    idx = rng.choice(len(d["y"]), size=N_sub, replace=False)
    sub = {k: (v[idx] if isinstance(v, np.ndarray) else v) for k, v in d.items()}
    tt = table(sub)
    f0 = bt.fit_bt(tt, lam=LAM)
    r = bt.ranking(f0.theta, tt.m)
    rows = []
    for q in range(min(tt.m, 6) - 1):
        i, j = int(r[q]), int(r[q + 1])
        if f0.theta[i] - f0.theta[j] <= 1e-8:
            continue
        res = bt.min_perturbation(tt, i, j, kind="drop", lam=LAM, fit0=f0)
        kg = res["k"]
        if kg is None or kg > 4:
            rows.append(dict(src=src, N_sub=N_sub, rep=rep, rank=q + 1, k_greedy=kg, k_oneshot=res["k_oneshot"], k_exact=None, status="too_large"))
            continue
        kex, status = exact_check(tt, f0, i, j, kg, max_combos=500_000)
        rows.append(dict(src=src, N_sub=N_sub, rep=rep, rank=q + 1, k_greedy=kg, k_oneshot=res["k_oneshot"], k_exact=kex, status=status))
    return rows


SUBSRC = {}


def main():
    ds = D.all_main(include_nba_all=False)
    for k, d in ds.items():
        TABLES[k] = table(d)
    jobs = []
    for k in ds:
        tt = TABLES[k]
        f0 = bt.fit_bt(tt, lam=LAM)
        r = bt.ranking(f0.theta, tt.m)
        R = min(10, tt.m)
        for q in range(R - 1):
            jobs.append((k, int(r[q]), int(r[q + 1]), "adjacent"))
        for q in range(2, R):
            jobs.append((k, int(r[0]), int(r[q]), "leader"))
    jobs.sort(key=lambda t: -TABLES[t[0]].N)
    t0 = time.time()
    rows = pool_map(pair_job, jobs)
    pd.DataFrame(rows).to_csv(os.path.join(RES, "e2_search.csv"), index=False)
    print(f"pairs done {time.time() - t0:.0f}s", flush=True)
    SUBSRC["mt_human"] = ds["mt_human"]
    SUBSRC["mt_gpt4"] = ds["mt_gpt4"]
    SUBSRC["nba2015"] = ds["nba2015"]
    sjobs = [(s, nsub, rep) for s in ("mt_human", "mt_gpt4") for nsub in (100, 200) for rep in range(30)]
    sjobs += [("nba2015", 300, rep) for rep in range(30)]
    srows = [r for rs in pool_map(sub_job, sjobs) for r in rs]
    pd.DataFrame(srows).to_csv(os.path.join(RES, "e2_exact_subinstances.csv"), index=False)
    print(f"all done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
