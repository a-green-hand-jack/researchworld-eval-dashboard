import sys; sys.path.insert(0, "/work/analysis")
import numpy as np, pandas as pd
from scipy import stats
from style import *

NAMES = ["euclid", "tv", "hellinger", "chi2", "kl", "aitchison"]
FAMS = [("dirichlet", "Dirichlet"), ("logistic_normal", "Logistic-normal"), ("additive", "Additive")]
df = pd.read_csv("/work/results/e2_geometry.csv")
df["G"] = np.maximum(df.worst_conf, df.worst_min)


def tci(x):
    x = np.asarray(x, float)
    return x.mean(), stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


def cell(fam, D, k, method="split", col="G", delta=False):
    d = df[(df.family == fam) & (df.D == D) & (df.kappa == k) & (df.method == method)]
    pm = d.groupby(["score", "prob"])[col].mean().unstack("score")   # problems x scores
    if delta:
        pm = pm.sub(pm.min(axis=1), axis=0)
    return {n: tci(pm[n]) for n in NAMES}


def fmt(m, h, nd=3, bold=False):
    s = f"{m:.{nd}f}\\,{{\\scriptstyle\\pm{h:.{nd}f}}}"
    return f"\\mathbf{{{m:.{nd}f}}}\\,{{\\scriptstyle\\pm{h:.{nd}f}}}" if bold else s


def main_table():
    settings = [(5, 100), (10, 300)]
    lines = []
    for fam, flab in FAMS:
        lines.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{{flab} noise}}}}\\\\")
        res = {s: (cell(fam, *s, col="G"), cell(fam, *s, col="lm1", delta=True)) for s in settings}
        for n in NAMES:
            row = [LAB[n].replace("\\chi", "\\chi")]
            for s in settings:
                g, d = res[s]
                bg = g[n][0] <= min(v[0] for v in g.values()) + 0.0025
                bd = d[n][0] <= 0.05
                row.append("$" + fmt(*g[n], 3, bg) + "$")
                row.append("$" + fmt(*d[n], 2, bd) + "$")
            lines.append(" & ".join(row) + "\\\\")
        lines.append("\\addlinespace[2pt]")
    hdr = ("\\begin{tabular}{lcccc}\\toprule\n & \\multicolumn{2}{c}{$D{=}5,\\kappa{=}100$} & \\multicolumn{2}{c}{$D{=}10,\\kappa{=}300$}\\\\\n"
           "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\nscore & $G$ & $\\Delta\\!\\log$mass & $G$ & $\\Delta\\!\\log$mass\\\\\\midrule\n")
    open("/work/paper/tables/e2_main.tex", "w").write(hdr + "\n".join(lines) + "\n\\bottomrule\\end{tabular}\n")


def full_table():
    """Appendix: every cell, G and dlogmass, best score marked."""
    rows = []
    for fam, flab in FAMS:
        for D in (3, 5, 10):
            for k in (30, 100, 300, 1000):
                if not ((df.family == fam) & (df.D == D) & (df.kappa == k)).any():
                    continue
                g, d = cell(fam, D, k, col="G"), cell(fam, D, k, col="lm1", delta=True)
                cv = cell(fam, D, k, col="cov")
                rows.append((flab, D, k, g, d, cv))
    out = ["\\begin{tabular}{llr" + "c" * 6 + "}\\toprule", "noise & $D$ & $\\kappa$ & " + " & ".join(LAB[n] for n in NAMES) + "\\\\\\midrule"]
    out_d = list(out)
    for flab, D, k, g, d, cv in rows:
        bg = min(v[0] for v in g.values())
        out.append(f"{flab} & {D} & {k} & " + " & ".join(
            ("$\\mathbf{%.3f}$" if g[n][0] <= bg + 0.0025 else "$%.3f$") % g[n][0] for n in NAMES) + "\\\\")
        out_d.append(f"{flab} & {D} & {k} & " + " & ".join(
            ("$\\mathbf{%.2f}$" if d[n][0] <= 0.05 else "$%.2f$") % d[n][0] for n in NAMES) + "\\\\")
    open("/work/paper/tables/e2_full_G.tex", "w").write("\n".join(out) + "\n\\bottomrule\\end{tabular}\n")
    open("/work/paper/tables/e2_full_dlm.tex", "w").write("\n".join(out_d) + "\n\\bottomrule\\end{tabular}\n")
    return rows


def coverage_check():
    d = df[df.method == "split"]
    pm = d.groupby(["family", "D", "kappa", "score", "prob"])["cov"].mean()
    allm = d["cov"].mean()
    print("overall mean split coverage:", allm, " per-cell min/max of problem-mean cov:", pm.min(), pm.max())
    # coverage given calibration is Beta(901,100)-distributed: SD 0.0095
    print("SD of coverage across reps:", d["cov"].std())


def rank_agreement():
    """Do the two reference measures (Dir(1), Dir(1/2)) rank scores identically per cell?"""
    d = df[df.method == "split"]
    ag, tot = 0, 0
    for (f, D, k), g in d.groupby(["family", "D", "kappa"]):
        a = g.groupby("score").lm1.mean().rank(); b = g.groupby("score").lm05.mean().rank()
        tot += 1; ag += int((a == b).all())
    print("cells with identical ranking under Dir(1)/Dir(1/2):", ag, "/", tot)
    # best score by cell
    for (f, D, k), g in d.groupby(["family", "D", "kappa"]):
        print(f, D, k, "best by lm1:", g.groupby("score").lm1.mean().idxmin(), "best by lm05:", g.groupby("score").lm05.mean().idxmin(),
              "best by G:", g.groupby("score").G.mean().idxmin())


def mondrian_table():
    d = df[(df.D == 5) & (df.kappa == 100)]
    print(d.groupby(["family", "method", "score"])[["cov", "worst_conf", "worst_min", "lm1"]].mean().round(3).loc[("dirichlet")])


if __name__ == "__main__":
    main_table(); full_table(); coverage_check(); rank_agreement(); mondrian_table()
