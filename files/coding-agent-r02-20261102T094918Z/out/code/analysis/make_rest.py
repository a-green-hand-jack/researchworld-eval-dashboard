import sys; sys.path.insert(0, "/work/analysis")
import numpy as np, pandas as pd
from scipy import stats
from style import *
from e5_analysis import load, boot_stats, table

R = "/work/results/"
T = "/work/paper/tables/"
ORDER = ["euclid", "tv", "hellinger", "chi2", "kl", "aitchison"]


def tci(x):
    x = np.asarray(x, float)
    return x.mean(), stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


# ---------------------------------------------------------------- E1: calibration law, ties, misranking
def e1():
    a = pd.read_csv(R + "e1a_beta_law.csv")
    rows = []
    for n, g in a.groupby("n"):
        rows.append(f"{n} & {g['mean'].mean():.4f} & {g.beta_mean.iloc[0]:.4f} & {g.sd.mean():.4f} & {g.beta_sd.iloc[0]:.4f} & {g.ks_stat.max():.3f} & {g.ks_p.min():.3f}\\\\")
    open(T + "e1a.tex", "w").write("\\begin{tabular}{rcccccc}\\toprule\n$n$ & mean $V$ & Beta mean & SD $V$ & Beta SD & max KS & min $p$\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    print("KS p<.05:", a.ks_p.lt(0.05).sum(), "of", len(a), "; min p", a.ks_p.min())
    b = pd.read_csv(R + "e1b_ties.csv").query("n==1000 and score in ['euclid','chi2']")
    rows = []
    for (N, s), g in b.groupby(["N_ann", "score"]):
        p, r = g[g.variant == "plain"].iloc[0], g[g.variant == "randomised"].iloc[0]
        rows.append(f"{N} & {LAB[s]} & {p.n_distinct_scores} & {p['mean']:.4f} & {p.ks_stat:.2f} & {r['mean']:.4f} & {r.ks_stat:.3f}\\\\")
    open(T + "e1b.tex", "w").write("\\begin{tabular}{rlrcccc}\\toprule\n$N_{\\rm ann}$ & score & \\#atoms & mean cov. & KS & mean cov. (rand.) & KS (rand.)\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    c = pd.read_csv(R + "e1c_misrank.csv")
    rows = []
    for (n, m), g in c.groupby(["n", "m"]):
        g = g.assign(nominal_gap=g.nominal_gap.round(2)).set_index("nominal_gap")
        rows.append(f"{n} & {m} & " + " & ".join(f"{g.loc[x, 'p_misrank_indep']:.2f} / {g.loc[x, 'p_misrank_paired']:.2f}" for x in (0.01, 0.02, 0.05)) + "\\\\")
    open(T + "e1c.tex", "w").write("\\begin{tabular}{rrccc}\\toprule\n$n$ & $m$ & gap 0.01 & gap 0.02 & gap 0.05\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


# ---------------------------------------------------------------- E2b: theory figure
def fig_theory():
    c = pd.read_csv(R + "e2b_curves.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.3), sharey=True)
    for ax, k in zip(axes, (100, 1000)):
        for n in ORDER:
            g = c[(c.kappa == k) & (c.score == n)].sort_values("conf_mid")
            ax.plot(g.conf_mid, g.cov_pred, "-", color=COL[n], lw=1.1)
            ax.plot(g.conf_mid, g.cov_exact, MK[n], color=COL[n], ms=3.2, mfc="none" if n not in ("chi2", "euclid", "aitchison") else COL[n], label=LAB[n])
        ax.axhline(0.9, color="k", lw=0.6, ls=":")
        ax.set_title(rf"$D=3,\ \kappa={k}$"); ax.set_xlabel(r"confidence $\max_i\hat y_i$ (decile mean)")
    axes[0].set_ylabel("conditional coverage"); axes[0].set_ylim(0.6, 1.02)
    axes[1].legend(ncol=2, frameon=False, loc="lower left", fontsize=6.5)
    fig.savefig(FIG + "fig_theory.pdf")
    t = pd.read_csv(R + "e2b_theory.csv")
    rows = []
    for D in (3, 5, 10):
        for k in (30, 100, 300, 1000, 3000):
            g = t[(t.D == D) & (t.kappa == k)].set_index("score")
            rows.append(f"{D} & {k} & " + " & ".join(f"{g.loc[n, 'max_abs_pred_vs_exact']:.3f}" for n in ORDER) + "\\\\")
    open(T + "e2b.tex", "w").write("\\begin{tabular}{rrcccccc}\\toprule\n$D$ & $\\kappa$ & " + " & ".join(LAB[n] for n in ORDER) + "\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


# ---------------------------------------------------------------- E3 (learned predictor, heteroscedastic, adaptive methods)
def e3():
    df = pd.read_csv(R + "e3_learned.csv")
    MET = [("split", "split"), ("studentised", "Studentised"), ("mondrian_scale", "Mondrian (pred. scale)"), ("mondrian_conf", "Mondrian (confidence)")]
    lines = []
    for fam, flab in (("dirichlet", "Dirichlet"), ("logistic_normal", "Logistic-normal")):
        for het in (0.0, 1.0):
            lines.append(f"\\multicolumn{{6}}{{l}}{{\\emph{{{flab}, {'heteroscedastic' if het else 'homoscedastic'}}}}}\\\\")
            d = df[(df.family == fam) & (df.het == het) & (df.n_train == 3000)]
            pm = d.groupby(["score", "method", "prob"])[["cov", "worst_het", "worst_conf", "lm1"]].mean()
            for sc in ("chi2", "euclid", "aitchison"):
                for m, ml in MET:
                    x = pm.loc[(sc, m)]
                    c, ch = tci(x["cov"])
                    lm, lh = tci(x["lm1"] - pm.loc[(sc, "split")]["lm1"])    # paired with plain split of the same score / problem
                    wh = tci(x["worst_het"])[0] if het else np.nan
                    wc = tci(x["worst_conf"])[0]
                    lines.append(f"{LAB[sc]} & {ml} & {c:.3f} & " + (f"{wh:.3f}" if het else "--") + f" & {wc:.3f} & ${lm:.2f}\\,{{\\scriptstyle\\pm{lh:.2f}}}$\\\\")
            lines.append("\\addlinespace[2pt]")
    main = [l for l in lines]
    i0 = lines.index("\\multicolumn{6}{l}{\\emph{Dirichlet, heteroscedastic}}\\\\")
    blk = [l for l in lines[i0 + 1:i0 + 13] if l.startswith("Pearson") or l.startswith("Aitchison")]
    open(T + "e3_main.tex", "w").write("\\begin{tabular}{llcccc}\\toprule\nscore & method & cov. & $G_{s(x)}$ & $G_{\\rm conf}$ & $\\Delta$ log mass\\\\\\midrule\n" + "\n".join(blk) + "\n\\bottomrule\\end{tabular}\n")
    open(T + "e3_full.tex", "w").write("\\begin{tabular}{llcccc}\\toprule\nscore & method & cov. & $G_{s(x)}$ & $G_{\\rm conf}$ & $\\Delta$ log mass vs split\\\\\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\\end{tabular}\n")
    for nt in (300, 3000):
        d = df[(df.n_train == nt)]
        print("n_train", nt, "KL(mu||f) mean", d.kl_pred.mean())


# ---------------------------------------------------------------- E4 (selection)
def e4():
    df = pd.read_csv(R + "e4_selection.csv")
    lines = []
    SCH = [("fixed_euclid", "fixed Euclid"), ("fixed_aitchison", "fixed Aitchison"), ("fixed_chi2", "fixed $\\chi^2$"), ("naive", "select \\& calibrate on same data"),
           ("honest", "select on half, calibrate on other half"), ("oracle", "oracle (population-best)")]
    for fam, flab in (("dirichlet", "Dirichlet"), ("logistic_normal", "Logistic-normal"), ("additive", "Additive")):
        for D in (5, 10):
            lines.append(f"\\multicolumn{{4}}{{l}}{{\\emph{{{flab}, $D={D}$}}}}\\\\")
            d = df[(df.family == fam) & (df.D == D)]
            best = d[d.scheme == "oracle"].groupby("prob")["lm"].mean()
            for s, sl in SCH:
                g = d[d.scheme == s]
                pl = g.groupby("prob")["lm"].mean()
                lm, lh = tci(pl - best)
                o = d[d.scheme == "oracle"].set_index(["prob", "rep"])["cov"]
                dd = g.set_index(["prob", "rep"])["cov"] - o       # paired with the oracle score on the same calibration draw / test pool
                se = dd.std() / np.sqrt(len(dd))
                lines.append(f"{sl} & ${dd.mean()*100:+.2f}\\,{{\\scriptstyle\\pm{1.96*se*100:.2f}}}$ & ${g['cov'].std()*100:.2f}$ & ${lm:.2f}\\,{{\\scriptstyle\\pm{lh:.2f}}}$\\\\")
            lines.append("\\addlinespace[2pt]")
    open(T + "e4.tex", "w").write("\\begin{tabular}{lccc}\\toprule\nscheme & cov. $-$ oracle cov. (pts) & SD cov. (pts) & $\\Delta$ log mass vs oracle\\\\\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\\end{tabular}\n")
    d = df[df.scheme == "naive"]
    print(d.groupby(["family", "D"])["pick"].value_counts(normalize=True).round(3))


# ---------------------------------------------------------------- E5b shift
def shift():
    df = pd.read_csv(R + "e5b_shift.csv")
    fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.2), sharex=True)
    meth = [("split", "split", "#888888", "o"), ("weighted_known", "weighted (known $w$)", "#2a78d6", "s"), ("weighted_est", "weighted (estimated $w$)", "#1baf7a", "^"),
            ("mondrian_conf", "Mondrian (conf.)", "#eb6834", "D")]
    for ax, (col, ttl) in zip(axes, [("cov", "marginal"), ("cov_low_conf_half", "low-confidence half"), ("cov_high_conf_half", "high-confidence half")]):
        for m, lab, c, mk in meth:
            g = df[(df.score == "chi2") & (df.method == m)].groupby("gamma")[col]
            mu, se = g.mean(), g.std() / np.sqrt(g.count())
            ax.errorbar(mu.index, mu.values, yerr=1.96 * se.values, color=c, marker=mk, ms=3.5, lw=1.1, capsize=1.5, label=lab)
        ax.axhline(0.9, color="k", lw=0.6, ls=":"); ax.set_title(ttl); ax.set_xlabel(r"tilt $\gamma$")
    axes[0].set_ylabel("coverage on uniform test"); axes[0].legend(frameon=False, fontsize=6, loc="lower left")
    fig.savefig(FIG + "fig_shift.pdf")
    rows = []
    for sc in ("chi2", "euclid", "kl"):
        for g_ in (0.0, 2.0, 4.0):
            r = []
            for m in ("split", "weighted_known", "weighted_est", "mondrian_conf"):
                x = df[(df.score == sc) & (df.gamma == g_) & (df.method == m)]
                r.append(f"{x['cov'].mean():.3f} / {x.cov_low_conf_half.mean():.3f}")
            rows.append(f"{LAB[sc]} & {g_:g} & " + " & ".join(r) + "\\\\")
    open(T + "e5b.tex", "w").write("\\begin{tabular}{lrcccc}\\toprule\nscore & $\\gamma$ & split & weighted (known) & weighted (est.) & Mondrian conf.\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    print(df.groupby("gamma").ess.mean())


# ---------------------------------------------------------------- E5/E7 real-data tables / figure
def sname(score):
    if score.startswith("aitchison_"):
        return "Aitchison $\\delta{=}10^{-" + score.split("1e-")[1] + "}$"
    if score.startswith("mahal_ilr_"):
        return "Mahalanobis-ilr $\\delta{=}10^{-" + score.split("1e-")[1] + "}$"
    return LAB[score]


def f3(t, nd=3):
    return f"{t[0]:.{nd}f}\\,[{t[1]:.{nd}f},{t[2]:.{nd}f}]"


def real(tag, cfg, name, scores_main, ci=True):
    sc = scores_main
    combos = [("split", s) for s in sc] + [("mondrian_conf", s) for s in ("euclid", "chi2", "kl")] + [("mondrian_class", s) for s in ("euclid", "chi2", "kl")]
    df = table(tag, cfg, combos, B=200)
    lines = []
    prev = None
    names = {"split": "split conformal", "mondrian_conf": "Mondrian by confidence decile", "mondrian_class": "Mondrian by predicted class"}
    for _, r in df.iterrows():
        if r.method != prev:
            lines.append("\\multicolumn{6}{l}{\\emph{" + names[r.method] + "}}\\\\")
            prev = r.method
        if ci:
            lines.append(f"{sname(r.score)} & {r.cov_split_mean:.3f} & {f3(r.G_conf)} & {f3(r.G_class)} & {f3(r.min_conf)} & {r.lm1[0]:.2f}\\,[{r.lm1[1]:.2f},{r.lm1[2]:.2f}]\\\\")
        else:
            lines.append(f"{sname(r.score)} & {r.cov_split_mean:.3f} & {r.G_conf[0]:.3f} & {r.G_class[0]:.3f} & {r.min_conf[0]:.3f} & {r.lm1[0]:.2f}\\,{{\\scriptstyle\\pm{(r.lm1[2]-r.lm1[1])/2:.2f}}}\\\\")
    open(T + f"{name}.tex", "w").write("\\begin{tabular}{lccccc}\\toprule\nscore & cov. & $G_{\\rm conf}$ & $G_{\\rm class}$ & min.\\ decile cov. & log mass\\\\\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\\end{tabular}\n")
    return df


def fig_real(tag, cfg, fname):
    rep, img = load(tag)
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4), sharey=True)
    panels = [("split", ["euclid", "hellinger", "chi2", "kl", "aitchison_1e-3"]), ("mondrian_conf", ["euclid", "chi2", "kl"])]
    for ax, (meth, scs) in zip(axes, panels):
        for s in scs:
            b = boot_stats(img, cfg, meth, s, B=200)
            cur, lo, hi = b["curve"]
            base = s.split("_")[0]
            ax.plot(np.arange(1, 11), cur, "-" + MK[base], color=COL[base], ms=3.2, label=LAB[base] + (r" $\delta{=}10^{-3}$" if base == "aitchison" else ""))
            ax.fill_between(np.arange(1, 11), lo, hi, color=COL[base], alpha=0.15, lw=0)
        ax.axhline(0.9, color="k", lw=0.6, ls=":")
        ax.set_xlabel("confidence decile of $\\hat y$ (1 = least confident)"); ax.set_title({"split": "split conformal", "mondrian_conf": "Mondrian by confidence"}[meth])
        ax.set_xticks(range(1, 11))
    axes[0].set_ylabel("coverage"); axes[0].legend(frameon=False, fontsize=6, loc="lower right")
    fig.savefig(FIG + fname)


def alpha_tab():
    d = pd.concat([pd.read_csv(R + f"e5_alpha_summary_{a}.csv") for a in (0.05, 0.1, 0.2)])
    lines = []
    for (m, sc), g in d.groupby(["method", "score"], sort=False):
        g = g.set_index("alpha")
        nm = LAB.get(sc, "Aitchison $\\delta{=}10^{-3}$") + (" (Mondrian conf.)" if m == "mondrian_conf" else "")
        lines.append(nm + " & " + " & ".join(f"{g.loc[a, 'cov']:.3f} & {g.loc[a, 'G_conf']:.3f} & {g.loc[a, 'lm1']:.2f}" for a in (0.05, 0.1, 0.2)) + "\\\\")
    nl = d[d.method == "split"].groupby("alpha").null_conf.mean()
    open(T + "e5_alpha.tex", "w").write("\\begin{tabular}{lccccccccc}\\toprule\n & \\multicolumn{3}{c}{$\\alpha=0.05$} & \\multicolumn{3}{c}{$\\alpha=0.10$} & \\multicolumn{3}{c}{$\\alpha=0.20$}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\\cmidrule(lr){8-10}\nscore & cov. & $G_{\\rm conf}$ & log mass & cov. & $G_{\\rm conf}$ & log mass & cov. & $G_{\\rm conf}$ & log mass\\\\\\midrule\n"
        + "\n".join(lines) + "\n\\bottomrule\\end{tabular}\n")
    print(nl)


def cifar_other():
    sc = ["euclid", "tv", "hellinger", "chi2", "kl", "aitchison_1e-4", "aitchison_1e-3", "aitchison_1e-2", "mahal_ilr_1e-2"]
    names = {"resnet56_raw": "ResNet-56, $T{=}1$", "resnet20_T": "ResNet-20, $T$ fitted", "vgg11_bn_T": "VGG-11-bn, $T$ fitted"}
    lines = []
    for cfg, nm in names.items():
        df = table("cifar10h", cfg, [("split", x) for x in sc], B=100)
        lines.append("\\multicolumn{6}{l}{\\emph{" + nm + "}}\\\\")
        for _, r in df.iterrows():
            lines.append(f"{sname(r.score)} & {r.cov_split_mean:.3f} & {r.G_conf[0]:.3f} & {r.G_class[0]:.3f} & {r.min_conf[0]:.3f} & {r.lm1[0]:.2f}\\\\")
    open(T + "cifar_other.tex", "w").write("\\begin{tabular}{lccccc}\\toprule\nscore & cov. & $G_{\\rm conf}$ & $G_{\\rm class}$ & min.\\ decile cov. & log mass\\\\\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\\end{tabular}\n")


def real_merged(nli_cfg):
    rows = [("split", "euclid"), ("split", "tv"), ("split", "hellinger"), ("split", "chi2"), ("split", "kl"), ("split", "aitchison_1e-4"),
            ("split", "aitchison_1e-2"), ("split", "mahal_ilr_1e-2"), ("mondrian_conf", "chi2"), ("mondrian_class", "chi2")]
    a = table("cifar10h", "resnet56_T", rows, B=200)
    b = table("chaosnli", nli_cfg, rows, B=200)
    lines = []
    for i, (m, s) in enumerate(rows):
        ra, rb = a.iloc[i], b.iloc[i]
        nm = sname(s)
        if m != "split":
            nm += " (Mondrian conf.)" if m == "mondrian_conf" else " (Mondrian class)"
        lines.append(f"{nm} & {ra.G_conf[0]:.3f} & {ra.G_class[0]:.3f} & {ra.lm1[0]:.2f} & {rb.G_conf[0]:.3f} & {rb.G_class[0]:.3f} & {rb.lm1[0]:.2f}\\\\")
    nul = (a.null_conf.mean(), a.null_class.mean(), b.null_conf.mean(), b.null_class.mean())
    open(T + "real_merged.tex", "w").write("\\begin{tabular}{lcccccc}\\toprule\n & \\multicolumn{3}{c}{CIFAR-10H (ResNet-56, $D{=}10$)} & \\multicolumn{3}{c}{ChaosNLI (" + nli_cfg.split("_")[0] + ", $D{=}3$)}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\nscore & $G_{\\rm conf}$ & $G_{\\rm class}$ & log mass & $G_{\\rm conf}$ & $G_{\\rm class}$ & log mass\\\\\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\\end{tabular}\n")
    print("null gaps (cifar conf,class; nli conf,class):", nul)


if __name__ == "__main__":
    what = sys.argv[1:]
    if "alpha" in what: alpha_tab()
    if "cifar_other" in what: cifar_other()
    if "merged" in what: real_merged(what[what.index("merged") + 1])
    SC = ["euclid", "tv", "hellinger", "chi2", "kl"] + [f"aitchison_{d}" for d in ("1e-4", "1e-3", "1e-2", "1e-1")] + ["mahal_ilr_1e-3", "mahal_ilr_1e-2"]
    if "e1" in what: e1()
    if "theory" in what: fig_theory()
    if "e3" in what: e3()
    if "e4" in what: e4()
    if "shift" in what: shift()
    if "cifar" in what:
        real("cifar10h", "resnet56_T", "e5_resnet56T", SC)
        real("cifar10h", "resnet56_T", "e5_resnet56T_compact", SC, ci=False)
        fig_real("cifar10h", "resnet56_T", "fig_cifar.pdf")
        for cfg in ("resnet56_raw", "resnet20_T", "vgg11_bn_T"):
            real("cifar10h", cfg, "e5_" + cfg.replace("_", ""), SC)
    if "nli" in what:
        avail = set(k.split("|")[0] for k in load("chaosnli")[1].files)
        for cfg in ("roberta-large_T", "roberta-large_raw", "distilroberta_T"):
            if cfg in avail:
                real("chaosnli", cfg, "e7_" + cfg.replace("-", "").replace("_", ""), SC)


