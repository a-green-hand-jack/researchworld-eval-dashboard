"""Subsample curves for the normalised scale b50: for subsamples (without replacement) of fraction f of the N comparisons,
probability that a decision differs from the full-data decision (top1, pair at ranks 1-2, pair at ranks 5-6, top-3 set,
Kendall tau < .95/.9). b50 (post-processing, 06_summaries.py) = f where this probability crosses 0.5.
Usage: 05_subsample_b50.py DATASET R   (DATASET may be 'nba_seasons')  ->  results/subsample_<DATASET>.csv"""
import sys, time, numpy as np, pandas as pd, os
from scipy.stats import kendalltau
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsens
ds, R = sys.argv[1], int(sys.argv[2]); res = os.path.dirname(os.path.abspath(__file__)) + "/../results/"
DESIGN = {"arena55k": "crowd", "mtbench_human": "expert", "mtbench_gpt4": "model_judge"}
fracs = np.unique(np.round(np.geomspace(0.002, 0.9, 16), 4)); rng = np.random.default_rng(5); rows = []; t0 = time.time()


def wilson(k, n, z=1.96):
    ph = k / n; d = 1 + z * z / n; ce = ph + z * z / (2 * n); h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return max(0., (ce - h) / d), min(1., (ce + h) / d)


def run(name, c):
    p, N = c.p, c.n; th0 = rsens.fit(c); r0 = rsens.ranking(th0, p); pos0 = np.empty(p, int); pos0[r0] = np.arange(p)
    for f in fracs:
        s = max(2, int(round(f * N))); acc = {}
        for _ in range(R):
            th = rsens.fit(c.subset(rng.choice(N, s, replace=False)), theta0=th0); r = rsens.ranking(th, p)
            pos = np.empty(p, int); pos[r] = np.arange(p); tau = kendalltau(pos0, pos).statistic
            d = {"top1": r[0] != r0[0], "pair12": pos[r0[0]] > pos[r0[1]], "tau<0.95": tau < .95, "tau<0.9": tau < .9}
            if p > 5: d["pair56"] = pos[r0[4]] > pos[r0[5]]
            if p > 3: d["topk3"] = set(r[:3]) != set(r0[:3])
            for k, v in d.items(): acc.setdefault(k, []).append(float(v))
        for k, v in acc.items():
            lo, hi = wilson(sum(v), len(v))
            rows.append(dict(dataset=name, eval_design=DESIGN.get(name, "sports"), N=N, p=p, subsample_frac=f, n_sub=s, decision=k, value=np.mean(v), ci_lo=lo, ci_hi=hi, n_draws=R, seed=5))
    print(name, round(time.time() - t0), flush=True)


if ds == "nba_seasons":
    for y, lg in [(y, "NBA") for y in range(1947, 2016)] + [(y, "ABA") for y in range(1968, 1977)]:
        c = rsens.load(f"nba:{y}" + (":ABA" if lg == "ABA" else ""))
        if c.p >= 8: run(f"nba:{y}" + (":ABA" if lg == "ABA" else ""), c)
else:
    run(ds, rsens.load(ds))
pd.DataFrame(rows).to_csv(res + f"subsample_{ds}.csv", index=False)
