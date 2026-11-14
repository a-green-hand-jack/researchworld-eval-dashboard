"""Stage 0: base fits, bootstrap intervals, fitter validation, dataset summary.
Outputs: results/base_<unit>.csv, results/dataset_summary.csv, results/validation_fitter.csv (+ .meta.json)
Usage: python code/s0_base.py [--B 1000]"""
import argparse
import os
import time

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from btlib import analysis as an, core, data, prov, units

ELO = 400 / np.log(10)
OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def sk_fit(c, lam=1.0):
    """Independent fit: scikit-learn L-BFGS on an expanded row-level design (ties = two half-weight rows)."""
    ti, tj, n = c.ti, c.tj, c.n
    X, Y, W = [], [], []
    for o, (lab, wt) in enumerate([((1,), 1.0), ((1, 0), 0.5), ((0,), 1.0)]):
        for l in lab:
            m = n[:, o] > 0
            M = np.zeros((m.sum(), c.D))
            r = np.arange(m.sum())
            M[r, ti[m]] = 1; M[r, tj[m]] = -1
            if c.home:
                M[:, c.K] = c.th[m]
            X.append(M); Y.append(np.full(m.sum(), l)); W.append(n[m, o] * wt)
    X, Y, W = np.vstack(X), np.concatenate(Y), np.concatenate(W)
    lr = LogisticRegression(C=1.0 / lam, fit_intercept=False, tol=1e-12, max_iter=20000)
    return lr, X, Y, W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    arena, ads = units.arena_unit()
    mth, _ = units.mt_unit("human")
    mtg, _ = units.mt_unit("gpt4")
    nba_all, nba = units.nba_all_unit()
    us = [arena, mth, mtg, nba_all]
    seasons = sorted(set(nba.season))
    us += [units.nba_season_unit(nba, y)[0] for y in seasons[:0]]  # per-season summaries are in the budget stage
    summ, val = [], []
    for u in us:
        t = time.time()
        c = u.c
        cnt = c.participant_counts()
        B = analysis_bs = an.bootstrap_fits(u, a.B, a.seed)
        th = u.x0[: c.K]
        lo, hi = np.percentile(B, [2.5, 97.5], axis=0)
        # rank intervals among eligible participants
        # (claims window: the top-W ranks among all participants; ranks and rank intervals are among all u.E participants)
        Be = B[:, u.elig]
        rk = (-Be).argsort(1).argsort(1) + 1
        rlo, rmed, rhi = np.percentile(rk, [2.5, 50, 97.5], axis=0)
        base_rank = np.empty(len(u.elig), int)
        base_rank[np.argsort(-th[u.elig], kind="stable")] = np.arange(1, len(u.elig) + 1)
        keep = np.where(base_rank <= u.W)[0]
        mem = u.elig[keep]
        rlo, rmed, rhi, base_rank = rlo[keep], rmed[keep], rhi[keep], base_rank[keep]
        df = pd.DataFrame(dict(participant=[c.names[k] for k in mem], n_comparisons=cnt[mem].astype(int),
                               score_elo=th[mem] * ELO, ci_lo_elo=lo[mem] * ELO, ci_hi_elo=hi[mem] * ELO,
                               se_elo=B.std(0, ddof=1)[mem] * ELO, rank=base_rank,
                               rank_lo=rlo, rank_median=rmed, rank_hi=rhi)).sort_values("rank")
        df.to_csv(os.path.join(OUT, f"base_{u.name}.csv"), index=False, float_format="%.6g")
        # validation against the independent implementation
        lr, X, Y, W = sk_fit(c, 1.0)  # lam = 1 as in units
        lr.fit(X, Y, sample_weight=W)
        d = np.abs(lr.coef_[0] - u.x0).max()
        # rank agreement and recentred difference
        val.append(dict(unit=u.name, K=c.K, N=int(c.N), max_abs_diff_theta=d, rank_identical=bool(np.array_equal(np.argsort(-lr.coef_[0]), np.argsort(-u.x0))),
                        newton_seconds=None))
        # ties
        cell = c.n.sum(0)
        ties = cell[1]
        pt = np.array(list(c.pair_totals().values()))
        summ.append(dict(unit=u.name, design=u.design, K=c.K, K_eligible=u.W, K_elig_challengers=u.E, N=int(c.N), n_pairs_compared=len(pt),
                         n_pairs_possible=c.K * (c.K - 1) // 2, tie_frac=ties / c.N,
                         pair_count_median=float(np.median(pt)), pair_count_min=int(pt.min()), pair_count_max=int(pt.max()),
                         comps_per_participant_median=float(np.median(cnt)), bootstrap_B=a.B, seconds=time.time() - t))
        print(u.name, "done", time.time() - t, "sk diff", d, flush=True)
    pd.DataFrame(summ).to_csv(os.path.join(OUT, "dataset_summary.csv"), index=False, float_format="%.6g")
    pd.DataFrame(val).drop(columns="newton_seconds").to_csv(os.path.join(OUT, "validation_fitter.csv"), index=False, float_format="%.6g")
    prov.write_meta(os.path.join(OUT, "s0_base.meta.json"), script="code/s0_base.py", args=vars(a), lam=1.0)


if __name__ == "__main__":
    main()
