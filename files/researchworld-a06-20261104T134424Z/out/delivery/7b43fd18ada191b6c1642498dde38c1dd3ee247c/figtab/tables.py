"""Tables T1-T4 as LaTeX fragments (booktabs tabulars; caption and \\begin{table} are the manuscript's) + one-line notes with the
numbers of repetitions, all generated from results/*.csv.  Writes paper/tables/<name>.tex and <name>_note.tex.
T1 reporting methods at the reference cell; T2 stress cells; T3 two-system comparison; T4 naive gap by n and K (main-text companion of E1)."""
import os
from style import *

TAB = os.path.join(HERE, "..", "paper", "tables")
ORDER = ["naive", "split", "crossfit", "boot_opt", "boot_oob", "boot_632", "simul", "cond"]
LAB = dict(EST_LABEL, boot_632="bootstrap .632")

def pm(v, se, s=100, nd=2):  # value +- standard error, in pp
    x = round(s * v, nd) + 0.0  # avoids "-0.00"
    return f"${x:.{nd}f} \\pm {s * se:.{nd}f}$"

def write(name, body, note):
    os.makedirs(TAB, exist_ok=True)
    open(os.path.join(TAB, name + ".tex"), "w").write(body)
    open(os.path.join(TAB, name + "_note.tex"), "w").write(note + "\n")
    print("wrote", os.path.normpath(os.path.join(TAB, name + ".tex")))

def tabular(cols, rows, head):
    out = ["{\\footnotesize\\setlength{\\tabcolsep}{3.5pt}", "\\begin{tabular}{" + cols + "}", "\\toprule", head + " \\\\", "\\midrule"]
    for r in rows: out.append(r if r == "\\midrule" else r + " \\\\")
    out += ["\\bottomrule", "\\end{tabular}}"]
    return "\n".join(out) + "\n"

def row_metrics(r):
    return [pm(r.bias, r.bias_se), f"{100 * r.rmse:.2f}", f"${r.cover:.3f} \\pm {r.cover_se:.3f}$", f"{100 * r.width:.1f}",
            f"{r.fp_rate:.3f}", f"{r.false_ship_2pp:.3f}"]

HEAD = "method & bias (pp) & RMSE (pp) & coverage & width (pp) & false claim & false ship"

def t1(p):
    r = p[p.is_reference].set_index("est_name")
    rows = [" & ".join([LAB[e]] + row_metrics(r.loc[e])) for e in ORDER]
    note = (f"Reference cell: n=200, K=16, $\\tau$=.01, $\\rho$=.5, mean accuracy .3, best-of-K; {int(r.reps.min())} repetitions. "
            "Bias and coverage are mean $\\pm$ Monte Carlo s.e.; coverage is of the nominal 95\\% interval for the true score of the selected configuration; "
            "false claim: rate of claiming tuned $>$ baseline when it is not truly better; false ship: rate of reporting a score at least 2 pp above the baseline's true score while the selected configuration's true score is below that bar.")
    write("t1_reference_cell", tabular("lrrrrrr", rows, HEAD), note)

def t2(p):
    s = p[p.f_kind == "stress"]; rows = []; cells = s[["f_n", "f_K", "f_tau", "f_m", "f_outlier"]].drop_duplicates().sort_values(["f_m", "f_outlier", "f_K", "f_n"]).values
    for k, (n, K, t, m, o) in enumerate(cells):
        if k: rows.append("\\midrule")
        g = s[(s.f_n == n) & (s.f_K == K) & (s.f_tau == t) & (s.f_m == m) & (s.f_outlier == o)].set_index("est_name")
        lab = f"$n$={int(n)}, $K$={int(K)}" + (f", acc. {m:g}" if m != 0.3 else "") + (f", outl. {o:g}" if o else "")
        for i, e in enumerate(["naive", "split", "crossfit", "boot_oob", "simul", "cond"]):
            r = g.loc[e]
            rows.append(" & ".join([lab if i == 0 else "", LAB[e], pm(r.bias, r.bias_se), f"${r.cover:.3f} \\pm {r.cover_se:.3f}$", f"{100 * r.width:.1f}", f"{r.fp_rate:.3f}"]))
    note = (f"Stress cells ($\\tau$=0, $\\rho$=.5, best-of-K; outlier = fraction of outlier configurations); {int(s.reps.min())} repetitions each. "
            "Columns as in the reference-cell table (RMSE and false-ship rate omitted for width; they are in the results file); bias and coverage are mean $\\pm$ Monte Carlo s.e.; outl. = outlier-configuration fraction, acc. = mean accuracy (.3 unless shown).")
    write("t2_stress_cells", tabular("llrrrr", rows, "cell & method & bias (pp) & coverage & width (pp) & false claim"), note)

def t3(path_n=200):
    c = pd.read_csv(os.path.join(RESULTS, "synth_compare_summary.csv")); c = c[c.n == path_n]; rows = []
    for k, t in enumerate(sorted(c.tau.unique())):
        if k: rows.append("\\midrule")
        for a, b in [(16, 16), (16, 4), (64, 4), (64, 1)]:
            g = c[(c.tau == t) & (c.KA == a) & (c.KB == b)].set_index("est_name"); r = g.loc["naive"]
            rows.append(" & ".join([f"{t:g}", f"{a}/{b}", f"{r.claim:.3f} \\pm {r.claim_se:.3f}".join("$$"), f"{r.false_claim:.3f}", f"{r.wrong_sign:.3f}",
                                    f"{100 * r.mean_reported_diff:.2f}", f"{100 * r.mean_true_diff:.2f}", f"{g.loc['split'].false_claim:.3f}"]))
    note = (f"Two tuned systems A and B searched with $K_A$ and $K_B$ configurations (best-of-K, $n$={path_n}); {int(c.reps.min())} repetitions per row. "
            "Naive columns: claim = rate of claiming A$>$B (one-sided 5\\%), false claim = claim while A is truly not better (true difference $\\le$ 0), wrong sign = claim while A is truly worse; "
            "mean reported and true difference A$-$B in pp. Last column: false-claim rate of the held-out split.")
    write("t3_unequal_budget", tabular("rlrrrrrr", rows, "$\\tau$ & $K_A/K_B$ & claim (naive) & false claim & wrong sign & reported diff. (pp) & true diff. (pp) & false claim (split)"), note)

def t4(p):
    g = p[(p.f_kind == "inter") & (p.f_proc == "argmax") & (p.f_rho == 0.5) & (p.est_name == "naive") & (p.f_tau.isin([0.0, 0.03]))]
    ns = sorted(g.f_n.unique()); Ks = sorted(g.f_K.unique()); rows = []
    for k, t in enumerate([0.0, 0.03]):
        if k: rows.append("\\midrule")
        for n in ns:
            vals = [pm(*g[(g.f_tau == t) & (g.f_n == n) & (g.f_K == K)][["bias", "bias_se"]].iloc[0]) for K in Ks]
            rows.append(" & ".join([f"{t:g}", str(int(n))] + vals))
    note = (f"Naive optimism gap (pp; reported minus true score of the selected configuration), mean $\\pm$ Monte Carlo s.e. over {int(g.reps.min())} repetitions; $\\rho$=.5, best-of-K.")
    write("t4_gap_by_n_K", tabular("rr" + "r" * len(Ks), rows, "$\\tau$ & $n$ & " + " & ".join(f"$K$={int(K)}" for K in Ks)), note)

if __name__ == "__main__":
    p = load_plan(); t1(p); t2(p); t3(); t4(p)
