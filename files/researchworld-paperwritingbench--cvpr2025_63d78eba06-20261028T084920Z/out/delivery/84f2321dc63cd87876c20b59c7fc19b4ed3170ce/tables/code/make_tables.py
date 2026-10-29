"""Generate tables/*.tex from tables/data/log_results.csv (every cell is a logged number; gaps recomputed)."""
import pathlib
from common import ROOT, COLS, load, sel, reference, check

rows = load()
OUT = ROOT / "tables"; OUT.mkdir(exist_ok=True)

def num(x, d):
    s = f"{x:.{d}f}"
    return s

def sgn(x, d):
    s = f"{abs(x):.{d}f}"
    if round(x, d) == 0: return s
    return ("$+" if x > 0 else "$-") + s + "$"

HDR = r"Test & Rem. & Forget & MIA"

def cells(r, dec):  # dec: decimals per column
    return " & ".join(num(r[c], d) for c, d in zip(COLS, dec))

def cells_inline(r, ref, dec):
    return " & ".join(f"{num(r[c], d)} ({sgn(r[c] - ref[c], d)})" for c, d in zip(COLS, dec))

def cells_gap(r, ref, dec, wrap="{}"):
    return " & ".join(sgn(r[c] - ref[c], d) for c, d in zip(COLS, dec))


def emit(name, spec, header, body, caption, label, notes=""):
    """tables/tabular_<name>.tex: self-contained tabular group (no float); tables/tab_<name>.tex: float using it."""
    tab = ["{\\footnotesize\\setlength{\\tabcolsep}{3pt}", rf"\begin{{tabular}}{{{spec}}}", r"\toprule", header, r"\midrule"] + body + [r"\bottomrule", r"\end{tabular}}"]
    (OUT / f"tabular_{name}.tex").write_text("\n".join(tab) + "\n")
    fl = [r"\begin{table}[t]", r"  \centering", rf"  \input{{tables/tabular_{name}}}", rf"  \caption{{{caption}}}", rf"  \label{{{label}}}", r"\end{table}"]
    (OUT / f"tab_{name}.tex").write_text("\n".join(fl) + "\n")

NOVAR = "One value per cell is logged; there are no variability estimates (single run)."
D = (0, 0, 0, 1)
HDR5 = rf"Setting & {HDR} \\"
def abl_rows(table, label_fmt, retr_per_setting):
    out = []
    rs = sel(rows, table, method="Retrained")
    if not retr_per_setting:
        out.append(r"Retrained & " + cells(rs[0], D) + r" \\")
    for u in sel(rows, table, method="Unlearned(-)"):
        ref = reference(rows, u)
        if retr_per_setting:
            out.append(r"Retrained, {} & ".format(label_fmt(u["setting"])) + cells(ref, D) + r" \\")
        out.append(r"Unl.($-$), {} & ".format(label_fmt(u["setting"])) + cells_inline(u, ref, D) + r" \\")
    return out
PAR = "Parentheses: Unlearned($-$) minus Retrained, in percentage points (the ideal MIA score is 50\\%). "
CAP = "CIFAR-10, linear classifier on ResNet-18 features. Test, remaining and forget accuracy and MIA score, all in \\%. "
SHARED = "The 500-perturbation and $\\lambda{=}0$ rows are the same configuration as the 10\\% forget row. "

fs = abl_rows("forget_size", lambda s: rf"{s}\%", True)
pt = abl_rows("perturb", lambda s: s, False)
lm = abl_rows("lambda", lambda s: rf"$\lambda{{=}}{s}$", False)
emit("forget_size", r"@{}lcccc@{}", HDR5, fs, CAP + "Effect of the forget-set size (\\% of the training set) on Unlearned($-$). " + PAR + NOVAR, "tab:forget_size")
emit("perturb", r"@{}lcccc@{}", HDR5, pt, CAP + "Effect of the number of perturbations used to estimate the retain Hessian (10\\% forget). " + PAR + SHARED + NOVAR, "tab:perturb")
emit("lambda", r"@{}lcccc@{}", HDR5, lm, CAP + "Effect of the L2 regularization $\\lambda$ (10\\% forget). " + PAR + SHARED + NOVAR, "tab:lambda")

# combined three-panel version (single float, same cells); use this OR the three tables above
def panel(t): return rf"\multicolumn{{5}}{{@{{}}l}}{{\textit{{{t}}}}} \\"
comb = [panel(r"(a) Forget-set size (\% of training set)")] + fs + [r"\midrule", panel(r"(b) Number of perturbations (10\% forget)")] + pt \
     + [r"\midrule", panel(r"(c) L2 regularization $\lambda$ (10\% forget)")] + lm
emit("ablations", r"@{}lcccc@{}", HDR5, comb, CAP + "Ablations of Unlearned($-$). " + PAR + SHARED + NOVAR, "tab:ablations")

# ---- mixed linear networks, CIFAR-100 ------------------------------------------------------
DM = (1, 1, 1, 1)
mb = []
for i, s in enumerate(["20", "15", "10"]):
    R = sel(rows, "mixed", s, "Retrained")[0]; P = sel(rows, "mixed", s, "Unlearned(+)")[0]; M = sel(rows, "mixed", s, "Unlearned(-)")[0]
    mb += [rf"{s}\% & Retrained & " + cells(R, DM) + r" \\", r" & Unlearned($+$) & " + cells(P, DM) + r" \\",
           r" & Unlearned($-$) & " + cells(M, DM) + r" \\",
           r" & \quad $\Delta$ to Unl.($+$) & " + cells_gap(M, P, DM) + r" \\",
           r" & \quad $\Delta$ to Retrained & " + cells_gap(M, R, DM) + r" \\"]
    if i < 2: mb.append(r"\midrule")
emit("mixed", r"@{}llcccc@{}", rf"Forget & Method & {HDR} \\", mb,
     "Mixed linear network (last layers of ResNet-18 linearized), CIFAR-100. All values in \\%. "
     "$\\Delta$ is Unlearned($-$) minus the named reference, in percentage points. The first $\\Delta$ row has the magnitudes "
     "of the ``Performance Gap'' rows in the experimental log, which are measured to Unlearned($+$), not to Retrained. " + NOVAR, "tab:mixed")

# ---- source-free baselines, CIFAR-10, 10% forget ----------------------------------------------
names = ["Retrained", "NegGrad", "Random Labels", "JiT", "Adversarial", "Unlearned(-)"]
R = {n: sel(rows, "baselines", "10", n)[0] for n in names}
free = names[1:]
best = {"test": max(free, key=lambda n: R[n]["test"]), "remaining": max(free, key=lambda n: R[n]["remaining"]),
        "forget": max(free, key=lambda n: R[n]["forget"]), "mia": min(free, key=lambda n: abs(R[n]["mia"] - 50))}
def bcells(n):
    out = []
    for c in COLS:
        s = num(R[n][c], 1)
        out.append(rf"\textbf{{{s}}}" if n != "Retrained" and best[c] == n else s)
    return " & ".join(out)
bb = [r"Retrained (reference) & " + bcells("Retrained") + r" \\", r"\midrule"]
for n in free:
    bb.append((r"Unlearned($-$) (ours)" if n == "Unlearned(-)" else n) + " & " + bcells(n) + r" \\")
emit("baselines", r"@{}lcccc@{}", r"Method & Test $\uparrow$ & Rem. $\uparrow$ & Forget $\uparrow$ & MIA $\to$ 50 \\", bb,
     "Comparison with source-free unlearning baselines on CIFAR-10 (linear classifier, 10\\% forget set). All values in \\%. "
     "Bold: best among the five unlearning methods per column (highest accuracy; MIA closest to 50\\%); "
     "the Retrained row is the reference and is not ranked. MIA scores of all methods lie within 3 points of 50\\%. " + NOVAR, "tab:baselines")
print(best)
check()
