"""Spillover-aware variant (appendix, Tier C; mean rule only).  usage: spillover.py TABLES_DIR OUTDIR   reads TABLES_DIR/calibration.csv (benchmark-level gains of real base -> fine-tune pairs).
Measured spillover: for each pair, the targeted benchmark j is the one with the largest gain; S[j', j] = median over pairs targeting j (with gain_j > 0) of max(gain_j', 0) / gain_j
(cells with < 10 such pairs use the pooled median over all pairs).  Under the mean rule, a direct boost d_j (cap B) then lifts the mean by (1 + sum_{j' != j} S[j', j]) d_j / m =: a_j d_j / m
(linear, ceilings on the spilled gains ignored: a lower bound on price).  Spillover-aware price = cheapest direct plan with sum a_j d_j >= gap * m (cap B on direct boost; greedy by a_j; exact
for this knapsack).  Compared with the no-spillover price on the m=6 `contents` board (own leader, 30 top targets of the main slice).  Writes OUTDIR/spillover_matrix.csv, spillover_price.csv.
The matrix is a descriptive estimate from non-randomised pairs (see calibration caveats); the CI of the mean multiplier is a bootstrap over base models (2000, seed 20260102)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice.boards import load_ollb, BEN6
T, OUT = sys.argv[1], sys.argv[2]
cal = pd.read_csv(os.path.join(T, "calibration.csv"))
G = cal.pivot_table(index=["child", "base"], columns="task", values="gain", aggfunc="first")[BEN6]; bases = np.array([i[1] for i in G.index]); G = G.values; m = 6


def matrix(G):
    arg = G.argmax(axis=1); S = np.zeros((m, m)); pooled = [[] for _ in range(m)]; cnt = np.zeros(m, int)
    for j in range(m):
        sel = (arg == j) & (G[:, j] > 0); cnt[j] = sel.sum()
        for jp in range(m):
            if jp != j: pooled[jp].append(np.maximum(G[sel, jp], 0) / G[sel, j])
    allr = {jp: np.concatenate([x for x in pooled[jp]] or [np.array([0.0])]) for jp in range(m)}
    for j in range(m):
        sel = (arg == j) & (G[:, j] > 0)
        for jp in range(m):
            if jp == j: continue
            S[jp, j] = np.median(np.maximum(G[sel, jp], 0) / G[sel, j]) if sel.sum() >= 10 else (np.median(allr[jp]) if len(allr[jp]) else 0.0)
    return S, cnt


S, cnt = matrix(G)
M = pd.DataFrame(S, index=["gain_on_" + b for b in BEN6], columns=["target_" + b for b in BEN6]); M.loc["n_pairs_targeting"] = cnt; M.to_csv(os.path.join(OUT, "spillover_matrix.csv"))
a = 1 + S.sum(axis=0)
rng = np.random.default_rng(20260102); ub = np.unique(bases); by = {b: G[bases == b] for b in ub}
boots = []
for _ in range(2000):
    Gb = np.concatenate([by[b] for b in rng.choice(ub, len(ub))]); Sb, _ = matrix(Gb); boots.append((1 + Sb.sum(axis=0)).mean())
print("a_j", a.round(2), "mean", a.mean().round(3), "CI", np.percentile(boots, [2.5, 97.5]).round(3), "pairs per target task", cnt)
b = load_ollb("m6"); S6 = b["S"]; top = np.argsort(-b["official"], kind="stable")[:30]
rows = []
for t in top:
    A = S6.mean(axis=1); A_ = A.copy(); A_[t] = -np.inf; gap = A_.max() - A[t] + 1e-6; need = gap * m; head = 100.0 - S6[t]
    for B in (5.0, 10.0, 100.0):
        for tag, w in (("no_spillover", np.ones(m)), ("spillover", a)):
            if gap <= 0: d, k, ok = 0.0, 0, True
            else:
                cap = np.minimum(B, head); order = np.argsort(-w, kind="stable"); got = 0.0; d = 0.0; k = 0; ok = False
                for j in order:
                    if cap[j] <= 0: continue
                    take = min(cap[j], (need - got) / w[j]); got += take * w[j]; d += take; k += 1
                    if got >= need - 1e-12: ok = True; break
            rows.append(dict(board="ollb_bench", target=int(t), model=b["names"][t], B=B, variant=tag, feasible=ok, depth=d if ok else np.nan, breadth=k if ok else np.nan))
r = pd.DataFrame(rows); r.to_csv(os.path.join(OUT, "spillover_price.csv"), index=False)
q = r.pivot_table(index=["target", "B"], columns="variant", values="depth").reset_index()
print(q.groupby("B").apply(lambda x: pd.Series(dict(median_ratio=(x.spillover / x.no_spillover).median(), feasible_no=x.no_spillover.notna().mean(), feasible_sp=x.spillover.notna().mean()))))
