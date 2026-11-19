"""Compute reliability metrics from stored KernelSHAP runs and write tables.

Terminology
  runs[r, i, j]  attribution of feature j for instance i from the r-th independent run
  ref[i, j]      reference attribution: exact Shapley (ACS, Pima) or none (German)
  T3             top-3 feature set by |attribution|
  m3_i           fraction of runs whose top-3 set equals the reference top-3 set
  reliable_i     m3_i >= THR (pre-registered threshold 0.9)
Outputs: /work/results/tables/*.csv and results/metrics_long.parquet (per-instance metrics)
"""
import os

import numpy as np
import pandas as pd

from common import BUDGETS_BY_DS, DATASETS, MODELS, K_BG, R_RUNS, RES_DIR, RETRAIN_SEEDS
from explain import out_path

TAB = f"{RES_DIR}/tables"
os.makedirs(TAB, exist_ok=True)
P_RBO = 0.9  # persistence of rank-biased overlap (Webber et al., 2010)
THR = 0.9  # single-run reliability threshold on the top-3 match rate
SATURATED = {"acs": 1000, "pima": 250, "german": 10**9}  # largest budget below the 2^d-2 cap
rng = np.random.RandomState(0)


def load_runs(ds, model, budget, output="prob", K=K_BG):
    return np.stack([np.load(out_path(ds, model, output, K, budget, r)) for r in range(R_RUNS)])


def load_ref(ds, model, output="prob", seed=0):
    if ds in ("acs", "pima"):
        return np.load(f"{RES_DIR}/exact/{ds}_{model}_s{seed}_{output}.npy")
    return None


def topk(phi, k):
    idx = np.argsort(-np.abs(phi), axis=-1, kind="stable")[..., :k]
    return np.sort(idx, axis=-1)


def rbo_ext_batch(a, b, p=P_RBO):
    """Extrapolated rank-biased overlap of full rankings of |a| and |b| (rows = instances)."""
    N, d = a.shape
    ra = np.argsort(np.argsort(-np.abs(a), axis=1), axis=1)
    rb = np.argsort(np.argsort(-np.abs(b), axis=1), axis=1)
    mx = np.maximum(ra, rb)
    t = np.arange(1, d + 1)
    X = np.stack([(mx < tt).sum(axis=1) for tt in t], axis=1)  # overlap at each depth
    return (1 - p) / p * ((X / t) * p ** t).sum(axis=1) + X[:, -1] / d * p ** d


def boot_ci(x, B=2000, seed=0):
    x = np.asarray(x, float)
    r = np.random.RandomState(seed)
    m = np.array([x[r.randint(0, len(x), len(x))].mean() for _ in range(B)])
    return x.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


def run_metrics(runs, ref):
    R, N, d = runs.shape
    T3 = topk(runs, 3)  # R,N,3
    pairs = [(a, b) for a in range(R) for b in range(a + 1, R)]
    agree = np.zeros((len(pairs), N), bool)
    jac = np.zeros((len(pairs), N))
    rbo = np.zeros((len(pairs), N))
    for k, (a, b) in enumerate(pairs):
        inter = (T3[a][:, :, None] == T3[b][:, None, :]).any(-1).sum(-1)
        jac[k] = inter / (6 - inter)
        agree[k] = inter == 3
        rbo[k] = rbo_ext_batch(runs[a], runs[b])
    out = {"pair_agree": agree.mean(0), "pair_jac": jac.mean(0), "pair_rbo": rbo.mean(0)}
    # reference-free margin between 3rd and 4th feature, from the runs only
    order = np.argsort(-np.abs(runs).mean(0), axis=1)
    rows = np.arange(N)
    j3, j4 = order[:, 2], order[:, 3]
    D = np.abs(runs)[:, rows, j3] - np.abs(runs)[:, rows, j4]  # R,N
    out["z_run"] = np.abs(D.mean(0)) / (D.std(0, ddof=1) + 1e-12)
    mean_att = runs.mean(0)
    out["nsr"] = np.sqrt(((runs - mean_att) ** 2).sum(-1).mean(0)) / np.linalg.norm(mean_att, axis=1)
    out["var"] = runs.var(0, ddof=1).mean(-1)  # per instance, mean over features
    if ref is not None:
        T3r = topk(ref, 3)
        T1r = topk(ref, 1)
        correct = (T3 == T3r[None]).all(-1)  # R,N
        out["m3"] = correct.mean(0)
        out["m1"] = (topk(runs, 1) == T1r[None]).all(-1).mean(0)
        sg = np.sign(runs[:, rows[:, None], T3r]) == np.sign(ref[rows[:, None], T3r])[None]
        out["sign3"] = sg.mean(axis=(0, 2))
        out["relerr"] = (np.linalg.norm(runs - ref[None], axis=-1)
                         / np.linalg.norm(ref, axis=-1)[None]).mean(0)
        out["_correct_pairs"] = np.stack([correct[a] for a, _ in pairs] +
                                         [correct[b] for _, b in pairs])
        out["_agree_pairs"] = np.concatenate([agree, agree])
    return out


def main():
    long_rows = []
    summary = []
    tworun = []
    scaling = []
    for ds in DATASETS:
        for mn in MODELS:
            per_budget_var = {}
            for b in BUDGETS_BY_DS[ds]:
                runs = load_runs(ds, mn, b)
                ref = load_ref(ds, mn)
                m = run_metrics(runs, ref)
                per_budget_var[b] = m["var"].mean()
                pa = m.pop("_correct_pairs", None)
                ag = m.pop("_agree_pairs", None)
                if pa is not None:
                    tworun.append(dict(ds=ds, model=mn, budget=b,
                                       P_correct=pa.mean(),
                                       P_correct_given_agree=pa[ag].mean(),
                                       P_correct_given_disagree=pa[~ag].mean() if (~ag).any() else np.nan,
                                       frac_agree=ag.mean()))
                for i in range(runs.shape[1]):
                    row = dict(ds=ds, model=mn, budget=b, inst=i)
                    row.update({k: float(v[i]) for k, v in m.items()})
                    long_rows.append(row)
                ms = pd.DataFrame({k: v for k, v in m.items()})
                s = dict(ds=ds, model=mn, budget=b)
                for k in ["m3", "m1", "sign3", "relerr", "pair_agree", "pair_jac", "pair_rbo", "nsr", "var", "z_run"]:
                    if k in ms:
                        mu, lo, hi = boot_ci(ms[k].values)
                        s[k] = mu
                        s[k + "_lo"], s[k + "_hi"] = lo, hi
                if "m3" in ms:
                    rel = (ms["m3"].values >= THR).astype(float)
                    mu, lo, hi = boot_ci(rel)
                    s["reliable_share"], s["reliable_lo"], s["reliable_hi"] = mu, lo, hi
                summary.append(s)
            # budget scaling of the run variance on non-saturated budgets
            bs = [b for b in BUDGETS_BY_DS[ds] if b <= SATURATED[ds]]
            if len(bs) >= 3:
                slope = np.polyfit(np.log(bs), np.log([per_budget_var[b] for b in bs]), 1)[0]
                scaling.append(dict(ds=ds, model=mn, budgets=str(bs), loglog_slope_var=slope))
    S = pd.DataFrame(summary)
    S.to_csv(f"{TAB}/summary_by_config.csv", index=False)
    pd.DataFrame(long_rows).to_parquet(f"{RES_DIR}/metrics_long.parquet", index=False)
    pd.DataFrame(tworun).to_csv(f"{TAB}/two_run_check.csv", index=False)
    pd.DataFrame(scaling).to_csv(f"{TAB}/variance_scaling.csv", index=False)
    print(S[["ds", "model", "budget", "m3", "reliable_share", "pair_agree", "pair_rbo", "relerr", "var"]]
          .round(3).to_string())


if __name__ == "__main__":
    main()
