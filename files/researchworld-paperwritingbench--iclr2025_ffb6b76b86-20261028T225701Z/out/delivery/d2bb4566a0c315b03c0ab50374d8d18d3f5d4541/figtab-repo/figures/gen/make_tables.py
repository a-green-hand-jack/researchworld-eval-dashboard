"""Writes tables/table_{1..4}.tex (body of each table environment) from gen/data.py."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from data import *

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "tables")
DASH = "--"

def cell(v, best=None, fmt="{:.1f}"):
    if v is None:
        return DASH
    s = fmt.format(v)
    return "\\textbf{%s}" % s if best is not None and abs(v - best) < 1e-9 else s

def write(name, text):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(text)

# ---- Table 1 -------------------------------------------------------------
best = [max(v for r in T1 for v in [r[1][i]] if v is not None) for i in range(4)]
rows = []
for name, vals in T1:
    rows.append(name + " & " + " & ".join(cell(v, best[i]) for i, v in enumerate(vals)) + " \\\\")
rows.insert(3, "\\midrule")  # separate baselines from the proposed method
write("table_1.tex", r"""\begin{table}[t]
\caption{Pass rates (\%) on the HumanEval Random Span infilling benchmark with CodeLlama-7b. PSM and SPM are the two infilling prompt templates; ``@10'' is pass@10. Healing and alignment are only applied in SPM mode (--: not applicable). Best per column in bold.}
\label{tab:fim}
\begin{center}
\begin{tabular}{lcccc}
\toprule
 & \multicolumn{2}{c}{PSM} & \multicolumn{2}{c}{SPM} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Method & Greedy & @10 & Greedy & @10 \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{center}
\end{table}
""")

# ---- Table 2 -------------------------------------------------------------
best2 = {}
for b in T2_BENCH:
    cands = [x for m in T2.values() for x in m[b]] + [T2_ENS[b]]
    best2[b] = max(cands)
rows = []
for m, d in T2.items():
    rows.append("%s & Token & %s \\\\" % (m, " & ".join(cell(d[b][0], best2[b]) for b in T2_BENCH)))
    rows.append(" & Byte & %s \\\\" % " & ".join(cell(d[b][1], best2[b]) for b in T2_BENCH))
    rows.append("\\addlinespace[2pt]")
rows[-1] = "\\midrule"
rows.append("Top-2 voting & Byte & %s \\\\" % " & ".join(cell(T2_VOTE[b], best2[b]) for b in T2_BENCH))
rows.append("Top-2 ensemble (ours) & Byte & %s \\\\" % " & ".join(cell(T2_ENS[b], best2[b]) for b in T2_BENCH))
write("table_2.tex", r"""\begin{table}[t]
\caption{Accuracy (\%) of open-weight general-purpose LMs using standard token-level prediction (Token) and our byte-level prediction (Byte), and of top-2 ensembles (byte-level average of the two best-performing models, selected per benchmark). Voting was only reported for MMLU and PIQA (--: not reported). Best per benchmark in bold. Single evaluation per cell; no confidence intervals are available.}
\label{tab:general}
\begin{center}
\small
\setlength{\tabcolsep}{4.5pt}
\begin{tabular}{llccccc}
\toprule
Model & Level & """ + " & ".join(T2_BENCH) + r""" \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{center}
\end{table}
""")

# ---- Table 3 -------------------------------------------------------------
best3 = {b: max([x for m in T3.values() for x in m[b]] + [T3_ENS[b]]) for b in T3_BENCH}
rows = []
for m, d in T3.items():
    rows.append("%s & Token & %s \\\\" % (m, " & ".join(cell(d[b][0], best3[b]) for b in T3_BENCH)))
    rows.append(" & Byte & %s \\\\" % " & ".join(cell(d[b][1], best3[b]) for b in T3_BENCH))
    rows.append("\\addlinespace[2pt]")
rows[-1] = "\\midrule"
rows.append("Top-2 ensemble (ours) & Byte & %s \\\\" % " & ".join(cell(T3_ENS[b], best3[b]) for b in T3_BENCH))
write("table_3.tex", r"""\begin{table}[t]
\caption{Pass@1 (\%) of code LMs with token-level and byte-level prediction, and of the top-2 byte-level ensemble. Top-2 ensemble: byte-level average of the two best-performing models, selected per benchmark; on HumanEval the pair is Yi-Coder-1.5B and CodeLlama-13b. On MBPP the ensemble ties the best single model (Yi-Coder-1.5B, byte-level). Single evaluation per cell; no confidence intervals are available. Best per benchmark in bold.}
\label{tab:code}
\begin{center}
\small
\begin{tabular}{llcc}
\toprule
Model & Level & HumanEval & MBPP \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{center}
\end{table}
""")

# ---- Table 4 -------------------------------------------------------------
b_psm = max(r[1] for r in T4); b_spm = max(r[2] for r in T4)
rows = ["%d & %s & %s \\\\" % (w, cell(p, b_psm), cell(s, b_spm)) for w, p, s in T4]
write("table_4.tex", r"""\begin{table}[t]
\caption{FIM pass rate (\%) on HumanEval for byte-level predictions versus beam width; width 1 equals the byte-level greedy entries of Table~\ref{tab:fim}. Best per column in bold.}
\label{tab:beam}
\begin{center}
\begin{tabular}{lcc}
\toprule
Beam width & PSM & SPM \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{center}
\end{table}
""")
print("ok")
