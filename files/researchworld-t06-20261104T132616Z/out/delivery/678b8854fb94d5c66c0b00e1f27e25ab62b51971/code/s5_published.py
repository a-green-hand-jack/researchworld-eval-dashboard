"""Claims on what a leaderboard publishes (paper-repo request #9a): interval-based claims and their flip budgets.

CI-separated order of an adjacent pair (a above b in the base ranking): the 95% percentile bootstrap interval (2.5%, 97.5% of B=200 resampled
refits, iid resampling of comparisons) of theta_a - theta_b excludes 0.
C1' (rank interval of the top participant): the 97.5th percentile of the bootstrap rank of the base top participant among ALL participants equals 1,
i.e. it keeps the rank interval [1, 1]  (P(rank = 1) >= 0.975).
Budget = smallest number of removed comparisons after which the claim is false when the perturbed counts are RE-BOOTSTRAPPED (same B, same seeds).
Search (an upper bound, stated as such): for the pair, the point-gap search is run with the target 'gap <= t * SE_base' (SE_base = bootstrap SD of the
base gap) for t in a bisection over [0, 2.5], every candidate removal is verified by re-bootstrapping, and the smallest verified one is reported
(t = 0 is the point-gap flip, always falsifies). C1' is searched against the 5 challengers with the smallest base z = gap/SE.
Claims already false on the base data have budget 0.
Writes results/parts/s5_published_<unit>.csv.   Usage: python code/s5_published.py --units arena55k,mt_human,... [--B 200]"""
import argparse
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from btlib import analysis as an
from btlib import core, data, prov, units

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
SEASONS = [1950, 1960, 1970, 1980, 1990, 2000, 2010]
TMAX, ITERS, NCH = 2.5, 4, 5


def build(name):
    if name == "arena55k":
        return units.arena_unit()[0]
    if name in ("mt_human", "mt_gpt4"):
        return units.mt_unit(name[3:])[0]
    if name == "nba_all":
        return units.nba_all_unit()[0]
    return units.nba_season_unit(data.load_nba(), int(name[3:]))[0]


def boot(u, n, B, x_start):
    """(B, K) refits of multinomial resamples of the count tensor n (same seeds for every perturbation)."""
    c = u.c.with_n(n.reshape(-1, 3))
    nf = c.n.ravel()
    out = np.empty((B, c.K))
    for b in range(B):
        rng = np.random.default_rng([7, b])
        s = rng.multinomial(int(nf.sum()), nf / nf.sum()).astype(float).reshape(-1, 3)
        out[b] = core.fit(c.with_n(s), u.lam, u.lam_h, theta0=x_start)[: c.K]
    return out


def pair_sep(Bs, a, b):
    g = Bs[:, a] - Bs[:, b]
    return float(np.percentile(g, 2.5)) > 0, g


def p_top(Bs, a):
    """P(participant a has bootstrap rank 1 among all) and the 97.5th percentile of its rank."""
    rank = 1 + (Bs > Bs[:, [a]]).sum(1)
    return float(np.mean(rank == 1)), float(np.percentile(rank, 97.5))


def bisect_t(u, a, b, se, falsified):
    """Smallest verified removal falsifying the claim; returns (k, t, k at t=0)."""
    c = u.c

    def attempt(t):
        r = core.adversarial_flip(c, a, b, u.lam, mode="remove", x0=u.x0, lam_h=u.lam_h, margin=-t * se)
        if not r["flipped"]:
            return None
        return r["k"], falsified(c.n.ravel() + r["delta"].ravel())

    best, k0 = None, np.nan
    r0 = attempt(0.0)
    if r0 is None:
        return np.nan, np.nan, np.nan
    k0 = r0[0]
    if r0[1]:
        best = (r0[0], 0.0)
    r = attempt(TMAX)
    if r is not None and r[1]:
        return r[0], TMAX, k0
    lo, hi = 0.0, TMAX
    for _ in range(ITERS):
        mid = 0.5 * (lo + hi)
        r = attempt(mid)
        if r is not None and r[1]:
            lo = mid
            if best is None or r[0] < best[0]:
                best = (r[0], mid)
        else:
            hi = mid
    return (best[0], best[1], k0) if best else (np.nan, np.nan, k0)


def work(args):
    name, claim, B = args
    u = build(name)
    c = u.c
    Bs0 = boot(u, c.n.ravel(), B, u.x0)
    o = u.order
    if claim == "c1p":
        a = o[0]
        p1, rhi = p_top(Bs0, a)
        gaps = [(float((u.x0[a] - u.x0[b]) / max(np.std(Bs0[:, a] - Bs0[:, b], ddof=1), 1e-12)), b) for b in o[1:]]
        row = dict(unit=name, claim="c1p", a=c.names[a], p_rank1=p1, rank_hi=rhi, base_holds=p1 >= 0.975)
        if not row["base_holds"]:
            row.update(budget=0, t_used=np.nan, budget_point=0, b=None)
            return [row]
        best = (np.inf, None, np.nan, np.nan)
        for z, b in sorted(gaps)[:NCH]:
            se = float(np.std(Bs0[:, a] - Bs0[:, b], ddof=1))
            k, t, k0 = bisect_t(u, a, b, se, lambda n, a=a: p_top(boot(u, n, B, u.x0), a)[0] < 0.975)
            if k < best[0]:
                best = (k, c.names[b], t, k0)
        row.update(budget=best[0] if np.isfinite(best[0]) else np.nan, b=best[1], t_used=best[2], budget_point=best[3])
        return [row]
    r = int(claim[2:])
    a, b = o[r], o[r + 1]
    sep, g = pair_sep(Bs0, a, b)
    se = float(np.std(g, ddof=1))
    row = dict(unit=name, claim=f"c2ci_{r}", a=c.names[a], b=c.names[b], gap=float(u.x0[a] - u.x0[b]), se_boot=se,
               lo95=float(np.percentile(g, 2.5)), hi95=float(np.percentile(g, 97.5)), base_holds=sep)
    if not sep:
        row.update(budget=0, t_used=np.nan, budget_point=0)
        return [row]
    k, t, k0 = bisect_t(u, a, b, se, lambda n: pair_sep(boot(u, n, B, u.x0), a, b)[0] is False)
    row.update(budget=k, t_used=t, budget_point=k0)
    return [row]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", default="arena55k,mt_human,mt_gpt4,nba_all," + ",".join(f"nba{y}" for y in SEASONS))
    ap.add_argument("--B", type=int, default=200)
    a = ap.parse_args()
    for name in a.units.split(","):
        u = build(name)
        tasks = [(name, "c1p", a.B)] + [(name, f"c2{r}", a.B) for r in range(u.W - 1)]
        with ProcessPoolExecutor(2) as ex:
            res = list(ex.map(work, tasks, chunksize=1))
        df = pd.DataFrame([r for rr in res for r in rr])
        df["N"] = float(u.c.N)
        df["B"] = a.B
        df["frac_N"] = df.budget / df.N
        os.makedirs(f"{OUT}/parts", exist_ok=True)
        df.to_csv(f"{OUT}/parts/s5_published_{name}.csv", index=False, float_format="%.6g")
        prov.write_meta(f"{OUT}/parts/s5_published_{name}.meta.json", script="code/s5_published.py", B=a.B, tmax=TMAX, iters=ITERS, nch=NCH)


if __name__ == "__main__":
    main()
