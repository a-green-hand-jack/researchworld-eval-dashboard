"""Table 2 (C6): coverage and width of the 95% intervals, by response class (main text) and by regime (appendix).
Reads results/summary/c6_cover.csv (95% bootstrap over cells, 2000 draws, seed in the file's README).
Writes tables/tab2_coverage.tex and tables/app_tab_cover_regime.tex (tabular bodies only).
Entry: value[lo,hi]. Classes: inside = linear, concave, convex; violating = threshold, convex 2-hop; count is kept apart.
The last two rows are controls: the iid and sandwich standard errors inflated by a constant to the mean width of the bias-aware interval."""
import os, re
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
c = pd.read_csv(os.path.join(ROOT, "results", "summary", "c6_cover.csv"))

IV = [("iid OLS", "iid OLS"), ("network sandwich", "sandwich"), ("pairs bootstrap", "pairs bootstrap"), ("Louvain block bootstrap", "block bootstrap"),
      ("sandwich + B (pre-registered)", "sandwich $+\\,B$")]
CTRL = {"sandwich SE": "sandwich SE", "iid SE": "iid SE"}
CLASS = [("inside curvature-rule class", "inside"), ("violating the curvature rule", "violating"), ("count (own class)", "count"), ("all", "all cells")]
REGIME = [("variance-dominated", "variance"), ("between", "between"), ("bias-dominated", "bias"), ("all", "all cells")]


def num(x, w):
    s = f"{x:.3f}" if not w else f"{x:.2f}"
    return s.replace("0.", ".") if not w else s


def entry(r, stat):
    v, lo, hi = r[stat], r[f"{stat}_lo"], r[f"{stat}_hi"]
    if stat == "mean_coverage" and lo > 0.9995:
        return "1.000"
    w = stat == "mean_width"
    return f"{num(v, w)}[{num(lo, w)},{num(hi, w)}]"


def rows(by, groups):
    sub = c[c.by.isin([by, "all"])]
    out = [(i, lab) for i, lab in IV]
    ctrl = sorted({i for i in sub.interval if "width-matched" in i})
    for i in ctrl:
        mult = re.search(r"x([\d.]+)", i).group(1)
        key = i.split(" x")[0].split(" SE")[0] + " SE"
        out.append((i, f"{CTRL[key]} $\\times${mult}"))
    return out


def make(by, groups, hdr, out):
    ivs = rows(by, groups)
    L = ["\\footnotesize\\setlength{\\tabcolsep}{2.4pt}", "\\begin{tabular}{l" + "c" * len(groups) + "}", "\\toprule"]
    n = {g: int(c[(c.by == (by if g != "all" else "all")) & (c.group == g)].n_cells.iloc[0]) for g, _ in groups}
    for p, (stat, ttl) in enumerate([("mean_coverage", "coverage of the true effect"), ("mean_width", "mean width of the interval")]):
        if p:
            L.append("\\midrule")
        L.append("\\multicolumn{%d}{l}{\\emph{%s}} \\\\" % (len(groups) + 1, ttl))
        L.append(hdr + " & " + " & ".join(f"{l} ({n[g]})" for g, l in groups) + " \\\\")
        L.append("\\cmidrule(lr){1-1}\\cmidrule(lr){2-%d}" % (len(groups) + 1))
        for k, (i, lab) in enumerate(ivs):
            if k == 5:
                L.append("\\addlinespace[1pt]")
            cells = []
            for g, _ in groups:
                r = c[(c.by == (by if g != "all" else "all")) & (c.group == g) & (c.interval == i)]
                cells.append(entry(r.iloc[0], stat) if len(r) else "--")
            L.append(f"{lab} & " + " & ".join(cells) + " \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    open(out, "w").write("\n".join(L) + "\n")


make("class", CLASS, "interval", os.path.join(ROOT, "tables", "tab2_coverage.tex"))
make("regime", REGIME, "interval", os.path.join(ROOT, "tables", "app_tab_cover_regime.tex"))
print(open(os.path.join(ROOT, "tables", "tab2_coverage.tex")).read())
