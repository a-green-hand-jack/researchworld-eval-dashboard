"""Table F: compute actually used per job. Reads results/compute.csv (T0 and T1 jobs; the T1 scoring job's tokens were not logged, shown '--'). Writes tables/table_f_compute.tex"""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common

c = pd.read_csv(common.path("compute.csv"))
tex = lambda s: str(s).replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")
num = lambda x: "--" if pd.isna(x) else f"{int(x):,}"  # LLM tokens of the scoring job were not logged
num = lambda x: "--" if pd.isna(x) else f"{int(x):,}"  # the T1 scoring job did not log LLM tokens
lines = [r"\begin{tabular}{lrrrrr}", r"\toprule", r"job & wall (s) & cells & replicates & LLM calls & LLM tokens \\", r"\midrule"]
for _, r in c.iterrows():
    lines.append(rf"{tex(r.job)} & {r.wall_seconds:,.0f} & {int(r.cells)} & {int(r.replicates):,} & {num(r.llm_calls)} & {num(r.llm_tokens)} \\")
lines += [r"\midrule", rf"total & {c.wall_seconds.sum():,.0f} & {int(c.cells.sum())} & {int(c.replicates.sum()):,} & {num(c.llm_calls.sum())} & {'--' if c.llm_tokens.isna().any() else num(c.llm_tokens.sum())} \\", r"\bottomrule", r"\end{tabular}"]
open(f"{common.TOUT}/table_f_compute.tex", "w").write("\n".join(lines) + "\n")
print("hardware:", "; ".join(c.hardware.unique()))
