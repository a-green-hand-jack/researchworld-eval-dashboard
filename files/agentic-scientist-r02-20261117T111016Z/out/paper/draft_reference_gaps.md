# Post-draft citation-gap memo

**Status:** ready

One medium-priority gap warrants targeted retrieval to contextualize the existing joint-maximum and coordinatewise Bonferroni comparators within multivariate conformal prediction. No broad literature expansion or manuscript restructuring is justified.

## Grounded assessment

Reviewed `paper.tex`, `references.bib`, `references_provenance.json`, `claims_grounding.json`, `paper_data.json`, `paper_strategy.json`, and `global_memory_summary.md`. The memory summary was used only as qualitative context. All 25 distinct citation keys in the draft have bibliography and provenance entries; there are no unresolved citation keys. This checks coverage and traceability, not full-text verification of every cited claim.

The retained evidence and claims grounding identify the actual comparisons as scaled ILR, unscaled ILR, a joint simplex-coordinate maximum-residual region, and coordinatewise Bonferroni regions. They support the implementation and measured comparisons, but do not substitute for direct literature context for the multivariate comparator families.

## Retrieval target

- **Target ID:** `multivariate-rectangular-comparators`
- **Existing section:** Prediction Regions and Evaluation Targets
- **Paragraph location:** Compared region constructions, `paper.tex:85`
- **Priority:** medium
- **Citation intent:** comparator
- **Anchor:** “The latter is a simultaneous-coordinate baseline”
- **Missing literature:** Multivariate conformal rectangular regions: joint maximum-residual calibration versus coordinatewise Bonferroni calibration.

The paragraph defines the simplex-coordinate maximum-residual and Bonferroni constructions without a direct comparator-family citation. Related Work discusses quantile-regression intervals, density-based adaptation, localized conformal inference, and compositional geometry, but does not explicitly connect these baselines to simultaneous vector-response prediction regions. A targeted pass for **one or two citations** would supply that context. This is an attribution and positioning gap, not a missing validity proof or evidence that the implemented baselines are incorrect. Medium priority reflects the draft’s already substantial support for general conformal theory.

**Focused search topics:**

1. Multivariate split conformal rectangular prediction regions using a maximum standardized absolute residual score.
2. Multivariate conformal prediction contrasting joint maximum-residual calibration with coordinatewise Bonferroni intervals.

**Bounded downstream edit:** Add a short comparator-context sentence or citation clause in this existing paragraph. Cite sources only for the general constructions they actually support; do not imply that the exact simplex-coordinate implementation was taken from a paper unless verified. Do not add unevaluated methods to the experimental comparison. If a suitable source is already in the bibliography, reuse it rather than adding a redundant reference. Stop once the direct comparator context is supported; no exact publication match is asserted at this stage.

## Areas not requiring retrieval

- **General calibration and adaptive scaling:** Related Work already cites split conformal, quantile regression, density-based adaptation, localization, and selection/aggregation. The existing `Lei2018` abstract also explicitly describes locally varying prediction-band lengths for heteroscedasticity; normalized-scale adaptation is not a separate retrieval target merely because a citation could be repeated in Method.
- **Conditional and shifted validity:** `Vovk2012`, `Barber2021Limits`, `Tibshirani2019`, `Barber2023Beyond`, and `Gibbs2021` already ground the relevant distinctions. No shift-aware benchmark experiment is claimed.
- **Compositional geometry and statistical ingredients:** Existing references cover compositional analysis, logistic-normal models, ILR coordinates, ridge regression, kernel smoothing, bootstrap uncertainty, and binomial intervals. The transformed-volume versus simplex-mass distinction is explained in the manuscript rather than presented as an unsupported novelty claim.
- **Quantitative findings and implementation details:** Coverage, mass, utility, generator settings, and retained comparisons are grounded in the supplied data and claims artifacts. Additional literature citations cannot replace absent selector-only ablations, real-data experiments, alternative geometries, or structural-zero evidence; these remain stated limitations, not retrieval targets.

No reference retrieval, network lookup, or manuscript/bibliography/provenance modification was performed in this stage.
