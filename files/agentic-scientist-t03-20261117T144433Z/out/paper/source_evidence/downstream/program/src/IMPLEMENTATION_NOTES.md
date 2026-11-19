# Budget-matched coalition design

## Implemented scope

The entrypoint remains `program.py:handle`. Its only responses are the original
`{"ok": true}`, `{"masks": ...}`, and `{"phi": ...}`. Reset erases the live
explanation; start creates or replaces it; observe consumes it. Seed and stream
initialize all randomness. Input/background fields remain opaque: the supplied
interface owns masking, fitted preprocessing, and probability evaluation.

The candidate changes the coalition design, not the estimand or regression.
Empty and full coalitions remain first and second. Exactly the requested number
of rows is returned, including duplicate rows and endpoints; no hidden model
calls or extra observations are used. Observe uses the starter's identical
efficiency-constrained, equal-weight least-squares solve and tolerance.

## Sampling method

For dimension d, combine sizes s and d-s into an unordered complement stratum.
Its probability is proportional to 2/[s(d-s)], except the central size in even
dimensions, whose weight is 1/[s(d-s)]. Randomized equal-probability strata of
the cumulative distribution reduce variation in size counts. Randomly permute
the selected sizes and choose uniform subsets within each size. Remember chosen
unordered complement pairs until that size's finite population is exhausted,
then start another cycle. Random orientation restores the original distribution
over individual masks. Each mask has the original kernel marginal distribution;
the masks are intentionally not independent within a run.

Complementary observations constrain the odd part of the coalition response
together and can reduce Monte Carlo variability. However, their regression
design rows are negatives of one another, so they do not provide two independent
design directions. If N is the interior row budget, use at most
min(floor(N/2), max(0, N-2(d-1))) pairs. The remaining rows are individually
sampled from the same stratified distribution. Thus pairing alone cannot reduce
the number of potentially distinct directions below min(N, 2(d-1)). This is
rank headroom, not a guarantee of full rank; the original least-squares rule
still handles singular designs. All mask generation is local to start, with
no cross-explanation cache of coalition values or other run observations.

This design is a variance-reduction hypothesis, not an accuracy guarantee.
Kernel marginals alone do not imply unbiasedness of a finite-sample regression
coefficient, nor universal improvement from pairing. Neither repeat agreement
nor exact efficiency establishes attribution accuracy or causal validity.

## Interface limitations and unperformed work

The interface does not expose a prediction callable, dataset identifiers,
training controls, original row identifiers, timing of black-box evaluation,
or independently queryable reference values. Consequently this candidate cannot
implement the proposed fixed-model Pima/ACS exact-reference study, German Credit
reference ensembles, prediction-row cap calibration, package-based SHAP calls,
background-resampling experiments, clustered reliability bootstrap, or empirical
paper. The background length is visible, but is not evidence of how many model
rows the external implementation actually evaluated. No such measurements or
artifacts are fabricated, and no diagnostic keys are added to the response.

No experiments, tests, literature searches, package installations, or evaluations
were run during this implementation stage. In particular there are no measured
reliability claims, performance results, verified official conference templates,
or completed paper deliverables. Only static source inspection was authorized.
