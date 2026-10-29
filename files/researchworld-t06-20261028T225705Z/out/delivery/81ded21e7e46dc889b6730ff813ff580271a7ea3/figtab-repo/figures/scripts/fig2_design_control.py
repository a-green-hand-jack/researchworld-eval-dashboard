"""Fig. 2 (C3): (a) same-question design contrast, MT-Bench expert vs GPT-4 judge on the 1,814 questions present in both;
(b) size/structure controls: cheapest top-1 attack (remove | flip) as % of N for Arena subsampled to MT-Bench's N, Arena restricted to
its top-6 models, MT-Bench, and NBA single seasons. Rows with [n=..]: dot = median, bar = 2.5-97.5 percentile over n subsamples. Full datasets: dot = original data, bar = 2.5-97.5 percentile over bootstrap resamples (none yet = no bar).
Reads results/mtbench_contrast.csv, arena_controls.csv, commonN.csv (random-6 control), decisions_mtbench_*.csv, nba_seasons.csv. Usage: fig2_design_control.py [RESULTS_DIR] [OUT_DIR]"""
import sys, os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullFormatter
sys.path.insert(0, os.path.dirname(__file__)); import style, common
res = sys.argv[1] if len(sys.argv) > 1 else "results"; out = sys.argv[2] if len(sys.argv) > 2 else "figures"
style.apply(); os.makedirs(out, exist_ok=True)
MODES = [("drop", "remove", "o", "#0072B2"), ("flip", "flip", "s", "#D55E00")]
def row(ax, y, v, n, N, mk, col, off, point=None):
    """v = replicate budgets (comparisons), N = size(s); point = original-data budget (dot) if given, else the median of v."""
    v = np.asarray(v, float); N = np.broadcast_to(np.asarray(N, float), v.shape); ok = np.isfinite(v); v = v[ok] / N[ok] * 100
    if len(v) == 0 and point is None: return
    m = point if point is not None else np.median(v)
    lo, hi = np.percentile(v, [2.5, 97.5]) if len(v) > 1 else (m, m)
    ax.errorbar(m, y + off, xerr=[[m - lo], [hi - m]], fmt=mk, color=col, ms=3.8, lw=0.9, capsize=1.5)
fig, (a, b) = plt.subplots(1, 2, figsize=(style.TEXTW, 2.9), gridspec_kw=dict(width_ratios=[1, 1.25]))
# (a) design contrast on identical questions
mc = pd.read_csv(f"{res}/mtbench_contrast.csv")
rows_a = [("GPT-4 judge\n(1,814 items)", ["gpt4", "gpt4_bootstrap"]), ("expert, 1 vote/item\n(1,814 items)", ["human_one_per_item"]), ("expert, all votes\n(3,355 votes)", ["human_all_judgements"])]
for i, (lab, srcs) in enumerate(rows_a[::-1]):
    g = mc[mc.source.isin(srcs)]
    for (mode, _, mk, col), off in zip(MODES[:2], (-0.12, 0.12)):
        boot = g[g.rep >= 0]; orig = g[g.rep < 0]
        row(a, i, boot[f"top1_{mode}"], len(boot), g.N.iloc[0], mk, col, off, point=float(orig[f"top1_{mode}"].iloc[0]) / g.N.iloc[0] * 100 if len(orig) and srcs[0] in ("gpt4", "human_all_judgements") else None)
a.set_yticks(range(3)); a.set_yticklabels([r[0] for r in rows_a[::-1]]); a.set_xscale("log"); a.set_ylim(-0.6, 2.6); a.set_xticks([1, 2, 5, 10])
a.set_xlabel("smallest top-1 change found, $k/N$ (%)"); a.set_title("(a) same questions", loc="left"); a.grid(axis="x", alpha=0.25, lw=0.4)
# (b) controls
ac = pd.read_csv(f"{res}/arena_controls.csv"); ns = pd.read_csv(f"{res}/nba_seasons.csv"); ns = ns[(ns.replicate < 0)]
dec = common.load(res, "decisions")
def full(k, mode):
    d = dec[k]; o = d[(d.replicate < 0) & (d.decision == "top1") & (d.method == "influence_exact") & (d.perturbation_type == mode)]
    bs = d[(d.replicate >= 0) & (d.decision == "top1") & (d.method == "influence_exact") & (d.perturbation_type == mode)].budget_k.to_numpy()
    return bs, int(d.N.iloc[0]), float(o.budget_k.iloc[0]) / int(d.N.iloc[0]) * 100
spec = []
for lab, ctl, Nv in [("Arena, $N{=}2400$, 64 models", "subN_all64", 2400), ("Arena, $N{=}3355$, 64 models", "subN_all64", 3355), ("Arena top-6, $N{=}2400$", "top6_subN", 2400)]:
    g = ac[(ac.control == ctl) & (ac.N == Nv)]; spec.append((lab, {m: (g[f"top1_{m}"].to_numpy(), Nv) for m in ("drop", "flip")}, len(g)))
cn = pd.read_csv(f"{res}/commonN.csv"); g = cn[(cn.control == "N+p") & (cn.dataset == "arena55k")]
spec.append(("Arena random 6 models, $N{=}2000$", {m: (g[f"top1_{m}"].to_numpy(), 2000) for m in ("drop", "flip")}, len(g)))
g = ac[ac.control == "top6_full"]; spec.append(("Arena top-6, all 3,222", {m: (g[f"top1_{m}"].to_numpy(), 3222) for m in ("drop", "flip")}, 1))
for k, lab in [("mtbench_human", "MT-Bench expert (3,355)"), ("mtbench_gpt4", "MT-Bench GPT-4 (2,400)")]:
    if k in dec: spec.append((lab, {m: full(k, m) for m in ("drop", "flip")}, 1))
spec.append(("NBA seasons ($N$: 192-1,230)", {m: (ns[f"top1_{m}"].to_numpy(), ns.N.to_numpy()) for m in ("drop", "flip")}, len(ns)))
if "arena55k" in dec: spec.append(("Arena, all 57,477", {m: full("arena55k", m) for m in ("drop", "flip")}, 1))
for i, (lab, d, n) in enumerate(spec[::-1]):
    for (mode, _, mk, col), off in zip(MODES, (-0.12, 0.12)): row(b, i, d[mode][0], n, d[mode][1], mk, col, off, point=(d[mode][2] if len(d[mode]) > 2 else None))
b.set_yticks(range(len(spec))); b.set_yticklabels([f"{s[0]}" + (f"  [n={s[2]}]" if s[2] > 1 else "") for s in spec[::-1]]); b.set_xscale("log")
b.set_xlabel("smallest top-1 change found, $k/N$ (%)"); b.set_title("(b) size and structure controls", loc="left"); b.grid(axis="x", alpha=0.25, lw=0.4)
for ax in (a, b): ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}")); ax.xaxis.set_minor_formatter(NullFormatter())
h = [plt.Line2D([], [], marker=m[2], color=m[3], ls="none", ms=4, label=m[1]) for m in MODES]
fig.legend(handles=h, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.04), fontsize=7)
fig.tight_layout(w_pad=0.6, rect=(0, 0.04, 1, 1)); fig.savefig(f"{out}/fig2_design_control.pdf"); fig.savefig(f"{out}/fig2_design_control.png", dpi=200)
