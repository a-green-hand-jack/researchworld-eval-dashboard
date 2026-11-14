# Independent technical audit of analysis-v1

Inspected experiment-repo **f558276d110ab218150edb4bc8e4d6a145998eb7** (main; release analysis-v1). This is an analysis audit, **not approval of a report/release/final PR**. No such version has been proposed to me and no final figures or PDF exist in the inspected paper-repo main.

## Standard and scope

Read internal-review-repo#1 and all five frozen inputs; commitment is internal-review-repo#3. Read idea-repo wiki Brief. The study must answer the investment question using justified definitions and reproducible public scores, with supported claims, uncertainty and explicit applicability/failure conditions; the full paper must meet the selected latest official venue format and frozen deliverable.md. No predetermined ordering is required. The prohibited prior work was neither sought nor encountered.

Read analysis scripts, tests, method/proof notes, primary/robustness findings, provenance/audit files, saved primary and sensitivity results and reproduction instructions. Evaluated the five rules, cardinal/ordinal tie handling, partial-gain and observed-ceiling scenarios, co/strict first, normalization/cohort changes, random baselines and composition sensitivity.

## Independent evidence

- Downloaded all **60** source files (**8,966,877 bytes**) using the delivered acquisition code; every frozen manifest hash matched. Re-ran preparation in a private copy. All **7** processed files reproduced byte-for-byte, including all four matrices and the data audit. Evidence: `analysis-v1-data-reproduction.json`.
- Wrote an independent verifier that imports no study optimizer, recomputes aggregates from the entire modified matrix, and fully reranks Borda rivals. Checked all **3,950 HELM** co/strict cases plus **600** seeded cases across the three six-task cohorts. **2,741** feasible witnesses passed; **1,809** infeasible cases remained unsuccessful even with every task upgraded (a valid infeasibility certificate by coordinatewise monotonicity). For the **600** six-task cases, direct full-matrix enumeration in increasing budget independently confirmed the minimum or infeasibility. No mismatch. Evidence: `analysis-v1-checks.json`, generator `../scripts/audit_analysis_v1.py`; seed 9182. Job job-647e9e9671 succeeded (27.907 measured elapsed seconds, 28.198 CPU seconds).
- Re-ran the delivered independent 11-task exhaustive suite: **120** analytic/MILP comparisons passed, with ties, zeros, co/strict and partial/full improvements. This is complementary validation, not a claim that I independently re-solved all 278,055 saved optima.
- Recomputed primary medians from saved rows: HELM mean/median/geometric/minimum/Borda **16/21/16/11/46**, Open LLM **2/3/3/3/6**; raw Open LLM **2/3/3/5/6**, unique-model cohort **2/3/3/3/6**. Cohorts are 79, 4,575, 4,575 and 4,496 respectively.

## Technical judgement

The additive-gain cardinal solutions, odd-median threshold count, exact even-six-task enumeration and Borda MILP formulation support their stated score-intervention optima. The Borda constraints correctly include each rival's loss as well as the target's gain. Pruning rivals below initial maximum minus n is valid: an initial maximum can lose at most n, and an excluded rival cannot gain. Half-integral Borda strictness is handled separately. Stored solver statuses distinguish infeasibility from unresolved work; inspected diagnostics report none unresolved.

The main conditional conclusions are supported. Unit selected-task cost counts support size, with fixed rivals, independent nonnegative target-score changes and no collateral effect. It measures neither attainable contamination effects nor examples, money, compute or training effort. It also does not permit direct training-effort comparison between 57 subjects and six task families. Published normalized Open LLM scores and raw scores are distinct representations: the minimum-rule change is material. Full cohorts, common challengers and rule-specific reachable subsets must remain distinct. The empirical Borda-versus-mean comparison is not a universal ordering theorem.

Uncertainty interpretation is appropriate: deterministic finite-cohort optima need no invented model-sampling intervals; Monte Carlo intervals concern random task orders, and HELM task-resampling ranges are composition sensitivity, not test-score or causal-effect confidence intervals. Model families/subjects are dependent. No item-level repeated evaluation evidence is supplied to infer score uncertainty.

## Actionable finding F1

**Random-baseline estimand versus unreachable-target handling.** `scripts/analysis.py` calls `random_baseline` only when an optimal feasible subset exists. Consequently infeasible targets have null random stopping means; `scripts/summarize.py` averages only reachable targets although summary n is the full cohort. Methods instead define E[min(T,n+1)] and call n+1 an explicit infeasible censoring code. Restricted-gain random means therefore need either explicit reachable-only labels/denominators or full-cohort n+1 values. Primary full-gain comparisons are unaffected, because all targets are reachable. Raised as **world/experiment-repo#4**, with instructions to notify paper and presentation owners. Until corrected, do not compare these restricted-gain random means as full-cohort quantities.

## Handoff and remaining review

Analysis audit request internal-review-repo#2 is answered by this record; F1 remains a separate owner request. No other actionable optimizer/cohort/uncertainty defect was found at this revision. This does not certify uninspected report claims, novelty/related-work coverage, figure/table renderings or final reproducibility integration. Those, all objective requirements and any outstanding findings will be checked at the exact proposed paper-repo version head before approval. A later analysis change requires review of the changed material.
