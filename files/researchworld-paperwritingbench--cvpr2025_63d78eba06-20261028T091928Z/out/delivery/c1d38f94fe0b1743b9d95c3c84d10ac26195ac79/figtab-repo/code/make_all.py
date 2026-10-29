"""Build all delivered figures/tables from data/log_results.csv.

Usage: python3 code/make_all.py   (run from the repo root)
Outputs: figures/fig_ablations.pdf (+ .png preview), tables/tab_*.tex
Every number comes from the experimental log (see data/log_results.csv);
the script verifies the logged "Performance Gap" rows against recomputed differences.
"""
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

METRICS = ["test", "remaining", "forget", "mia"]
LABELS = {"test": "Test acc.", "remaining": "Remaining acc.", "forget": "Forget acc.", "mia": "MIA score"}
d = pd.read_csv("data/log_results.csv", comment="#", dtype={"setting": str})


def row(exp, setting, method):
    r = d[(d.experiment == exp) & (d.setting == setting) & (d.method == method)]
    assert len(r) == 1, (exp, setting, method)
    return r.iloc[0]


def gap(exp, setting, ref="Retrained", method="Unlearned(-)"):
    a, b = row(exp, setting, method), row(exp, setting, ref)
    return {m: abs(a[m] - b[m]) for m in METRICS}


# --- consistency check against logged gap rows -------------------------------------------
for exp in ["forget_size", "perturbations", "l2"]:
    for s in d[d.experiment == exp].setting.unique():
        g = gap(exp, s)
        u = row(exp, s, "Unlearned(-)")
        for m in METRICS:
            assert abs(g[m] - u["gap_" + m]) < 0.051, (exp, s, m, g[m], u["gap_" + m])
for s in d[d.experiment == "mixed"].setting.unique():
    g = gap("mixed", s, ref="Unlearned(+)")
    u = row("mixed", s, "Unlearned(-)")
    for m in METRICS:  # logged gaps in this experiment are w.r.t. Unlearned(+)
        assert abs(g[m] - u["gap_" + m]) < 0.051, ("mixed", s, m)

# --- Figure: ablations ---------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "Liberation Serif", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.linewidth": 0.6, "pdf.fonttype": 42,
})
STYLE = {  # Okabe-Ito colours + marker + linestyle so colour is never the only cue
    "test": ("#0072B2", "o", "-"),
    "remaining": ("#009E73", "s", "--"),
    "forget": ("#D55E00", "^", "-."),
    "mia": ("#000000", "D", ":"),
}
PANELS = [
    ("forget_size", ["5%", "10%", "15%"], "Forget-set size (% of training set)", "(a) Forget-set size"),
    ("perturbations", ["250", "500", "1000"], "Number of perturbations", "(b) Perturbations"),
    ("l2", ["0", "0.0005", "0.001"], r"L2 regularization $\lambda$", r"(c) Regularization $\lambda$"),
]
fig, axes = plt.subplots(1, 3, figsize=(6.9, 2.25), sharey=True)
for ax, (exp, xs, xlabel, title) in zip(axes, PANELS):
    gs = [gap(exp, x) for x in xs]
    for m in METRICS:
        c, mk, ls = STYLE[m]
        ax.plot(range(3), [g[m] for g in gs], color=c, marker=mk, ls=ls, lw=1.3, ms=4.5,
                label=LABELS[m], clip_on=False)
    ax.set_xticks(range(3)); ax.set_xticklabels(xs)
    ax.set_xlim(-0.2, 2.2); ax.set_ylim(0, 17)
    ax.set_xlabel(xlabel); ax.set_title(title)
    ax.grid(axis="y", lw=0.4, color="#cccccc"); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
axes[0].set_ylabel("Gap to Retrained (pp)")
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02),
           handlelength=2.6, columnspacing=1.8)
fig.tight_layout(rect=(0, 0.1, 1, 1), w_pad=1.0)
fig.savefig("figures/fig_ablations.pdf")
fig.savefig("figures/fig_ablations.png", dpi=200)


# --- Tables --------------------------------------------------------------------------------
def f(x):
    return f"{x:.1f}"


def fx(x, bold=False):
    s = f(x)
    return r"\textbf{" + s + "}" if bold else s


# Baselines (CIFAR-10, 10% forget): bold = closest to Retrained among the non-Retrained rows
rows = ["Retrained", "NegGrad", "Random Labels", "JiT", "Adversarial", "Unlearned(-)"]
R = {m: row("baselines", "10%", m) for m in rows}
best = {k: min(rows[1:], key=lambda m: abs(R[m][k] - R["Retrained"][k])) for k in METRICS}
L = [r"\begin{table}[t]", r"  \centering", r"  \small", r"  \setlength{\tabcolsep}{4pt}",
     r"  \begin{tabular}{@{}lcccc@{}}", r"    \toprule",
     r"    Method & Test & Remaining & Forget & MIA \\", r"    \midrule"]
for m in rows:
    name = {"Unlearned(-)": r"Unlearned($-$) (ours)", "Random Labels": "Random Labels"}.get(m, m)
    cells = [fx(R[m][k], bold=(m == best[k])) for k in METRICS]
    L.append(f"    {name} & " + " & ".join(cells) + r" \\")
    if m == "Retrained":
        L.append(r"    \midrule")
L += [r"    \bottomrule", r"  \end{tabular}",
      r"  \caption{Source-free baselines on CIFAR-10 (linear classifier, 10\% forget set), accuracy and MIA score in \%. "
      r"Bold: closest to Retrained among the non-retrained methods (for MIA, closest to the ideal 50). "
      r"Single run per method.}", r"  \label{tab:baselines}", r"\end{table}"]
open("tables/tab_baselines.tex", "w").write("\n".join(L) + "\n")

# Mixed linear network (CIFAR-100, ResNet-18)
L = [r"\begin{table}[t]", r"  \centering", r"  \small", r"  \setlength{\tabcolsep}{3.5pt}",
     r"  \begin{tabular}{@{}lcccc@{}}", r"    \toprule",
     r"    Method & Test & Remaining & Forget & MIA \\"]
for s in ["10%", "15%", "20%"]:
    L.append(r"    \midrule")
    L.append(r"    \multicolumn{5}{@{}l}{\emph{Forget set: " + s.replace("%", r"\%") + r"}} \\")
    for m, name in [("Retrained", "Retrained"), ("Unlearned(+)", r"Unlearned($+$)"), ("Unlearned(-)", r"Unlearned($-$)")]:
        r = row("mixed", s, m)
        L.append(f"    {name} & " + " & ".join(f(r[k]) for k in METRICS) + r" \\")
    g1, g2 = gap("mixed", s), gap("mixed", s, ref="Unlearned(+)")
    L.append(r"    $|\Delta|$ vs.\ Retrained & " + " & ".join(f(g1[k]) for k in METRICS) + r" \\")
    L.append(r"    $|\Delta|$ vs.\ Unlearned($+$) & " + " & ".join(f(g2[k]) for k in METRICS) + r" \\")
L += [r"    \bottomrule", r"  \end{tabular}",
      r"  \caption{Mixed linear network (last layers of ResNet-18 linearized, CIFAR-100), accuracy and MIA score in \%. "
      r"$|\Delta|$ is the absolute difference of Unlearned($-$) to the named model, computed from the logged values. "
      r"Single run per setting.}", r"  \label{tab:mixed}", r"\end{table}"]
open("tables/tab_mixed.tex", "w").write("\n".join(L) + "\n")

# Full numbers behind the ablation figure (appendix)
L = [r"\begin{table}[t]", r"  \centering", r"  \small", r"  \setlength{\tabcolsep}{3.5pt}",
     r"  \begin{tabular}{@{}llcccc@{}}", r"    \toprule",
     r"    Setting & Method & Test & Remaining & Forget & MIA \\"]
for exp, xs, _, title in PANELS:
    nm = {"forget_size": "Forget", "perturbations": "Pert.", "l2": r"$\lambda$"}[exp]
    L.append(r"    \midrule")
    for x in xs:
        xl = x.replace("%", r"\%")
        for m in ["Retrained", "Unlearned(-)"]:
            r = row(exp, x, m)
            name = "Retrained" if m == "Retrained" else r"Unlearned($-$)"
            L.append(f"    {nm}~{xl} & {name} & " + " & ".join(f(r[k]) for k in METRICS) + r" \\")
L += [r"    \bottomrule", r"  \end{tabular}",
      r"  \caption{Absolute values behind \cref{fig:ablations} (CIFAR-10, linear classifier; accuracy and MIA score in \%). "
      r"Unless varied, the settings are 10\% forget set, 500 perturbations and $\lambda=0$. Single run per setting.}",
      r"  \label{tab:ablations}", r"\end{table}"]
open("tables/tab_ablations.tex", "w").write("\n".join(L) + "\n")
open("tables/fig_ablations.tex", "w").write(
    "\\begin{figure*}[t]\n  \\centering\n  \\includegraphics[width=\\linewidth]{figures/fig_ablations.pdf}\n"
    "  \\caption{Gap between Unlearned($-$) and Retrained as a function of (a) the forget-set size, (b) the number of "
    "perturbations used for Hessian estimation and (c) the L2 regularization $\\lambda$ (CIFAR-10, linear classifier). "
    "Each curve is the absolute difference in percentage points (pp) for one metric; lower is better and 0 means identical to Retrained. "
    "Unless varied, the settings are 10\\% forget set, 500 perturbations and $\\lambda=0$. "
    "Single run per setting; absolute values in \\cref{tab:ablations}.}\n  \\label{fig:ablations}\n\\end{figure*}\n")
print("ok")
