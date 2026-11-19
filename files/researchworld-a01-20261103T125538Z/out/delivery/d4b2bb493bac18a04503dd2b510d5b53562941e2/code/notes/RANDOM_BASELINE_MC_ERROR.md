# Monte Carlo precision of HELM random-order mean costs

This is the analysis response to internal-review-repo's request **experiment-repo#4**, routed from **external-review-repo#4**. It supplements the original random baseline with precision for its four reported average costs. The previous Wilson intervals describe success-at-optimum probabilities and do not answer this question.

## Estimand and method

Fix all M=79 HELM entries and all57 subjects. For rule r and entry i, let K_irj be the stopping task count for random permutation j under the original perfect-score/tied-first intervention. The estimand is theta_r=(1/M) sum_i E_order[K_irj]. The estimate averages the R=2,000 simulated stopping costs within each target, then averages those target means. Already-winning targets remain in the average with zero stopping cost and zero variance.

The RNG (NumPy default_rng seed519733) generates separate permutation arrays for successive targets. Rules within a target share the same permutations. Using the sample variance s_ir^2 with denominator R-1, the marginal estimator variance is Vhat_r=sum_i(s_ir^2/R)/M^2. We report SE_r=sqrt(Vhat_r) and the **approximate marginal normal95% interval** theta_hat_r +/-1.959964 SE_r. The independent randomization is over permutations within fixed targets; related model families do not invalidate this calculation because there is no model-population sampling claim. Intervals are Monte Carlo precision of this fixed-census estimand, not accuracy, future-task, training-cost or between-rule-difference uncertainty. Rules share draws, so a difference interval would require their covariance; none is reported. Four marginal intervals do not provide simultaneous95% coverage.

## Executed results

| Rule | Original/regenerated average K | MC SE | Approximate marginal95% interval |
|---|---:|---:|---:|
| Mean |27.2314113924|0.0051691294|[27.2212800850,27.2415426999]|
| Median |21.8963101266|0.0037437173|[21.8889725756,21.9036476776]|
| Geometric |29.9356392405|0.0063159223|[29.9232602604,29.9480182207]|
| Borda |47.8901012658|0.0034245061|[47.8833893572,47.8968131744]|

These values come from `results/random_mean_mc_summary_helm.csv`. Full variance records for all316 entry/rule combinations are in `random_mean_mc_targets_helm.csv`. The regenerated run compared every original baseline column (numeric atol1e-12) and did not rewrite `random_baseline_helm.csv`; that file remains byte identical. Original versus regenerated per-target mean differences are exactly zero after CSV parsing. The original manuscript's rounded means therefore stay the same; their simulation precision should now be stated. The largest interval half-width is about0.0124 tasks, far below the observed optimal-versus-random gaps; exact optima have no Monte Carlo error. Open LLM uses exact subset expectations and receives no Monte Carlo interval.

An independent analytic check uses median stopping as the r-th order statistic of B eligible subject positions among T=57: E K=r(T+1)/(B+1), Var K=r(B-r+1)(T+1)(T-B)/[(B+1)^2(B+2)]. Leaders have r=0. This gives exact across-target expected median cost21.9001183724 and exact MC SE0.0037614102 at R=2,000, close to the estimated0.0037437173. The observed simulation error is-0.0038082458, about one SE, and the reported interval contains the exact expectation. This is a check of the Monte Carlo moments, not a replacement of the original seeded baseline.

## Reproduction and provenance

From the analysis root (or `cd code` in the integrated delivery):

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
python3 src/random_baseline.py --board helm --repeats 2000 --mc-error-only
python3 src/validate_mc_precision.py
python3 -m unittest discover -s tests -v
```

The first command regenerates the original samples and fails if any original baseline column differs, writing only the two new precision sidecars. The ordinary full-reproduction HELM random-baseline command now also emits these sidecars. The validator checks their moments, aggregate formula, original baseline checksum, target alignment and independent analytic median calculation. It retains provenance hashes in `random_mean_mc_validation.json`. `random_mean_mc_run.json` records successful resource job job-d0d64cbec1 and its output; measured inner runtime1.24s (resource startup excluded). The original1.04s run measurement remains original evidence. The existing timed run sized this identical2,000-draw repeat; no broad optimization run was repeated. The optimizer tests and new known-moment tests all pass (five test methods,2.474s in this execution).

Paper and figure owners should add the marginal intervals or SEs to the HELM random-average display/caption and give the estimator and limits in methods/appendix. Preserve the original numerical source and its manifest; add the new source with provenance. This note supplies analysis, not final manuscript text or a publication figure. The report owner must convey revised content itself to outside review, which cannot read paper code. The original deterministic ceiling-reversal and minimum-cost results are unchanged.
