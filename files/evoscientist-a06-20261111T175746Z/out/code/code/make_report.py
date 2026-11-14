"""Build every figure (paper/figs/*.pdf) and LaTeX table (paper/tables/*.tex) used in the paper from results/*.json.

python code/make_report.py
"""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("paper/figs", exist_ok=True); os.makedirs("paper/tables", exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 6.5,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.25})
PTS = 100.0  # report accuracy differences in percentage points
COL = {"naive": "#d62728", "boot_opt": "#9467bd", "boot_632": "#8c564b", "cv": "#2ca02c", "eb": "#ff7f0e", "split50": "#1f77b4",
       "split20": "#17becf", "maxt": "#7f7f7f"}
NAMES = {"naive": "naive (reuse)", "boot_opt": "bootstrap optimism", "boot_632": ".632 bootstrap", "cv": "5-fold nested CV",
         "eb": "paired EB shrinkage", "split50": "split 50/50", "split20": "split 20/80 (sel/rep)"}


def load(p):
    return json.load(open(p)) if os.path.exists(p) else None


synth = load("results/synth.json"); needle = load("results/synth_needle.json")
real = {m: load(f"results/real_{m}.json") for m in ("0.5B", "1.5B")}
dec = {m: load(f"results/dec_{m}.json") for m in ("0.5B", "1.5B")}
MODEL_LONG = {"0.5B": "Qwen2.5-0.5B-Instruct", "1.5B": "Qwen2.5-1.5B-Instruct"}


def fmt(x, d=2, sign=False):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s


# ------------------------------------------------------------------------------------------- Figure 1: scaling
fig, ax = plt.subplots(1, 4, figsize=(7.2, 2.25))
if synth:
    rows = [r for r in synth["rows"] if r["kind"] == "scaleK" and abs(r["rho_target"] - 0.3) < 1e-9]
    for n, c in zip((100, 400, 1600), ("#d62728", "#1f77b4", "#2ca02c")):
        rr = sorted([r for r in rows if r["n"] == n], key=lambda r: r["K"])
        Ks = [r["K"] for r in rr]
        ax[0].errorbar(Ks, [PTS * r["naive"]["bias"] for r in rr], yerr=[PTS * 1.96 * r["naive"]["bias_se"] for r in rr], fmt="o", ms=3, color=c, label=f"n={n}")
        ax[0].plot(Ks, [PTS * r["pred_null"] for r in rr], "-", color=c, lw=0.9)
        ax[0].plot(Ks, [PTS * r["pred_hoeffding"] for r in rr], ":", color=c, lw=0.9)
    ax[0].set_xscale("log"); ax[0].set_xlabel("number of searched configs $K$"); ax[0].set_ylabel("reported $-$ true (pts)")
    ax[0].set_title("(a) synthetic null: bias vs $K$"); ax[0].legend(loc="upper left", title="dots: sim; solid: Prop. 2;\ndotted: Prop. 1(ii)", title_fontsize=5, fontsize=5.5)
    # (b) rho dependence at n=400
    for rho, c in zip((0.0, 0.3, 0.7), ("#444444", "#1f77b4", "#ff7f0e")):
        rr = sorted([r for r in synth["rows"] if r["kind"] == "scaleK" and abs(r["rho_target"] - rho) < 1e-9 and r["n"] == 400], key=lambda r: r["K"])
        ax[1].plot([r["K"] for r in rr], [PTS * r["naive"]["bias"] for r in rr], "o-", ms=3, color=c, lw=0.9,
                   label=f"$\\hat\\rho$={np.mean([r['rho_hat'] for r in rr]):.2f}")
    ax[1].set_xscale("log"); ax[1].set_xlabel("$K$"); ax[1].set_title("(b) shared difficulty"); ax[1].legend(loc="upper left")
if needle:
    rr = sorted(needle["rows"], key=lambda r: r["mu_top_gap"])
    g = [PTS * r["mu_top_gap"] for r in rr]
    for m in ("naive", "boot_opt", "eb", "split50", "cv"):
        ax[2].plot(g, [PTS * r[m]["bias"] for r in rr], "o-", ms=3, lw=0.9, color=COL[m], label=NAMES[m])
    ax[2].axhline(0, color="k", lw=0.5); ax[2].set_xlabel("true lead of best over 2nd best (pts)")
    ax[2].set_title("(c) one clear winner"); ax[2].legend(loc="upper right", fontsize=5)
cols = {"0.5B": "#1f77b4", "1.5B": "#d62728"}
for m in ("0.5B", "1.5B"):
    d = real[m]
    if not d:
        continue
    for n, ls in ((100, "o"), (400, "s")):
        rr = sorted([r for r in d["rows"] if r["opt"] == "exh" and r["n"] == n], key=lambda r: r["K"])
        ax[3].errorbar([r["K"] for r in rr], [PTS * r["naive"]["bias"] for r in rr], yerr=[PTS * 1.96 * r["naive"]["bias_se"] for r in rr],
                       fmt=ls, ms=3, color=cols[m], alpha=0.9 if n == 100 else 0.55, label=f"{m}, n={n}")
        ax[3].plot([r["K"] for r in rr], [PTS * r["pred_gauss"] for r in rr], "-", color=cols[m], lw=0.8, alpha=0.9 if n == 100 else 0.55)
ax[3].set_xscale("log"); ax[3].set_xlabel("$K$"); ax[3].set_title("(d) real LLM (MMLU-Pro)"); ax[3].legend(loc="upper left", fontsize=5)
from matplotlib.ticker import ScalarFormatter
for i_, tk in ((0, [2, 10, 100, 1000]), (1, [2, 10, 100, 1000]), (3, [2, 4, 8, 16, 32])):
    ax[i_].set_xticks(tk); ax[i_].xaxis.set_major_formatter(ScalarFormatter()); ax[i_].minorticks_off()
plt.tight_layout(pad=0.4); plt.savefig("paper/figs/fig_scaling.pdf"); plt.close()


# ------------------------------------------------------------------------------------------- Table: real-LLM winner's curse
def tab_curse():
    lines = []
    for m in ("0.5B", "1.5B"):
        d = real[m]
        if not d:
            continue
        for opt in ("exh", "sh"):
            for n in (100, 200, 400, 800):
                rr = sorted([r for r in d["rows"] if r["opt"] == opt and r["n"] == n], key=lambda r: r["K"])
                if not rr:
                    continue
                for r in rr:
                    if r["K"] not in (4, d["K"]) and not (r["K"] == 16 and d["K"] > 16):
                        continue
                    pred = fmt(PTS * r["pred_gauss"], 2) if opt == "exh" else "--"
                    cost = f"{r['budget']}" if opt == "sh" else f"{r['K']*r['n']}"
                    lines.append(f"{m} & {opt.upper()} & {r['K']} & {n} & {cost} & {fmt(PTS*r['truth_mean'],1)} & "
                                 f"{fmt(PTS*(r['truth_mean']+r['naive']['bias']),1)} & {fmt(PTS*r['naive']['bias'],2,True)} $\\pm$ {fmt(PTS*1.96*r['naive']['bias_se'],2)} & {pred} & "
                                 f"{fmt(PTS*r['naive']['cov'],0)} \\\\")
    open("paper/tables/tab_curse.tex", "w").write("\n".join(lines) + "\n")


tab_curse()


# ------------------------------------------------------------------------------------------- Table: protocols
def proto_rows(r, label):
    out = []
    for m in ("naive", "split20", "split50", "cv", "boot_opt", "eb"):
        if m not in r:
            continue
        x = r[m]
        out.append(f"{label} & {NAMES[m]} & {fmt(PTS*x['bias'],2,True)} $\\pm$ {fmt(PTS*1.96*x['bias_se'],2)} & {fmt(PTS*x['rmse'],2)} & "
                   f"{fmt(PTS*x['cov'],0) if 'cov' in x else '--'} & {fmt(PTS*x['width'],1) if 'width' in x else '--'} \\\\")
    if "maxt" in r:
        out.append(f"{label} & max-$T$ simultaneous CI & -- & -- & {fmt(PTS*r['maxt']['cov'],0)} & {fmt(PTS*r['maxt']['width'],1)} \\\\")
    return out


def tab_protocols():
    lines = []
    if synth:
        for regime, lab in (("null", "synth null"), ("needle", "synth needle")):
            r = [x for x in synth["rows"] if x["kind"] == "regimes" and x["regime"] == regime and x["K"] == 32 and x["n"] == 200 and x["opt"] == "exh"]
            if r:
                lines += proto_rows(r[0], lab)
                lines.append("\\midrule")
        r = [x for x in synth["rows"] if x["kind"] == "regimes" and x["regime"] == "spread3" and x["K"] == 32 and x["n"] == 200 and x["opt"] == "exh"]
        if r:
            open("paper/tables/tab_protocols_spread.tex", "w").write("\n".join(proto_rows(r[0], "synth spread")) + "\n")
    for m in ("0.5B", "1.5B"):
        d = real[m]
        if d:
            r = [x for x in d["rows"] if x["opt"] == "exh" and x["K"] == d["K"] and x["n"] == 200]
            if r:
                lines += proto_rows(r[0], f"{m} real")
                lines.append("\\midrule")
    if lines and lines[-1] == "\\midrule":
        lines = lines[:-1]
    open("paper/tables/tab_protocols.tex", "w").write("\n".join(lines) + "\n")


tab_protocols()


# ------------------------------------------------------------------------------------------- Figure 2: protocol bars across settings
def fig_protocols():
    settings = []
    if synth:
        for regime, lab in (("null", "synth null"), ("heavy", "synth heavy-tail"), ("needle", "synth needle")):
            for (K, n) in ((32, 200), (32, 800)):
                r = [x for x in synth["rows"] if x["kind"] == "regimes" and x["regime"] == regime and x["K"] == K and x["n"] == n and x["opt"] == "exh"]
                if r:
                    settings.append((f"{lab}\nK={K}, n={n}", r[0]))
    for m in ("0.5B", "1.5B"):
        d = real[m]
        if d:
            for n in (200, 800):
                r = [x for x in d["rows"] if x["opt"] == "exh" and x["K"] == d["K"] and x["n"] == n]
                if r:
                    settings.append((f"real {m}\nK={d['K']}, n={n}", r[0]))
    if not settings:
        return
    ms = ["naive", "split50", "cv", "boot_opt", "eb"]
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.5))
    w = 0.16
    for j, mth in enumerate(ms):
        ax[0].bar(np.arange(len(settings)) + (j - 2) * w, [PTS * s[1][mth]["bias"] for s in settings], w, yerr=[PTS * 1.96 * s[1][mth]["bias_se"] for s in settings],
                  color=COL[mth], label=NAMES[mth], error_kw=dict(lw=0.6))
        ax[1].bar(np.arange(len(settings)) + (j - 2) * w, [PTS * s[1][mth]["cov"] for s in settings], w, color=COL[mth])
    ax[0].axhline(0, color="k", lw=0.5); ax[0].set_ylabel("bias: reported $-$ true of chosen config (pts)")
    ax[1].axhline(95, color="k", lw=0.8, ls="--"); ax[1].set_ylabel("coverage of nominal-95% CI (%)"); ax[1].set_ylim(0, 105)
    for a_ in ax:
        a_.set_xticks(np.arange(len(settings))); a_.set_xticklabels([s[0] for s in settings], rotation=60, ha="right", fontsize=5.5)
    ax[0].legend(fontsize=5.5, loc="upper right"); plt.tight_layout(pad=0.4); plt.savefig("paper/figs/fig_protocols.pdf"); plt.close()


fig_protocols()


# ------------------------------------------------------------------------------------------- decisions
def tab_decisions():
    L, Lf = [], []
    for m in ("0.5B", "1.5B"):
        d = dec[m]
        if not d:
            continue
        for r in d["claims"]:
            if r["n"] not in (200, 800):
                continue
            row = (f"{m} & {r['base_rank']+1} & {r['K']} & {r['n']} & {fmt(PTS*r['mean_rep_impr'],2,True)} & {fmt(PTS*r['mean_true_impr'],2,True)} & "
                   f"{fmt(PTS*r['frac_true_impr_le0'],0)} & {fmt(PTS*r['naive_claim_rate'],1)} & {fmt(PTS*r['naive_false_claim_rate'],1)} & "
                   f"{fmt(PTS*r['split_claim_rate'],1)} & {fmt(PTS*r['split_false_claim_rate'],1)} & {fmt(PTS*r['maxt_claim_rate'],1)} & {fmt(PTS*r['maxt_false_claim_rate'],1)} \\\\")
            Lf.append(row)
            if r["n"] == 200:
                L.append(row)
    open("paper/tables/tab_claims.tex", "w").write("\n".join(L) + "\n")
    open("paper/tables/tab_claims_full.tex", "w").write("\n".join(Lf) + "\n")
    L = []
    for m in ("0.5B", "1.5B"):
        d = dec[m]
        if not d:
            continue
        for r in d["systems"]:
            if r["n"] not in (100, 400, 800):
                continue
            L.append(f"{m} & {r['KA']} & {r['KB']} & {r['n']} & {fmt(PTS*r['mean_rep_gap'],2,True)} & {fmt(PTS*r['mean_true_gap'],2,True)} & "
                     f"{fmt(PTS*r['p_rep_A_better'],0)} & {fmt(PTS*r['p_true_A_better'],0)} & {fmt(PTS*r['naive_claim_rate'],1)} & {fmt(PTS*r['naive_claim_given_A_not_better'],1)} & "
                     f"{fmt(PTS*r['split_claim_rate'],1)} & {fmt(PTS*r['split_claim_given_A_not_better'],1)} \\\\")
    open("paper/tables/tab_systems.tex", "w").write("\n".join(L) + "\n")
    L = []
    for m in ("0.5B", "1.5B"):
        d = dec[m]
        if not d:
            continue
        seen = set()
        for r in d["shift"]:
            if r["n"] not in (100, 400) or (r["K"], r["n"]) in seen:
                continue
            seen.add((r["K"], r["n"]))
            L.append(f"{m} & {r['K']} & {r['n']} & {fmt(PTS*r['naive'],1)} & {fmt(PTS*r['t_in'],1)} & {fmt(PTS*r['t_out'],1)} & "
                     f"{fmt(PTS*r['curse'],2,True)} $\\pm$ {fmt(PTS*1.96*r['curse_se'],2)} & {fmt(PTS*r['shift'],2,True)} $\\pm$ {fmt(PTS*1.96*r['shift_se'],2)} & {fmt(PTS*r['regret_out'],2)} \\\\")
    open("paper/tables/tab_shift.tex", "w").write("\n".join(L) + "\n")


tab_decisions()


# ------------------------------------------------------------------------------------------- gain decomposition
def tab_gain():
    L = []
    for m in ("0.5B", "1.5B"):
        d = real[m]
        if not d:
            continue
        for n in (100, 200, 400, 800):
            r = [x for x in d["rows"] if x["opt"] == "exh" and x["K"] == d["K"] and x["n"] == n]
            if not r:
                continue
            r = r[0]
            rep = r["truth_mean"] + r["naive"]["bias"] - r["mean_cfg"]
            tru = r["truth_mean"] - r["mean_cfg"]
            orc = r["oracle_mean"] - r["mean_cfg"]
            L.append(f"{m} & {d['K']} & {n} & {fmt(PTS*rep,2,True)} & {fmt(PTS*tru,2,True)} & {fmt(PTS*orc,2,True)} & {fmt(100*tru/rep,0) if rep > 0 else '--'} \\\\")
    open("paper/tables/tab_gain.tex", "w").write("\n".join(L) + "\n")


tab_gain()


# ------------------------------------------------------------------------------------------- split sweep figure
def fig_split():
    sp = {m: load(f"results/split_{m}.json") for m in ("0.5B", "1.5B")}
    if not any(sp.values()):
        return
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 1.8))
    for m, ls in (("0.5B", "-"), ("1.5B", "--")):
        d = sp[m]
        if not d:
            continue
        for row, c in zip(d["rows"], ("#d62728", "#ff7f0e", "#2ca02c", "#1f77b4")):
            n = row["n"]
            fr = sorted(float(f) for f in row["split"])
            ax[0].plot(fr, [PTS * row["split"][str(f)]["rmse"] for f in fr], ls, color=c, lw=1, marker="o", ms=2, label=f"{m} n={n}" if m == "0.5B" else None)
            ax[0].plot([1.0], [PTS * row["full"]["rmse"]], "x", color=c, ms=4)
            ax[1].plot(fr, [PTS * (row["split"][str(f)]["truth"] - row["oracle"] * 0 - row["full"]["truth"]) for f in fr], ls, color=c, lw=1, marker="o", ms=2)
            ax[2].plot(fr, [PTS * row["split"][str(f)]["width"] for f in fr], ls, color=c, lw=1, marker="o", ms=2)
    ax[0].set_ylabel("RMSE of reported score (pts)"); ax[0].set_title("(a) error of the reported score")
    ax[1].set_ylabel("delivered true acc. minus\nfull-$n$ selection (pts)"); ax[1].set_title("(b) cost to the delivered config")
    ax[2].set_ylabel("mean 95% CI width (pts)"); ax[2].set_title("(c) CI width")
    for a_ in ax:
        a_.set_xlabel("selection fraction of benchmark", fontsize=7)
    ax[0].legend(fontsize=5, loc="upper left")
    plt.tight_layout(pad=0.4); plt.savefig("paper/figs/fig_split.pdf"); plt.close()


fig_split()


# ------------------------------------------------------------------------------------------- fresh-question validation
def tab_fresh():
    L1, L2 = [], []
    for m in ("0.5B", "1.5B"):
        d = load(f"results/fresh_{m}.json")
        if not d:
            continue
        rs = d["real_selection"]
        L1.append(f"{m} & {d['K']} & {d['N']} & {d['Nf']} & {fmt(PTS*rs['pool_acc'],1)} & {fmt(PTS*rs['fresh_acc'],1)} "
                  f"[{fmt(PTS*rs['fresh_ci'][0],1)}, {fmt(PTS*rs['fresh_ci'][1],1)}] & {fmt(PTS*rs['mean_pool_acc'],1)} & {fmt(PTS*rs['mean_fresh_acc'],1)} & "
                  f"{rs['fresh_rank']} & {fmt(d['corr_pool_fresh'],2)} & {fmt(d['slope_fresh_on_pool'],2)} \\\\")
        for r in d["rows"]:
            if r["K"] == d["K"] and r["n"] in (100, 200, 400, 800):
                L2.append(f"{m} & {r['K']} & {r['n']} & {fmt(PTS*r['bias_pool'],2,True)} & {fmt(PTS*r['bias_fresh'],2,True)} "
                          f"[{fmt(PTS*r['bias_fresh_ci'][0],2,True)}, {fmt(PTS*r['bias_fresh_ci'][1],2,True)}] & {fmt(PTS*r['bias_fresh_adj'],2,True)} "
                          f"[{fmt(PTS*r['bias_fresh_adj_ci'][0],2,True)}, {fmt(PTS*r['bias_fresh_adj_ci'][1],2,True)}] \\\\")
    open("paper/tables/tab_fresh_real.tex", "w").write("\n".join(L1) + "\n")
    open("paper/tables/tab_fresh_sim.tex", "w").write("\n".join(L2) + "\n")


tab_fresh()


# ------------------------------------------------------------------------------------------- OOS-truth sensitivity (pool vs without-replacement truth)
def tab_oos():
    L = []
    for m in ("0.5B", "1.5B"):
        d = real[m]
        if not d:
            continue
        for n in (100, 400, 800):
            r = [x for x in d["rows"] if x["opt"] == "exh" and x["K"] == d["K"] and x["n"] == n]
            if r and "oos" in r[0]:
                r = r[0]
                L.append(f"{m} & {n} & {fmt(PTS*r['naive']['bias'],2,True)} & {fmt(PTS*r['oos']['naive']['bias'],2,True)} & {fmt(PTS*r['boot_opt']['bias'],2,True)} & {fmt(PTS*r['oos']['boot_opt']['bias'],2,True)} \\\\")
    open("paper/tables/tab_oos.tex", "w").write("\n".join(L) + "\n")


tab_oos()


# ------------------------------------------------------------------------------------------- synthetic tables
def tab_synth_scale():
    if not synth:
        return
    L = []
    for rho in (0.0, 0.3, 0.7):
        for K in (4, 32, 256, 1000):
            cells = []
            for n in (100, 400, 1600):
                r = [x for x in synth["rows"] if x["kind"] == "scaleK" and abs(x["rho_target"] - rho) < 1e-9 and x["K"] == K and x["n"] == n][0]
                cells.append(f"{fmt(PTS*r['naive']['bias'],2)} ({fmt(PTS*r['pred_null'],2)}) [{fmt(PTS*r['naive']['cov'],0)}]")
            rr = [x for x in synth["rows"] if x["kind"] == "scaleK" and abs(x["rho_target"] - rho) < 1e-9 and x["K"] == K and x["n"] == 100][0]
            L.append(f"{fmt(rr['rho_hat'],2)} & {K} & " + " & ".join(cells) + " \\\\")
    open("paper/tables/tab_synth_scale.tex", "w").write("\n".join(L) + "\n")


tab_synth_scale()


def tab_needle_lower():
    if needle:
        L = []
        for r in sorted(needle["rows"], key=lambda r: r["mu_top_gap"]):
            d = float(r["regime"][6:])
            L.append(f"{fmt(PTS*d,0)} & {fmt(PTS*r['mu_top_gap'],1)} & {fmt(PTS*r['naive']['bias'],2,True)} & {fmt(PTS*r['boot_opt']['bias'],2,True)} & "
                     f"{fmt(PTS*r['eb']['bias'],2,True)} ({fmt(PTS*r['eb']['cov'],0)}) & {fmt(PTS*r['cv']['bias'],2,True)} & {fmt(PTS*r['split50']['bias'],2,True)} \\\\")
        open("paper/tables/tab_needle.tex", "w").write("\n".join(L) + "\n")
    if synth:
        L = []
        for regime, lab in (("null", "null"), ("spread3", "spread (sd 3 pts)"), ("needle", "needle (+5 pts)"), ("heavy", "heavy-tailed")):
            for (K, n, o) in ((32, 200, "exh"), (32, 800, "exh"), (256, 400, "exh"), (32, 200, "sh")):
                r = [x for x in synth["rows"] if x["kind"] == "regimes" and x["regime"] == regime and x["K"] == K and x["n"] == n and x["opt"] == o]
                if r:
                    r = r[0]
                    L.append(f"{lab} & {o.upper()} & {K} & {n} & {fmt(PTS*r['naive_lower1']['cov'],0)} ({fmt(PTS*r['naive_lower1']['margin'],1)}) & "
                             f"{fmt(PTS*r['maxt_lower1']['cov'],0)} ({fmt(PTS*r['maxt_lower1']['margin'],1)}) & {fmt(PTS*r['hoeff_lower1']['cov'],0)} ({fmt(PTS*r['hoeff_lower1']['margin'],1)}) \\\\")
        open("paper/tables/tab_lower.tex", "w").write("\n".join(L) + "\n")
    # real lower bounds
    L = []
    for m in ("0.5B", "1.5B"):
        d = real[m]
        if not d:
            continue
        for n in (100, 200, 400):
            r = [x for x in d["rows"] if x["opt"] == "exh" and x["K"] == d["K"] and x["n"] == n]
            if r:
                r = r[0]
                L.append(f"{m} & {d['K']} & {n} & {fmt(PTS*r['naive_lower1']['cov'],0)} ({fmt(PTS*r['naive_lower1']['margin'],1)}) & "
                         f"{fmt(PTS*r['maxt_lower1']['cov'],0)} ({fmt(PTS*r['maxt_lower1']['margin'],1)}) & {fmt(PTS*r['hoeff_lower1']['cov'],0)} ({fmt(PTS*r['hoeff_lower1']['margin'],1)}) \\\\")
    open("paper/tables/tab_lower_real.tex", "w").write("\n".join(L) + "\n")


tab_needle_lower()


def tab_curse_main():
    L = []
    for m, sets in (("0.5B", [("exh", 32, 100), ("exh", 32, 200), ("exh", 32, 400), ("exh", 32, 800), ("exh", 4, 100), ("exh", 8, 100), ("exh", 16, 100), ("sh", 32, 100), ("sh", 32, 400)]),
                    ("1.5B", [("exh", 16, 100), ("exh", 16, 200), ("exh", 16, 400), ("exh", 16, 800), ("exh", 4, 100), ("exh", 8, 100), ("sh", 16, 100), ("sh", 16, 400)])):
        d = real[m]
        if not d:
            continue
        for (opt, K, n) in sets:
            r = [x for x in d["rows"] if x["opt"] == opt and x["K"] == K and x["n"] == n]
            if not r:
                continue
            r = r[0]
            pred = fmt(PTS * r["pred_gauss"], 2) if opt == "exh" else "--"
            cost = r["budget"] if opt == "sh" else r["K"] * r["n"]
            L.append(f"{m} & {opt.upper()} & {K} & {n} & {cost} & {fmt(PTS*r['truth_mean'],1)} & "
                     f"{fmt(PTS*r['naive']['bias'],2,True)} $\\pm$ {fmt(PTS*1.96*r['naive']['bias_se'],2)} & {pred} & {fmt(PTS*r['naive']['cov'],0)} \\\\")
    open("paper/tables/tab_curse_main.tex", "w").write("\n".join(L) + "\n")


tab_curse_main()
# NOTE: some TeX Live builds mis-handle a row-final \\ at the end of an \input file inside tabular
# when \bottomrule follows in the parent file, so every table body file ends with its own \bottomrule.
import glob
for f in glob.glob("paper/tables/*.tex"):
    t = open(f).read()
    if not t.rstrip().endswith("\\bottomrule"):
        open(f, "w").write(t.rstrip("\n") + "\n\\bottomrule\n")
print("report built")
