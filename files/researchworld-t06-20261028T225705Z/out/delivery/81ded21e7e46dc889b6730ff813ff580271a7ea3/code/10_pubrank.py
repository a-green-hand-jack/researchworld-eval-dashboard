"""Arena-convention decision (e): published-style rank = 1 + #{j : CI lower bound of j > CI upper bound of i} (Wald 95% CIs from the
Hessian; the Arena site uses bootstrap CIs, so this is an approximation). Reports, per dataset: how many models have published rank !=
point rank, and what the cheapest verified top-1 drop/flip attack (and the cheapest adjacent-swap attack at ranks 1-2) does to published ranks.
Usage: 10_pubrank.py -> results/pubrank.csv (per-model table at replicate -1) and results/pubrank_summary.csv"""
import sys, numpy as np, pandas as pd, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsens
res = os.path.dirname(os.path.abspath(__file__)) + "/../results/"


def pubrank(c, th, w=None):
    H = rsens.hess(c, th, w); Hinv = np.linalg.inv(H)
    # score differences are identified up to a constant: use SE of each score relative to the mean score
    p = c.p; M = np.eye(c.P)[:p] - 1.0 / p * np.r_[np.ones(p), np.zeros(c.P - p)]
    se = np.sqrt(np.einsum("ij,jk,ik->i", M, Hinv, M)); s = th[:p] - th[:p].mean(); lo, hi = s - 1.96 * se, s + 1.96 * se
    return 1 + np.array([(lo > hi[i]).sum() for i in range(p)]), s, se


rows, summ = [], []
for ds in ("arena55k", "mtbench_human", "mtbench_gpt4", "nba"):
    c = rsens.load(ds); th = rsens.fit(c); pr, s, se = pubrank(c, th); r = rsens.ranking(th, c.p)
    pos = np.empty(c.p, int); pos[r] = np.arange(1, c.p + 1)
    for i in range(c.p): rows.append(dict(dataset=ds, participant=c.names[i], score=s[i], se=se[i], point_rank=pos[i], published_rank=pr[i]))
    for mode in ("drop", "flip"):
        best = None
        for j in (1, 2, 3):
            o = rsens.worst_case(c, r[0], r[j], mode, th0=th)
            if o["w"] is not None and (best is None or o["k"] < best["k"]): best = o
        w, Y = best["w"], best["Y"]; c2 = c.with_Y(Y); th2 = rsens.fit(c2, w, th); pr2, _, _ = pubrank(c2, th2, w); r2 = rsens.ranking(th2, c.p)
        summ.append(dict(dataset=ds, attack=f"top1_{mode}", k=best["k"], new_top1=c.names[r2[0]], old_top1=c.names[r[0]], old_top1_pubrank=pr[r[0]],
                         old_top1_pubrank_after=pr2[r[0]], n_models_pubrank_changed=int((pr != pr2).sum()), n_models_pointrank_changed=int((r != r2).sum() > 0) * int((np.argsort(r) != np.argsort(r2)).sum()),
                         n_top1_pubrank=int((pr == 1).sum()), n_top1_pubrank_after=int((pr2 == 1).sum()), p=c.p))
pd.DataFrame(rows).to_csv(res + "pubrank.csv", index=False); pd.DataFrame(summ).to_csv(res + "pubrank_summary.csv", index=False)
print(pd.DataFrame(summ).to_string())
