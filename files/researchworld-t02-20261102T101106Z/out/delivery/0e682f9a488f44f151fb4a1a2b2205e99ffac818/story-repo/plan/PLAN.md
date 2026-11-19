# Study plan: model width and delayed generalization (grokking) on modular arithmetic

Owner: `story-repo`. Settles the questions, the falsifiable account, the comparisons and who delivers what.
Anything below marked *(adjustable)* may change when `idea-review-repo`, `idea-repo` or `experiment-repo` show it is infeasible or wrong; the objective (`Research objective`, story-repo#1) wins over this file.

## Question
In modular arithmetic tasks, how does the occurrence and timing of delayed generalization depend on model scale? Scale axis = **width** (d_model / hidden width) at fixed depth; secondary axis = training-set fraction.

## Proposed account (time-scale / memorization-speed account)
Grokking time splits as t_gen = t_fit + D. Width changes t_fit and the weight norm at the time of fit; D is the time weight decay needs to move the network from the memorizing solution (large norm) to the generalizing one (small norm). We propose:

* **A1 (direction).** At fixed (p, f, lr, wd, optimizer, steps), median t_gen is non-increasing in width above a minimal width w_min; below w_min nothing groks within budget.
* **A2 (mechanism).** D ~ (lr·wd)^-1 · log(‖θ_fit‖/‖θ*‖). Width acts on D *only through* ‖θ_fit‖ (norm at t_fit) and t_fit; no residual width effect once those are controlled.
* **A3 (scope).** The data fraction needed for generalization at fixed budget decreases with width (wider nets groke at smaller f); at large f the delay vanishes; at wd = 0 nothing groks inside the budget.

Competing accounts the data can favour instead: (C1) width has an independent effect on D through more capacity for the generalizing circuit (circuit efficiency, Varma et al.); (C2) width is a pure lazy->rich/init-scale effect (Kumar et al., Omnigrok), i.e. the effect is explained by init scale alone; (C3) no systematic width dependence beyond seed noise.

## Falsification criteria (fixed before looking at results)
* A1 refuted if the trend test on right-censored t_gen over width (cells above w_min) fails to reject at 0.05 or the trend is increasing, or per-cell KM medians are non-monotone beyond bootstrap CIs.
* A2 refuted if (i) the log-log slope of D vs wd (wd sweep, at fixed lr) has a 95% CI excluding -1 (tolerance: report the CI, interpretation by experiment/report), or (ii) in the regression log t_gen ~ log t_fit + log‖θ_fit‖ + log width (censoring-aware) the width coefficient CI excludes 0, or (iii) the init-scale intervention at fixed width does not move D in the direction of the norm at fit.
* A3 refuted if the grok fraction vs f curves for different widths do not shift in the predicted direction (Wilson CIs) or grokking occurs at wd = 0 in budget.
* Negative/contradicting outcomes are reported as such; the paper states which of A1–A3, C1–C3 survive.

## Comparisons and analyses (what experiment-repo's runs must provide)
Priority order (cut from the bottom if budget runs out; unfinished cells reported as unfinished):
1. **Main sweep**: width {8,16,32,64,128,256} x >=5 seeds, p=53 (or experiment's pilot value), f=0.4, AdamW lr 1e-3, wd 1, full batch, 1-layer transformer. Endpoints: t_fit, t_gen (val acc >=0.99), D, right-censoring at the step budget; KM medians, bootstrap CIs, trend test (tests A1).
2. **Mechanism sweeps (A2)**: (a) wd {0.3,1,3} at two widths; (b) init-scale multiplier alpha {0.5,1,2} (interventional control) at >=2 widths; log weight norm and t_fit for the mediation regression. Includes a check of parametrisation confound (fixed vs width-scaled init/lr), at least at one width pair.
3. **Scope (A3)**: f {0.3,0.4,0.5} (and 0.2 if budget allows) x widths {16,64,256}; wd=0 control at one width.
4. **Robustness**: second architecture (MLP on embeddings) over width; second operation (modular multiplication, or subtraction) at 2–3 widths; second prime if cheap.
Each sweep: >=5 seeds per cell where run, fixed seed list recorded; censored runs kept. Metrics logged every N steps: train/val acc and loss, weight norm. Provenance (script, seeds, commit) beside every results file. Primary reporting is on t_gen (not D alone), because D can mix a shrinking t_fit.
Pilot (experiment-repo, 1 seed): width 128 groks at 11k steps, width 32 not by 12k — consistent with A1 but is only a regime check, not evidence.

## Division of work
| Position | Delivers (paths in `paper-repo`) |
|---|---|
| story-repo | this plan (`plan/`), `.forgejo/CODEOWNERS`, the claim structure the paper tests |
| experiment-repo | `experiments/` (trainer, sweeps, analysis, reproduction notes with env, seeds, commands, runtime), `results/` (CSV/JSON + provenance) |
| figtab-repo | `figures/` (figures/tables, plus scripts that produce them; which script makes which figure) |
| venue-repo | `venue/` (chosen venue among ICML/ICLR/NeurIPS, latest official template and checklist requirements, page limit) |
| paper-repo | `paper/` (LaTeX source, PDF, checklist), root `README.md` |
| idea-repo | context: related work, conventions (not a delivered path) |
| idea-review-repo / internal / external review | judgements; no delivered path |

Figure/table needs (for figtab-repo; claim -> content): F1 t_gen (KM median ± bootstrap CI, censored runs marked) vs width, per-seed points -> A1. F2 survival/val-acc curves per width -> shape of delay. F3 D and t_fit vs width and norm at fit -> A2 mediation. F4 D vs wd log-log with fit slope CI; init-scale effect -> A2. F5 grok fraction vs f per width (Wilson CIs) -> A3. T1 per-cell table: n, n censored, t_fit, t_gen medians+CIs. T2 robustness (MLP, second operation). T3 regression coefficients with CIs.

## Scope statement the paper must carry
Results apply to modular addition (and the robustness ops) at small p, 1-layer transformer/MLP, AdamW full-batch, tested width range; any claim beyond is untested. Failure cases of A1–A3 reported as findings.

## Additions after idea-repo's Brief (wiki page "Brief")
* **Operationalization (pre-registered).** Scale = d_model (width) with n_heads and MLP width (4·d_model) tied to it, depth fixed at 1; parameter count reported per width. t_fit = first step with train acc >= 0.99, t_gen = first step with val acc >= 0.99, D = t_gen - t_fit, plus ratio t_gen/t_fit as secondary. Runs without t_gen in the step budget are right-censored (KM, censored fraction reported), never dropped or set to 0. Thresholds (0.99 vs 1.0) as a sensitivity check.
* **Fixed vs. retuned hyperparameters** are reported separately: primary = all hyperparameters fixed across width; secondary = lr/init rescaled with width (the parametrisation check in sweep 2). Conclusions are stated per regime; a result that holds in only one regime is reported as conditional.
* **Seeds.** Initialization seed and data-split seed are recorded separately; main sweep varies both (a fresh split per seed), and a subset varies init with the split fixed to separate the two noise sources.
* **Mechanistic diagnostics (optional, if budget)**: weight norm curves (required, used by A2), Fourier-key-frequency sparsity / restricted-excluded loss at a few widths.
* **Literature rule.** Related-work searches must not use model-size/scale + grokking as core query terms (task independence rule); positioning uses the starter literature (Nanda config as reference; Omnigrok, circuit efficiency, lazy->rich, double descent as competing accounts C2/C1).
* Layout note: delivered code path is `experiments/` (matching experiment-repo's existing layout), not `code/`.

## Amendment 1 (after seeing partial main-sweep logs; disclosed as post-hoc)
* Partial `main` logs show that at the smallest width (8) most runs never reach train acc 0.99 but val acc rises to 0.56–0.97, i.e. "generalising without a memorisation phase". A1's "nothing groks below w_min" is therefore replaced by a **regime classification per run**, applied to all widths: (R1) fits then groks (t_fit < t_gen, delay measurable); (R2) generalises without a separate memorisation phase (val >= 0.99 reached with t_gen <= t_fit or fit never reached); (R3) fits, not generalised in budget (censored); (R4) neither. A1 is stated on t_gen over the R1/R2/R3 mix with censoring, and the regime fractions per width are reported. A2's D-based tests use R1 runs only (selection on regime is stated in the paper).
* Cut order accepted from experiment-repo: `splitfix`, `mul`, `lrscale`, then `mlp`. Kept as required for the claims: `main`, `wd`, `alpha`, `wd0`, `frac`. Unfinished cells are reported as unfinished.
* Estimates of run counts/time are experiment-repo's; idea-review-repo's feasibility remains pending and can further revise the grid.

## Amendment 2 (after feasibility review, idea-review-repo#2; supersedes the falsification criteria above where they differ)
Decision rule for every pre-stated estimand: **supported** (95% CI wholly on the predicted side, beyond a pre-stated negligible band), **refuted** (CI wholly on the opposite side or wholly inside the negligible band), **inconclusive** otherwise. A CI containing 0 is never read as support for a null; low power is never read as refutation. "Not run (budget)" is never reported as a null.

* **A1.** Estimand = censoring-aware slope (AFT / Cox with bootstrap CI over seeds) of log t_gen on log2 width. w_min is defined *before* the data: the smallest width at which >=80% of seeds reach train acc >=0.99 within T_max; the slope is estimated over widths >= w_min, widths below are reported as "did not fit" (consistent with the regime classification of Amendment 1). "KM medians non-monotone beyond CIs" is descriptive only. T_max is fixed after a 2-seed pilot at d in {16,32,64} to be >= ~2x the slowest t_gen to resolve, so "never groks" and "not yet" are not confounded; runs censored on t_gen are censored on D; runs censored on t_fit are reported separately. Conclusions are worded "under fixed lr/wd/init" (also in the abstract).
* **A2.** The regression is supporting only (width and norm at fit are nearly collinear; t_fit on both sides is mechanical). Regress log D (not log t_gen) on log t_fit and log norm at fit, state which norm (total L2 vs per-parameter RMS), and measure norm at t_gen too (it may depend on width, which is C1). The identifying test is **interventional**: init-scale alpha {0.5,1,2} at widths {32,128}, plus a **norm-matched comparison** (choose alpha at the wider net so norm at fit matches the narrower net, then compare D/t_gen). wd test: wd in {0.5,1,2} (not {0.3,1,3}, since 0.3 is the most censored cell), two widths, vary wd only (not lr), longer T_max (~2x) for wd=0.5; a slope CI containing both -1 and 0 is inconclusive.
* **A3.** Grok fraction with Wilson CIs, >=3 seeds for the wd=0 control (init scale stated); minimal separable pattern pre-stated (e.g. 5/5 vs <=1/5), or pool across f with a logistic model in (f, log width). One run never refutes.
* **Parametrisation confound**: one width pair, 3 seeds; it can only flag the confound, not settle it.

### Revised grid / cut order (target <= ~40 CPU-h, >=30% reserve; supersedes the earlier cut order where it differs)
1. main (d=8 with 3 seeds; others >=5 seeds); 2. alpha + norm-matched (widths 32,128); 3. wd {0.5,1,2} at two widths; 4. lrscale check (one pair, 3 seeds); 5. scope: widths {32,128} x f {0.25,0.4,0.5}, wd=0 control (one width, 3 seeds, full T_max); 6. robustness: MLP over width, then second operation (2 widths x 3 seeds); second prime dropped; optional 1–3 Nanda-config p=113 anchor runs only if budget remains. Cells already running that are not in this list (e.g. wd 0.3/3, frac 0.3, splitfix) may finish if cheap but are secondary; they are not to displace the list above. Early stop on sustained val>=0.99 and incremental per-run result files are required.
