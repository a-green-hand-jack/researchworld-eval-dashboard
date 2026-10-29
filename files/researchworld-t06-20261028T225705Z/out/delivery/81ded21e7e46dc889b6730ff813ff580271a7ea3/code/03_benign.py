"""Benign-noise baselines: random removal of m comparisons, random flip of m decisive comparisons, and full-size bootstrap
resampling. Records decision-change probabilities (Wilson 95% CI), Kendall tau, and per adjacent pair SD of the score
gap change and flip probability. Also the participant table (BT score, bootstrap CI, rank, rank CI).
Usage: 03_benign.py DATASET R  ->  results/benign_<DS>.csv, benign_pairs_<DS>.csv, scores_<DS>.csv"""
import sys, time, numpy as np, pandas as pd, os
from scipy.stats import kendalltau
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsens
DESIGN = {"arena55k": "crowd", "mtbench_human": "expert", "mtbench_gpt4": "model_judge"}
ds, R = sys.argv[1], int(sys.argv[2]); tag = ds.replace(":", "_"); res = os.path.dirname(os.path.abspath(__file__)) + "/../results/"
c = rsens.load(ds); p, N = c.p, c.n; design = DESIGN.get(ds, "sports")
th0 = rsens.fit(c); r0 = rsens.ranking(th0, p); pos0 = np.empty(p, int); pos0[r0] = np.arange(p)
rng = np.random.default_rng(2024); dec = np.flatnonzero(c.Y != .5)
grid = sorted(set(max(1, int(round(N * f))) for f in np.geomspace(2e-4, 0.4, 10)))


def wilson(k, n, z=1.96):
    ph = k / n; d = 1 + z * z / n; ce = ph + z * z / (2 * n); h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return max(0.0, (ce - h) / d), min(1.0, (ce + h) / d)


def summarize(th):
    r = rsens.ranking(th, p); o = dict(top1=float(r[0] != r0[0]), tau=kendalltau(pos0, np.argsort(r)).statistic if False else None)
    pos = np.empty(p, int); pos[r] = np.arange(p); tau = kendalltau(pos0, pos).statistic
    o = {"top1": float(r[0] != r0[0]), "tau": tau, "tau<0.95": float(tau < .95), "tau<0.9": float(tau < .9)}
    for k in (3, 5, 10):
        if p > k: o[f"topk{k}"] = float(set(r[:k]) != set(r0[:k]))
    return o, th[r0[:-1]] - th[r0[1:]], pos


rows, prow = [], []
def record(ptype, m, outs, dphis, flips):
    for key in outs[0]:
        v = np.array([o[key] for o in outs])
        if key == "tau": rows.append(dict(dataset=ds, eval_design=design, perturbation_type=ptype, budget_k=m, budget_frac=m / N, metric="tau_mean", value=v.mean(), ci_lo=np.percentile(v, 2.5), ci_hi=np.percentile(v, 97.5), n_draws=len(v), seed=2024))
        else:
            lo, hi = wilson(v.sum(), len(v)); rows.append(dict(dataset=ds, eval_design=design, perturbation_type=ptype, budget_k=m, budget_frac=m / N, metric="p_" + key, value=v.mean(), ci_lo=lo, ci_hi=hi, n_draws=len(v), seed=2024))
    d = np.array(dphis); base = th0[r0[:-1]] - th0[r0[1:]]
    for i in range(p - 1):
        prow.append(dict(dataset=ds, perturbation_type=ptype, budget_k=m, budget_frac=m / N, pos=i + 1, phi0=base[i], sd_dphi=(d[:, i] - base[i]).std(ddof=1), p_flip=float((d[:, i] <= 0).mean())))


t0 = time.time()
for ptype in ("random_drop", "random_flip"):
    for m in grid:
        outs, dphis = [], []
        for _ in range(R):
            w, Y = np.ones(N), c.Y.copy()
            if ptype == "random_drop": w[rng.choice(N, m, replace=False)] = 0
            else:
                i = rng.choice(dec, min(m, len(dec)), replace=False); Y[i] = 1 - Y[i]
            th = rsens.fit(c.with_Y(Y), w, th0); o, dp, _ = summarize(th); outs.append(o); dphis.append(dp)
        record(ptype, m, outs, dphis, None); print(ds, ptype, m, round(time.time() - t0), flush=True)
outs, dphis, ths, poss = [], [], [], []
for b in range(R):
    cb = c.subset(rng.integers(0, N, N)); th = rsens.fit(cb, theta0=th0)
    o, dp, pos = summarize(th); outs.append(o); dphis.append(dp); ths.append(th[:p] - th[:p].mean()); poss.append(pos)
record("bootstrap", N, outs, dphis, None)
ths, poss = np.array(ths), np.array(poss); cnt = np.bincount(np.r_[c.I, c.J], minlength=p)
pd.DataFrame(dict(dataset=ds, participant=c.names, score=th0[:p] - th0[:p].mean(), ci_lo=np.percentile(ths, 2.5, 0), ci_hi=np.percentile(ths, 97.5, 0), rank=pos0 + 1,
                  rank_lo=np.percentile(poss, 2.5, 0) + 1, rank_hi=np.percentile(poss, 97.5, 0) + 1, n_comparisons=cnt, n_boot=R)).sort_values("rank").to_csv(res + f"scores_{tag}.csv", index=False)
pd.DataFrame(rows).to_csv(res + f"benign_{tag}.csv", index=False); pd.DataFrame(prow).to_csv(res + f"benign_pairs_{tag}.csv", index=False)
print(ds, "done", round(time.time() - t0), flush=True)
