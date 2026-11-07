"""Tables/figures for the CIFAR-10H experiment.  usage: python code/analyze_cifar.py"""
import json, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.special import softmax
from scipy.stats import beta as Beta

MODELS = ["resnet20", "rf", "lin"]
ci = lambda x: 1.96 * np.std(x, ddof=1) / np.sqrt(len(x))
D = pd.read_csv("results/cifar10h.csv")
Y = np.load("data/c10h.npy"); yt = np.load("data/cifar/test.npz")["y"]
S = {}
for m in MODELS:
    h = softmax(np.load(f"data/cifar_logits_{m}.npy"), 1)
    S[m] = dict(acc_vs_label=float((h.argmax(1) == yt).mean()), acc_vs_human_mode=float((h.argmax(1) == Y.argmax(1)).mean()),
                mean_maxprob=float(h.max(1).mean()), mean_L2_to_human=float(np.sqrt(((h - Y) ** 2).sum(1)).mean()),
                frac_zero_entries_human=float((Y == 0).mean()))
S["human_gini_mean"] = float((1 - (Y ** 2).sum(1)).mean())
ORDER = ["L2", "L1", "Linf", "Hellinger", "KL", "Aitchison", "Mahal-clr", "DirNLL", "L2/sqrtGini",
         "L2/learned-sigma", "L2-Mondrian(argmax)", "L2-Mondrian(gini)"]
TEX = {s: s.replace("sqrtGini", r"$\sqrt{\mathrm{Gini}}$") for s in ORDER}
cols = [("cov", "cov."), ("xc", "XC"), ("vf0.1", "V$_{.1}$"), ("vf1", "V$_{1}$"), ("gapG_max", "gap$_G$"), ("minG", "min$_G$"), ("gapC_max", "gap$_C$")]
for mod in MODELS:
    d = D[(D.model == mod) & (D.n_cal == 500) & (D.alpha == 0.1)]
    g = d.groupby("score")
    lines = [r"\begin{tabular}{l" + "r" * len(cols) + "}", r"\toprule", "score & " + " & ".join(c[1] for c in cols) + r" \\", r"\midrule"]
    mu = {c: g[c].mean() for c, _ in cols}
    best = {c: (mu[c].loc[ORDER].idxmax() if c in ("cov", "minG") else mu[c].loc[ORDER].idxmin()) for c, _ in cols if c != "cov"}
    for s in ORDER:
        cells = []
        for c, _ in cols:
            v = mu[c][s]
            t = f"{v:.3f}"
            if c != "cov" and best[c] == s: t = r"\mathbf{" + t + "}"
            cells.append("$" + t + r"{\scriptstyle\pm" + f"{ci(d[d.score == s][c]):.3f}" + "}$")
        lines.append(TEX[s] + " & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(f"tables/cifar_{mod}.tex", "w").write("\n".join(lines))
    S[f"{mod}_max_ci"] = {c: float(g[c].apply(ci).max()) for c, _ in cols}
    S[f"{mod}_table"] = {c: mu[c].round(4).to_dict() for c, _ in cols}
# coverage law check on real data (R draws of calibration, test fixed size 4000, population = 10000 shared pool -> not independent;
# report mean coverage and SD only)
for mod in MODELS:
    for n in [100, 500, 2000]:
        d = D[(D.model == mod) & (D.n_cal == n) & (D.alpha == 0.1) & (D.score == "L2")]
        S[f"cov_{mod}_n{n}"] = dict(mean=float(d["cov"].mean()), sd=float(d["cov"].std()), exp=float(np.ceil((n + 1) * 0.9) / (n + 1)))
# Aitchison delta sensitivity
dl = D[(D.n_cal == 500) & (D.alpha == 0.1) & D.score.str.startswith("Aitchison")]
S["aitchison_delta"] = {f"{m}|{s}": dict(xc=float(g.xc.mean()), vf1=float(g.vf1.mean()), gapG=float(g.gapG_max.mean()))
                        for (m, s), g in dl.groupby(["model", "score"])}
# conditional coverage figure
fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.2), sharey=True)
show = ["L2", "KL", "Aitchison", "L2/sqrtGini", "L2/learned-sigma", "L2-Mondrian(gini)"]
cc = dict(zip(show, ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown"]))
for ax, mod in zip(axs, MODELS):
    d = D[(D.model == mod) & (D.n_cal == 500) & (D.alpha == 0.1)]
    for s in show:
        g = d[d.score == s]
        ax.errorbar(range(5), [g[f"covG{i}"].mean() for i in range(5)], yerr=[ci(g[f"covG{i}"].dropna()) for i in range(5)],
                    marker="o", ms=2.5, lw=1, color=cc[s], label=s, capsize=1.5)
    ax.axhline(0.9, color="k", ls=":", lw=0.8); ax.set_title(f"CIFAR-10H, {mod}", fontsize=8); ax.set_xlabel("Gini($\\hat h$) quintile")
axs[0].set_ylabel("coverage"); axs[0].legend(fontsize=6, loc="lower left")
plt.tight_layout(); plt.savefig("figs/fig_cifar_cond.pdf", bbox_inches="tight")
json.dump(S, open("results/summary_cifar.json", "w"), indent=1)
print(json.dumps({k: v for k, v in S.items() if "table" not in k}, indent=1)[:3000])
