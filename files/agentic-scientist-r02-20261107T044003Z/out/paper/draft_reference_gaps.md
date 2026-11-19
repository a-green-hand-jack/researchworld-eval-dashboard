# Draft Reference Gap Analysis

**Status:** ready

One targeted retrieval pass is justified to position the adaptive ILR ellipsoids against joint multivariate conformal-region methods; the remaining citation coverage does not warrant expansion.

## Basis and Scope

Reviewed `paper.tex`, `references.bib`, `references_provenance.json`, `claims_grounding.json`, `paper_data.json`, `paper_strategy.json`, and `global_memory_summary.md`. The draft cites all 25 existing bibliography entries, every cited key has a bibliography entry, and the provenance registry covers the same keys. This checks citation presence, not independent full-text verification. The 47 claim-grounding entries distinguish retained numerical evidence, implementation evidence, and literature support. The strategy centers a condition-dependent empirical comparison, not a new conformal guarantee. Global memory was used only as qualitative context.

## Missing Literature

Joint multivariate conformal prediction regions with adaptive residual scale or ellipsoidal geometry.

## Target: related-work-joint-region-comparators

- **Section:** Related Work, existing “Calibration and adaptation” paragraph.
- **Priority:** high.
- **Citation intent:** positioning.
- **Anchor:** “our study instead evaluates joint multivariate membership after residual rescaling”.
- **Reason:** The paragraph moves from scalar conformalized quantile regression (`Romano2019`) to the paper's joint multivariate construction without directly citing the closest joint-region family. `Lei2018` supports general split-conformal regression; `Stone1974`, `Geisser1975`, and `Barber2021Jackknife` address residual reuse and distinct calibration constructions. The covariance-regularization citations in Method support shape stabilization, not positioning against multivariate conformal regions. Neither the existing bibliography nor its provenance identifies a dedicated joint multivariate conformal-region comparator. This is a reviewer-facing gap because adaptive residual geometry is central to the manuscript's question.
- **Focused search topics:** “split-conformal multivariate regression ellipsoidal prediction regions residual covariance”; “locally adaptive conformal multivariate prediction regions covariate-dependent residual scaling”.
- **Bounded follow-up:** Seek 1–3 directly relevant sources and add a brief comparison in this paragraph distinguishing joint-region geometry, adaptation, and separate calibration. Check each source's actual construction before asserting similarity. Do not add experimental baselines, claim superiority over untested methods, or imply that any specific prior method uses the paper's ILR transform or boundary routing. These are retrieval topics, not already verified references.

## No Additional Targets

- Composition geometry and logistic-normal background already have direct citations to `AitchisonShen1980`, `Aitchison1982`, `Egozcue2003`, and `Pawlowsky2011`; their presence does not justify another broad compositional-literature pass.
- Marginal versus conditional validity, classification distinctions, and covariate-shift corrections already have direct citations in Related Work. The standard calibration argument is also cited in Method.
- Ridge fitting, covariance regularization, Wilson intervals, and bootstrap uncertainty already have method-specific citations. Implementation details are grounded in source artifacts rather than treated as unsupported literature claims.
- Reported coverage, volume, controls, and limitations are grounded in retained study evidence. They do not require external citations merely because they are quantitative or unfavorable.
- Real-data applications, structural zeros, alternative transforms, Hellinger scores, and extra calibration schemes would expand the story beyond the evaluated study and are not retrieval targets.

No references were retrieved. `paper.tex`, `references.bib`, and `references_provenance.json` remain unchanged. There is no analysis failure (`failure_reason` is empty).
