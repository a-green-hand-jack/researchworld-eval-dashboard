import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, data
out = sys.argv[1] if len(sys.argv) > 1 else "/work/paper/tables/data.tex"
lines = []
for n in data.ALL:
    Y, o = data.load(n)
    acc = Y.mean(1)
    const = int(((Y.mean(0) == 0) | (Y.mean(0) == 1)).sum())
    lines.append(f"{n.replace('_', ' ')} & {'OLL' if n in data.OPENLLM else 'HELM'} & {Y.shape[0]} & {Y.shape[1]} & {100*acc.mean():.1f} & {100*acc.std():.1f} & {100*acc.min():.1f}--{100*acc.max():.1f} & {const} \\\\")
open(out, "w").write("\\begin{tabular}{llrrrrrr}\n\\toprule\nbenchmark & source & models & items & mean acc. & sd acc. & range & const.\\ items \\\\\n\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n")
