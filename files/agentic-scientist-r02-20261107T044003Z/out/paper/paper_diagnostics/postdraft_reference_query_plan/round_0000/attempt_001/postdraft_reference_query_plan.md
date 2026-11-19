# Post-Draft Reference Query Plan

**Status:** ready

## Central Topic and Grounding

Position the manuscript's training-adaptive ILR ellipsoids against joint multivariate conformal prediction regions with ellipsoidal residual geometry or covariate-dependent residual scaling. Read `draft_reference_gaps.md` and `draft_reference_gaps.json` first, then checked the draft, original query-plan schema, existing bibliography, provenance, and global memory summary. Memory supplies qualitative context only, not numerical evidence.

The gap artifacts identify exactly one high-priority positioning target: `related-work-joint-region-comparators`, in Related Work's **Calibration and adaptation** paragraph (`paper.tex:58`). Its anchor is “our study instead evaluates joint multivariate membership after residual rescaling”. The study fits adaptive ILR residual geometry on training data and calibrates the joint region separately. This plan does not propose changes to that construction.

## Incremental Scope

Use **two complementary queries**, deliberately below the default range because the sole supported gap supplies only these two focused directions. Seek **1–3 directly relevant new sources total**, not per query; one source can address both directions. Stop when joint geometry and adaptation are adequately positioned in this paragraph. Do not pad the query set or refresh the bibliography.

All 25 bibliography entries have matching provenance entries. Existing coverage includes general split-conformal regression (`Lei2018`), scalar conformalized quantile regression (`Romano2019`), residual reuse (`Stone1974`, `Geisser1975`, `Barber2021Jackknife`), and covariance stabilization (`SchaferStrimmer2005`, `Chen2010`). These do not fill the dedicated joint-region positioning gap identified by the memo. Citation presence and recorded metadata/abstract reading scope are not independent full-text verification.

## Queries in Priority Order

### 1. Joint Ellipsoidal Geometry

- **Query:** `split-conformal multivariate regression ellipsoidal prediction regions residual covariance`
- **Category:** `baseline_comparator`
- **Target:** `related-work-joint-region-comparators`; Related Work, Calibration and adaptation; `paper.tex:58`, at the anchor above.
- **Rationale:** Supply a direct joint-region comparator for the transition from scalar CQR to multivariate residual membership. General split calibration and covariance-shrinkage citations cover different roles and should not be retrieved again.
- **Later verification:** Check joint response coverage, ellipsoidal score/region geometry, residual covariance construction, and separation of fitting from calibration before asserting a relationship to the manuscript.

### 2. Covariate-Dependent Residual Scaling

- **Query:** `locally adaptive conformal multivariate prediction regions covariate-dependent residual scaling`
- **Category:** `baseline_comparator`
- **Target:** The same paragraph, target identifier, and literal anchor as Query 1.
- **Rationale:** Position adaptive joint residual rescaling beyond the already-cited scalar CQR example. This complements the geometry query rather than opening a new literature family or rewrite target.
- **Later verification:** Confirm joint rather than componentwise coverage, identify what depends on covariates, and inspect the calibration construction and stated coverage assumptions. Local adaptation alone does not imply conditional validity. Deduplicate against Query 1 and all existing bibliography/provenance entries.

## Context Fields and Exclusions

Both queries concern literature-only positioning comparators. The evaluated Euclidean and isotropic ILR balls remain the experimental references; no newly found method becomes an experimental baseline. The JSON's `core_methods` and `comparators` fields capture this context. Its `benchmarks`, `architectural_shifts`, and `result_driven_themes` lists are empty because the gap analysis supports no retrieval in those directions.

Do not search broadly for conformal foundations, composition geometry, logistic-normal models, ILR, covariance regularization, or uncertainty summaries already cited. Exclude new datasets, real-data applications, structural zeros, alternative transforms, Hellinger scores, and extra calibration schemes. Do not portray jackknife+, groupwise/Mondrian calibration, importance weighting, or retrieved comparator methods as executed here. Do not imply superiority over untested methods, conditional validity, shift robustness, a demonstrated interpolation advantage, or prior use of this study's ILR transform or boundary routing.

## Bounded Follow-Up and Stop Rule

A later retrieval stage may inspect and deduplicate candidates, verify their actual constructions, and support a brief comparison of joint geometry, adaptation, and separate calibration in the identified paragraph. Retain at most three directly relevant new sources across both queries and stop once those positioning needs are met. If candidates do not support a comparison, report the unresolved gap rather than inventing a citation or broadening the search.

No references were retrieved in this stage. The manuscript, bibliography, reference provenance, gap artifacts, global memory summary, and original query plan remain unchanged.
