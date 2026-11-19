# Confirmatory analysis implementation

The prospective plan is plan/protocol.md in the final integrated artifact. All204 configs use H60000 onset, evaluation every100 updates, and execution through60200 so three-sample events can begin at H. Events after H are excluded. Continuous clock ratios are undefined at zero clocks and remain explicitly flagged, not silently clipped. Conditional delays have their observed-pair denominators; fitted noncrossers retain lag/ratio lower bounds. The registered scripts enforce completeness before final interpretation.

# Registered event and uncertainty conventions

Default train-fit event: at least 99% accuracy on the full training set at three consecutive scheduled evaluations. Default generalization event: at least 95% accuracy on the entire complementary input set at three consecutive scheduled evaluations. Event onset is the first evaluation in the confirmed sequence; confirmation is recorded separately. An isolated accuracy spike does not count. We also record whether the final three evaluations exceed threshold, so an early event followed by collapse is visible. The event can be reported with the previous sampled evaluation as a lower step bound; this brackets the sampled onset only and cannot exclude unobserved oscillation between checkpoints. Threshold/cadence sensitivities must be recorded explicitly.

Noncrossings have `observed=false`, `step=null` and a censor horizon. We never assign the horizon as an observed event time. For comparisons that include all seeds, `restricted_train_time` and `restricted_valid_time` are min(event time, horizon). The explicit name matters: they describe the observed window, not the eventual event. Under a common administrative horizon, their means estimate restricted mean event times without a survival-model extrapolation. Different horizons and evaluation cadences remain distinct aggregation cells. The restricted waiting time is max(0, restricted validation time minus restricted train time). This measures fit-before-generalization waiting observed within the window; it does not distinguish 'no generalization ever' from later generalization. Conditional event-delay distributions include only observed event pairs and will be labeled as such to avoid survivor bias.

Seeds will be paired across widths with identical split and initialization seed labels. Initial parameter arrays have different shapes, so these labels do not mean identical initialized functions. Pairing primarily blocks the data-split variation, with a deterministic initialization recipe. Each seed pair is an independent replication of the full experiment. Cell summaries use percentile bootstrap intervals from resampling seed pairs/runs; width differences use paired seed-level differences and verify equal split hashes. No confidence interval will be interpreted from the n=1 exploratory pilots. Bootstrap uncertainty at small replication counts remains coarse. All validation examples belong to a finite exhaustive task domain; uncertainty is over training seeds and random splits, not an imagined population of independent validation examples. There will be no binomial test on individual pairs as a substitute for training replication.

Cell event probabilities additionally report Wilson 95% intervals over independent seed runs, which retain uncertainty even if all or none cross. One-seed continuous-metric summaries report a mean with null confidence limits, rather than a misleading zero-width bootstrap interval. Paired bootstrap event-probability differences may be degenerate if all seed-level differences agree; these should be read together with cell-level score intervals and replication counts.

# Paired binary interval, selected before confirmatory outcomes

2026-11-03, before any registered block 1100+j/2100+j is run or read.

For secondary paired incidence contrasts, use the full 2x2 paired table and a conservative exact confidence interval for the marginal probability difference. Let n_plus count (reference event=0, changed condition event=1), n_minus count (reference event=1, changed condition event=0). The difference is (n_plus-n_minus)/n. The pair, not an input example, is the replication unit.

Construct separate two-sided 97.5% Clopper–Pearson intervals for p_plus and p_minus (tail probabilities 0.0125 and 0.9875). Each discordance count has a binomial marginal over independent seed blocks; their within-block mutual exclusivity is retained in the table. Bonferroni guarantees joint coverage of the two intervals of at least 95% without assuming independence of their counts. The difference interval is [lower_plus-upper_minus, upper_plus-lower_minus]. This is a valid, conservative exact paired interval. It is wider than optimized paired-score intervals, particularly at n=8. It avoids certainty when there are zero discordances. It does not permit a claim of equality from a zero observed difference.

Implementation: `code/src/events.py::paired_binary_interval`. Uses SciPy beta quantiles with exact boundary handling at counts zero and n. Synthetic tests check no-discordance uncertainty, all-plus positive direction, all-minus negative direction. Raw paired tables accompany every reported difference. Continuous P1/P3 contrasts retain the registered paired percentile bootstrap (10000 draws, seed1701).

# Secondary reporting implementation

`cell_summary.py` computes all-run and fixed first8 cell summaries, onset and
terminal sustained counts, seed-level uncertainty, and CPU-budget sampling limits.
Terminal success uses the last declared number of selected evaluations through
execution end; onset additionally must start no later than60000. Both are reported.
Multiplication zero/nonzero validation accuracies are exact on each run's finite
subsets; their cell uncertainty resamples blocks, never individual ordered pairs.

`sensitivity.py` evaluates all12 combinations of train threshold{.95,.99}, held-out
threshold{.90,.95,.99} and persistence{1,3}, plus one primary-threshold thin2 variant.
This fully specifies the secondary recomputation before inspecting fresh results.
No best variant is selected. Thinning removes existing observations only, and its
reduced confirmation coverage near H is disclosed. Each variant retains completed
matrix counts, P1/P2/P3 results and measured-input hashes. The complete-primary
predicate remains unchanged.
