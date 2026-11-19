# Measured pilot and frozen production proposal

This is a feasibility/correctness report, not the production accuracy evidence.
See `pilot_timings.csv` for every measured cell and `pilot_budget.json` for exact
arithmetic. `configs/production_manifest.json` and its three named configs freeze
the proposal; launching remains subject to the independent feasibility judgement.

## What was actually measured

The initial pilot used14 graph/design cells with R20, eight mechanisms and nine
estimator outputs (seven regressions, HT and Hajek). It covered regular n2000,
d4/80, and n8000,d20 at graph seeds101/102, plus the full4039-node SNAP graph.
Per-cell timing includes graph generation/partitioning, sparse noise construction,
endpoint truth, fit/HC3/oracle diagnostics, an independent experimental assignment
for prediction, and Parquet plus JSON output. Total cell wall22.0593s and
CPU20.8617s; maximum reported process RSS300432KiB. Time ranged0.560–2.191s.

An extension uses ER, SBM and BA n2000/mean20 at two pilot graph seeds and
full SNAP, rho1, both designs, R20. Production-sized memory calibration uses
n8000/d20 regular and full SNAP, rho1, both designs, R400, pilot seed101. This
checks accumulating the intended400-replicate output frame rather than assuming
20-replicate memory scales harmlessly. All actual timings are in the CSV.
No hyperparameter tuning is performed: spline knots, degree, partition target,
noise and response parameters are fixed. The pipeline evaluates all intended
estimators rather than timing a cheaper proxy. Pilot master seed89103 is separate
from production masters2202601/2202602/2202603 and synthetic graph seeds201–205.

The separate exact HT audit covered all14 initial pilot cells: total wall44.8265s,
CPU44.7115s, maximum process RSS395332KiB. Largest cell wall12.1462s (n8000,
cluster assignment). It uses exact joint probabilities, all node pairs blockwise,
and long-double exponentiation; it does not estimate rare tails by more Monte
Carlo. Risk file `results/pilot/ht_risk_audit.json` contains the measured outputs.

## Proposed bounded production and cost arithmetic

Core72cells: five graphs each of regular n2000 d4/20/80; ER n2000 mean20; SBM
n2000 mean20 with eight blocks and85% expected edges within; BA n2000 m10;
regular n8000 d20; one full SNAP graph with covariate/partition seed201, each under
node Bernoulli(.5) and fixed BFS-cluster Bernoulli(.5). Thus36graph instances.
ER-vs-SBM and BA-vs-regular are compound topology comparisons, not uniquely
identified interventions on community strength or degree heterogeneity.

Noise22cells: regular n2000 d20 and SBM at all five graph seeds, plus SNAP,
both designs, rho1. Imbalance8cells: regular n2000 d20 seed201 and SNAP,
both designs, p.2/.8. Core/noise/imbalance all use gamma1, R400, all eight
prespecified mechanisms and all nine outputs. Total102cells,326400 experimental
outcome datasets,326400 fresh prediction-evaluation datasets,2937600 estimator
rows. Shared features/assignment make retaining the extra mechanisms relatively
cheap; all are nonetheless in measured full-pipeline timings.

Exact HT evaluation computes three endpoint families per cell: no interference,
standard endpoint effect, and hidden-tail endpoint effect. Linear/quadratic/cubic/
sigmoid/threshold share the same global endpoints, so the same exact risk applies
to all of them under one-hop sufficiency. No one-hop unbiasedness is asserted for
two-hop outcomes. Worst measured exact-risk time is applied to every cell and
all three endpoint families for a deliberately conservative projection. Monte
Carlo projection uses the larger of the slowest measured R400 cell and the
slowest R20 cell times20, then multiplies by102. The report doubles their sum
for runtime contingency; `pilot_budget.json` is the executable arithmetic.
This is a planning estimate, not a measured production runtime. Two days remain
reserved within the one-week objective for integration/reproduction/review.

## Resources, checkpointing and output plan

Every run sets BLAS/OpenMP/MKL threads1. Per-cell output is atomic: completed
Parquet is reused, incomplete temporary output is recomputed; config mismatch
in the same directory is rejected. All seeds are derived by SHA256 namespace,
with graph and replicate identities retained. The long resource job prints
progress every100of400 replicates, emits wake lines at checkpoints/stages, and
records timing/RSS and graph summaries. One sequential job is initially planned
because host CPU placements exceeded physical CPUs at inspection. More concurrent
independent shards are possible if the host has headroom, without changing seeds.
Summarization streams one cell at a time; raw3million-row concatenation is avoided.
Raw public graph bytes are hash-checked before each graph construction. Source
hashes/config hash accompany production cells.

Measured RSS is far below3GiB headroom. R400 calibration covers accumulated output
memory. Peak RSS is process cumulative maximum, not an isolated per-cell delta.
Exact risk uses128-row blocks and full sparse covariance. Files remain small:
production Parquet storage is projected from measured calibration compression,
with only a few MB of numerical summaries; raw source data are downloaded rather
than redistributed. Full final output sizes will be measured and reported.

## Validity and the pilot's useful failures

`tests/test_identities.py` has six scientific checks: direct endpoint evaluation;
matched-linear exact contrast and covariance algebra; exhaustive HT expectation;
exhaustive correlated-noise HT risk at p.3 for node/cluster designs; a realized
quadratic misspecification bias; and complement cancellation/no-interference/
intentional rank failure. All pass. Matched-linear maximum conditional bias in
the initial pilot was1.42e-14, matched-quadratic1.07e-14.

Initial pilot returned finite minimum-norm estimates even where endpoint
contrasts were not estimable. Spline valid fraction74.3%, threshold oracle80.4%,
Hajek defined57.1% across its full initial cells. These are not excluded invisibly:
raw outputs retain rank, contrast residual and valid flags; summaries retain
algorithm-level errors and report validity. Undefined Hajek finite-value risk is
conditional on a defined return and accompanied by its defined fraction.

Dense HT rare-event risk is addressed analytically, not by claiming finite-run
RMSE is accurate. For example initial SNAP node-design log10 exact variance308.63
under its linear/gamma1 DGP exceeded ordinary float range; log risk is retained.
Its covariance/noise and outcome model are simulation-known. Full-exposure
probability underflow for absent high-degree events is recorded (zero numerical
probability), never used as justification to truncate weights or change targets.

HC3 is a working-independence interval; known-covariance Gaussian intervals are
oracle diagnostics. Correct conditional mean and iid noise can justify a
noise-conditional regression interval even with clustered assignment; cluster
assignment alone is not a covariance failure. Fresh-assignment predictive risk,
endpoint bias, assignment variance, noise variance, graph-population variation
and performance Monte Carlo uncertainty remain distinct.

No production comparisons have been inspected or used to select shapes/models.
No withheld-paper source has been accessed. The graph hash matches the frozen
SNAP snapshot; initial supplied materials and idea's published Brief were read.

Final measured rollup:32pilot cells,155520 estimator rows; summed cell wall183.9813s,
CPU182.1201s. Largest R400 cell36.7453s; process peak including exact-risk audit
395332KiB. Executable conservative budget is18182.66s =5.05h for all102cells,
all three exact-risk endpoint families and factor-two allowance. This includes
new prediction-evaluation outcomes, without treating them as extra training data.
Summaries/figure integration have independent reserved time. These estimates are
intentionally larger than the expected sum because every exact-risk cell is
charged at the slowest n8000 cost, including the much smaller n2000 cases.

## Additional clearance evidence and seed correction
The preliminary report's imbalance stage was costed by a conservative extrapolation,
not a direct imbalance measurement. An additional eight production-sized pilot
cells now measure R400/p.2/.8 under both designs on regular2000/20 and SNAP,
using only pilot graph seeds/master. They are saved in results/pilot_imbalance.
The finalization script additionally times the streaming summary stage and
records process RSS in notes/calibration_finalization.json. Pilot streams can
overlap across these cost-calibration folders, so this aggregate benchmark is
not a graph-population accuracy dataset and is not supplied as research evidence.
Actual production inputs have one checkpoint per unique graph/scenario/stream.

The final budget generator includes output-compression measurements, an explicit
summary projection and7200s reserved for selected-cell clean reproduction/audit/
integration, in addition to doubling numerical generation/summary costs. The
one-week plan separately retains its final-two-days integration/review reserve.
The full measured arithmetic is in the updated pilot_budget.json once this
calibration completes. These are cost controls, not additional production factors.

Final production seed policy is the original distinct-panel proposal:
2202601(core),2202602(noise),2202603(imbalance). The6302026 shared-master draft was
superseded before any production launch. The plan owner's later acceptance of
that superseded draft crossed with this correction; current executable configs
and analysis notes are authoritative and internally consistent. Pairing IDs
contain the actual master. Cross-panel assignment/noise streams are independent.

The supplementary calibration completed successfully: its tracked wrapper measured
194.54s wall/194.06s CPU for the eight R400 imbalance cells, peakRSS398884KiB.
Its summary timing benchmark measured59.84s wall/59.74s CPU across all calibration
folders. Those folders overlap in graph/stream identity; the benchmark's numbers
are used only to cost summary generation, not as population performance evidence.
A separate corrected, unique-input imbalance summary is rebuilt for inspection.
No production factors were selected from these accuracy values. The independently
cleared scope remains102cells. Final updated budget/output arithmetic is produced
by scripts/pilot_report.py from the actual JSON and file sizes.

The additional ten-test validation passed after the aggregation corrections.
Initial pilot has exactly576nominal family/model rows and960paired family rows;
the dense regular family retains both graph seeds. All48fully undefined groups
retain NaN lower/upper RMSE endpoints. An initial test fixture omitted its declared
conditional-bias field and failed; the fixture was corrected, with no numerical
simulation change. No production simulation has been repeated for a summary fix.
