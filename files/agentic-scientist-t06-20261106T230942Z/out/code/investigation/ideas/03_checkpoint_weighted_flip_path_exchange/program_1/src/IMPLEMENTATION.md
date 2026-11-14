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

## Checkpoint-local complete-path refinement

The width-two search above is retained unchanged as the incumbent generator.
Its complete returned path is scored first using the same lexicographic sum of
checkpoint displacement, inversions, and smooth inversion potential. Duplicate
budgets retain their original multiplicity in that sum. This internal objective
is not assumed to equal the harness's combined score.

The optional search considers both selected-position swaps and replacements by
unused original binary rows. For a swap at zero-based positions `left < right`,
only budgets `left < budget <= right` change; for a replacement at `position`,
only budgets `budget > position` change. Unaffected checkpoint scores are reused.
The fitter and its convergence check are unchanged; each new prefix set is fitted
with the original ridge and baseline warm start. Request-local caches use sorted
original-row tuples, not dataset identities, ordering-dependent keys, or influence
predictions. Equivalent design types only screen proposals and identify the
lowest-index unused representative; they do not replace original-row cache keys.

Screening uses current fitted rank gaps in the existing smooth potential and the
original fitted inverse Hessian. Each sweep samples up to 24 evenly spaced path
positions plus checkpoint boundaries. At a position it screens all selected
partners and one unused representative of each binary design/outcome type,
then exactly scores the best screened swap and replacement when available.
Strict complete-score improvement alone permits acceptance. The sweep restarts
after acceptance with a rotated position cursor so it visits other sampled
positions before repeatedly revisiting the same position. This is heuristic
screening, not exhaustive exchange optimization or an optimality certificate.

After the incumbent is fully scored, optional work is capped at 128 proposals,
72 additional converged refits for dimensions at most 64 (24 otherwise), and a
two-second soft deadline checked before proposals and uncached fits. An ongoing
fit is not interrupted; the deadline is not a hard total-runtime guarantee.
Proposal screening and traversal are deterministic, but the deadline can truncate
the accepted search prefix differently under different machine loads.
Incomplete/nonfinite proposals are never compared as complete scores. Numerical
or optional-search failure returns the best fully accepted path, or the original
incumbent if none was accepted. No cache, counters, scores, or errors extend the
public response. Actual returned paths are checked for uniqueness, original-row
bounds, binary outcomes, and coverage of every requested checkpoint.

The live refinement path includes small synthetic prefix-set checks for every
swap and replacement on a four-row path, including repeated checkpoint budgets.
These compare local updates against full checkpoint prefix-set recomputation;
they are structural checks, not scientific data or independent fitter validation.

## Validation status

Only static source inspection was permitted during preparation. No candidate
code, tests, benchmarks, optimizers, or evaluation was executed. Runtime,
numerical agreement with an independent fitter, and scientific effectiveness
remain unmeasured; the harness owns the subsequent evaluation. No external
literature or prohibited research source was accessed.
