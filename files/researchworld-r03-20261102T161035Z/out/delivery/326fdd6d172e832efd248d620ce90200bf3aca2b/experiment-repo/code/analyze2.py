"""Aggregate common-target-set runs (ct_*.csv; shards *_a/_b merged). usage: analyze2.py RAW_DIR OUT_DIR
Outputs ct_curves.csv (z-RMSE, cluster-bootstrap CI over test models, skill), ct_reference.csv (full-information reference),
ct_paired.csv (selector minus random / minus greedy_ridge, same targets), ct_k_needed.csv (sufficiency criteria)."""
import sys, glob, os, re, numpy as np, pandas as pd
from scipy import stats
raw, out = sys.argv[1:3]; B = 1000; rng = np.random.default_rng(0); FULL = 9999
groups = {}
for f in sorted(glob.glob(os.path.join(raw, "ct_*.csv")) + glob.glob(os.path.join(raw, "ex_*.csv"))):      # ex_*: extra selectors/PRED runs of the same splits
    groups.setdefault(re.sub(r"_[a-f]$", "", re.sub(r"^ex_", "ct_", os.path.basename(f)[:-4])), []).append(f)
curves, refs, paired, kneed = [], [], [], []
views = []
for name, fs in groups.items():
    d = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates(["rep", "sel", "inf", "k", "model", "target"]); data = name[3:]
    repsets = d.groupby("sel").rep.agg(lambda r: frozenset(r)); Rfull = repsets["random"]; part = [s for s in repsets.index if repsets[s] != Rfull]
    if not part: views.append((data, d)); continue
    # selectors run on a subset of the repeats (ex_* runs) are only compared on those repeats: separate view "<data>|sub" with every selector restricted to them
    Rsub = frozenset.intersection(*[repsets[s] for s in part])
    views.append((data, d[~d.sel.isin(part)])); views.append((data + "|sub", d[d.rep.isin(Rsub)]))
for data, d in views:
    units = np.sort(d.model.unique()); ui = {u: i for i, u in enumerate(units)}; d["u"] = d.model.map(ui); U = len(units)
    cnt = np.stack([np.bincount(b, minlength=U) for b in rng.integers(0, U, (B, U))])
    cache = {}
    for (sel, inf, k), g in d.groupby(["sel", "inf", "k"]):
        s = np.bincount(g.u, weights=g.sez2, minlength=U); n = np.bincount(g.u, weights=g.n, minlength=U); cache[(sel, inf, k)] = (s, n)
        est = np.sqrt(s.sum() / n.sum()); bt = np.sqrt((cnt @ s) / np.maximum(cnt @ n, 1)); lo, hi = np.percentile(bt, [2.5, 97.5])
        curves.append((data, sel, inf, k, est, lo, hi, np.sqrt(g.se2.sum() / g.n.sum()), g.model.nunique(), g.rep.nunique(), g.ksz.mean()))
    cv = pd.DataFrame(curves[-len(cache):], columns="data sel inf k zrmse lo hi rmse_raw n_models n_reps mean_ksz".split())
    # paired
    ks = sorted(set(k for (_, _, k) in cache if k != FULL))
    pairs = [(a, "random") for a in sorted(set(s for (s, _, _) in cache)) if a not in ("random", "full")] + \
            [("random", "greedy_ridge")] + [(a, "greedy_ridge") for a in ("greedy_bayes", "qr", "coverage", "variance", "corr_mean", "farthest", "backelim", "random_pm")]
    for inf in ("ridge", "fa", "knn"):
        for a, b in pairs:
            for k in ks:
                if (a, inf, k) not in cache or (b, inf, k) not in cache: continue
                (sa, na), (sb, nb) = cache[(a, inf, k)], cache[(b, inf, k)]; ok = (na > 0) & (nb > 0)
                diff = np.sqrt(sa.sum() / na.sum()) - np.sqrt(sb.sum() / nb.sum())
                bt = np.sqrt((cnt @ sa) / np.maximum(cnt @ na, 1)) - np.sqrt((cnt @ sb) / np.maximum(cnt @ nb, 1)); lo, hi = np.percentile(bt, [2.5, 97.5])
                da, db = (sa / np.maximum(na, 1))[ok], (sb / np.maximum(nb, 1))[ok]
                p = stats.wilcoxon(da, db).pvalue if np.any(da != db) else 1.0
                paired.append((data, a, b, inf, k, diff, lo, hi, p, int(ok.sum())))
    # reference + sufficiency
    mean_s, mean_n = cache[("random", "mean", ks[0])]; mean_z = np.sqrt(mean_s.sum() / mean_n.sum())
    for inf in ("ridge", "fa", "knn", "rank1"):
        if ("full", inf, FULL) not in cache: continue
        s, n = cache[("full", inf, FULL)]; zf = np.sqrt(s.sum() / n.sum()); bt = np.sqrt((cnt @ s) / np.maximum(cnt @ n, 1)); lo, hi = np.percentile(bt, [2.5, 97.5])
        skf = 1 - (zf / mean_z) ** 2; refs.append((data, inf, zf, lo, hi, mean_z, skf))
        for sel in ("random", "random_pm", "greedy_ridge", "greedy_bayes", "backelim"):
            sub = cv[(cv.sel == sel) & (cv.inf == inf) & (cv.k != FULL)].sort_values("k")
            if not len(sub): continue
            sk = 1 - (sub.zrmse / mean_z) ** 2
            for crit, ok in (("skill>=0.9*ref_skill", sk >= 0.9 * skf), ("zrmse<=1.1*ref", sub.zrmse <= 1.1 * zf), ("zrmse<=1.25*ref", sub.zrmse <= 1.25 * zf)):
                kneed.append((data, sel, inf, crit, int(sub.k[ok.values].iloc[0]) if ok.any() else None, int(sub.k.max()), float(sk.iloc[-1]), float(skf)))
cvall = pd.concat([pd.DataFrame(c, columns="data sel inf k zrmse lo hi rmse_raw n_models n_reps mean_ksz".split()) for c in [curves]])
mean_ref = cvall[(cvall.sel == "random") & (cvall.inf == "mean")].groupby(["data", "k"]).zrmse.first()
cvall["skill"] = [1 - (r.zrmse / mean_ref[(r.data, min(k for (dd, k) in mean_ref.index if dd == r.data))]) ** 2 for r in cvall.itertuples()]
cvall.to_csv(os.path.join(out, "ct_curves.csv"), index=False)
pd.DataFrame(refs, columns="data inf ref_zrmse lo hi mean_zrmse ref_skill".split()).to_csv(os.path.join(out, "ct_reference.csv"), index=False)
pd.DataFrame(paired, columns="data sel_a sel_b inf k diff_zrmse lo hi wilcoxon_p n_models".split()).to_csv(os.path.join(out, "ct_paired.csv"), index=False)
pd.DataFrame(kneed, columns="data sel inf criterion k_needed kmax_tried skill_at_kmax ref_skill".split()).to_csv(os.path.join(out, "ct_k_needed.csv"), index=False)
print(pd.read_csv(os.path.join(out, "ct_reference.csv")).round(3).to_string())
