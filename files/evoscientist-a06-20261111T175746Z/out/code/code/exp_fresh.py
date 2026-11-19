"""Validation on disjoint 'fresh' questions (E7).

The correctness matrices Y (pool, used for all simulations) and Yf (fresh questions never used for anything else) are
available for the SAME configurations.  We check
 (1) whether simulating 'truth = pool mean' agrees with 'truth = accuracy on fresh questions' for the winner's curse
     of exhaustive search over subsets of the pool (benchmark S of n questions drawn from the pool);
 (2) the one real, un-simulated selection: select the best of all K configs on the full pool, report its pool accuracy,
     measure it on the fresh questions.

python code/exp_fresh.py --m 0.5B
"""
import argparse, json, math, sys
import numpy as np
sys.path.insert(0, "code")
import sel
from common import load_matrix, to_py

ap = argparse.ArgumentParser(); ap.add_argument("--m", required=True); ap.add_argument("--R", type=int, default=2000)
a = ap.parse_args()
name = {"0.5B": "Qwen2.5-0.5B-Instruct", "1.5B": "Qwen2.5-1.5B-Instruct"}[a.m]
Y, meta = load_matrix(f"{name}_fp32"); Yf, metaf = load_matrix(f"{name}_fp32_fresh")
assert Y.shape[0] == Yf.shape[0]
assert meta["configs"] == metaf["configs"], "configs differ"
assert not set(meta["question_id"]) & set(metaf["question_id"]), "pools overlap"
K, N = Y.shape; Nf = Yf.shape[1]
mu, muf = Y.mean(1), Yf.mean(1)
out = dict(model=a.m, K=K, N=N, Nf=Nf)
from scipy import stats
out["corr_pool_fresh"] = float(np.corrcoef(mu, muf)[0, 1]); out["spearman_pool_fresh"] = float(stats.spearmanr(mu, muf)[0])
out["sd_mu_pool"] = float(mu.std(ddof=1)); out["sd_mu_fresh"] = float(muf.std(ddof=1))
slope = np.polyfit(mu, muf, 1); out["slope_fresh_on_pool"] = float(slope[0])
# (2) the one real selection
kb = int(np.argmax(mu)); rank_fresh = int((muf > muf[kb]).sum() + 1)
lo, hi = sel.wilson(muf[kb], Nf)
se_pool = math.sqrt(mu[kb] * (1 - mu[kb]) / N)
out["real_selection"] = dict(best_cfg=kb, pool_acc=float(mu[kb]), fresh_acc=float(muf[kb]), fresh_ci=[float(lo), float(hi)], fresh_rank=rank_fresh,
                             gap=float(mu[kb] - muf[kb]), pool_se=se_pool, best_fresh_acc=float(muf.max()), mean_fresh_acc=float(muf.mean()),
                             mean_pool_acc=float(mu.mean()), lead_pool=float(mu[kb] - mu.mean()), lead_fresh=float(muf[kb] - muf.mean()))
# (1) simulation, two truths
rng = np.random.default_rng(0)
rows = []
for n in (50, 100, 200, 400, 800):
    for Ksub in sorted({2, 4, 8, 16, K}):
        ks, naive, truth_pool = [], [], []
        for _ in range(a.R):
            idx = rng.choice(K, Ksub, replace=False) if Ksub < K else np.arange(K)
            S = rng.integers(0, N, n); Ys = Y[idx][:, S]
            k = sel.opt_exh(Ys, rng)
            ks.append(idx[k]); naive.append(Ys[k].mean()); truth_pool.append(mu[idx[k]])
        ks, naive, truth_pool = np.array(ks), np.array(naive), np.array(truth_pool)
        b_pool = float((naive - truth_pool).mean())
        b_fresh = float((naive - muf[ks]).mean())
        delta = mu.mean() - muf.mean()   # level shift between the two question samples (common to all configs)
        b_fresh_adj = float((naive - (muf[ks] + delta)).mean())
        # bootstrap over fresh questions (fresh-truth noise) and over replicates
        bs, bsa = [], []
        for _ in range(300):
            fi = rng.integers(0, Nf, Nf); mub = Yf[:, fi].mean(1)
            ri = rng.integers(0, a.R, a.R)
            bs.append((naive[ri] - mub[ks[ri]]).mean())
            bsa.append((naive[ri] - (mub[ks[ri]] + mu.mean() - mub.mean())).mean())
        rows.append(dict(n=n, K=Ksub, R=a.R, bias_pool=b_pool, bias_fresh=b_fresh, bias_fresh_ci=[float(np.quantile(bs, .025)), float(np.quantile(bs, .975))],
                         bias_fresh_adj=b_fresh_adj, bias_fresh_adj_ci=[float(np.quantile(bsa, .025)), float(np.quantile(bsa, .975))], level_shift=float(delta),
                         truth_pool=float(truth_pool.mean()), truth_fresh=float(muf[ks].mean())))
out["rows"] = rows
json.dump(to_py(out), open(f"results/fresh_{a.m}.json", "w"))
print(json.dumps(to_py({k: v for k, v in out.items() if k != "rows"}), indent=1))
for r in rows:
    if r["K"] == K:
        print(r)
