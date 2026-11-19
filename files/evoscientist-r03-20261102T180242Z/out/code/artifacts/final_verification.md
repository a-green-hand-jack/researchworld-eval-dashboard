# Final verification

## Result and scope

**The corrected secondary analysis checks out; PA5 is not fully closed because the current PDF predates one manuscript paragraph.** No stale secondary result was found in the current manuscript, its ten included tables, README, or final report. No additional scientific preprocessing/arithmetic defect was established by this verification. This is not an acceptance-readiness assessment.

Read `self_review.md` as a historical audit and `revision_response.md` as a response, then checked the current manuscript, every included generated table, analysis CSVs/JSON, preparation and data-test source, raw local parquet, saved configurations/splits/losses/diagnostics, build records and PDF text. Independently inspected the existing page-1/7/14 images. All calculations were read-only consistency checks on existing data/results, including deterministic reproduction of reported inference; no web access, estimator fitting, experiment/test reruns, manuscript/code edits, report regeneration, or compilation was performed. This document is the only intended output change. No persistent memory was updated.

Verification snapshot:
- Current `paper/paper.tex` SHA-256: `5556460950be5c205da5cd18739b91956dfb8f5fbdfbf9775e18ab5791fcbb5a`.
- Existing `paper/paper.pdf` SHA-256: `c5e855ec307f0d7962b3dd8abd4df866a6a56be7024261c389102067641bf39d`.

## PA1–PA6 disposition

| Finding | Independently checked evidence | Disposition |
|---|---|---|
| **PA1: missing-base sentinel** | `prepare.py:20–26` excludes known normalized missing sentinels while allowing genuine slash-free identifiers. Reconstructing retained metadata from the pinned local parquet finds exactly **549** literal `Removed` fields. The current grouping function reproduces every saved secondary group ID: **3,748 rows, 472 groups**. Archived graph has 381 groups; its 2,509-row giant splits into 92 repaired components. Expanded data tests cover sentinel/slash-free behavior and real owner/base edges. | **Corrected and disclosed.** Old secondary conclusions are withdrawn, flawed outputs/graph archived, and current secondary evidence is explicitly post-review exploratory corrective reanalysis. Prior inspection, unknown ancestry, inference assumptions and unspecified license remain limitations. |
| **PA2: metadata precision** | Selected MTEB metadata contain **199/278** missing adaptation fields and **three** absolute local paths. The manuscript states namespace-derived owners and excluded unusable ancestry edges; it does not certify independent families. Repaired secondary split-size imbalance is reported without the former causal attribution. | **Requested clarification closed.** Unknown ancestry remains. |
| **PA3: adequacy tail** | Code and saved policies use `1−.05/(4×2×B)`, with **B=6/5** and 2,000 draws: about **2.08/2.50** expected draws beyond the nominal quantile. Text explicitly calls this an extreme-tail heuristic, not a certificate, and retains tuning/training/small-group limitations. Only secondary seeds **23/53** select `k=4`; no MTEB split selects a non-full budget. | **Documentation correction closed; calibration validity is not repaired or claimed.** |
| **PA4: MNAR transform** | `run.py:controlled_mask` agrees with the explicit unweighted complete-training-anchor means and population SDs, floor one, slopes ±1.5 and expected—not exact realized—50% retention. | **Closed at requested reproducibility scope.** Synthetic masks/cohort differences remain limitations. |
| **PA5: build/finalization** | Corresponding-author macro is present; existing PDF has no `AUTHORERR`; provenance hashes use `seqsplit`. Existing log has **zero Overfull** and no undefined-reference warnings. Existing PDF is **16 pages**, main body ends p.7, Impact/references p.8, appendix starts p.9. Inspected images show no author error or prior hash clipping. **However, the PDF/build audit does not correspond to the latest source; see blocker below.** | **Partially closed; final-build freshness remains blocking.** Current-source pagination is not yet certified by the existing build. Submission-form obligations remain unaudited. |
| **PA6: Figure 3 reference** | `fig:stresscal` is explicitly cited in the model-uncertainty paragraph. Source scan finds no duplicate labels, undefined source references, or TODO/FIXME/TBD markers. | **Closed.** |

## Numerical and protocol cross-checks

- **Raw data/repair:** Independently reconstructed the 3,748×6 retained score matrix from local parquet filtering/sorting/deduplication; CSV values agree to `7.11e−15`. Raw parquet SHA-256 matches the manuscript. Against `pre_group_repair_hashes.json`, `panel.csv`, `groups.csv`, and `openllm_matrix.csv` match exactly; `openllm_groups.csv` appropriately differs.
- **Saved splits/configurations:** All ten saved splits agree with their model indices and group IDs; train/validation/test groups are disjoint and held-out targets are complete. Secondary group counts are **282/95/95** throughout. Secondary row counts by seed are **2946/324/478**, **2879/313/556**, **2826/464/458**, **2740/576/432**, **1498/359/1891**. All ten configurations' recorded source hashes match current source files. Comparing corrected secondary configurations/tuning ledgers with archived secondary runs confirms unchanged seeds, budget grids, primary budget, random-path count/orders and tuning candidate grids. Source retains the same metric/program-order protocol. This does not independently certify historical noninspection or immutable freezing.
- **Primary unchanged evidence:** Primary-only `per_seed.tex`, `common.tex`, `stress.tex`, and `inference.tex` match their pre-repair reference byte hashes. Shared tables appropriately differ in secondary entries. MTEB remains **2.622340 vs 4.013432** on split 11 and **3.321338±0.925711 vs 4.650394±0.802042** over overlapping splits.
- **Saved-loss arithmetic:** Reaggregating all main per-path group losses reproduces all **585** main risk-summary rows to maximum absolute RMSE difference **1.78e−15**. Recomputing both datasets' designated-split estimates, marginal intervals, paired difference intervals, sign-randomization p-values and Holm adjustment agrees to **1.78e−15** for estimates/intervals and **2.78e−17** for p-values.
- **Corrected secondary:** Split-11 trace-risk **3.931960 [3.459105, 4.434906]**, random **6.419183 [5.920806, 6.897144]**; unseen **4.815648 vs 7.861861**. Five-split values are **4.165097±0.240165 vs 6.721107±0.295732**. Paired difference **−2.487223 [−2.985465, −2.026642]**, Holm **0.000799920**. Variance/maximum-entropy Holm **0.136786**, OOF **1**, factor-with-trace-risk **0.021598**. These are exploratory, not additional primary confirmatory evidence.
- **Frozen secondary policies:** Seeds 23/53 alone select `k=4`; test full RMSE **1.589698/1.560892**, unseen **2.753437/2.703545**. Saved intervals, facts, tables and prose agree. Post-hoc test-budget minima remain separately labeled.
- **Calibration/fitting:** Secondary predicted/actual mean RMSE **4.890144/4.165097**, coverage **0.933809**, split range **0.920542–0.945165**. Factor maximum final relative change **0.004634812**, zero recorded objective increases; secondary seed 71 selects rank 4, others rank 2. Current values replace the old secondary calibration/factor summaries.
- **Tables/summaries:** All **ten** included generated tables exactly match their existing numerical inputs and formatting rules in an in-memory comparison, without rewriting anything. README and `final_report.md` report consistent primary/secondary numbers, resource rounding, two passing secondary splits and corrective chronology. Targeted old-number/prose scans found only intentional historical `381→472` disclosures or values legitimately belonging to current MTEB/other comparator rows—not stale secondary conclusions.

## Limits explicitly retained and checked

- **Six primary test groups:** minimum exact two-sided p-value `.03125` exceeds first eight-way Holm threshold `.00625`; no rejection is attainable. Overlapping splits are not independent replications; nonsignificance is not equivalence.
- **18/33 executable stress fits capped**, plus **two infeasible MCAR20 attempts**, seeds 23/53, with empty training columns. Counts independently agree with per-split logs; capped outputs remain included.
- **2/30 inner fits capped**, on MTEB seeds 53/71; all **10/10 selected main Gaussian fits converge**. Main convergence does not establish stress robustness.
- Extreme-tail conditional bootstrap adequacy remains **heuristic**, with tuning reuse, training uncertainty, dependence and small-group limitations; no MTEB non-full budget qualifies.
- **No algorithmic novelty**, unique-selector-superiority, universal small-budget guarantee, calibrated coverage or measured benchmark-execution-speedup claim is established. Metadata ancestry/independence and secondary licensing remain unresolved.

## Remaining blocking issue

### B1 — Latest source has not been built/audited

`paper.fdb_latexmk:156` records the compiled source as **61,766 bytes**, MD5 **`548203ff753b114a47edcc1aced46545`**, source timestamp **19:38:19 UTC**. Current source is **62,204 bytes**, MD5 **`d0eb5e8dc59b889ba1033f9277855157`**, timestamp **19:46:35 UTC**; the existing PDF was written **19:44:55 UTC** and build audit **19:44:56 UTC**.

This is an exactly localized difference, not merely timestamp suspicion: removing only current source **lines 149–150**, the new paragraph beginning **“The tuned MTEB training covariance has median off-diagonal correlations…”** plus its following blank line, reconstructs the recorded **61,766-byte source and its exact MD5**. PDF text lacks that paragraph. Its numbers (correlations 0.653–0.696, effective rank 4.26–4.61) agree with saved facts, so this is **not a numerical defect**. All ten table and three figure hashes match the versions consumed by the existing build.

**Consequence:** the existing seven-main-page/16-total-page result, clean log, and inspected images verify the immediately preceding source, not the latest manuscript. The compiling agent must rebuild the current source and refresh the build audit/affected-page inspection before claiming final-source build closure. No new experiments are needed. No rebuild was performed here.

## Other factual handoff discrepancies (not scientific blockers)

1. `revision_response.md` quotes **“ten passed … 4.01 seconds”**; current `artifacts/tests.txt` instead records **10 passed in 3.50s**. The pass count agrees; the response's duration is stale. No tests were rerun for this verification.
2. README and final report advertise root **`paper.pdf`**, and README advertises **`code_and_results.zip`**. Neither root file exists at this snapshot; the actual existing PDF is **`paper/paper.pdf`**. These are unresolved delivery pointers/packaging, not evidence defects; verify final copies/package after resolving B1.
3. The revision response's final-build TODO is a historical handoff, not evidence that the latest source has been compiled. The existing build audit is real but predates the exact paragraph addition above. The old self-review's flawed secondary numbers appropriately remain historical, not current manuscript evidence.

**Bottom line:** PA1/2/3/4/6 requested repairs/clarifications are verified at their stated scopes. PA5's author-error and wrapping repairs are verified on the existing PDF, but current-source finalization remains open. No acceptance/readiness verdict is inferred from these checks.
