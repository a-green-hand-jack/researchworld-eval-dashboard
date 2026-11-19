# Rational exposure-boundary correction (v2)

The full v1 production and arithmetic audit finished successfully, but the final
scientific claim check found an implementation defect before final delivery.
A normalized sparse sum can place rational exposures on the wrong side of a
step boundary: summing17copies of1/20can give0.8500000000000002, and summing60copies
of1/80can give0.7499999999999993. Thus tail_active did not consistently describe
max(s)<=.85 and the threshold outcome/feature could exclude equality at.75.
The v1d20/node identical-data diagnostic was about.1005, inconsistent with its
mathematical event's lower bound.59755. This contradiction triggered repair,
not an effort to choose a preferred estimator ranking.

The correction computes one-hop exposure by counting treated neighbors and
then dividing by degree; isolates still use their own treatment. Step/tail
comparisons now follow the intended rational boundary. Two-hop exposure remains
the row-normalized random-walk operation on this corrected one-hop vector.
No graph, assignment/noise/prediction stream, seed, R400, mechanism, feature
basis, parameter or102-cell scientific configuration changes. Smooth-model
floating arithmetic can change, so every raw cell and exact-risk endpoint is
rerun; earlier patterns are not assumed to survive. A regression test checks
60/80inclusion,17/20tail exclusion and the isolate convention. All13scientific
checks pass before launch. The public source bytes and processed graph are
unchanged.

The original full102-cell raw outputs and arithmetic receipts are preserved on
experiment-repo's archive-roundoff-v1 branch; its exact revision is recorded in
roundoff_v1/README.md. V1 raw arithmetic audits remain true as arithmetic checks,
but are not scientific validation of the intended boundary. Original source/
launch/audit receipts are under analysis/roundoff_v1 in the delivered layout.
The v1core paperPR14must be superseded; figures and claims need corrected values.

Three independent disjoint resource shards each rerun34original cells, with
BLAS/OpenMP/MKL one thread. Sharding preserves each complete original config for
hashes and seeds; it does not construct altered sub-configs. Every cell again
produces R400all8mechanisms/9outputs and three exact one-hop endpoint risks.
Source/config launch hashes and resource references are recorded in the new
execution_manifest.json; corrected output first lives in a clean workspace.
Checkpoint source guards prevent mixed-source cells. No scientific module will
change while corrected production runs.

On completion: replace v1with corrected raw results; summarize all102cells;
repeat the complete checkpoint/raw-to-summary audits and selected four-cell
clean replay. A new independent integer-inequality checker replays all40800saved
assignments, verifying4k>=3d and20k>17d, stored support counts and exposure maxima.
It does no regression fitting. Full H1–H4diagnostics/claim maps and explicit
old/new execution accounting follow. Requests3/4/9stay open until those actual
corrected artifacts exist. This is implementation repair under the existing
scope, not a new feasibility/resource-permission request or a measured negative
result for an unrun condition.

## Completed independent boundary validation

The full boundary_audit.json now checks all102cells and40800saved assignments.
Every corrected threshold/tail active count and exposure extremum agrees with the
independent integer inequalities, using isolate self-treatment. No model fitting
was repeated by this checker.

For diagnosis, the old normalized sparse sum disagrees with the rational event in 56864 node/assignment threshold decisions and 532949 tail decisions; 14050 and 20769 assignments, respectively, have at least one disagreement. These count computations on the saved corrected assignments, across graph/design/p/noise cells; they are not independent statistical samples, performance-error rates or a direct comparison of the two complete estimator studies. The all-assignment/cell hashes and actual source hash are in boundary_audit.json. Final numerical accuracy authority additionally requires the completed summary/diagnostic audits and replay in final_execution.json.
