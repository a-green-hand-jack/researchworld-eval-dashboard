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
