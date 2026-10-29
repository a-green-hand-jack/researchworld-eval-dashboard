"""
jNMF importance factors (NumPy only).

Dataset: /benchmark/datasets/jnmf_visualization/fit_result_conscientiousness_{W_high,W_low,H_high,H_low}.npy
W matrices are [p, K], H matrices are [n, K].

Conditions (plan names preserved):
  - raw_spec_hbased_importance_scores        (baseline: literal spec formulas)
  - unit_norm_canonical_gauge_hbased_scores  (baseline: unit-norm W columns, H rescaled)
  - threshold_zeroed_hbased_scores           (ablation: zero |x| < tau, tau in grid)
  - rescaled_component_stress_test           (ablation: per-component rescaling preserving W·H)
  - gauge_invariant_energy_share_scores      (proposed method)

Seeds: [0, 1, 2]. Only the rescaling stress test uses randomness; other
conditions are deterministic and give identical values across seeds.

primary_metric (per condition, per seed) = mean of the six factor values.
"""

import json
import math
import os

import numpy as np

SEEDS = [0, 1, 2]

HYPERPARAMETERS = {
    "data_dir": "/benchmark/datasets/jnmf_visualization/",
    "file_prefix": "fit_result_conscientiousness",
    "K_expected": 2,
    "tau_grid": [1.0e-12, 1.0e-9, 1.0e-6],
    "rescale_log_sigma": 1.0,
    "top_k_rows": 5,
    "eps": 1.0e-30,
    "unit_check_atol": 1.0e-9,
}

OUT_DIR = "/workspace/pred_results/"
PRIMARY_OUT = os.path.join(OUT_DIR, "jnmf_h_importances.json")
DIAG_OUT = os.path.join(OUT_DIR, "jnmf_h_diagnostics.json")

FACTOR_NAMES = [
    "common_error",
    "common_importance",
    "high_importance",
    "low_importance",
    "distinct_error",
    "distinct_importance",
]


def load_factors():
    """Load and validate the four factor matrices."""
    mats = {}
    for name in ["W_high", "W_low", "H_high", "H_low"]:
        path = os.path.join(
            HYPERPARAMETERS["data_dir"],
            f"{HYPERPARAMETERS['file_prefix']}_{name}.npy",
        )
        arr = np.load(path, allow_pickle=False).astype(np.float64)
        if arr.ndim != 2 or arr.shape[1] != HYPERPARAMETERS["K_expected"]:
            raise ValueError(f"{name} has unexpected shape {arr.shape}")
        if not np.all(np.isfinite(arr)):
            raise ValueError(f"{name} contains NaN/Inf")
        mats[name] = arr.copy()
    if mats["W_high"].shape != mats["W_low"].shape:
        raise ValueError("W_high and W_low shapes differ")
    if mats["H_high"].shape[1] != mats["H_low"].shape[1]:
        raise ValueError("H_high and H_low component counts differ")
    return mats


def raw_factors(W_high, W_low, H_high, H_low):
    """Literal implementation of the six formulas from the user request."""
    eps = HYPERPARAMETERS["eps"]
    total_all = H_high.sum() + H_low.sum()
    total_high = H_high.sum()
    total_low = H_low.sum()
    return {
        "common_error": 1.0 - float(np.dot(W_high[:, 0], W_low[:, 0])),
        "common_importance": float((H_high[:, 0].sum() + H_low[:, 0].sum())
                                   / max(total_all, eps)),
        "high_importance": float(H_high[:, 1].sum() / max(total_high, eps)),
        "low_importance": float(H_low[:, 1].sum() / max(total_low, eps)),
        "distinct_error": float(np.dot(W_high[:, 1], W_low[:, 1])),
        "distinct_importance": float((H_high[:, 1].sum() + H_low[:, 1].sum())
                                     / max(total_all, eps)),
    }


def canonical_gauge(W, H):
    """Unit-norm W columns; absorb the norms into H so W·H is preserved."""
    eps = HYPERPARAMETERS["eps"]
    norms = np.maximum(np.linalg.norm(W, axis=0), eps)
    return W / norms, H * norms


def unit_norm_scores(W_high, W_low, H_high, H_low):
    Wh, Hh = canonical_gauge(W_high, H_high)
    Wl, Hl = canonical_gauge(W_low, H_low)
    return raw_factors(Wh, Wl, Hh, Hl)


def threshold_zeroed(mats, tau):
    out = {}
    for k, v in mats.items():
        w = v.copy()
        w[np.abs(w) < tau] = 0.0
        out[k] = w
    return out


def rescale_components(mats, rng):
    """Independent per-component rescaling per model; W·H is preserved exactly."""
    sigma = HYPERPARAMETERS["rescale_log_sigma"]
    K = HYPERPARAMETERS["K_expected"]
    c_high = np.exp(sigma * rng.standard_normal(K))
    c_low = np.exp(sigma * rng.standard_normal(K))
    return {
        "W_high": mats["W_high"] * c_high,
        "H_high": mats["H_high"] / c_high,
        "W_low": mats["W_low"] * c_low,
        "H_low": mats["H_low"] / c_low,
    }


def top_k_mass_fraction(H, k):
    row_mass = H.sum(axis=1)
    total = row_mass.sum()
    if total <= HYPERPARAMETERS["eps"]:
        return 0.0
    top = np.sort(row_mass)[::-1][:k]
    return float(top.sum() / total)


def energy_share_scores(W_high, W_low, H_high, H_low):
    """Gauge-invariant analogues: e_k = ||w_k|| * ||h_k||_1 normalized per model."""
    eps = HYPERPARAMETERS["eps"]

    def shares(W, H):
        e = np.linalg.norm(W, axis=0) * np.abs(H).sum(axis=0)
        return e / max(e.sum(), eps)

    sh = shares(W_high, H_high)
    sl = shares(W_low, H_low)

    def cos(a, b):
        return float(np.dot(a, b) / max(np.linalg.norm(a) * np.linalg.norm(b), eps))

    return {
        "common_error": float(1.0 - cos(W_high[:, 0], W_low[:, 0])),
        "common_importance": float((sh[0] + sl[0]) / 2.0),
        "high_importance": float(sh[1]),
        "low_importance": float(sl[1]),
        "distinct_error": float(cos(W_high[:, 1], W_low[:, 1])),
        "distinct_importance": float((sh[1] + sl[1]) / 2.0),
    }


def mean_of(scores):
    return float(np.mean([scores[k] for k in FACTOR_NAMES]))


def unit_checks(scores):
    atol = HYPERPARAMETERS["unit_check_atol"]
    s26 = scores["common_importance"] + scores["distinct_importance"]
    ok_sum = abs(s26 - 1.0) <= atol
    ok_range = all(-atol <= scores[k] <= 1.0 + atol
                   for k in ["high_importance", "low_importance"])
    print(f"UNIT_CHECK: f2+f6 = {s26:.12f} pass={ok_sum}")
    print(f"UNIT_CHECK: f3,f4 in [0,1] pass={ok_range}")
    return ok_sum and ok_range


def report(condition, per_seed_scores):
    """Print per-seed and aggregated primary_metric lines."""
    vals = []
    for s, sc in per_seed_scores:
        v = mean_of(sc)
        vals.append(v)
        print(f"condition={condition} seed={s} primary_metric: {v:.10f}")
    arr = np.array(vals)
    print(f"condition={condition} primary_metric_mean: {arr.mean():.10f} "
          f"primary_metric_std: {arr.std():.3e}")
    return {"per_seed_primary_metric": vals,
            "mean": float(arr.mean()), "std": float(arr.std())}


def main():
    mats = load_factors()
    W_high, W_low = mats["W_high"], mats["W_low"]
    H_high, H_low = mats["H_high"], mats["H_low"]
    print(f"Loaded W: {W_high.shape}, H_high: {H_high.shape}, H_low: {H_low.shape}")
    diag = {"seeds": SEEDS, "conditions": {}}

    # Baseline 1: raw spec H-based scores (primary deliverable)
    raw = raw_factors(W_high, W_low, H_high, H_low)
    for name in FACTOR_NAMES:
        print(f"primary_metric {name}: {raw[name]:.10f}")
    unit_ok = unit_checks(raw)
    diag["conditions"]["raw_spec_hbased_importance_scores"] = {
        "scores": raw,
        **report("raw_spec_hbased_importance_scores",
                 [(s, raw) for s in SEEDS]),
    }

    # Baseline 2: unit-norm canonical gauge
    canon = unit_norm_scores(W_high, W_low, H_high, H_low)
    diag["conditions"]["unit_norm_canonical_gauge_hbased_scores"] = {
        "scores": canon,
        **report("unit_norm_canonical_gauge_hbased_scores",
                 [(s, canon) for s in SEEDS]),
    }

    # Ablation: threshold-zeroed scores
    thr = {}
    thr_per_seed = []
    for tau in HYPERPARAMETERS["tau_grid"]:
        z = threshold_zeroed(mats, tau)
        s_tau = raw_factors(z["W_high"], z["W_low"], z["H_high"], z["H_low"])
        rel = {k: float(abs(s_tau[k] - raw[k]) / max(abs(raw[k]), HYPERPARAMETERS["eps"]))
               for k in FACTOR_NAMES}
        n_zeroed = {k: int(np.sum(np.abs(mats[k]) < tau)) for k in mats}
        thr[f"{tau:.0e}"] = {
            "scores": s_tau,
            "relative_change": rel,
            "max_relative_change": max(rel.values()),
            "n_zeroed": n_zeroed,
        }
        print(f"condition=threshold_{tau:.0e} max_relative_change: {max(rel.values()):.3e}")
        thr_per_seed.append(s_tau)
    diag["conditions"]["threshold_zeroed_hbased_scores"] = {
        "by_tau": thr,
        **report("threshold_zeroed_hbased_scores",
                 [(s, thr_per_seed[-1]) for s in SEEDS]),
    }

    # Ablation: rescaled component stress test (per seed)
    stress = []
    stress_per_seed = []
    for s in SEEDS:
        rng = np.random.default_rng(s)
        r = rescale_components(mats, rng)
        raw_r = raw_factors(r["W_high"], r["W_low"], r["H_high"], r["H_low"])
        en_r = energy_share_scores(r["W_high"], r["W_low"], r["H_high"], r["H_low"])
        en_0 = energy_share_scores(W_high, W_low, H_high, H_low)
        raw_rel = max(abs(raw_r[k] - raw[k]) / max(abs(raw[k]), HYPERPARAMETERS["eps"])
                      for k in FACTOR_NAMES)
        en_rel = max(abs(en_r[k] - en_0[k]) / max(abs(en_0[k]), HYPERPARAMETERS["eps"])
                     for k in FACTOR_NAMES)
        print(f"condition=rescaled_component_stress_test seed={s} "
              f"raw_max_rel_change: {raw_rel:.3e} energy_max_rel_change: {en_rel:.3e}")
        stress.append({"seed": s, "raw_max_rel_change": raw_rel,
                       "energy_max_rel_change": en_rel, "raw_scores": raw_r,
                       "energy_scores": en_r})
        stress_per_seed.append((s, raw_r))
    diag["conditions"]["rescaled_component_stress_test"] = {
        "per_seed": stress,
        **report("rescaled_component_stress_test", stress_per_seed),
    }

    # Proposed method: gauge-invariant energy shares
    energy = energy_share_scores(W_high, W_low, H_high, H_low)
    diag["conditions"]["gauge_invariant_energy_share_scores"] = {
        "scores": energy,
        **report("gauge_invariant_energy_share_scores",
                 [(s, energy) for s in SEEDS]),
    }

    # Concentration diagnostics
    top_k = HYPERPARAMETERS["top_k_rows"]
    conc = {
        "H_high_top_k_mass": top_k_mass_fraction(H_high, top_k),
        "H_low_top_k_mass": top_k_mass_fraction(H_low, top_k),
    }
    diag["concentration"] = conc
    for k, v in conc.items():
        flag = "EXCEEDS_50pct" if v > 0.5 else "below_50pct"
        print(f"primary_metric {k}: {v:.4f} ({flag})")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(PRIMARY_OUT, "w") as f:
        json.dump({k: float(raw[k]) for k in FACTOR_NAMES}, f, indent=2)
    print(f"Saved primary scores to {PRIMARY_OUT}")

    diag["unit_checks_pass"] = bool(unit_ok)
    with open(DIAG_OUT, "w") as f:
        json.dump(diag, f, indent=2)
    print(f"Saved diagnostics to {DIAG_OUT}")
    print("SUMMARY: " + ", ".join(f"{k}={raw[k]:.6f}" for k in FACTOR_NAMES))


if __name__ == "__main__":
    main()