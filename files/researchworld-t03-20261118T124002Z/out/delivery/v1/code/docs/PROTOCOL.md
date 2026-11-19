# Protocol (analysis role) — fixed before the E1–E5 results were looked at

Status: written 2026-11-18 after the E0 pilots and the cost measurements, before any E1/E2/E5 result. Changes after this point are
listed in "Amendments" at the bottom with the reason; nothing is silently edited.

## 1. Objects
- **Run** φ̂ = E(f, x, D, B, ξ). f = trained model, explained on the probability scale P(y=1|x) (GBDT also on the raw margin for the d-curve);
  x = one test instance; D = background set of m = 30 training rows (fixed per dataset/split; same D for estimator and target);
  explainer E; seed ξ. **Players = original attributes** (a one-hot block is masked together). Only attributes that differ between x and
  at least one background row are players (as in shap); the others get φ = 0 exactly.
- **Budget** = number of coalitions evaluated (each = m masked-input model evaluations); wall-clock is recorded separately.
  Grid: ×{¼, ½, 1, 2, 4, 16} of shap's KernelExplainer default 2d + 2048 coalitions; PermutationExplainer is additionally run at its own
  shipped default (max_evals = 500).
- **Target** φ\* = exact interventional Shapley value of the same (f, x, D) by enumeration of the 2^d-coalition value table (d ≤ 20).
- **Read-outs**: top-k set by |φ| (k = 1, 3, 5); ε-tolerant top-k (ε = 0.1 main; 0, 0.25 sensitivity: the weakest chosen member is within ε·|φ\*|_(k) of the strongest excluded one);
  sign agreement on the true top-k; rank-biased overlap (p = 0.9); relative L2; reason-code read-out (signed top-k) as a robustness arm.
- **r_k(x; B)** = P_ξ[top-k(φ̂) = top-k(φ\*)] (accuracy), estimated from R reruns. **Repeatability** = pairwise agreement among reruns (Nogueira stability, mean pairwise Jaccard, RBO), no φ\* needed.
- An instance is **reliable at (k, δ)** if r_k(x; B) ≥ 1 − δ. Headline: **fraction of reliable instances** F_k(δ), δ ∈ {0.05, 0.1}, k ∈ {1,3,5}.

## 2. Sizes and seeds
n = 100 test instances per cell (fixed random subset of the held-out 30 % / 20 %); 3 model seeds (LR is deterministic: its seeds differ only in nothing
but are kept for a common layout; MLP init, GBDT bagging differ); R = 20 reruns per (instance, arm, budget) for pooled statements;
R ≈ 200 reruns on ~30 stratified instances per cell at ×¼, ×1, ×4 for the per-instance statements (Clopper–Pearson at 20/20 is [0.83, 1]).
Every random draw is seeded from crc32 of (cell, instance, arm, budget, rerun). ≥ 10 retrains / ≥ 10 background resamples for E4 on a subset.

## 3. Statistics
Instance is the unit. CIs: cluster bootstrap (2000 resamples) over instances, with model seeds as a second cluster level (resample seeds, then instances within);
Clopper–Pearson for per-instance proportions; paired per-instance differences for explainer comparisons (Wilcoxon signed-rank, Holm over the pre-stated comparisons only).
No p-value is reported for an exploratory description.

## 4. Verdict rules (per claim, per cell; "supported / not supported / depends")
- **C1 hidden tail.** Four outcomes per cell, decided in this order. (a) *Unreliable at the default*: mean r_3 < 0.90 at the shipped default (the average run is already not a safe basis; the tail question is moot). (b) *Supported* if mean r_3 ≥ 0.90 at the shipped default **and** the unreliable share U_3(δ=0.1) = 1 − F_3(0.1) ≥ 0.05 with the bootstrap CI lower bound > 0.
  (c) *Not supported* if mean r_3 ≥ 0.90 and U_3(0.1) < 0.05 (then "single runs are fine at the default in this cell" is the finding). (d) *Inconclusive* if mean r_3 ≥ 0.90, U_3(0.1) ≥ 0.05 but the bootstrap lower bound is ≤ 0. The tail is "predicted by z" if the Spearman correlation between r_3 and the true z = gap/SE_gap is ≥ 0.5 **and**
  the plug-in z from the single run separates reliable from unreliable instances with AUC ≥ 0.7 (reported with the plug-in's miscalibration, i.e. P(correct | plug-in z bin) against Φ(z)).
  Across cells: "supported" if supported in ≥ 2/3 of the cells of the main grid, "depends" otherwise with the factor (d, model, explainer) stated.
- **C2 budget law (non-trivial part).** B\*(x) = smallest grid budget with r_k ≥ 1 − δ (right-censored at ×16). Reported: spread (IQR / range of log2 B\*), Spearman between B\*_pred = c·σ²/gap² (c fitted once per cell on the ×1 run) and B\*_emp, the bias floor (budget at which r_k stops increasing).
  Supported if the spread covers ≥ 2 grid octaves (IQR in log2 ≥ 2) **and** Spearman ≥ 0.5.
- **C3 yardstick.** Per instance, d_rerun (mean pairwise rerun disagreement at the default) vs d_bg (disagreement of φ\* across background resamples) vs d_retrain (disagreement of φ\* across retrains with equal accuracy: |ΔAUC| ≤ 0.01, seed-only retraining primary, bootstrap-of-training-set secondary).
  Disagreement = 1 − top-3 Jaccard. Report the per-instance paired difference distribution and the share of instances where d_rerun < d_retrain. "Estimator noise below accepted variation" supported if that share ≥ 0.75 with CI lower bound ≥ 0.6.
- **C4 certificate calibration.** For rule ρ and level δ, the calibrated quantity is P(top-k of the delivered run is correct | certified by ρ), pooled over instances with cluster bootstrap CIs, on independent reruns, **under the stopping rule**
  (first certified stage of the 7-stage doubling schedule ¼…×16; if never certified, the run is "uncertified" and excluded from the conditional, its cost is the maximum).
  Calibrated if the CI of the conditional correct rate contains or exceeds 1 − δ for δ ∈ {0.2, 0.1, 0.05, 0.01}; miscalibrated if the point estimate is below 1 − δ by more than 0.02 with the CI upper bound below 1 − δ.
  Cost claim: adaptive (certified, calibrated rule) beats a fixed budget if, at equal *pooled* correct rate, its mean coalitions are lower than the cheapest grid budget achieving that rate.
- **C5 default decomposition.** For d ≥ 11: share of top-k disagreement of the shipped default with φ\* due to truncation (bias): instances whose *expected* default attribution already has a wrong top-k, versus instances whose error is sampling noise only (kshap_l1off right in expectation). Supported if the bias share ≥ 0.2 of unreliable instances.

## 5. What is not claimed
No result of this study is taken from a paper; baselines are re-implemented from published descriptions (shap 0.51.0 is the live reference; Covert & Lee, Kariyappa et al., Musco & Witter from the papers).
Interventional (marginal) Shapley values only; tabular; LR/MLP/GBDT (RF Tier 2); d ≤ 20 enumerated, d > 20 only for GBDT on the margin scale.

## Amendments
- 2026-11-18 (before any E1 result): C1 outcome (a) 'unreliable at the default' and (d) 'inconclusive' added at story-repo's request (experiment-repo#3).
- 2026-11-18 (before any E4 result): LR is deterministic given the data, so seed-only retraining is vacuous for LR; E4 uses bootstrap-of-training-set retraining as the retrain arm for LR (and reports both for MLP/GBDT).
