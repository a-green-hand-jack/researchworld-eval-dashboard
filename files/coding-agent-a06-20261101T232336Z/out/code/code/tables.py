"""LaTeX table generators (booktabs).  Usage: python tables.py synth|real"""
import sys; sys.path.insert(0, "/work/code")
import numpy as np, pandas as pd
from summ import summarize
from fig_methods import prep
OUT = "/work/paper/tables/"
NM = {"naive": "naive", "holdout": "hold-out", "crossfit": "cross-fit", "boot_opt": "replay-boot.", "boot_632": "replay .632", "eb": "EB shrink", "worstcase": "worst-case corr.", "cond": "conditional",
      "simult": "simultaneous", "ladder": "Ladder", "thresholdout_lo": "Thresholdout"}
AN = {"rs8": "RS $B{=}8$", "rs72": "RS $B{=}72$", "sh72": "SH $B{=}72$", "ca": "coord.\\ asc.", "mipro40": "MIPRO-like"}
def f(x, d=1): return "--" if not np.isfinite(x) else f"{x:.{d}f}"

def methods_table(d, fname, taus, ns, algs, methods, wcol="w_tau", caption_note=""):
    s = summarize(prep(d), ["alg", "n", "method"] + ([wcol] if wcol else []))
    lines = []
    cols = "ll" + "r" * 0
    hdr = "setting & " + " & ".join(NM[m] for m in methods) + " \\\\"
    body = []
    for tau in taus:
        for a in algs:
            for n in ns:
                h = s[(s.alg == a) & (s.n == n) & ((s[wcol] == tau) if wcol else True)].set_index("method")
                row = f"{AN[a]}, $n{{=}}{n}$"
                if wcol and len(taus) > 1: row = f"$\\tau{{=}}{tau}$, " + row
                cells = []
                for m in methods:
                    if m not in h.index: cells.append("--"); continue
                    r = h.loc[m]
                    cells.append(f"{100*r.bias:+.1f}/{100*r.rmse:.1f}/{100*r.cover:.0f}")
                body.append(row + " & " + " & ".join(cells) + " \\\\")
    tex = "\\begin{tabular}{l" + "c" * len(methods) + "}\n\\toprule\n" + hdr + "\n\\midrule\n" + "\n".join(body) + "\n\\bottomrule\n\\end{tabular}\n"
    open(OUT + fname, "w").write(tex)

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "synth":
        d = pd.read_parquet("/work/results/synth_main.parquet"); d = d[d.w_rho == 0.8]
        methods_table(d, "synth_methods.tex", (0.0, 0.1), (100, 400), ("rs72", "mipro40"), ["naive", "holdout", "crossfit", "boot_opt"])
        print(open(OUT + "synth_methods.tex").read())


def pct(x, d=1): return f"{100*x:.{d}f}"

def t_real_optimism():
    d = pd.read_parquet("/work/results/real_main.parquet"); d = prep(d[d.method_set == "main"])
    nv = d[d.method == "naive"].copy(); nv["opt"] = nv.est - nv.truth
    g = nv.groupby(["alg", "n"]).agg(rep=("est", "mean"), tru=("truth", "mean"), opt=("opt", "mean"), se=("opt", lambda x: x.std() / np.sqrt(len(x)))).reset_index()
    rows = []
    for a in ("rs8", "rs72", "sh72", "ca", "mipro40"):
        cells = []
        for n in (50, 100, 200, 400, 800):
            r = g[(g.alg == a) & (g.n == n)].iloc[0]
            cells.append(f"{pct(r.opt)}$\\pm${pct(1.96*r.se)}")
        rows.append(AN[a] + " & " + " & ".join(cells) + " \\\\")
    tex = "\\begin{tabular}{lccccc}\n\\toprule\n & $n{=}50$ & 100 & 200 & 400 & 800 \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
    open(OUT + "real_optimism.tex", "w").write(tex); print(tex)

def t_conclusions():
    out = []
    for nm, fn, filt in (("real", "conclusions_real", None), ("sim, $\\tau{=}0$", "conclusions_synth", 0.0), ("sim, $\\tau{=}0.1$", "conclusions_synth", 0.1)):
        d = pd.read_parquet(f"/work/results/{fn}.parquet")
        if filt is not None: d = d[d.w_tau == filt]
        d = d[d.algoA == "rs"].copy(); d["claim"] = (d.gap / d.se) > 1.645; d["fc1"] = d.claim & (d.true_gap < 0.01); d["B"] = d.algoB.fillna("None").replace("None", "default")
        for B, bn in (("default", "vs.\\ untuned default"), ("rs", "vs.\\ RS $B{=}4$")):
            for n in (100, 400):
                h = d[(d.B == B) & (d.n == n)]
                cell = []
                for m in ("naive", "boot_opt", "holdout"):
                    x = h[h.method == m]
                    cell.append(f"{100*x.claim.mean():.0f} / {100*x.fc1.mean():.0f}")
                out.append(f"{nm}, {bn}, $n{{=}}{n}$ & {100*h[h.method=='naive'].true_gap.mean():.1f} & {100*h[h.method=='naive'].gap.mean():.1f} & " + " & ".join(cell) + " \\\\")
    tex = "\\begin{tabular}{lcccrr}\n\\toprule\n & true gap & naive gap & \\multicolumn{3}{c}{claims / false claims [\\%]} \\\\\n & [pts] & [pts] & naive & replay-boot. & hold-out \\\\\n\\midrule\n" + "\n".join(out) + "\n\\bottomrule\n\\end{tabular}\n"
    open(OUT + "conclusions.tex", "w").write(tex); print(tex)

def t_extras():
    e = pd.read_parquet("/work/results/real_extras.parquet"); e = e[e.method.isin(["naive", "eb", "worstcase", "cond", "simult", "ladder", "thresholdout_lo"])]
    s = summarize(e, ["kw_B", "n", "method"]); meth = ["naive", "eb", "worstcase", "cond", "simult", "ladder", "thresholdout_lo"]
    rows = []
    for B in (72,):
        for n in (100, 400):
            h = s[(s.kw_B == B) & (s.n == n)].set_index("method"); cells = []
            for m in meth:
                r = h.loc[m]; cells.append(f"{100*r.bias:+.1f}/{100*r.rmse:.1f}/{100*r.cover:.0f}/{100*r.width:.0f}" if np.isfinite(r.rmse) else f"--/--/{100*r.cover:.0f}/{100*r.width:.0f}")
            rows.append(f"RS $B{{=}}{B}$, $n{{=}}{n}$ & " + " & ".join(cells) + " \\\\")
    tex = "\\begin{tabular}{l" + "c" * len(meth) + "}\n\\toprule\n & " + " & ".join(NM[m] for m in meth) + " \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
    open(OUT + "real_extras.tex", "w").write(tex); print(tex)

def t_robust():
    d = pd.read_parquet("/work/results/synth_robust.parquet"); d = d[d.method.isin(["naive", "boot_opt", "holdout", "eb", "worstcase", "cond", "simult"])]
    s = summarize(d[(d.w_K == 72) & (d.w_tau == 0.05) & (d.n == 100)], ["w_dist", "method"])
    rows = []
    for dist in ("normal", "sparse", "heavy", "bimodal"):
        h = s[s.w_dist == dist].set_index("method"); cells = []
        for m in ("naive", "boot_opt", "holdout", "eb", "worstcase", "cond", "simult"):
            r = h.loc[m]; cells.append(f"{100*r.bias:+.1f}/{100*r.cover:.0f}" if np.isfinite(r.bias) else f"--/{100*r.cover:.0f}")
        rows.append(f"{dist} & " + " & ".join(cells) + " \\\\")
    tex = "\\begin{tabular}{lccccccc}\n\\toprule\n config.\\ effects & naive & replay-boot. & hold-out & EB & worst-case & conditional & simult. \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
    open(OUT + "robust.tex", "w").write(tex); print(tex)

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "real":
    t_real_optimism(); t_conclusions(); t_extras(); t_robust()


def t_permnull():
    pn = pd.read_parquet("/work/results/permnull.parquet"); pn["opt"] = pn.report - pn.truth; pn["alg"] = pn.algo + pn.B.astype(str)
    g = pn.groupby(["alg", "n", "kind"]).opt.mean().unstack("kind") * 100
    rows = []
    for a in ("rs8", "rs72", "sh72", "ca0", "mipro40"):
        nm = AN.get(a, "coord.\\ asc.")
        rows.append(nm + " & " + " & ".join(f"{g.loc[(a, n), 'real']:.1f} / {g.loc[(a, n), 'perm']:.1f}" for n in (50, 100, 200, 400, 800)) + " \\\\")
    tex = "\\begin{tabular}{lccccc}\n\\toprule\n & $n{=}50$ & 100 & 200 & 400 & 800 \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
    open(OUT + "permnull.tex", "w").write(tex); print(tex)

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "real":
    t_permnull()


def t_ablate():
    d = pd.read_parquet("/work/results/ablate_boot.parquet"); d = d[(d.method == "boot_opt") & (d.n == 100)]
    s = summarize(d, ["algo", "nboot"]).set_index(["algo", "nboot"]); rows = []
    for a, nm in (("rs", "RS $B{=}72$"), ("mipro", "MIPRO-like")):
        rows.append(nm + " & " + " & ".join(f"{100*s.loc[(a, b), 'bias']:+.1f} / {100*s.loc[(a, b), 'rmse']:.1f} / {100*s.loc[(a, b), 'cover']:.0f}" for b in (10, 25, 100, 300)) + " \\\\")
    tex = "\\begin{tabular}{lcccc}\n\\toprule\n & $b{=}10$ & 25 & 100 & 300 \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
    open(OUT + "ablate_boot.tex", "w").write(tex); print(tex)

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "real":
    t_ablate()


def t_real2():
    d = pd.read_parquet("/work/results/real2_main.parquet"); d["alg"] = d.algo + d.kw_B.astype(str); d = d[(d.method_set == "main") & (d.alg == "rs32")]
    s = summarize(d, ["n", "method"]).set_index(["n", "method"]); rows = []
    for n in (50, 100, 200):
        rows.append(f"$n{{=}}{n}$ & " + " & ".join(f"{100*s.loc[(n,m),'bias']:+.1f}/{100*s.loc[(n,m),'rmse']:.1f}/{100*s.loc[(n,m),'cover']:.0f}" for m in ("naive", "holdout", "crossfit", "boot_opt")) + " \\\\")
    tex = "\\begin{tabular}{lcccc}\n\\toprule\n & naive & hold-out & cross-fit & replay-boot. \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
    open(OUT + "real2.tex", "w").write(tex); print(tex)

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "real":
    t_real2()
