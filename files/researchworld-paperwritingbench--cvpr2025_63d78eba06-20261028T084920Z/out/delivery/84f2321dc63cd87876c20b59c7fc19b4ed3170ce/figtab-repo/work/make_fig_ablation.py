"""work/fig_ablation.pdf (working material, not delivered): gap to Retrained vs forget size, #perturbations, lambda (CIFAR-10 linear). Data: tables/data/log_results.csv."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "tables" / "code"))
from common import ROOT, load, sel, reference

plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
                     "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
                     "axes.linewidth": 0.6, "pdf.fonttype": 42})
rows = load()
BLUE, ORANGE = "#0072B2", "#D55E00"   # Okabe-Ito; second channel = marker + linestyle
panels = [("forget_size", "(a) Forget-set size (% of training set)", [5, 10, 15], lambda v: f"{v:g}"),
          ("perturb", "(b) Number of perturbations", [250, 500, 1000], lambda v: f"{v:g}"),
          ("lambda", r"(c) L2 regularization $\lambda$", [0, 0.0005, 0.001], lambda v: f"{v:g}")]
fig, axes = plt.subplots(1, 3, figsize=(7.0, 1.85), sharey=True)
for ax, (tab, title, xs, fmt) in zip(axes, panels):
    us = {float(r["setting"]): r for r in sel(rows, tab, method="Unlearned(-)")}
    pos = range(len(xs))
    gt = [abs(us[x]["test"] - reference(rows, us[x])["test"]) for x in xs]
    gm = [abs(us[x]["mia"] - reference(rows, us[x])["mia"]) for x in xs]
    ax.plot(pos, gt, "-o", color=BLUE, lw=1.3, ms=4)
    ax.plot(pos, gm, "--s", color=ORANGE, lw=1.3, ms=4, mfc="white")
    for p, a, b in zip(pos, gt, gm):
        ax.annotate(f"{a:g}", (p, a), textcoords="offset points", xytext=(0, 5 if a >= b else -10), ha="center", fontsize=7, color=BLUE)
        ax.annotate(f"{b:.1f}", (p, b), textcoords="offset points", xytext=(0, 5 if b > a else -10), ha="center", fontsize=7, color=ORANGE)
    ax.set_xticks(list(pos)); ax.set_xticklabels([fmt(x) for x in xs]); ax.set_xlim(-0.35, len(xs) - 0.65)
    ax.set_title(title, loc="left", pad=3)
    ax.set_ylim(-3.2, 18)
    ax.grid(axis="y", lw=0.4, color="0.85"); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
axes[0].set_ylabel("Gap to Retrained (pp)")
axes[0].text(1.45, 9.0, "test accuracy", color=BLUE, ha="right", fontsize=7.5)
axes[0].text(1.3, 0.2, "MIA score", color=ORANGE, ha="left", fontsize=7.5)
fig.tight_layout(pad=0.4, w_pad=1.0)
out = ROOT / "work"; out.mkdir(exist_ok=True)
fig.savefig(out / "fig_ablation.pdf"); fig.savefig(ROOT / "work" / "fig_ablation_preview.png", dpi=200)
