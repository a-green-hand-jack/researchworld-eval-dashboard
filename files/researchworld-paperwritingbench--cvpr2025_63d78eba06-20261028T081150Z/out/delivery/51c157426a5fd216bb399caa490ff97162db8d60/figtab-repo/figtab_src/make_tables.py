"""Writes tables/*.tex (booktabs fragments, no extra packages) from data.py."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from data import *

OUT = os.path.join(os.path.dirname(__file__), '..', 'tables')
H = r"Test & Remain. & Forget & MIA"

INT = True  # the log reports integer accuracies for CIFAR-10; do not imply extra precision

def f(x):
    if INT and abs(x - round(x)) < 1e-9:
        return f"{int(round(x))}"
    return f"{x:.1f}"

def row(label, v, bold=False):
    cells = [f(x) for x in v]
    if bold:
        cells = [r"\textbf{%s}" % c for c in cells]
    return f"{label} & " + " & ".join(cells) + r" \\"

def grow(label, g):
    return r"\;\;$\Delta$ " + label + " & " + " & ".join(f(x) for x in g) + r" \\"

def write(name, body):
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write(body)

# ---- forget-size ablation
L = [r"\begin{table}[t]", r"  \centering", r"  \small", r"  \setlength{\tabcolsep}{4pt}",
     r"  \begin{tabular}{@{}llcccc@{}}", r"    \toprule",
     r"    Forget & Model & " + H.replace("Test", "Test", 1) + r" \\", r"    \midrule"]
for i, (s, (r, u)) in enumerate(sorted(FORGET.items())):
    L.append(f"    \\multirow{{3}}{{*}}{{{s}\\%}}" if False else f"    {s}\\% & Retrained & " + " & ".join(f(x) for x in r) + r" \\")
    L.append("     & Unlearned($-$) & " + " & ".join(f(x) for x in u) + r" \\")
    L.append("     & $\\Delta$ & " + " & ".join(f(x) for x in gap(r, u)) + r" \\")
    if i < len(FORGET) - 1:
        L.append(r"    \midrule")
L += [r"    \bottomrule", r"  \end{tabular}",
      r"  \caption{Forget-set size on CIFAR-10 (linear classifier on ResNet-18 features). The 10\% row coincides with the 500-perturbation, $\lambda{=}0$ row of \cref{tab:ablations}; the perturbation count and $\lambda$ used for the 5\% and 15\% rows are not recorded in the log. "
      r"Accuracies and MIA score in \%; $\Delta$ is the absolute difference to Retrained in percentage points (ideal: 0 on all metrics, MIA 50). "
      r"Single run per setting. The gap is 0 at 5\% (at the log's whole-percent resolution, i.e.\ below about 0.5 points) and grows to 14--15 points at 15\%, where Unlearned($-$) clearly degrades.}",
      r"  \label{tab:forget_size}", r"\end{table}", ""]
write("forget_size.tex", "\n".join(L))

# ---- perturbations + lambda in one table
L = [r"\begin{table}[t]", r"  \centering", r"  \small", r"  \setlength{\tabcolsep}{4pt}",
     r"  \begin{tabular}{@{}llcccc@{}}", r"    \toprule",
     r"    Setting & Model & " + H + r" \\", r"    \midrule",
     r"    --- & Retrained & " + " & ".join(f(x) for x in PERT_RETRAINED) + r" \\", r"    \midrule"]
for i, (n, v) in enumerate(sorted(PERT.items())):
    L.append(f"    $n{{=}}{n}$ & Unlearned($-$) & " + " & ".join(f(x) for x in v) + r" \\")
    L.append("     & $\\Delta$ & " + " & ".join(f(x) for x in gap(PERT_RETRAINED, v)) + r" \\")
L.append(r"    \midrule")
for i, (l, v) in enumerate(sorted(LAM.items())):
    lab = "0" if l == 0 else ("5{\\times}10^{-4}" if l == 0.0005 else "10^{-3}")
    L.append(f"    $\\lambda{{=}}{lab}$ & Unlearned($-$) & " + " & ".join(f(x) for x in v) + r" \\")
    L.append("     & $\\Delta$ & " + " & ".join(f(x) for x in gap(LAM_RETRAINED, v)) + r" \\")
L += [r"    \bottomrule", r"  \end{tabular}",
      r"  \caption{Ablations on CIFAR-10 (10\% forget set). Top: number of random perturbations $n$ used to estimate the Hessian; "
      r"bottom: $\ell_2$ regularisation $\lambda$. The $n{=}500$ and $\lambda{=}0$ rows are identical to each other and to the 10\% row of \cref{tab:forget_size} (one shared configuration); "
      r"the value of the other factor in the remaining rows is not recorded in the log. "
      r"Accuracies and MIA score in \%; $\Delta$ is the absolute difference to Retrained in percentage points. Single run per setting; "
      r"the MIA gap is not monotone in $\lambda$ (0.2 at $5{\times}10^{-4}$, 0.9 at $10^{-3}$).}",
      r"  \label{tab:ablations}", r"\end{table}", ""]
write("ablations.tex", "\n".join(L))

# ---- mixed linear network (log gives one decimal throughout)
INT = False
L = [r"\begin{table}[t]", r"  \centering", r"  \small", r"  \setlength{\tabcolsep}{4pt}",
     r"  \begin{tabular}{@{}llcccc@{}}", r"    \toprule",
     r"    Forget & Model & " + H + r" \\", r"    \midrule"]
for i, (s, (r, p, m)) in enumerate(sorted(MIXED.items(), reverse=True)):
    L.append(f"    {s}\\% & Retrained & " + " & ".join(f(x) for x in r) + r" \\")
    L.append("     & Unlearned($+$) & " + " & ".join(f(x) for x in p) + r" \\")
    L.append("     & Unlearned($-$) & " + " & ".join(f(x) for x in m) + r" \\")
    L.append("     & $\\Delta$ vs.\\ Retrained & " + " & ".join(f(x) for x in gap(r, m)) + r" \\")
    L.append("     & $\\Delta$ vs.\\ Unlearned($+$) & " + " & ".join(f(x) for x in gap(p, m)) + r" \\")
    if i < len(MIXED) - 1:
        L.append(r"    \midrule")
L += [r"    \bottomrule", r"  \end{tabular}",
      r"  \caption{Mixed linear network (last layers of ResNet-18 linearised) on CIFAR-100. Accuracies and MIA score in \%; "
      r"$\Delta$ rows are absolute differences of Unlearned($-$) to the named reference in percentage points. "
      r"Unlearned($-$) tracks Unlearned($+$) closely on test accuracy ($\le$0.5) but its remaining accuracy (70.0, 70.1, 70.1 across sizes) is above Retrained's at 20\% and 15\% (70.0 vs.\ 65.7; 70.1 vs.\ 68.9) and below it at 10\% (70.1 vs.\ 72.0). Single run per setting.}",
      r"  \label{tab:mixed}", r"\end{table}", ""]
write("mixed_linear.tex", "\n".join(L))

# ---- source-free baselines (mixed precision in the log: one decimal)
INT = False
best = {}
L = [r"\begin{table}[t]", r"  \centering", r"  \small", r"  \setlength{\tabcolsep}{4pt}",
     r"  \begin{tabular}{@{}lcccc@{}}", r"    \toprule", r"    Method & " + H + r" \\", r"    \midrule"]
for i, (n, v) in enumerate(BASE):
    if i == 1:
        L.append(r"    \midrule")
    if i == len(BASE) - 1:
        L.append(r"    \midrule")
    L.append("    " + row(n, v))
L += [r"    \bottomrule", r"  \end{tabular}",
      r"  \caption{Source-free unlearning baselines on CIFAR-10 (linear classifier, 10\% forget set). Accuracies and MIA score in \%. "
      r"Retrained (top) is the reference: an ideal method matches its accuracies and has MIA 50. "
      r"Unlearned($-$) is closest to Retrained on all three accuracies, while the baselines lose 20--51 points of test accuracy. "
      r"MIA scores (47--51.4) do not separate the methods; Unlearned($-$)'s is farther from 50 than JiT's and Adversarial's. Single run.}",
      r"  \label{tab:baselines}", r"\end{table}", ""]
write("baselines.tex", "\n".join(L))
