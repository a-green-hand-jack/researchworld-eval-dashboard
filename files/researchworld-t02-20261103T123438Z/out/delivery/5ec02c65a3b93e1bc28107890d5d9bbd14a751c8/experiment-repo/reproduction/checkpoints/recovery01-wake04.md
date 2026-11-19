# Complete low-decay width control and medium orbit cell

2026-11-07. Fixed01:46:19Z scientific snapshot has173 completed registered inputs
and31 absent registrations;two then-executing narrow high-LR runs are excluded.
Exact names/source/registry:derived-timing/recovery01-wake04-snapshot.json. The
single narrow high-LR block in this freeze remains partial cell evidence,not n8.

Job job-873a93b9c0 passed all five independent raw/seed/split/terminal/optimizer/
numerical audit,canonical+first8/paired predictions,13-sensitivity and inventory
stages. Actual59.646594wall seconds,64.939080childCPU+0.064908wrapperCPU seconds,
peak299252KiB. Exact trace:derived-timing/partial-recovery01-wake04.json. All1612
frozen manifest entries match transferred bytes/hashes;canonical,audit and freeze
membership agree. P1/P2/P3 are unchanged;P3 fit-comparability gate still fails.
The only retained float64 prediction discrepancy remains decay_w512_b04;measured
float32 events/curves are unchanged. Full204 remains required.

## Low-decay control: complete three-width results

All8 width32 low-decay runs fit,but0/8 have primary confirmed onset,declared delay
or terminal held-out success,Wilson95%CI[0,0.324407565]. All13 definitions retain
zero held-out onset and terminal success for this narrow cell,including90%.
Mean terminal/horizon accuracy0.012993763,seed-bootstrap95%CI[0.008056133,
0.018711018]. Wider low-decay cells were previously supplied;all three registered
widths32/128/512 now have n8 complete and0/8 primary held-out onsets/terminal
successes. Thus the registered low-decay endpoint-width restricted-time contrast
is0[0,0],eight paired blocks:both endpoints are administratively restricted at60000.
This is a finite-window threshold result,not proof of equal eventual onset or
absence of every width effect. In particular,the complete low-decay width512-minus32
horizon-accuracy contrast is+0.852130984,pointwise paired-bootstrap95%CI
[0.838097726,0.866164237]. Width128/512 horizon means remain0.407224528/0.865124747.
Do not describe all three low-decay cells as the same accuracy or as never learning.

All three registered decay-within-width comparisons are now complete. At width32,
both matched first8 default and low-decay cells have0 primary onsets;the low-decay
minus default incidence difference0 has conservative exact95%CI[-0.421752516,
0.421752516],and restricted-time difference0[0,0] reflects common restriction.
Width128's incidence-0.625[-0.934025711,0.213231543] includeszero,while restricted
time+17637.5[7100,25525] is positive. Width512's incidence-1[-1,-0.156494968] and
restricted time+43975[43687.5,44325] support recipe dependence under the primary
criterion. These are registered pointwise paired contrasts,not a newly estimated
width-by-decay interaction or evidence for a unique mechanism.

Retain the known low-threshold exception:wide low-decay block5 has a single-point
90% onset at59200 but fails terminal90%;requiring three points yields0/8. This
holds for either training threshold. All13 definitions are supplied;do not select
a favorable threshold or claim zero onsets at every definition across all widths.

Narrow low-decay CPU100 is available8/8,steps59200–60000,recorded CPU79.196209–
99.852929seconds. Seven runs completed the onset horizon AND execution before100CPU
seconds;their supplied metric uses the horizon point,without extra training or
interpolation. No narrow run has incomplete accounting. The low-decay endpoint
sampled-CPU accuracy contrast is-0.009875260[-0.014812889,-0.005197505],but it compares
these actual unequal progress points and is not a hardware-independent compute law.
The recovered medium low-decay cell remains7/8 CPU100 availability with one actual
incomplete account andnull all-block mean;do not impute it from the new narrow cell.

## Medium orbit split: complete n8 and sensitivity

All8 width128 orbit-split runs fit,but0/8 have primary confirmed onset,declared
delay or terminal held-out success,Wilson95%CI[0,0.324407565]. Mean restricted onset
60000[60000,60000] is administrative restriction. Mean terminal accuracy0.816716783,
seed-bootstrap95%CI[0.790087689,0.848826617]. At90%,1/8 has onset AND terminal
success,Wilson95%CI[0.022417491,0.470888182],for either training threshold and
one/three-evaluation persistence. Under train99%/held-out90%/three points,block5
begins38400,confirmed38600. All95%/99% and primary thinning retain0/8 held-out
onset/terminal success. These are the prescribed13 definitions,not additional seeds.

Independent audit verifies ordered disjointness/exhaustive coverage,exact orbit
hashes and zero unordered-orbit overlap for every run. Actual training sizes are
[482,480,474,484,477,478,479,478],held-out sizes[479,481,487,477,484,483,482,483].
Realized fractions differ across seed blocks;do not present them as exactly0.5 or
infer a causal split effect free of fraction/partition differences. Width32 orbit
is absent,so the registered orbit endpoint-width contrast remains unfinished.
No new medium-versus-wide or within-width split contrast test was introduced.

Medium orbit CPU100 is available8/8,no incomplete accounting or horizon/execution
completion before budget;sampled steps31600–43700. Mean sampled held-out accuracy
0.808680207,seed-bootstrap95%CI[0.781978302,0.840031460]. Exact timestamps,counts,
flags and split hashes remain in cell/run/audit JSON.

## Operational reconciliation and remaining delivery

Separate non-atomic01:48:35Z live scan:177complete,2incomplete,25unstarted. Later
files do not enter the173-input science. Both immutable one-thread guarded lanes
continue unchanged. Updated selected affine forecast includes actual new tooling:
2.827386reserved serialh versus22.343117available;known components+remaining50%
CPUreserve+future0.1CPUh allowance14.524122h<44. This is a projection/lower-bound
accounting,not an exact final total:the interrupted run's lost CPU tail remains
unknown. Reserved results archive308698174bytes<1GB. Largest observed elapsed
excess remains57.676544s;old failed scenarios and raw clocks remain.

All8 owned directories/Git/copies separately count701512090unique logical/
723021824allocated bytes. Before removing only the superseded162 worktree,all1759
non-cache/non-Git-pointer files matched exact published Git blobs;per-file proof
is recovery04-superseded162-retention.json. Current173 snapshot/immutable runners
remain available. No raw,derived,attempt,failed-tool or source history was lost.

Preparation failure is distinct from scientific failure:the first retention check
refused to treat the worktree's .git pointer as published scientific content. The
shell then launched job-5ed69a846a before its snapshot root existed;it failed with
FileNotFoundError before any stage/training. Original platform error is retained in
recovery01-wake04-resource-status-initial.json. Corrected exclusion of Git/cache
metadata and verified-worktree removal preceded the successful frozen pipeline.
No registered trajectory changed;failed startup CPU was not measured by the
pipeline and is not fabricated.

Latest bounded multiplication report wording needs no correction:all20 evidence
pins match exact published sources;onset/terminal,subset/horizon and CPU boundaries
agree. Complete unchanged later report access history is preserved with original
revision/path/bytes/hash. This is a source/text check,not our own PDF visual/final
certification. Earlier presentation access history remains;no new presentation
revision was available. Objective and frozen constraints were re-read;no external
scientific source/package fetch/literature query,withheld identification or
recognized prohibited encounter occurred.

Full204 raw/derived/audit/paired uncertainty/all13 sensitivities/scope/resources/
inventory/hash/access owner handoff remains mandatory. TrainingNov8 00:09Z,usable
package00:39Z,separate30min finalization,12h report/presentation and48h independent
review remain unchanged. Integrated84-input science/displays remain pinned until
coordinated complete204 delivery. Requests#3/#7 remain open;this is not final approval.
