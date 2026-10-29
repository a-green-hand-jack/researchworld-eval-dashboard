"""E3: non-adversarial perturbations (data noise) -- random dropping, random label flips and the
nonparametric bootstrap -- and the probability that they change the top-1 / top-10 ordering.
Also evaluates random dropping at exactly the adversarial top-1 budget k*_top1 from E1.

Output: artifacts/results/e3_random.csv (one row per replicate) and e3_summary.csv
Usage: python code/exp_e3_random.py   (requires e1_pairs.csv for the matched-budget rows)
"""
import os
import time
import zlib

import numpy as np
import pandas as pd

from common import LAM, RES, bt, D, pool_map, table

TABLES = {}
BASE = {}
ALPHAS = [0.001, 0.005, 0.01, 0.05, 0.1, 0.2]
R = 200
BLOCK = 25
SEED = 20261028


def summarize(theta, base_theta, m, top=10):
    r0 = bt.ranking(base_theta, m)
    r1 = bt.ranking(theta, m)
    R0 = min(top, m)
    top_ids = r0[:R0]
    adj_swaps = int(sum(theta[top_ids[q]] < theta[top_ids[q + 1]] for q in range(R0 - 1)))
    tau = bt.kendall_tau(base_theta[top_ids], theta[top_ids])
    return dict(top1_changed=int(r1[0] != r0[0]), adj_swaps=adj_swaps, tau_top=tau,
                top10_set_changed=int(set(r1[:R0]) != set(r0[:R0])) if m > R0 else 0,
                frac_pairs_swapped=float(np.mean([theta[top_ids[a]] < theta[top_ids[b]] for a in range(R0) for b in range(a + 1, R0)])))


def job(args):
    key, mode, level, block = args
    tt = TABLES[key]
    f0 = BASE[key]
    seed = SEED + zlib.crc32(f"{key}|{mode}|{level}|{block}".encode()) % 10**6
    rng = np.random.default_rng(seed)
    rows = []
    for rep in range(BLOCK):
        if mode == "drop":
            n2 = bt.random_drop_counts(rng, tt.n, round(level * tt.N) if level < 1 else level)
        elif mode == "drop_k":     # absolute budget (matched to adversarial k)
            n2 = bt.random_drop_counts(rng, tt.n, int(level))
        elif mode == "flip":
            n2 = bt.random_flip_counts(rng, tt, tt.n, round(level * tt.N))
        elif mode == "bootstrap":
            n2 = rng.multinomial(int(tt.N), tt.n / tt.N).astype(float)
        f = bt.fit_bt(tt, n2, lam=LAM, theta0=f0.theta)
        row = dict(dataset=key, mode=mode, level=level, seed=seed, rep=block * BLOCK + rep)
        row.update(summarize(f.theta, f0.theta, tt.m))
        rows.append(row)
    return rows


def main():
    ds = D.all_main(include_nba_all=False)
    for k, d in ds.items():
        TABLES[k] = table(d)
        BASE[k] = bt.fit_bt(TABLES[k], lam=LAM)
    kstar = {}
    e1p = os.path.join(RES, "e1_pairs.csv")
    if os.path.exists(e1p):
        e1 = pd.read_csv(e1p)
        e1 = e1[(e1.kind == "drop") & ((e1.pair_type == "leader") | ((e1.pair_type == "adjacent") & (e1.rank_i == 1)))]
        kstar = e1.groupby("dataset").k.min().to_dict()
    jobs = []
    for k in ds:
        for b in range(R // BLOCK):
            for a in ALPHAS:
                jobs.append((k, "drop", a, b))
                jobs.append((k, "flip", a, b))
            jobs.append((k, "bootstrap", 1.0, b))
            if k in kstar and kstar[k] > 0:
                jobs.append((k, "drop_k", int(kstar[k]), b))
    print(len(jobs), "jobs", flush=True)
    t0 = time.time()
    rows = [r for rs in pool_map(job, jobs) for r in rs]
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RES, "e3_random.csv"), index=False)
    g = df.groupby(["dataset", "mode", "level"])
    s = g.agg(n=("top1_changed", "size"), p_top1=("top1_changed", "mean"), mean_adj_swaps=("adj_swaps", "mean"),
              mean_tau=("tau_top", "mean"), p_top10_set=("top10_set_changed", "mean"),
              frac_pairs_swapped=("frac_pairs_swapped", "mean")).reset_index()
    # Wilson 95% interval for p_top1
    z = 1.96
    p, n = s.p_top1, s.n
    den = 1 + z ** 2 / n
    c = (p + z ** 2 / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / den
    s["p_top1_lo"], s["p_top1_hi"] = c - hw, c + hw
    s.to_csv(os.path.join(RES, "e3_summary.csv"), index=False)
    print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
