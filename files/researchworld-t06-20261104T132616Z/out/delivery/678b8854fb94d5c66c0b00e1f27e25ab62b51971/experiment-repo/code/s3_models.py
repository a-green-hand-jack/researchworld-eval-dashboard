"""Q3: is the adversarial flip budget explained by the statistical margin (z-gap), the influence signal-to-noise, or the data on the pair?

Sample: strictly ordered adjacent-pair claims (c2, base gap > 1e-9) with a verified budget >= 1 of results/budgets_remove.csv, joined with
the influence descriptors of results/s3_influence.csv. Datasets: arena55k, mt_human, mt_gpt4 and nba_seasons (the 69 regular-season fits;
the NBA full-history fit `nba_all` is only fitted separately, as an ablation). Per the plan there is NO inference about 'design' across the
3-4 datasets: every pooled model has dataset-specific intercepts (reference: nba_seasons) and weights each dataset equally.
Models (response log budget):
  M0  log z                    M1  log z + log n_pair_involving      M2  log snr (influence)
  M3  log z + log snr          M4  log z + log snr + log n_pair_involving      M5  log gap + log n_pair_involving
fitted per dataset (OLS) and pooled (WLS, dataset intercepts, weight 1/n_claims of the dataset).
Uncertainty: bootstrap B (default 2000) resampling claims within a dataset; for the NBA seasons the 69 seasons are the clusters.
Writes results/s3_models_coef.csv, results/s3_models_bins.csv.   Usage: python code/s3_models.py [--B 2000]"""
import argparse
import os

import numpy as np
import pandas as pd

from btlib import prov

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
DS = ["nba_seasons", "arena55k", "mt_human", "mt_gpt4"]
MODELS = {
    "M0 log z": ["log_z"],
    "M1 log z + log n_pair": ["log_z", "log_n_pair_involving"],
    "M2 log snr": ["log_snr"],
    "M3 log z + log snr": ["log_z", "log_snr"],
    "M4 log z + log snr + log n_pair": ["log_z", "log_snr", "log_n_pair_involving"],
    "M5 log gap + log n_pair": ["log_gap", "log_n_pair_involving"],
    "M0c log z_cluster": ["log_zc"],  # z from the cluster / block bootstrap (results/s5_cluster_se.csv, request #7)
    "M1c log z_cluster + log n_pair": ["log_zc", "log_n_pair_involving"],
}


def prep():
    d = pd.read_csv(f"{OUT}/budgets_remove.csv")
    inf = pd.read_csv(f"{OUT}/s3_influence.csv")
    d = d.merge(inf, on=["unit", "claim"], how="left")
    cl = pd.read_csv(f"{OUT}/s5_cluster_se.csv")[["unit", "claim", "z_cluster", "se_gap_cluster"]]
    d = d.merge(cl, on=["unit", "claim"], how="left")
    d = d[d.claim.str.startswith("c2") & (d.gap > 1e-9) & (d.budget >= 1) & (d.z > 0) & d.flipped].copy()
    d["dataset"] = np.where(d.season.notna(), "nba_seasons", d.unit)
    d = d[d.dataset.isin(DS)]
    d["log_budget"] = np.log(d.budget)
    d["log_z"] = np.log(d.z)
    d["log_zc"] = np.log(d.z_cluster.where(d.z_cluster > 0))
    d["log_gap"] = np.log(d.gap)
    d["log_snr"] = np.log(d.infl_snr.clip(lower=1e-12))
    d["log_n_pair_involving"] = np.log(d.n_a_or_b.clip(lower=1))
    d["cluster"] = np.where(d.season.notna(), d.season.fillna(0).astype(int).astype(str), d.unit + ":" + d.claim)
    return d.dropna(subset=["log_snr", "log_zc"])


class Data:
    """Arrays of one scope plus, per dataset, the index sets that are resampled (NBA: whole seasons; others: single claims)."""

    def __init__(self, d):
        self.d = d.reset_index(drop=True)
        self.y = self.d.log_budget.values
        self.ds = self.d.dataset.values
        self.groups = []
        for _, s in self.d.groupby("dataset"):
            if s.season.notna().all():
                self.groups.append([np.asarray(v) for v in s.groupby("cluster").groups.values()])
            else:
                self.groups.append([np.array([i]) for i in s.index])

    def resample(self, rng):
        out = []
        for g in self.groups:
            out += [g[k] for k in rng.integers(0, len(g), len(g))]
        return np.concatenate(out)

    def design(self, terms, pooled):
        cols, names = [np.ones(len(self.d))], ["const"]
        if pooled:
            for k in DS[1:]:
                cols.append((self.ds == k).astype(float)); names.append(f"dataset_{k}")
        for t in terms:
            cols.append(self.d[t].values); names.append(t)
        return np.column_stack(cols), names


def wls(dat, X, idx, pooled):
    Xi, y = X[idx], dat.y[idx]
    if pooled:
        _, inv, cnt = np.unique(dat.ds[idx], return_inverse=True, return_counts=True)
        w = 1.0 / cnt[inv]
        w = w / w.sum() * len(w)
    else:
        w = np.ones(len(idx))
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(Xi * sw[:, None], y * sw, rcond=None)
    res = y - Xi @ beta
    ybar = np.average(y, weights=w)
    r2 = 1 - np.sum(w * res ** 2) / np.sum(w * (y - ybar) ** 2)
    return beta, r2, float(np.sqrt(np.average(res ** 2, weights=w)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=2000)
    a = ap.parse_args()
    d = prep()
    rows = []
    for label, terms in MODELS.items():
        for scope in ["pooled"] + DS:
            s = d if scope == "pooled" else d[d.dataset == scope]
            if len(s) < 8:
                continue
            dat = Data(s)
            X, names = dat.design(terms, scope == "pooled")
            beta, r2, rmse = wls(dat, X, np.arange(len(s)), scope == "pooled")
            rng = np.random.default_rng(5)
            bs = np.array([wls(dat, X, dat.resample(rng), scope == "pooled")[0] for _ in range(a.B)])
            for k, nme in enumerate(names):
                lo, hi = np.percentile(bs[:, k], [2.5, 97.5])
                rows.append(dict(scope=scope, model=label, term=nme, coef=beta[k], ci_lo=lo, ci_hi=hi, r2=r2, rmse_log=rmse,
                                 n_claims=len(s), boot_B=a.B))
    out = pd.DataFrame(rows)
    out.to_csv(f"{OUT}/s3_models_coef.csv", index=False, float_format="%.5g")
    # budgets by z-gap bin and dataset (median with interval from the same resampling)
    bins = [0, 0.25, 0.5, 1, 2, 4, 8, 100]
    d["zbin"] = pd.cut(d.z, bins)
    ob = []
    for (ds, zb), s in d.groupby(["dataset", "zbin"], observed=True):
        rng = np.random.default_rng(6)
        dat = Data(s)
        meds = [np.median(dat.d.frac_pairinv.values[dat.resample(rng)]) for _ in range(500)] if len(s) > 1 else [np.nan]
        ob.append(dict(dataset=ds, design=s.design.iloc[0], zbin=str(zb), n=len(s), median_budget=s.budget.median(), median_frac_N=s.frac_N.median(),
                       median_frac_pairinv=s.frac_pairinv.median(), pairinv_ci_lo=np.percentile(meds, 2.5), pairinv_ci_hi=np.percentile(meds, 97.5),
                       median_leverage=s.leverage.median()))
    pd.DataFrame(ob).to_csv(f"{OUT}/s3_models_bins.csv", index=False, float_format="%.5g")
    prov.write_meta(f"{OUT}/s3_models.meta.json", script="code/s3_models.py", args=vars(a))
    print(out[out.term.str.startswith("log_")].round(3).to_string())


if __name__ == "__main__":
    main()
