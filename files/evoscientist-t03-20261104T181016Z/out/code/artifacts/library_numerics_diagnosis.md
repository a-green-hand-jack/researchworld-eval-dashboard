# Official KernelExplainer low-budget numerical diagnosis

## Scope and reproducibility

Diagnostic only: **no experimental design, reported library output, main result, or estimator source was changed**. No network, web, literature, or topic discovery was used. Read the request, adapter, runner, estimator, existing CSV/NPZ records, and installed SHAP source only. Followed experiment-craft's five-step diagnostic. Huge means the existing normalized L1 error `> 1e+06`; thresholds from 100 through 1e12 select the same four rows. Error is `sum(abs(phi-reference))/max(sum(abs(reference)),0.02)`, not absolute attribution magnitude.

Exact command (single-thread CPU; no arguments or inputs to tune):

```sh
python /work/diagnose_library.py
```

Environment: Python 3.11.15; SHAP 0.49.1; NumPy 2.4.6; SciPy 1.17.1; scikit-learn 1.7.2. The helper asserts bitwise stored-output reproduction for all four huge cases and the two stored controls, warning equality, cache/reference identities, and unchanged protected-file SHA256 hashes. Full precision arrays, singular values, weights, warnings, source excerpts, and hashes are in `artifacts/library_numerics_diagnosis.json`. Local source: `/opt/research/lib/python3.11/site-packages/shap/explainers/_kernel.py`, SHA256 `206aac3fcd71e455f49c9509a247ad71603eb77b4c9fdac7dc1624b86b268a62`. Results can depend on numerical-library/platform rounding; exact reproduction assertions intentionally fail on drift instead of silently replacing a run.

## 1. Collect actual failure cases

All 1728 CSV rows were checked against corresponding original NPZ JSON records (same ordered run keys, errors and warning lists). No rows were discarded. Only four pass the descriptive huge threshold; all four were separately reproduced without saving over any result.

| mode | p | n | huge | warning_records | warning_events | singular_records | degenerate_records | max_error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| default | 1 | 432 | 0 | 59 | 218 | 0 | 59 | 1.4996843721023982 |
| default | 16 | 432 | 0 | 0 | 0 | 0 | 0 | 0.2921789960411866 |
| no_l1 | 1 | 432 | 4 | 116 | 116 | 116 | 0 | 4806173543960378.0 |
| no_l1 | 16 | 432 | 0 | 0 | 0 | 0 | 0 | 0.0829584981894582 |

Warning-record counts count runs with >=1 warning; event counts include repeated warnings. Singular and degenerate categories are text classifications of the stored warning messages, not inferred failures. **All four huge-error records have no warnings.** No inference that absence of a warning means a well-conditioned solve.

Dataset breakdown (all raw records, not just reproduced cases):

| dataset | mode | p | n | huge | warning_records | warning_events |
| --- | --- | --- | --- | --- | --- | --- |
| acs | default | 1 | 192 | 0 | 29 | 107 |
| acs | default | 16 | 192 | 0 | 0 | 0 |
| acs | no_l1 | 1 | 192 | 2 | 50 | 50 |
| acs | no_l1 | 16 | 192 | 0 | 0 | 0 |
| german | default | 1 | 48 | 0 | 0 | 0 |
| german | default | 16 | 48 | 0 | 0 | 0 |
| german | no_l1 | 1 | 48 | 0 | 3 | 3 |
| german | no_l1 | 16 | 48 | 0 | 0 | 0 |
| pima | default | 1 | 192 | 0 | 30 | 111 |
| pima | default | 16 | 192 | 0 | 0 | 0 |
| pima | no_l1 | 1 | 192 | 2 | 63 | 63 |
| pima | no_l1 | 16 | 192 | 0 | 0 | 0 |

First huge run in existing CSV order: `/work/results/library/acs_hgb_11_00.npz`, attributions index 28; ACS/HGB seed 11, slot 0, P=1, no_l1, repeat 12. The seed is produced exactly by `int(rng_for('acs','hgb',11,0,5,True,1,12).integers(0,2**31-1)) = 2039799453`. It requests 18 interior samples for 10 players; the analogous Pima cases request 14 for 8 players.

## 2. Find a working version (diagnostic controls only)

The original default and P=16 runs for the first point/repeat reproduce bitwise. A same-seed default control also runs on **identical masks, weights and finite-game values** to the failing no_l1 case; only `l1_reg` changes. It selects `[2 7 8 1 0 9 3 5 4]` and yields rank 8/8. The two stored modes use different `rng_for` method streams, so their reported errors are not treated as a paired seed comparison. Default `num_features(10)` is feature selection, not necessarily shrinkage; it may select fewer than ten features on a degenerate design.

| case | mode | P | seed | rank | cond_normal | library_error | same_design_SVD_error | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| acs/hgb/s0/r12 | no_l1 | 1 | 2039799453 | 8/9 | 1.20486569e+17 | 4.80617354e+15 | 0.0851068172 | 0 |
| acs/lr/s0/r2 | no_l1 | 1 | 1872149042 | 8/9 | 9.106672e+16 | 2.16261787e+14 | 0.464663077 | 0 |
| pima/hgb/s1/r2 | no_l1 | 1 | 297207827 | 6/7 | 6.82105125e+16 | 1.77820867e+15 | 0.212949745 | 0 |
| pima/lr/s0/r11 | no_l1 | 1 | 1929548066 | 6/7 | 1.5305872e+17 | 1.43045354e+13 | 0.218954752 | 0 |
| acs/hgb/s0/r12 matched seed | default | 1 | 2039799453 | 8/8 | 14.4748951 | 0.101274527 | 0.0851068172 | 0 |
| acs/hgb/s0/r12 | default | 1 | 93751344 | 8/8 | 191.469779 | 0.441947031 | 0.420378048 | 0 |
| acs/hgb/s0/r12 | no_l1 | 16 | 1440179476 | 9/9 | 13.077504 | 0.0128941583 | 0.0128941583 | 0 |

SVD columns are **new diagnosis-only reconstructions**, not corrected reported library outputs. They remain nonzero-error estimates, and rank deficiency still entails non-identifiability.

## 3. Bridge the gap: verify the adapter and expose the actual system

For every reproduced case, assertions confirmed:
- Inputs to the adapter are finite, exactly binary, shape `(n,d)`, with a lossless integer-mask round trip. All `d` players vary; one zero background row and the all-one query are the intended finite-game adapter, not raw model-feature inputs.
- Library and main caches contain the entire game (`2**d` sorted masks), with **bitwise equal cache values**. The adapter's outputs and SHAP's `ey` equal the cached values exactly. No uncached model rows are evaluated during the explanation.
- Independent evaluation of the actual frozen model on all finite-game masks differs from the cache by at most 0. Exact Shapley references recomputed by exhaustive marginal sums equal the stored references; full weighted constrained-kernel references agree to 1e-12.
- For the first case, `v(empty)=0.41236457849308472`, `v(full)=0.34641353343379316`, delta=-0.065951045059291558; the entire game's value range is [0.165054215, 0.720506528]. Both endpoint/library/cache comparisons are exact.

First case actual design: 18 unique interior rows; 20 adapter rows including two endpoints. Selected indices (zero-based) `[0 1 2 3 4 5 6 7 8 9]`; eliminated feature index **9**. These indices were captured from the original installed `solve` frame at return using Python profiling, without changing solver arithmetic. No warnings: `[]`. **Identical sampled column pair: `[(4, 6)]`.** Thus features 4 and 6 cannot be distinguished by these samples: their contrast is an exact null direction compatible with the efficiency constraint. The huge output assigns them approximately +1.377e15 and -1.377e15. The same-seed default removes feature 6 and its selected normal system has condition estimate 14.4748951.

Let `Z` be the actual library mask matrix and `w` its actual kernel weights. SHAP eliminates the final selected feature `j`, using `X = Z[:,selected[:-1]] - Z[:,j,None]`, `y = v - v0 - Z[:,j]*delta`, and solves `(X.T @ W @ X) beta = (W*X).T @ y`.

- `sqrt(W) X`: shape [18, 9]; numerical rank 8; **exact rational rank of integer X = 8 < 9**; floating condition estimate 2.41578432e+16 (mathematically singular). Its singular values are `[1.200045386e+00 6.159196883e-01 5.606436342e-01 4.714045208e-01 3.660510846e-01 2.714447537e-01 2.551222882e-01 1.946641641e-01 4.967518734e-17]`.
- `X.T W X`: numerical rank 8; floating condition estimate 1.20486569e+17. Singular-design condition estimates are finite floating approximations, not evidence of invertibility.
- Weights: all positive/finite; sum 0.99999999999999989; min 0.055555555555555546; max 0.055555555555555546. Rows and values below are the **library** samples, not the main estimator's distinct random design. Binary strings list features 0..d-1 left to right (little-endian integer encoding).

| mask | binary | weight | value |
| --- | --- | --- | --- |
| 128 | 0000000100 | 0.0555555556 | 0.537430685 |
| 895 | 1111111011 | 0.0555555556 | 0.284541017 |
| 512 | 0000000001 | 0.0555555556 | 0.425530965 |
| 511 | 1111111110 | 0.0555555556 | 0.309796973 |
| 1 | 1000000000 | 0.0555555556 | 0.478261089 |
| 1022 | 0111111111 | 0.0555555556 | 0.283921204 |
| 416 | 0000010110 | 0.0555555556 | 0.53568223 |
| 607 | 1111101001 | 0.0555555556 | 0.333105526 |
| 3 | 1100000000 | 0.0555555556 | 0.390628585 |
| 1020 | 0011111111 | 0.0555555556 | 0.443219315 |
| 136 | 0001000100 | 0.0555555556 | 0.557161104 |
| 887 | 1110111011 | 0.0555555556 | 0.26740586 |
| 36 | 0010010000 | 0.0555555556 | 0.32436186 |
| 987 | 1101101111 | 0.0555555556 | 0.461269589 |
| 260 | 0010000010 | 0.0555555556 | 0.259378873 |
| 763 | 1101111101 | 0.0555555556 | 0.545211947 |
| 264 | 0001000010 | 0.0555555556 | 0.401746268 |
| 759 | 1110111101 | 0.0555555556 | 0.40604445 |

## 4. Hypothesize and verify

**Confirmed on the four selected failures:** rank-deficient subset systems enter the installed normal-equation solve; it returns enormous finite coefficients rather than raising `LinAlgError`. Recomputing that exact normal system reproduces the captured coefficients (max difference for the first case: 0.0). In installed SHAP 0.49.1, `KernelExplainer.solve` only invokes the weighted `lstsq` fallback and singularity warning after an exception. Thus the successful return from a numerically singular solve bypasses both safeguards. Forming a Gram matrix worsens conditioning and floating-point perturbations can make exact rank deficiency appear solvable. It is not evidence that the original statistical estimation problem has a huge optimum or that the adapter passed a different game.

Competing explanations were checked: binary-mask mapping, endpoint handling, cached model values, changed reference, and failed seed reproduction were excluded by the assertions above. Rank deficiency **alone** does not imply huge output: some systems can trigger the existing fallback, and a default feature-selected subproblem may be smaller and well-conditioned. The original main constrained-SVD estimator uses a different design and does not form these normal equations; its P1 rank deficiency is an identifiability/variance limitation, not this particular numerical blow-up.

## 5. Minimal diagnostic remedy and verification (not applied to main runs)

On **exactly the same Z, W and v**:
1. Replace only the normal-equation solve with `np.linalg.lstsq(sqrt(w)[:,None]*X, sqrt(w)*y, rcond=1e-10)`, then recover the eliminated coefficient by efficiency.
2. Independently reconstruct the full efficiency-constrained orthonormal solution: `phi = delta/d + U @ lstsq(sqrt(w)[:,None]*(Z@U), sqrt(w)*(v-v0-Z@base), rcond=1e-10)[0]`, where `ones.T @ U = 0` and U is orthonormal (the same constraint mechanism as the main kernel, but **library masks and weights**).

The first solution minimizes the norm of the retained eliminated-coordinate coefficients; the second minimizes the full attribution's deviation from the equal-allocation base. On a rank-deficient design they can legitimately differ, while both avoid the pathological normal solve. Neither identifies the exact reference uniquely from these few samples. Using `rcond=None` as in the installed fallback gives the same retained SVD coefficients as `rcond=1e-10` on all four failures (maximum difference 0); the improvement is not an artifact of a specially tuned cutoff. On all three working controls, changing only the selected-system normal solve to weighted SVD preserves library attributions to 1e-12. The full-feature constrained reconstruction is a different diagnostic from default feature selection, not a purported replacement for its selected-subproblem solution.

First-case normalized error: library **4.80617354e+15**, eliminated-coordinate SVD **0.0851068172**, constrained orthonormal SVD **0.0851068172**. Weighted fit residual norms: 0.134696495, 0.0297461833, 0.0297461833, respectively. Efficiency residuals: 0.00471506755, 2.77555756e-17, 5.55111512e-17. Efficiency alone is not a sufficient numerical check. Constrained weighted design rank is 8/9.

| j | reference | library | eliminated_SVD | constrained_SVD |
| --- | --- | --- | --- | --- |
| 0 | 0.0662987665 | 0.0962785201 | 0.0641944199 | 0.0641944199 |
| 1 | -0.132917435 | -0.167594318 | -0.123465307 | -0.123465307 |
| 2 | -0.129441108 | -0.222525769 | -0.125332918 | -0.125332918 |
| 3 | 0.0178053864 | 0.0485566342 | 0.0165588758 | 0.0165588758 |
| 4 | -0.00321413128 | 1.37700837e+15 | 0.00463218212 | 0.00463218212 |
| 5 | 0.0250143926 | 0.199133257 | 0.024278313 | 0.024278313 |
| 6 | 0.0244599842 | -1.37700837e+15 | 0.00463218212 | 0.00463218212 |
| 7 | 0.0948246234 | 0 | 0.0945936584 | 0.0945936584 |
| 8 | -0.0539110983 | -0.0423345011 | -0.0509339246 | -0.0509339246 |
| 9 | 0.0251295745 | -0.023616544 | 0.0248914731 | 0.0248914731 |

**Fix summary:** add only `/work/diagnose_library.py` and these diagnosis artifacts. No patch to the installed library, adapter, experimental design, analyses, paper, or reported results. A weighted rank-revealing least-squares solve is a demonstrated diagnostic remedy; adopting it as a baseline would be a separate protocol decision and is explicitly not done here.

**Verification:** rerun the command above. It checks deterministic matches, same-game identities, identical-design control, finite and bounded reconstruction assertions, all raw-record counts, and SHA256 invariance of 836 protected files. Protected hashes are identical before/after this diagnostic run: `True`.

**Bounded conclusion:** the four extreme records in this frozen limited library audit are reproduced numerical failures of this version/environment's unregularized low-budget normal-equation path on rank-deficient sampled designs. This does not condemn KernelExplainer generally, predict failure in all rank-deficient systems, establish every low-budget error's cause, or generalize to other SHAP versions, backgrounds, links, models or budgets. Original default and P16 results remain as recorded; all original huge values and warning-free failures are retained.
