"""Macro (benchmark-averaged) comparisons for Q3, Q5, Q7 from the per-seed metric tables.
For each (split_type, n, method): mean over benchmarks of the per-benchmark seed-mean; percentile bootstrap (B=2000) over seed index
(each replicate resamples seeds, the same seeds for every benchmark; benchmarks are fixed). Paired differences to B1 (random+mean) are computed
within (benchmark, split_type, n, seed) before averaging. Benchmark sets: tier2 = the 7 Tier-2 benchmarks, family = the 4 open-LLM ones.
usage: python analysis_macro.py TIER1_DIR TIER2_DIR TIER3_DIR OUT_DIR"""
import sys, os, numpy as np, pandas as pd

t1, t2, t3, out = sys.argv[1:5]; os.makedirs(out, exist_ok=True)
M = {k: pd.read_csv(os.path.join(d, "metrics_by_seed.csv")) for k, d in (("t1", t1), ("t2", t2), ("t3", t3))}
T2B = sorted(M["t2"].benchmark.unique()); FAMB = sorted(M["t2"][M["t2"].split_type == "family"].benchmark.unique())
BASE = "random+mean"; B = 2000
rng = np.random.default_rng(0)
METS = ["mae", "rmse", "spearman", "kendall"]


def macro(df, benchmarks, base_df=None):
    """df: rows of one (split_type, n, method) cell over benchmarks x seeds -> dict of macro mean/CI (and paired diff if base_df given)."""
    df = df[df.benchmark.isin(benchmarks)]
    piv = {m: df.pivot_table(index="seed", columns="benchmark", values=m) for m in METS}
    seeds = piv["mae"].index
    r = dict(n_benchmarks=piv["mae"].shape[1], n_seeds=len(seeds))
    bi = rng.integers(0, len(seeds), (B, len(seeds)))
    for m in METS:
        v = piv[m].mean(1).values
        r[m] = v.mean(); r[m + "_lo"], r[m + "_hi"] = np.percentile(v[bi].mean(1), [2.5, 97.5])
        if base_df is not None:
            bp = base_df[base_df.benchmark.isin(benchmarks)].pivot_table(index="seed", columns="benchmark", values=m).reindex(seeds)
            d = (piv[m] - bp[piv[m].columns]).mean(1).values
            r[m + "_diff"] = d.mean(); r[m + "_diff_lo"], r[m + "_diff_hi"] = np.percentile(d[bi].mean(1), [2.5, 97.5])
    return r


def table(ms, benchmarks, splits, ns, methods, label):
    rows = []
    for sp in splits:
        for n in ns:
            g = ms[(ms.split_type == sp) & (ms.n == n)]
            if g.empty: continue
            base = g[g.method == BASE]
            for me in methods:
                c = g[g.method == me]
                if c.empty: continue
                rows.append(dict(analysis=label, split_type=sp, n=n, method=me, **macro(c, benchmarks, None if me == BASE else base)))
    return pd.DataFrame(rows)


CORE = ["const", "random+mean", "strat+mean", "random+cal", "anchor+anchor", "anchor+irt", "random+irt", "random+lowrank",
        "strat+lowrank", "random+lowrank_dr", "omp+ridge", "strat+lowrank_dr", "strat+lowrank_eb"]
NS = [20, 50, 100]
# Q3: same 7 (and 4) benchmarks under random, extrapolation and family splits
t1p = M["t1"]
q3 = pd.concat([
    table(t1p, T2B, ["random", "extrap"], NS, CORE, "q3_7bench"),
    table(M["t2"], T2B, ["family"], NS, CORE, "q3_7bench") if False else pd.DataFrame(),
    table(t1p, FAMB, ["random", "extrap"], NS, CORE, "q3_4bench_openllm"),
    table(M["t2"], FAMB, ["family"], NS, CORE, "q3_4bench_openllm")])
q3.to_csv(os.path.join(out, "q3_split_comparison.csv"), index=False)
# Q3b: does the ranking of methods on random splits predict the ranking under shift? (Spearman over methods of macro MAE, n=50)
rows = []
from scipy.stats import spearmanr
for lab, bs in (("4bench_openllm", FAMB),):
    for n in NS:
        d = q3[(q3.analysis == "q3_" + lab.replace("4bench_openllm", "4bench_openllm")) & (q3.n == n)].pivot(index="method", columns="split_type", values="mae")
        d = d.drop(index="const", errors="ignore")
        for other in ("extrap", "family"):
            rows.append(dict(benchmarks=lab, n=n, shifted_split=other, spearman_over_methods_random_vs_shift=spearmanr(d["random"], d[other]).statistic, n_methods=len(d)))
pd.DataFrame(rows).to_csv(os.path.join(out, "q3_method_rank_transfer.csv"), index=False)
# Q5: size of S (10, 20, 40 sources vs all = the Tier-1 split) and 50% targets / duplicates kept, on the 7 Tier-2 benchmarks
q5 = pd.concat([table(t1p, T2B, ["random", "extrap"], NS, CORE, "q5_all_sources"),
                table(M["t2"], T2B, [f"{k}_S{s}" for k in ("random", "extrap") for s in (10, 20, 40)] + ["random_T50", "random_nodedup"], NS, CORE, "q5_S_size_and_targets")])
q5.to_csv(os.path.join(out, "q5_ssize_macro.csv"), index=False)
# Q7a: selector x estimator factorial
fact = M["t2"][M["t2"].split_type.isin(["random_fact", "extrap_fact"])]
methods = sorted(fact.method.unique())
q7 = table(fact, T2B, ["random_fact", "extrap_fact"], NS, methods, "q7_factorial")
q7["selector"] = q7.method.str.split("+").str[0]; q7["estimator"] = q7.method.str.split("+").str[1]
q7.to_csv(os.path.join(out, "q7_factorial_macro.csv"), index=False)
# Q7b: rank / regularisation ablation on the 5 benchmarks of Tier 3
R3 = sorted(M["t3"].benchmark.unique())
q7b = table(M["t3"], R3, ["random_rank", "extrap_rank"], NS, sorted(M["t3"].method.unique()), "q7_rank")
q7b.to_csv(os.path.join(out, "q7_rank_macro.csv"), index=False)
print("done", T2B, FAMB, R3)
