# Independent audit of the frozen study

## Scope and bottom line

Audit date: 2026-11-03 UTC. Read `protocol.md`, `extension_protocol.md`, `analyze.py`, `main_manifest.json`, and `mechanism_audit.md`; inspected `train.py` only to verify recorded quantities. No web/literature, training, optimizer, protocol, manifest, or original analysis-code changes were made. No plots or manuscript were generated. Pilots were excluded.

**P1's promised doubling is rejected, with no censoring ambiguity at its endpoints.** The 64→256 paired mean log2 clock-ratio difference is **0.205498**, or **1.15308×**, not ≥1 log2 unit / ≥2×. Absolute generalization is faster, supporting the weaker behavioral two-clock direction. **P2 shows a unanimous sample benefit (10/10 versus 0/10), but its ≥0.5 population-probability magnitude is not established by nondegenerate conservative uncertainty bounds.** P3's optimizer-coordinate correspondence is numerically very close, not bitwise equality. The mathematical identity has narrower scope than generic random-width equivalence.

All 185 main summaries were present on the first completeness check, so no wait was necessary. The first unchanged `python /work/analyze.py` excluded an incomplete extension. All 20 extension runs completed during independent checking; the script was then rerun unchanged. **The final outputs audited here include all 205 runs, 2,460,000 updates, and 98,605 checkpoint rows** (481 per run). Extension results remain exploratory and are never pooled into P1/P2.

## 1. Reproduction, provenance, and integrity

Commands, in order, sufficient to reproduce the final audit outputs:

```sh
python /work/analyze.py
python /work/analysis/independent_audit_recompute.py
python /work/analysis/independent_audit_supplement.py
```

The independent scripts perform inference and numerical analysis only; they never train or patch the original files. In `/work/analysis/audit_checks.json`, **7,475 checks passed, zero failed**. Checks cover all 205 configs and all checkpoint rows, including:

- Exact manifest/summary config agreement, complete 0:25:12000 grids, finite scalar metrics, accuracy/Fourier ranges, and layer/total norm identities.
- Independent running-streak reconstruction of every main and extension 99%/five-evaluation endpoint, censor flag, clipped clock, delay, grok/strict-grok indicator, final/best accuracy, and post-crossing regression count.
- All 54 original primary threshold/persistence sensitivity rows, checked against independent reconstruction. Supplemental delay-ratio 3 and 10 results are also retained without selecting a preferred definition.
- Recreated partition hashes and sizes, reverse-pair overlap, parameter counts, model metadata, and source provenance. Grouped splits have no reverse leakage; ordered controls are explicitly different.
- Every saved final model independently evaluated: final accuracy, test loss, parameter norm, and (where applicable) full-domain centered-logit Fourier fraction match recorded rows within the stated numerical tolerances. Initial model logit scales were also reconstructed without training.
- Exact reproduction of the original seeded 20,000-draw cell and primary paired bootstrap calculations, and all original replication trajectory-difference numbers.

The three frozen hashes match `protocol_freeze.json`, and every main/extension summary has the same training-source hash:

| File | SHA256 |
|---|---|
| `protocol.md` | `84954b83e41018f6dc949df0b03b10870134371082008286df703b1d69d87648` |
| `main_manifest.json` | `8ef6496e2a241142f4f0a548f7eefdf101dd4066ab6d7f469c3298b4146a83f3` |
| `train.py` | `671bf454f97fbf3f8c14f819c4cab31e79b1e5bee6ff7497e9366c677ebd80ec` |

These checks establish file-level consistency and successful endpoint recomputation, not a full training replay or independent certification of every optimizer update. The protocol freeze is local/prospective, not public preregistration. Checkpoints are not independent replicates: inference uses ten joint split/initialization blocks for P1/P2, and five or ten blocks in secondary cells.

## 2. Metrics and measured cells

`tM` and `tG` are the **onsets** of the first five consecutive evaluations with train/test accuracy ≥99%, respectively: a 100-update confirmation span. An unobserved onset is right-censored at **C=11900**, not at 12000. `uM=min(tM,C)` and `uG=min(tG,C)` retain censor flags. The restricted ratio endpoint is `LC=log2[(uG+25)/(uM+25)]`.

Operational delayed grokking additionally requires both events, `tG >= 10*max(tM,25)`, and test accuracy at `tM <=0.5`. Strict grokking requires train accuracy to remain ≥99% from `tM` through `tG`; it does **not** require test accuracy to remain above threshold forever afterward.

### Primary p31, grouped addition, decay=1

All train clocks are observed. `11900*` denotes a censored restricted median, not an observed generalization time. Accuracy and intervals below are percentages; intervals are the original 95% whole-block bootstrap intervals for mean final test accuracy.

| Width | Parameters | Fit | Generalized | Delayed / strict | Median tM | Median uG | Final test mean [95% CI] |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 1,488 | 10/10 | 0/10 | 0/0 | 200 | 11900* | 44.672 [41.440, 48.112] |
| 32 | 2,976 | 10/10 | 0/10 | 0/0 | 100 | 11900* | 88.648 [87.793, 89.449] |
| 64 | 5,952 | 10/10 | 10/10 | 10/10 | 75 | 1087.5 | 99.916 [99.812, 100] |
| 128 | 11,904 | 10/10 | 10/10 | 10/10 | 50 | 887.5 | 99.979 [99.937, 100] |
| 256 | 23,808 | 10/10 | 10/10 | 10/10 | 50 | 887.5 | 100 [100, 100] |
| 512 | 47,616 | 10/10 | 10/10 | 10/10 | 25 | 737.5 | 100 [100, 100] |

An empirical bootstrap interval [100,100] from unanimous final accuracies does not imply zero population uncertainty. Generalization-event Wilson intervals are [0,0.277533] for 0/10 and [0.722467,1] for 10/10. The observed 32/64 boundary is a finite-grid, finite-budget boundary, not an exact architectural threshold or eventual impossibility result.

### Decay and function-preserving interventions (all n=10)

All cells fit 10/10. Final-test mean is descriptive here; original 95% bootstrap intervals are preserved in `audit_cells.csv` / `group_summary.csv`.

| Condition | Width | Generalized | Delayed / strict | Median uG | Final test mean (%) |
|---|---:|---:|---:|---:|---:|
| decay=0 | 64 | 0/10 | 0/0 | 11900* | 7.999 |
| decay=0 | 256 | 0/10 | 0/0 | 11900* | 5.360 |
| decay=0.1 | 64 | 0/10 | 0/0 | 11900* | 79.849 |
| decay=0.1 | 256 | 1/10 | 1/0 | 11900* | 73.560 |
| replicated 64→256 | 256 | 10/10 | 10/10 | 1250 | 99.459 |
| rate-matched narrow | 64 | 10/10 | 10/10 | 1250 | 99.459 |
| balanced rescale | 256 | 10/10 | 10/10 | 825 | 100 |
| balanced rescale | 32 | 0/10 | 0/0 | 11900* | 87.010 |

### Secondary scope and controls (all n=5)

All cells fit 5/5. No multiplicity-corrected confirmatory claims are made for these cells.

| Condition | Width | Generalized | Delayed / strict | Median uG | Final test mean (%) |
|---|---:|---:|---:|---:|---:|
| p53 addition | 32 | 0/5 | 0/0 | 11900* | 89.202 |
| p53 addition | 64 | 5/5 | 1/1 | 625 | 99.872 |
| p53 addition | 128 | 5/5 | 0/0 | 300 | 100 |
| p53 addition | 256 | 5/5 | 0/0 | 225 | 100 |
| ordered split | 64 | 5/5 | 5/5 | 875 | 100 |
| ordered split | 256 | 5/5 | 5/5 | 625 | 100 |
| multiplication | 64 | 5/5 | 5/5 | 1850 | 99.627 |
| multiplication | 256 | 5/5 | 5/5 | 1000 | 100 |
| random orbit labels | 256 | 0/5 | 0/0 | 11900* | 4.407 |
| extension: fraction=.7 square | 32 | 0/5 | 0/0 | 11900* | 93.549 |
| extension: fraction=.7 square | 64 | 5/5 | 0/0 | 500 | 100 |
| extension: fraction=.5 ReLU | 64 | 0/5 | 0/0 | 11900* | 25.613 |
| extension: fraction=.5 ReLU | 256 | 0/5 | 0/0 | 11900* | 90.006 |

For n=5, even 5/5 events has 95% Wilson interval [0.565518,1], while 0/5 has [0,0.434482]. These are small scope checks. The ReLU change also changes initial function scale and optimization; it is not an isolated feature-count experiment. The p53 and fraction=.7 cells show that successful generalization need not meet the operational 10× delay definition.

## 3. P1: paired timing, uncertainty, and observability

Define, within each of the ten paired blocks:

- `dM=log2[(uM256+25)/(uM64+25)]`;
- `dG=log2[(uG256+25)/(uG64+25)]`;
- `dL=LC256−LC64=dG−dM`.

**All ten blocks have both clocks observed at both widths: 40/40 component clocks, 20/20 endpoint runs.** The ≥8/10 observability gate is satisfied with no residual censoring. Restricted and observed operational-clock effects therefore coincide for this contrast; no eventual-time bound or successful-only subset is needed.

The unchanged final `statistics.json` reports:

| Effect | Mean log2 difference | Original 20k bootstrap 95% CI | Original 20k bootstrap 97.5% CI |
|---|---:|---:|---:|
| dL: relative clock | 0.205498 | [0.033872, 0.380133] | [0.012046, 0.398389] |
| dM: training clock | −0.473534 | [−0.590526, −0.415037] | **Not emitted** |
| dG: generalization clock | −0.268036 | [−0.399156, −0.151030] | **Not emitted** |

To supply the missing component intervals without patching `analyze.py`, the independent audit enumerates the entire empirical paired-bootstrap distribution. For n=10, there are **92,378 multinomial count vectors**; each has weight `10! / prod(count_i!) * 10^(-10)`. Percentiles use the first support value whose cumulative mass reaches the target. This is exact computation of the **empirical bootstrap**, not an exact finite-sample population-confidence procedure.

| Effect | Exhaustive-bootstrap 95% CI | Exhaustive-bootstrap 97.5% CI | Geometric factor `2^mean` |
|---|---:|---:|---:|
| dL | [0.035580, 0.379473] | [0.011972, 0.404426] | 1.153084 |
| dM | [−0.590526, −0.415037] | [−0.649022, −0.415037] | 0.720198 |
| dG | [−0.402073, −0.151706] | [−0.422819, −0.139389] | 0.830449 |

The 97.5% marginal intervals implement the protocol's conservative two-family adjustment alongside ordinary 95% intervals. They are not a simultaneous band over all secondary endpoints.

The paired log-clock ratio increases by about **15.3%**, not 100%; the promised ≥1 effect is well above both upper bounds. Training's shifted clock is reduced by about 28.0%, while generalization's shifted clock is reduced by about 17.0%. These are geometric effects on `t+25`, not ratios of marginal median times. Eight of ten `dL` values are positive; all ten `dG` values are negative. Full per-block times/effects are in `audit_primary_pairs.csv`.

**Interpretation:** reject P1 as stated because its magnitude fails; support its absolute-generalization direction and the weaker statement that interpolation accelerates more in relative log-clock terms. Do not write that the whole original prediction was confirmed. The 25-update grid, rapid 25–75 update fitting, the prespecified +25 offset, and n=10 limit precision and external scope. For censored width16/32 cells, high `LC` is a finite-budget restricted quantity, not evidence of observed delayed grokking or a known eventual delay.

## 4. P2: unanimous outcomes are not certainty

At width256, all ten decay=1 blocks generalize and none of the paired decay=0 blocks does. The paired sample difference is **1.000**, exceeding the prespecified 0.5 point-effect target. Both 95% and 97.5% empirical paired-bootstrap intervals are **[1,1]** because every resampled difference equals +1. **This degeneracy must explicitly accompany, not replace, population uncertainty.**

| Cell uncertainty | 95% Wilson | 97.5% Wilson |
|---|---:|---:|
| decay=1, 10/10 | [0.722467, 1] | [0.665607, 1] |
| decay=0, 0/10 | [0, 0.277533] | [0, 0.334393] |

The original script's difference envelope `[0.444934,1]` is numerically the difference of the two **95% marginal** Wilson intervals. It is explicitly not an exact paired interval; importantly, two such marginals do **not** automatically give a calibrated conservative 95% difference interval. Even with individually exact 95% intervals, a union-bound simultaneous guarantee would only be ≥90%; Wilson coverage is approximate.

For transparent supplemental uncertainty without assuming independence between paired cells:

- Bonferroni-calibrated Wilson difference envelopes use 97.5% cell intervals for a nominal 95% difference envelope: **[0.331213,1]**; use 98.75% cell intervals for nominal 97.5%: **[0.231638,1]**. These retain Wilson's approximate coverage.
- Replacing Wilson with exact Clopper–Pearson cell intervals gives conservative guaranteed-coverage Bonferroni envelopes **[0.290390,1]** (95%) and **[0.203976,1]** (97.5%), under independent identically distributed joint blocks, with arbitrary dependence within each pair.
- A less loose conservative paired bound uses `D=eventG_decay1−eventG_decay0 ∈ {−1,0,+1}` and `q=P(D=+1)`. Because `E[D] >= 2q−1`, transforming the two-sided Clopper–Pearson lower bound from 10/10 positive pairs gives **[0.383006,1]** at nominal 95% and **[0.290390,1]** at nominal 97.5%. Here the lower endpoint is `2*((1−level)/2)^(1/10)−1`; the upper endpoint is the logical maximum 1. These are conservative bounds, not a replacement analysis selected to obtain significance.

Thus the observed benefit and its direction are strongly supported, but these nondegenerate intervals all include effects below 0.5. **P2's ≥0.5 magnitude is supported by the sample estimate, not established at the stated confidence levels; do not call the [1,1] bootstrap proof of the population magnitude.** Nor does any finite-budget result prove no-decay models can never generalize later.

## 5. P3 and numerical replication audit

The mechanism audit's real-arithmetic result requires narrow hidden epsilon ×4, output LR ×4, output decay ÷4, aligned initial function, and the clone-symmetric trajectory. It is not equality to ordinary width64 AdamW or to random width256.

Across all ten replicated/rate-matched pairs and every saved checkpoint:

| Quantity | Largest absolute difference |
|---|---:|
| Initial full-domain logits (rebuilt initialization) | 7.264316e−8 |
| Training loss | 2.384186e−7 |
| Test loss | 5.109608e−5 |
| Training accuracy | 0 |
| Test accuracy | 0.0020877123 (0.208771 percentage points) |
| Fourier fraction | 6.126139e−5 |
| Logit standard deviation | 0.000273943 |

The largest test-accuracy mismatch is about one held-out example (test size varies by split). **tM and tG agree in all ten pairs**; both medians are 50 and 1250. Mean final test accuracy agrees, but regression counts differ by one saved evaluation for seed103 (39 versus 40). At the saved final state, hidden and output clones remain exactly identical within each replicated model; nevertheless the largest mapped narrow/wide final parameter differences across pairs are **0.0100465** for hidden weights and **0.00506373** for output weights (`4*V_wide−V_narrow`). These are not whole-trajectory parameter error bounds. Small scalar/function discrepancies do not imply exact parameter agreement.

These measurements support **approximate finite-precision implementation agreement**, with no observed endpoint mismatch. They do not negate the real-arithmetic proof and do not establish bitwise equality, long-run stability, or equality between checkpoints. The fp64 100-step unit-test claim in the mechanism audit was not rerun; no new trajectory training was performed.

Design-motivated P3/control comparisons, computed using all ten paired blocks, with exhaustive empirical-bootstrap 95% intervals and **no secondary multiplicity correction** (`audit_secondary_comparisons.csv`):

| Comparison minus reference | Mean paired log2 shifted generalization-clock difference [95% CI] |
|---|---:|
| replicated256 − random256 | 0.483409 [0.385613, 0.584537] |
| rate-matched64 − ordinary64 | 0.215373 [0.068247, 0.357823] |
| rescaled256 − standard256 | −0.128712 [−0.215993, −0.025443] |
| rescaled32 − standard32 | 0 [0,0], **both censored: restricted effect only** |

At the same raw count of 23,808 parameters, random256 generalizes earlier than replicated256 (medians 887.5 versus 1250; geometric shifted-clock factor 1.39804 for replicated/random). This and the function-preserving rescale control undermine a **parameter-count-only** account. They do not isolate feature diversity as the unique causal mediator: initial function, feature parameterization, and effective optimizer coordinates differ between random and replicated settings. Narrow64 with the matching recipe is itself slower than ordinary narrow64, despite having the same starting function. The rescale32 null restricted timing effect is uninformative about eventual times.

## 6. Suspicious outcomes, reporting corrections, and diagnostic caveats

### Retained failures and regressions

No missing completed runs, nonfinite recorded metrics, source-hash mismatches, truncated grids, or grouped reverse-pair overlaps were found. Every one of the 205 runs fits the training threshold eventually. Failure to generalize in narrow/no-decay/random-label/ReLU conditions is retained, not filtered out.

**Weak decay is dynamically unstable, not a clean monotonic dose-response.** Width256/decay=.1/seed100 is the sole 1/10 success: tM=25, tG=10400, best test accuracy 0.997930, final test accuracy 0.939959. It falls below 99% at **56** post-event evaluations, starting at 10625; the worst post-event test accuracy is **0.525880**. Train accuracy between the two clocks falls to **0.914226**, so ordinary delayed-grok classification is true but strict classification is false. Its parameter norm peaks at **272.963310**. These measured fluctuations warrant disclosure and cannot be diagnosed as a training bug from scalar logs alone. No endpoint or optimizer was changed in response.

Four seeds in **each** replicated/rate-matched cell regress below 99% after confirmed generalization: 101,102,103,104. Seed102 first regresses at1500 after tG=1250, reaches a minimum0.979210, and finishes0.981289; both models have387 post-event below-threshold evaluations. Consequently, 10/10 sustained-crossing success is not 10/10 permanent convergence. Ordinary primary width64/128/256/512 cells have no post-crossing <99% regressions in the recorded grid.

### Original analysis omissions / reporting hazards — reported, not patched

1. **Missing adjusted component intervals:** `statistics.json` emits 97.5% for P1 `relative_clock` only, not `train_clock` or `generalization_clock`. Supplemental values are provided above; `analyze.py` remains unchanged. It also does not emit 97.5% Wilson cell intervals; these are supplied here.
2. **Wilson difference envelope calibration:** the original `[0.444934,1]` is an envelope of 95% marginals, not an automatically conservative 95% paired CI. Retain its transparent construction, but do not assign it that confidence interpretation. See Section4 for calibrated alternatives.
3. **Raw `summary.json` endpoints use three evaluations, not the frozen five.** The analysis correctly ignores those summary clocks and reconstructs raw rows. Three runs disagree: primary seed100 width64 has summary/frozen tG875/1000; primary seed106 width256 has800/900; multiplication seed100 width64 has1150/6450. Training crossings agree. Do not copy summary `t_val`, `delay`, or `ratio` into the paper as frozen endpoints. The raw ratio additionally lacks the protocol's +25 offset.
4. **Missing delay-ratio sensitivity:** original `sensitivity.csv` covers the 3×3 threshold/persistence grid but fixes the delay ratio at10. The protocol also specifies ratio3. The supplemental `audit_sensitivity.csv` includes both; in the primary cells, none of the54 threshold/persistence/width grok counts changes between ratios3 and10. No definition was selected after seeing results.
5. **Shared global bootstrap RNG:** including the completed extension changes RNG consumption before P1, although the main samples are unchanged. The main-only dL 95% interval was `[0.035029,0.378222]`; the final all205 script interval is `[0.033872,0.380133]`. The point estimate is identical. This is Monte Carlo/order dependence, not evidence from the extension changing the primary data. Exhaustive supplemental bootstrap values remove this simulation variation. No RNG/code patch was made.
6. **Scalar trajectory wording:** the original replication block computes differences for train loss, test loss, and test accuracy, not literally every scalar. Coordinate norms should not be expected to match. Additional functional diagnostic differences are supplied in Section5.

### Norms and Fourier: what they can and cannot show

Raw norm is `sqrt(||W||_F^2+||V||_F^2)`, not a parameterization-invariant complexity measure. For exact r-fold replication it becomes `sqrt(r||W||_F^2+||V||_F^2/r)`; balanced `W→cW,V→V/c²` also changes norm while preserving the square-network function. Indeed replicated/rate-matched final mean norms are **52.442859 versus64.077446** despite close functions; standard/rescaled width256 initial means are **9.793425 versus13.179770** with function preservation. Primary standard initial logit standard deviations remain near0.0095–0.0097 across widths, whereas norms increase strongly with width. Norm change alone therefore does not establish compression, circuit competition, minimal-norm selection, or the cause of grokking.

Fourier fraction is centered **raw-logit energy** on `(k,k,−k), k≠0`, divided by total 3D DFT energy. Its final-state calculation was independently checked on every applicable model. It is a translation-compatible functional diagnostic, not a latent-feature/circuit count or causal mediator. Uniform logit rescaling leaves it unchanged, while example-dependent margins or other function changes can alter it without changing classification. It includes all input pairs and output classes; it is not a held-out-accuracy metric and should not be presented as independent confirmatory evidence from a second dataset.

Descriptive final mean fractions illustrate association, not equivalence: primary width32 **0.442733**, width64 **0.707144**, width256 **0.797335**; replicated/rate-matched **0.627289/0.627287**; no-decay width256 **0.256994**. ReLU256 reaches **0.490966** yet has0/5 sustained99% successes. The diagnostic is deliberately absent for multiplication/random labels, where the addition-mode interpretation is inappropriate. No mediation analysis or internal-circuit intervention was performed.

Ordered controls have mean reverse overlap **0.470686**, with a reverse-lookup-plus-majority baseline accuracy **0.480249**. Grouped primary runs have zero overlap; the same baseline reduces to the majority fallback, mean **0.016403**. Thus ordered-split performance is not evidence for leakage-free generalization. Random-label test accuracy4.407% is not exactly the uniform1/31 baseline3.226%; with only five blocks and no dedicated null test, do not assert exact chance equality or infer a mechanism from the small excess.

Prespecified sensitivity is largely stable at95%/99% thresholds: widths16/32 never generalize and widths64+ always do for persistence3/5/9. At99.9%, widths64 and128 have9/10 successes for persistence5/9, whereas widths256/512 retain10/10. Do not silently upgrade the primary99% conclusion to universal perfect or arbitrarily persistent convergence.

## 7. Concise paper interpretation and next steps

- **Rejected:** the deliberately strong P1 prediction that widening64→256 at least doubles the generalization-to-fit clock ratio. All its relevant clocks are observed, and the effect is much smaller than promised.
- **Supported within the measured setting:** faster absolute generalization alongside a modest relative-clock increase; a large finite-budget decay benefit; approximate clone/rate optimizer-coordinate correspondence; and behavior inconsistent with raw parameter count being sufficient by itself.
- **Inconclusive / not established:** P2's population magnitude≥0.5 at the stated adjusted confidence level; eventual behavior of censored runs; a universal width threshold; permanent convergence after the first confirmed streak; generic narrow/wide equivalence; a unique feature-diversity mediator; distinct memorization/generalization circuits; causal Fourier/norm mediation; or transfer to broader architectures/tasks/training recipes. P3's real-arithmetic proof remains conditional on exact clone symmetry and matching coordinates.
- **Exploratory scope only:** transfer-modulus, ordered/multiplication/random-label controls, rescaling comparisons, and the fraction/ReLU extension. They expose boundaries but do not rescue the failed P1 magnitude or create new primary confirmation. Secondary intervals are descriptive and uncorrected for their many comparisons; no new significance claims or outcome-dependent experimental selections were made.

Future work only, **not selected or run as part of this frozen study**: (1) a separately frozen larger fresh-block replication to narrow P2 uncertainty and prespecify regression/permanent-convergence endpoints; (2) a higher-precision numerical stability audit of the clone/rate identity with parameter and function discrepancies logged; (3) a separately designed matched-function intervention isolating feature diversity before claiming causal mediation. These recommendations do not alter the present protocol or rescue its failed prediction.

### Files produced / sources of every reported number

All paths below are under `/work/analysis/` (the requested audit location):

- `independent_audit.md`: this audit and interpretation.
- `independent_audit_recompute.py`, `independent_audit_supplement.py`: reproducible independent calculations, without training.
- `audit_checks.json`: check results, hashes, exact-bootstrap P1 intervals, P2 uncertainty, complete regression and replication summaries.
- `audit_endpoints.csv`, `audit_primary_pairs.csv`: every reconstructed endpoint and all ten primary paired effects/times.
- `audit_cells.csv`: all measured cell counts, medians, and original 95% final-accuracy bootstrap intervals.
- `audit_sensitivity.csv`: complete primary threshold/persistence/delay-ratio sensitivity counts.
- `audit_diagnostics.csv`, `audit_diagnostic_cells.csv`: per-run and cell-mean norms, Fourier fractions, baselines and regression diagnostics.
- `audit_secondary_comparisons.csv`: all four design-motivated P3/control contrast calculations, with clearly secondary intervals.
- `audit_regression_details.json`, `audit_final_replication_parameters.json`: raw-derived instability details and final clone/parameter mismatch checks.
- `audit_bootstrap_rng_order.json`: recomputation of original primary CI changes caused solely by main-only versus main-plus-extension RNG consumption.
- `independent_audit_recompute.log`, `independent_audit_supplement.log`: execution logs.

Original unpatched-script outputs remain `runs.csv`, `curves.csv`, `group_summary.{json,csv}`, `statistics.json`, `primary_pairs.csv`, `sensitivity.csv`, `main_table.tex`, `results_summary.md`; final unchanged analysis stdout is `/work/analyze_audit_run.log`. The script-generated table is an existing analysis output, not a newly drafted manuscript. No figures were produced.
