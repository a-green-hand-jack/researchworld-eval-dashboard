"""E6: controlled (paired) comparison of evaluation designs on identical items.

(a) Arena single-turn battles (49,938): crowd labels vs. 5 LLM judges on exactly the same battles.
    For every pair among the crowd's top-12 models we compute, under each labeller, the gap
    (oriented by that labeller's own order), z-score, and the verified minimum number of dropped
    comparisons that reverses the pair.
(b) MT-Bench: expert humans vs. GPT-4 judge, all 15 model pairs; plus 20 random subsamples of
    the human data to the GPT-4 sample size (2,400) as a sample-size control.
Output: artifacts/results/e6_paired.csv
"""
import os
import time
import zlib

import numpy as np
import pandas as pd

from common import LAM, RES, bt, D, pool_map, table

TABLES = {}
SEED = 20261028


def pair_job(args):
    key, pi, pj, tag = args
    tt = TABLES[key]
    idx = {p: k for k, p in enumerate(tt.players)}
    if pi not in idx or pj not in idx:
        return None
    f0 = bt.fit_bt(tt, lam=LAM)
    i, j = idx[pi], idx[pj]
    if f0.theta[i] < f0.theta[j]:
        i, j = j, i
    gap = f0.theta[i] - f0.theta[j]
    se_m, se_s = bt.pair_se(tt, f0, i, j)
    pc = tt.player_counts()
    nij = float(tt.n[((tt.a == i) & (tt.b == j)) | ((tt.a == j) & (tt.b == i))].sum())
    k = 0 if gap <= 1e-8 else bt.min_perturbation(tt, i, j, "drop", lam=LAM, fit0=f0)["k"]
    return dict(dataset=key, tag=tag, pair=f"{min(pi, pj)}|{max(pi, pj)}", higher=tt.players[i], lower=tt.players[j],
                N=tt.N, gap=gap, z_model=gap / se_m, z_sand=gap / se_s, local=pc[i] + pc[j] - nij, k=k)


def main():
    t0 = time.time()
    keys = ["st_crowd"] + ["st_" + j for j in D.JUDGES]
    for k in keys:
        jn = None if k == "st_crowd" else k[3:]
        TABLES[k] = table(D.arena_single_turn(jn)[0])
    f = bt.fit_bt(TABLES["st_crowd"], lam=LAM)
    r = bt.ranking(f.theta, TABLES["st_crowd"].m)
    top = [TABLES["st_crowd"].players[x] for x in r[:12]]
    jobs = [(k, top[a], top[b], "arena_st") for k in keys for a in range(12) for b in range(a + 1, 12)]
    # MT-Bench
    TABLES["mt_human"] = table(D.mtbench("human")[0])
    TABLES["mt_gpt4"] = table(D.mtbench("gpt4")[0])
    mods = TABLES["mt_human"].players
    hum = D.mtbench("human")[0]
    for s in range(20):
        rng = np.random.default_rng(SEED + zlib.crc32(f"mtsub|{s}".encode()) % 10**6)
        sel = rng.choice(len(hum["y"]), size=2400, replace=False)
        TABLES[f"mt_human_sub{s}"] = table({k: (v[sel] if isinstance(v, np.ndarray) else v) for k, v in hum.items()})
    for k in ["mt_human", "mt_gpt4"] + [f"mt_human_sub{s}" for s in range(20)]:
        jobs += [(k, mods[a], mods[b], "mtbench") for a in range(6) for b in range(a + 1, 6)]
    rows = [x for x in pool_map(pair_job, jobs) if x is not None]
    pd.DataFrame(rows).to_csv(os.path.join(RES, "e6_paired.csv"), index=False)
    print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
