"""Appendix table T9: synthetic generator calibrated to the real matrix vs the real replay (best-of-K naive gap).
Inputs: results/generator_calibration.csv, generator_pairwise_fit.csv, generator_vs_real_gap.csv.  Writes paper/tables/t9_generator_vs_real.tex + _note.tex.
Gap rows: disjoint truth arm, n = 200 and K in the file's list (K=1 omitted: no search); summary rows over all cells of the file (both truth arms)."""
from tables import write, tabular
from style import *

NG = 200
fm = lambda x: f"{x:.3f}".replace("-", "$-$")

def main():
    cal = pd.read_csv(os.path.join(RESULTS, "generator_calibration.csv")).set_index("item")
    pw = pd.read_csv(os.path.join(RESULTS, "generator_pairwise_fit.csv")).set_index("item")
    g = pd.read_csv(os.path.join(RESULTS, "generator_vs_real_gap.csv"))
    pwr = "pairwise phi: max |generator - real| over pairs"; rms = "pairwise phi: rms difference"
    rows = [
        f"accuracy, mean (\\%) & {100 * cal.loc['accuracy mean'].real:.2f} & {100 * cal.loc['accuracy mean'].generator:.2f} & (same thresholds)",
        f"accuracy, sd across configs (pp) & {100 * cal.loc['accuracy sd across configs'].real:.2f} & {100 * cal.loc['accuracy sd across configs'].generator:.2f} & (same thresholds)",
        f"item difficulty, sd across items & {cal.loc['sd of item-mean accuracy across items'].real:.3f} & {cal.loc['sd of item-mean accuracy across items'].generator:.3f} & --",
        f"mean pairwise $\\phi$ & {cal.loc['mean pairwise phi'].real:.3f} & {cal.loc['mean pairwise phi'].generator:.3f} & --",
        f"pairwise $\\phi$, min--max & {fm(cal.loc['min pairwise phi'].real)}--{cal.loc['max pairwise phi'].real:.3f} & {fm(cal.loc['min pairwise phi'].generator)}--{cal.loc['max pairwise phi'].generator:.3f} & --",
        f"pairwise $\\phi$, max $|\\Delta|$ over pairs & -- & {float(pw.loc[pwr].uniform_rho):.3f} & {float(pw.loc[pwr].tetrachoric):.3f}",
        "\\midrule",
    ]
    d = g[(g.truth_arm == "disjoint") & (g.n == NG) & (g.K > 1)]
    for K in sorted(d.K.unique()):
        u = d[(d.K == K) & (d.generator == "uniform_rho")].iloc[0]; t = d[(d.K == K) & (d.generator == "tetrachoric")].iloc[0]
        f = lambda gap, se, z: f"${100 * gap:.2f} \\pm {100 * se:.2f}$ ({z:+.1f})".replace("-", "$-$")
        rows.append(f"naive gap, $n$={NG}, $K$={int(K)} (pp) & ${100 * u.real_gap:.2f} \\pm {100 * u.real_se:.2f}$ & {f(u.gen_gap, u.gen_se, u.z)} & {f(t.gen_gap, t.gen_se, t.z)}")
    rows.append("\\midrule")
    g = g.assign(rel=(g.gen_gap - g.real_gap) / g.real_gap); cells = g[g.K > 1]; hi = cells[cells.K >= 4]
    st = {gen: dict(mean=hi[hi.generator == gen].rel.mean(), lo=hi[hi.generator == gen].rel.min(), hi=hi[hi.generator == gen].rel.max(),
                    nz=int((g[g.generator == gen].z.abs() > 2).sum()), n=int((g.generator == gen).sum())) for gen in ("uniform_rho", "tetrachoric")}
    rows.append("generator $-$ real, mean ($K\\ge4$, \\%) & -- & " + " & ".join(f"${100 * st[x]['mean']:+.1f}$" for x in ("uniform_rho", "tetrachoric")))
    rows.append("generator $-$ real, range ($K\\ge4$, \\%) & -- & " + " & ".join(f"${100 * st[x]['lo']:+.0f}$ to ${100 * st[x]['hi']:+.0f}$" for x in ("uniform_rho", "tetrachoric")))
    rows.append("cells with $|z|>2$ & -- & " + " & ".join(f"{st[x]['nz']} of {st[x]['n']}" for x in ("uniform_rho", "tetrachoric")))
    pools, reps = int(g.pools.iloc[0]), int(g.reps_per_pool.iloc[0]); arms = " and ".join(sorted(g.truth_arm.unique())); ns = sorted(g.n.unique())
    clip = int(float(pw.loc["tetrachoric R: eigenvalues clipped (count)"].tetrachoric))
    note = (f"Gaussian-copula generator calibrated to the real matrix (accuracies as thresholds): one common latent correlation (``one-rho'', matched to the mean pairwise $\\phi$) or one per pair "
            f"(``pairwise copula'', tetrachoric correlations, {clip} eigenvalues clipped). Gap rows: disjoint truth arm, mean $\\pm$ s.e. (pp) of the generator ({pools} pools $\\times$ {reps} replications) with $z$ against the real replay in parentheses. "
            f"Summary rows pool all $n$ ({', '.join(str(int(x)) for x in ns)}) and both truth arms ({arms}). The copula cannot reproduce the heterogeneity of the real pairwise dependence (near-duplicate and near-independent pairs) "
            f"and, for the pairwise version, higher-order structure.")
    write("t9_generator_vs_real", tabular("lrrr", rows, "quantity & real matrix & one-rho copula & pairwise copula"), note)

if __name__ == "__main__":
    main()
