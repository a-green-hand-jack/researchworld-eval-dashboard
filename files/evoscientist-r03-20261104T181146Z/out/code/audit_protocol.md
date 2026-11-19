# Independent protocol/code audit

**Scope:** `/work`, completed artifacts as inspected; protocol/code audit only. No web access, delegation, source edits, reruns of experiments, new efficacy tests, favorable-test selection, or retuning. The only requested deliverable created is this report. Line references are 1-based and relative to `/work`.

## Executive verdict

1. **The primary MTEB >=3-feasible-organization-split gate FAILED: 1/5 passed. All MTEB results, including seed 37, are descriptive only.** Neither random-row results, native coverage, stress results, nor OpenLLM can restore the original confirmatory claim.
2. **A claim of prediction over the full 62-task MTEB suite is unsupported.** The source matrix has 62 columns, but each evaluated MTEB split uses only **12 tasks: 8 candidates and 4 never-acquired audit targets**. Across the five organization splits, the union is just **15 panel tasks and 6 audit tasks**. Ingesting 62 columns is not evaluating 62 prediction targets.
3. **OpenLLM has actual metadata-defined revision-group overlap across partitions**, in addition to exact score-vector duplication. Its cohort-size gates passing does not establish independent unseen-model transfer. Treat existing transfer results as contaminated with respect to that independence claim, not as a replacement primary study.
4. The current code and prediction archives support **train-only fitting, inductive low-rank inference, identical fixed-audit support, and averaging random-policy losses rather than averaging random predictions**. I found no direct test-score input into fitting/tuning/anchor selection in the current runner.
5. Native-cohort deployment selection optimizes a broader coordinate set than its scored deployment loss. This invalidates an **observed-support-aligned deployment-objective interpretation**, not the stored fixed-audit errors of the implemented policy. Several optional selected budgets also have no native-cohort evaluation record.

A **full, honest feasibility/descriptive paper remains viable**, with standard-method framing, negative or inconclusive results allowed. A full confirmatory success paper, full62-task claim, or clean independent OpenLLM transfer claim is not supported by these artifacts.

## 1. What was audited and checked

Read the requested `src/data.py`, `src/cohorts.py`, `src/models.py`, `src/run.py`, entire parsed `protocol/manifests.json`, `plan.md`, and `experiment_log.md`. Also cross-checked `success_criteria.md`, `protocol/frozen.json`, `protocol/cohort_counts.txt`, `tests/test_contracts.py`, processed matrices/provenance/schema, local OpenLLM parquet metadata, representative local MTEB archive records, final run reports, CSVs, and prediction archives. Used the local paper-review skill's protocol-audit and calibrated-evidence guidance; this is not a manuscript/literature review.

**Numeric coverage:** all **20 final base runs**, all **18 registered stress runs**, their **38 validation CSVs**, and all **40 base prediction archives**. Superseded smoke artifacts were not pooled into final analyses. The 38 loss CSVs contain **753,404 records**, and validation CSVs contain **429,344 records**. Archive reconstruction covered **736,340 base loss records** in **3,454 prediction arrays**. These are stored records, not independent observations; dense/native cohorts and repeated splits overlap.

**Deterministic checks passed:** no duplicate `(cohort, model, method, k)` keys, nonfinite/negative loss fields, unexpected final method sets, unexpected budget supports, or row-support mismatches; all manifest ID orders match the processed matrices; no row-index overlap across partitions; no normalized organization overlap for organization splits. MTEB role hashes and train-only eligibility rules match the manifests. All three checksums in `protocol/frozen.json` match current contents.

Reconstructed fixed-audit NMSE from archived predictions agrees with CSV NMSE to maximum absolute difference **9.20e-7** (maximum difference divided by `max(1, abs(CSV loss))`: **2.30e-7**), consistent with float32 prediction storage. All archived anchors are distinct, available candidate coordinates, with exactly k anchors; audit labels are never anchors. Same-anchor low-rank/Gaussian comparisons match exactly. The mean baseline is flat in k; maximum k=0 cross-method loss spread is **2.84e-14**.

These checks establish current artifact consistency, not historical proof that all choices preceded test access. No superiority effect sizes, p-values, CIs, or plots were computed in this audit. Tables below summarize protocol facts, not selected predictive wins.

## 2. Claim-blocking defects and required invalidation/restriction

### P0-A — Primary feasibility/repetition gate failed

**Evidence:** `plan.md:35-37`; `success_criteria.md:19-22`; `src/cohorts.py:44-63`; `experiment_log.md:6`. The manifest's per-split `confirmatory` field records local feasibility, not overall study eligibility.

| MTEB organization seed | Train rows / groups | Dense validation rows / groups | Dense test rows / groups | Per-split gate |
|---|---:|---:|---:|---|
| 11 | 146 / 45 | 23 / 10 | 28 / 13 | Fail: test rows <30 |
| 23 | 150 / 57 | 22 / 10 | 26 / 10 | Fail: test rows <30 |
| 37 | 146 / 45 | 27 / 12 | 32 / 9 | Pass |
| 53 | 139 / 55 | 34 / 12 | 21 / 6 | Fail: test rows/groups |
| 71 | 143 / 46 | 18 / 13 | 19 / 12 | Fail: validation/test rows |

Manifest evidence: `protocol/manifests.json:1111-1124`, `2246-2259`, `3377-3390`, `4500-4513`, `5616-5640`; compact counts also appear in `protocol/cohort_counts.txt:1-5`.

**Invalidation scope:** all confirmatory MTEB C1 claims, including a seed-37-only analysis. The numerical evaluations need not be discarded. Preserve all five preset splits and identify the fallback panels and failed gates. Do not lower thresholds, replace seeds, select the favorable split/budget, or promote a secondary dataset.

**Recommendation:** make feasibility failure a headline design result. Use all five fixed splits for explicitly descriptive reporting; any interval on that aggregate is not the registered accepted-split confirmatory estimand.

### P0-B — full62 task claim unsupported by the implemented support

**Evidence:** `src/data.py:8,45-48` describes ingestion; `src/cohorts.py:37-46,59-63` selects panels; `src/run.py:103-104` immediately restricts the matrix to `m['panel']`; `src/run.py:61,73-77` scores only panel audit tasks. Example 12-task panel: `protocol/manifests.json:6-20`; seed 37: `2265-2279`.

All ten MTEB manifests have `nc=8` and 12 panel columns. Each dense primary loss therefore averages **4 audit tasks**, not 62 tasks and not all 12 panel tasks. Native losses use **2-4 observed audit tasks**, fixed per row. Larger source coverage and predictions on acquired coordinates do not expand this support.

**Invalidation scope:** any full62 reconstruction/transfer/benchmark-budget-reduction claim; any claim that k=8 completes 62-task evaluation. Existing results describe selected, coverage-conditioned 12-task panels with a four-task fixed audit evaluation. Even the observed-only deployment metric concerns that panel, with policy-dependent unmeasured targets.

**Recommendation:** title, abstract, tables, captions, and conclusions must state the 8-candidate/4-audit setting. A valid source-data statement is: “A 279-model × 62-task source matrix was ingested; experiments used split-specific 12-task panels.” Do not silently extrapolate from 15 unique organization-panel tasks or 6 unique organization-audit tasks to the full suite.

### P0-C — OpenLLM revision/alias separation is not enforced, and collisions exist

**Evidence:** `src/cohorts.py:9-17` groups only the normalized name prefix (or literal row ID); `src/cohorts.py:24-30` deduplicates only `fullname`, then discards `Model sha` and `Base Model` before splitting. This does not implement the metadata-connected grouping required by `plan.md:31-33` and `success_criteria.md:17`. The pinned local parquet contains these metadata fields; the issue is not their complete absence.

After the declared precision/fullname selection, there are **4,497 rows**, **4,451 distinct `Model sha` values**, and **54 duplicate six-score rows beyond the first occurrence**. Every organization split has train/test overlap in `Model sha`:

| OpenLLM organization seed | Shared train/test SHA values | Train × test row pairs sharing SHA | Train × test pairs with identical six-score vectors |
|---|---:|---:|---:|
| 11 | 5 | 6 | 4 |
| 23 | 5 | 8 | 2 |
| 37 | 4 | 5 | 1 |
| 53 | 5 | 5 | 1 |
| 71 | 6 | 7 | 2 |

Counts are within-split cross-partition pair counts, not independent contaminated models or an estimated bias magnitude. They use retained metadata rows from `data/raw/openllm.parquet` and the frozen manifest indices. Same-score pairs and same-SHA pairs are separate diagnostics; equal scores alone do not prove model identity.

**Concrete revision collision:** `gpt2` and `openai-community/gpt2` share SHA `607a30d783dfa663caf39e06633721c8d4cfcd7e`. In organization seed 37, row indices 2693 and 3698 are train/validation respectively; in seed 53 they are test/train. Their scores differ slightly, so deduplicating only identical score vectors would not solve revision-group separation. Corresponding manifest objects: `protocol/manifests.json:49185-68179` and `68180-87145`.

**Invalidation scope:** certification of zero revision-group overlap and clean unseen-model/alias-independent transfer for existing OpenLLM splits. The stored numbers remain descriptions of these dependent leaderboard rows; no claim is made here about the sign or size of bias, or that every shared SHA proves identical deployed weights.

**Recommendation:** quarantine the independence claim and record the overlap. Any corrected grouping experiment requires a separately versioned future protocol and genuinely untouched evaluation data for renewed confirmation. Do not post-hoc remove suspicious test rows and relabel the remainder pristine. MTEB has no exact duplicate full canonical rows in this matrix and no detected exact cross-partition panel duplicates, but its unimplemented alias graph remains an independence limitation, not evidence of a clean family split.

### P1-A — Native deployment objective and evaluated deployment support disagree

**Evidence:** `src/run.py:58-64` supplies only available candidates and observed audit targets, but `src/models.py:57` sets the deployment objective's residual set to **every matrix coordinate not acquired**, ignoring that availability mask and the passed targets. In contrast, `src/run.py:74-75` scores deployment error only on **observed** unacquired coordinates.

Thus native `greedy_deploy` and its same-anchor `lowrank_greedy` can select anchors to reduce posterior uncertainty on historically missing candidates/audit tasks that do not enter the reported deployment loss. This is not target-value leakage. It is a different objective from observed-support-aligned native deployment selection. Across the five MTEB organization native cohorts, **84/210 row appearances** have incomplete panels; across both regimes, **182/429** do. The mismatch is therefore exercised, not merely hypothetical. This count does not assert every affected row's selected path would change.

**Restriction scope:** withdraw any claim that those native paths greedily optimize the reported observed-support deployment objective. Dense-cohort paths are unaffected because all panel tasks are observed. Native fixed-audit losses still correctly evaluate the implemented full-panel selector on paired observed targets. Random, audit-only greedy, and correlation paths do not have this particular full-coordinate residual-set issue.

**Recommendation:** report the implemented full-panel objective explicitly, separate it from observed-support error, and avoid using native deployment curves as validation of an availability-aware objective. Any future implementation change must first receive synthetic/train/validation contract checks; no repair or rerun was performed here.

### P1-B — Resolved test lock and exposure history cannot be certified from these artifacts

**Evidence:** `src/cohorts.py:67-68` freezes only plan, criteria, and manifests. It does **not** hash source, processed data, transforms, fitted covariance/factors, tuning results, paths, or selected budgets as required by `success_criteria.md:7-10`. `src/run.py:108-127` tunes and selects budgets before evaluation within the same process, which is good data flow, but `src/run.py:129-134` writes the reports only **after** evaluation. The comment at `src/run.py:131` mentions covariance, but the report contains diagnostics, not the fitted covariance/factor arrays. Existing `_done.json` alone causes an unconditional skip (`src/run.py:100-102`), without verifying source/data/config hashes or quick/full mode.

There is also concrete pre-lock label materialization: `src/data.py:58` writes the first two rows, including task scores, into the purported schema artifact. `data/processed/openllm_schema.json:39-82,123-170` identifies the rows and exposes raw/display scores. Those rows later occur in held-out partitions: in organization seed 11, `0-hero/Matter-0.2-7B-DPO` is validation and `01-ai/Yi-1.5-34B` is test; in seed 23 both are test. This is broader than a score-free schema inventory, even though `experiment_log.md:7` reports only schema/range-check exposure.

**Restriction scope:** current code inspection does not demonstrate test-based tuning, and writing a label-containing artifact does not prove a human used it to choose a method. Nevertheless, a sealed-test/exposure-free history is not established. Do not call this externally preregistered or a cryptographically verified pre-test fitted-pipeline lock. Retain descriptive status and disclose the schema-head exposure. Hash agreement now proves current consistency, not freeze chronology.

**Recommendation:** preserve existing history; document known exposures and missing lock components. Future runs should verify content-addressed source/data/config identity and seal fitted choices before test access. Do not retrofit a newly generated hash as historical evidence.

## 3. Core mechanics that passed the audit

### Leakage and inductive inference

- Training rows alone enter standardization, covariance, and factor fitting (`src/run.py:103-108`; `src/models.py:5-23,62-74`). Task eligibility/coverage ordering uses the training partition (`src/cohorts.py:35-39`). Test masks determine only declared feasibility/availability cohorts (`src/cohorts.py:47-62`). Revision/coverage canonicalization uses global metadata/masks; it is not a test-performance selection rule.
- Gaussian tuning uses the validation audit loss and the declared lambda grid; the chosen lambda is shared by the main Gaussian selectors (`src/run.py:14-22,36-46`). No current-code test-loss-driven choice was found.
- Low-rank loadings are fit on training cells, with missing entries masked out of the objective and normal equations (`src/models.py:63-71`). Inference solves `u=(B_A^T B_A + alpha I)^(-1) B_A^T z_A` from that row's acquired labels only (`src/models.py:76-82`). No test-row factor co-fitting or other-test-row score input occurs. Three initialization predictions are intentionally averaged; this is distinct from random-policy averaging.
- `lowrank_random` and `lowrank_greedy` use exactly the Gaussian random and G-deploy anchors respectively (`src/run.py:49-51`), verified in all base archives. `lowrank_dopt` is a separate training-factor-based selector (`src/models.py:39-48`), not an isolated imputer comparison.

### Candidate/audit pairing and target support

- C/T roles are disjoint; MTEB hash roles are permanent across splits, though selected membership changes with training coverage (`src/cohorts.py:37-46`). An audit task is never selectable.
- Every dense policy/k uses exactly the same row and audit-cell support. Native eligibility is fixed before evaluation at the largest reported native k, and every policy uses the same per-row observed audit set (`src/cohorts.py:61-63`; `src/run.py:61-77,123-127`). Native per-row equal task weighting differs from globally equal task weighting because task availability varies.
- Dense G-deploy explicitly excludes acquired coordinates from its posterior residual trace (`src/models.py:57-58`). There is no evident retained-pre-acquisition-self-variance or double-subtraction bug. The fixed ridge means measured posterior variance need not be exactly zero, but the trace explicitly excludes it.
- `deployment_nmse` is **not paired in target support across policies**: its residual candidate set changes with anchors (`src/run.py:74-75`; `plan.md:94`). It cannot establish fixed-target C1 or be pooled with audit NMSE.

### Random expected losses, not average predictions

`src/run.py:11-12` creates 50 nested random permutations. Evaluation filters each permutation by availability, preserving nested prefixes and uniform permutation restriction (`src/run.py:63,69-76`). It computes squared errors separately per path and then averages **losses**. Tuning does the same (`src/run.py:19-21,30-32`).

Correct quantity: `E_path[mean_t (prediction_path,t - truth_t)^2]`, **not** `mean_t (E_path[prediction_path,t] - truth_t)^2`. Reconstruction across all archived random/low-rank-random arrays confirms the former. Among **77,398** nontrivial per-row/path-bank checks, **77,376** have a strictly positive Jensen gap >1e-8 between these quantities, so substituting averaged predictions would generally change the estimand. No such substitution was found in saved NMSE.

The 50 paths are Monte Carlo repetitions of a policy, not 50 independent test cohorts. Random-bank Monte Carlo uncertainty is separate from organization sampling uncertainty.

### Missingness and units

- Historically missing labels remain NaN; they are not fabricated as targets. Mean-filled covariance is explicitly a baseline (`src/models.py:11-12`), while masked factors use zero storage only inside a masked objective, not as observed zero labels.
- Stress deletion touches training only, before recomputing means/SD/covariances and retuning (`src/run.py:85-108`). Propensity weights use original train coverage; synthetic MNAR weights use original train score ranks. Using those train labels to generate synthetic missingness is declared, not test leakage. One seed-derived uniform array couples deletion rates; panels and dense evaluation truth remain fixed. This does not identify accuracy on historically unreported labels.
- MTEB extraction takes a unique finite English test `main_score`, enforces [-1,1], selects a single model version by coverage, and enforces a modal dataset revision per task (`src/data.py:27-45`). The retained matrix is **279 × 62**, with **9,882 observed cells (57.13%)**, no duplicate `(model,task)` provenance records, no retained unknown dataset revisions, and one dataset revision per task. Local representative records had proportion/correlation-scale main scores. These checks do not certify every evaluator/configuration as identical.
- OpenLLM correctly uses `* Raw` proportions, without `/100`, and constrains them to [0,1] (`src/cohorts.py:27-30`). The processed **4,497 × 6** matrix has all **26,982** cells observed. The documented pre-model conversion correction (`experiment_log.md:7`) is consistent with present code. No current 100-fold unit error was found.
- Inverse-scale errors use train SD correctly (`src/run.py:73`). `raw_mse` is squared canonical-score error, **not RMSE**. Do not label it RMSE without specifying the square-root aggregation. MTEB's accepted range includes negative correlations; do not describe every source metric as an accuracy or a 0-1 probability.

## 4. Limitations and incomplete protocol elements, not blanket invalidations

### P1 — Low-rank convergence limits weaken baseline-completeness claims

`src/models.py:62-74` stops at 200 iterations and logs convergence; `src/run.py:28-33` permits nonconverged bounded fits in validation selection. Replaying only the already-saved deterministic validation choice rule (no fitting or new selection criterion) shows selected MTEB organization seed 11 and 37 configurations are rank 1/alpha .01, with **all three starts reaching 200 iterations without convergence**. Seed 53's rank 1/alpha .1 has one of three starts nonconverged. See `results/mteb_organization_11_done.json:1223-1250`, `results/mteb_organization_37_done.json:1223-1250`, and `results/mteb_organization_53_done.json:1246-1273`.

This is a valid disclosed fixed-compute baseline, not transduction. It does not demonstrate competitiveness against an optimized/converged low-rank solution. Preserve those runs and convergence flags; do not improve the baseline retrospectively and relabel the same test pristine. All selected OpenLLM fits were convergence-flagged, but its alias issue remains.

### P1 — Budget-selection logic is validation-only, but native application is incomplete

`src/run.py:114-121` implements the declared smallest-k-within-one-bootstrap-SE rule, including k=0, at each policy's validation minimum. I recomputed **every saved budget, validation minimum, and SE** from all 38 validation CSVs; they agree. The 500 resamples estimate the conditional SE used for this heuristic, not a 95% test confidence bound or calibrated per-model risk. No test-minimum budget selection was found.

However, selection ranges over dense-validation k up to 8 (MTEB) or 3 (OpenLLM), while native curves stop at 4 or 2 (`src/run.py:111,126`). Examples: MTEB organization seed 37 random selects k=6 (`results/mteb_organization_37_done.json:66-70`); organization seed 11 correlation selects k=6 (`results/mteb_organization_11_done.json:21-25`); OpenLLM row seed 23 random selects k=3 (`results/openllm_row_23_done.json:66-70`). No native result exists at those frozen budgets. Do not silently cap, substitute nearest k, or drop unsupported rows/policies for a stopped-native table. This does not invalidate dense selected-budget or fixed-k results. Also label train mean as spending zero labels even when its flat audit curve is displayed at larger k.

### P1 — CV terminology and uncertainty must remain narrow

These are **five repeated grouped train/validation/test holdouts**, not disjoint K-fold or nested cross-validation (`src/cohorts.py:12-18,33-35`). Rows/organizations recur across seeds. Validation is reused for hyperparameter selection and the optional global budget heuristic; its fitted-pipeline SE does not include that selection or refitting uncertainty.

The audited runner does not implement the final 2,000-draw cross-split organization-cluster CI or final equal-split aggregation specified in `plan.md:91-96` and `success_criteria.md:27-52`. Its 500-draw validation budget SE is not a substitute. This audit does not assert that no separate downstream analysis exists; it certifies no such analysis outside the inspected scope. Any paper intervals should resample organization IDs jointly across repeated split appearances, preserving methods/budgets/pairing and equal split weights. Report conditional descriptive intervals and all split directions, not independent-split t-tests or task/path pseudo-replication. Additional superiority tests require a predeclared family and Holm correction; otherwise remain descriptive. No such tests were introduced here.

### P1 — Some planned comparisons/checks are missing or not fully auditable

- `plan.md:76` promises complete-training-row covariance when >=40 rows and the intentionally wrong retained-pre-acquisition-variance diagnostic. Neither appears in `src/run.py:36-52`. Complete-training-row covariance is actually feasible in all ten MTEB base manifests (**76-95 complete training rows**), so absence cannot be called infeasible. This limits a “all planned ablations completed” claim, not validity of existing contrasts.
- `plan.md:68` also requests a standardized-variance tie reference; only original-unit variance is configured (`src/run.py:109`; `src/models.py:38`). The high-variance baseline is unit-dependent, as intended, not standardized covariance diagonal ranking.
- Training duplicates are **counted, not removed** (`src/run.py:133`), contrary to `plan.md:31`. Three MTEB organization panels have one duplicate training row each; OpenLLM training duplication is larger. Some panel duplicates may reflect identical sparse observed information, not proven model identity. Record the weighting/protocol deviation without test-informed exclusions.
- `success_criteria.md:59` requires a strongest comparator chosen on validation before test lock for C2. No explicit chosen-comparator lock is emitted by this runner. Reporting every baseline is fine; picking the strongest/favorable comparator from test ranks is not a confirmatory C2 test.
- Four synthetic tests exist (`tests/test_contracts.py:7-38`), but they do not exercise the full runner's native mask/objective agreement, metadata alias grouping, or random expected-loss pipeline. The audit's archive checks add evidence, not a retrospective proof of prospective test coverage. Condition numbers requested in `plan.md:58` are not logged by the current code.
- Canonical acquisition ties in `success_criteria.md:80` are not followed literally: `src/models.py:38,48,59` uses panel indices/first argmax, and panels are ordered by coverage/hash rather than canonical task ID. This is deterministic and not observed test-driven selection, but should be recorded as a deviation, especially for identity/diagonal ties.

### P2 — Genuine scientific boundaries

- Dense cohorts are selected for reporting completeness; native cohorts are also mask-informed and coverage-conditioned. Training-derived task coverage ordering is disclosed, not representative task sampling. Task-type round-robin was omitted and logged (`experiment_log.md:8`), leaving narrow, correlated panels with several STS tasks.
- Native MTEB organization counts are 38/48/37/40/47 rows from 18/13/13/10/19 organizations; these are secondary overlapping cohorts, not new independent replications or evidence on unobserved targets. OpenLLM native and dense cohorts are identical rows, with identical losses at common k, because all processed task scores are observed. It provides no independent native-missingness validation.
- Organization names are imperfect independence proxies even apart from the verified OpenLLM revision collisions. MTEB alias/family linkage is unresolved; random-row splits do not isolate unseen-family inference. Different split regimes also select different panels/cohorts, so their contrast is descriptive, not a controlled causal estimate of organization shift.
- [-1,1] acceptance and matching dataset revision are not a full per-task metric-direction/configuration/evaluator-version registry. `src/data.py:30-35` trusts `main_score`, and retained provenance omits `mteb_version` even though local raw records contain that field (sometimes null). No actual incompatible-unit cell was established; schema harmonization beyond these checks remains unverified.
- Unsupported covariance pairs are zeroed at overlap <20 and PSD repair is explicit (`src/models.py:18-23`). Base reports show zero unsupported pairs; stress reports reach 11.11% unsupported entries and 15.64% relative pre-renormalization PSD repair. These are estimator diagnostics, not recovery guarantees. Large but finite stress losses were retained; do not trim difficult test rows or compare NMSE across deletion levels without acknowledging changed retained-training scales and showing raw-unit errors too.
- Stress runs include only the six Gaussian/mean variants and three fixed organization seeds (`src/run.py:110,142-144`); do not claim full low-rank robustness. Synthetic deletion and equal label counts do not measure actual benchmark evaluation cost, causal MNAR correction, calibrated predictive uncertainty, or adaptive acquisition. Paths are static given training estimates and availability, not score-adaptive.

## 5. Metrics and safe reporting definitions

The audit checked the following stored quantities (`src/run.py:73-77`):

- **NMSE:** per row, mean squared audit error in train-SD-standardized units; dense targets are the fixed four audit tasks (three for OpenLLM). Native targets are that row's fixed observed audit subset.
- **raw_mse:** per-row mean squared audit error after restoring canonical score units. **MAE:** corresponding mean absolute error.
- **deployment_nmse:** standardized squared error on observed unacquired panel coordinates, averaged per row; policy-dependent target support, secondary only.
- **Random-policy loss:** arithmetic mean of each loss over 50 nested permutation paths, not loss of their averaged prediction.
- **Feasibility counts:** retained row and unique normalized-organization counts per partition; pass thresholds are jointly applied, then the study requires >=3/5 organization splits.
- **Budget SE:** sample SD of 500 organization-cluster-bootstrap validation loss replicates at that policy's validation-minimum k, conditional on fixed fits.

For a later descriptive paper, retain the predeclared core arithmetic mean over k=1,2,4 for MTEB (k=1,2 for OpenLLM), not best k and not a logarithmic AUC. Define `Delta = L_G - L_random` and `I = 1 - L_G/L_random`, report both with appropriate paired conditional uncertainty, and suppress unstable ratios when baseline loss <=1e-12 (`success_criteria.md:27-52`). Failure of the feasibility gate does not disappear if either effect estimate is positive. Do not pool OpenLLM and MTEB or use deployment error as the same estimand.

## 6. High-priority actions and next experiments

**For the current paper, without changing code or choosing new tests:**

1. State the failed primary gate and descriptive-only status prominently; report all five fixed organization splits and all declared final conditions, including negative/inconclusive findings. Interpret `manifest.confirmatory` as local feasibility only.
2. Remove full62, family-independence, clean OpenLLM revision-separation, availability-aligned native deployment, and calibrated stopping claims where unsupported. Explain the exact 8/4 task support and the verified overlap/exposure/lock issues.
3. Keep existing results and deviation history intact. Separate fixed-audit paired evidence from policy-dependent deployment errors and overlapping native cohorts. Include convergence flags, missing planned ablations, and fixed-compute baseline caveats rather than presenting incompleteness as infeasibility.
4. If downstream analyses are supplied, independently verify their paired cross-split clustering, equal weighting, raw-unit aggregation, frozen-budget joins, and multiplicity handling. This audit made no new inferential selections.

**At most three future, separately versioned experiments; none performed here:**

1. **Metadata-connected independence evaluation:** construct and audit alias/revision connections from available metadata, establish zero cross-partition connected-group overlap before fitting, and evaluate on genuinely untouched models. This resolves the concrete OpenLLM separation failure without test-score-similarity filtering.
2. **Prospective support/feasibility study:** freeze the intended task universe, roles, reporting masks, and >=3-split gate on a new evaluation cohort. If 62-task prediction is the intended claim, collect/identify untouched ground truth supporting that task coverage; otherwise explicitly retain the smaller-panel estimand. Do not redesign the old panel based on accuracy.
3. **Native-objective and bounded-factor validation:** first use synthetic/train/validation contracts to check availability/support consistency and convergence behavior under a fixed future compute budget, then test the preregistered resulting pipeline only on fresh held-out data. Such work must not retroactively upgrade existing comparisons.

**Exact defensible current scope:** a reproducible, standard-method, coverage-conditioned feasibility/descriptive study of whole-task acquisition for held-out leaderboard rows, with narrow 12-task MTEB panels, four fixed audit tasks per dense split, preserved failed seeds, and explicitly qualified secondary native/missingness evidence. OpenLLM can illustrate the implemented pipeline and its limitations, but its current splits are not certified independent-model transfer. A full paper can report these findings without a positive result or a new-algorithm claim.

## 7. Artifact and inspection fingerprints

**Produced:** `/work/audit_protocol.md` only. Its tables are protocol/sanity summaries; no figures, efficacy tables, edited source, or changed experiment outputs were produced.

SHA256 at inspection:

```text
src/data.py               7bbfcdacdcc373440c719e33c81cd12b767e1a798730b4811c6e7484d224d8df
src/cohorts.py            63f1f91fdcf275e7bc19b0fad90d6e4d7bf2482188750e64ac2a691d767a6bd0
src/models.py             4def16669315629ebf3047de96185ee98923260a55a390dacbcb86b80d6273ea
src/run.py                930aef93e78601079dd98ab00b82d11203c4b357bc8f74cd2c50e3eafd0cb283
protocol/manifests.json   50197b9132cbc253603f6ce3bff1ae397c51d7a8cbdb3e6f0155e612e0c800d8
plan.md                   91954df400a71d083d22ac33d66e780fae5f9bcc459ec86b84236be9e0fd31bd
experiment_log.md         484041b80272883e1fed9760cd1269f66b00381b9bd18d828b96a493b5c21006
```

These are audit-time identifiers, not evidence of prospective registration. No claims are made about literature novelty, paper text not inspected, source-wide schema certification, or historical human decisions beyond the documented evidence above.
