"""Merge per-benchmark tables; write data audit, splits, headline predictions, cross-benchmark aggregate, provenance.
usage: merge_tables.py OUTDIR RAWDIR [RAWDIR ...]"""
import glob, json, os, subprocess, sys
import numpy as np, pandas as pd
from scipy.stats import wilcoxon
sys.path.insert(0, os.path.dirname(__file__))
import analysis as A, data, protocol as P

out, dirs = sys.argv[1], sys.argv[2:]
cells = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{out}/cells/*.csv")) if "__paired" not in f])
paired = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{out}/cells/*__paired.csv"))])
DEV = ["ifeval", "arc_challenge", "gpqa", "gsm"]   # benchmarks used to choose the ensemble predictor of mass_ens (development pilot)
NARROW = ["gpqa", "musr", "openllm_math"]            # narrow spread of model accuracies (see data_audit.csv)
SUBSETS = {"all13": list(data.ALL), "non_dev9": [b for b in data.ALL if b not in DEV], "dev4": DEV,
           "oll": list(data.OPENLLM), "helm": list(data.HELM), "narrow3": NARROW}
for t in (cells, paired):
    t.insert(1, "dev_bench", t.bench.isin(DEV))
cells.to_csv(f"{out}/cells.csv", index=False, float_format="%.6g")
paired.to_csv(f"{out}/paired.csv", index=False, float_format="%.6g")

# --- data audit
rows = []
for b in data.ALL:
    X0, m0 = data.load(b)
    X, m = P.dedup(X0, m0)
    a = X.mean(1)
    rows.append(dict(bench=b, suite="openllm" if b in data.OPENLLM else "helm", n_models_raw=X0.shape[0], n_models_dedup=X.shape[0],
                     n_items=X.shape[1], acc_min=a.min(), acc_median=np.median(a), acc_max=a.max(), n_missing=0,
                     n_const_items=int((X.min(0) == X.max(0)).sum()), has_model_names=m is not None))
pd.DataFrame(rows).to_csv(f"{out}/data_audit.csv", index=False)

# --- predictions (headline budgets), splits
raw = A.load(dirs)
raw = raw[raw.method.isin(cells.method.unique())]
pr_rows, sp_rows = [], []
for b, g in raw.groupby("bench"):
    Xd, md = P.dedup(*data.load(b))
    Xr, mr = data.load(b)
    for proto, gp in g.groupby("protocol"):
        X, m = (Xr, mr) if proto.endswith("nodedup") else (Xd, md)
        acc = X.mean(1)
        for rep, gr in gp.groupby("rep"):
            tgt = np.sort(gr.model.unique())
            src_n = int(gr.n_src.iloc[0])
            sp_rows.append(dict(bench=b, protocol=proto, rep=rep, n_src=src_n, n_tgt=len(tgt),
                                target_models=" ".join(map(str, tgt))))
        h = gp[gp.n.isin([50, 100])]
        # source set of rep 0 (fixed for extrap*) defines the position relative to the sources
        srcacc = {}
        for rep in h.rep.unique():
            tgt = h[h.rep == rep].model.unique()
            if proto.startswith("extrap"):
                src = np.setdiff1d(np.arange(len(acc)), np.where(acc >= np.sort(acc)[-len(tgt)])[0])
            else:
                src = np.setdiff1d(np.arange(len(acc)), tgt)
            srcacc[rep] = np.sort(acc[src])
        if proto.startswith("extrap"):
            mean = h.groupby(["method", "n", "model"], as_index=False).agg(true=("true", "first"), pred=("pred", "mean"), pred_sd=("pred", "std"), n_reps=("rep", "nunique"))
            sa = srcacc[min(srcacc)]
            mean["rank_pct_in_sources"] = [float((sa < t).mean()) for t in mean.true]
            mean["above_all_sources"] = mean.true > sa.max()
        else:
            mean = h.groupby(["method", "n", "model"], as_index=False).agg(true=("true", "first"), pred=("pred", "mean"), pred_sd=("pred", "std"), n_reps=("rep", "nunique"))
            mean["rank_pct_in_sources"] = np.nan
            mean["above_all_sources"] = np.nan
        mean["bench"], mean["protocol"] = b, proto
        names = m
        mean["model_name"] = [names[i] if names else "" for i in mean.model]
        pr_rows.append(mean)
HEAD = ["random", "ridge", "aipw_rand", "anchor", "anchor_irt", "calib", "irt_rand", "sources_only", "mass_ens", "mass", "aipw_ridge_repo", "aipw_ridge_cf"]
pr = pd.concat(pr_rows)
pr = pr[pr.protocol.isin(["random", "extrap"]) & pr.method.isin(HEAD)]  # headline methods / protocols only (file size)
pr.to_csv(f"{out}/predictions_headline.csv", index=False, float_format="%.5g")
pd.DataFrame(sp_rows).to_csv(f"{out}/splits.csv", index=False)

# --- cross-benchmark aggregate (benchmark = unit); reference = random, ridge, strongest-by-source-CV baseline
bbp = f"{out}/best_baseline.csv"
best = {}
if os.path.exists(bbp):
    bb = pd.read_csv(bbp)
    best = {(r.bench, r.protocol): r.method for r in bb.itertuples()}
rng = np.random.default_rng(0)
ag, rk = [], []
for (proto, n), g in cells.groupby(["protocol", "n"]):
    base_p = "extrap" if proto.startswith("extrap") else "random"
    for met in ["mae", "rmse", "spearman", "kendall"]:
        pv0 = g[g.metric == met].pivot(index="bench", columns="method", values="mean")
        for sub, members in SUBSETS.items():
            pv = pv0.loc[[b for b in pv0.index if b in members]]
            if len(pv) < 3:
                continue
            for refname in ["random", "ridge", "best_cv"]:
                if refname == "best_cv":
                    if not best:
                        continue
                    ref = pd.Series({b: pv.loc[b, best[(b, base_p)]] if (b, base_p) in best and best[(b, base_p)] in pv.columns else np.nan for b in pv.index})
                else:
                    if refname not in pv:
                        continue
                    ref = pv[refname]
                for m in pv.columns:
                    if m == refname:
                        continue
                    ok = pv[m].notna() & ref.notna()
                    if ok.sum() < 3:
                        continue
                    lower_better = met in ("mae", "rmse")
                    if lower_better:
                        stat = np.log(pv[m][ok] / ref[ok]).values   # log ratio; <0 better than reference
                    else:
                        stat = (pv[m][ok] - ref[ok]).values          # >0 better than reference
                    bs = stat[rng.integers(0, len(stat), (2000, len(stat)))].mean(1)
                    try:
                        pw = wilcoxon(stat).pvalue if (np.any(stat != 0) and len(stat) >= 6) else np.nan
                    except ValueError:
                        pw = np.nan
                    ex = (lambda x: np.exp(x)) if lower_better else (lambda x: x)
                    ag.append(dict(subset=sub, protocol=proto, n=n, metric=met, method=m, ref=refname, n_bench=len(stat), effect=ex(stat.mean()),
                                   ci_lo=ex(np.percentile(bs, 2.5)), ci_hi=ex(np.percentile(bs, 97.5)),
                                   wins=int((stat < 0).sum() if lower_better else (stat > 0).sum()), wilcoxon_p=pw,
                                   effect_def=("geomean_ratio" if lower_better else "mean_diff")))
            if met in ("spearman", "kendall"):
                for m in pv.columns:
                    rk.append(dict(subset=sub, protocol=proto, n=n, metric=met, method=m, n_bench=int(pv[m].notna().sum()), mean_value=pv[m].mean(), min_value=pv[m].min(), max_value=pv[m].max()))
pd.DataFrame(ag).to_csv(f"{out}/aggregate.csv", index=False)
pd.DataFrame(rk).to_csv(f"{out}/ranking_by_subset.csv", index=False, float_format="%.5g")   # absolute mean rank correlation per method, subset, protocol, n

# --- benchmark counts whose paired CI excludes 0 (per-benchmark model-level bootstrap), proposed vs references
cnt = []
for prop in ["mass_ens", "mass"]:
    pp = paired[(paired.method == prop) & paired.metric.isin(["rmse", "kendall"])].copy()
    if best:   # per-benchmark source-CV choice also counted as the pseudo-reference "best_cv"
        bc = pp[[best.get((r.bench, "extrap" if r.protocol.startswith("extrap") else "random")) == r.ref for r in pp.itertuples()]].copy()
        bc["ref"] = "best_cv"
        pp = pd.concat([pp, bc])
    for (proto, n, met, ref), g in pp.groupby(["protocol", "n", "metric", "ref"]):
        better = (g.ci_hi < 0) if met == "rmse" else (g.ci_lo > 0)
        worse = (g.ci_lo > 0) if met == "rmse" else (g.ci_hi < 0)
        for sub, members in SUBSETS.items():
            k = g.bench.isin(members).values
            if k.sum():
                cnt.append(dict(subset=sub, proposed=prop, protocol=proto, n=n, metric=met, ref=ref, n_bench=int(k.sum()),
                                n_better=int(better.values[k].sum()), n_worse=int(worse.values[k].sum())))
pd.DataFrame(cnt).to_csv(f"{out}/proposed_ci_counts.csv", index=False)

# --- effective-sample-size gain: (RMSE_random / RMSE_method)^2 (items-equivalent factor) per cell
r = cells[cells.metric == "rmse"].pivot_table(index=["bench", "protocol", "n"], columns="method", values="mean")
ess = ((r["random"].values[:, None] / r.values) ** 2)
pd.DataFrame(ess, index=r.index, columns=r.columns).stack().rename("ess_gain").reset_index().to_csv(f"{out}/ess_gain.csv", index=False)

# --- coverage of the reported interval (methods with a standard error) and bias
cv = raw[raw.se.notna()].copy() if "se" in raw else pd.DataFrame()
if len(cv):
    cv["cover95"] = (cv.pred - cv.true).abs() <= 1.96 * cv.se
    cv["cover80"] = (cv.pred - cv.true).abs() <= 1.2816 * cv.se
    cv["z"] = (cv.pred - cv.true) / cv.se
    cv.groupby(["bench", "protocol", "method", "n"], as_index=False).agg(
        cover95=("cover95", "mean"), cover80=("cover80", "mean"), mean_se=("se", "mean"), z_sd=("z", "std"), n_obs=("z", "size")
    ).to_csv(f"{out}/coverage.csv", index=False)

prov = dict(git_commit=subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
            data_commit="55faff496947789f94e6b5908c77cbc3e84f81ad", bootstrap_B=200, raw_dirs=dirs,
            budgets=sorted(map(int, cells.n.unique())), methods=sorted(cells.method.unique()),
            protocols=sorted(cells.protocol.unique()))
json.dump(prov, open(f"{out}/provenance.json", "w"), indent=1)
print("merged", len(cells), len(paired))
