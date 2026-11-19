"""E3: optimism gap in the real setting (Qwen2.5-0.5B-Instruct letter-logit scores on MMLU-Pro, replayed from the cached response matrix).
Gap = naive report - truth of the selected configuration; best-of-K (argmax) unless stated.
(a) disjoint truth arm: truth = accuracy of the selected configuration on the pool questions outside the tuning set;
(b) iid truth arm: tuning set drawn i.i.d. with replacement, truth = accuracy over the whole pool.
Markers = replayed gap over `reps` replications with 1.96 * MC s.e., colour = tuning-set size n; lines = Gaussian-max prediction computed from the real
matrix's empirical covariance (results/real_gaussian_max_check.csv).  (c) search procedures at the largest K, disjoint arm, from results/real_summary.csv.
K is read from the files (largest K present)."""
from style import *
PROC = {"argmax": "best-of-K", "sh": "succ. halving", "sr": "succ. rejects", "greedy": "greedy"}

def main():
    setup(); c = pd.read_csv(os.path.join(RESULTS, "real_gaussian_max_check.csv"))
    s = pd.read_csv(os.path.join(RESULTS, "real_summary.csv")); s = s[(s.est_name == "naive") & (s.truth_arm == "disjoint")]
    Ks = sorted(int(k) for k in c.K.unique()); Kmax = int(s.K.max())
    fig, axs = plt.subplots(1, 3, figsize=(W, 2.3), sharey=True, gridspec_kw=dict(width_ratios=[1, 1, 0.9]))
    ns = sorted(int(n) for n in c.n.unique())
    for ax, arm, t in zip(axs[:2], ["disjoint", "iid"], ["(a) disjoint truth", "(b) i.i.d. truth"]):
        for i, n in enumerate(ns):
            g = c[(c.truth_arm == arm) & (c.n == n)].sort_values("K")
            if g.empty: continue
            ax.plot(g.K, 100 * g.pred_gap, color=OI[i], ls="-", lw=1.0, alpha=0.8)
            ax.errorbar(g.K, 100 * g.replay_gap, yerr=100 * 1.96 * g.replay_se, color=OI[i], marker=MARK[i], ls="none", capsize=1.5, elinewidth=0.7, ms=3.5, label=f"n = {n}")
        ax.axhline(0, color="0.4", lw=0.6); ax.set_xscale("log", base=2)
        tk = list(Ks); ax.set_xticks(tk); ax.set_xticklabels([str(k) for k in tk]); ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_title(t); ax.set_xlabel("candidates searched, K")
    procs = [p for p in PROC if not s[(s.proc == p) & (s.K == Kmax)].empty]; sty = {"argmax": 4, "sh": 5, "sr": 6, "greedy": 3}
    for i, p in enumerate(procs):
        g = s[(s.proc == p) & (s.K == Kmax)].sort_values("n"); j = sty[p]
        axs[2].errorbar(g.n * (1 + 0.04 * (i - (len(procs) - 1) / 2)), 100 * g.bias, yerr=100 * 1.96 * g.bias_se, color="0.5" if p == "greedy" else OI[j], marker="h" if p == "greedy" else MARK[j], ls=LS[j], capsize=1.5, elinewidth=0.7, ms=3.5, label=PROC[p])
    nn = sorted(s.n.unique())
    axs[2].axhline(0, color="0.4", lw=0.6); axs[2].set_xscale("log"); axs[2].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axs[2].set_xticks(nn); axs[2].set_xticklabels([str(int(v)) for v in nn]); axs[2].set_xlabel("tuning questions, n"); axs[2].set_title(f"(c) procedure, K = {Kmax}")
    axs[2].legend(loc="upper right", handlelength=1.6, borderaxespad=0.2)
    axs[0].set_ylabel("optimism gap (pp)")
    h, l = axs[0].get_legend_handles_labels()
    h2, l2 = axs[1].get_legend_handles_labels()
    for hh, ll in zip(h2, l2):
        if ll not in l: h.append(hh); l.append(ll)
    h.append(plt.Line2D([], [], color="0.3", ls="-")); l.append("Gaussian-max prediction")
    fig.legend(h, l, loc="upper center", ncol=4, bbox_to_anchor=(0.5, -0.07), columnspacing=1.0, handletextpad=0.4)
    save(fig, "e3_real_gap.pdf")

if __name__ == "__main__":
    import matplotlib.ticker
    main()
