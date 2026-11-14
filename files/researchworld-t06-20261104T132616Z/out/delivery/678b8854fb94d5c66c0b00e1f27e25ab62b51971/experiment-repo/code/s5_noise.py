"""Noise-equivalent budget per claim (paper-repo request #8b): the smallest number k of uniformly random removals that flips the claim
with probability >= 5% (and >= 50%), by Monte Carlo over a grid of k, next to the adversarial budget.

For each unit and each k of a geometric grid (36 values from 0.05% to 98% of N), 200 random removals (multivariate hypergeometric, exact refit)
give the flip frequency of every claim (C1, C2_r, C3_k as defined by Unit.claim_outcomes, so the real claim, not only the argmin pair).
k_noise_p = log-linear interpolation of the first grid crossing of the level p; NaN (censored, 'cap') when the frequency stays below p up to 98% of N.
Writes results/s5_noise.csv. Usage: python code/s5_noise.py [--draws 200]"""
import argparse
import os
import zlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from btlib import analysis as an
from btlib import core, prov
from s1_run import build

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
UNITS_MAIN = ["arena55k", "mt_human", "mt_gpt4", "nba_all", "arena55k_top20count", "nba_all_top20count"]
LEVELS = (0.05, 0.5)


def crossing(ks, p, level):
    """First k (log-linear interpolation) at which the flip frequency p (monotone-ised) reaches `level`."""
    p = np.maximum.accumulate(p)
    idx = np.argmax(p >= level) if (p >= level).any() else None
    if idx is None:
        return np.nan, np.nan
    if idx == 0:
        return float(ks[0]), float(ks[0])
    x0, x1, y0, y1 = np.log(ks[idx - 1]), np.log(ks[idx]), p[idx - 1], p[idx]
    return float(np.exp(x0 + (level - y0) / (y1 - y0) * (x1 - x0))), float(ks[idx])


def work(args):
    name, draws = args
    u = build(name)
    c = u.c
    N = int(c.N)
    ks = np.unique(np.round(N * np.geomspace(0.0005, 0.98, 36)).astype(int))
    ks = ks[ks >= 1]
    claims = ["c1"] + [f"c2_{r}" for r in range(u.W - 1)] + [f"c3_{k}" for k in u.ks]
    freq = np.zeros((len(ks), len(claims)))
    for ki, k in enumerate(ks):
        for s in range(draws):
            rng = np.random.default_rng([5, zlib.crc32(name.encode()), ki, s])
            n2 = an.sample_remove(c, int(k), rng)
            x = core.fit(c.with_n(n2), u.lam, u.lam_h, theta0=u.x0)
            o = u.claim_outcomes(x[: c.K])
            ok = [o["c1"]] + list(o["c2"]) + [o[f"c3_{k_}"] for k_ in u.ks]
            freq[ki] += 1.0 - np.array(ok, dtype=float)
    freq /= draws
    rows = []
    for ci, cl in enumerate(claims):
        r = dict(unit=name, claim=cl, N=N, draws=draws)
        for lv in LEVELS:
            kn, kg = crossing(ks, freq[:, ci], lv)
            r[f"k_noise_{int(lv * 100):02d}"] = kn
            r[f"k_noise_{int(lv * 100):02d}_gridpoint"] = kg
        r["max_flip_freq_grid"] = float(freq[:, ci].max())
        r["flip_freq_at_1pct_N"] = float(np.interp(0.01 * N, ks, freq[:, ci]))
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    d = pd.read_csv(f"{OUT}/budgets_remove.csv")
    names = [n for n in d.unit.unique() if n in UNITS_MAIN or (n.startswith("nba") and n[3:].isdigit())]
    with ProcessPoolExecutor(2) as ex:
        res = list(ex.map(work, [(n, a.draws) for n in names], chunksize=1))
    pd.concat(res, ignore_index=True).to_csv(f"{OUT}/s5_noise.csv", index=False, float_format="%.6g")
    prov.write_meta(f"{OUT}/s5_noise.meta.json", script="code/s5_noise.py", args=vars(a))


if __name__ == "__main__":
    main()
