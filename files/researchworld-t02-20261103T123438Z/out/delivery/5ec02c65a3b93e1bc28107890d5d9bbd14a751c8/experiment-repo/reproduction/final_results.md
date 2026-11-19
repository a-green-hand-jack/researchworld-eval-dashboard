# Complete registered study: analysis-owner evidence and claim limits

2026-11-07 UTC. All 204 prospective configurations completed through 60200 updates
(primary onset horizon 60000). No seed was replaced, no family omitted, and no
performance stopping or further scientific run was added. The final two recovery
lanes each report 40 new completions and zero failed configurations. The last
registered attempt ended at 02:06:59Z. The immutable 02:10:12Z input freeze is
`derived-timing/final204-snapshot.json`; it excludes no live/incomplete run.
The helper's historical “partial input snapshot” label describes input selection,
not the final analysis, which ran with complete-mode checks and no `--partial`.

`derived-timing/final204.json` records job `job-279941a91d`: all five stages passed
(raw audit, canonical/matched-first8 summaries, registered paired predictions,
all 13 sensitivity definitions, attempt/hash inventory). Actual pipeline cost:
64.829205 wall seconds, 70.229805 child CPU plus 0.066556 wrapper CPU seconds,
297788 KiB peak child RSS. This measures automation, not owner interpretation,
Git transfer or independent review. `checkpoints/final204-verification.json`
checks identical 204-name memberships, all 23 registered n12/n8 cells, first8
matching, every variant's complete status, event/terminal/CPU consistency and exact
manifest bytes/hashes. Primary P1/P2/P3 objects equal the prior published objects.

The source-level evidence begins at `../results/confirmatory-analysis/`, with
`runs.json`, `cells.json`, `cells-first8.json` and `predictions.json`. Every raw run
has its configuration, seeds, split hash, curve, initial/final model and optimizer
states and attempt history under `../results/confirmatory/<name>/`. The independent
raw audit is `../results/registered-audit.json`. The exact selected final handoff
is `../results/final-study-summary.json`, produced by `summarize_final.py` without
new estimation. Full sensitivities retain per-variant runs/cells/predictions and
input hashes. Manifest/inventory are regenerated after the final resource records
and summary selection; this final inventory extension changes no scientific input
or statistic from the timed pipeline. Original frozen verification is retained
separately when the final inventory is extended.

## Falsifiable explanation and decisions

The registered explanation proposes that, in this fixed parameterization and
recipe, increasing width can shorten the transition after training fit while
preserving a long fit-to-generalization lag at large width; an intervention freezing
the hidden representation was intended to distinguish this from fitting capacity
alone. P1/P2 are supported within this window; P3 cannot establish that mechanistic
part because its prespecified fit-comparability gate fails. Completing all controls
does not turn this into an established complete explanation or a unique mechanism.

P1, all 12 matched blocks, width512 minus32: restricted held-out onset difference
-43800 updates, paired percentile-bootstrap 95% CI [-44150,-43433.333333]. Training
fit difference -1741.666667 [-1816.666667,-1675]; restricted post-fit wait difference
-42058.333333 [-42408.333333,-41716.666667]. This distinguishes a larger observed
post-fit component from the smaller earlier-fit component. Restricted clocks use
the common administrative horizon for non-events; they are not observed crossings
at 60000 or extrapolations of eventual time. Main onset/terminal counts at widths
32/64/128/256/512 are 0/0/8/12/12 out of 12 under the primary rule, with terminal
counts equal to onset counts here. Every main run fits the training data.

P2: all 12 wide main blocks satisfy the declared delay criteria; Wilson 95% CI
[0.757505993,1]. The observed-pair lags and log2 clock ratios are retained per block,
not inferred from a pooled curve. P1/P2 decisions remain supported in every one of
the 13 prescribed threshold/persistence/thinning variants.

P3, first eight matched four-cell blocks: full-minus-frozen endpoint-width
interaction -43975 updates [-44325,-43687.5]. Despite its negative statistical
direction, frozen width32 has 0/8 train-fit events versus 8/8 at512 (and 8/8 in both
full cells). Frozen width128 also has 0/8 train fits. Thus representation learning
versus fitting capacity remains unresolved; neither frozen-readout failure nor a
Fourier/norm trace proves a unique circuit or an initial full-network NTK account.
The fit gate fails in all 13 variants. Frozen features are random-feature readout
training, not full-network tangent linearization.

## Complete scope contrasts

All following contrasts use eight matched blocks, width512 minus32. Intervals are
registered paired percentile-bootstrap 95% and pointwise, without multiplicity
adjustment. Report every family, including the saturated clocks. Exact block deltas,
horizon-accuracy and sampled-CPU contrasts are in predictions.json. Cross-family
changes are not newly estimated width-by-condition interactions.

| Family | Restricted onset difference, updates [95% CI] | Horizon accuracy difference [95% CI] |
|---|---:|---:|
| Low decay 0.1 | 0 [0,0] | +0.852130984 [0.838097726,0.866164237] |
| Frozen hidden | 0 [0,0] | -0.004937630 [-0.007536383,-0.002598753] |
| Low learning rate 0.0003 | -28112.5 [-29650,-26650] | +0.923596674 [0.901507286,0.945686063] |
| High learning rate 0.003 | -48375 [-48712.5,-48050] | +0.617203733 [0.546777535,0.683998180] |
| Unordered-orbit split | -18812.5 [-28487.5,-7975] | +0.857958690 [0.833088290,0.881510889] |
| Multiplication | -43425 [-44350,-42450] | +0.511694379 [0.422557168,0.599792086] |

Low-decay primary onset/terminal events are 0/8 at all three widths, so the zero
restricted-time contrast is common censoring, not equality of eventual learning
or no width effect. The large positive horizon-accuracy difference is retained.
The matched decay0.1-minus1 incidence differences at widths32/128/512 are
0 [-0.421752516,0.421752516], -0.625 [-0.934025711,0.213231543], and
-1 [-1,-0.156494968] under the prespecified conservative exact paired-discordance
method. Corresponding restricted-time differences: 0 [0,0], +17637.5 [7100,25525],
+43975 [43687.5,44325]. The medium incidence interval includes zero even though the
continuous restricted-time interval does not. A single-point 90% definition gives
one wide low-decay onset at59200 but no terminal success; three-point90% has zero.
Do not report zero events under every definition.

Both learning-rate endpoint contrast intervals remain wholly negative across all
13 definitions. Narrow low-rate fits8/8 but onset/terminal0/8 even at90%; its final
accuracy is0.070426197 [0.050935552,0.089916841]. Wide low-rate primary onset/terminal
8/8 drops to5/8 at99%. High-rate medium primary8/8 drops to2 onset/0 terminal at99%,
while high-rate wide retains8/8 for every definition. Changing learning rate also
changes per-update AdamW shrinkage, so these comparisons do not isolate gradient
speed at fixed cumulative decay or a unique causal route.

Orbit width32 fits8/8 but onset/terminal0/8 across all definitions. Width512 has
5/8 primary onsets (Wilson[0.305742395,0.863155714]) and4/8 terminal successes
([0.215216062,0.784783938]); it does not establish a majority delayed prevalence.
At90%, wide onset/terminal8/7; at99%,0/0, making the endpoint restricted contrast
0[0,0]. The width effect at primary95% therefore is not threshold-universal.
Medium orbit primary0/0 has1/1 at90%. All24 orbit runs have zero shared unordered
orbits between train and held-out. Paired split counts across blocks0–7 are train
[482,480,474,484,477,478,479,478], held-out[479,481,487,477,484,483,482,483], repeated
across widths. Each split selects248/496 unordered orbits; varying diagonal counts
change realized ordered-pair fractions. This is a split/scope intervention, not an
isolated causal comparison at identical ordered fraction/partition.

Multiplication narrow fits8/8 but onset/terminal0/8 across all definitions; primary
medium8onset/7terminal and wide8/8. Strict99% medium1/0, wide8/8. Its endpoint
restricted contrast remains wholly negative for all13 definitions. Zero-label
held-out subset counts by block are[37,33,32,39,27,30,32,25], nonzero
[444,448,449,442,454,451,449,456], with480 training/481 held-out pairs per run.
Horizon zero-subset accuracy is1 for all widths. Nonzero-subset mean accuracies at
32/128/512 are0.447612606 [0.354590289,0.541606300],0.966137417
[0.956697397,0.975419544],0.995560810 [0.994172953,0.997213417]. Thus wide success
is not only the easy zero subset; no addition-Fourier interpretation is applied
to multiplication. These intervals resample seeds, not ordered input pairs.

## CPU, integrity, recovery and limits

CPU100 is the last recorded observation at/before100 cumulative process CPU seconds
within the onset horizon, with no interpolation or extrapolated extra training.
All204 scientific curves are complete, but CPU100 is available for203: the recovered
`decay_w128_b00` has an unknown interrupted CPU tail, so its CPU100 is unavailable
and its cell has7/8 available with null all-block mean. Model/optimizer recovery is
exact and the scientific curve remains usable. All other cells have complete CPU
sampling. Narrow low-rate, high-rate, multiplication and orbit runs all finish
both horizon and execution before100CPU seconds; CPU100 therefore selects60000.
Their actual CPU sample ranges are respectively76.438604–79.522908,
77.135847–79.204688,75.886569–78.047861,71.352124–79.144275 seconds. Wide samples
are much earlier updates, as supplied in each cell. Sampled-CPU endpoint effects
are not universal FLOP/hardware efficiency laws and can differ from fixed-update
effects: e.g. low decay has -0.009875260 [-0.014812889,-0.005197505] despite its large
positive fixed-horizon effect. Full progress/missingness flags are supplied.

All603 recorded evaluations, exact configurations, split coverage/disjointness,
initial seed tensors, terminal model predictions/loss/norm/displacement, terminal
AdamW60200 and frozen/full initialization identities pass the independent raw
audit. Float32 production metrics are retained. Independent float64 dense one-hot
evaluation has one held-out prediction discrepancy in `decay_w512_b04` near a tie;
all other terminal prediction comparisons agree. Explicit roundoff bounds and
ambiguous predictions are exposed; this is not claimed as exact cross-precision
identity or independent raw rechecking of every intermediate model checkpoint.
See numerical_audit.md for the initially failed large-logit loss audit and fix.

Inventory preserves204 completed attempt-end records plus one unmatched
interrupted attempt start. The raw rollback archive, checkpoint, failed resource
guards, old deadline scenarios, superseded forecasts, software/preparation
failures, exploratory configurations and historical trainers remain delivered.
Pilots informed the registered recipe and remain excluded from confirmatory
inference. No negative or failed attempt is silently erased. No additional
post-horizon continuation, prime/depth/activation/fraction sweep, circuit ablation,
NTK measurement or multiplicity-adjusted omnibus claim was performed. These are
limits, not planned work mislabeled as a negative result. Prior permitted work
already studies model size; no first-size-study or exhaustive novelty claim is made.

`final-resource-accounting.json` separates actual known components from projections:
production summaries record48710.214841CPU seconds (13.530615h, lower bound due to
unknown tail), preproduction540.826764s, timed derived tools666.031338s and measured
software4.297300s, totaling13.867047 known-componentCPUh. Other sandbox/import,
guard/transfer/manual checking and the unknown tail are not fabricated as zero.
Platform aggregate50049.266598s is separate and overlaps those clocks, so it is not
added. Raw summed elapsed clocks preserve two historical very long low-CPU gaps
and overlap concurrent runs; they are not ordinary serial throughput or project
wall time. OriginalNov6 deadline remains missed; all training completed before
revisedNov8 00:09Z cutoff, leaving the separate full finalization/report/review
windows and unchangedNov10 12:39Z absolute week. Remaining registered training is
zero; generic forecast startup reserves are not remaining scientific work.

Latest actual source-access supplies for all nine owners and dated additions are
preserved unchanged with provenance in access-records/ and access_log.md, including
internal-review'sNov7 issue-supplied addendum without reading its code. No future
absence or review approval is inferred. Figure/table renderings, manuscript,
venue compliance and independent exact-version acceptance belong to their owners;
this scientific package is ready for coordinated promotion of the84-input interim
science to the complete204 supply. Later actual integrated-review accesses must
be appended by their owners.

## All registered primary cell denominators

Counts are fit / held-out onset / declared delay / terminal held-out success.
Cell Wilson and seed-bootstrap intervals accompany these counts in cells.json;
first8 main matching is separately in cells-first8.json.

|Family|Width|n|Fit|Onset|Delay|Terminal|
|---|---:|---:|---:|---:|---:|---:|
|decay|32|8|8|0|0|0|
|decay|128|8|8|0|0|0|
|decay|512|8|8|0|0|0|
|frozen|32|8|0|0|0|0|
|frozen|128|8|0|0|0|0|
|frozen|512|8|8|0|0|0|
|lr-high|32|8|8|0|0|0|
|lr-high|128|8|8|8|8|8|
|lr-high|512|8|8|8|8|8|
|lr-low|32|8|8|0|0|0|
|lr-low|128|8|8|0|0|0|
|lr-low|512|8|8|8|8|8|
|main|32|12|12|0|0|0|
|main|64|12|12|0|0|0|
|main|128|12|12|8|8|8|
|main|256|12|12|12|12|12|
|main|512|12|12|12|12|12|
|multiply|32|8|8|0|0|0|
|multiply|128|8|8|8|8|7|
|multiply|512|8|8|8|8|8|
|orbit|32|8|8|0|0|0|
|orbit|128|8|8|0|0|0|
|orbit|512|8|8|5|5|4|
