"""Table D (Q1c, Q2a): decision errors of the claim 'the tuned system beats the untuned baseline by more than m' (T0).
False-claim rate = share of replicates claiming improvement when the true gain is < m (regimes gain<=0 and 0<gain<m);
power = share claiming it when the true gain >= m. 'point' claims from the method's estimate, 'lo' from its lower 95% bound.
Rates carry Wilson 95% intervals over replicates. Reads results/decisions_t0.csv. Writes tables/table_d_decisions.tex and table_d_all_cells.csv."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common

d = pd.read_csv(common.path("decisions_t0.csv"))
d = common.reference(common.main_grid(d))
d = d[d.rule == "tuned_gt_baseline_by_m"]
d["kind"] = np.where(d.regime.isin(["gain<=0", "0<gain<m"]), "false", "power")
g = d.groupby(["tau", "K", "n", "method", "variant", "margin_m", "kind"])[["n_reps", "n_reject"]].sum().reset_index()
g["rate"] = g.n_reject / g.n_reps
g["lo"], g["hi"] = common.wilson(g.n_reject, g.n_reps)
g.to_csv(f"{common.TOUT}/table_d_all_cells.csv", index=False)

m_, K_, n_ = 0.02, 200, 100
s = g[(g.margin_m == m_) & (g.K == K_) & (g.n == n_)]
order = ["M0", "M1_f0.2", "M1_f0.5", "M1_f0.8", "M2", "M3_opt", "M4_simult", "M4_cond", "M4_hybrid", "M5_eb", "M5_ladder"]
def cell(tau, kind, variant, meth):
    r = s[(s.tau == tau) & (s.kind == kind) & (s.variant == variant) & (s.method == meth)]
    if r.empty: return "--"
    r = r.iloc[0]; return rf"{100 * r.rate:.1f} [{100 * r.lo:.1f}, {100 * r.hi:.1f}]"
cols = [(0.0, "false", "point"), (0.0, "false", "lo"), (0.1, "false", "point"), (0.1, "power", "point"), (0.1, "power", "lo")]
head = [r"$\tau{=}0$ false claim, point", r"$\tau{=}0$ false claim, lower bound", r"$\tau{=}0.1$ false claim, point", r"$\tau{=}0.1$ power, point", r"$\tau{=}0.1$ power, lower bound"]
lines = [r"\begin{tabular}{l" + "r" * len(cols) + "}", r"\toprule", "method & " + " & ".join(head) + r" \\", r"\midrule"]
for meth in [o for o in order if o in set(s.method)]:
    lines.append(meth.replace("_", r"\_") + " & " + " & ".join(cell(*c, meth) for c in cols) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(f"{common.TOUT}/table_d_decisions.tex", "w").write("\n".join(lines) + "\n")
print("replicates per cell:", int(g.n_reps.min()), "-", int(g.n_reps.max()))
