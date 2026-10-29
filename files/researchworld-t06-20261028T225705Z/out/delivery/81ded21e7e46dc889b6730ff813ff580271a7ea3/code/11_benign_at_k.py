"""Benign random removal / label flip at EQUAL size to the verified adversarial budget (m = k and m = 10k) for each decision.
Reads results/decisions_<DS>.csv (replicate -1, influence_exact drop/flip rows). P(decision changes) with Wilson 95% CI over R draws.
Usage: 11_benign_at_k.py DS R -> results/benign_at_k_<DS>.csv"""
import sys, time, numpy as np, pandas as pd, os
from scipy.stats import kendalltau
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsens
ds, R = sys.argv[1], int(sys.argv[2]); res = os.path.dirname(os.path.abspath(__file__)) + "/../results/"
c = rsens.load(ds); N, p = c.n, c.p; th0 = rsens.fit(c); r0 = rsens.ranking(th0, p); pos0 = np.empty(p, int); pos0[r0] = np.arange(p)
d = pd.read_csv(res + f"decisions_{ds}.csv"); d = d[(d.replicate == -1) & d.method.isin(["influence_exact", "influence_exact_greedy"]) & d.perturbation_type.isin(["drop", "flip"]) & d.budget_k.notna()]
rng = np.random.default_rng(11); dec_idx = np.flatnonzero(c.Y != .5); rows = []; t0 = time.time()


def wilson(k, n, z=1.96):
    ph = k / n; dd = 1 + z * z / n; ce = ph + z * z / (2 * n); h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)); return max(0., (ce - h) / dd), min(1., (ce + h) / dd)


def changed(th, dec):
    r = rsens.ranking(th, p); pos = np.empty(p, int); pos[r] = np.arange(p)
    if dec == "top1": return r[0] != r0[0]
    if dec.startswith("topk"): k = int(dec[4:]); return set(r[:k]) != set(r0[:k])
    return kendalltau(pos0, pos).statistic < float(dec[3:])


for _, row in d.iterrows():
    mode, dec, k = row.perturbation_type, row.decision, int(row.budget_k)
    for mult in (1, 10):
        m = min(k * mult, N // 2 if mode == "drop" else len(dec_idx) // 2); hits = []
        for _ in range(R):
            w, Y = np.ones(N), c.Y.copy()
            if mode == "drop": w[rng.choice(N, m, replace=False)] = 0
            else:
                i = rng.choice(dec_idx, m, replace=False); Y[i] = 1 - Y[i]
            hits.append(float(changed(rsens.fit(c.with_Y(Y), w, th0), dec)))
        lo, hi = wilson(sum(hits), R)
        rows.append(dict(dataset=ds, decision=dec, perturbation_type="random_" + mode, adversarial_k=k, multiple=mult, budget_k=m, budget_frac=m / N, p_change=np.mean(hits), ci_lo=lo, ci_hi=hi, n_draws=R, seed=11))
    print(ds, dec, mode, round(time.time() - t0), flush=True); pd.DataFrame(rows).to_csv(res + f"benign_at_k_{ds}.csv", index=False)
