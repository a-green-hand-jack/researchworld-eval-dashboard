"""Tables 2, 3 and the price table as booktabs `tabular` fragments (\\footnotesize = 8 pt in a 10 pt document).

usage: make_tables.py --results DIR --out DIR

Table 2 (`boards`): board, snapshot, m, N, noise source, targets, as written in the file (file paths
and commit hashes are shortened, nothing else is edited).
Table 3 (`verdicts`): the pre-registered tests R1-R5, one block per test. Every number is a number of
a row of `verdicts.csv`; where a block pools rows (R2: the largest share over the budget grid; R3: the
range over rules) the pooling is a max / min / count over those rows and is named in the row. The
verdict word is copied from the file, never set here. `units.csv` (R5 detail) goes to the appendix.
Price table (`price`): over the targets of the top 30 that are not yet first (own incumbent, B = 100 = ceilings) the median
total boost and median minimal feasible per-task budget B* (`price_magnitude.csv`) and the median breadth k/m (`price.csv`,
same targets), per rule and board; a dagger marks a cell with a MILP optimality gap above 1e-4.
Table 3 also reads `predictors_within.csv` (grouped-CV R^2 at B = 100, model gap), `bx_crossing.csv` (sigma unit, breadth over
feasible targets) and `predictors_hl.csv` (model gap+profile; intercept re-estimated, plus the fitted-intercept count). The verdict "not supported" for the deficit-profile test
is `paper-repo`'s wording (the file has no verdict column); every other verdict word is copied from `verdicts.csv`.
Table 1 (rule classes) is typeset by `paper-repo` in the text.
"""
import argparse
import json
import os
import re

import numpy as np
import pandas as pd

import common

ESC = {"_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#"}
BOARD = {"helm_mmlu": "HELM MMLU ($m{=}57$)", "ollb_bench": "OLLB benchmarks ($m{=}6$)",
         "ollb_bench_raw": "OLLB bundled ($m{=}6$)", "ollb_sub": "OLLB sub-tasks ($m{=}39$)"}
RULE = {"median": "median", "plurality": "plurality", "copeland": "Copeland", "borda": "Borda", "mean": "mean",
        "zmean": "z-mean", "min": "min"}


def tex(x):
    s = "".join(ESC.get(c, c) for c in str(x))
    return s.replace(">=", r"$\ge$").replace("<=", r"$\le$")


def num(x, d=2):
    if pd.isna(x):
        return "--"
    if abs(x) >= 100 or (x != 0 and abs(x) < 0.005):
        return f"{x:.2g}".replace("e-0", "e-").replace("e+0", "e")
    return f"{x:.{d}f}".replace("-", "$-$")


def sci(x):
    e = int(np.floor(np.log10(abs(x))))
    return f"$-{abs(x) / 10 ** e:.1f}\\times10^{{{e}}}$" if abs(x) >= 100 else num(x)


def ci(lo, hi, d=2):
    return f"[{num(lo, d)}, {num(hi, d)}]" if pd.notna(lo) and pd.notna(hi) else "--"


def table2(res, out):
    b, p = common.load(res, "boards")
    rows = []
    # the price tables use the 30 highest-ranked targets; boards.csv counts every model of HELM as a target (79)
    targets = lambda r: "30 (79 in the full-HELM run)" if (r.board == "helm_mmlu" and r.n_targets == 79) else str(r.n_targets)
    for _, r in b.iterrows():
        snap = re.sub(r"\(commit ([0-9a-f]{7})[0-9a-f]*, updated ([0-9-]+)\)", r"(\1, \2)", r.snapshot)
        snap = snap.replace("`", "")
        noise = re.sub(r"\s*\([^)]*\.csv\)", "", r.noise_source).replace("`", "")
        rows.append(" & ".join([BOARD.get(r.board, tex(r.board)), tex(snap), str(r.m), str(r.N), tex(noise), targets(r)]) + r"\\")
    body = "\n".join([r"\footnotesize\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{1.1in}>{\raggedright\arraybackslash}p{1.65in}rr>{\raggedright\arraybackslash}p{1.05in}>{\raggedright\arraybackslash}p{0.62in}@{}}", r"\toprule",
                      r"Board & Snapshot & $m$ & $N$ & Noise & Targets\\", r"\midrule"] + rows + [r"\bottomrule", r"\end{tabular}"])
    common.save_table(body, out, "table2_boards", [p])


def mean_diff(detail):
    m = re.search(r"mean diff (-?[0-9.]+)", detail)
    return float(m.group(1)) if m else np.nan


SHORT = {"helm_mmlu": "HELM-57", "ollb_bench": "OLLB-6", "ollb_bench_raw": "OLLB-6", "ollb_sub": "OLLB-39"}
LETTER = {"supported": "S", "partial": "P", "failed": "F"}


def table3(res, out):
    v, p = common.load(res, "verdicts")
    w, pw = common.load(res, "predictors_within")
    bx, pbx = common.load(res, "bx_crossing")
    hl, phl = common.load(res, "predictors_hl")
    rows = []

    def block(title):
        rows.append((r"\addlinespace[2pt]" if rows else "") + r"\multicolumn{4}{@{}>{\raggedright\arraybackslash}p{5.4in}}{\emph{" + title + r"}}\\")

    def row(*cells):
        rows.append(" & ".join(cells) + r"\\")

    def span(text):
        return r"\multicolumn{2}{>{\raggedright\arraybackslash}p{4.09in}}{" + text + "}"

    # R1: one line per board, the three rules side by side in the order MED, PLU, COP
    r1 = v[v.R == "R1"]
    ORDER = ["median", "plurality", "copeland"]
    block("R1: median-type rules (median, plurality, Copeland) need more breadth than the mean. Share of targets ($\\ge0.8$ predicted); paired difference "
          "in $k/m$ [95\\% CI] ($>0$ predicted); S/P/F = supported/partial/failed")
    for b, g in r1.groupby("board", sort=False):
        g = g.assign(rk=g.rule.str.split(" vs ").str[0]).set_index("rk").loc[ORDER]
        row(SHORT[b], "/".join(num(x) for x in g.value),
            r"\hspace{2pt}".join(f"{num(mean_diff(r.detail))}\\,{ci(r.ci_lo, r.ci_hi).replace(', ', ',')}" for _, r in g.iterrows()),
            ", ".join(LETTER[x] for x in g.verdict))
    r2 = v[v.R == "R2"]
    ms = []
    for b, g in r2.groupby("board", sort=False):
        m = g.loc[g.value.idxmax()]
        ms.append((b, RULE.get(m.rule.split(": ")[1], m.rule), m.value, m.verdict))
    block("R2: no rule is cheapest in depth for $\\ge90\\%$ of targets (largest share over budgets, incumbents)")
    row("each board", span("; ".join(f"{SHORT[b]} {r} {num(x)}" for b, r, x, _ in ms)), tex(ms[0][3] if len({x[3] for x in ms}) == 1 else ", ".join(x[3] for x in ms)))
    r3 = v[v.R == "R3"]
    block("R3: the gap alone does not predict price (held-out $R^2<0.9$ in the worst of the six directions)")
    row("across", span(f"worst direction per rule: best {num(r3.value.max())}, lowest {sci(r3.value.min())}; $<0$ for {int((r3.value < 0).sum())} of {len(r3)}"),
        tex(r3.verdict.iloc[0] if r3.verdict.nunique() == 1 else "; ".join(sorted(r3.verdict.unique()))))
    g = w[(w.model == "gap") & (w.B == 100)]
    pl = g[g.rule == "plurality"].cv_r2.clip(lower=0)
    rest = g[g.rule != "plurality"].cv_r2
    row("within", span(f"grouped-CV $R^2$ over target families: {num(round(rest.min(), 2))}--{num(round(rest.max(), 2))}; plurality {num(round(pl.min(), 2))}--{num(round(pl.max(), 2))}"), "--")
    r4 = v[v.R == "R4"]
    block("R4: median/mean breadth ratio rises with $m$ (slope $>0$ predicted; $b=2\\sigma$, other $b$ in Fig.~\\ref{fig:m})")
    for _, r in r4.iterrows():
        what = "slope vs $\\ln m$" if r.board.startswith("helm") else "ratio$_{39}-$ratio$_{6}$"
        row("HELM" if r.board.startswith("helm") else "OLLB", what, f"{num(r.value, 3)} {ci(r.ci_lo, r.ci_hi, 3)}", tex(r.verdict))
    r5 = v[v.R == "R5"]
    block("R5: median-type cheaper in all 4 units and $\\tau\\ge0.5$: min Kendall $\\tau$; units cheaper; cap/no cap; S/P/F")
    for b, g in r5.groupby("board", sort=False):
        c = g[g.rule.str.contains(r"\(cap\)")].iloc[0]; n = g[~g.rule.str.contains(r"\(cap\)")].iloc[0]
        cnt = lambda r: sum(x == "True" for x in re.findall(r"'(?:\w+)': (True|False)", r.detail))
        row(SHORT[b], f"{num(c.value)}/{num(n.value)}", f"median-type cheaper in {cnt(c)}/{cnt(n)} of 4 units", f"{LETTER[c.verdict]}/{LETTER[n.verdict]}")
    # crossing budget (sigma unit, breadth over feasible targets)
    x = bx[(bx.unit == "sigma") & (bx.objective == "breadth_feasible")]
    block("Crossing budget $B_\\times$ ($\\sigma$/task) above which the median needs more breadth than the mean (feasible; 95\\% CI)")
    cells = []
    for b in ("helm_mmlu", "ollb_bench_raw", "ollb_sub"):
        r = x[(x.board == b) & (x.rule == "median")].iloc[0]
        cells.append(f"{SHORT[b]} " + (f"{num(r.B_x, 1)} {ci(r.B_x_ci_lo, r.B_x_ci_hi, 1)}" if pd.notna(r.B_x) else "none"))
    r = x[(x.board == "helm_mmlu") & (x.rule == "plurality")].iloc[0]
    row("crossing", span("median: " + "; ".join(cells) + "; plurality: HELM-57 " + ("none" if pd.isna(r.B_x) else num(r.B_x, 1))), "--")
    # H-L: exploratory, post hoc; the primary model is gap+profile with the intercept re-estimated on the test board
    h = hl[(hl.model == "gap+profile") & (hl.r2_variant == "recentred")]
    kept = h.groupby("rule").retained.sum()
    block("Deficit-profile test (exploratory, post hoc): profile adds $\\ge0.1$ held-out $R^2$ to the gap (CI above 0); cross-board, intercept re-estimated")
    zero = h[h.rule == "mean"].gain.abs().max()
    assert zero < 1e-6
    assert h[h.rule == "zmean"].retained.sum() == 0
    hk = hl[(hl.model == "gap+profile") & (hl.r2_variant == "heldout")]
    row("profile", span(f"retained in {int(h.retained.sum())} of {len(h)} cases ({int(hk.retained.sum())} with the fitted intercept kept): " + ", ".join(f"{RULE[r]} {int(k)}" for r, k in kept.items() if k > 0)
        + "; mean: gain 0 (identity); z-mean: never retained"), "not supported")
    body = "\n".join([r"\footnotesize\setlength{\tabcolsep}{2.5pt}", r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.58in}>{\raggedright\arraybackslash}p{0.82in}>{\raggedright\arraybackslash}p{3.2in}>{\raggedright\arraybackslash}p{0.7in}@{}}", r"\toprule",
                      r"Scope & Value & 95\% CI / detail & Verdict\\", r"\midrule"] + rows + [r"\bottomrule", r"\end{tabular}"])
    common.save_table(body, out, "table3_verdicts", [p, pw, pbx, phl])

PRICE_BOARDS = [("helm_mmlu", "HELM MMLU ($m{=}57$)"), ("ollb_bench", "OLLB benchmarks ($m{=}6$)"), ("ollb_sub", "OLLB sub-tasks ($m{=}39$)")]
PRICE_RULES = ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]


def table_price(res, out):
    """Median over the targets not yet first (own incumbent, B = 100 = ceilings): boost and B* from price_magnitude.csv,
    k/m and the optimality-gap dagger from the same targets in price.csv (same filter as analysis/magnitude.py)."""
    pm, p1 = common.load(res, "price_magnitude")
    pr, p2 = common.load(res, "price")
    pm = pm[(pm.incumbent == "own") & (pm.B == 100)].set_index(["board", "rule"])
    pr = pr[(pr.incumbent == "own") & (pr.B == 100) & (pr.unit == "points") & (pr.init_rank <= 30)]
    nf = pr[~((pr.rank_rule == 1) | (pr.gap <= 0))].assign(kfrac=lambda d: d.k_star / d.m)
    nf = nf.groupby(["board", "rule"]).agg(kfrac=("kfrac", "median"), gap=("opt_gap", "max"), n=("target", "size"))
    rows = []
    for r in PRICE_RULES:
        cells = [RULE[r]]
        for b, _ in PRICE_BOARDS:
            e, q = pm.loc[(b, r)], nf.loc[(b, r)]
            assert e.n_not_first == q.n and e.share_infeasible == 0
            dag = r"$^\dagger$" if q.gap > 1e-4 else ""
            cells += [f"{round(e.median_depth):d}" + dag, num(q.kfrac), num(e.median_B_star, 1)]
        rows.append(" & ".join(cells) + r"\\")
    head = " & ".join([""] + [r"\multicolumn{3}{c}{" + t + "}" for _, t in PRICE_BOARDS]) + r"\\"
    cmid = "".join(rf"\cmidrule(lr){{{2 + 3 * i}-{4 + 3 * i}}}" for i in range(3))
    sub = " & ".join(["Rule"] + ["boost", "$k/m$", "$B^\\ast$"] * 3) + r"\\"
    body = "\n".join([r"\footnotesize\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{@{}l" + "rrr" * 3 + "@{}}", r"\toprule",
                      head, cmid, sub, r"\midrule"] + rows + [r"\bottomrule", r"\end{tabular}"])
    common.save_table(body, out, "table_price", [p1, p2])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    for f in (table2, table3, table_price):
        try:
            f(a.results, a.out)
        except FileNotFoundError as e:
            print("skipped", f.__name__, e)
