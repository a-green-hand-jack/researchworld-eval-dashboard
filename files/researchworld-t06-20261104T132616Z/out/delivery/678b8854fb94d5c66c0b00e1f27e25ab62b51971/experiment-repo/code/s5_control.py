"""Arena six-model vs MT-Bench human matched comparison with intervals (paper-repo request #10c).

Both sides have the same six-participant claim structure (C1, C2_0..C2_4 adjacent pairs, C3_3) and N = 1,367 comparisons:
  arena6 : the 1,367 Arena battles among the six models that also appear (as versions) in MT-Bench (the whole such population in the 55k file);
           D draws = bootstrap resamples (with replacement) of these 1,367 battles.
  mt_human: D draws = uniform subsamples of 1,367 of the 3,355 MT-Bench human judgments (without replacement).
Per draw, the verified flip budget of every claim (greedy + polish, prune 10) and the median over the five adjacent-pair claims as a share of N.
Summary: mean / median over draws with a percentile interval over draws, the ratio of the two medians with a bootstrap interval over draws,
the number of independent claims per draw (the five adjacent pairs; C1 = C2_0 and C3_3 are functions of them), and the MINIMUM DETECTABLE RATIO:
the larger of q97.5(r) and 1/q2.5(r) of the ratio r of the two draw-level medians under the null that the draws of both sides come from one
distribution (5,000 label permutations of the pooled draws), i.e. the design effect this comparison can detect at the 5% level.
Writes results/s5_control_draws.csv and results/s5_control_summary.csv.   Usage: python code/s5_control.py [--D 40]"""
import argparse
import os
import zlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from btlib import analysis as an, data, prov, report, units
from s2_controls import ARENA6

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
N = 1367


def draw(args):
    side, d = args
    rng = np.random.default_rng([17, zlib.crc32(side.encode()), d])
    if side == "arena6":
        ds = data.load_arena55k()
        idx = [ds.names.index(m) for m in ARENA6]
        m = np.isin(ds.i, idx) & np.isin(ds.j, idx)
        d6 = ds.subset(m, "arena6")
        remap = {k: n for n, k in enumerate(idx)}
        d6.i = np.array([remap[v] for v in d6.i]); d6.j = np.array([remap[v] for v in d6.j]); d6.names = ARENA6
        assert len(d6) == N, len(d6)
        pick = rng.integers(0, len(d6), N)
        c = d6.counts(rows=pick)
        u = an.Unit(f"arena6_boot{d}", "crowd", c, None, meta=dict(has_ties=True))
    else:
        ds = data.load_mt("human")
        pick = rng.choice(len(ds), N, replace=False)
        c = ds.counts(rows=pick)
        u = an.Unit(f"mt_human_sub{d}", "expert", c, None, meta=dict(has_ties=True))
    t = report.adv_table(u, heur=False, rand=False, oneshot=False, boot=0, raw=False, prune=10.0)
    t["side"], t["draw"], t["N"] = side, d, int(c.N)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--D", type=int, default=40)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    tasks = [(s, d) for s in ("arena6", "mt_human") for d in range(a.D)]
    with ProcessPoolExecutor(a.workers) as ex:
        t = pd.concat(list(ex.map(draw, tasks, chunksize=1)), ignore_index=True)
    t["share"] = t.budget / t.N
    t.drop(columns=["lin_est", "steps", "mode", "strategy"], errors="ignore").to_csv(f"{OUT}/s5_control_draws.csv", index=False, float_format="%.6g")
    rng = np.random.default_rng(23)
    c2 = t[t.claim.str.startswith("c2_")]
    med = c2.groupby(["side", "draw"]).share.median().unstack(0)  # draws x side
    med_all = t[t.claim.isin(["c1"]) | t.claim.str.startswith("c2_")].groupby(["side", "draw"]).share.median().unstack(0)
    rows = []
    for tag, m in (("median of 5 adjacent-pair claims", med), ("median of C1 + 5 adjacent-pair claims", med_all)):
        x, y = m["arena6"].values, m["mt_human"].values
        ratio = np.median(x) / np.median(y)
        bs = [np.median(rng.choice(x, len(x))) / np.median(rng.choice(y, len(y))) for _ in range(5000)]
        pool = np.concatenate([x, y])
        null = []
        for _ in range(5000):
            p = rng.permutation(pool)
            null.append(np.median(p[: len(x)]) / np.median(p[len(x):]))
        q_lo, q_hi = np.percentile(null, [2.5, 97.5])
        for side, v in (("arena6", x), ("mt_human", y)):
            rows.append(dict(statistic=tag, side=side, draws=len(v), N=N, independent_claims_per_draw=5,
                             mean_share=v.mean(), median_share=np.median(v), lo95=np.percentile(v, 2.5), hi95=np.percentile(v, 97.5),
                             median_budget=np.median(v) * N))
        rows.append(dict(statistic=tag, side="ratio arena6/mt_human", draws=len(x), N=N, independent_claims_per_draw=5, median_share=ratio,
                         lo95=np.percentile(bs, 2.5), hi95=np.percentile(bs, 97.5), min_detectable_ratio=max(q_hi, 1 / q_lo),
                         null_q025=q_lo, null_q975=q_hi))
    # claim-level view: the five adjacent-pair claims are the independent units (draw-averaged share per claim, 5 values per side); exact permutation of the 10 values
    cl = c2.groupby(["side", "claim"]).share.mean().unstack(0)
    x, y = cl["arena6"].values, cl["mt_human"].values
    pool = np.concatenate([x, y])
    from itertools import combinations
    null = []
    for comb in combinations(range(10), 5):
        m = np.zeros(10, bool); m[list(comb)] = True
        null.append(np.median(pool[m]) / np.median(pool[~m]))
    q_lo, q_hi = np.percentile(null, [2.5, 97.5])
    for side, v in (("arena6", x), ("mt_human", y)):
        rows.append(dict(statistic="claim level: draw-averaged share of each of the 5 adjacent-pair claims", side=side, draws=5, N=N,
                         independent_claims_per_draw=5, mean_share=v.mean(), median_share=np.median(v), lo95=v.min(), hi95=v.max(), median_budget=np.median(v) * N))
    rows.append(dict(statistic="claim level: draw-averaged share of each of the 5 adjacent-pair claims", side="ratio arena6/mt_human", draws=5, N=N,
                     independent_claims_per_draw=5, median_share=np.median(x) / np.median(y), min_detectable_ratio=max(q_hi, 1 / q_lo), null_q025=q_lo, null_q975=q_hi))
    pd.DataFrame(rows).to_csv(f"{OUT}/s5_control_summary.csv", index=False, float_format="%.5g")
    prov.write_meta(f"{OUT}/s5_control.meta.json", script="code/s5_control.py", D=a.D)
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main()
