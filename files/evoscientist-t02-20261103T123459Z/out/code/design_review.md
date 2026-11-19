# Design review: a finite-budget falsification study

## 1. Assumptions, scope, and verdict

This is a proposed protocol, not experimental evidence. Reviewed only `/work/todos.md`, `/work/research_request.md`, `/work/train.py`, and `/work/literature_notes.md`; no experiments, code changes, external literature, or web access. Apply the paper-planning workflow: narrow the claim, design controls first, and anticipate rejection risks.

**Recommendation:** target a specific width/AdamW/parameterization account, not a universal mechanism: in this quadratic addition model, (W) increasing width preferentially accelerates interpolation, and (C) changing decay primarily changes a regularization clock governing generalization. Test W and C separately. A failure rejects the corresponding operational prediction, not every feature-selection theory. A generic width sweep is not a first discovery; the local notes already document previous model-wise grokking.

Use **176 runs maximum for the core design**, including 16 independent pilots; optionally 16 second-modulus runs, giving **192 total**. Keep confirmatory seeds **0–7** untouched until the protocol is frozen. Prefer replication and normalization controls over adding operations or models. No transformer replication or universal width law is claimed.

### What the actual architecture implies

For width h and class c, the script implements

`f_c(a,b) = h^(-1/2) sum_j R[j,c] (A[a,j] + B[b,j])^2`.

- There are **3ph parameters**, not quadratically many parameters in h. At p=31 and h=8…256 this is **744…23,808**. “Quadratic” describes activation/parameter homogeneity, not parameter-count growth.
- Initially A,B have variance 1/2 and R variance 1. For each fixed input, E[f_c²]=3, independent of h; expected class-centered RMS² is `3(1-1/p)`. Individual seeds still differ. This is an ensemble statement, not proof of identical kernels, learning speeds, or width-invariant function distributions.
- Mean normalization divides by h instead: initial RMS is smaller by approximately sqrt(h). A raw sqrt-versus-mean comparison changes confidence, gradients, effective optimization and decay competition together.
- All three parameter tensors are decayed in the trainable model. With only multiplicative decay, `q=1-eta*lambda`, parameters shrink as q^t and logits as **q^(3t)**. The frozen-feature model has only its readout optimized/decayed, so its decay-only logits shrink as q^t instead. Do not interpret frozen and trained networks as sharing an identical decay mechanism.
- The squared features contain A²-only, B²-only and 2AB terms. The network has additive/input-constant nuisance components as well as interactions. Raw total norm is not a circuit decomposition; report layer RMS and centered logit components.

## 2. Operational hypotheses and the approximate-clock problem

### W: preferential interpolation acceleration

Primary width contrast: h=32 versus h=128, under sqrt normalization and the pilot-selected common recipe. Hypothesis: the high/low-width train-event time multiplier is smaller than the corresponding held-out multiplier. The other four widths map the range and reveal capacity failures; they are not six independent hypothesis discoveries.

Define a practically meaningful preferential acceleration as a **1.25-fold relative advantage**, i.e. a train/evaluation multiplier ratio <=0.8 (20% lower). Also report the weaker directional prediction (<1). This margin is a proposed scientific commitment, not a known law. Report interpolation incidence before talking about an “above-interpolation” regime.

### C: a prespecified clock, not a fitted explanation

For the script's constant-rate AdamW, verify the installed optimizer's semantics locally, then record

`r(lambda) = -log(1-eta*lambda)`, `C(t)=t*r(lambda)`.

Use `-log1p(-eta*lambda)` numerically. For schedules, use the sum of per-update rates, not eta*lambda*t. The usual approximation `C≈eta*lambda*t` is close here, but bookkeeping precision is not mechanistic identification.

A strict total-time inverse-clock model predicts similar generalization-event distributions in C across lambda0/2, lambda0, 2lambda0. It predicts elasticity approximately -1 for log generalization time versus log r, wherever event times are observable. A useful sharpened target is **clock-time ratios within [0.8,1.25]**. For doubling decay this corresponds approximately to raw time ratios [0.4,0.625]. Freeze this target before confirmation.

The current proposed “within factor two after rescaling” is too permissive: doubling decay predicts a time ratio of 0.5, but its factor-two tolerance is [0.25,1], admitting no acceleration at its boundary. Do not call mere overlap of rescaled curves confirmation. **Distinguish falsifying this original loose prediction from falsifying the new sharpened model.** Where all paired events are observable, also report the original doubling-decay contrast at each primary width (lambda0 versus 2lambda0); an uncertainty interval wholly outside [0.25,1] contradicts its loose quantitative prediction. A result outside the sharpened margin but inside this original range does not reject the original tolerance. These additional comparisons are secondary unless explicitly included in an expanded multiplicity family before launch.

Additional limitations:

1. `C(t)` exactly describes the decay-only multiplicative factor, **not actual parameter norms or circuit strength during training**. Adam moment states, gradients and evolving features remain active. Shrinkage of a cubic predictor does not by itself explain why a rule wins.
2. A lower norm can coexist with worse or better generalization. A high projection fraction can arise because residual energy disappears, without rule energy growing.
3. Learning-rate changes also change the adaptive gradient step. Matching eta*lambda while changing eta is not a clean causal decay control; omit that expansion from this minimal study.
4. Total-time and post-interpolation clocks are different hypotheses. The primary clock starts at initialization. A later claim about a post-fit clock requires the predeclared fixed-landmark sensitivity below; do not retrofit a seed-specific offset to rescue a failed total-time collapse.
5. No-decay generalization rejects “decay is necessary” in this recipe, not necessarily “positive-decay transitions have clock dependence.” No transition at zero decay by H establishes only a finite-budget bound.

## 3. Stages and fixed run ledger

### Stage 0 — audit and freeze measurement definitions; no training runs

**Goal:** ensure data, projection, optimizer, event and normalization comparisons mean what they claim.

**What to run later:** unit/audit checks of exhaustive labels, split hashes, projection identities, event extraction, exact parameter counts, AdamW group masks, deterministic CPU execution and checkpoint metadata. Do not add external data. Add the minimal logging described below before confirmation; the present script is not yet sufficient for every diagnostic.

**Success signals:** all checks pass; no optimizer access to held-out labels/logits; independent RNG streams documented; malformed/nonfinite runs are flagged rather than converted into successful/censored runs.

**Artifacts:** audit report, dependency lock, source hash, frozen protocol JSON and full run manifest.

### Stage 1 — independent pilots; at most 16 runs

**Settings:** p=31, addition, fraction=.30, full-batch CE, float32 CPU, AdamW betas=(.9,.98), eps=1e-8, eta=.01, sqrt normalization, evaluation every 50 updates, one thread/process.

1. Seeds **900,901** × h={32,128} × lambda={.05,.1,.2}: **12 runs**, H=12,000.
2. Choose one common lambda0 deterministically: prefer .1, then .05, then .2 among recipes for which all four pilot runs interpolate by 3,000 updates and at least one seed at each width has a sustained held-out event between twice its interpolation time and 9,000 updates. If none qualifies, stop this recipe as unestablished; do not choose a “best seed.”
3. Seeds **902,903** × h={32,128} at that recipe: **4 runs**, up to H=24,000, with complete logging.

These pilots may use their own full complement for development. They are not included in confirmatory estimates. Inspecting the first 12k of the last four runs allows choosing H=12k versus 24k without touching seeds 0–7.

**Success signals:** at least 3/4 validation runs interpolate by H/4, and at least 2/4 have a sustained held-out event between twice their interpolation time and .75H; representative widths both show learning. These are feasibility gates, not required confirmatory outcomes. Check whether half/double decay is likely observable; do not choose H solely from the fastest decay. Freeze H=12k if these gates hold at 12k, otherwise 24k if they hold there. Failing both gates is a reportable failure to establish the delayed-generalization test bed.

**Budget gate:** measure total wall time including evaluations. Project the complete ledger conservatively by width and horizon (use at least 1.5× the largest observed per-update time as a provisional upper estimate for h=256). Require projected execution <=120 CPU-hours, leaving roughly 40 hours of a one-week single-core budget for diagnostics, analysis, reruns of technical failures and writing. With full 24k validation pilots, the core ledger uses approximately 2.16 million updates at confirmatory H=12k, or 4.08 million at H=24k. At the latter horizon, 120 CPU-hours permits about 0.106 seconds per update averaged over the ledger, including amortized evaluation; this is an arithmetic budget target, not a measured speed. If infeasible, lower H only if pilot gates still hold; otherwise halt/defer the design. Do not silently sacrifice seeds or controls.

**Artifacts:** all 16 pilot configs/curves including failures, timing table, selection record and signed/hash-stamped protocol before any confirmatory launch.

### Stage 2 — width and clock falsification; 96 confirmatory runs

All rows use paired **seeds 0–7** and the same frozen H, data fraction, eta and evaluation schedule.

| Block | Widths | Decays | New runs |
|---|---|---|---:|
| Main sqrt width sweep | 8,16,32,64,128,256 | lambda0 | 48 |
| Clock and no-decay controls | 32,128 | 0, lambda0/2, 2lambda0 | 48 |

Reuse the lambda0 runs; never rerun them as nominally independent baselines.

**Success signals:** interpretable paired width effects; observable/interpretable clock comparisons or explicit bounds; every planned seed retained. “Successful stage” means a decisive or honestly inconclusive test, not acceptance of the account. If fewer than 6/8 seeds at either primary width interpolate by H/4, explicitly mark the claimed above-interpolation regime as poorly established; do not filter those seeds out.

**What to run:** parameterized invocations of the existing `/work/train.py`, e.g. `python /work/train.py --p 31 --fraction .3 --width 32 --seed 0 --lr .01 --decay <lambda0> --steps <H> --eval-every 50 --threads 1 --tag confirm --out /work/results/confirm`. Expand from a frozen manifest, not manual curve-driven choices. Output tags must distinguish every intervention and prevent file collisions.

**Artifacts:** configs, raw CSVs, final checkpoints, completion/failure ledger, six-width train/held-out curves, censor marks, matched-clock event curves and per-seed paired contrasts.

### Stage 3 — mechanism and normalization stress tests; 64 confirmatory runs

Use widths {32,128}, all eight seeds, selected lambda0, same H and split membership.

| Block | Intervention | Runs |
|---|---|---:|
| Frozen features | Existing `--frozen`: train readout only | 16 |
| Shuffled labels | Existing `--shuffle`: full-table label permutation before split | 16 |
| Raw mean | Existing `--normalization mean` | 16 |
| Function-matched mean | Mean normalization, initialize R_mean=sqrt(h)*R_sqrt; same A,B | 16 |

**Important handoff:** the last block is a design recommendation requiring a later implementation change; the current CLI cannot run it. This review implements nothing. Ensure tags/configs record the intervention explicitly; current filenames alone do not encode it.

Function-matched mean starts with **identical logits** to sqrt for a fixed h and seed, but a different readout parameterization. Keep the readout learning rate unchanged for this sensitivity: Adam's approximately scale-invariant coordinate update becomes a smaller effective function update after dividing the mean readout by sqrt(h). Therefore this is a parameterization stress test, not a fully dynamics-matched experiment. Multiplying mean logits by sqrt(h) externally would merely recreate sqrt and is not an independent control. Simply applying a GD alpha^-2 learning-rate rule to AdamW is unjustified.

**Success signals:** initial paired logits match numerically in the function-matched arm; raw-mean RMS follows its expected scale change; width contrasts are reported separately for each convention. A changed width effect exposes recipe dependence, not automatically a capacity effect or a clean normalization mechanism. With two widths these are stress tests, not universal scaling fits.

Frozen features must be evaluated for training interpolation before interpreting failure to generalize as evidence of feature learning. At h=32/128 there are fewer frozen features than 288 training pairs, so inadequate random-feature capacity is a real alternative explanation. Do not call this a capacity-matched kernel control. Shuffled labels test memorization under the same task-independent training procedure; they are not expected to obey the same modular-rule projection or cubic trainable-feature competition quantitatively.

**Artifacts:** initial-logit identity check; baseline/control table of interpolation, held-out incidence, loss and energy; raw and matched-scale normalization plots with paired points.

### Stage 4 — analysis and audit; optional 16 runs

**Core total:** 16 pilots + 48 width + 48 decay + 64 controls = **176 runs**. No sweep extensions after inspecting confirmatory outcomes.

If CPU budget remains, preregister **before confirmation** an optional replication at p=23, widths {32,128}, seeds 0–7, addition, sqrt, selected recipe and H: 16 additional runs (**192 total**). Keep its inference separate: changing p at fixed fraction changes absolute sample count. Do not substitute a second operation merely because it looks more favorable. Under pressure, omit this optional block first.

**Success signals:** every numeric claim traces to raw artifacts; no pilot/confirmation mixing, hidden exclusions, best-seed illustrations, or unreported stopped runs. Negative outcomes retain an explicit fallback contribution: a reproducible boundary or falsification of the narrow clock/width account.

**Artifacts:** analysis tables with paired effects and uncertainty; width/update and matched-clock figures; projection energy plots; protocol deviations; CPU-time/accounting table and claim-to-evidence audit.

## 4. Exact modular-rule projection on the full grid

Retain the existing exact diagnostic, not a selected-frequency approximation. In canonical ordered-pair order, evaluate logits Z on **all p² inputs**. Center every example across classes: `Zc=Z-mean_class(Z)`. For the true rule r(a,b), define

`M[k,c] = average of Zc[a,b,c] over all pairs with r(a,b)=k`,
`PZ[a,b,c] = M[r(a,b),c]`.

This is the empirical orthogonal projection onto **all functions of the known rule output**, using the uniform full-grid inner product. For addition/subtraction each output has p preimages; division is absent here. Multiplication would have unequal counts, which must be honored; the script's averaging does so. For p=31 the row-centered rule subspace has dimension p(p-1)=930, including 30 input-constant class-bias directions. It is broader than “the learned Fourier circuit.”

**Required checks:** canonical row order; idempotence; `sum(PZ*(Zc-PZ))≈0`; reconstruction and energy conservation; row means zero; class-offset invariance; known rule-only synthetic logits project exactly; label-independent nuisance examples behave as expected. Use explicit float tolerances scaled by tensor norms, not exact bit equality.

**Required diagnostic additions:** the current `rule_energy` logs only a fraction. Also log per-entry squared energies of PZ and Zc-PZ, and split off the global class-bias component `B=mean_input(Zc)`; report `PZ-B` as nonconstant rule energy and `Zc-PZ` as residual. Record projected and residual train/held-out CE and accuracy, original centered-logit RMS, plus layer RMS/movement. Do not interpret a growing fraction without absolute energies. Final checkpoints alone cannot reconstruct missing trajectory diagnostics.

**Leakage/interpretation warning:** grouping uses the known exact rule and predictions on held-out inputs. That is permitted for a frozen, retrospective mechanistic diagnostic, **not a deployable held-out predictor, training signal, checkpoint selector, or hyperparameter objective**. `projected_eval_acc` is oracle-assisted and can inherit train-example logits within each rule group. A residual can contain useful non-rule information; its norm is not ground-truth memorization. Report the shuffled model's projection against the original true rule separately from accuracy against shuffled labels; the present script mixes these meanings unless labeled carefully.

## 5. Evaluation protocol, uncertainty and falsification decisions

### Splits and pairing

For p=31, fraction .30 gives **288 training and 673 held-out ordered pairs**. Labels are exact integer modular addition; validate all pairs, uniqueness, disjointness, exhaustive coverage, label counts, operand coverage and split hashes. Inspect coverage without rejecting difficult seeds. Addition labels are marginally balanced on the full grid.

Use the training subset and its full complement as the two-way split already implemented. Hyperparameters are selected only on independent pilot seeds. The confirmatory complement may be logged repeatedly by an automated fixed procedure, but no settings or H may be altered from its curves. This is not a third, untouched test set.

Within each seed, reuse exact split membership and label permutations across widths/arms. Same-h decay/frozen/normalization comparisons should reuse base initial tensors; different-width networks sharing a seed are **not** identical or automatically nested initializations in the present script. Verify rather than claim stronger pairing. Seeds jointly vary split and initialization: eight seed clusters estimate joint variability, not separate variance components. Grid examples and checkpoints are not independent replicates.

### Events and right censoring

Primary events: >=99% train/held-out accuracy for **three consecutive evaluations**, recording the first of those evaluations. Keep 90%/95% as prespecified sensitivities; also report CE curves, fixed-budget accuracy and loss. At cadence Delta=50, the latest confirmable onset is `tau=H-2*Delta`. If no onset by tau is established, record event status 0 and censor at tau. Do not replace missing times with H and call them observed events. Mark numerical failures separately from administrative censoring.

Events are grid-defined and interval-limited, not exact continuous transition times. Report the cadence uncertainty; a one-checkpoint excursion does not count. Continue every run to H regardless of early interpolation/generalization. Do not select best-checkpoint held-out accuracy as the primary result.

### Primary three-contrast family

Use paired seed-cluster contrasts; exact enumeration of **2^8 sign flips** for two-sided paired mean-difference tests, with **Holm correction across these three contrasts at family-wise alpha=.05**; interpret the sign afterward. State the exchangeability/symmetry assumptions: paired sign-flip inference is not made assumption-free by calling it exact. Provide all eight paired values and a paired cluster bootstrap (e.g. 10,000 resamples) for effect-size intervals; n=8 intervals and power are limited. Do not resample individual table entries as independent training replications.

1. **Width preferential acceleration:** define `Y_k(h)=log(1+min(T_k(h),tau)/Delta)` for train and held-out events, taking min= tau for an administratively censored run. Test the paired contrast
   `D=[Y_train(128)-Y_train(32)]-[Y_eval(128)-Y_eval(32)]`.
   This is a valid **restricted-time endpoint**, not an imputation of the true censored event. exp(mean D) approximates the relative train/evaluation time multiplier for late, uncensored transitions; label its exact offset/capped interpretation otherwise. Report separate train and held-out restricted effects and incidence so a negative D cannot hide universally failed learning. Supporting the original acceleration story additionally requires a negative train-width effect: a negative D while both train and evaluation times increase is not evidence that larger width accelerates fitting.
2. **Clock collapse at h=32:** compare lambda0/2 versus 2lambda0 on a common clock horizon as below.
3. **Clock collapse at h=128:** identical comparison, not a pooled width average that can cancel opposing effects.

For each clock test, re-index existing accuracy logs onto a **common C-grid** with spacing `deltaC=max(r)*Delta` for the two decays, using the first recorded evaluation at or after each requested clock time; the sampling overshoot is at most r*Delta per arm. Require three consecutive common-clock evaluations, rather than persistence over different decay-scaled durations. Choose the largest grid endpoint <= `min(r)*H` whose required evaluations exist in both logs; the last possible onset is two common-clock bins earlier, called kappa. Thus both arms have the same observable clock horizon. Repeat extraction using the preceding rather than following evaluation as a cadence sensitivity; if the conclusion changes, report unresolved timing rather than a clock rejection.

Let U be that clock-grid generalization onset. Define `A=min(U,kappa)/kappa`, retaining non-events at the cap. The paired clock contrast is **K=A_double-A_half**; expectation zero is the operational collapse prediction. Mean A is a normalized restricted mean clock-event time; report the difference, ratio of restricted means, fixed-clock event incidence and curves. Large common censoring can force K toward zero: all-censored data do not support collapse. This protocol equalizes observation duration rather than comparing complete cases with unequal event availability.

### Effect sizes, uncertainty and decisions

- Report 95% intervals for D, exp(D), K, restricted mean ratios, paired event-incidence differences, and fixed-H CE/accuracy differences. Show Wilson intervals for each arm's event incidence, explicitly not a paired-difference interval. Report medians only when identifiable; otherwise provide lower bounds.
- For W, a negative corrected contrast supports the directional prediction for the restricted endpoint. An interval entirely above zero is evidence against its direction. An interval entirely above `-log(1.25)` excludes the proposed 1.25-fold advantage **for the restricted endpoint**; crossing either margin is inconclusive. When held-out events are mostly censored, faster train events alone cannot establish that actual held-out learning is comparatively slower; say so explicitly. Holm-adjusted tests govern confirmatory declarations; ordinary 95% effect intervals are clearly labeled unadjusted, with simultaneous/conservative intervals if making family-level claims.
- For C, require corrected evidence of K!=0 **and a meaningful discrepancy** (proposed |K|>=.15, with its interval beyond that margin; equivalently an unnormalized restricted mean difference >=.15*kappa) for a strong finite-horizon falsification. If all eight event pairs are observed, additionally report paired log clock-time ratios and elasticity, with a 25% equivalence margin. Equivalence requires its interval wholly inside the margin, not p>.05 for a difference test. Sparse events or wide intervals are inconclusive, not support.
- The .15-kappa rejection margin and 25% ratio margin are distinct predeclared effect scales, not interchangeable laws. Always show the continuous estimates; strong effect-size statements can be underpowered with eight seeds.
- If censoring is negligible, report paired log(T_eval/T_train) and log-event-time contrasts directly as supplementary mechanistic summaries. Never compute those only in successful seeds and present them as the population effect. Survival displays retain every administrative censor; no parametric survival extrapolation or complex frailty model is needed at n=8.

**Clock-origin sensitivity:** at the fixed landmark L=H/4 (rounded to an evaluation), repeat a common-clock restricted analysis of time after L, setting already-generalized runs to zero and retaining every seed. Record whether all arms had interpolated by L. If not, the sensitivity does not isolate post-fit selection. It is secondary and cannot erase rejection of the initialization-clock hypothesis. Actual `T_eval-T_train` is descriptive only when both events are observed, unless a separately specified censored multistate analysis is added.

All additional width contrasts, lambda0 intermediate curves, normalization interactions, projected diagnostics, alternate thresholds and optional modulus results are labeled secondary/exploratory. A causal circuit claim would need stronger interventions than oracle logit projection; this study need not make one.

## 6. Dependencies, environment preflight and iteration triggers

### Preflight to run later, not performed in this review

- Record Python, OS, CPU model/physical cores, available RAM, BLAS backend and PyTorch version; `torch` and `numpy` are training dependencies. Recommended analysis packages: `pandas`, `scipy`, `matplotlib`, `pytest`; freeze exact installed versions. Standard-library JSON/CSV/hash utilities suffice for manifests.
- Set OMP/MKL/OpenBLAS and PyTorch intra-op threads to 1; inter-op to 1. Begin with one process, then permit only a measured small number of CPU workers that do not oversubscribe memory/cores. Account in CPU-hours as well as elapsed wall time.
- GPU/CUDA/VRAM are **not required**. Record availability once if relevant, but do not change device mid-confirmation. CPU deterministic tests and fixed versions remain the protocol. No new package, literature or repository retrieval is needed to design these experiments.
- Check disk free space and estimate logs/checkpoints before launch; reserve at least 2 GB. Models are small, but retain one final checkpoint per run, raw logs and all metadata. Measure peak resident RAM, diagnostic overhead and actual complete-run times; do not infer feasibility solely from parameter count.
- Freeze source hash, seed manifest, split/initialization hashes, optimizer masks and all primary decisions before seeds 0–7. The existing script records several of these but needs additional trajectory diagnostics and intervention identity. This is a future handoff, not implemented here.

### When to change course

- **Audit failure:** fix and repeat audits before training; a numerical/implementation failure is not scientific falsification.
- **Pilot no-delay/no-fit:** report recipe failure; do not spend the confirmatory budget chasing a visually appealing transition. Any change to fraction, eta, modulus, objective or model is a new exploratory protocol using new seeds >=900, with a newly allocated budget—not a hidden amendment.
- **Budget failure:** drop only the preregistered optional p=23 block first; if the core remains infeasible, defer rather than underpower it after seeing outcomes.
- **Confirmatory censoring:** retain it. Do not extend only slow widths/decays. Any uniform extension must have been budgeted and frozen in advance; the present design has no automatic post-outcome extension.
- **Width effect changes under normalization:** narrow the conclusion to recipe dependence. Raw mean alone cannot establish an output-scale-independent width effect; even function-matched mean changes coordinate dynamics.
- **Clock fails but projection looks attractive:** reject the operational clock, report diagnostic trajectories and alternatives without fitting a new offset/exponent and claiming confirmation. A new clock requires a new independent study.

## 7. Pre-emptive rejection risks and bounded claims

| Likely criticism | Mitigation and remaining limitation |
|---|---|
| Width-wise grokking is already known | No first-width or universal novelty claim; emphasize prespecified falsification and parameterization boundaries. |
| An inverse-decay fit was assumed rather than tested | Exact optimizer clock, fixed effect margins, half/double intervention, common-clock horizon and independent seeds; still not a microscopic feature-selection proof. |
| Width is optimization/output-scale in disguise | State sqrt convention; raw and function-matched mean controls; report layer RMS and movement. No claim of fully isolated capacity. |
| Only successful transitions were analyzed | Censor-safe restricted endpoints, event incidence, all seed pairs and complete failure ledger; n=8 remains low power. |
| Oracle projection manufactured a mechanism | Exact full-grid definition, bias removal, absolute energies, no model selection from diagnostics; no circuit identity claim. |
| Frozen features failed because they lacked capacity | Measure interpolation and feature capacity explicitly; use failure only conditionally, not as proof of learned-rule necessity. |
| Pilot selection inflated the result | Separate seeds >=900 from 0–7, freeze once, retain pilot failures; inference is conditional on the pilot-selected recipe. |
| Results are narrow or transitions remain censored | Admit the finite horizon, two-way synthetic split, single architecture and AdamW regime. Optional p=23 checks a boundary, not universality. |

**Permissible endpoint:** “Under the frozen quadratic/AdamW recipe, the prespecified preferential-width and/or inverse-clock prediction was supported, contradicted, or unresolved within a finite CPU budget.” No outcome here establishes the first width effect, a universal monotonic law, or an identified general mechanism of grokking.
