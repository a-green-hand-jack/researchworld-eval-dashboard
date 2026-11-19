"""Secondary views from the PRED=1 runs (raw/*.pred.csv.gz: true/predicted z-score per test cell, selectors random, random_pm,
greedy_ridge, full; ridge and mean inference).  usage: analyze3.py RAW_DIR OUT_DIR
 rank_corr.csv : (a) per-model Spearman between predicted and true z over the model's target benchmarks (bootstrap CI over test models),
                 (b) per-benchmark Spearman across test models (mean over benchmarks and repeats); 'mean' inference is constant -> 0 by convention.
 lowsd_check.csv: z-RMSE (ridge) with all targets vs excluding the 10% of benchmarks with the smallest overall sd (matrix-wide sd, raw scale),
                  and the share of squared z-error carried by those benchmarks."""
import sys, glob, os, re, numpy as np, pandas as pd
raw, out = sys.argv[1:3]; rng = np.random.default_rng(0); B = 500; FULL = 9999
D = "/hutian/repo/data/"; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from bench import dense_core
mats = {"mteb": dense_core(pd.read_csv(D + "mteb_matrix.csv", index_col=0), 0.95), "helm": pd.read_csv(D + "helm_lite_matrix.csv", index_col=0), "olb": pd.read_csv(D + "olb_matrix.csv", index_col=0)}
groups = {}
for f in sorted(glob.glob(os.path.join(raw, "*.pred.csv.gz"))):
    groups.setdefault(re.sub(r"_[a-f]$", "", re.sub(r"^(ex|ct)_", "", os.path.basename(f)[: -len(".pred.csv.gz")])), []).append(f)
rc, ls = [], []
for name, fs in groups.items():
    d = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates(["rep", "sel", "inf", "k", "model", "col"]); data = name
    base = data.split("_")[0]; Xm = mats[base] if base in mats else None
    print(data, len(d), flush=True)
    for (sel, inf, k), g in d.groupby(["sel", "inf", "k"]):
        if inf == "mean": continue
        # (a) per-model rank correlation across target cells
        g = g.copy(); g["rt"] = g.groupby(["rep", "model"]).z_true.rank(); g["rp"] = g.groupby(["rep", "model"]).z_pred.rank()
        cm = g.groupby(["rep", "model"]).apply(lambda h: h.rt.corr(h.rp) if len(h) > 2 else np.nan).dropna()
        bym = cm.groupby(level="model").mean().values
        bt = [bym[rng.integers(0, len(bym), len(bym))].mean() for _ in range(B)]
        # (b) per-benchmark rank correlation across test models
        g["rt2"] = g.groupby(["rep", "col"]).z_true.rank(); g["rp2"] = g.groupby(["rep", "col"]).z_pred.rank()
        cb = g.groupby(["rep", "col"]).apply(lambda h: h.rt2.corr(h.rp2) if len(h) > 5 else np.nan).dropna()
        rc.append((data, sel, inf, k, cm.mean(), *np.percentile(bt, [2.5, 97.5]), len(bym), cb.mean(), len(cb)))
        # low-sd check
        if Xm is not None:
            sd = Xm.std(); lo_sd = set(sd.index[sd.values <= sd.quantile(0.10)]); cols = np.array(Xm.columns)
            g["low"] = [cols[j] in lo_sd for j in g["col"]]; e2 = (g.z_pred - g.z_true) ** 2
            ls.append((data, sel, inf, k, np.sqrt(e2.mean()), np.sqrt(e2[~g.low].mean()), e2[g.low].sum() / e2.sum(), g.low.mean()))
pd.DataFrame(rc, columns="data sel inf k mean_model_spearman lo hi n_models mean_bench_spearman n_bench_rep".split()).to_csv(os.path.join(out, "rank_corr.csv"), index=False)
pd.DataFrame(ls, columns="data sel inf k zrmse_all zrmse_excl_lowsd err_share_lowsd cell_share_lowsd".split()).to_csv(os.path.join(out, "lowsd_check.csv"), index=False)
