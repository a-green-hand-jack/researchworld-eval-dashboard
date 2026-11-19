# Post-draft incremental reference query plan

**Status:** ready

## Topic and scope

Supply direct multivariate conformal context for the existing joint simplex-coordinate maximum-residual and coordinatewise Bonferroni comparators in the study of scale-adaptive split-conformal regions for observed positive continuous compositions. This is an attribution and positioning task, not a literature refresh, a new experiment, or a missing validity proof.

The primary drivers, `draft_reference_gaps.md` and `draft_reference_gaps.json`, identify exactly one medium-priority target: `multivariate-rectangular-comparators`. The bounded destination is **Prediction Regions and Evaluation Targets → Compared region constructions**, `paper.tex:85`, anchored by “The latter is a simultaneous-coordinate baseline”.

**Budget: two focused queries, aiming for one or two citations total.** The single gap and its two explicit search topics justify fewer than the default three to six queries. Both queries address the same paragraph, but distinguish joint-score construction from coordinatewise multiplicity correction. A single source supporting both constructions can close the gap; do not seek one new reference per query.

## Grounding and existing coverage

Reviewed the two gap artifacts first, then `paper.tex`, `references.bib`, `references_provenance.json`, `global_memory_summary.md`, and the schema and exclusions in `reference_query_plan.json`. The memory summary supplies qualitative context only, not numerical or bibliographic evidence.

The existing bibliography contains 25 entries with provenance. General conformal foundations and regression calibration are already represented by `Vovk2005`, `Papadopoulos2002`, `Lei2018`, and `Angelopoulos2021`; the draft also cites adaptive scalar-interval work including `Romano2019` and `Sesia2020`. These are context, not evidence that the specific multivariate comparator families have already been directly attributed. The provenance records for these entries report abstract, overview, or metadata-level reading rather than verified full-text support for this paragraph. Do not infer that these sources lack relevant material: downstream, reuse an existing entry if its actual content supports the needed construction before adding a redundant reference. Deduplicate any new candidate against existing titles and DOI/arXiv identifiers.

## Queries

### 1. Joint maximum-residual rectangles

- **Query:** `multivariate split conformal rectangular prediction regions maximum standardized absolute residual score`
- **Category:** `baseline_comparator`
- **Rationale:** At `paper.tex:85`, directly contextualize the vector-response rectangular region obtained by jointly calibrating a maximum absolute residual score. A standardized-score formulation is relevant family context, but the implemented **Simplex max** comparator is unscaled; verify that the source supports the unit-scale specialization. This fills a specific comparator-attribution gap rather than repeating a general split-conformal or adaptive scalar-interval search.
- **Acceptance boundary:** Support must concern simultaneous vector-response regions and joint maximum-score calibration. Cite only verified general constructions; do not imply that the exact simplex-intersected implementation was taken from the source. Reuse an existing suitable bibliography entry where possible.

### 2. Coordinatewise Bonferroni versus joint calibration

- **Query:** `multivariate conformal prediction simultaneous prediction intervals coordinatewise Bonferroni joint maximum residual calibration`
- **Category:** `baseline_comparator`
- **Rationale:** At the same paragraph and its simultaneous-coordinate anchor, directly contextualize separate coordinatewise calibration at miscoverage `alpha/K` and distinguish it from a jointly calibrated maximum-residual threshold. This is the multiplicity/simultaneous-coverage aspect of the gap, not another search for adaptive marginal intervals.
- **Acceptance boundary:** Prefer a source explicitly discussing both constructions; complementary sources can support them separately. Do not claim an efficiency ordering, a new validity theorem, or publication of the exact compositional implementation. One source satisfying both queries is enough.

## Context deliberately not queried

- **Core methods:** Independent split calibration and maximum standardized ILR residuals already have general conformal and compositional support; no additional core-method search is planned.
- **Comparators:** The targets are exactly the joint simplex-coordinate maximum-absolute-residual region and separate coordinatewise Bonferroni intervals intersected with the simplex. The scaled and unscaled ILR comparisons remain unchanged.
- **Benchmarks:** The existing synthetic logistic-normal and Dirichlet IID and shifted evaluations supply context only. No dataset or benchmark-context gap was identified.
- **Architectural shifts and result-driven themes:** No incremental queries are justified. Citation additions cannot establish selector-only effects, conditional or shifted validity, uniform efficiency superiority, or results on unevaluated data or geometries.

## Exclusions and stopping rule

Preserve the original plan's exclusions: no attempt to identify or retrieve the prohibited study or derivative material; no broad joint compositional-conformal discovery, citation-network expansion, cited-by traversal, related-paper recommendations, or unrestricted survey crawling. Keep searches in the separate multivariate-conformal neighborhood without compositional benchmark terms. Do not introduce classification, image/text datasets, latent probabilities, alternative geometries, structural zeros, neural architectures, or architecture transfer as evaluated settings. Do not present weighted conformal, jackknife+, quantile-regression conformal, credal, clustered, or multivalid methods as implemented comparisons. Avoid generic optimization, benchmarking, writing, chronology, or internal scoring searches. Do not search to support unsupported conditional-validity, shift-robustness, superiority, or selector-causality claims.

Do not reopen already-supported calibration, adaptive scaling, compositional geometry, conditional/shifted validity, statistical ingredients, or benchmark topics. Stop once one or two verified sources, including suitable existing entries, directly support both comparator families. The only intended downstream manuscript edit is a short context sentence or citation clause in the existing paragraph; no new experimental method, section, or manuscript reframing is needed. An unsuccessful targeted pass should leave this positioning gap unresolved rather than expand the search or imply support.

No reference retrieval or network lookup was performed. The manuscript, bibliography, and provenance are unchanged.
