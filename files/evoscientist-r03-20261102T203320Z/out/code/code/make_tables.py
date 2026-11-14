"""Build the LaTeX tables of the paper from results/*.csv and results/raw. Usage: PYTHONPATH=code python code/make_tables.py"""
import os, json
import numpy as np, pandas as pd
from analysis import Res, load, DATA_LABEL

os.makedirs("paper/tables", exist_ok=True)
S = pd.read_csv("results/summary_curves.csv")
K = pd.read_csv("results/summary_k_needed.csv")
SP = pd.read_csv("results/summary_spectrum.csv").set_index("data")
SHORT = {"mteb_mid": "MTEB-mid", "mteb_dense": "MTEB-dense", "mteb_wide": "MTEB-wide", "olb": "OpenLLM-LB", "helm": "HELM-Lite", "livebench": "LiveBench"}


def cell(data, split, sel, pred, k, stat="median"):
    r = S[(S.data == data) & (S.split == split) & (S["stat"] == stat) & (S.sel == sel) & (S.pred == pred) & (S.k == k)]
    if r.empty:
        return "--"
    r = r.iloc[0]
    return f"{r.rmse:.3f} \\scriptsize[{r.lo:.3f},{r.hi:.3f}]"


def write(name, s):
    open(f"paper/tables/{name}.tex", "w").write(s)


# ---- Table 1: datasets
rows = []
for data in SHORT:
    D = pd.read_csv(f"data/processed/{data}.csv", index_col=0)
    sp = SP.loc[data]
    rows.append(f"{SHORT[data]} & {D.shape[0]} & {D.shape[1]} & {100*D.notna().values.mean():.0f}\\% & {sp.pc1:.2f} & {int(sp.r80)} & {int(sp.r90)} & {sp.part_ratio:.1f} \\\\")
write("tab_data", "\\begin{tabular}{lrrrrrrr}\\toprule\nmatrix & models & benchm. & observed & PC1 & $r_{80}$ & $r_{90}$ & part.\\ ratio \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")

# ---- Table 2/3: main results (family split), median RMSE_z with family-cluster-bootstrap 95% CI
cfgs = [("random", "mean", "train mean"), ("random", "gauss", "random + Gauss"), ("random", "fa", "random + FA"),
        ("greedy_iopt", "fa", "greedy I-opt + FA"), ("cov_greedy", "gauss", "greedy cov + Gauss")]


def main_table(datas, ks, name):
    out = []
    for data in datas:
        lab_t = DATA_LABEL[data].replace("%", "\\%")
        out.append(f"\\multicolumn{{{len(ks)+1}}}{{l}}{{\\textit{{{lab_t}}}}} \\\\")
        for sel, pred, lab in cfgs:
            out.append(lab + " & " + " & ".join(cell(data, "family", sel, pred, k) for k in ks) + " \\\\")
    write(name, "\\begin{tabular}{l" + "r" * len(ks) + "}\\toprule\n$k$ & " + " & ".join(str(k) for k in ks) + " \\\\\\midrule\n" + "\n".join(out) + "\n\\bottomrule\\end{tabular}\n")


main_table(["mteb_mid", "mteb_dense", "mteb_wide"], [1, 2, 4, 8, 16, 24], "tab_main_mteb")
main_table(["olb", "helm", "livebench"], [1, 2, 3], "tab_main_llm")

# ---- Table 4: k needed
rows = []
for data in SHORT:
    for sel, pred, lab in [("random", "gauss", "random+Gauss"), ("cov_greedy", "gauss", "greedy cov+Gauss"), ("greedy_iopt", "fa", "greedy I-opt+FA")]:
        r = K[(K.data == data) & (K.split == "family") & (K.sel == sel) & (K.pred == pred)].set_index("frac")
        if r.empty:
            continue
        f = lambda x: f"{int(round(x.k_pt))} \\scriptsize[{x.k_lo:.0f},{x.k_hi:.0f}]"
        rows.append(f"{SHORT[data]} & {lab} & {f(r.loc[0.5])} & {f(r.loc[0.8])} & {int(r.iloc[0].kmax)} \\\\")
write("tab_kneeded", "\\begin{tabular}{llrrr}\\toprule\nmatrix & method & $k_{50}$ & $k_{80}$ & $k_{\\max}$ tested \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")

# ---- Table 5: stability across fold-assignment seeds, and family vs random split (MTEB-mid)
rows = []
for tag, lab in [("", "seed 0"), ("_seed1", "seed 1"), ("_seed2", "seed 2")]:
    R = Res(f"mteb_mid_family{tag}")
    vals = []
    for sel, pred in [("random", "gauss"), ("cov_greedy", "gauss"), ("greedy_iopt", "fa")]:
        for k in [4, 12]:
            pt, lo, hi, _ = R.curve(sel, pred)
            vals.append(f"{pt[R.ks.index(k)]:.3f}")
    rows.append(f"family split, {lab} & " + " & ".join(vals) + " \\\\")
R = Res("mteb_mid_random")
vals = []
for sel, pred in [("random", "gauss"), ("cov_greedy", "gauss"), ("greedy_iopt", "fa")]:
    for k in [4, 12]:
        pt, lo, hi, _ = R.curve(sel, pred)
        vals.append(f"{pt[R.ks.index(k)]:.3f}")
rows.append("random split, seed 0 & " + " & ".join(vals) + " \\\\")
write("tab_seeds", "\\begin{tabular}{lrrrrrr}\\toprule\n & \\multicolumn{2}{c}{random+Gauss} & \\multicolumn{2}{c}{greedy cov+Gauss} & \\multicolumn{2}{c}{greedy I-opt+FA} \\\\\n & $k$=4 & $k$=12 & $k$=4 & $k$=12 & $k$=4 & $k$=12 \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")

# ---- Table 6: raw-score units (median over models of mean absolute error in benchmark points)
rows = []
for data in ["mteb_mid", "mteb_dense", "mteb_wide"]:
    d = load(f"{data}_family")
    for k in [4, 8, 24]:
        def med(sel, pred):
            return d[(d.sel == sel) & (d.pred == pred) & (d.k == k)].mae.median()
        rows.append(f"{SHORT[data]} & {k} & {med('random', 'mean'):.2f} & {med('random', 'gauss'):.2f} & {med('cov_greedy', 'gauss'):.2f} & {med('greedy_iopt', 'fa'):.2f} \\\\")
write("tab_raw_units", "\\begin{tabular}{lrrrrr}\\toprule\nmatrix & $k$ & train mean & random+Gauss & greedy cov+Gauss & greedy I-opt+FA \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")

# ---- Table 7: conditions sweep (MTEB-mid, random split), median RMSE_z at k=6 and k=12
C = pd.read_csv("results/summary_conditions_mid.csv")
C["tag"] = C.tag.fillna("")
rows = []
for tag, lab, M in [("_trainfrac0.12", "12\\% of rows ($M\\approx$15)", 15), ("_trainfrac0.25", "25\\% ($M\\approx$31)", 31), ("_trainfrac0.5", "50\\% ($M\\approx$62)", 62), ("", "100\\% ($M\\approx$125)", 125)]:
    vals = []
    for sel, pred in [("random", "gauss"), ("cov_greedy", "gauss"), ("greedy_iopt", "fa")]:
        for k in [6, 12]:
            r = C[(C.tag == tag) & (C.sel == sel) & (C.pred == pred) & (C.k == k)].rmse.iloc[0]
            vals.append(f"{r:.3f}")
    rows.append("train rows kept: " + lab + " & " + " & ".join(vals) + " \\\\")
rows.append("\\midrule")
for tag, lab in [("_trainmiss0.3", "30\\%"), ("_trainmiss0.6", "60\\%"), ("_trainmiss0.8", "80\\%")]:
    vals = []
    for sel, pred in [("random", "gauss"), ("cov_greedy", "gauss"), ("greedy_iopt", "fa")]:
        for k in [6, 12]:
            r = C[(C.tag == tag) & (C.sel == sel) & (C.pred == pred) & (C.k == k)].rmse.iloc[0]
            vals.append(f"{r:.3f}")
    rows.append(f"train cells masked: {lab} & " + " & ".join(vals) + " \\\\")
mean_ref = C[(C.tag == "") & (C.sel == "random") & (C.pred == "mean") & (C.k == 6)].rmse.iloc[0]
write("tab_conditions", "\\begin{tabular}{lrrrrrr}\\toprule\n & \\multicolumn{2}{c}{random+Gauss} & \\multicolumn{2}{c}{greedy cov+Gauss} & \\multicolumn{2}{c}{greedy I-opt+FA} \\\\\n & $k$=6 & $k$=12 & $k$=6 & $k$=12 & $k$=6 & $k$=12 \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
print("mean-predictor ref (full) k=6:", mean_ref)

# ---- Table 8: selection gains (percent change in median RMSE vs random, Gauss predictor) at selected k
G = pd.read_csv("results/summary_paired_gain.csv")
rows = []
for data in ["mteb_mid", "mteb_dense", "mteb_wide"]:
    for sel, lab in [("cov_greedy", "greedy cov"), ("greedy_iopt", "greedy I-opt"), ("kmeans", "k-means cover"), ("piv_qr", "pivoted QR"), ("top_load", "top communality")]:
        vals = []
        for k in [2, 4, 8, 16, 24]:
            r = G[(G.data == data) & (G.split == "family") & (G["stat"] == "median") & (G.sel == sel) & (G.pred == "gauss") & (G.k == k)].iloc[0]
            vals.append(f"{100*r.rel:+.0f}\\% \\scriptsize[{100*r.lo:+.0f},{100*r.hi:+.0f}]")
        rows.append(f"{SHORT[data]} & {lab} & " + " & ".join(vals) + " \\\\")
write("tab_selgain", "\\begin{tabular}{llrrrrr}\\toprule\nmatrix & selection & $k$=2 & 4 & 8 & 16 & 24 \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")

# ---- Table 9: theory vs measurement
T = pd.read_csv("results/summary_theory_vs_real.csv")
rows = []
for data in ["mteb_mid", "mteb_dense", "mteb_wide", "olb", "helm", "livebench"]:
    x = T[(T.data == data) & (T.split == "random") & (T.sel == "random") & (T.pred == "fa")].set_index("k")
    ks = [k for k in [1, 4, 16] if k in x.index]
    rows.append(f"{SHORT[data]} & " + " & ".join((f"{x.loc[k].measured_trim:.3f} / {x.loc[k].implied:.3f}" if k in ks else "--") for k in [1, 4, 16]) + f" & {x.noise_floor.iloc[0]:.3f} \\\\")
write("tab_theory", "\\begin{tabular}{lrrrr}\\toprule\nmatrix & $k$=1 & $k$=4 & $k$=16 & $\\bar\\psi$ \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")

# numbers quoted in text
fits = json.load(open("results/raw/mteb_mid_family_fits.json"))
print("selected r (mteb_mid family):", [f["r"] for f in fits], "alpha", [f["alpha"] for f in fits])
for n in ["mteb_dense_family", "mteb_wide_family", "olb_family", "helm_family", "livebench_family"]:
    f = json.load(open(f"results/raw/{n}_fits.json")); print(n, [x["r"] for x in f], [x["alpha"] for x in f])
d = load("mteb_mid_random")
print("n test models:", {n: load(n).model.nunique() for n in ["mteb_mid_family", "mteb_dense_family", "mteb_wide_family", "olb_family", "helm_family", "livebench_family"]})
