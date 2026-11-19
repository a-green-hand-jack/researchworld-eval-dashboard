# Experimental reproduction

All 204 registered runs are complete and independently raw-audited; all 23 cells,
registered contrasts and 13 sensitivity definitions pass complete-mode checks.
`final_results.md` is the analysis-owner handoff, `../results/final-study-summary.json`
the source-pinned selection, and `checkpoints/final204-verification.json` the exact
membership/hash/accounting check. Complete-study manuscript/presentation integration
and independent acceptance belong to their owners. Historical status paragraphs
below retain their dated scope and do not describe the current complete science.

The synthetic data are all ordered integer pairs a,b in 0..30. Labels are (a+b)%31 or (a*b)%31, exactly as registered. No download, account or third-party dataset version is required. See configs/confirmatory.json for the complete prospective204-run matrix; pilots are separate and do not enter confirmation.

Run from the repository root. The required CPU environment is recorded in environment/environment.json and exact package versions in environment/requirements.txt. PyTorch uses the official CPU build. All runs use a single intra-op thread and deterministic algorithms. At most two independent resource jobs run concurrently.

```bash
python3 code/scripts/check_implementation.py
python3 code/scripts/check_events.py
python3 code/scripts/check_reporting.py
python3 code/scripts/check_controls.py /path/to/new-validation-output
python3 code/scripts/run_grid.py configs/stages/main-and-frozen-1.json results/confirmatory
python3 code/scripts/run_grid.py configs/stages/main-and-frozen-2.json results/confirmatory
python3 code/scripts/run_grid.py configs/stages/follow-on-1.json results/confirmatory
python3 code/scripts/run_grid.py configs/stages/follow-on-2.json results/confirmatory
python3 code/scripts/analyze.py results/confirmatory --registry configs/confirmatory.json --output results/confirmatory-analysis
```

The two main/frozen grids may be run concurrently; follow-on grids begin only after the production gates and required launch decision. On the research platform, computations belong to tracked resource jobs. A full reproduction runs all204 configurations through60200 updates (primary onset horizon60000, additional200 for persistence confirmation). Scientific runs have no performance-based early stopping. Plotting and document build commands belong to presentation and paper owners.

The run entrypoint refuses to overwrite a completed config and verifies its metadata on skip. For an interrupted run with a durable checkpoint, add --resume; configuration and training-source hashes must match. Rolling checkpoints are atomic, saved every10000 updates and at termination. Raw rows beyond the last durable checkpoint are archived on recovery. Initial/final states, AdamW optimizer, RNG state, seeds, actual split hashes, all curves and attempts are retained. Separate-horizon continuation is supported by train.py --continue-from and never overwrites the primary directory; it is an optional separately gated study.

The paired block is the uncertainty unit, varying split and initialization jointly. No confidence interval treats validation pairs as independently retrained models. Event rules, censoring, boundary cases and precise paired binary method are documented in reproduction/analysis_methods.md and plan/protocol.md. The implemented estimands and uncertainty methods are specified in analysis_methods.md; plan/protocol.md is the prospective plan supplied in the integrated manuscript repository.

Measured pilot runtimes:20000 updates took about33/64/169 wall seconds at widths32/128/512, with exact source summaries in results/pilot. This is a pilot measurement, not a guarantee for production. Actual production costs and successive prospective resource/deadline decisions are retained in resource_gates.md, deadline_ledger.json and the dated checkpoint records. No final prediction, uncertainty estimate or claim about204 outcomes is asserted before those outcomes exist.

## Registered analysis and integrity checks

After completion, run:

~~~bash
python3 code/scripts/audit_registered.py results/confirmatory --require-complete --output results/registered-audit.json
python3 code/scripts/analyze.py results/confirmatory --registry configs/confirmatory.json --output results/confirmatory-analysis
python3 code/scripts/study_analysis.py results/confirmatory-analysis/runs.json --output results/confirmatory-analysis/predictions.json
python3 code/scripts/sensitivity.py results/confirmatory --registry configs/confirmatory.json --output results/sensitivity --require-complete
python3 code/scripts/inventory.py
~~~

P1 reports all12 paired endpoint restricted-time differences. P2 uses declared lag/ratio and Wilson seed-level prevalence. P3 resamples each complete four-cell seed block and retains the frozen fit gate. Secondary decay differences retain paired2x2 counts and conservative exact confidence bounds. Scope comparisons are pointwise, with all families reported. Sensitivity uses the same analyze entrypoint with --valid-threshold 0.90 or 0.99, --train-threshold 0.95 or 0.99, --sustain 1 or 3; --thin 2 uses measured evaluations only and can have less confirmation coverage near the boundary. It does not estimate unmeasured finer dynamics.

The audit recomputes data/split hashes, all603 evaluation steps, finite values, exact counts, optimizer terminal step, frozen tensors and full/frozen initialization equality. Final checking requires all204 complete raw runs. Manifest lists actual files/hashes and source/config provenance; inventory includes every observed attempt and explicitly labeled unstarted registrations during preparation. Such rows are not scientific results.

Archived trainers reproduce the exact historical timing pilot, full exploratory pilot and cost-benchmark implementation. Source commits, paths and hashes are in code/archive/provenance.json. Current production trainer retains durable attempt-start/end events. Measured discarded-attempt work contributes to recovery CPU/wall clocks; an abrupt process loss leaving an unmeasured CPU tail is flagged, and exact100CPU-second accuracy is not claimed for that run. Model and optimizer recovery remain bitwise identical in non-timing checks.

Run python3 code/scripts/resource_quote.py to regenerate the quote. Existing deadline_ledger is preserved, especially after production launch. Consult reproduction/resource_gates.md for measured/projected throughput, storage and reserve. Actual owner access records are consolidated in reproduction/access_log.md.


Production grids print ordinary progress throughout, and wake the analysis owner every six newly completed configurations, on failure, and when the grid ends. This limits repeated incomplete-study activations while leaving atomic checkpoints and flushed curves available. --wake-every changes notification cadence, never training or evaluation cadence.

## Historical pilot commands

Use a new output directory:

~~~bash
python3 code/archive/timing-v0/scripts/run_grid.py configs/timing.json results/reproduce-timing
python3 code/archive/pilot-v0/scripts/run_grid.py configs/pilot-a.json results/reproduce-pilot
python3 code/archive/pilot-v0/scripts/run_grid.py configs/pilot-b.json results/reproduce-pilot
~~~

Full-pilot and gate-benchmark source hashes match the archived trainers. The initial timing stage predated embedded source hashes; its exact revision is archived in code/archive/provenance.json. Historical configs/outputs remain unaltered.

## Presentation inputs and secondary recomputation

`results/confirmatory-analysis/cells.json` supplies all seed-cell estimates;
`cells-first8.json` restricts every main and secondary cell to registered blocks0–7,
so matched control displays use the same denominator. Both retain onset and terminal
sustained success separately, with Wilson intervals. `runs.json` exposes split hashes,
actual data-construction metadata and per-run CPU100 step/availability flags. The
final `registered-audit.json` recomputes ordered and unordered disjointness, exhaustive
coverage, exact orbit hash/pair counts and multiplication zero/nonzero counts.

`code/scripts/sensitivity.py` executes the complete train{.95,.99} ×
held-out{.90,.95,.99} × persistence{1,3} grid on the same measured curves, plus
the primary thresholds at every second evaluation. It writes variant run/cell/first8
files and prediction summaries to `results/sensitivity/`; `sensitivity.json` retains
P1 paired intervals, P2 prevalence, P3 gate and input hashes for every variant.
These are secondary pointwise analyses; the primary prediction decisions remain
fixed. Thinning to200-update cadence cannot confirm an onset at60000 with three
points from the60200 endpoint; the output explicitly states this boundary limitation.

The CPU100 cell summary reports available run count, minimum/maximum actual sample
steps and recorded CPU timestamps, and counts for horizon/execution completion
before budget and incomplete timing accounting. Accuracy is the last measured point
at/before100 cumulative process-CPU seconds within the onset horizon. It is not an
interpolated100-second value or a universal hardware/FLOP comparison.


## Historical 84-input interim evidence

At the first main/frozen interim checkpoint, all84 runs had complete raw artifacts and passed the partial registered
audit;120 mandatory control registrations were then unstarted. See interim_results.md
for exact results and limits. That checkpoint's predictions.json contains complete main P1/P2
and P3 with failed fit gate, not full-study scope evidence. All13 sensitivity variants
retain full-matrix complete=false; P1/P2 directions hold and P3 fit gate fails across
these variants. The manifest and inventory are regenerated from this actual snapshot.
Typical production process CPU totals5.718h for these84 runs; recorded wall includes
two very long low-CPU gaps and should not be advertised as ordinary training time.
Follow-on estimate9.459CPUh is a planning quote. Deadline gate/revision is explicit
in deadline_ledger.json and the resource checkpoint.

## Historical initial recovery guard and distinct planning scenarios

The original failed experiment-time gate is preserved. `recovery_scenario.json`
contains a separately identified prospective scenario; its actual story-repo decision is now recorded and relayed unchanged in
planning-supplies/recovery-authorization/. The fresh selected launch gate passed
and both immutable one-thread follow-on jobs are tracked in deadline_ledger.json.
Affordability alone does not grant authorization. The exact unchanged assessment and
hash manifest are retained under `planning-supplies/feasibility-v2/`.

`monitor_resources.py --schedule reproduction/recovery_scenario.json` retains the
literal historical maximum-wall scenario and reports a separate `selected_gate`.
A pending/missing decision always blocks that selected gate. An authorized decision
must name its story owner, full revision and path; the analysis owner records it
only after reading the actual supply. Both original deadline and absolute week
clock remain unchanged. The prospective factor is at least1.860141102946608 and
increases for slower newly observed run ratios. Only the two explicitly named
historical timing-anomaly runs are excluded from that prospective population;
all raw measurements remain delivered. Any new stall enters the maximum and can
stop further work.

For platform-budget-controlled execution, the runner accepts paired arguments
`--resource-root /hutian/repo --resource-schedule /hutian/repo/reproduction/recovery_scenario.json`.
Before every new configuration it reprices the entire remaining registered work,
retains50% remaining contingency, checks CPU/storage/time, and refuses to invoke
the trainer if the selected gate fails. Guard failures exit3 and print a wake;
they are unstarted research, not failed training or scientific non-events.
Completed runs are still verified/skipped. This wrapper changes no scientific
configuration, update, seed, evaluation schedule or event definition.

`python3 code/scripts/check_resource_guard.py` verifies pending-decision refusal
before any trainer invocation, retained original false gate, explicit structural
schedule selection, historical anomaly population and failure on any new stall.
Those are isolated software fixtures, never real approvals or scientific results.
The study's ordinary reproduction commands above remain available for independent
reproduction; this guard records the research platform's execution budget decision.

The recovery target now distinguishes training completion from usable-package
handoff. Authorized training cutoff is00:09:10.373Z onNov8, with a separate30-minute
final-derived/verification/transfer/owner-check allowance before00:39:10.373Z.
Measured partial pipeline cost and the conservative planning allocation are in
`derived-timing/`. Actual authorization is source-attributed in recovery_scenario.json; the
original pending checkpoints remain historical, and no status is inferred from
a software fixture or affordability alone. `finalize_analysis.py` defaults
to a complete204-run audit/sensitivity requirement and writes exact per-stage
runtime/source records outside the results-only hash manifest.


2026-11-06 follow-on execution update: the84-run inventory/derived results above
remain the last checked scientific snapshot. All120 remaining controls have
been launched unchanged as two60-config resource lanes under story-repo's
explicit schedule amendment and passed fresh launch check. Exact source/jobs,
both guard arguments and milestones are in follow_on_launch.md and
 deadline_ledger.json. Completion wakes trigger repricing and checked evidence
handoffs; unverified live outputs are not complete-study evidence. The final
all204 audit, sensitivity, claim/scope and resource/access package remains due.


First-control checkpoint96/204: checkpoints/follow-on-wake01.md records the
consistent frozen inputs, new matched wide-decay evidence and numerical audit.
Run python3 code/scripts/check_numerical_audit.py on the supplied completed
large-logit endpoint to verify exact stored-metric replay, independently exposed
float64 near-tie sensitivity and rejection of a corrupted stored loss. This is
a software check on copied existing inputs, not new training. New final data
must pass the full204 audit and all13 sensitivity/completeness gates.

For an abrupt stop with an unmatched attempt-start record, recovery retains the
old attempt without fabricating its end, archives rows after the durable checkpoint,
and flags cumulative CPU as incomplete. Such runs remain excluded from CPU100
comparisons. The isolated regression `python3 code/scripts/check_abrupt_recovery.py
--output /path/to/software-check.json` checks bitwise state/trajectory recovery,
raw-row preservation and that exclusion through the actual analysis entrypoint.
It does not resume registered production data or grant a scheduling decision.


## Current guarded recovery and complete-study handoff

After the initial follow-on guard stopped new launches, an independently supported
replacement decision authorized the affine forecast and exact checkpoint recovery.
The original failure, unmatched attempt start, archived post-checkpoint rows and
unavailable CPU tail remain recorded. `recovery01_launch.md` and
`guard-recovery01-authorized.json` give the actual decision/source and the shared
before-configuration guard. `deadline_ledger.json` identifies both immutable
one-thread recovery jobs. Changes to documentation do not alter those runners.
An incomplete CPU account makes the affected run's CPU100 outcome unavailable;
its valid model/optimizer trajectory remains usable for the registered scientific
outcomes. Missing CPU outcomes are never imputed into an all-block cell mean.

For the final bundle, run the measured full pipeline from a stable root containing
all 204 completed runs (omit `--partial`):

~~~bash
python3 code/scripts/finalize_analysis.py --root . --timing-output reproduction/derived-timing/final204.json
~~~

This performs the required complete raw audit, canonical and matched-first8
summaries, registered predictions, all 13 sensitivity definitions and attempt/hash
inventory. Per-stage exit status, stdout/stderr, source hashes, wall/CPU and peak
child RSS are recorded in the timing JSON. A failed stage stops the pipeline;
`--partial` is explicitly a progress/timing mode and cannot certify final evidence.
The single entrypoint invokes the same individual commands listed above.

Before final handoff, verify that audit/analysis/sensitivity/manifest all identify
the same 204 registered names, that all 23 cells have their registered n12/n8
counts, and that every manifest file matches its bytes/hash. Preserve every actual
attempt, rollback archive and precision discrepancy; separate onset from terminal
success. Reconcile per-run CPU100 flags and all-block unavailability, split/orbit
counts, multiplication subsets, pointwise scope intervals, actual resource totals,
all owned copies and date-scoped owner access records. The final source transfer
and semantic checks are separate from measured pipeline runtime and independent
paper review. Latest frozen evidence and actual live operational status must
retain their separate timestamps. The registered matrix, horizons and milestone
clocks remain unchanged.


For a dated progress snapshot while training continues, `code/scripts/freeze_completed.py`
selects complete registered runs into a new sibling `experiment-checkpoint-*` root.
Its `--record` JSON names the archived source, exact completed inputs, excluded live
runs and generator hash. With `--superseded-record` and `--retention-record`, it
first verifies every non-cache scientific file of the older copy against published
Git blobs; any mismatch refuses removal. Only after successful freezing should a
tracked `finalize_analysis.py --root /path/to/snapshot --partial ...` job be launched.
Partial runs never replace the mandatory complete204 pipeline and final semantic
checks above. Use repository scripts for repeated preparation; `/tmp` helpers do
not persist across research activations.

## Final supplied commands and actual runtimes

The complete pipeline ran without `--partial`; exact cost/source/per-stage records
are in `derived-timing/final204.json`. After adding final resource records or the
optional selected summary, regenerate the inventory and verify every supplied hash:

~~~bash
python3 code/scripts/finalize_analysis.py --root . --timing-output reproduction/derived-timing/new-reproduction.json
python3 code/scripts/summarize_final.py
python3 code/scripts/inventory.py
python3 code/scripts/verify_bundle.py --root . --output reproduction/new-verification.json
~~~

On the supplied completed runs, the full five-stage pipeline measured 64.829205
wall seconds / 70.296361 child-plus-wrapper CPU seconds. This is regeneration of
analysis, not rerunning training. `final-resource-accounting.json` lists actual
per-cell min/median/max/sum CPU and elapsed runtimes across all 204 training runs.
Production summaries record 13.530615 CPU hours plus separate startup/tooling and
unknown interrupted-tail costs. Retained clocks include old low-CPU wall gaps; do
not use their summed wall time as ordinary throughput. The original prospective
weighted all-run quote was 22.518461 CPUh including startup/50%reserve. A fresh
reproduction needs new directories and fresh actual resource checks. No guaranteed
wall duration, hardware-independent FLOP match or exact exhaustive total is claimed.

`final_accounting.py` regenerates the final clock reconciliation from the retained
resource snapshot and raw runs; `summarize_final.py` selects exact final statistics
without a new fit or interval estimate. Presentation owns the figure/table generator
map and commands in the integrated artifact. The analysis owner's work supplies all
measured inputs and their complete paths; it does not claim visual or venue approval.
