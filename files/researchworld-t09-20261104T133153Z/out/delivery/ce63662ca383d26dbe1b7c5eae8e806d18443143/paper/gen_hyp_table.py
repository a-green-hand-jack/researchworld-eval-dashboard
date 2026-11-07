"""Writes hyp_table.tex (appendix table of the tests and verdicts) from results/hypotheses.csv and, if given, results/hypotheses_postfreeze.csv."""
import sys
import pandas as pd

src, dst = sys.argv[1], sys.argv[2]
h = pd.read_csv(src)
post = pd.read_csv(sys.argv[3]) if len(sys.argv) > 3 else None


def esc(s):
    s = str(s)
    for a, b in [("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#"), (">=", "$\\ge$"),
                 ("<=", "$\\le$"), ("|", "$|$"), ("~", "$\\sim$"), ("^", "\\^{}")]:
        s = s.replace(a, b)
    return s.replace("<", "$<$").replace(">", "$>$")


CHECKS = {"H1", "H2", "H3b", "H6a", "H3g"}  # identities of the model or implementation checks, not tests of an empirical claim


def row(r, check):
    v = {"supported": "passes", "refuted": "fails"}.get(r.verdict, r.verdict) if check else r.verdict
    return " & ".join([esc(r.hypothesis), esc(r.test), esc(r.decision_rule), esc(v)]) + " \\\\"


frames = [h] + ([post] if post is not None else [])
allr = pd.concat(frames, keys=range(len(frames))).reset_index(drop=True)
allr["post"] = [i for i, f in enumerate(frames) for _ in range(len(f))]
rows = ["\\multicolumn{4}{@{}l}{\\emph{A. Consistency checks: identities of the model or of the code (a failure would indicate an error, a pass is not evidence about the world)}} \\\\ \\midrule"]
rows += [row(r, True) for _, r in allr[allr.hypothesis.isin(CHECKS)].iterrows()]
rows.append("\\midrule \\multicolumn{4}{@{}l}{\\emph{B. Empirical hypotheses (first freeze)}} \\\\ \\midrule")
rows += [row(r, False) for _, r in allr[~allr.hypothesis.isin(CHECKS) & (allr.post == 0)].iterrows()]
if post is not None:
    rows.append("\\midrule \\multicolumn{4}{@{}l}{\\emph{C. Empirical, post-freeze additions (run after the first results were seen)}} \\\\ \\midrule")
    rows += [row(r, False) for _, r in allr[~allr.hypothesis.isin(CHECKS) & (allr.post == 1)].iterrows()]
body = "\n".join(rows)
open(dst, "w").write(
    "\\begin{longtable}{@{}p{0.11\\linewidth}p{0.33\\linewidth}p{0.4\\linewidth}p{0.08\\linewidth}@{}}\n"
    "\\toprule ID & test & decision rule & verdict \\\\\n\\endhead\n" + body +
    "\n\\bottomrule\n\\end{longtable}\n")
