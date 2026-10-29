"""Render ablation figure and LaTeX tables from figtab/results.csv.

Usage: python3 figtab/make_figures.py   (run from repo root)
Every number printed comes from figtab/results.csv, itself transcribed from the
experimental log; gaps are recomputed here and checked against the logged gaps.
"""
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

matplotlib.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.linewidth": 0.6, "pdf.fonttype": 42,
})
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = list(csv.DictReader(open(os.path.join(ROOT, "figtab/results.csv"))))
METRICS = ["test_acc", "remain_acc", "forget_acc", "mia"]

def get(table, setting, method):
    for r in rows:
        if r["table"] == table and r["setting"] == setting and r["method"] == method:
            return {m: float(r[m]) for m in METRICS}
    raise KeyError((table, setting, method))

def gap(table, setting, a="Retrained", b="Unlearned(-)"):
    x, y = get(table, setting, a), get(table, setting, b)
    return {m: round(abs(x[m] - y[m]), 1) for m in METRICS}

# ---- sanity check against gaps printed in the log ------------------------
LOGGED = {("forget_size", "5"): (0, 0, 0, 0), ("forget_size", "10"): (2, 3, 4, 1.4),
          ("forget_size", "15"): (14, 15, 14, 5.8), ("perturbations", "250"): (15, 16, 15, 6.2),
          ("perturbations", "500"): (2, 3, 4, 1.4), ("perturbations", "1000"): (0, 0, 1, 1),
          ("lambda", "0"): (2, 3, 4, 1.4), ("lambda", "0.0005"): (1, 2, 1, 0.2),
          ("lambda", "0.001"): (0, 1, 0, 0.9)}
for (t, s), v in LOGGED.items():
    g = gap(t, s)
    assert tuple(g[m] for m in METRICS) == tuple(float(x) for x in v), (t, s, g, v)
MIXED_LOGGED = {"20": (0.1, 6.6, 3.9, 0.4), "15": (0.5, 2.2, 0.0, 1.0), "10": (0.5, 2.4, 3.7, 1.3)}
for s, v in MIXED_LOGGED.items():  # mixed-linear: gap is Unlearned(+) vs Unlearned(-)
    g = gap("mixed_c100", s, "Unlearned(+)", "Unlearned(-)")
    assert (g["test_acc"], g["remain_acc"], g["forget_acc"], g["mia"]) == v, (s, g, v)

# ---- Figure: ablation gaps ------------------------------------------------
# Okabe-Ito colours + distinct markers/linestyles (second discriminating feature)
STYLE = {"test_acc": ("Test", "#0072B2", "o", "-"),
         "remain_acc": ("Remaining", "#E69F00", "s", "--"),
         "forget_acc": ("Forget", "#009E73", "^", "-."),
         "mia": ("MIA", "#CC79A7", "D", ":")}
PANELS = [("forget_size", ["5", "10", "15"], "Forget set size (% of training set)", "(a) Forget-set size"),
          ("perturbations", ["250", "500", "1000"], "Number of perturbations", "(b) Perturbations"),
          ("lambda", ["0", "0.0005", "0.001"], "$\\lambda$ ($\\ell_2$ regularisation)", "(c) Regularisation")]
fig, axes = plt.subplots(1, 3, figsize=(6.875, 2.1), sharey=True)
for ax, (t, xs, xl, title) in zip(axes, PANELS):
    g = [gap(t, s) for s in xs]
    for m in METRICS:
        lab, c, mk, ls = STYLE[m]
        ax.plot(range(3), [d[m] for d in g], color=c, marker=mk, ls=ls, lw=1.3, ms=4.5, label=lab)
    ax.axhline(0, color="0.3", lw=0.6)
    ax.set_xticks(range(3)); ax.set_xticklabels(xs)
    ax.set_xlim(-0.25, 2.25); ax.set_ylim(-0.8, 17)
    ax.set_xlabel(xl); ax.set_title(title, pad=3)
    ax.grid(axis="y", lw=0.4, color="0.85"); ax.set_axisbelow(True)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
axes[0].set_ylabel("Gap to Retrained (points)")
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.03),
           handlelength=2.6, columnspacing=1.6)
fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=1.0)
fig.savefig(os.path.join(ROOT, "figures/fig_ablation_gaps.pdf"))
fig.savefig(os.path.join(ROOT, "figures/fig_ablation_gaps.png"), dpi=200)

# ---- Tables ---------------------------------------------------------------
def f(x):  # print as logged: whole numbers without decimals, else one decimal
    return f"{x:.0f}" if float(x).is_integer() else f"{x:.1f}"

def row(name, v, bold=()):
    cells = []
    for m in METRICS:
        s = f(v[m]); cells.append(f"\\textbf{{{s}}}" if m in bold else s)
    return f"{name} & " + " & ".join(cells) + " \\\\\n"

# T1: source-free baselines (CIFAR-10, linear classifier, 10% forget)
base = {m: get("baselines", "10", m) for m in
        ["Retrained", "NegGrad", "Random Labels", "JiT", "Adversarial", "Unlearned(-)"]}
unl = [m for m in base if m != "Retrained"]
best = {m: min(unl, key=lambda k: abs(base[k][m] - base["Retrained"][m])) for m in METRICS}
t1 = "\\begin{tabular}{@{}lcccc@{}}\n\\toprule\n& Test & Remain. & Forget & MIA \\\\\n\\midrule\n"
t1 += row("Retrained", base["Retrained"]) + "\\midrule\n"
for k in unl[:-1]:
    t1 += row(k, base[k], [m for m in METRICS if best[m] == k])
t1 += row("Unlearned($-$) (ours)", base["Unlearned(-)"], [m for m in METRICS if best[m] == "Unlearned(-)"])
t1 += "\\bottomrule\n\\end{tabular}\n"
CAP1 = ("Source-free baselines on CIFAR-10 (linear classifier on ResNet-18 features, 10\\% forget set, "
        "single run; all values in \\%). Retrained is the reference: closer is better for every column. "
        "\\textbf{Bold}: unlearning method closest to Retrained in that column.")
open(os.path.join(ROOT, "tables/tab_baselines.tex"), "w").write(
    "\\begin{table}[t]\n\\centering\\small\n\\setlength{\\tabcolsep}{4pt}\n" + t1 +
    "\\caption{" + CAP1 + "}\n\\label{tab:baselines}\n\\end{table}\n")

# T2: mixed linear network, CIFAR-100
t2 = "\\begin{tabular}{@{}clcccc@{}}\n\\toprule\nForget & Method & Test & Remain. & Forget & MIA \\\\\n\\midrule\n"
for i, s in enumerate(["10", "15", "20"]):
    if i: t2 += "\\midrule\n"
    for j, m in enumerate(["Retrained", "Unlearned(+)", "Unlearned(-)"]):
        lead = f"{s}\\%" if j == 0 else ""
        t2 += lead + " & " + row(m.replace("(-)", "($-$)").replace("(+)", "($+$)"), get("mixed_c100", s, m))
    g = gap("mixed_c100", s, "Unlearned(+)", "Unlearned(-)")
    t2 += " & \\quad $|\\Delta|$ vs.\\ ($+$) & " + " & ".join(f(g[m]) for m in METRICS) + " \\\\\n"
    gr = gap("mixed_c100", s)
    t2 += " & \\quad $|\\Delta|$ vs.\\ Retrained & " + " & ".join(f(gr[m]) for m in METRICS) + " \\\\\n"
t2 += "\\bottomrule\n\\end{tabular}\n"
CAP2 = ("Mixed linear network (last layers of ResNet-18 linearised) on CIFAR-100, single run, values in \\%. "
        "Rows $|\\Delta|$ give the absolute difference of Unlearned($-$) (source-free) to Unlearned($+$) (exact retain Hessian; "
        "the gap rows printed in the log) and to Retrained (recomputed from the logged values).")
open(os.path.join(ROOT, "tables/tab_mixed_linear.tex"), "w").write(
    "\\begin{table}[t]\n\\centering\\small\n\\setlength{\\tabcolsep}{3pt}\n" + t2 +
    "\\caption{" + CAP2 + "}\n\\label{tab:mixed}\n\\end{table}\n")

# T3: ablation numbers (appendix); gap to Retrained, each setting once
t3 = ("\\begin{tabular}{@{}llccccc@{}}\n\\toprule\n & Setting & Test & Remain. & Forget & MIA & \\\\\n"
      "\\midrule\n")
def abl(title, t, xs, fmt):
    out = f"\\multicolumn{{6}}{{@{{}}l}}{{\\emph{{{title}}}}} \\\\\n"
    for s in xs:
        out += f"& {fmt(s)} & " + " & ".join(f(get(t, s, 'Unlearned(-)')[m]) for m in METRICS) + " & \\\\\n"
        g = gap(t, s)
        out += "& \\quad $|\\Delta|$ to Retrained & " + " & ".join(f(g[m]) for m in METRICS) + " & \\\\\n"
    return out
t3 = "\\begin{tabular}{@{}llcccc@{}}\n\\toprule\n& Setting & Test & Remain. & Forget & MIA \\\\\n\\midrule\n"
def abl(title, t, xs, fmt):
    out = f"\\multicolumn{{6}}{{@{{}}l}}{{\\emph{{{title}}}}} \\\\\n"
    for s in xs:
        out += f"& {fmt(s)} & " + " & ".join(f(get(t, s, 'Unlearned(-)')[m]) for m in METRICS) + " \\\\\n"
        g = gap(t, s)
        out += "& \\quad $|\\Delta|$ to Retrained & " + " & ".join(f(g[m]) for m in METRICS) + " \\\\\n"
    return out
t3 += abl("Forget-set size (retrained reference differs per size)", "forget_size", ["5", "10", "15"], lambda s: s + "\\%")
t3 += "\\midrule\n" + abl("Number of perturbations (10\\% forget)", "perturbations", ["250", "500", "1000"], lambda s: s + " pert.")
t3 += "\\midrule\n" + abl("$\\ell_2$ regularisation (10\\% forget)", "lambda", ["0", "0.0005", "0.001"], lambda s: "$\\lambda{=}" + s + "$")
t3 += "\\bottomrule\n\\end{tabular}\n"
CAP3 = ("Ablations for Unlearned($-$) on CIFAR-10 (linear classifier), single run, values in \\%. "
        "$|\\Delta|$ rows give the absolute difference to Retrained (percentage points) as logged. "
        "The 10\\% forget-set, 500-perturbation and $\\lambda{=}0$ settings are the same run.")
open(os.path.join(ROOT, "tables/tab_ablations.tex"), "w").write(
    "\\begin{table}[t]\n\\centering\\small\n\\setlength{\\tabcolsep}{3pt}\n" + t3 +
    "\\caption{" + CAP3 + "}\n\\label{tab:ablations}\n\\end{table}\n")
print("ok")
