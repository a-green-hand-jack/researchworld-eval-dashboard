# program_1 notes

## What was implemented
- Baseline-equivalent skeleton (8 folds over complement pairs, jackknife, simulated top-3 Jaccard).
- Variance reduction: 1000 draws as 500 antithetic pairs, common random numbers per episode (seeded by reset seed).
- `_jackknife_cov` gives centred, scaled delete-one-group deviations; full-covariance draws are `phi + mult * z @ dev` (sum(phi) constraint preserved since each replicate satisfies it).
- `_sim_jaccard(phi, dev, mult, k, ...)` exposes the spread multiplier and diag/full-cov choice.
- `_calibrate` maps features (sim Jaccard diag@1, diag@0.7, full@1, full@sqrt2, log2(B/d), tanh(margin z/3), family) with `_CALIB_COEF`, then final r = 0.7*calibrated + 0.3*diag@1, clipped to [0.02, 1].
- Any per-instance exception or non-finite value falls back to 0.9.

## IMPORTANT limitation: calibration constants are NOT fitted
This candidate was authored under a rule set forbidding executing any code (no Python, no local replica,
no CV). The planned local replica (sklearn datasets, logreg/RF/MLP, B in {4d,16d}, 32 background rows,
8 reruns, leave-one-dataset-out CV) was therefore NOT run. No held-out-CV MSE exists; none is claimed.
`_CALIB_COEF` values are hand-set conservative priors: weights 0.5/0.2/0.3 on diag@1, diag@0.7, full@1
(sum 1.0, so the map is a convex combination of simulators), zero weight on the sqrt(2)-inflated simulator,
B/d, margin and family terms. Rationale: cycle-1 (inflation sqrt2 + full cov + 48 groups) scored below
baseline and labels skew high, so mild deflation / no inflation is the direction suggested; this is a
hypothesis, not a result. Expected behaviour is close to the baseline with lower MC noise; the
ablation (variance-only vs +cov vs +inflation vs +calibration) remains to be done by running the
replica harness described in the idea plan.

---
# Cycle 3 (program_1): budget-aware empirical-Bayes shrinkage + partition-ensembled jackknife
Attempt `c03_budget_prior_partition_ensemble_attempt_01`.

## Changes vs cycle 2 (program_0)
1. `_N_PARTITIONS = 4`: the delete-one-group jackknife is repeated over 4 independent random fold
   partitions (`rng.permutation(pairs) % _FOLDS`, drawn from the reset-seeded generator); simulated
   Jaccards (diag@1.0, diag@0.7, full-cov@1.0) and the margin z are averaged with `np.mean(sims, axis=0)`.
   CRN/antithetic draws unchanged. Partitions with <2 valid folds are skipped; if none is valid -> prior.
2. `_PRIOR_BY_RATIO = {2.0: 0.84, 4.0: 0.96}` keyed on log2(B/d), `_prior_for(B, d)` interpolates linearly, clips outside.
3. `_empirical_bayes`: r = `_W_SIM`(0.6) * sim_combo + (1-`_W_SIM`) * prior, sim_combo = 0.5 s_d10 + 0.2 s_d07 + 0.3 s_f10
   (the cycle-2 convex combination, so `_calibrate`/`_SHRINK` are no longer used in the output path).
4. Soft margin gate: + `_MARGIN_BOOST`(0.02) * tanh(margin_z / `_MARGIN_SCALE`(3)); clip to [0.02, 1].
5. Fallback on exception / non-finite -> budget prior (not constant 0.9; 0.9 only if B/d itself is unusable).

## Provenance of constants (honest statement)
- Prior values 0.84 / 0.96: aggregate label means by budget seen in earlier evaluation metrics (not instance labels,
  not fitted by this code). `_W_SIM`, `_MARGIN_BOOST`, `_MARGIN_SCALE`, `_N_PARTITIONS`: hand-set, untuned.
- No code was executed while writing this candidate (rules forbade it): no sanity run, no CV, no tuning. Correctness
  of shapes/finiteness is by inspection only. Runtime estimate: 4 partitions x 9 lstsq solves + 3 sims per instance.
- Planned ablation order if runs become possible: partition ensemble only, prior only, margin gate only; tune `_W_SIM` in {0.5, 0.6, 0.8}.
- Risk: the prior encodes the budget-wise label mean from the search datasets; if held-out label means differ, the shrinkage may hurt.
