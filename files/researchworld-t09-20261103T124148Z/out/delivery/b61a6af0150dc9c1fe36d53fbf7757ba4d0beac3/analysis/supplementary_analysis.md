# Supplementary accuracy evidence: definitions and claim map

These definitions accompany the corrected complete study. Completion is established by
production_audit.json, summary_audit.json, diagnostics_audit.json and final_execution.json,
rather than by this specification. The frozen matrix is configs/production_manifest.json.
No estimator or mechanism is selected by its apparent accuracy.

`scripts/analyze_results.py` complements the main `gatebench.summarize` outputs.
It reads executed Parquet cells and performs no new model fitting. Full mode
requires every planned cell; `--partial` is only checkpoint inspection. The
full outputs are results/diagnostics/, separate from the standard summary.
For the paper delivery layout use `--root .` from the delivery root; it detects
code/configs automatically. In the analysis development repository use the same
command with PYTHONPATH=src. The complete source/input hashes accompany outputs.

* diagnostics_by_graph.csv: every mechanism/model/cell; empirical error SD,
  finite/estimable fractions, mean conditional bias, mean b(z)^2, mean oracle
  variance, weights, prediction errors, coverage, exposure/event diagnostics.
  The Monte Carlo residual error^2-[b(z)^2+v(z)] checks the total MSE identity;
  error-b(z) checks the bias identity. These residuals have sample mean/MCSE,
  not an asserted exact zero in a finite Monte Carlo sample. Diagnostic means
  have normal95% Monte Carlo bounds; coverage and event rates use Wilson95%.
  `oracle_to_iid_variance_ratio` is the mean per-assignment v(z)/||a(z)||^2,
  distinct from a ratio of means; m and covariance are simulation-known.
* prediction_gate_pairs_by_graph.csv: every regression versus linear in the
  same mechanism/cell, using actual pairing_id and shared noise/assignments.
  `delta_mse` is model squared-GATE-error minus reference squared error;
  `delta_prediction_mse` and `delta_prediction_mean_mse` analogously compare
  fresh-assignment outcomes and the oracle mean. Positive means worse for the
  model. Contradictory signs indicate that a prediction ranking and a GATE
  ranking differ, with uncertainty inspected before claiming a reversal.
  Every metric preserves its finite-pair denominator; total and jointly
  estimable counts remain visible. It does not rank an undefined return as zero
  error or treat unsupported minimum-norm predictions as identified endpoints.
* support_coupling_by_graph.csv: paired linear/hidden_tail DGPs for every model;
  observed P_hat(max s<=.85), Wilson interval, equality of returned estimates
  on this event, target gap, and both empirical risks with MCSEs. The field
  empirical_two_risk_bound is gamma^2*P_hat(E)/4, a sample diagnostic; the
  separate analytic regular-graph bound is results/support_bounds.json.
  This bound concerns a fully defined shared estimation rule. A partially
  defined Hajek's finite-pair risks do not satisfy an unconditional risk claim;
  its defined_pair_fraction is retained and the analytic risk interpretation
  must not be applied to its conditional-success subset.
* independent_contrasts_by_graph.csv: cluster-minus-node for every available
  panel and rho1-minus-rho0 on matching graphs/designs. Masters are retained.
  Distinct design and cross-panel streams are independent. Each Monte Carlo SE
  is sqrt(SE_A^2+SE_B^2); these are not replicate-paired contrasts. The graph
  matching is only used to retain the per-graph contrast before averaging
  across graph seeds. All finite-return/estimability fractions are supplied.
* graph_inventory.csv: actual processed graph counts/degrees/partitions and
  adjacency hashes, deduplicated across experiments on the same fixed graph.
* exact_ht_risk.csv: exactly evaluated one-hop HT risk, including log10 variance
  and RMSE, three endpoint families per cell. no_interference has its own
  endpoint family; linear/quadratic/cubic/sigmoid/threshold share `linear`;
  hidden_tail has its own. Twohop has no one-hop unbiased-risk identification.

Each *_by_family.csv weights graph summaries equally and supplies a t interval
across independent graph draws, with its actual graphs-defined count. A public
single graph has no graph-population interval. error_sd_graph_mean is the mean
conditional SD, not a pooled SD; defined_fraction_graph_mean is the mean of
per-graph defined-return fractions. Family coverage and prediction metrics have
the same conditional/operational rules as graph metrics. With only five graph
draws, intervals are modest descriptive uncertainty rather than broad topology
validity. Heavy-tail Monte Carlo RMSE/normal intervals cannot replace exact HT
risk even when all observed estimates happen to be the same.

## H1–H4 evidence routes (analysis outputs, not promised findings)

H1 uses summary/performance_by_graph.csv and diagnostics for matched linear,
quadratic, cubic, twohop and supported threshold fits. Compare degree4/20/80
at n2000 and n2000/n8000 at degree20, then graph-level uncertainty. The MSE
identity applies to minimum-norm weights too, but matched unbiasedness requires
estimability. Noise variance alone is not a sufficient misspecification metric.

H2 uses paired prediction/GATE differences and the support-coupling outputs,
plus the quadratic contrast under p.5 versus the focused p.2/.8 conditions.
Keep no_interference/linear and matched-response controls. Do not presume
quadratic misspecification must produce signed bias at half allocation, or that
more flexible fitting improves global endpoint recovery.

H3 uses design contrasts plus exposure spread, cluster count/retained edges,
validity and mean oracle variance. Design effects change the experiment's
assignment distribution as well as support; no universal benefit is presumed.
ER/SBM/BA contrasts change multiple graph properties and are descriptive.

H4 uses twohop DGP with linear versus twohop fits; rho1/rho0 independent-panel
contrasts; HC3 and oracle coverage with denominators; exact HT risk versus its
finite-run tail illusion; and supported versus unsupported threshold fits.
Correlated noise has unit marginal variance and a specific local covariance,
so its direction cannot be inferred merely from rho being positive.

## Selected clean reproduction

`scripts/replay_selected.py` copies source into a clean workspace and reruns
regular n2000/degree4 and degree80, graph seed201, both designs, originalR400
streams. These four cells were selected by structural extremes, not by measured
success. It compares every scientific dataframe column exactly, including all
errors, diagnostics, seeds and failure states. The actual receipt is
notes/reproduction_audit.json (analysis/reproduction_audit.json in paper layout).
The corrected replay receipt reports actual elapsed time and all115200rows with
original/replay Parquet hashes. It is a selected-cell clean replay, not an independent
implementation, full102-cell replay or graph-population test. Source hashes distinguish
the corrected launch, summaries and replay. Superseded v1 replay/checkpoint history
is in roundoff_v1/; it has no corrected numerical authority.

## Final numerical audit

After the production job supplies all102cells, its exact-risk files and standard
summaries, `scripts/finalize_results.py --root .` runs the complete raw checkpoint
audit, supplementary analysis and raw-to-summary audit sequentially, recording
stage wall/CPU and child high-water RSS in postprocessing_timings.json. The
raw-to-summary audit independently recomputes finite/estimable error moments,
coverage denominators, within-cell paired moments and equal-graph means/t
intervals, and checks planned graph/family counts and source/input hashes. It
also verifies all306exact-risk rows and their source JSON hashes. This is an
internal arithmetic/provenance check, not an independent research implementation
or independent review. A script being supplied does not mean its full-data audit
has run; the completed receipt is notes/summary_audit.json when actually produced.

## V2 scientific-boundary validation

The v1 arithmetic audits reproduced stored outputs but did not validate the rational support boundary. The final check found normalized sparse sums could cross .75/.85 at equality. All102cells/exact-risk outputs are regenerated with counts before division under the same configs/graphs/streams. The v1diagnostics are superseded, even where the arithmetic was correct. The finalization now additionally runs audit_boundaries.py against every40800saved assignment, with exact4k>=3d and20k>17d comparisons. The corrected clean replay and source/input/summary audit receipts establish their actual completion. The13scientific checks include the explicit boundary/isolate regression test. See exposure_boundary_correction.md and execution_manifest.json for authority and recorded jobs.

## Supplementary arithmetic audit

`audit_diagnostics.py` independently recalculates raw conditional decomposition
moments, support coupling/denominators, all independent-stream contrast values and
MCSEs, every supplementary equal-graph family mean/t interval and claim selectors.
Its actual receipt is diagnostics_audit.json. It does no fitting or model selection
and remains an internal arithmetic check, separate from independent review.
