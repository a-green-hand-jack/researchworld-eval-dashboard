# Interface-compatible scope

The starter's only input is an inline float64 table of participant indices,
outcomes, and a home covariate. Its only intervention is a nested sequence of
distinct binary outcome flips. This implementation does not reinterpret flips as
deletions and does not infer dataset identities, prompts, annotators, response
identities, or clusters from anonymous rows.

Consequently the proposed matched human/GPT-4 study, whole-question deletion,
real-data acquisition, cluster bootstrap, supported-ordering intervals, random
deletion controls, and paper production are not implemented. The stage forbids
the acquisition and experimental runs needed to support those claims. No
empirical results, confidence guarantees, or causal judge-type claims are made.

## Implemented adaptation

- The sum-loss, fixed-ridge Bradley-Terry objective and optional home nuisance
  are unchanged. Half-win ties remain in every fit and are never selected.
- Sufficient statistics aggregate equal design rows without deleting or
  deduplicating genuine observations. Each selectable unit remains one original
  binary observation. Grouping by design and original outcome permits exact
  accounting of flip capacity while avoiding a dense observation-by-parameter
  matrix.
- Fits use damped Newton steps with Cholesky solves, an L-BFGS fallback, and a
  stationarity check. Flips change win sufficient statistics, not observation
  counts or ridge strength. Every candidate ordering used in search is refitted;
  no first-order shift is treated as a finite-change ranking.
- A deterministic width-two search adapts priorities at the three requested
  checkpoints. Branches include the prescribed frozen contrast and up to six
  currently close, baseline-oriented participant contrasts. Closeness is only a
  search heuristic, not a confidence interval. Branches are compared by summed
  exact rank displacement across checkpoints, then inversions, then a smooth
  inversion potential. The original fixed-influence path is retained as a
  candidate. This is bounded heuristic search, not an optimality certificate or
  a claim of a successful reversal.
- All public influences, eight audit derivatives, and three predicted shifts
  still use the original fitted Hessian and the documented frozen contrast.
  Predictions are linear approximations even though search uses exact refits.
  Internal search scores never appear in the response.
- Reset, upload, analyze, and download responses and the float64 result layout
  are unchanged. The implementation is self-contained in `program.py`; this
  document is not required at runtime.

## Validation status

Only static source inspection was permitted during preparation. No candidate
code, tests, benchmarks, optimizers, or evaluation was executed. Runtime,
numerical agreement with an independent fitter, and scientific effectiveness
remain unmeasured; the harness owns the subsequent evaluation. No external
literature or prohibited research source was accessed.
