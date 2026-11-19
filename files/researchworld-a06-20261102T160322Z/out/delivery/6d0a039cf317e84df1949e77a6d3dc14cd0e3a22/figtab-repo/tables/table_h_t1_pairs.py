"""Table H (Q1c, Q2a): ranking two tuned systems A and B on the real MMLU-Pro outcome matrix (T1 pair design; same search set D,
A and B tuned exhaustively from disjoint candidate subsets of K_A and K_B configs; 1000 replicates per cell, 10 delete-a-block blocks).
True order: sign of the fresh-set accuracy difference theta_A - theta_B. 'A beats B' is claimed when the method's estimate for A exceeds B's
('point'), or A's lower bound exceeds B's estimate ('lo'). Flip: reported and true difference have different signs (a tie in the reported
scores counts as a flip). Every rate is mean +- 1.96 x delete-a-block SE: replicates share items, so Wilson intervals would be too narrow.
Reads results/methods_t1_pairs.parquet, runs_t1_pairs.parquet. Writes tables/table_h_t1_pairs.tex, table_h_t1_decisions.tex (n=100),
table_h_t1_decisions_n500.tex, table_h_all_cells.csv"""
import os, sys, re
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common

PAT = r"pair\|n=(\d+)\|KA=(\d+)\|KB=(\d+)\|([AB])"
m = pd.read_parquet(common.path("methods_t1_pairs.parquet"))
r = pd.read_parquet(common.path("runs_t1_pairs.parquet"))
for f in (m, r):
    c = f.cell_id.str.extract(PAT)
    f["n"], f["KA"], f["KB"], f["side"] = c[0].astype(int), c[1].astype(int), c[2].astype(int), c[3]
key = ["n", "KA", "KB", "rep"]
w = r.pivot_table(index=key, columns="side", values=["reported_naive", "theta"])
blk = r[r.side == "A"].set_index(key).block
base = pd.DataFrame({"rd": (w["reported_naive"]["A"] - w["reported_naive"]["B"]).round(9), "td": (w["theta"]["A"] - w["theta"]["B"]).round(9)})
base["block"] = blk
base["flip"] = (np.sign(base.rd) != np.sign(base.td)).astype(float)
base["true_A"] = (base.td > 0).astype(float)
base["rep_A"] = (base.rd > 0).astype(float)


def rate(x, blocks):
    """mean and 1.96 x delete-a-block SE of a 0/1 (or numeric) series."""
    bm = x.groupby(blocks).mean()
    return x.mean(), 1.96 * bm.std() / np.sqrt(len(bm))


# --- pairs: truth, claim rate, flip rate
rows = []
for (n, ka, kb), d in base.groupby(["n", "KA", "KB"]):
    rec = dict(n=n, KA=ka, KB=kb, reps=len(d))
    for c in ("true_A", "rep_A", "flip"):
        rec[c], rec[c + "_ci"] = rate(d[c], d.block)
    rec["rd"], rec["rd_ci"] = rate(100 * d.rd, d.block)
    rec["td"], rec["td_ci"] = rate(100 * d.td, d.block)
    rows.append(rec)
P = pd.DataFrame(rows)

# --- decisions per method: A_not_better = fresh difference <= 0
a = m[m.side == "A"].set_index(key + ["method"]); b = m[m.side == "B"].set_index(key + ["method"])
dec = pd.DataFrame({"point": a.estimate > b.estimate, "lo": a.lo > b.estimate})
dec["has_lo"] = a.lo.notna()
dec = dec.reset_index().merge(base.reset_index()[key + ["td", "block"]], on=key)
dec["regime"] = np.where(dec.td > 0, "A_better", "A_not_better")
rows = []
for (n, ka, kb, meth, reg), d in dec.groupby(["n", "KA", "KB", "method", "regime"]):
    for v in ("point", "lo"):
        if v == "lo" and not d.has_lo.any():
            continue
        x, ci = rate(d[v].astype(float), d.block)
        rows.append(dict(n=n, KA=ka, KB=kb, method=meth, regime=reg, variant=v, n_reps=len(d), rate=x, ci=ci))
D = pd.DataFrame(rows)
D.to_csv(f"{common.TOUT}/table_h_all_cells.csv", index=False)

# check against experiment-repo's decisions file (margin 0, point)
ref = pd.read_csv(common.path("decisions_ab_t1.csv"))
ref = ref[(ref.margin_m == 0) & (ref.variant == "point")].rename(columns={"K_A": "KA", "K_B": "KB", "regime": "reg"})
ref["regime"] = ref.reg
chk = D[D.variant == "point"].merge(ref, on=["n", "KA", "KB", "method", "regime"])
assert len(chk) == len(D[D.variant == "point"]) and np.allclose(chk.rate * chk.n_reps_x, chk.n_reject), "differs from decisions_ab_t1.csv"

# --- Table H1
PAIRS = [(75, 5), (75, 75), (24, 24), (5, 5)]
lines = [r"\begin{tabular}{rrrrrrr}", r"\toprule",
         r"$K_A$ vs $K_B$ & $n$ & true $\theta_A-\theta_B$ (pts) & reported $\hat\theta_A-\hat\theta_B$ (pts) & P(A truly better) & P(claim A$>$B) & P(rank flip) \\", r"\midrule"]
for ka, kb in PAIRS:
    for n in (100, 500):
        p = P[(P.KA == ka) & (P.KB == kb) & (P.n == n)].iloc[0]
        lines.append(rf"{ka} vs {kb} & {n} & {p.td:+.2f} $\pm$ {p.td_ci:.2f} & {p.rd:+.2f} $\pm$ {p.rd_ci:.2f} & {p.true_A:.2f} & {p.rep_A:.2f} $\pm$ {p.rep_A_ci:.2f} & {p.flip:.2f} $\pm$ {p.flip_ci:.2f} \\")
    lines.append(r"\midrule")
lines[-1] = r"\bottomrule"
lines.append(r"\end{tabular}")
open(f"{common.TOUT}/table_h_t1_pairs.tex", "w").write("\n".join(lines) + "\n")

# --- Table H2: false-winner rate (A not truly better) and detection rate (A truly better)
METHODS = ["M0", "M1_f0.5", "M2", "M4_simult", "M4_cond", "M4_hybrid", "M5_eb", "M5_ladder"]
COLS = [((75, 5), "A_not_better", "point"), ((75, 5), "A_not_better", "lo"), ((75, 75), "A_not_better", "point"), ((75, 75), "A_not_better", "lo"),
        ((75, 5), "A_better", "point"), ((75, 5), "A_better", "lo")]
HEAD = [r"\shortstack{75 vs 5\\ false winner, point}", r"\shortstack{75 vs 5\\ false winner, lower bd}", r"\shortstack{75 vs 75\\ false winner, point}",
        r"\shortstack{75 vs 75\\ false winner, lower bd}", r"\shortstack{75 vs 5\\ A truly better, point}", r"\shortstack{75 vs 5\\ A truly better, lower bd}"]
for n, name in ((100, "table_h_t1_decisions.tex"), (500, "table_h_t1_decisions_n500.tex")):
    lines = [r"\begin{tabular}{l" + "r" * len(COLS) + "}", r"\toprule", "method & " + " & ".join(HEAD) + r" \\", r"\midrule"]
    for meth in METHODS:
        cells = []
        for (ka, kb), reg, v in COLS:
            x = D[(D.n == n) & (D.KA == ka) & (D.KB == kb) & (D.method == meth) & (D.regime == reg) & (D.variant == v)]
            cells.append("--" if x.empty else rf"{100 * x.rate.iloc[0]:.1f} $\pm$ {100 * x.ci.iloc[0]:.1f}")
        lines.append(meth.replace("_", r"\_") + " & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(f"{common.TOUT}/{name}", "w").write("\n".join(lines) + "\n")
print(P.round(3).to_string())
