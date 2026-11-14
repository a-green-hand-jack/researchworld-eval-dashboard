"""Offline research helpers (NOT used by the RPC entry point ``program.handle``).

Contains
  * ``run_ablation_grid``  : repeated K-fold leave-models-out CV over {z-score vs quantile transform} x
                             {trace vs wrapper vs random selection} x {Gaussian only vs stacked} x {clip on/off},
                             with a column-median baseline; per-held-out-model nrmse on identical folds;
  * ``summarise_grid``     : mean +- bootstrap CI (``bootstrap_ci``) and paired Wilcoxon tests against random
                             selection and against the cycle-1 configuration (z-score, trace, Gaussian, no clip);
  * ``run_k_sweep``        : the ablation restricted to the headline cells for k in {1,2,3,5,8,12,20};
  * ``synthetic_factor_matrix`` / ``theoretical_posterior_error`` / ``synthetic_theory_check``: rank-r factor-model
    theory check, with a heavy-tailed (Student-t, 3 dof) variant showing where the Gaussian theory breaks.

nrmse of a held-out model = sqrt(mean over its observed, non-selected cells of ((pred - y) / std_b)^2) with std_b the
TRAINING-fold standard deviation of benchmark b (the evaluator's own normalisation is not known to us).

Usage:
  python experiments.py synthetic out.json
  python experiments.py ablation matrix.npz out.json [k]   (npz with arrays ``values`` [M,N] and ``mask`` [M,N])
  python experiments.py ksweep matrix.npz out.json
Everything is seeded.
"""
import json
import sys

import numpy as np

try:
    from program import (_build_sigma, _cv_tune, _forward_columns, _make_folds, build_rep, conditional_gaussian_impute,
                         em_gaussian_covariance, fit_model, greedy_select_conditional_variance,
                         predict_raw, quantile_normal_transform, inverse_quantile_transform,
                         wrapper_forward_select_cv, QUICK_SHRINKS, QUICK_RANKS, QUICK_LAMS)
except ImportError:  # pragma: no cover
    from .program import (_build_sigma, _cv_tune, _forward_columns, _make_folds, build_rep, conditional_gaussian_impute,
                          em_gaussian_covariance, fit_model, greedy_select_conditional_variance,
                          predict_raw, quantile_normal_transform, inverse_quantile_transform,
                          wrapper_forward_select_cv, QUICK_SHRINKS, QUICK_RANKS, QUICK_LAMS)


# ---------------------------------------------------------------------------------------------------------
# synthetic theory check
# ---------------------------------------------------------------------------------------------------------
def synthetic_factor_matrix(m, n, r, sigma, missing_rate=0.0, seed=0, heavy_tail=False, dof=3):
    """Rank-r factor model x = L f + sigma eps. Gaussian by default; with heavy_tail=True the factors and the noise
    are Student-t with ``dof`` degrees of freedom rescaled to unit variance (rng.standard_t), so that the covariance
    is identical but the marginals are heavy-tailed. Returns X [m, n], mask, true Sigma."""
    rng = np.random.default_rng(seed)
    L = rng.normal(size=(n, r)) / np.sqrt(r)
    if heavy_tail:
        scale = np.sqrt((dof - 2.0) / dof)
        f = rng.standard_t(dof, size=(m, r)) * scale
        eps = rng.standard_t(dof, size=(m, n)) * scale
    else:
        f = rng.normal(size=(m, r))
        eps = rng.normal(size=(m, n))
    X = f @ L.T + sigma * eps
    mask = rng.random((m, n)) >= missing_rate
    Sigma = L @ L.T + sigma ** 2 * np.eye(n)
    return X, mask, Sigma


def theoretical_posterior_error(Sigma, selected, lam=0.0):
    """Mean per-benchmark posterior variance of the unselected benchmarks:
    tr(Sigma_UU - Sigma_US (Sigma_SS + lam I)^-1 Sigma_SU) / |U|."""
    n = Sigma.shape[0]
    S = np.asarray(selected, dtype=int)
    U = np.setdiff1d(np.arange(n), S)
    Sigma_UU = Sigma[np.ix_(U, U)]
    Sigma_US = Sigma[np.ix_(U, S)]
    Sigma_SS = Sigma[np.ix_(S, S)] + lam * np.eye(len(S))
    post = Sigma_UU - Sigma_US @ np.linalg.solve(Sigma_SS, Sigma_US.T)
    return float(np.trace(post) / len(U))


def synthetic_theory_check(m=400, n=40, r=4, sigma=0.3, ks=(1, 2, 3, 4, 6, 8, 12), n_test=4000, seed=0,
                           heavy_tail=False, dof=3):
    """Measured test MSE of greedy-trace selection + Gaussian conditional mean vs the closed-form posterior error.
    For the Gaussian case they should agree up to estimation error; for heavy_tail=True the theory (which only uses
    second moments) still gives the best LINEAR predictor error but the measured error of the EM-fitted Gaussian is
    expected to deviate. An extra column reports the same predictor after a rank-Gauss transform of every column."""
    X, mask, Sigma_true = synthetic_factor_matrix(m, n, r, sigma, 0.0, seed, heavy_tail, dof)
    Xt, _, _ = synthetic_factor_matrix(n_test, n, r, sigma, 0.0, seed + 1, heavy_tail, dof)
    mu, Sig, _, _ = em_gaussian_covariance(X, mask, shrink=0.0)
    Tq, params = quantile_normal_transform(X, mask)
    muq, Sigq, _, _ = em_gaussian_covariance(Tq, mask, shrink=0.0)
    rows = []
    for k in ks:
        sel = greedy_select_conditional_variance(Sig, k, lam=1e-6)
        U = np.setdiff1d(np.arange(n), sel)
        pred = conditional_gaussian_impute(mu, Sig, sel, Xt[:, sel], np.ones((n_test, k), bool), lam=1e-6)
        meas = float(np.mean((pred[:, U] - Xt[:, U]) ** 2))
        # quantile-transformed predictor evaluated in raw units
        Xq_sel = _forward_columns(params, sel, Xt[:, sel])
        pq = conditional_gaussian_impute(muq, Sigq, sel, Xq_sel, np.ones((n_test, k), bool), lam=1e-6)
        pq = np.clip(inverse_quantile_transform(params, pq), X.min(0), X.max(0))
        meas_q = float(np.mean((pq[:, U] - Xt[:, U]) ** 2))
        rng = np.random.default_rng(seed + k)
        rnd = rng.choice(n, size=k, replace=False)
        rows.append({"k": int(k), "heavy_tail": bool(heavy_tail), "measured_mse_greedy": meas,
                     "measured_mse_greedy_quantile": meas_q,
                     "theory_mse_greedy": theoretical_posterior_error(Sigma_true, sel),
                     "theory_mse_random_subset": theoretical_posterior_error(Sigma_true, rnd),
                     "noise_floor": sigma ** 2})
    return rows


# ---------------------------------------------------------------------------------------------------------
# baselines and uncertainty
# ---------------------------------------------------------------------------------------------------------
def random_subset_baseline(n, k, rng):
    return [int(j) for j in rng.choice(n, size=k, replace=False)]


def bootstrap_ci(values, n_boot=2000, alpha=0.05, seed=0):
    """Mean and percentile-bootstrap (1-alpha) CI; NaNs are dropped."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(n_boot, len(values)))
    means = values[idx].mean(1)
    return float(values.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def paired_wilcoxon(a, b):
    """Two-sided paired Wilcoxon signed-rank p-value on the pairs where both entries are finite."""
    from scipy.stats import wilcoxon
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    if len(a) == 0 or np.allclose(a, b):
        return 1.0
    return float(wilcoxon(a, b).pvalue)


# ---------------------------------------------------------------------------------------------------------
# model-level cross-validation on a real (values, mask) matrix
# ---------------------------------------------------------------------------------------------------------
def _per_model_nrmse(pred, y, tgt, std):
    """nrmse per held-out model (NaN for models without target cells)."""
    se = (((pred - y) / std) ** 2) * tgt
    cnt = tgt.sum(1)
    out = np.full(len(y), np.nan)
    ok = cnt > 0
    out[ok] = np.sqrt(se[ok].sum(1) / cnt[ok])
    return out


def run_ablation_grid(values, mask, k, n_folds=5, n_repeats=2, seed=0, transforms=("z", "q"),
                      selectors=("trace", "wrapper", "random"), stackings=(False, True), clips=(False, True),
                      em_budget=15.0):
    """Repeated K-fold CV over MODELS. For every fold, the representation (transform + EM), selection, tuning and
    stack use training models only; a held-out model reveals only its selected benchmarks (those it has).
    Returns {cell: [per-held-out-model nrmse]} with cell = (transform, selector, stacked, clip) plus the column
    median baseline under ("median",); all lists are aligned across cells (same models, NaN where undefined) so
    that paired tests are valid. The sanity check "stack not worse than the median baseline" is in summarise_grid."""
    values = np.asarray(values, dtype=float)
    mask = np.asarray(mask, dtype=bool)
    m, n = values.shape
    k = int(min(k, n))
    res = {}
    for rep_i in range(n_repeats):
        rng = np.random.default_rng(seed + rep_i)
        for fi, va in enumerate(np.array_split(rng.permutation(m), n_folds)):
            tr = np.setdiff1d(np.arange(m), va)
            sel_rand = random_subset_baseline(n, k, rng)
            cell_seed = seed + 100 * rep_i + fi
            for kind in transforms:
                rp = build_rep(values[tr], mask[tr], kind, em_budget=em_budget)
                folds = _make_folds(len(tr), cell_seed + 1000)
                for selector in selectors:
                    if selector == "trace":
                        sel = greedy_select_conditional_variance(_build_sigma(rp["S_all"], 0.05, None), k,
                                                                 lam=0.05, weights=rp["cover"])
                    elif selector == "wrapper":
                        sel = wrapper_forward_select_cv(rp, k, alpha=0.0, seed=cell_seed)
                    else:
                        sel = sel_rand
                    sel = [int(j) for j in sel]
                    params, _ = _cv_tune(rp, sel, folds, QUICK_SHRINKS, QUICK_RANKS, QUICK_LAMS)
                    model = fit_model(rp, sel, params, cell_seed, with_stack=any(stackings))
                    tgt = mask[va].copy()
                    tgt[:, sel] = False
                    for stacked in stackings:
                        for clip in clips:
                            pred = predict_raw(model, values[va][:, sel], mask[va][:, sel], use_stack=stacked,
                                               clip=clip)
                            e = _per_model_nrmse(pred, values[va], tgt, rp["std"])
                            res.setdefault((kind, selector, stacked, clip), []).extend(e.tolist())
                if kind == transforms[0]:  # median baseline (independent of the transform)
                    med_pred = np.tile(rp["rawmed"], (len(va), 1))
                    tgt = mask[va].copy()
                    tgt[:, sel_rand] = False
                    e = _per_model_nrmse(med_pred, values[va], tgt, rp["std"])
                    res.setdefault(("median",), []).extend(e.tolist())
    return res


def summarise_grid(res, ref_cell=("z", "trace", False, False), seed=0):
    """Mean +- bootstrap CI per cell, paired Wilcoxon vs the random-selection cell with the same other settings and
    vs the cycle-1 configuration, and the median-baseline sanity check."""
    out = []
    ref = res.get(ref_cell)
    med = res.get(("median",))
    for cell, e in res.items():
        if cell == ("median",):
            continue
        mean, lo, hi = bootstrap_ci(e, seed=seed)
        row = {"cell": list(cell), "nrmse_mean": mean, "ci_lo": lo, "ci_hi": hi}
        rnd = res.get((cell[0], "random", cell[2], cell[3]))
        if rnd is not None and cell[1] != "random":
            row["wilcoxon_p_vs_random"] = paired_wilcoxon(e, rnd)
            row["mean_diff_vs_random"] = float(np.nanmean(np.asarray(e) - np.asarray(rnd)))
        if ref is not None and cell != ref_cell:
            row["wilcoxon_p_vs_cycle1"] = paired_wilcoxon(e, ref)
            row["mean_diff_vs_cycle1"] = float(np.nanmean(np.asarray(e) - np.asarray(ref)))
        if med is not None:
            row["worse_than_median_baseline"] = bool(np.nanmean(e) > np.nanmean(med))
        out.append(row)
    if med is not None:
        mean, lo, hi = bootstrap_ci(med, seed=seed)
        out.append({"cell": ["median"], "nrmse_mean": mean, "ci_lo": lo, "ci_hi": hi})
    return out


def run_k_sweep(values, mask, ks=(1, 2, 3, 5, 8, 12, 20), n_folds=5, n_repeats=2, seed=0):
    """Headline cells (cycle-1 vs full method vs random) as a function of the budget k."""
    out = {}
    for k in ks:
        res = {}
        for tf, sel_, stk, clp in (("z", "trace", False, False), ("q", "trace", True, True),
                                   ("q", "wrapper", True, True), ("q", "random", True, True),
                                   ("z", "random", False, False)):
            part = run_ablation_grid(values, mask, k, n_folds, n_repeats, seed, transforms=(tf,),
                                     selectors=(sel_,), stackings=(stk,), clips=(clp,))
            res.update(part)
        out[int(k)] = summarise_grid(res, seed=seed)
    return out


def run_ablation_grid_summary(values, mask, k, **kw):
    return summarise_grid(run_ablation_grid(values, mask, k, **kw))


def _load_npz(path):
    d = np.load(path)
    return d["values"], d["mask"].astype(bool)


def main(argv):
    mode = argv[1] if len(argv) > 1 else "synthetic"
    out_path = None
    if mode == "synthetic":
        out = {"gaussian": synthetic_theory_check(), "student_t3": synthetic_theory_check(heavy_tail=True, dof=3)}
        out_path = argv[2] if len(argv) > 2 else None
    elif mode == "ablation":
        values, mask = _load_npz(argv[2])
        out_path = argv[3] if len(argv) > 3 else None
        k = int(argv[4]) if len(argv) > 4 else 5
        out = {"k": k, "grid": run_ablation_grid_summary(values, mask, k)}
    elif mode == "ksweep":
        values, mask = _load_npz(argv[2])
        out_path = argv[3] if len(argv) > 3 else None
        out = run_k_sweep(values, mask)
    else:
        raise SystemExit("unknown mode")
    text = json.dumps(out, indent=2)
    if out_path:
        with open(out_path, "w") as fh:
            fh.write(text)
    else:
        print(text)


if __name__ == "__main__":
    main(sys.argv)
