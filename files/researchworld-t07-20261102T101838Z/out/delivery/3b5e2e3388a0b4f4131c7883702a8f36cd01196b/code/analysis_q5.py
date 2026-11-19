"""Q5 (second half): does the gain of the proposed estimator over simple sampling depend on benchmark properties?
Descriptive across the 13 benchmarks (n=13, Spearman rank correlation with a bootstrap CI over benchmarks; no causal reading).
usage: python analysis_q5.py SUMMARY_PAIRED_B1.csv OUT.csv [n]   (paired_vs_baseline.csv of tier1, baseline random+mean)"""
import sys, numpy as np, pandas as pd
from scipy.stats import spearmanr
from bpx import data

paired = pd.read_csv(sys.argv[1]); out = sys.argv[2]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 50
props = []
for b in data.BENCHMARKS:
    S, _, _ = data.load(b); M, N = S.shape; q = S.mean(0); acc = S.mean(1)
    s = np.linalg.svd(S - q, compute_uv=False) ** 2
    props.append(dict(benchmark=b, M=M, N=N, model_sd=acc.std(), model_range=np.ptp(acc), mean_acc=acc.mean(),
                      item_p_sd=q.std(), frac_items_mid=float(((q > .2) & (q < .8)).mean()),
                      top8_var_share=float(s[:8].sum() / s.sum()), top1_var_share=float(s[0] / s.sum())))
P = pd.DataFrame(props)
rows = []
for split in ("random", "extrap"):
    for m in ("strat+lowrank_dr", "strat+lowrank_eb", "strat+mean", "random+lowrank"):
        d = paired[(paired.split_type == split) & (paired.n == n) & (paired.method == m)].set_index("benchmark")
        if len(d) < 6: continue
        Q = P.set_index("benchmark").loc[d.index]
        for c in ["M", "N", "model_sd", "model_range", "mean_acc", "item_p_sd", "frac_items_mid", "top8_var_share", "top1_var_share"]:
            r = spearmanr(Q[c], d.mae_diff).statistic
            rng = np.random.default_rng(0); bs = []
            for _ in range(2000):
                i = rng.integers(0, len(d), len(d))
                if len(set(Q[c].values[i])) > 1 and len(set(d.mae_diff.values[i])) > 1: bs.append(spearmanr(Q[c].values[i], d.mae_diff.values[i]).statistic)
            rows.append(dict(split=split, method=m, n=n, property=c, n_benchmarks=len(d), spearman_with_mae_diff=r,
                             lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5)))
pd.DataFrame(rows).to_csv(out, index=False); P.to_csv(out.replace(".csv", "_table.csv"), index=False)
