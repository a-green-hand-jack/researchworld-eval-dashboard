"""Table 1 (static): scores and calibration schemes compared.  Definitions follow experiment-repo/results/README.md (method names in the CSVs)."""
from common import *

rows = [
    (r"$L_2$ (Brier)", "l2", r"$\|y-\hat y\|_2$", "none"),
    (r"$L_1$ (=2 TV)", "l1", r"$\|y-\hat y\|_1$", "none"),
    (r"$L_\infty$", "linf", r"$\|y-\hat y\|_\infty$", "none"),
    ("Hellinger", "hell", r"$\|\sqrt y-\sqrt{\hat y}\|_2$", "none"),
    ("KL", "kl", r"$\mathrm{KL}(y\,\|\,\hat y)$", r"$\hat y$ ($\varepsilon$)"),
    ("Aitchison", "ait", r"$\|\mathrm{clr}(y)-\mathrm{clr}(\hat y)\|_2$", r"$y,\hat y$ ($\varepsilon$, then closure)"),
    ("Dirichlet NLL", "nll", r"$-\log \mathrm{Dir}(y;\hat\phi\hat y)$", r"$y$ ($\varepsilon$)"),
]
lines = [r"\begin{tabular}{llll}", r"\toprule", r"score & name in results & definition & zero replacement \\ \midrule"]
for a, b, c, d in rows:
    lines.append(f"{a} & \\texttt{{{b}}} & {c} & {d} \\\\")
lines += [r"\midrule",
          r"\multicolumn{4}{l}{Calibration schemes (E1): split (\texttt{<score>}); locally normalised, score$/\hat\sigma(x)$ (\texttt{<score>\_n}); Mondrian by argmax of $\hat y$ (\texttt{<score>\_m});} \\",
          r"\multicolumn{4}{l}{CV+ with $L_2$ (\texttt{cvp\_l2}, linear predictor only).  Label sets (E2): LAC, APS, RAPS, and the scores above evaluated at vertices.} \\",
          r"\bottomrule", r"\end{tabular}"]
write_table("\n".join(lines) + "\n", "tab1_methods.tex")
