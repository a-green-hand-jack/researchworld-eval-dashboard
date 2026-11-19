# Draft reference gap analysis

**Status:** ready. There are 3 targets, and only the first is high priority.

The PPI comparator family in Related Work is already well cited. It covers PPI, PPI++, cross-PPI, stratified PPI and about a dozen variants. The quantitative claims are grounded in `paper_data.json`, so none of them need citations. The gaps below are the ones where retrieval would materially help.

## Missing literatures
- Control variates and augmented / efficient estimation with missing outcomes (AIPW, semi-supervised mean estimation).
- Provenance of the PPI-style benchmark pools.
- Isotonic regression and recalibration for continuous outcomes.

## Targets

1. **control-variate-efficiency-positioning** (Related Work, high, positioning)
   - Anchor: "The control-variate form of PPI has antecedents in semi-supervised mean estimation".
   - The thesis rests on PPI++ being a control-variate estimator and on a headroom formula (R² = η² when E[Y|Ŷ] is in the feature set). That formula restates semiparametric efficiency results.
   - The paragraph has only two semi-supervised citations and one DML citation. Classical control variates and AIPW / missing-data efficiency theory are uncited, so reviewers will likely ask what is new.
   - Search topics: AIPW semiparametric efficiency for mean estimation with missing outcomes; optimal control-variate coefficient; relation of PPI to AIPW.

2. **benchmark-pool-provenance** (Method, evaluation protocol, medium, benchmark_context)
   - Anchor: "a plankton-imaging pool whose label and prediction are both binary".
   - The plankton pool and the search pools (Amazon deforestation, gene expression, protein disorder) have no sources. The intro's remote-sensing and galaxy-morphology motivation is also uncited. Only Galaxy Zoo and the census pools are cited.
   - Search topics: plankton imaging dataset; Amazon deforestation dataset; gene expression sequence-to-expression dataset; protein disorder with AlphaFold.

3. **isotonic-recalibration-regression** (Related Work, Calibration, low, background)
   - Anchor: "Isotonic and binned maps from scores to outcome probabilities are standard calibration tools".
   - The cited calibration papers address probabilities. The method and the η² estimate use isotonic regression for continuous outcomes.
   - Search topics: isotonic regression for conditional mean estimation; recalibration of regression predictions.

## Not pursued
- Post-selection / adaptive interval selection. The draft states plainly that the 1% fallback rule has no guarantee, so this would be speculative expansion.
- More PPI variants. Several bib entries are not cited in the text (credit risk, cardiac, etc.) and are off-topic. The strategy file says not to cite them.
