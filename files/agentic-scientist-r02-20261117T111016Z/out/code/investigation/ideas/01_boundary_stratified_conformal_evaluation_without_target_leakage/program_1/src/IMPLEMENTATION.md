# Boundary-aware training-only adaptation

The only executable entrypoint remains `program.py:handle`. The specification,
array encodings, response keys, fixed ILR basis, output bounds, and state
transitions are unchanged. The model uses only the supplied training responses.
It neither identifies query roles nor updates during prediction.

## Implemented

- A fixed observable regime `x[:, 0] >= 0` and its covariate interactions enter
  the ridge design. Pairwise feature interactions supplement the starter's
  linear, quadratic, and sine terms. Feature clipping at 12 is fixed in advance.
- Four-fold training cross-validation selects the center ridge penalty from
  0.1, 1, 10, 100. The largest penalty within one percent of the minimum training
  cross-validation MSE is selected. The reset seed only randomizes training folds.
- Out-of-fold center residuals, rather than optimistic full-fit residuals, are
  used for scale regression. For fewer than eight training rows, full-fit
  residuals are used with the strongest penalty; no cross-fitting is claimed.
- Predicted-boundary scale features are computed from the fitted center alone.
  If `p = softmax(center @ basis.T)`, the proxy for coordinate `j` is
  `0.5 * log(sum_k basis[k,j]^2 / p[k])`, with inverse probabilities capped at
  `exp(30)`. This is a heuristic inspired by log-composition variance growth near
  the boundary, not a fitted Dirichlet likelihood or a theorem. Dividing these
  proxies by three fixes their feature scale.
- Scale ridge penalties 10, 100, 1000, 10000 are selected on training log-absolute
  residual MSE using the same fold scheme. Center residuals are cross-fitted,
  but this second selection is not a nested independent risk estimate: no such
  estimate is reported. Scales remain within the starter's bounds.

## Contract limitations

The planned pooled-versus-Mondrian, Euclidean/Hellinger/pseudocount-CLR,
structural-zero, count-response, latent-vector, and reference-mass experiments
cannot be implemented through this interface. The harness owns calibration and
the standardized-ILR maximum-score region. It supplies positive compositions
with dimensions three or eight, not the proposed closed-simplex synthetic
responses with dimensions three or ten. No alternative scores, group-specific
calibration thresholds, membership diagnostics, or proposal draws are returned.
In particular, adding a sign feature to scale regression is **not** Mondrian
calibration and provides no group-conditional coverage guarantee.

Conditionally on a frozen training fit, ordinary split-conformal marginal
response coverage still relies on the harness applying the exact independent
calibration rank and on calibration/test exchangeability. Feature-dependent
scales do not supply a covariate-shift guarantee or certify latent probabilities.
This candidate does not assert any of these unsupported conclusions.

## Validation status

This stage permits source editing and static inspection only. No candidate,
test, experiment, external literature retrieval, or evaluation was executed.
There are no measured results, paper/PDF, uncertainty estimates, or claimed
improvements. The full preregistered core and optional sensitivity runs remain
unexecuted. All numerical settings above describe implementation choices, not
observations. The harness will perform the official evaluation after submission.
