# Post-draft reference query plan

**Status:** ready. Six queries, no retrieval run in this stage.

## Central topic
Foundational sources for a Mondrian least-ambiguous-set split-conformal procedure with gated covariate-shift weighting, evaluated against LAC, APS, RAPS and class-wise LAC on compositional (softmax) outputs.

## Why this plan
`draft_reference_gaps` reports that Related Work cites many peripheral conformal papers but none of the foundational or directly used sources. `references.bib` has no Vovk, Romano, Angelopoulos, Tibshirani (weighted) or Aitchison entries. The appendix also admits these are "stated as background without citation". Each query below maps to one gap target. Nothing is added for quantitative results, real-data literature or further applied conformal papers, which the gap memo deliberately ignores.

## Queries

### Target 1: baseline-score-sources (high, comparator)
Section: Method, "Baselines, negative controls and validity conditions". The baseline sources are split into three narrow queries so each one finds its specific paper.
1. `least ambiguous set-valued classifiers with bounded error levels` (baseline_comparator). Source for LAC.
2. `classification with valid and adaptive coverage adaptive prediction sets APS` (baseline_comparator). Source for APS.
3. `uncertainty sets for image classifiers using conformal prediction regularized adaptive prediction sets RAPS` (baseline_comparator). Source for RAPS.

Class-wise LAC is not searched separately. Class-conditional coverage papers (Ding 2023, Shi 2024) are already in the bibliography, and the Mondrian query covers the underlying idea.

### Target 2: mondrian-split-conformal-foundations (high, background)
Section: Method, "Statistical background".
4. `Mondrian conformal prediction category-conditional validity inductive split conformal foundations` (core_method). Gives a source for the "textbook" Proposition and rank argument, and for Mondrian calibration as the core of the method.

### Target 3: weighted-conformal-shift-and-compositional-framing (medium, positioning)
Sections: Method, "Weighted calibration under covariate shift"; Related Work, "Positioning".
5. `conformal prediction under covariate shift weighted exchangeability likelihood ratio` (core_method). Source for the gated weighting step and a hook for a short shift paragraph. Classifier-based density-ratio estimation is folded into this retrieval rather than given its own query.
6. `Aitchison statistical analysis of compositional data log-ratio geometry simplex` (benchmark_context). Single foundational source for the compositional framing.

## Avoided directions
- More applied, clinical, time-series or tutorial conformal papers.
- Class-/group-conditional, length-optimisation and long-tailed conformal work already in `references.bib`.
- CIFAR-10 or other real-data queries, since the paper is synthetic-only.
