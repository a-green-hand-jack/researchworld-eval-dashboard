# Independent audit of existing experiment outputs

**Scope:** Read-only audit completed 2026-11-02. No experiments, estimators, hyperparameters, existing analysis code, or manuscript files were changed or rerun. A standalone data-analysis script reads saved outputs; it never imports or invokes experiment estimators. No web or paper-content inference was used. **`artifacts/irt_runs/**` was excluded entirely:** this report makes no statement about the separate, unfinished stronger comparator.

## 1. Bottom line and paper-safe claims

The saved summaries and four budget-50 effects are numerically reproducible. The defensible story is **modest MAE improvement over sampling baselines, not overall superiority, universal improvement, better ranking, or deployment-calibrated inference**. The repeated-mask panel supports a bias–variance tradeoff: honest correction removes substantial observed signed bias in the MMLU-Pro frontier panel, but biased alternatives can still have lower MAE/MSE.

Paper-ready wording:

> Across the 13 supplied banks, with exact-response target groups weighted equally and five seeds averaged within bank, budget-50 SCFD macro MAE was 3.765808 percentage points under IID holdout and 3.802826 under retrospective capability-frontier holdout. Relative to uniform sampling, the reductions were 0.715471 pp (15.9658%) and 0.599164 pp (13.6112%); relative to stratified means they were 0.217988 pp (5.4719%) and 0.125194 pp (3.1872%). These are descriptive results on correlated banks, not independent-dataset or deployment guarantees. The frontier comparison with stratified means did not meet the nominal 0.05 threshold under the prespecified Holm-adjusted sign-flip analysis (p=0.0515137).

> In the prespecified fixed-source, six-target MMLU-Pro frontier panel at budget 10, over 200 saved masks, AIPW-population had signed error −3.844525 ± 0.489666 pp (Monte Carlo SE), compared with SCFD's +0.060830 ± 0.498066 pp. This panel is consistent with reduced signed bias under honest auditing; it does not establish zero bias for every target or all banks. Nor does it imply minimum prediction error: the contaminated diagnostic had lower empirical MSE than SCFD in this same panel.

The four primary tests are prespecified in the supplied frozen protocol; all additional analyses/failure cases in this report are **exploratory/descriptive**. Historical preregistration timing cannot be independently established from a current protocol file alone.

## 2. Metrics and exact budget-50 verification

For target group j, error e_j = predicted finite-bank mean correctness minus true mean correctness. MAE = mean_j |e_j|; MSE = mean_j e_j²; RMSE = sqrt(MSE); signed error = mean_j e_j. Primary macro MAE averages five seeds within each bank and then gives 13 banks equal weight. Macro RMSE is **sqrt of the equally bank/seed-weighted MSE**, not mean per-bank RMSE. Errors in CSV/JSON are fractions: multiply MAE/RMSE/signed error by 100 for percentage points; multiply fraction-squared MSE/variance by 10,000 for pp².

### Macro errors at budget 50 (pp)

| Method | IID MAE | IID RMSE | Frontier MAE | Frontier RMSE |
|---|---:|---:|---:|---:|
| Uniform | 4.481279 | 5.746914 | 4.401990 | 5.601746 |
| Stratified mean | 3.983796 | 5.119576 | 3.928019 | 4.998653 |
| Stratified item difference | 3.914657 | 5.046158 | 3.830210 | 4.891587 |
| Score ridge | 3.090308 | 4.055960 | 7.513082 | 9.079332 |
| Stratified score ridge | 3.020969 | 4.039512 | 7.369486 | 8.886552 |
| AIPW-population | 3.602308 | 4.625885 | 3.815325 | 4.843596 |
| Rasch 1PL (labeled reimplementation) | 3.742502 | 4.850756 | 3.757393 | 4.798037 |
| SCFD | 3.765808 | 4.835794 | 3.802826 | 4.857882 |

### Four prespecified paired contrasts

Delta = SCFD MAE − comparator MAE; negative favors SCFD. CIs are the saved 10,000-replicate percentile bank-bootstrap intervals (seed 701), reproduced independently. Sign-flip p-values exhaust all 2^13 sign configurations. Holm adjustment correctly covers the **four** primary tests.

| Regime | Comparator | Delta MAE (pp) | Descriptive 95% bank-bootstrap interval (pp) | Banks lower MAE | Raw sign-flip p | Holm p |
|---|---|---:|---:|---:|---:|---:|
| IID | Uniform | −0.715471 | [−0.904381, −0.535765] | 13/13 | 0.000244140625 | 0.0009765625 |
| IID | Stratified mean | −0.217988 | [−0.337087, −0.116747] | 12/13 | 0.000732421875 | 0.002197265625 |
| Frontier | Uniform | −0.599164 | [−1.000041, −0.186668] | 11/13 | 0.0185546875 | 0.037109375 |
| Frontier | Stratified mean | −0.125194 | [−0.231636, −0.018388] | 10/13 | 0.051513671875 | 0.051513671875 |

**No contradiction:** the last unadjusted percentile-bootstrap interval excludes zero while its sign-flip p-value exceeds 0.05. They use different constructions and are not inversions of the same test. The intervals also are not simultaneous four-contrast intervals. Do not claim all four contrasts are statistically significant.

The original-row-weighted sensitivity preserves the directions: budget-50 MAEs (SCFD / uniform / stratified mean) are IID 3.737893 / 4.446669 / 3.970737 pp and frontier 3.799621 / 4.407401 / 3.928390 pp. This sensitivity does not remove family/model dependence.

## 3. Independent NPZ and integrity checks

Read the requested protocol, summary CSVs/JSON, `src/analyze.py`, `data_audit.csv`, and the saved-output/metric definitions in `common.py`, `run_experiments.py`, `diagnostics.py`, and `methods.py`.

- Main grid: **130** bank/regime/seed cells, **8,840** group-weighted method/budget records = 13 banks × 2 regimes × 5 seeds × 4 budgets × 17 methods. Optional gap grid: 65 cells. All JSON records including row sensitivities and gap: **19,890**, with no duplicate composite record keys.
- Reconstructed all summary MAE/RMSE/bias/rho values from saved run JSONs. Maximum macro discrepancies were 1.2490e−16 / 1.1102e−16 / 9.9747e−17 / 2.2204e−16, respectively; ordinary CSV floating-point roundoff. The four effect estimates, interval endpoints, raw p-values and Holm p-values reproduced **exactly**.
- Independently recomputed MAE, MSE, RMSE and signed error from **20 main NPZ files**: GSM and MMLU-Pro × IID/frontier × all five seeds × all four budgets × all 17 methods × group/row weighting = **2,720 metric rows**. Maximum discrepancy against the JSON metrics across all four error fields: **0.0**. This is independent arithmetic on saved predictions, not independent rerunning of an estimator.
- Ground-truth means matched the original binary-bank rows exactly (maximum discrepancy 0.0). Saved group IDs and representatives matched independently recomputed raw-response equivalence groups; source/target rows and response groups were disjoint. GSM is 83 × 1,000 with 83 unique rows; MMLU-Pro is 448 × 12,032 with 425 unique rows. Both input-file SHA-256 hashes match `data_audit.csv`; binary/finite checks pass.
- Across **all 520 main bank/regime/seed/budget query cells**, saved uniform and stratified query sets have exactly the advertised number of unique items, and saved pilot/audit folds are disjoint and exhaust the stratified queries. Stratified fold sizes are 5/5, 10/15, 25/25, 50/50 for budgets 10,25,50,100. This establishes actual saved budget compliance, not a general feasibility guarantee of the sampler.
- All recorded code hashes match current `methods.py`, `common.py`, `run_experiments.py`. Hash coverage does **not** include `analyze.py` or `diagnostics.py`; current consistency cannot establish historical tuning absence or complete environment reproducibility.
- `integrity.json` reports zero undefined core group correlations; Rasch maximum final update 9.998656777270953e−7 and maximum 62 iterations. Update convergence is not proof of best possible comparator quality or faithful reproduction of a different IRT algorithm.

### Independently recomputed two-bank budget-50 errors (pp)

Each entry averages group-weighted MAE or MSE over five seeds; RMSE is the square root **after** averaging MSE. The full seed/budget/method/weighting results are in the verification CSV.

| Bank | Regime | Method | MAE | RMSE |
|---|---|---|---:|---:|
| GSM | IID | Uniform | 4.674400 | 5.666893 |
| GSM | IID | Stratified mean | 3.653600 | 4.725260 |
| GSM | IID | AIPW-population | 4.011324 | 4.933074 |
| GSM | IID | SCFD | 3.558604 | 4.721935 |
| GSM | Frontier | Uniform | 3.325600 | 4.247117 |
| GSM | Frontier | Stratified mean | 3.552800 | 4.415926 |
| GSM | Frontier | AIPW-population | 3.040446 | 3.854894 |
| GSM | Frontier | SCFD | 3.664522 | 4.473165 |
| MMLU-Pro | IID | Uniform | 4.339943 | 5.410045 |
| MMLU-Pro | IID | Stratified mean | 3.868571 | 4.811268 |
| MMLU-Pro | IID | AIPW-population | 3.423150 | 4.389200 |
| MMLU-Pro | IID | SCFD | 3.896797 | 4.858045 |
| MMLU-Pro | Frontier | Uniform | 4.816741 | 5.990692 |
| MMLU-Pro | Frontier | Stratified mean | 4.989701 | 6.196367 |
| MMLU-Pro | Frontier | AIPW-population | 4.377931 | 5.441073 |
| MMLU-Pro | Frontier | SCFD | 4.697648 | 5.867193 |

## 4. Repeated masks: decomposition and uncertainty

Independently read **all eight diagnostic NPZ files**, covering two banks × two regimes × budgets 10/100, each with 200 masks and six fixed target groups, and recomputed all **88** method records. Maximum discrepancy against the saved repeated-mask summary: 9.9747e−17. All eight diagnostic ground-truth vectors match the original binary matrices exactly and their rows belong to the corresponding main seed-0 target set. **There is no budget-50 repeated-mask panel:** do not transport these bias measurements numerically to the primary budget-50 endpoint.

Let R=200, J=6, e_rj=prediction_rj−truth_j, and b_hat_j=mean_r e_rj. The saved identity is

    empirical MSE = mean_j Var_r(e_rj, ddof=0) + mean_j b_hat_j².

The maximum absolute identity residual across 88 records is **2.74574200181954e−17**. The `variance` column is average **within-target, across-mask** variance, not variance across the six truths. `bias_squared` is average squared **targetwise** estimated bias, NOT `(overall signed error)²`. Opposite target biases can cancel in the overall signed error without cancelling in MSE.

Furthermore, `bias_squared` has finite-mask upward noise even for a truly unbiased estimator. Under independent mask repetitions its noise correction is

    corrected squared bias = bias_squared − variance/(R−1).

This correction can be negative and should not be silently clipped/interpreted as a negative true squared bias. The empirical ddof=0 decomposition is exact; replacing its variance with ddof=1 without adjusting the other term destroys that exact identity. Neither the empirical identity nor small aggregate signed error proves design unbiasedness.

### Frontier bias panel: signed error ± one MCSE (pp)

| Bank | Budget | Stratified mean | AIPW-population | SCFD | SCFD no audit | Contaminated diagnostic |
|---|---:|---:|---:|---:|---:|---:|
| GSM | 10 | +0.391667 ± 0.356756 | +0.468977 ± 0.399951 | +0.301102 ± 0.354789 | +0.711864 ± 0.348237 | +0.505451 ± 0.349851 |
| GSM | 100 | +0.030833 ± 0.106744 | −0.181982 ± 0.099426 | +0.047938 ± 0.083037 | −0.283545 ± 0.092499 | −0.109080 ± 0.085204 |
| MMLU-Pro | 10 | −0.386961 ± 0.514183 | −3.844525 ± 0.489666 | +0.060830 ± 0.498066 | −5.754699 ± 0.464989 | −2.846006 ± 0.473206 |
| MMLU-Pro | 100 | −0.169474 ± 0.172982 | −1.095059 ± 0.146272 | +0.048372 ± 0.152066 | −1.720243 ± 0.149489 | −0.832345 ± 0.145472 |

Across all eight panels, max |SCFD overall signed error|/MCSE = **1.136076**. This is compatibility with zero aggregate bias at this Monte Carlo resolution, not evidence that every target is unbiased. For example, MMLU-Pro IID budget-10 SCFD has maximum absolute targetwise estimated bias **1.471118 pp**.

### Numeric MSE decomposition examples (fraction-squared units)

| Panel / method | Empirical MSE | Within-target variance (ddof=0) | Targetwise estimated bias² |
|---|---:|---:|---:|
| MMLU-Pro frontier b10 / SCFD | 0.015215140664 | 0.015157521231 | 0.000057619433 |
| MMLU-Pro frontier b10 / AIPW-population | 0.016336372217 | 0.014795567789 | 0.001540804429 |
| MMLU-Pro frontier b10 / no audit | 0.016925202369 | 0.013585620411 | 0.003339581958 |
| MMLU-Pro frontier b10 / contaminated | 0.014695652824 | 0.013847119833 | 0.000848532991 |
| MMLU-Pro frontier b100 / SCFD | 0.001643520173 | 0.001633889739 | 0.000009630433 |
| MMLU-Pro frontier b100 / AIPW-population | 0.001685762449 | 0.001552469513 | 0.000133292936 |
| GSM frontier b10 / SCFD | 0.008125235746 | 0.008076946094 | 0.000048289652 |
| GSM frontier b10 / no audit | 0.007612279392 | 0.007483939884 | 0.000128339508 |

For MMLU-Pro frontier b10 SCFD, noise-corrected estimated squared bias is **−0.000018549016** (consistent with no resolved squared bias), versus **0.001466454842** for AIPW-population. SCFD has **higher** within-target variance than AIPW-population in that panel, despite lower MSE. Thus “auditing always reduces variance” is false. The contaminated diagnostic's still smaller MSE is a concrete counterexample to “honesty necessarily minimizes error.”

### Shared-mask dependence and paired Monte Carlo errors

The existing bias MCSE is correctly computed as `SD_r(mean_j e_rj, ddof=1)/sqrt(200)`. All targets see the same mask, so the **mask**, not the individual target/mask prediction, is the Monte Carlo unit. Averaging 1,200 predictions as independent observations would be pseudoreplication. On MMLU-Pro frontier b10 SCFD, correct bias MCSE is **0.498066 pp**; ignoring between-target covariance yields **0.356297 pp**. Correct same-mask paired differences also retain covariance between methods; budgets and regimes reuse mask-seed schedules and must not simply be stacked as independent replicates.

Exploratory paired examples (SCFD − comparator MAE, mean ± one MCSE):

- MMLU-Pro frontier b10 versus AIPW-population: **−0.450602 ± 0.346484 pp**; the unadjusted normal Monte Carlo interval includes zero. Strongly different signed errors do not establish a resolved MAE difference with 200 masks.
- MMLU-Pro frontier b100 versus AIPW-population: **+0.001372 ± 0.110701 pp**; essentially equal observed MAE despite different signed errors.
- GSM frontier b10 versus no audit: **+0.248817 ± 0.058155 pp**; correction costs empirical MAE here.
- MMLU-Pro frontier b100 versus contaminated: **+0.143642 ± 0.042494 pp**; smaller signed bias is not smaller MAE.

All mask-paired differences, MCSEs, and **unadjusted, exploratory** normal 95% Monte Carlo intervals are saved separately. These are not multiple-testing-adjusted significance findings, simultaneous intervals, target-population confidence intervals, or model-deployment intervals. No additional confirmatory p-value family was introduced.

## 5. Ranking is not score accuracy

Spearman rho, Kendall tau-b, and pairwise agreement measure ordering, not calibration. Pairwise agreement excludes true-score ties and awards half credit to predicted ties. Each reported correlation/agreement is computed within a bank/seed then macro-averaged; it is not a pooled across-bank correlation. These metrics can disagree even among themselves because their tie handling/normalization differs.

At frontier budget 50:

| Method | MAE (pp) | Spearman rho | Kendall tau-b | Pairwise agreement |
|---|---:|---:|---:|---:|
| Uniform | 4.401990 | 0.663848 | 0.518484 | 0.748707 |
| Stratified mean | 3.928019 | 0.692975 | 0.531627 | 0.761258 |
| SCFD | 3.802826 | 0.675426 | 0.509560 | 0.755486 |
| Rasch 1PL | 3.757393 | 0.663747 | 0.517385 | 0.748831 |

SCFD has lower MAE than stratified means but worse **all three** ranking metrics. It has better rho and pair agreement than uniform, yet worse tau-b. Conversely, Rasch has lower MAE than SCFD but worse rho/pair agreement. Claims of universally improved ranking are unsupported. Adding a common offset to predictions would change MAE/bias without changing any ordering metric; calibration and ordering are intrinsically different objectives. Comparing IID and frontier correlations also changes the target score range, so lower frontier rho is not solely an estimator failure.

## 6. Concrete failures and limits on inference

### Losses must remain visible

- Frontier budget-50 SCFD loses to uniform on **BBH (+0.792899 pp)** and **GSM (+0.338922 pp)**.
- Frontier budget-50 SCFD loses to stratified means on **GPQA (+0.186591 pp), GSM (+0.111722 pp), IFEval (+0.197611 pp)**. IID it loses on **MMLU-Pro (+0.028226 pp)**.
- At budget 25, SCFD is worse than stratified means in **both** regimes: IID 5.637957 versus 5.604798 pp; frontier 5.451268 versus 5.384966 pp. Improvements are not monotone across all budgets/contrasts. Unequal 10/15 folds and fixed half-averaging at b25 are prespecified, not a discovered posthoc repair target.
- IID budget-50 SCFD is worse than score ridge, stratified score ridge, AIPW-population, and the saved Rasch 1PL MAE. Frontier Rasch 1PL also has lower MAE/RMSE. SCFD's frontier MAE advantage over AIPW-population is only **0.012500 pp**, and its RMSE is **higher** (4.857882 versus 4.843596 pp). No overall winner/SOTA claim follows.
- Frontier score ridge has large negative aggregate signed error (**−7.426390 pp**) versus SCFD (**−0.256671 pp**), but this five-seed aggregate is not a conditional design-bias estimate. Frontier stratified mean has signed error −0.198987 pp, smaller in magnitude than SCFD in this finite run grid.
- Relative to stratified item difference, learned-pilot SCFD's budget-50 MAE gains are **0.148850 pp IID** and **0.027384 pp frontier**; at frontier b100 stratified item difference is slightly better (2.584827 versus 2.593369 pp). The existing outputs do not show that target-specific learning always improves source-only control variates.

### Bootstrap and sign-flip dependence

1. **Correct pairing, limited inferential unit:** the implementation averages five seeds within bank, forms paired differences, and resamples the 13 paired bank means. It does not improperly treat 65 seed/bank cells as independent bank draws. However, shared model pools and related benchmarks mean the 13 banks are not independent sampling units. Neither the bootstrap nor independent sign flipping preserves that cross-bank dependence. Holm only adjusts multiplicity; it does not repair invalid exchangeability/independence assumptions. Numerical p-values are correctly computed conditional on their reference scheme, not certified population-level significance.
2. **Finite seeds:** bank-bootstrap intervals condition on the realized five-seed averages, not the infinite-mask expected error. `seed_sd` is sample SD of five *macro* MAEs, not a standard error, per-target interval, bank heterogeneity measure, or uncertainty propagated into the bank bootstrap. Under frontier construction all 13 banks have **identical source/target row sets across seeds**; seed variation there is query/fitting randomization, not five independent OOD holdouts. IID target sets also overlap across seeds.
3. **Influential mask seed:** frontier SCFD−uniform seed-specific macro deltas are −0.201229, −0.237344, −1.668957, −0.194793, −0.693497 pp. Seed 2 supplies a disproportionately large gain. Descriptively dropping it changes the average from −0.599164 to **−0.331716 pp**, still favorable; this is sensitivity, not an alternate primary endpoint. IID the corresponding change is −0.715471 to **−0.488785 pp**. Leave-one-bank-out effect estimates remain negative for all four contrasts, but that does not establish independence or calibrated coverage.
4. **What would be needed for broader uncertainty:** credible model/family linkage and a defensible sampling/design unit, or external replication on sufficiently independent banks, neither supplied by these summaries. A naive target bootstrap would not automatically solve shared masks, duplicate families, overlapping source fits, or cross-bank model reuse.

### Additional rigor/provenance gaps

- Exact target-response duplicates are grouped for splits and primary evaluation, not removed from the source fitting pool. This prevents exact-row train/test leakage but does not establish model-family disjointness; duplicated source rows retain influence on representations and fitted nuisance models.
- `data_audit.csv` retains structural zeros/constants. For example openllm_math includes 53 zero rows (one response-equivalence group), 375 unique rows among 447, and 119 constant items. These choices materially distinguish group- from original-row weighting; zeros cannot be presumed invalid without external evidence.
- Frontier/gap stress uses full target score information for retrospective split construction. The frontier contrast is not prospective temporal/family OOD and is not a deployment selector; the optional gap stress is secondary/exploratory.
- The main runner uses the same experiment seed for source splitting and item-mask schedules (with different offsets). A five-seed grid does not establish uniform item randomization **conditional on an IID selected source split**. The mathematical unbiasedness statement requires a fixed/source-independent item design, pilot-only fitting, audit-membership independence, valid partitions, and uniform complement auditing. The saved estimator algebra supports that ideal-design statement, not a proof of exact unbiasedness of every finite runner seed grid. No actual systematic bias from seed reuse was demonstrated here.
- General sampler feasibility/partition contracts are not fully checked inside every public estimator. The saved main queries pass budget/disjointness checks, so this is a **generalization caveat, not an observed budget failure**. Equal 10/15 half-averaging at b25 remains unbiased under the ideal design but need not recover a constant-nuisance sample mean.
- No SCFD prediction falls outside [0,1] in the saved main group records or diagnostic panels; lack of clipping preserves the intended estimator. This is empirical, not a universal range guarantee. The one-direction diagnostic does produce out-of-range values (up to 68% of target groups in one main method/budget cell).
- `p95` in the macro table is the **average of per-bank/seed 95th absolute-error quantiles**, not a pooled 95th percentile or coverage guarantee. `valid_rho` counts banks with a non-null seed-averaged correlation, not independent models or all valid seed instances; here the integrity check separately reports no undefined core correlations.
- Rasch/anchor baselines must keep their existing approximation/reimplementation labels. Existing convergence and arithmetic checks cannot certify equivalence to another published model or implementation. No assertion about the unfinished stronger comparator is made.

## 7. Artifacts and reproducibility

All new files are confined to `/work/artifacts/analysis/`:

- **`independent_audit.md`** — this report, including paper-ready claims and failure tables.
- `independent_recompute.py` — standalone read-only arithmetic verification; run with `OPENBLAS_NUM_THREADS=1 python /work/artifacts/analysis/independent_recompute.py`.
- `independent_metric_verification.csv` — 2,720 independently computed metric rows from the two-bank main NPZ files.
- `independent_mask_verification.csv` — 88 independently recomputed diagnostic records, decompositions, finite-MC squared-bias correction, MSE MCSE, and covariance-naive bias MCSE for comparison.
- `independent_mask_paired_differences.csv` — 112 exploratory paired MAE/MSE contrasts with shared-mask MCSE and unadjusted normal Monte Carlo intervals.
- `independent_mask_target_bias.csv` — 528 targetwise signed errors and MCSEs; useful for detecting cancellation hidden by overall signed error.
- `independent_verification.json` and `independent_recompute.log` — summary/effect checks and numerical execution output.
- `independent_additional_checks.json` — all-main saved-query budget/fold checks, duplicate-key check, two-bank raw-file checks.
- `independent_diagnostic_truth_checks.json` — eight diagnostic truth/subset checks.

No new figures were needed; tables are embedded here and supplied as machine-readable verification CSVs. Existing manuscript plots/tables were not regenerated or edited.

## 8. Recommended future checks (not executed; no tuning recommendation)

1. If stronger bias claims at the primary endpoint are desired, preregister a **budget-50 fixed-source repeated-mask panel**, including targetwise bias, matched-mask MAE/MSE differences, Monte Carlo precision targets, and prespecified multiplicity handling. Do not infer b50 bias from b10/b100.
2. For confirmatory generalization claims, use external banks or defensible family/model-disjoint blocks with suitable metadata and preserve paired mask dependence. Keep current correlated-bank intervals explicitly descriptive.
3. In any future randomization validation, separate source-split and item-mask randomization streams and test conditional design behavior at fixed sources; preserve current losses, endpoints and saved results rather than tuning on them.
