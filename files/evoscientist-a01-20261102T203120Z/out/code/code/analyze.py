"""Produce every table (paper/tables/*.tex, results/*.csv) and figure (paper/figs/*.pdf) of the paper from results/*.csv.
Usage: python code/analyze.py"""
import os, sys, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, ScalarFormatter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES = os.path.join(ROOT, "results"); TAB = os.path.join(ROOT, "paper", "tables"); FIG = os.path.join(ROOT, "paper", "figs")
os.makedirs(TAB, exist_ok=True); os.makedirs(FIG, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lb import boards

def clean_logx(ax):
    ax.xaxis.set_minor_formatter(NullFormatter())


plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 6.5,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "figure.dpi": 150, "pdf.fonttype": 42})
ORDER = ["max", "q75", "median", "q25", "min", "trim20", "mean", "gmean", "borda", "plural"]
LAB = {"max": "max", "q75": "Q75", "median": "median", "q25": "Q25", "min": "min", "trim20": "trim-20%", "mean": "mean",
       "gmean": "geo-mean", "borda": "Borda", "plural": "plurality"}
COL = dict(zip(ORDER, ["#8c564b", "#17becf", "#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#000000", "#7f7f7f", "#ff7f0e", "#e377c2"]))
MK = dict(zip(ORDER, "v^osDPXdp*"))
BNAME = {"helm57": "HELM-MMLU", "bbh24": "BBH-24", "bbh24x": "BBH-24 (no outlier)", "oll6": "OLL-6"}
BO = ["helm57", "bbh24", "bbh24x", "oll6"]
M = {"helm57": 57, "bbh24": 24, "bbh24x": 24, "oll6": 6}

e1 = pd.read_csv(os.path.join(RES, "e1_contenders.csv"))
e1["m"] = e1.board.map(M); e1["depth"] = e1.l1 / e1.m; e1["bfrac"] = e1.br / e1.m
e5 = pd.read_csv(os.path.join(RES, "e5_uncertainty.csv"))
e5["depth"] = e5.l1 / e5.m; e5["bfrac"] = e5.br / e5.m
e2 = pd.read_csv(os.path.join(RES, "e2_rank_sweep.csv")); e2["m"] = e2.board.map(M); e2["depth"] = e2.l1 / e2.m
e4 = pd.read_csv(os.path.join(RES, "e4_scaling.csv")); e4["depth"] = e4.l1 / e4.m; e4["bfrac"] = e4.br / e4.m
e0 = pd.read_csv(os.path.join(RES, "e0_winners.csv"))


def fmt(x, d=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "--"
    if np.isinf(x):
        return r"$\infty$"
    return f"{x:.{d}f}"


# ------------------------------------------------------------------ bootstrap replicate medians
def rep_medians(kind, scen, col):
    d = e5[(e5.kind == kind) & (e5.scenario == scen)]
    g = d.groupby(["board", "rule", "rep"])[col].median().reset_index()
    return g


ci = {}
for kind in ["noise", "taskboot"]:
    g = rep_medians(kind, "ceil", "depth")
    for (b, r), s in g.groupby(["board", "rule"]):
        v = s["depth"].values
        ci[(kind, b, r)] = (np.nanquantile(v, 0.025), np.nanquantile(v, 0.975))
gb = rep_medians("noise", "ceil", "bfrac")
cib = {}
for kind in ["noise", "taskboot"]:
    g = rep_medians(kind, "ceil", "bfrac")
    for (b, r), s in g.groupby(["board", "rule"]):
        cib[(kind, b, r)] = (np.nanquantile(s["bfrac"].values, 0.025), np.nanquantile(s["bfrac"].values, 0.975))

# ------------------------------------------------------------------ Table: main results
main = e1[e1.scenario == "ceil"].groupby(["board", "rule"]).agg(depth=("depth", "median"), bfrac=("bfrac", "median"),
                                                                 br=("br", "median")).reset_index()
rows = []
for b in BO:
    for r in ORDER:
        x = main[(main.board == b) & (main.rule == r)]
        if x.empty or np.isnan(x.depth.values[0]):
            continue
        rows.append(dict(board=b, rule=r, depth=x.depth.values[0], bfrac=x.bfrac.values[0], br=x.br.values[0],
                         d_lo_n=ci[("noise", b, r)][0], d_hi_n=ci[("noise", b, r)][1],
                         d_lo_t=ci[("taskboot", b, r)][0], d_hi_t=ci[("taskboot", b, r)][1],
                         b_lo_t=cib[("taskboot", b, r)][0], b_hi_t=cib[("taskboot", b, r)][1]))
T1 = pd.DataFrame(rows); T1.to_csv(os.path.join(RES, "table_main.csv"), index=False)
with open(os.path.join(TAB, "main.tex"), "w") as f:
    f.write("\\begin{tabular}{l" + "rr" * 4 + "}\n\\toprule\n")
    f.write(" & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{BNAME[b]}}}" for b in BO) + " \\\\\n")
    f.write("Rule & " + " & ".join("depth & breadth" for b in BO) + " \\\\\n\\midrule\n")
    for r in ORDER:
        cells = []
        for b in BO:
            x = T1[(T1.board == b) & (T1.rule == r)]
            if x.empty:
                cells += ["--", "--"]
            else:
                x = x.iloc[0]
                cells.append(f"{x.depth:.2f}")
                cells.append(f"{x.bfrac:.2f}")
        f.write(LAB[r] + " & " + " & ".join(cells) + " \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# detailed table with CIs (appendix)
with open(os.path.join(TAB, "main_ci.tex"), "w") as f:
    f.write("\\begin{tabular}{llrrrrr}\n\\toprule\nBoard & Rule & depth/task & 95\\% CI (noise) & 95\\% CI (tasks) & breadth/$m$ & 95\\% CI (tasks)\\\\\n\\midrule\n")
    for b in BO:
        for r in ORDER:
            x = T1[(T1.board == b) & (T1.rule == r)]
            if x.empty:
                continue
            x = x.iloc[0]
            f.write(f"{BNAME[b]} & {LAB[r]} & {x.depth:.2f} & [{x.d_lo_n:.2f}, {x.d_hi_n:.2f}] & [{x.d_lo_t:.2f}, {x.d_hi_t:.2f}] & "
                    f"{x.bfrac:.2f} & [{x.b_lo_t:.2f}, {x.b_hi_t:.2f}] \\\\\n")
        f.write("\\midrule\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# ------------------------------------------------------------------ Figure 1: depth by rule (ceiling cap) with CIs
fig, axs = plt.subplots(1, 4, figsize=(7.0, 2.3), sharey=False)
for ax, b in zip(axs, BO):
    x = T1[T1.board == b].set_index("rule").reindex([r for r in ORDER if r in set(T1[T1.board == b].rule)])
    ypos = np.arange(len(x))[::-1]
    ax.barh(ypos, x.depth.clip(lower=1e-3), color=[COL[r] for r in x.index], height=0.65, alpha=0.85)
    lo = np.clip(x.d_lo_t.values, 1e-3, None); hi = x.d_hi_t.values
    ax.errorbar(x.depth.values, ypos, xerr=[np.clip(x.depth.values - lo, 0, None), np.clip(hi - x.depth.values, 0, None)],
                fmt="none", ecolor="k", elinewidth=0.7, capsize=1.5)
    ax.set_xscale("log"); ax.set_xlim(5e-3, 2e2 if b != "oll6" else 40)
    ax.set_yticks(ypos); ax.set_yticklabels([LAB[r] for r in x.index] if b == "helm57" else [])
    ax.set_title(BNAME[b]); ax.set_xlabel("depth per task (points)")
    ax.grid(axis="x", alpha=0.3)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_depth.pdf")); plt.close()

# ------------------------------------------------------------------ Figure 2: gain-bound sweep
e1["g"] = e1.scenario.map(lambda s: 100.0 if s == "ceil" else float(s))
fig, axs = plt.subplots(2, 4, figsize=(7.0, 3.7), sharex=True)
for j, b in enumerate(BO):
    for r in ORDER:
        d = e1[(e1.board == b) & (e1.rule == r)]
        if d.l1.isna().all():
            continue
        g = d.groupby("g").agg(feas=("l1", lambda s: np.isfinite(s).mean()))
        g2 = d[np.isfinite(d.l1)].groupby("g").bfrac.median()
        gs = sorted(d.g.unique())
        axs[0, j].plot(gs, [g.feas.get(x, np.nan) for x in gs], marker=MK[r], ms=3, lw=0.9, color=COL[r], label=LAB[r])
        axs[1, j].plot(gs, [g2.get(x, np.nan) for x in gs], marker=MK[r], ms=3, lw=0.9, color=COL[r])
    axs[0, j].set_title(BNAME[b]); axs[1, j].set_xlabel("gain bound $g$ (points)")
    axs[0, j].set_xscale("log"); axs[1, j].set_xscale("log")
    for a_ in (axs[0, j], axs[1, j]):
        clean_logx(a_); a_.set_xticks([2, 5, 10, 20, 50, 100]); a_.set_xticklabels(["2", "5", "10", "20", "50", "100"])
    axs[0, j].set_ylim(-0.05, 1.05); axs[1, j].set_ylim(0, 1.05)
    axs[0, j].grid(alpha=0.3); axs[1, j].grid(alpha=0.3)
axs[0, 0].set_ylabel("fraction of contenders\nthat can reach \\#1"); axs[1, 0].set_ylabel("breadth / $m$ (feasible ones)")
h, l = axs[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=10, frameon=False, bbox_to_anchor=(0.5, -0.02), columnspacing=0.9, handletextpad=0.3)
plt.tight_layout(rect=(0, 0.05, 1, 1)); plt.savefig(os.path.join(FIG, "fig_gain_bound.pdf")); plt.close()

# feasibility table at g=10 and g=20
with open(os.path.join(TAB, "gain10.tex"), "w") as f:
    f.write("\\begin{tabular}{l" + "rr" * 4 + "}\n\\toprule\n")
    f.write(" & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{BNAME[b]}}}" for b in BO) + " \\\\\n")
    f.write("Rule & " + " & ".join("feas. & breadth" for b in BO) + " \\\\\n\\midrule\n")
    for r in ORDER:
        cells = []
        for b in BO:
            d = e1[(e1.board == b) & (e1.rule == r) & (e1.g == 10.0)]
            if d.empty or d.l1.isna().all():
                cells += ["--", "--"]; continue
            fe = np.isfinite(d.l1).mean()
            br = d[np.isfinite(d.l1)].bfrac.median() if fe > 0 else np.nan
            cells += [f"{fe:.1f}", fmt(br) if fe > 0 else "--"]
        f.write(LAB[r] + " & " + " & ".join(cells) + " \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# ------------------------------------------------------------------ Figure 3: cost vs starting rank
fig, axs = plt.subplots(1, 4, figsize=(7.0, 2.3), sharey=True)
for ax, b in zip(axs, BO):
    for r in ORDER:
        d = e2[(e2.board == b) & (e2.rule == r)].sort_values("rule_rank")
        if d.empty:
            continue
        ax.plot(d.rule_rank, d.depth.clip(lower=1e-3), marker=MK[r], ms=2.5, lw=0.8, color=COL[r])
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(BNAME[b]); ax.set_xlabel("starting rank under the rule")
    clean_logx(ax); ax.set_xticks([2, 10, 100, 1000] if b != "helm57" else [2, 5, 10, 20, 50]); ax.set_xticklabels(["2", "10", "100", "1000"] if b != "helm57" else ["2", "5", "10", "20", "50"])
    ax.grid(alpha=0.3)
axs[0].set_ylabel("depth per task (points)")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_rank.pdf")); plt.close()

# ------------------------------------------------------------------ Figure 4: scaling with m
fig, axs = plt.subplots(2, 2, figsize=(5.2, 3.9), sharex="col")
for j, b in enumerate(["helm57", "bbh24x"]):
    for r in ORDER:
        d = e4[(e4.board == b) & (e4.rule == r)]
        if d.l1.isna().all():
            continue
        rep = d.groupby(["m", "rep"]).agg(depth=("depth", "median"), bfrac=("bfrac", "median")).reset_index()
        for k, col in enumerate(["depth", "bfrac"]):
            s = rep.groupby("m")[col].agg(["median", lambda v: np.quantile(v, .1), lambda v: np.quantile(v, .9)])
            s.columns = ["med", "lo", "hi"]
            axs[k, j].plot(s.index, s.med.clip(lower=1e-3) if k == 0 else s.med, marker=MK[r], ms=2.5, lw=0.8, color=COL[r], label=LAB[r])
    axs[0, j].set_yscale("log"); axs[0, j].set_title(BNAME[b]); axs[1, j].set_xlabel("number of tasks $m$ (random subsets)")
    axs[0, j].grid(alpha=0.3); axs[1, j].grid(alpha=0.3); axs[1, j].set_xscale("log"); axs[0, j].set_xscale("log")
    for a_ in (axs[0, j], axs[1, j]):
        clean_logx(a_); a_.set_xticks([3, 5, 10, 25, 57] if b == "helm57" else [3, 5, 8, 12, 24]); a_.set_xticklabels(["3", "5", "10", "25", "57"] if b == "helm57" else ["3", "5", "8", "12", "24"])
axs[0, 0].set_ylabel("depth per task (points)"); axs[1, 0].set_ylabel("breadth / $m$")
h, l = axs[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.02), columnspacing=0.9, handletextpad=0.3)
plt.tight_layout(rect=(0, 0.07, 1, 1)); plt.savefig(os.path.join(FIG, "fig_scaling.pdf")); plt.close()

# ------------------------------------------------------------------ bootstrap ordering stability vs mean
rows = []
for kind in ["noise", "taskboot"]:
    g = rep_medians(kind, "ceil", "depth")
    for b in BO:
        pv = g[g.board == b].pivot(index="rep", columns="rule", values="depth")
        for r in ORDER:
            if r == "mean" or r not in pv or "mean" not in pv:
                continue
            ok = pv[["mean", r]].dropna()
            rows.append(dict(kind=kind, board=b, rule=r, p_cheaper_than_mean=float((ok[r] < ok["mean"]).mean()), n=len(ok),
                             ratio_median=float(np.median(ok[r] / ok["mean"]))))
ST = pd.DataFrame(rows); ST.to_csv(os.path.join(RES, "table_vs_mean_stability.csv"), index=False)
with open(os.path.join(TAB, "stability.tex"), "w") as f:
    f.write("\\begin{tabular}{l" + "rr" * 4 + "}\n\\toprule\n")
    f.write(" & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{BNAME[b]}}}" for b in BO) + " \\\\\n")
    f.write("Rule & " + " & ".join("ratio & P" for b in BO) + " \\\\\n\\midrule\n")
    for r in ORDER:
        if r == "mean":
            continue
        cells = []
        for b in BO:
            x = ST[(ST.kind == "taskboot") & (ST.board == b) & (ST.rule == r)]
            if x.empty:
                cells += ["--", "--"]
            else:
                cells += [f"{x.ratio_median.values[0]:.2f}", f"{x.p_cheaper_than_mean.values[0]:.2f}"]
        f.write(LAB[r] + " & " + " & ".join(cells) + " \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# ------------------------------------------------------------------ winners table + Borda gap
with open(os.path.join(TAB, "winners.tex"), "w") as f:
    f.write("\\begin{tabular}{l" + "r" * 4 + "}\n\\toprule\nRule & " + " & ".join(BNAME[b] for b in BO) + " \\\\\n\\midrule\n")
    for r in ORDER:
        cells = []
        for b in BO:
            x = e0[(e0.board == b) & (e0.rule == r)]
            cells.append(str(int(x.mean_rank_of_winner.values[0])) if len(x) else "--")
        f.write(LAB[r] + " & " + " & ".join(cells) + " \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
bd = e1[(e1.rule == "borda")].copy()
bd["relgap"] = (bd.l1 - bd.l1_lb) / bd.l1.replace(0, np.nan)
print("Borda UB/LB relative gap (max) per board:\n", bd.groupby("board").relgap.max())
bd.groupby(["board"]).relgap.agg(["mean", "max"]).to_csv(os.path.join(RES, "borda_gap.csv"))

# ------------------------------------------------------------------ case study + gains tables
cs = pd.read_csv(os.path.join(RES, "e6_case.csv")); cr = pd.read_csv(os.path.join(RES, "e6_case_ranks.csv"))
with open(os.path.join(TAB, "case.tex"), "w") as f:
    f.write("\\begin{tabular}{lrrr}\n\\toprule\nRule & min.\\ depth & min.\\ breadth & rank of outlier\\\\\n\\midrule\n")
    for r in ORDER:
        a = cs[cs.rule == r]; c = cr[cr.rule == r]
        if a.empty:
            continue
        f.write(f"{LAB[r]} & {fmt(a.min_l1.values[0], 0)} & {fmt(a.min_breadth.values[0], 0)} & {int(c.outlier_rank.values[0])} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
gq = pd.read_csv(os.path.join(RES, "e7_gain_quantiles.csv"))
gq.to_csv(os.path.join(RES, "table_gain_quantiles.csv"), index=False)
print(cs); print(gq.T)
print("analysis done")
