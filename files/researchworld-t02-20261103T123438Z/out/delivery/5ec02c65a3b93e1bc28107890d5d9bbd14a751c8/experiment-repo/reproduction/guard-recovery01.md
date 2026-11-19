# Actual guard stop and proposed supported recovery

Dated preparation/hold history below. The later actual supported decision, fresh passing gate and tracked execution are recorded in `recovery01_launch.md`; prior pending statements remain historical.

No training is authorized by this document or proposed scenario. Both lanes are held. The original matrix,all remaining controls,seeds,training/event windows,milestones and final checks remain required.

At2026-11-07T00:20:26.587403Z the immutable follow-on lane2 guard stopped before decay_w128_b01 and exited3. Its exact unchanged report is results/resource-checkpoints/guard/follow-on-2/decay_w128_b01.json. It saw124 complete,one executing and79 unstarted. CPU/storage passed,but latest measured elapsed/CPU ratio7.52412809495 on executing decay_w128_b00 at step3600(66.777537wall/8.875120CPU seconds) projected37.811615 reserved serial hours versus23.812163 available before the training cutoff. No decay_w128_b01 was launched. The owner stopped lane1 as well to prevent further launches after this new failed common gate;its platform status is outside/torn-down. This is an intentional owner stop,not evidence of a specific host failure.

The actual incomplete decay_w128_b00 curve reaches36900,last recorded150.798245wall/92.828855CPU seconds. Saved model/AdamW/RNG checkpoint is step30000,133.705476wall/75.749848CPU seconds;hash/source and actual stop action are in results/resource-checkpoints/guard-stop01-recovery.json. There is an unmatched started attempt. Do not forge a normal attempt end or exact total compute. Exact resume under the unchanged trainer/config must archive the rolled-back rows and flag incomplete CPU accounting;CPU100 for this run becomes unavailable under existing rules. It is an interrupted execution,not a scientific non-event or a failed optimization outcome.

The full measured curve also records an earlier step100 prefix:58.161637wall/0.260782CPU seconds,ratio223.027389. The cause is unknown;do not call it scheduler/host/provider interference without evidence. Later accumulated elapsed/CPU is smaller,but no raw prefix or failed guard may be erased to justify restart. This recovery therefore requests an explicit scheduling-model decision,rather than treating a later averaged ratio as automatic clearance under the failed decision.

## Concrete proposal for independent assessment

Keep approved baseline slope rho=1.860141102946608 and the same two explicitly named historical gap exclusions only. For every other registered run,scan every main and discarded-curve clock prefix,actual completed end and recorded attempt end. Let A=max(0,elapsed-rho*CPU) over that entire population. This records all new slowdowns as positive additive elapsed excess,not an exclusion or zero-cost deduction. The quote enumerates74180 actual prefix/end observations at this checkpoint. A=57.6765442939seconds at decay_w128_b00 step100. The raw maximum ratio223.027389 and the failed guard7.524128 remain explicitly separate data.

For the80 unfinished configurations,quote a full configuration CPU price even for the interrupted/actively running case,using the original quote or slower actual same-family/width rate. With four-interpreter startup CPU allowance retained,quote:

reserved wall=1.5 * [rho*(sum unfinished full CPU prices+startup CPU) +80*A].

Known measured CPU plus1.5 unfinished full CPU and future0.1CPUh finalization allowance is16.342790CPUh<44. Reserved wall11.277349h fits23.733807h available at the quote,without dividing by two or using concurrency speedup. Every unfinished configuration is charged the largest observed additive excess,not merely the interrupted one. New larger prefixes/archived or end excesses reprice the entire remainder before every configuration and at completion wakes. A sufficiently large new stall still stops the jobs. This is a monitored prospective empirical envelope with contingency,not a bound on future stalls or a proof of calendar reliability.

The original schedule result and original latest-ratio result remain in monitor output. New optional model elapsed_prefix_affine_v1 is implemented in code/src/resource_forecast.py and monitor_resources.py;the default behavior is unchanged. reproduction/guard-recovery01-proposal.json has pending status and no decision. Its actual selected continue flag is false even though the proposed arithmetic fits. An explicit durable guard-hold marker also blocks the old decision even if a later averaged ratio fits:the scenario must name the failed revision as superseded and carry a different actual story decision. No fixture,structural test approval or plan prose supplies real authorization. A genuine explicit supported story decision with full revision/path and a fresh gate is required before starting immutable guarded recovery jobs,with at most two one-thread jobs. No milestone/review-window change,extra exclusion or scientific-scope reduction is proposed.

Actual quote:results/resource-checkpoints/guard-recovery01-proposed-affine.json. Exact failed/recovery/implementation/proposal hashes:reproduction/checkpoints/guard-recovery01-inputs.json. Software regression check_affine_forecast.py tests retained early/discarded/zero-CPU prefixes,full unfinished price,50% reserve,unchanged default stop logic and the actual pending proposal blocking training. Actual initial software job job-d55fd5f5a4 and strengthened durable-hold regression job-2762ce7d75 both passed with no trainer invocation;their exact platform outputs are preserved under reproduction/checkpoints/. Actual124-input science pipeline job-12a8e43b1b also passed;its cost is now included in the refreshed proposal quote. The refreshed proposed known-component CPU+reserve+future allowance is16.358157CPUh;the original16.342790 quote remains separately preserved. Ancillary software-test CPU not separately timed is disclosed rather than claimed as exhaustive project compute.

The proposed next actions are:independent assessment/explicit plan decision;fresh live inventory/resource/storage/serial fit;exact step30000 recovery with truthful CPU limitation and raw rollback archive;all remaining unchanged mandatory controls;complete204 audit/13 sensitivities/uncertainty/scope/resource/access handoff and independent final review. Existing124 completed inputs remain available for a separate checked partial scientific supply. They do not complete the study or justify bypassing this hold.

## Abrupt-stop recovery validation before any permitted restart

The additional software-only job job-dd9ed9feab passed the actual unchanged trainer's
lost-attempt-end path. `code/scripts/check_abrupt_recovery.py` uses an isolated
40-update fixture with a durable checkpoint at20 and raw rows through30. It
explicitly removes only the fixture's last attempt-end record and restores its
older checkpoint to simulate this failure mode. Production inputs are never edited.
On resume, model tensors, complete AdamW state, RNG, initial vector and final step
are bitwise equal to an uninterrupted fixture, and all nonclock curve metrics agree.
The exact rolled-back rows are archived; the unmatched attempt start remains
without an invented end. Known measured prefix CPU is retained as a lower bound,
and incomplete-accounting flags reach metadata and summary. Running the real
analysis entrypoint confirms CPU100 step/accuracy/timestamp are all null.

Actual report/source hashes are in
`reproduction/checkpoints/abrupt-recovery-software.json`; the platform success
record is `job-dd9ed9feab-status.json` there. The fixture took5.636245wall seconds;
measured in-script process4.068921 plus child0.228379CPU seconds exclude
interpreter/import startup and are recorded separately from the existing
science-derived-tooling forecast component. This is validated recovery behavior,
not a new trained seed, measured204 result or authorization to resume. The actual
interrupted run and pending scenario are unchanged; a supported story decision and
fresh complete resource gate still precede any production restart.

## Automatic failure latch and known software cost refinement

Before any possible recovery, the runner now atomically records a shared
`guard-stop-auto-<timestamp>-recovery.json` if validation or the selected gate fails
under a structurally authorized story decision. It still exits3 before invoking
the trainer. Both lanes' later gates read that hold, so a later smaller average or
shorter remaining-work quote cannot clear it. A pending proposal does not create
an authorization. Multiple historical holds require explicit cumulative
supersession through `supersedes_decision_revisions` (the existing singular field
remains supported). Each actual superseding revision must still be read from the
plan owner's supply; structural fixtures are not decisions.

The monitor also separately adds measured software-fixture process/child CPU to
known components, without overlapping training/derived-tooling aggregates. This
currently adds4.297300seconds from the abrupt-recovery test; its import/startup
omission and other untimed ancillary tooling remain disclosed. No scientific
trainer,configuration,wall formula,prefix population,exclusion,contingency or
milestone changed. The refreshed pending report is
`results/resource-checkpoints/guard-recovery01-refined-pending.json`:
reserved serial11.277349h and known-component+remaining-reserve+future allowance
16.359351CPUh;authorized=false and continue=false. This remains a proposal and a
nonexhaustive compute accounting, not independent feasibility approval.

Tracked job job-3a045f1a89 passed the expanded isolated guard checks and affine
regressions. In the fixture,an actual gate failure creates the automatic hold;
changing measured elapsed to an affordable value still blocks launch;only explicit
supersession clears it,and all prior failed decisions must be named after multiple
holds. Tests also check measured software costs enter the quote. No production
trainer was invoked. Exact platform status and refinement source hashes are under
`reproduction/checkpoints/`. The platform's final-output tail retains the last two
messages of the combined test;the added assertions are in check_resource_guard.py.
