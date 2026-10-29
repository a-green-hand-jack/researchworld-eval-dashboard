"""Source-set-size ablation: relative RMSE vs number of source models. Usage: analyze_src.py [OUTDIR]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from load_results import load_all
from stats_util import tensor, boot_rel

OUT = sys.argv[1] if len(sys.argv) > 1 else "/work/paper"
main = load_all("main")
BENCH = ["arc_challenge", "gpqa", "ifeval", "musr", "openllm_math", "mmlu", "gsm"]
main = main[main.bench.isin(BENCH) & (main.seed <= 9) & main.n.isin([25, 100]) & main.protocol.isin(["random", "top"])]
base = main[main.method == "rand/mean"]
METHODS = ["strat/mean", "pps1.0/ridge", "pps1.0/irt4", "pps1.0/greg4", "pps1.0/cal4", "pps1.0/shrcal4"]
NAMES = {"strat/mean": "Difficulty-stratified sampling", "pps1.0/ridge": "VA-PPS + ridge regression", "pps1.0/irt4": "VA-PPS + IRT (pure)",
         "pps1.0/greg4": "VA-PPS + IRT-AIPW", "pps1.0/cal4": "VA-PPS + Cal-IRT", "pps1.0/shrcal4": "VA-PPS + ShrinkCal-IRT"}
dfs = {}
for K in [20, 50, 100]:
    d = load_all(f"src{K}")
    dfs[str(K)] = pd.concat([d, base], ignore_index=True)
dfs["all"] = pd.concat([main[main.method.isin(METHODS)], base], ignore_index=True)
for d in dfs.values():
    d["mse"] = d.rmse ** 2
res = {}
for K, d in dfs.items():
    for p in ["random", "top"]:
        for n in [25, 100]:
            ms = ["rand/mean"] + METHODS
            arr, benches = tensor(d, ms, p, n, "mse")
            pt, lo, hi, _ = boot_rel(arr, 0, B=1000)
            for i, m in enumerate(ms):
                res[(m, p, n, K)] = (pt[i], lo[i], hi[i])
Ks = ["20", "50", "100", "all"]
for n in [25, 100]:
    lines = []
    for m in METHODS:
        cells = [f"{res[(m,p,n,K)][0]:.2f}\\,\\scriptsize({res[(m,p,n,K)][1]:.2f}--{res[(m,p,n,K)][2]:.2f})" for p in ["random", "top"] for K in Ks]
        lines.append(NAMES[m] + " & " + " & ".join(cells) + r" \\")
    tab = ("\\begin{tabular}{l" + "c" * 8 + "}\n\\toprule\n & \\multicolumn{4}{c}{Random split} & \\multicolumn{4}{c}{Stronger targets} \\\\\n & "
           + " & ".join([f"$m$={K}" for _ in range(2) for K in Ks]) + " \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n")
    open(f"{OUT}/tables/src_size_n{n}.tex", "w").write(tab)
pd.Series({"|".join(map(str, k)): v for k, v in res.items()}).to_csv(f"{OUT}/tables/src_size.csv")
print("done")
