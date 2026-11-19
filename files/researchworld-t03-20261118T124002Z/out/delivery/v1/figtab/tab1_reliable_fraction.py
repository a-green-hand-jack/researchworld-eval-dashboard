"""Table 1 (table*, C1 + C5): per dataset x model x explainer at k=3, delta=0.1 and the explainer's budget:
fraction of instances reliable (r_3 >= 0.9) with 95% cluster-bootstrap CI, mean r_3, rerun repeatability (Nogueira),
and the bias share = share of unreliable instances whose *mean* attribution already has the wrong top-3 (a repeatable but wrong
explainer). Budget: x1 = shipped KernelSHAP default (2d+2048 coalitions) for the KernelSHAP arms and Covert-Lee; Permutation at its shipped 500."""
import os, json
import numpy as np, pandas as pd
import figstyle as fs, common as C

K, DELTA, B = 3, 0.10, 300
a = C.args(__doc__)
df, files = C.load_tidy(a.pilot)
df = df[df.k == K].copy()
ARMROW = [("kshap_default", "x1", "KernelSHAP (shipped)"), ("kshap_l1off", "x1", "KernelSHAP \\texttt{l1\\_reg=False}"),
          ("perm", "perm500", "Permutation (shipped)"), ("covert_lee", "x1", "Covert--Lee")]
df["rel"] = (df.r >= 1 - DELTA).astype(float)
df["rel_e"] = (df.r_eps10 >= 1 - DELTA).astype(float)
df["unrel"] = 1.0 - df.rel
df["unrel_bias"] = df.unrel * (~df.mean_ok.astype(bool)).astype(float)
df["group"] = df.dataset.map(lambda s: C.DATA_LABEL.get(s, s)) + " " + df.model.map(lambda s: C.MODEL_LABEL.get(s, s.upper()))


def ci(m, lo, hi, nd=2):
    return f"{m:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]"


rows, shape = [], set()
for g, gdf in df.groupby("group"):
    nseed = gdf.seed.nunique(); ninst = gdf.groupby("seed").inst.nunique().sum()
    for arm, b, label in ARMROW:
        s = gdf[(gdf.arm == arm) & (gdf.budget == b)]
        if s.empty:
            continue
        F = C.cluster_boot(s, lambda f: f.rel.mean(), B=B)
        def bshare(f):
            u = f.unrel.sum()
            return np.nan if u == 0 else f.unrel_bias.sum() / u
        Fe = C.cluster_boot(s, lambda f: f.rel_e.mean(), B=B)
        bs = C.cluster_boot(s, bshare, B=B)
        bs_txt = "--" if np.isnan(bs[0]) else (ci(*bs) if not (np.isnan(bs[1]) or np.isnan(bs[2])) else f"{bs[0]:.2f}")
        shape.add((nseed, ninst // nseed))
        rows.append((g, "", label, ci(*F), ci(*Fe), f"{s.r.mean():.2f}", f"{s.r_eps10.mean():.2f}", f"{s.nog.mean():.2f}", bs_txt))

assert len(shape) == 1, f"groups differ in (seeds, instances): {shape}; state it in the table"
lines = ["\\begingroup\\setlength{\\tabcolsep}{2.5pt}", "\\begin{tabular}{@{}llcccccc@{}}", "\\toprule",
         "Dataset, model & Explainer & $F_3$ & $F_3^{\\epsilon}$ & mean $r_3$ & mean $r_3^{\\epsilon}$ & Nogueira & Bias share \\\\", "\\midrule"]
last = None
for g, _, label, F, Fe, mr, mre, ng, bs in rows:
    if last is not None and g != last:
        lines.append("\\addlinespace[2pt]")
    lines.append(f"{g if g != last else ''} & {label} & {F} & {Fe} & {mr} & {mre} & {ng} & {bs} \\\\")
    last = g
lines += ["\\bottomrule", "\\end{tabular}", "\\endgroup"]
out = os.path.join(C.outdir(a), "tab1_reliable_fraction.tex")
open(out, "w").write("\n".join(lines) + "\n")
pv = C.provenance(files); pv["seeds_x_instances_per_group"] = [int(v) for v in sorted(shape)[0]]
json.dump(pv, open(out.replace(".tex", ".json"), "w"), indent=1)
print("wrote", out)
