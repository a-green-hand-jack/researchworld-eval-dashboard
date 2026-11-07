# Width, decay, and delayed generalization: a CPU-bounded empirical plan

## 1. Assumptions, scope, and independence

- **Execution owner:** the main agent implements everything; this document contains no implementation. No human decisions are required. Total elapsed budget is **168 hours**, including pilots, failures, analysis, and manuscript production. CPU is the default; do not assume a GPU.
- **Research inputs used:** `/work/research_request.md` and `/work/artifacts/research_support.md`. No web, original papers, other workspace research files, or external model code were inspected for this plan. Source claims below are second-hand summaries from the support document, not newly verified paper readings.
- **Independence exception:** a higher-priority mandatory memory preflight accessed the prior-topic observation `O-04331dce2fbac114`. Exclude that observation from research evidence and record this access in the eventual independence audit; do not claim there was no prior-topic exposure. A required generic `paper-planning` skill was also read for workflow, not topical evidence. No identity of a forbidden paper was inferred.
- **Smallest defensible contribution:** a controlled empirical test of whether an apparent width effect in a particular quadratic modular-addition network reflects decay-dependent learned representations, rather than simply initialization, optimizer scaling, initial random features, or finite runtime. **A width sweep is not a novelty claim.** Do not promise publication-level novelty or universal grokking theory.
- Data are all ordered pairs `(a,b)` with label `(a+b) mod p`. Primary modulus is **31** (961 examples). Widths are **8,16,32,64,128,256**. Results concern interpolation in one finite operation table, not arbitrary arithmetic or unseen moduli.
- This is a new small surrogate experiment, **not an exact reproduction** of a transformer recipe. An expensive transformer anchor is unnecessary under this budget.

### Working hypothesis and falsifiers

**H:** with variance-normalized initialization and a fixed AdamW recipe, width changes the rate at which learned hidden representations support sum-structured logits. Weight decay favors that route relative to sample-specific fitting. Thus a wider network's earlier generalization should be enhanced by decay, depend on hidden-feature learning, and survive a check that matches initial function-update scale and decay exposure.

Predictions, all conditional on this architecture and finite budget:
1. At fixed updates, the width advantage at decay-on exceeds the width advantage at zero decay.
2. A fixed, task-defined structural projection gains strength before or through generalization; removing it damages held-out margins more than matched random projections.
3. Readout-only training of initial features does not reproduce the full nonlinear width-by-decay result. Removing decay after training memorization delays or weakens later generalization.
4. Random labels can be memorized in sufficiently wide models but do not show additive generalization.

Any one prediction can fail. In particular, equivalent frozen-feature performance refutes a *necessary learned-feature* account; disappearance after update-scale matching favors an optimization-scaling explanation. Decay-free generalization refutes necessity of decay, not necessarily a local decay interaction. A null interaction refutes the stated directional prediction even if grokking is visible.

## 2. Frozen model and optimizer specification

Use two untied input lookup matrices `A,B` of shape `width × p` and readout `V` of shape `p × width`, no learned biases, no embeddings beyond these lookups, no normalization layers:

`h_j(a,b)=A[j,a]+B[j,b]`

`phi(h)=(h^2-1)/sqrt(2)`

`f_c(a,b)=sum_j V[c,j]*phi(h_j(a,b))/sqrt(width)`.

Initialize independent `A,B ~ Normal(0,1/2)` and `V ~ Normal(0,1)`. Consequently each preactivation has variance one, each feature has zero ensemble mean and unit second moment, and each logit has width-independent ensemble second moment. These statements are about initialization distributions, **not equality of realized logits, kernels, or learning dynamics**. Center logits across classes for diagnostics; softmax CE itself is gauge invariant. The fixed feature centering is an intentional architectural choice and must be reported. Parameter count is `3*p*width`: 744–23,808 at p=31, far below the cap.

**Do not use an unnormalized sum or a 1/width readout without explicitly changing the hypothesis.** Width-independent initial logit variance does not imply AdamW function steps are width-independent. Same seed also does not imply identical initial functions across differently sized networks. Couple per-unit initialization streams across widths where practical, but document the coupling and normalization.

Default full-batch AdamW: constant LR `3e-3`, betas `(0.9,0.98)`, epsilon `1e-8`, no warmup, no clipping, float32. All three matrices are decayed. Main decay levels are **0 and 1**. Freeze exact settings after the bounded pilot; if the common positive coefficient changes, name it `lambda_star` throughout. Define the convention as decoupled shrinkage with factor `1-eta*lambda` per update and verify the framework behavior. Log `sum_t log(1-eta_t*lambda)`; never substitute adaptive-gradient L2 regularization.

**Initialization audit:** training-set centered-logit RMS, initial CE, margin spread, per-layer RMS/norm, gradient RMS, and 1/10-step function-update RMS. Use training inputs only for calibration. A >25% systematic width difference in RMS or initial function movement is a confound flag, not an excuse to silently normalize final runs.

## 3. Evaluation, primary contrasts, and data quality

### Splits and selection protection

- Default fractions **30/10/60%**: 288 train, 96 validation, 577 final test at p=31. Save exact memberships and hashes, not just PRNG seeds. Uniform ordered-pair sampling is the primary split; do not quietly enforce class balance after seeing results.
- Pilot blocks use separate split/initialization seeds from frozen blocks. Pilot complements and any pilot test-like metrics are exploratory forever. Freeze final split seeds before opening final-test results; no seed rejection for an inconvenient outcome.
- Default **5 independent blocks**, each with its own split and initialization seed, matched across every width/decay/control cell. The inference unit is the whole block. This samples joint split/init variation but cannot separately estimate their contributions. If 10 blocks are affordable, decide that **at freeze time from timings only**, and run every mandatory cell for all 10; do not add seeds only to promising cells.
- Same ordered input pair cannot cross split boundaries. Reverse pairs `(a,b)` and `(b,a)` may: this exploits an algebraic relation, not unseen-modulus generalization. Report test metrics separately for reverse-seen and reverse-unseen examples. If their gap dominates the result, qualify the claim; an orbit-held-out split is an optional stress test, not a replacement selected after seeing test results.
- During frozen runs, the controller may see training metrics and resource metadata. Validation is not used to select widths, stop runs, extend successful seeds, or revise hypotheses. Test trajectories can be evaluated at scheduled times into a sealed output stream, but cannot be read by the experiment controller until the mandatory batch is finished or its predeclared deadline occurs. No need to retain hundreds of weight checkpoints for this purpose.

### Events and continuous outcomes

Freeze evaluation spacing **Delta=100 updates**, including step 0 and T. An event requires >=99% accuracy for three consecutive evaluations; event time is the **third**, confirmation evaluation, with first crossing also recorded. Use the same rule for train memorization `tau_M` and held-out generalization `tau_G`. Report event-resolution uncertainty (at least one evaluation interval).

Operational delayed generalization additionally requires held-out accuracy <=80% at `tau_M` and `tau_G-tau_M >= max(1000,10*Delta)`. This is a declared descriptive definition, not a natural law. Runs can generalize without meeting it.

Retain raw, uncalibrated CE, accuracy, correct-minus-best-wrong margins, centered-logit RMS, parameter norms, feature movement, update count, examples processed, process CPU time and wall time. Accuracy alone cannot establish an abrupt mechanism. Never stop because training loss is small.

### Primary estimand

Predeclare **L=16, H=128**, without choosing them from the sweep. For each block and condition, set `U=min(tau_G,T)`, marking runs without a confirmed event as censored at T. With a common complete horizon and no other censoring, mean U estimates restricted mean time-to-generalization through T, not the mean eventual grokking time.

The primary contrast is the paired width-by-decay interaction:

`I = (U[H,lambda_star]-U[L,lambda_star]) - (U[H,0]-U[L,0])`.

H predicts I<0. Report `I/T`; **-0.10** is a predeclared practical-effect reference, not a guaranteed power target. Also report both constituent width effects and both constituent decay effects: an interaction alone can be driven by pathological deterioration in one cell.

Key robustness outcomes: the analogous interaction in **final test CE**, final accuracy and generalization event rates. Show all six widths, including the fixed secondary contrast 128 versus 256. Do not claim the low-to-high contrast isolates pure capacity. Report observed delays only for runs with both events, explicitly noting the resulting selection; never summarize only successful seeds as the whole population.

### Uncertainty and censoring

- Plot all block trajectories and paired effects. Bootstrap whole matched blocks (e.g. 10,000 draws) for approximate 95% intervals of the interaction and CE contrasts, preserving all cells within a block. State that intervals with n=5 are unstable; include leave-one-block-out estimates and the raw paired table.
- Report event counts `k/n` and Wilson intervals for each cell, but do not treat widths as independent when contrasting them. A two-sided sign test with five unanimous paired signs cannot attain p<0.05; avoid significance theater.
- Do not bootstrap examples or checkpoints as independent experimental replications. Do not turn all censored observations into infinite times, omit them, or infer a sharp critical width.
- If all runs are censored, U differences may be zero while eventual behavior remains unknown. Emphasize event-rate bounds, continuous loss, and the finite horizon. Infrastructure failures are missing runs, **not** non-grokking observations; rerun identical configurations or report the incomplete paired analysis separately.
- Compare widths at both common updates and common CPU budget. For the latter, predeclare B as the minimum realized cumulative CPU time to T across the complete primary-cell runs, selected using timings only. Use the last logged observation at or before B, report discretization, and never extrapolate. Compute-matched comparisons have different decay exposure and are explicitly secondary.

### Data and numerical checks

Check all p^2 unique pairs, integer ranges, exact label formula, split disjointness/exhaustion, class and operand counts per split, and reverse-pair exposure. Validate chance and majority-class baselines. Check finite losses/gradients, deterministic reruns on a tiny run, checkpoint/resume equivalence including optimizer moments, decay-only behavior, and agreement of an optimized lookup implementation with an explicit one-hot reference. Zero-decay random-label training should fit at a wide width before its lack of test generalization is mechanistically interpreted.

## 4. Minimally sufficient mechanistic controls

Use the primary extreme pair 16/128, both decay settings, and the same five blocks unless stated otherwise. Cheap controls take precedence over transfer datasets.

### A. Fixed structural diagnostics: no frequency fishing

On scheduled snapshots, obtain the full table of class-centered logits F. Remove input-row and input-column means (add the global mean back) to get its pair-interaction component `F_cross`. Define a fixed projection onto cyclic relative-error logits:

`q[r] = mean_(a,b) F_cross[a,b,(a+b+r) mod p]`

`P_task F_cross[a,b,c] = q[(c-a-b) mod p]`.

This groups entries by the known relative error, not frequencies selected from a final successful network. Report its squared-energy fraction, its margins/CE, and residual-logit CE, along with row/column components. Protect the zero-denominator case. CE is nonlinear: these are diagnostic ablations, **not an additive loss decomposition**.

Evaluate removal of this component on held-out logits, with and without restoring the original centered-logit RMS. Compare to eight frozen random, rank-matched projectors made by independent input/output index permutations conjugating the same projector. This controls generic rank and confidence loss. Because the projection is task-informed, a large damage effect is not by itself proof of a particular learned circuit. Full-table diagnostics use known algebraic structure and are strictly nonadaptive; never use them to choose models or checkpoints.

Supporting temporal signal: a >=0.10 increase in projected energy fraction after train memorization and before confirmed generalization in at least 4/5 relevant blocks. This threshold is descriptive and can fail; dependence on projection normalization must be shown. Use fixed snapshot times and training events, not retrospectively selected frequencies. Layer-relative movement and centered-feature Gram similarity on a fixed training-only subset of <=64 inputs are enough; a dense multiclass NTK is unnecessary.

### B. Frozen-initial-feature readout baseline — 20 runs

Freeze A,B at initialization and train only V on the identical data, LR, decay setting, and update horizon. Apply no hidden decay to genuinely frozen features. This tests whether more initial random features suffice; it is not a perfectly optimizer-matched linearization. Report train fit as well as generalization. If it matches nonlinear generalization, reject necessity of feature learning. If it cannot fit train, its failure alone is inconclusive.

### C. Balanced random-label memorization control — 20 runs

Permute the vector of all table labels across input pairs, preserving global label counts, independently per block; use the same shuffled table across widths and decay cells. **Do not merely permute class names**, which preserves the addition task. Keep inputs, splits, and initialization matched. Report chance/majority references and train fit. Near-chance held-out accuracy without train fit is not evidence that a memorization circuit was learned. Repeat structural diagnostics using the original additive coordinates to check for spurious task alignment.

### D. AdamW update-scale plus decay-exposure control — 20 runs

In the pilot only, determine a frozen per-width LR multiplier for widths 16 and 128 from training-only first-10-step centered-logit movement. Use bounded scalar calibration with a reset optimizer, aiming for movement within 20% across widths. Then run both decay settings on fresh frozen blocks.

When LR changes from eta_ref to eta_w, set positive decay `lambda_w = eta_ref*lambda_star/eta_w`, so per-step shrinkage and its cumulative product remain equal at equal updates. Keep the zero-decay arm zero. Report realized function movement, parameter steps and cumulative decay. If calibration fails within the bounded search or matching drifts immediately, label the control unsuccessful rather than claiming scaling was eliminated. This only matches early dynamics; it is not full kernel/optimizer equivalence.

Do not import a GD `eta proportional to alpha^-2` rule into AdamW. A separately centered-output GD study would require its own design and is not necessary here. Avoid adding an unmatched output-scale intervention as if it isolated laziness.

### E. Training-triggered decay-off branches — 10 branches

For each decay-on nonlinear run at widths 16 and 128, branch at the confirmed **training-only** memorization event. Clone weights and complete optimizer state; compare the original decay-on continuation against a zero-decay continuation with identical LR and remaining horizon through T. No held-out event chooses the branch. If no train event occurs, mark the branch inapplicable, not failed generalization. Summarize paired changes in U and CE. A >=0.10T increase in restricted time, with concordant CE deterioration, is a practical supporting effect.

This intervention tests the role of **continued** decay after memorization, not whether decay was necessary earlier. Its null result does not prove an optimization bug or disprove all regularization effects.

### F. Cheap capacity witness

Before interpreting absence as inability, implement a hand-constructed quadratic addition scorer using sine/cosine products and polarization `uv=((u+v)^2-(u-v)^2)/4`. Four products for each positive Fourier frequency and two squares per product give a candidate construction using `4*(p-1)` hidden units: 120 at p=31. Verify all-table exact classification numerically, allowing a positive readout scale for low CE, before making a capacity claim. Fixed feature-centering constants cancel in paired squares. This is a proposed independently checkable construction, not an experimentally established result in this plan.

A successful construction at widths 128/256 rules out absolute inability there, not lack of trainability or a norm/regularization constraint. It proves nothing about widths 8–64. Report its norms alongside trained models; an enormous-norm witness does not establish equal efficiency.

## 5. Stages, commands, artifacts, and gates

All command names below are **conceptual interfaces for scripts the main agent will create**, not existing executables or instructions to fetch code. Each stage writes a machine-readable status including failed/abandoned work.

### Stage 0 — Preflight and reliable tiny runner (hours 0–8)

**Goal:** establish an honest CPU throughput/resource envelope and prevent implementation artifacts.

**What to run:** environment inventory; dependency import checks; model/data/optimizer unit tests; short deterministic training and resume tests; benchmark widths 8,128,256 for 1,000–2,000 updates after warmup. Conceptual commands: `preflight --cpu`, `test-data-model-optimizer`, `benchmark --p 31 --widths 8 128 256 --threads 1 2 4`.

**Success signals:** data/gradient/decay/reference tests pass; no nonfinite values; measured seconds/update and evaluation overhead; deterministic seed replay; projected storage <0.8 GB. Fix correctness before scientific runs.

**Artifacts:** environment/package lock, hardware inventory, test report, benchmark CSV, CPU-thread decision, projected run ledger. Choose one stable thread/concurrency layout; avoid oversubscribing BLAS workers.

### Stage 1 — Bounded exploratory pilots (hours 8–20)

**Goal:** find one common stable recipe and determine whether delayed generalization is observable, without turning pilot selection into confirmation.

**What to run:** start p31, width64, eta=3e-3, lambda=1, train fraction .30; use three dedicated pilot blocks for the eventual candidate. If numerically unstable or train fitting fails, test eta=1e-3, then 1e-2, within the time cap. If stable training never reaches held-out generalization, allow lambda=.1 and, at most, train fraction .50, in that order. These are bounded alternatives, not a full grid. Inspect widths16/128, zero decay, initial update scales, and one random-label wide run. Calibrate the scaling-control LR multipliers. Conceptual command: `pilot --manifest exploratory.yaml --max-wall-hours 12`.

**Success signals:** preferably >=2/3 pilot blocks show train memorization before generalization with the declared delay; stable CE reduction and no numerical pathology are required regardless. Pilot success is a feasibility gate, not a research result.

**Artifacts:** complete pilot table including failures, training/validation curves, chosen-recipe rationale, initialization/scale audit, all pilot compute. Never promote pilot held-out results to final-test evidence.

**If the gate fails:** freeze the best stable recipe by mean pilot validation CE at the common pilot horizon, breaking near ties in favor of the default. Proceed with a finite-horizon null study; do not spend the week finding an attractive transition. If no stable implementation exists, halt scientific claims and produce a diagnostic report.

### Stage 2 — Freeze protocol and resource schedule (hours 20–24)

**Goal:** commit all adaptive choices before final evidence exists.

**What to run:** generate protocol/seed/split manifests and hashes; validate the complete dependency/run graph; estimate cost for every mandatory run, including controls. Conceptual commands: `freeze-protocol --seeds 5 --horizon-grid 10000 25000 50000 100000`, `audit-run-ledger`.

**Success signals:** 5 complete matched blocks can be run for all mandatory cells within hours24–132, with >=25% timing overhead allowance; horizon and seed count are identical across primary cells. Prefer T>=25,000 if feasible. Choose the largest feasible candidate T from the grid using measured throughput and pilot feasibility, and record the decision. If 10 blocks fit with the same horizon and controls, freeze 10 now; otherwise retain five. If even T=10,000 cannot fit, reduce optional work first; do not silently deliver fewer than five primary blocks as the requested uncertainty study.

**Artifacts:** frozen protocol, seed/split files, expected cost per cell, exact LR/decay groups, diagnostic/random-projector seeds, censoring rules, immutable analysis specification and full execution order.

### Stage 3 — Frozen primary width-by-decay sweep (target hours 24–96)

**Goal:** estimate the prespecified interaction and whole width response.

**What to run:** **6 widths × 2 decay levels × 5 blocks = 60 runs**, all to T. With 10 blocks this doubles. Block-interleave and deterministically randomize width/decay run order to avoid machine-drift/order confounding. Conceptual command: `run-manifest --frozen core.yaml --resume --deadline-hour 96`.

**Success signals:** all planned cells complete or have explicit infrastructure status; paired raw table available; no final-test-dependent scheduling; test streams remain sealed. Scientifically, an I/T<=-0.10 with interval excluding zero is strong support for the directional interaction, but a null or reverse effect is an equally valid completed experiment.

**Artifacts:** per-run metrics and runtime logs, event/censoring table, small checkpoint set, provisional training-only integrity report. Final figures wait for the frozen batch to close.

### Stage 4 — Mandatory mechanism tests and finite-time stress (target hours 96–132)

**Goal:** discriminate competing explanations instead of decorating a sweep.

**What to run:** controls A–F above. B/C/D each cost 20 runs at five blocks; E costs at most 10 additional continuation horizons. Budget for a conservative total of **130 T-equivalent runs** including the 60 primary runs, before any extension. Execute controls earlier/interleaved if that improves utilization, but do not read final-test results to prioritize them. Conceptual commands: `run-manifest controls.yaml`, `branch --trigger train-confirmed --decay 0`, `diagnose-structure --fixed-projectors`, `verify-capacity-witness`.

Predeclare an optional doubled-horizon stress set: widths16/128, both decays, **the first two frozen blocks**, all extended from T to 2T regardless of success. This costs 8 extra T-equivalents and tests censoring without selecting apparent boundary runs. It does not replace the primary T analysis. Run only if the budget ledger permits the whole subset before hour132.

**Success signals:** control comparisons are interpretable (train fit shown, scale matching measured, branch applicability reported); direction and uncertainty reported whether supportive or not. If controls are incomplete, downgrade the mechanism to a hypothesis and state which alternatives remain unresolved.

**Artifacts:** paired control table; projected/residual-logit plots with confidence controls; feature-motion summaries; branch comparisons; capacity-witness test and norms; T/2T censoring sensitivity.

### Stage 5 — Optional narrow transfer (hours 132–140 only)

**Goal:** test scope, not rescue a failed primary result.

**What to run:** only if mandatory cells and analyses fit budget. First p47 with the same quadratic model, widths16/128, both decays, five fresh matched blocks; then p31 ReLU under the same restricted factorial, only if separately affordable. Match initial logit RMS and document activation/update-scale differences. No transfer-specific hyperparameter search. Conceptual commands: `run-manifest transfer-p47.yaml`, then `run-manifest transfer-relu.yaml`.

**Success signals:** a full five-block transfer comparison completes within the cap; otherwise skip before launch. A shorter frozen horizon is allowed if clearly labeled, but compare transfer cells at their common horizon. Transfer failure is a scope limit, not permission to retune until positive.

**Artifacts:** separate transfer table/plot with uncertainty, initialization audit, skipped-work reasons. Never pool these runs into the p31 primary estimand. If only one transfer fits, prefer p47 to avoid simultaneously changing the task size and nonlinearity.

### Stage 6 — Unseal, analyze, reproduce, and write (hours 140–168)

**Goal:** deliver a complete honest research package by the deadline.

**What to run:** unseal test streams only after the execution manifest closes; frozen block-paired analysis; recreate every numerical table/plot from logs; independent rerun of a short selected integrity case; manuscript compile and artifact audit. Conceptual commands: `analyze --protocol frozen.json`, `make-figures --from-raw`, `reproduce-smoke-test`, `build-paper --neurips-2026`, `audit-deliverables`.

**Success signals:** every number has a source run; complete/incomplete/censored counts reconcile; all preliminary and failed compute counted; no unsupported mechanistic claim; PDF compiles. Use the already acquired official NeurIPS2026 style, <=9 content pages, single PDF, references/appendix/checklist outside the main limit, all 16 checklist items answered with justifications, substantive autonomous LLM use disclosed. No new web/template search is needed.

**Artifacts:** paper PDF/LaTeX, raw compact logs, code and package versions, split/seed manifests, run/plot/table commands, compute/independence/failure audits, machine-readable results and a README.

## 6. Compute, environment, and storage preflight

The planner has **not measured the current hardware or installed software**. The main agent must check, without requiring network research:
- OS, Python, CPU model/core count, RAM, available disk, process/thread limits and BLAS backend; record process CPU versus elapsed time and any concurrent jobs.
- GPU availability with `nvidia-smi` when available and torch CUDA checks; record GPU/CUDA/driver/VRAM if present, or explicitly `CPU-only / CUDA not used`. Do not install CUDA or depend on a GPU merely to run these tiny models. If using a GPU, use it consistently for compared cells or report the device split.
- Minimum practical environment: `torch` CPU build, `numpy`, `scipy`, `pandas`, `matplotlib`, `pyyaml`, `pytest`; optionally `psutil` and a PDF-inspection package. Freeze installed versions. Bootstrap CIs need no heavyweight survival library. Use offline/local dependency installation if possible; no external model repositories.
- Manuscript dependencies: a LaTeX engine, `latexmk`/BibTeX as appropriate, acquired official style/checklist. Planner does not inspect those files here.
- Estimate total cost as the sum of **measured per-cell seconds/update × T × repetitions**, plus test evaluations, branches, initialization calibration, diagnostics and >=25% overhead. Core alone is 60T updates; mandatory controls increase the conservative ceiling to 130T; extensions to138T. At T=50,000 this is about 6.5 million training updates before extensions, **not a runtime prediction**. Freeze a smaller horizon if this does not fit; do not pretend p31 makes the week automatically sufficient.
- Keep only initialization/selected training-event/end checkpoints plus resumable current state. Evaluate test curves into compact sealed summaries instead of archiving every evaluation checkpoint. Full p31 logit tables are ~0.12 MB float32, but store only a few snapshots. Target <0.8 GB total, well below the original 1 GB scale. Avoid full NTKs/Jacobians, per-step tensors, and unconstrained optimizer-state histories.
- Automatic watchdog: checkpoint on interruption; retry the identical configuration once after infrastructure failure; stop new optional jobs when the ledger threatens the hour140 analysis reserve. Never reinterpret a crashed run as a censored scientific outcome. Report any incomplete mandatory matrix rather than silently substituting selected seeds.

## 7. Iteration rules and fallback narratives

1. **Before freeze:** change LR/decay/train fraction only through Stage1's bounded ladder; no new dataset or model search. Use throughput to select T and N. All such choices remain exploratory.
2. **After freeze:** fixes to scientific logic/data/model require a new protocol version and rerunning affected cells; retain invalidated logs. Harmless logging fixes need a documented equivalence check. Do not change the objective or split because outcomes disappoint.
3. **Scale control changes the interaction:** narrative becomes "apparent width dependence was substantially an AdamW function-step/decay-exposure confound." Do not call this proof of a specific lazy regime.
4. **Frozen features match nonlinear results:** narrative becomes "initial random features suffice within this finite setting"; learned-feature necessity is rejected. If frozen features cannot train-fit, leave that alternative unresolved.
5. **No delayed generalization or heavy censoring:** report width-dependent trainability and held-out loss at the measured horizons, with the prespecified extension if affordable. No critical-width/impossibility conclusion.
6. **No decay interaction:** report the null/reverse interaction with uncertainty; do not change to a norm-shrinkage universal story. Structured logits may still emerge with zero decay.
7. **Transfers fail or are skipped:** restrict the claim to p31 quadratic networks. One supportive transfer is not universality. If mandatory controls are incomplete, deliver a descriptive controlled benchmark plus unresolved-mechanism list.

Main narrative if supported: "Under a specified variance-normalized AdamW parameterization, width modulates a decay-dependent learned-structure pathway, within the tested horizon." Main fallback: "A paired finite-budget audit separates what width predicts from what capacity, optimizer scaling, and censoring can actually explain." Either can be a complete honest report; neither is automatically a top-conference contribution.

## 8. Figures and claim-to-evidence map

1. **Primary figure:** all-seed width × update trajectories, event/censoring summaries and paired interaction with interval. Show CE as well as accuracy; do not average away abrupt seed-specific events.
2. **Mechanism figure:** fixed structural fraction and margins over time, ablation with random/rank/RMS controls, and frozen-feature/decay-off comparisons. This supports a bounded mechanism only jointly with the scale control.
3. **Confound figure:** initial logit/update RMS by width, matched-scale interaction, update-matched versus CPU-matched results, and optional T/2T comparison.
4. **Main table:** per-cell N, events, final CE/accuracy, restricted time, parameter count and CPU time. Appendix: every seed, shuffled labels, capacity witness, transfers, failures and all pilot expenditure.
5. **Protocol schematic:** exploratory pilots -> freeze -> paired factorial -> mechanistic interventions -> sealed-test analysis. The contribution is the falsifiable discrimination, not a novel MLP diagram.

## 9. Top five likely rejection risks — and planned responses

| Likely rejection | Why serious | Required response / residual limit |
|---|---|---|
| **1. "Only another width sweep; narrow toy result."** | Size-dependent grokking already exists according to the supplied support. | Center the interaction, controls and explicit falsifiers; never claim width-sweep novelty. Bound conclusions to this model/task; acknowledge publication value remains uncertain. |
| **2. "Width changes initialization and AdamW dynamics, not capacity."** | Constant parameter variance, output variance, raw norm or seed alone does not isolate learning speed. | Explicit 1/sqrt(width) output normalization, initialization/function-step audit, matched-LR plus matched-decay-product control, frozen features, and verified high-width capacity witness. Residual optimizer-path differences remain. |
| **3. "Your critical width is just finite-time censoring."** | Non-generalization within T does not establish impossibility; survivor-only delays are biased. | Common horizons, sustained events, right-censoring, CE/margins, restricted-time estimand, fixed-seed doubled-horizon subset and CPU-matched view. No asymptotic threshold claim. |
| **4. "Seed/split fishing and hidden test leakage."** | Pilot complements, frequency selection, reversed inputs, or outcome-dependent extensions can manufacture a story. | Disjoint pilot/frozen seeds, hashed splits, sealed final-test stream, fixed task projection, train-only branch trigger, paired whole-block uncertainty, reverse-exposure strata and full failure ledger. Five blocks still have weak power. |
| **5. "Mechanistic plots are correlational or tautological."** | A task-informed projection will naturally correlate with success; shuffling alone proves little. | Pair structural diagnostics with initial-feature freezing, post-memorization decay-off branches, matched random/rank/RMS ablations, shuffled-label train-fit checks and the update-scale control. State what each intervention does not isolate; downgrade to descriptive evidence if alternatives survive. |
