"""F6: is "late" really "never"? (a) the same seeds at the 30k-step ceiling (main) and at the 100k-step ceiling (long), per width;
(b) forest plot of the A1 slope (log t_gen per width doubling) under budget / threshold / architecture variants (sens_stats.json, *_stats.json).
python fig_budget.py"""
import json, os
import numpy as np
import matplotlib.pyplot as plt
import common as C


def main():
    C.style()
    L, M = C.load_runs("long"), C.load_runs("main")
    sens = json.load(open(os.path.join(C.RESULTS, "sens_stats.json"))) if os.path.exists(os.path.join(C.RESULTS, "sens_stats.json")) else {}
    if L.empty or not sens: print("budget figure: long sweep / sens_stats.json not available"); return
    fig, axs = plt.subplots(1, 2, figsize=(C.TXT_W, 3.0), gridspec_kw=dict(width_ratios=[1, 1.25]))
    ax = axs[0]
    col = C.width_colors(M.width.unique())
    ws = sorted(L.width.unique())
    for k, w in enumerate(ws):
        for s in sorted(L[L.width == w].seed):
            a = M[(M.width == w) & (M.seed == s)].iloc[0]; b = L[(L.width == w) & (L.seed == s)].iloc[0]
            x0, x1 = 2 * k, 2 * k + 1
            ya, yb = (float(r.t_gen) if r.grokked else float(r.steps_run) for r in (a, b))
            ax.plot([x0, x1], [ya, yb], color=col[w], lw=0.7, alpha=0.8)
            for x, y, g in ((x0, ya, a.grokked), (x1, yb, b.grokked)):
                ax.scatter([x], [y], s=14, color=col[w], lw=0.8, **({} if g else dict(marker="^", facecolor="none", edgecolor=col[w])))
    ax.axhline(30000, color=C.OI["grey"], lw=0.5, ls=":"); ax.axhline(100000, color=C.OI["grey"], lw=0.5, ls=":")
    ax.set_yscale("log"); C.logfmt(ax)
    ax.set_xticks(range(2 * len(ws))); ax.set_xticklabels(["30k", "100k"] * len(ws), fontsize=6)
    for k, w in enumerate(ws): ax.text(2 * k + 0.5, -0.17, f"w = {w}", transform=ax.get_xaxis_transform(), ha="center", fontsize=7)
    ax.set_xlim(-0.5, 2 * len(ws) - 0.5); ax.set_ylabel("t_gen (steps)"); ax.set_xlabel("step ceiling", labelpad=14)
    ax.set_title("(a) same seeds, longer budget", loc="left", fontsize=7)
    ax = axs[1]
    items = []
    def add(lbl, v, key_slope="slope"):
        if v: items.append((lbl, v[key_slope], v["ci95"], f"{v['n_censored']}/{v['n_runs']} cens."))
    add("main (30k, thr 0.99)", sens.get("S0_main_default"))
    add("budget 100k for w ≤ 32 seeds 0–2", sens.get("S1_extended_budget"))
    add("  … widths ≥ 32 only", sens.get("S1b_extended_budget_w>=32"))
    add("threshold 0.95", sens.get("S2b_threshold_0.95")); add("threshold 0.90", sens.get("S2b_threshold_0.9"))
    add("threshold 1.0, censored bound (old)", sens.get("S2_threshold_1.0"))
    add("threshold 1.0 exact re-runs, w ≥ 64", sens.get("S2c_threshold_1.0_exact_w>=64"))
    for sw, lbl in (("mlp", "MLP architecture (30k)"),):
        v = next((x for k, x in C.load_stats(sw).items() if k.endswith("A1_aft_slope")), None)
        if v: items.append((lbl, v["slope_log_tgen_per_log2_width"], v["ci95"], f"{v['n_censored']}/{v['n_runs']} cens."))
    s3 = sens.get("S3b_lrscale_grid_A1")
    if s3:
        items.append(("lr·√(64/w) grid, seeds 0–2 (CI unreliable)", s3["slope"], s3["ci95"], f"{s3['n_censored']}/{s3['n_runs']} cens."))
        m = s3.get("main_same_seeds")
        if m: items.append(("  fixed-lr, same grid (reference)", m["slope"], m["ci95"], f"{m['n_censored']}/{m['n_runs']} cens."))
    for i, (lbl, est, ci, note) in enumerate(items[::-1]):
        unreliable = "unreliable" in lbl
        ax.plot(ci, [i, i], color=C.OI["verm"] if unreliable else "k", lw=1.2)
        ax.plot([est], [i], "o", color="k", ms=3.5, mfc="white" if unreliable else "k")
        ax.text(max(ci[1], 0) + 0.04, i, note, fontsize=6, va="center")
    ax.axvline(0, color=C.OI["grey"], lw=0.6)
    ax.set_yticks(range(len(items))); ax.set_yticklabels([x[0] for x in items[::-1]], fontsize=6.5)
    ax.set_xlim(-0.8, 0.45); ax.set_xlabel("AFT slope: d log t_gen / d log₂ width"); ax.set_title("(b) A1 slope under variants", loc="left", fontsize=7)
    C.caption("budget", "Sensitivity of the width effect to the step budget, threshold and architecture. (a) Seeds 0–2 at widths 16 and 32 run with the 30,000-step ceiling (main) and "
              "with a 100,000-step ceiling (long; identical through step 30,000). Open triangles: not generalised at that ceiling (dotted lines). "
              "(b) Censoring-aware lognormal AFT slope of log t_gen on log2 width (negative: wider generalises sooner) over widths ≥ w_min, with 95% bootstrap CI over runs; "
              "right: censored/total runs. The old threshold-1.0 row is only a censored bound because those runs stop 500 steps after crossing 0.99; the exact row re-ran widths ≥ 64 to validation accuracy 1.0 (thr1). "
              "The lr·√(64/w) row (red, open marker) is the AFT slope over widths 16–256 with the learning rate scaled, seeds 0–2; 10 of 15 runs are censored, so its bootstrap CI collapses toward 0 and is not evidence of no effect; "
              "the row beneath is the fixed-lr slope on the same seeds and widths for reference.")
    fig.tight_layout()
    C.save(fig, "budget")


if __name__ == "__main__":
    main()
