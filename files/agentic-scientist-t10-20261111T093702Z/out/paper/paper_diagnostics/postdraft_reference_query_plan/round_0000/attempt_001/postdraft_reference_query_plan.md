# Post-draft reference query plan

**Status:** ready. There are 5 queries covering the 3 gap targets in `draft_reference_gaps.json`.

**Central topic:** Can confidence intervals for a population mean be shortened beyond PPI++ at valid coverage when labels, unlabeled data and predictor are fixed? The method adds a cross-fitted isotonic/binned recalibration as a second control variate. The queries fill only the gaps the draft exposes. The comparator family (PPI, PPI++, cross-PPI, stratified PPI and variants) is already well cited, so it is not searched again.

## Queries

### 1–3. Control-variate / efficiency positioning (high priority, Related Work)
Anchor: "The control-variate form of PPI has antecedents in semi-supervised mean estimation".

The headroom result (R² = η² when E[Y|Ŷ] is in the feature set) restates semiparametric efficiency results. The bibliography has Zhang 2016, Xu 2025 and Chernozhukov 2017. It has no AIPW, missing-data efficiency or classical control-variate source.

1. `augmented inverse probability weighting semiparametric efficient estimation of a mean with missing outcomes` (core_method). This is the foundational AIPW and efficient-influence-function literature.
2. `optimal control variate coefficient variance reduction estimated coefficient regression estimator` (core_method). This covers classical control variates and regression estimators, including the cost of estimating the coefficient. It supports the framing of PPI++ as a control-variate estimator.
3. `prediction-powered inference relation to augmented inverse probability weighting efficient influence function` (baseline_comparator). This looks for work that links PPI to AIPW, so the paper can say how its ceiling differs from known results.

### 4. Benchmark pool provenance (medium priority, Method / evaluation protocol)
Anchor: "a plankton-imaging pool whose label and prediction are both binary".

4. `plankton imaging dataset image classification; Amazon deforestation forest cover remote sensing dataset; protein intrinsic disorder AlphaFold; gene expression sequence-to-expression dataset` (benchmark_context). The plankton pool and the three search pools have no sources, and the introduction's remote-sensing motivation is uncited. Galaxy Zoo and the census pools are already cited. The retriever should split this into one lookup per dataset and keep dataset-origin papers only.

### 5. Isotonic regression for continuous outcomes (low priority, Related Work / Calibration)
Anchor: "Isotonic and binned maps from scores to outcome probabilities are standard calibration tools".

5. `isotonic regression monotone conditional mean estimation recalibration of regression predictions` (core_method). The cited calibration papers cover probabilities only. The method and the η² estimate use isotonic fits for continuous outcomes. One or two foundational references are enough.

## Deliberately not pursued
- Post-selection or adaptive interval selection. The draft says plainly that the 1% fallback has no guarantee, so this would be speculative expansion.
- More PPI variants. The uncited off-topic bib entries (credit risk, cardiac, soil, microbiome and similar) should not be extended.
- Active labeling, which violates the fixed-label constraint.
- Any search aimed at the withheld published paper.

No retrieval was performed in this stage.
