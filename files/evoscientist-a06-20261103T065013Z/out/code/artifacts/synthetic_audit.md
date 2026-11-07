# Synthetic-results audit

## Verdict and scope

**The completed synthetic results support selection optimism, reliable exact-audit coverage, conservative simultaneous Hoeffding coverage, and a genuine failure of the unguarded Gaussian multiplier approximation in a correlated boundary setting. No selected-column indexing, target-mapping, or first-200 dataset-pairing defect was found. They do not establish a universal guarantee for the guarded approximation or a joint 95% accuracy-and-improvement guarantee from `evaluate`.**

Audited on 2026-11-03. Read the six requested files:

- `/work/code/statistics.py`
- `/work/code/run_experiments.py`
- `/work/artifacts/synthetic_summary.csv`
- `/work/artifacts/analytic_independent.csv`
- `/work/artifacts/guarantee_audit.csv`
- `/work/artifacts/tests.json`

For lightweight consistency and paired-uncertainty calculations, also read the 58 completed **synthetic-only** replication files: `replications/syn_00.npz` through `syn_56.npz`, and `replications/synthetic_finite_0.npz`. No experiments or multiplier simulations were rerun, no implementation/source files were changed, no web/literature search was performed, and no real-LLM outputs or data were inspected. The shared source file was read as requested; its real-data branch is outside this assessment.

The summary has **348 rows = 58 cells × 6 methods**, with no duplicate `(cell, method)` keys. All rows' coverage, mean width, optimism, paired coverage, and remainder-audit bias agree with their saved replication arrays within `1e-12`. There are 36 core, 8 K-stress, 4 boundary, 2 duplicate, 2 audit-size, 1 independent-multiplier, 4 B-sensitivity, and 1 finite-pool cells.

## Metrics and uncertainty

Let `j` be the first maximizer of selection means, `s` its selection score, and `a` its audit score.

- **Optimism:** `s - p[j]` for iid data; `s - mu[j]` for the fixed finite cohort. This is not selection regret, which is `max(p) - p[j]`.
- **Coverage:** fraction of replications whose interval contains the selected target; **width:** upper minus lower endpoint.
- **Audit remainder bias:** `a - remainder_target`. In iid cells the remainder target is `p[j]`; in finite-pool cells it is the selected column's actual unselected-remainder mean.
- **Audit gap:** `s-a`; its expectation equals remainder optimism, not generally finite-cohort optimism.
- **Paired coverage:** coverage of the selected-minus-column-0 difference by the paired exact-discordance interval. **False promotion:** `P(promote and true difference <= 0)`, with all replications as denominator, not the conditional rate among nonpositive targets.
- **MCSE:** sample standard deviation across replications divided by `sqrt(R)`. Mean and paired-difference intervals below use the normal approximation `estimate ± 1.96 MCSE`, unless otherwise specified. Coverage intervals are pointwise two-sided **Clopper–Pearson 95% Monte Carlo intervals**, including at 100% observed coverage. These describe simulation uncertainty, not the confidence intervals being evaluated.

The primary iid configuration is `syn_21`: K=8, n=64, m=128, p=0.7, equal means, latent rho=0.5, R=2,000, B=999. The finite complement has N=600 with the same n, m, K and one fixed generated pool. Primary summaries are targeted checks of the completed design; all new discrepancy tests, across-cell screening, and mechanistic findings here are exploratory. No pre-output registration was independently established by these files.

## 1. Exact independent all-equal optimism versus Monte Carlo

For independent, equal Bernoulli columns, with `F(x)=P(Binomial(n,0.7)<=x)`, the known exact benchmark is

`E[max_j selection_mean[j]] - 0.7 = sum_{x=0}^{n-1} [1-F(x)^K]/n - 0.7`.

Recomputing all **20 analytic CSV entries** changes none materially: maximum absolute discrepancy is **1.32e-16**. Eight of those entries have matching completed iid Monte Carlo cells with rho=0, gap=0, p0=0.7; the other twelve lack matching MC configurations and cannot be checked against this output grid.

| Cell | K | n | Exact optimism | MC mean | MCSE | MC minus exact | z |
|---|---:|---:|---:|---:|---:|---:|---:|
| syn_00 | 8 | 16 | 0.15443328 | 0.15328125 | 0.00136947 | -0.00115203 | -0.841 |
| syn_09 | 8 | 32 | 0.11145839 | 0.11056250 | 0.00099809 | -0.00089589 | -0.898 |
| syn_18 | 8 | 64 | 0.07976354 | 0.08020313 | 0.00073485 | +0.00043958 | +0.598 |
| syn_27 | 8 | 128 | 0.05682077 | 0.05774609 | 0.00054476 | +0.00092533 | +1.699 |
| syn_36 | 1 | 64 | 0 | -0.00112500 | 0.00127431 | -0.00112500 | -0.883 |
| syn_38 | 2 | 64 | 0.03223074 | 0.03026563 | 0.00101893 | -0.00196512 | -1.929 |
| syn_40 | 4 | 64 | 0.05821336 | 0.05794531 | 0.00084381 | -0.00026805 | -0.318 |
| syn_42 | 16 | 64 | 0.09810092 | 0.09907031 | 0.00064919 | +0.00096939 | +1.493 |

Here `z=(MC-exact)/MCSE`. Every exact value is inside its pointwise normal 95% MC interval. Exploratory two-sided normal tests with **Holm correction over these eight comparisons** have minimum adjusted p=**0.4302**. The largest absolute deviation is 0.001965, or 0.197 percentage points. Small negative K=1 sample optimism is consistent with zero, not a target/indexing failure. Dependence between n contrasts does not invalidate Holm.

## 2. Primary coverage and precision

All widths are in accuracy units; multiply by 100 for percentage points.

| Method | iid coverage [95% MC interval] | iid mean width | Finite coverage [95% MC interval] | Finite mean width |
|---|---:|---:|---:|---:|
| Naive-Wilson | 0.8395 [0.8227, 0.8553] | 0.202782 | 0.9020 [0.8881, 0.9147] | 0.203648 |
| Simult-Hoeffding | 0.9995 [0.9972, 1.0000] | 0.417067 | 1.0000 [0.9982, 1] | 0.417804 |
| Multiplier | 0.9730 [0.9649, 0.9797] | 0.308849 | 0.9705 [0.9621, 0.9775] | 0.293383 |
| Guarded-multiplier | 0.9730 [0.9649, 0.9797] | 0.308849 | 0.9705 [0.9621, 0.9775] | 0.293383 |
| Audit-Wilson | 0.9460 [0.9352, 0.9555] | 0.155828 | 0.9705 [0.9621, 0.9775] | 0.139798 |
| Audit-exact | 0.9660 [0.9571, 0.9735] | 0.163990 | 0.9565 [0.9466, 0.9650] | 0.127751 |

Primary iid optimism is **0.0650703 [0.0632891, 0.0668515]**; finite-cohort optimism is **0.0567496 [0.0548886, 0.0586105]**.

Paired primary iid effects, using the same replay outcomes:

- Exact-audit minus naive coverage: **+12.65 percentage points**, 95% MC interval **[+10.85, +14.45]**.
- Exact-audit minus naive mean width: **-0.038793 [-0.039375, -0.038210]**.
- Exact-audit minus Hoeffding mean width: **-0.253077 [-0.253851, -0.252304]**.

These are descriptive, pointwise effect intervals, not an additional family of confirmatory significance tests. **The precision comparison is not equal-budget:** the audit uses 128 additional observations whereas the selection intervals use n=64. With shared selection data, exact-audit mean widths are **0.329870** at m=32, **0.233196** at m=64, and **0.163990** at m=128; corresponding coverages are 0.9720, 0.9755, and 0.9660. Do not attribute the primary audit's narrower-than-naive width entirely to a superior interval formula.

### Guaranteed-method audit

Recomputed all **116 one-sided exact binomial tests** of coverage below 0.95 for Hoeffding and Audit-exact. Raw p-values match `guarantee_audit.csv` to 1.11e-16; Holm adjustments match exactly. **All adjusted p-values equal 1.0.** Across cells:

- Hoeffding coverage: **0.9975–1.0000**, strongly conservative.
- Exact-audit coverage: **0.9480–0.9820**. Its minimum, `syn_35`, has MC interval **[0.9373, 0.9573]**, raw undercoverage p=**0.3548**; this is not evidence against 95% coverage.

Repeated/shared configurations make this family conservative but do not invalidate Holm, which permits dependent tests. Absence of rejection is not proof of uniform coverage. The finite-cohort result is conditional on one fixed pool, not a distribution of newly generated pools.

### Paired improvement

Primary iid paired coverage is **0.9980 [0.9949, 0.9995]**. Under its all-equal null, naive false promotion is **217/2000=10.85%** versus exact-paired **2/2000=0.10%**, a paired reduction of **10.75 percentage points [9.38, 12.12]**. The individual exact MC intervals are [9.52%, 12.30%] and [0.012%, 0.361%].

Finite-pool paired coverage is **0.9985 [0.9956, 0.9997]**. Its nonpositive-target frequency is only 784/2000=0.392: the reported unconditional false-promotion rates 0.031 and 0.0005 correspond to conditional rates **62/784=7.91%** and **1/784=0.128%**. Across all cells, paired coverage is 0.995–1.0. Self-selection of baseline 0 is handled by an exact [0,0] difference interval; in the primary iid cell it occurs 338 times. Nonself paired coverage there remains 0.99759, so high coverage is not solely this trivial case.

## 3. Approximate-method boundary failure

All rows below have K=8, n=16, m=128, equal means, R=2,000.

| Cell | p0 | Latent rho | Any-column zero-variance rate | Raw multiplier coverage [95% MC interval] | Guarded coverage | Exact-audit coverage |
|---|---:|---:|---:|---:|---:|---:|
| syn_44 | 0.30 | 0 | 0.0225 | 0.9610 [0.9516, 0.9691] | 0.9975 | 0.9685 |
| syn_45 | 0.30 | 0.9 | 0.0190 | 0.9695 [0.9610, 0.9766] | 0.9975 | 0.9650 |
| syn_46 | 0.95 | 0 | 0.9925 | 0.9990 [0.9964, 0.9999] | 1.0000 | 0.9820 |
| syn_47 | 0.95 | 0.9 | 0.7340 | **0.8250 [0.8076, 0.8414]** | 1.0000 | 0.9735 |

The correlated high-accuracy cell misses nominal coverage by **12.5 percentage points**, despite otherwise benign primary behavior. All **350 failures** have selected score 1 and effectively zero multiplier width (<1e-7); there are exactly 350 such zero-width intervals. Thus the empirical covariance has collapsed on fully saturated data and cannot express the true sampling uncertainty. An *any-column* zero-variance flag alone does not predict failure: independent `syn_46` has more such columns but other variable columns keep the maximum radius nonzero in almost every replay.

In the duplicate-column cell `syn_48` (rho=1, p0=0.7, n=16), raw multiplier coverage is also low: **0.8735 [0.8581, 0.8878]**. Only 9 of its 253 misses have effectively zero width; the other 244 show small-sample Gaussian approximation error even without complete covariance collapse. This is a second mechanism, not evidence that duplicate columns were accidentally treated as independent.

For an explicitly defined **exploratory 58-cell raw-multiplier undercoverage family**, exact one-sided binomial tests with Holm correction give adjusted p=**8.48e-90** for `syn_47` and **1.22e-38** for `syn_48`; no other cell rejects at 0.05. This separate family is not the guaranteed-method family supplied in the CSV. The guarded method falls back to Hoeffding for every n=16/32 replay and repairs these demonstrated failures. Its worst observed coverage is nevertheless 0.9420 (`syn_37`, K=1, n=64; interval [0.9308, 0.9518]); no guarded undercoverage test rejects after Holm over its 58 cells. No cell has a guard rate strictly between 0 and 1: the grid does not test a genuinely mixed/data-dependent fallback regime.

## 4. Source audit: indexing, estimands, correlation, and seeds

### Selected-column and baseline indexing — passed

`statistics.py::evaluate` computes a length-R winner vector from selection data only. Advanced indexing `S[idx,:,winner]` and `A[idx,:,winner]` selects the same per-replay column with shape (R,n) and (R,m), respectively; it does not swap sample and prompt axes. `target[winner]` is the correct population/pool truth. Discordances compare this selected audit column with `A[:,:,0]`; selection differences use `S[:,:,0]`. Neither selector nor guard accesses audit outcomes. The >0 gap is assigned to the **last** prompt; ties intentionally choose the **first** maximum, favoring early indices/baseline and potentially disadvantaging that last best prompt. This is a convention to disclose, not a hidden random tie break.

### Finite remainder versus full cohort — passed, label carefully

For fixed total successes T[j], `remtruth=(T[j]-n*s)/(N-n)`. The hypergeometric interval uses **M=N-n=536**, m=128; it targets the remainder, not N=600 directly. The full-cohort interval correctly maps endpoints as

`full_endpoint = (n/N)*s + ((N-n)/N)*remainder_endpoint`.

Paired difference endpoints use the corresponding observed selection difference plus the mapped remainder difference. Exact remainder and mapped full-cohort coverage arrays are identical. The saved identity

`remainder_optimism = N/(N-n) * cohort_optimism`

holds to **1.11e-16**. Finite mean remainder optimism is **0.06352565**, versus cohort optimism **0.05674958** and mean audit gap **0.06416016**. Do not call all three quantities the same estimand.

The finite multiplier uses `(1-n/N)` on its estimated sample-mean covariance; the exact interval uses hypergeometric inversion, not that approximate correction. The iid Clopper–Pearson intervals and the finite hypergeometric intervals are appropriately separate. The finite Audit-Wilson comparator is a mapped binomial approximation and need not be narrower than the finite exact hypergeometric interval.

### Latent versus binary correlation — important distinction

Generation is `sqrt(rho)*common + sqrt(1-rho)*eps <= norm.ppf(p)`. Thus rho is the Gaussian **latent** correlation; it is not Bernoulli outcome correlation. For p0=0.7, equal means, observed average binary correlation is **0.31769** at latent rho=0.5 and **0.70276** at latent rho=0.9; at p0=0.95, latent rho=0.9 gives only **0.61744**. `binary_correlation` correctly records the empirical outcome correlation, averaged over pairs and all generated rows (not just selection rows). At rho=1 equal-mean columns are identical; at K=1 off-diagonal correlation is undefined/NaN. A singular covariance is valid and intentionally preserved.

The `independent_multiplier` cell changes only the approximation's covariance to diagonal; **the data remain correlated** with latent rho=0.5. Relative to the primary full-covariance multiplier, its width increases by **0.004100 [0.003809, 0.004391]** and coverage by 0.004 (descriptive paired interval [0.00034, 0.00766]). This is an inference ablation, not an independently generated-data cell or a demonstration that ignoring positive dependence causes undercoverage here.

### Seed structure and pairing — first-200 claim verified

`run_experiments.py::synthetic` seeds each dataset using SHA-256-derived `sid(f"{K}_{rho}_{gap}_{p0}")`, then **always generates R=2000 × 256 rows before truncating to `reps`**. Specifically, source lines 49–50 generate `common` and `eps` with the global R and only slice `[:reps]` after thresholding. K, rho, gap, p0 determine the key; n, m, B, replication truncation, and approximation choice do not.

Consequently:

- `syn_53`/`syn_54` use exactly the first 200 datasets of n=16 main `syn_03`.
- `syn_55`/`syn_56` use exactly the first 200 datasets of n=64 main `syn_21`.
- At fixed K/rho/gap/p0, n contrasts share underlying item vectors; m contrasts share selection data and nested audits. Audits start at row n, so n contrasts do **not** share an unchanged audit slice. Within every cell the selection and audit rows are disjoint; n+m never exceeds 256.
- Across K, rho, or gap, seeds change; those contrasts are **not** intentionally paired/common-random-number contrasts. The 22 distinct actual generation keys have 22 distinct hash seeds.
- The independent-multiplier ablation shares the primary datasets. Finite replay permutations are generated independently using seed 3301 on a single fixed pool generated with seed 7711.

Saved arrays corroborate the construction without rerunning generation: **every result array** in B=999 low cells equals the corresponding first-200 main array exactly, including multiplier coverage and widths. High-B cells match the main first 200 in every array except the multiplier/guarded-multiplier outputs that can depend on B.

**Dataset pairing is not nested multiplier-draw pairing.** `multiplier_radius` requests normals with shape `(batch_size,B,K)` from a shared seed. Increasing B changes the stream offsets for subsequent replays, so their low-B normals are generally not prefixes of their high-B normals; using the same seed does not guarantee that nesting. The first replay shares an initial prefix, but this does not extend to all replays. This does not invalidate either estimate or paired-by-dataset analysis.

| n | B=999 multiplier coverage | B=3999 coverage | High-minus-low mean width [paired 95% MC interval] | Coverage discordance |
|---:|---:|---:|---:|---:|
| 16 | 0.970 | 0.965 | +0.000187 [-0.000748, +0.001123] | 1 replay loses coverage |
| 64 | 0.965 | 0.970 | +0.000455 [-0.000461, +0.001372] | 1 replay gains coverage |

Each coverage change is only 0.5 percentage points among 200 datasets; the exact paired discordance/sign test has two-sided p=1 for each n. B=999 coverage 0.970 has exact MC interval [0.9358, 0.9889]; coverage 0.965 has interval [0.9292, 0.9858]. These are reassuring small observed differences, **not a tight equivalence or convergence guarantee**. At n=16 the guarded method is identical for both B values because it uses Hoeffding throughout.

## 5. Severity-ranked findings and minimal fixes (proposals only)

| Rank | Severity | Finding | Minimal proposed action; no code edited |
|---:|---|---|---|
| 1 | High, substantive method failure | Raw multiplier coverage collapses to 82.5% in the correlated p0=0.95/n=16 cell and 87.35% with n=16 duplicates. | Do not recommend the raw approximation in these regimes. Use the already available exact audit or existing small-n Hoeffding fallback; do not mask singularity with an arbitrary variance floor. Keep the boundary counterexample visible. |
| 2 | High if a joint guarantee is claimed; otherwise a reporting caveat | `evaluate` spends alpha=0.05 on accuracy and 0.025 on each discordance marginal, yielding separate 95% accuracy and 95% difference claims, not guaranteed joint 95% coverage. The two claims together only obtain a 90% union-bound floor. | Label them marginal; if joint 95% is required, allocate alpha=0.025 to accuracy and 0.0125 to each discordance marginal, then regenerate only affected interval outputs in a later authorized step. Empirical primary joint coverage, 0.9640 iid and 0.9555 finite, cannot supply the missing uniform guarantee. |
| 3 | Medium, interpretation | Latent rho is not binary correlation; `independent_multiplier` is not independent data; finite remainder optimism is not cohort optimism. | Name rho “latent Gaussian correlation”; show the binary-correlation metadata and distinguish the three finite selection-gap quantities. Rename the ablation descriptively in reporting. |
| 4 | Medium, scope of validation | Guarded coverage looks good in the failing cells because all small-n cases use Hoeffding; mixed fallback behavior is untested, and K=1 n=64 coverage is 0.942–0.9425. | Call it a heuristic, not a finite-sample-guaranteed method. Retain guaranteed Hoeffding/exact audit for guaranteed claims; add mixed-regime validation only in a future experiment. |
| 5 | Medium, comparison fairness/generalization | Primary audit has m=128 extra rows versus n=64 selection data; finite results condition on one realized N=600 cohort. | Qualify precision claims with sample cost; present existing m=64 contrast. Restrict finite coverage conclusions to the fixed-cohort design. |
| 6 | Low, reproducibility/interpretation | B sensitivity is correctly paired on the first 200 datasets, but normals are not nested across B; 200 datasets give limited precision. | Describe the current experiment accurately. If nested-draw coupling is desired later, use per-replay bootstrap streams or pre-generated maximum-B draws and take prefixes. No rerun is needed to verify current dataset sharing. |
| 7 | Low, reporting | `honest_false_promotion` and `naive_false_promotion` are unconditional joint probabilities, and `coverage_mcse=0` at 100% is only a plug-in boundary artifact. | State denominators and show conditional rates separately when useful; use exact/Wilson Monte Carlo intervals rather than a zero-width uncertainty bar at 100%. |
| 8 | Low, evidence limits | `tests.json` reports passing finite tests but does not specify tested grids, tolerance, source version, or multiplier-equivalence replication details. | Preserve the reported results as finite checks, not a proof or full provenance record; later attach test-domain/version metadata if stronger reproducibility claims are needed. |

No critical implementation defect requiring a source change was established. The second finding is conditional on claiming joint coverage: marginal coverage is what the inspected synthetic code actually computes. The current boundary failures are failures of an approximation, not evidence that the exact-audit implementation is broken.

## 6. Test-summary evidence and residual checks

`tests.json` reports minimum exhaustive hypergeometric coverage **0.9502262443**, minimum CP-grid coverage **0.9507460925**, **560** enumerated selection/audit cases, full-pipeline and paired-pipeline coverage **1.0**, a passed duplicate/tie/self-comparison check, and multiplier-equivalence quantile difference **0.0005350536**. These support implementation sanity on the tested domains. They do not independently prove all-parameter validity or say whether “full-pipeline” and “paired-pipeline” are jointly evaluated. The parser fixture result is outside this synthetic statistical audit and was not investigated.

The multiplier computes sample covariance divided by n, `X'X/[n(n-1)]`, with Gaussian eigenbasis simulation. This preserves fitted dependence and singular columns, with no variance floor. Its equivalence to row multipliers requires the corresponding finite-sample normalization (weights applied as `1/sqrt(n(n-1))`); the common `1/n` row normalization differs by a factor `sqrt(n/(n-1))`. No incompatible row-multiplier implementation was found in the requested source, so this is a normalization convention to state, not an established error.

Primary iid audit bias is +0.0023047 (pointwise MC interval [0.0005247, 0.0040847]); this isolated deviation should not be called a selection-induced audit bias. Exploratory normal mean-bias tests across the 58 cells yield minimum Holm p=**0.3024** (primary adjusted p=0.6248), and source generation gives independent audit rows. Finite primary audit bias is -0.0006345 [-0.0022445, 0.0009755]. No systematic seed/leakage problem is demonstrated.

## Recommended next experiments — not executed

1. **Guard-transition stress test:** n near 64 and probabilities near 0/1, including identical/highly correlated columns; choose configurations with guard rates strictly between zero and one. Evaluate marginal and, if claimed, correctly budgeted joint coverage with predefined undercoverage families.
2. **More precise B sensitivity:** increase the paired dataset count, couple normals per replay if desired, and predefine a practically relevant coverage/width equivalence margin; keep saturated boundary failures separate from finite-B noise.
3. **Fixed-budget and pool robustness:** compare selection/audit allocations at fixed total observations, and repeat finite-pool checks over independently generated cohorts if making across-cohort claims.

## Outputs

Tables and calculations are embedded in **`/work/artifacts/synthetic_audit.md`**. No standalone figures, scripts, source edits, or model outputs were produced. Overall: retain the exact-audit and selection-optimism conclusions, retain the raw-multiplier boundary failure as a strong counterexample, and qualify joint-coverage, correlation, guarded-method, cost, and B-convergence claims as above.
