"""C5: at (approximately) matched compute, is it better to average c independent runs of budget m or to run once at ~c*m?

usage: python3 analysis/compute_matched.py [raw_dir] [out_dir]
For each cell x explainer x base budget b and factor c in {2, 4, 8}: the budget b' with the closest rows ratio to c (within
[0.8c, 1.3c]) is the 'enlarged' single run; the 'repeat' estimate is the mean attribution of c disjoint runs of budget b.
Writes tables/compute_matched.csv (per instance differences summarised with instance-level bootstrap CIs) and
tables/c5_hier.csv: per explainer x c, a hierarchical bootstrap over cells (resample cells, then instances within each
resampled cell; the cell statistic is the mean over its pairs of the instance mean); lo/hi_dataset_cluster resample datasets first
(then the cells of a chosen dataset, then instances), because cells of one dataset share instances and random-number streams.  'all' uses every pair; 'unsaturated' drops
Kernel pairs whose enlarged budget exceeds half of the 2^d-2 coalitions (where the enlarged run is nearly exact).
"""
import glob, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import binomtest
sys.path.insert(0, os.path.dirname(__file__))
import metrics as M

raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results", "raw")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "results", "tables")
rng = np.random.RandomState(7)
res = []
store = {}   # (explainer, c, subset) -> cell -> list of per-pair (N,) arrays per metric
HM = ("lerr", "m1", "m3", "m5")
for fref in sorted(glob.glob(f"{raw}/*__ref.npz")):
    cell = os.path.basename(fref).rsplit("__", 1)[0]; ds, model = cell.split("__")
    ref = np.load(fref)["ref"]; N, d = ref.shape
    for ex in ("kernel", "perm"):
        f = f"{raw}/{cell}__{ex}.npz"
        if not os.path.exists(f):
            continue
        z = np.load(f); phi, rows = z["phi"], z["rows"].mean((0, 2)); R = phi.shape[2]
        for b in range(phi.shape[1]):
            for c in (2, 4, 8):
                ratios = rows / (c * rows[b])
                cand = [bb for bb in range(phi.shape[1]) if 0.8 <= rows[bb] / rows[b] / c * c <= 1.3 * c and bb > b]
                if not cand:
                    continue
                bb = min(cand, key=lambda x: abs(rows[x] / rows[b] - c))
                G = R // c
                per = []
                for i in range(N):
                    avg = phi[i, b, :G * c].reshape(G, c, d).mean(1)        # G averaged estimates
                    big = phi[i, bb]                                         # R single enlarged runs
                    nr = np.linalg.norm(ref[i])
                    row = dict(inst=i,
                               err_rep=(np.linalg.norm(avg - ref[i], axis=1) / nr).mean(), err_big=(np.linalg.norm(big - ref[i], axis=1) / nr).mean())
                    for k in (1, 3, 5):
                        if k >= d:
                            continue
                        Sr = M.topk_ind(ref[i][None], k)[0]
                        row[f"match_rep_k{k}"] = (M.topk_ind(avg, k) == Sr).all(1).mean()
                        row[f"match_big_k{k}"] = (M.topk_ind(big, k) == Sr).all(1).mean()
                    per.append(row)
                P = pd.DataFrame(per)
                r = dict(dataset=ds, model=model, d=d, explainer=ex, base_rows=rows[b], enlarged_rows=rows[bb], c=c,
                         compute_ratio=rows[bb] / (c * rows[b]), n_groups=G, n_inst=N)
                lr = np.log(P.err_rep / P.err_big)
                r["log_err_ratio_rep_over_big"], r["log_err_ratio_lo"], r["log_err_ratio_hi"] = M.boot_ci(lr.values, rng, B=1000)
                for k in (1, 3, 5):
                    if f"match_rep_k{k}" in P:
                        dd = (P[f"match_rep_k{k}"] - P[f"match_big_k{k}"]).values
                        r[f"match_diff_k{k}"], r[f"match_diff_k{k}_lo"], r[f"match_diff_k{k}_hi"] = M.boot_ci(dd, rng, B=1000)
                        r[f"match_rep_k{k}"] = P[f"match_rep_k{k}"].mean(); r[f"match_big_k{k}"] = P[f"match_big_k{k}"].mean()
                r["enl_frac_space"] = (int(z["budgets"][bb]) / (2 ** d - 2)) if ex == "kernel" else np.nan
                res.append(r)
                vals = {"lerr": lr.values}
                for k in (1, 3, 5):
                    if f"match_rep_k{k}" in P:
                        vals[f"m{k}"] = (P[f"match_rep_k{k}"] - P[f"match_big_k{k}"]).values
                if ds.endswith("_logit"):
                    continue   # log-odds sensitivity cells are not pooled with the core cells
                cr = r["compute_ratio"]; unsat = not (ex == "kernel" and r["enl_frac_space"] > 0.5)
                for sub, ok in (("all", True), ("unsaturated", unsat), ("matched", 0.9 <= cr <= 1.1),
                                ("matched_unsaturated", unsat and 0.9 <= cr <= 1.1), ("matched_wide", 0.8 <= cr <= 1.25)):
                    if ok:
                        store.setdefault((ex, c, sub), {}).setdefault(cell, []).append((vals, cr))
pd.DataFrame(res).to_csv(f"{out}/compute_matched.csv", index=False)
print(len(res), "comparisons")


# hierarchical bootstrap over cells (core cells only).  Subsets of the budget pairs: all; unsaturated (Kernel enlarged budget <= half of
# the coalition space); matched (compute ratio enlarged_rows / (c * base_rows) in [0.9, 1.1]); matched_unsaturated; matched_wide ([0.8, 1.25]).
# A cell without a pair in a subset drops out (n_cells).  sign_test_p: two-sided exact sign test over the cells with a non-zero cell mean.
hr = np.random.RandomState(8); BH = 2000; hier = []
for (ex, c, sub), cells in sorted(store.items()):
    names = sorted(cells)
    for m in HM:
        # per cell: array (pairs, N) of the metric (pairs lacking the metric, e.g. k>=d, are dropped)
        A = {cn: np.array([v[m] for v, _ in cells[cn] if m in v]) for cn in names}
        A = {cn: a for cn, a in A.items() if a.size}
        if len(A) < 2:
            continue
        cn_ = sorted(A)
        pt = np.array([A[cn].mean() for cn in cn_])
        boots = []
        for _ in range(BH):
            pick = hr.randint(0, len(cn_), len(cn_)); v = []
            for j in pick:
                a = A[cn_[j]]; ix = hr.randint(0, a.shape[1], a.shape[1]); v.append(a[:, ix].mean())
            boots.append(np.mean(v))
        # cells of one dataset share instances and random-number streams (see seed_correlation.csv): also resample whole datasets
        dsets = sorted({cn.split("__")[0] for cn in cn_}); boots_ds = []
        for _ in range(BH):
            v = []
            for ds_ in hr.randint(0, len(dsets), len(dsets)):
                mem = [cn for cn in cn_ if cn.split("__")[0] == dsets[ds_]]; w = []
                for cn in mem:
                    a = A[cn]; ix = hr.randint(0, a.shape[1], a.shape[1]); w.append(a[:, ix].mean())
                v.append(np.mean(w))
            boots_ds.append(np.mean(v))
        lcr = np.mean([np.log(cr) for cn in cn_ for v, cr in cells[cn] if m in v])
        nz = pt[pt != 0]; fav = int((nz < 0).sum() if m == "lerr" else (nz > 0).sum())
        hier.append(dict(explainer=ex, c=c, subset=sub, mean_log_compute_ratio=lcr, sign_test_p=(binomtest(fav, len(nz), .5).pvalue if len(nz) else np.nan), metric={"lerr": "log_err_ratio_rep_over_big"}.get(m, f"match_diff_k{m[1:]}"),
                         n_cells=len(cn_), n_pairs=int(sum(len(A[cn]) for cn in cn_)), estimate=pt.mean(),
                         lo=np.quantile(boots, .025), hi=np.quantile(boots, .975), n_datasets=len(dsets),
                         lo_dataset_cluster=np.quantile(boots_ds, .025), hi_dataset_cluster=np.quantile(boots_ds, .975), cells_favouring_repeat=int((pt < 0).sum() if m == "lerr" else (pt > 0).sum())))
pd.DataFrame(hier).to_csv(f"{out}/c5_hier.csv", index=False)
print(len(hier), "hierarchical rows")


# per cell: mean over the matched pairs of the repeat-minus-enlarged difference, instances resampled jointly across the pairs of the cell
cr_ = np.random.RandomState(9); rowsc = []
for (ex, c, sub), cells in sorted(store.items()):
    if not sub.startswith("matched"):
        continue
    for cn in sorted(cells):
        for m in ("lerr", "m3"):
            A = np.array([v[m] for v, _ in cells[cn] if m in v])
            if not A.size:
                continue
            bs = [A[:, ix].mean() for ix in cr_.randint(0, A.shape[1], (1000, A.shape[1]))]
            rowsc.append(dict(cell=cn, explainer=ex, c=c, subset=sub, metric="log_err_ratio_rep_over_big" if m == "lerr" else "match_diff_k3",
                              n_pairs=len(A), mean_compute_ratio=float(np.mean([cr for v, cr in cells[cn] if m in v])), estimate=A.mean(),
                              lo=np.quantile(bs, .025), hi=np.quantile(bs, .975)))
pd.DataFrame(rowsc).to_csv(f"{out}/c5_cell.csv", index=False)
print(len(rowsc), "per-cell rows")
