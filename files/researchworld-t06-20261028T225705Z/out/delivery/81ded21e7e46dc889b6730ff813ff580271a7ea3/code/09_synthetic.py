"""SYNTHETIC calibration (RQ4; never a headline result): Bradley-Terry worlds with known scores, uniform random pairing, ties with
probability 0.25 (half-win), N comparisons, p participants, score SD sigma. Records the gap in SE units and worst-case budgets of the
top-1 decision and (p<=20) the cheapest adjacent swap, to see how budgets scale with N, p and the gap.
Usage: 09_synthetic.py R -> results/synthetic.csv"""
import sys, numpy as np, pandas as pd, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsens
res = os.path.dirname(os.path.abspath(__file__)) + "/../results/"; R = int(sys.argv[1]); rng = np.random.default_rng(9); rows = []; t0 = time.time()
for p in (6, 20, 64):
    for N in (2000, 10000, 60000):
        for sigma in (0.3, 1.0):
            reps = R if N < 60000 else max(3, R // 4)
            for rep in range(reps):
                th_true = rng.normal(0, sigma, p); I = rng.integers(0, p, N); J = (I + rng.integers(1, p, N)) % p
                pr = rsens.sigmoid(th_true[I] - th_true[J]); win = rng.random(N) < pr; Y = np.where(rng.random(N) < 0.25, 0.5, win.astype(float))
                c = rsens.Comp([str(i) for i in range(p)], I, J, Y, "synthetic"); th = rsens.fit(c); r = rsens.ranking(th, p)
                q = rsens.qvec(c, r[0], r[1]); z = (th[r[0]] - th[r[1]]) / np.sqrt(q @ np.linalg.inv(rsens.hess(c, th)) @ q)
                true_top = int(np.argmax(th_true)); o = dict(p=p, N=N, sigma=sigma, replicate=rep, seed=9, z_top=z, top1_correct=bool(r[0] == true_top), tau_true=float(__import__("scipy.stats").stats.kendalltau(th, th_true).statistic))
                for m in ("drop", "flip"):
                    o[f"top1_{m}"] = min(rsens.worst_case(c, r[0], r[j], m, th0=th)["k"] for j in (1, 2, 3))
                    if p <= 20: o[f"adjmin_{m}"] = min(rsens.worst_case(c, r[i], r[i + 1], m, th0=th)["k"] for i in range(p - 1))
                rows.append(o)
            print(p, N, sigma, round(time.time() - t0), flush=True); pd.DataFrame(rows).to_csv(res + "synthetic.csv", index=False)
