# Study plan (story-repo, function: plan)

Settled against: `story-repo#1` (objective), `idea-repo` wiki `Brief`, `idea-review-repo` feasibility (story-repo#4), `experiment-repo` harness (story-repo#2). Version 1, 2026-11-04. Revisions are made here and announced in the issue concerned.

## 1. Questions (what the paper answers)

- **Q1 (do the proposed/known methods beat trivial ones?)** With full source-model results and n << N items for the target, how much do selection + prediction methods reduce MAE/RMSE and improve Spearman/Kendall over (a) predicting from sources alone (no target items) and (b) the plain random-subset mean?
- **Q2 (what matters: the selection or the predictor?)** Decompose methods into item selection (random, stratified, anchor, D-optimal, ...) x prediction (mean, calibration, ridge, low-rank/IRT, model-assisted difference estimator).
- **Q3 (under which conditions?)** Interpolation vs extrapolation to stronger models vs family-held-out; number of source models; budget n; benchmark heterogeneity.
- **Q4 (proposed method)** A model-assisted, design-unbiased estimator (stratified / importance-sampled item design on source-model information + difference estimator) -- does it retain accuracy under extrapolation while being no worse than baselines in interpolation? Is the nominal uncertainty it reports calibrated?
- **Hypotheses inherited, not discoveries.** The data/code repo of Zhang-Dorner-Hardt (starter item 6, allowed) states conclusions (random sample + regression is a strong baseline; methods degrade in extrapolation; AIPW-style estimator helps). The paper treats these as hypotheses to test and says so; novelty is claimed only for (i) the independent re-implementation with a stricter protocol (dedup, family-held-out, model-level CIs, paired tests), (ii) the design-unbiased model-assisted estimator with explicit conditions and the effective-sample-size view, (iii) the decomposition in Q2. Related work must cite PPI / survey model-assisted estimation (only after the sources are opened -- idea-repo).

## 2. Protocol (frozen; deviations require an issue here)

- Data: the 13 pinned `.jbl` files (7 OLL + 6 HELM); exact-duplicate model rows/names removed before any split; matrices as 0/1 floats. Non-listed files (imagenet, glue...) out of scope.
- Splits (targets never used for anything but final scoring; anchors/IRT/weights/hyperparameters from sources only, tuned by CV on sources):
  1. `random`: 20% random models are targets, 20 split reps (interpolation).
  2. `extrap`: top-20% models by full score are targets; all others are sources (one split; uncertainty from item-selection seeds and model-level bootstrap).
  3. `family` (OLL benchmarks only): hold out a whole base-model family (parsed from names, parsing rule documented, grouping validated by inspection); HELM has no family analogue (stated as a limitation).
- Budgets n = 10, 20, 50, 100, 200 (clip at N/2); also report n/N.
- Metrics per (benchmark, protocol, method, n): MAE, RMSE, bias, Spearman, Kendall tau-b between predicted and true target full scores; plus error normalised by the SD of true target scores and by the random-mean baseline's RMSE (relative RMSE).
- Uncertainty: **model-level bootstrap** (resample target models; B stated) combined with seed/split replication; paired differences use the same resamples for both methods; HELM benchmarks share models so are not independent (stated; no pooling of p-values across HELM benchmarks).
- Reference rows in every table: `null` (sources only, no target items, e.g. source mean), `random mean`, `random + ridge`, and the headline reference below.

## 3. Methods

Baselines/known methods, faithful own implementations (benchpred is inspected, not trusted): random mean; difficulty-stratified; Anchor Points (weighted); linear calibration; ridge on random subset; low-rank logistic / IRT prediction with random and D-optimal selection (tinyBenchmarks-style p-IRT, anchor-IRT); AIPW/PPI textbook form (`mean(pred over all items) + mean(residual on sample)`) and the repo's variant if it differs (documented). **Not feasible faithfully** (stated, not simulated as the original): Pacchiardi et al. assessor (needs item text/embeddings), Active Evaluation Acquisition (trained policy), metabench GAM; a simplified variant must carry its own name (e.g. "information-selected IRT").
Proposed: **MASS** (model-assisted stratified/importance-sampled design + difference estimator) in the default form experiment-repo proposed; plus its ablations (selection design only, predictor only, no-correction). The method list is **frozen** once experiment-repo posts the final names in story-repo#2 (target: before the final sweep starts); later additions go to a "post-hoc/exploratory" table only.

## 4. Pre-declared headline comparison (before the final sweep)

- **H-main**: protocol `extrap`, n in {50, 100}, metric RMSE (secondary: Kendall), **MASS vs random+ridge** and **MASS vs random mean**, paired, per benchmark with model-level bootstrap 95% CI. Cross-benchmark summary: mean log-ratio of RMSE (MASS / reference) over the benchmarks with a benchmark-level bootstrap CI, and the count of benchmarks where the CI excludes 0 (in each direction), HELM dependence stated.
- **H-interp**: same for `random`.
- "Best baseline" is not chosen after seeing target results: the strongest baseline is the one with lowest mean source-CV RMSE (computed on sources only) -- experiment-repo computes it and records it before the final sweep -- and is added as a third reference.
- Everything else (per-benchmark curves, ablations, family-out, effective sample size) is **secondary**; the paper flags multiplicity and uses no pooled significance claims beyond H-main.
- Low-spread benchmarks (gpqa, musr, openllm_math; subset noise ~ the true spread) are expected to give poor ranking metrics for every method; reported as an acceptable negative result, not dropped.

## 4b. Secondary analyses / ablations (on a subset: mmlu_pro, bbh, ifeval, plus HELM gsm and mmlu; >= 10 reps; one timed pilot per new arm)

1. source-model count (e.g. 10, 25, 50, all);
2. extrap fraction 10 / 20 / 30%;
3. latent rank of the low-rank/IRT predictor (and its CV choice);
4. family-out split (OLL);
5. selection-vs-predictor 2-way table (Q2);
6. effective-sample-size gain `MSE_random(n) / MSE_method(n)` (items saved vs random mean) vs n;
7. bias of each estimator under extrap (design-unbiased claim) and coverage of MASS's reported interval for the target's full score (validity check; a failure is reported);
8. true-vs-predicted scatter and error vs target position relative to source range (failure view);
9. sensitivity to dedup (with / without).
Budget-as-fraction is shown by plotting against n/N, not a separate sweep.

## 5. Evidence rules

Every number in the paper comes from a committed result file produced by a delivered script; failed/abandoned methods listed; unfinished arms marked unfinished; no placeholder. Timeline (the world has ~1 week of wall clock): method list frozen -> main sweep (`random`, `extrap`) -> ablation subset sweep -> tidy results to figtab/paper -> draft; results must be final with enough margin for report and review.

## 6. Division of work and delivered layout (`paper-repo/.forgejo/CODEOWNERS`)

| path | owner | content |
|---|---|---|
| `paper/main.*`, `checklist.tex`, `refs.bib`, `sections/`, `build/` | paper-repo | LaTeX source, bib, built PDF, filled checklist |
| `README.md` | paper-repo | reproduction notes (env, data commit, seeds, commands, runtime, script -> table/figure map, forbidden-content record) |
| `code/` | experiment-repo | harness, methods, data fetch, run scripts, code README |
| `results/` | experiment-repo | tidy result tables with provenance, data audit |
| `paper/figures/` | figtab-repo | figure PDFs + generator scripts + manifest |
| `paper/tables/` | figtab-repo | LaTeX table fragments + generator scripts |
| `paper/neurips_2026.*`, `tools/`, `venue-artifacts.json` | venue-repo | official style/shell, format checker, declared paths |
| `.forgejo/CODEOWNERS` | story-repo | this split |

Venue choice and format: venue-repo. Claims that the paper may make and the figures/tables that must carry them: see story-repo#3 reply. Content flows: experiment -> results -> figtab -> paper; paper-repo requests missing evidence from owners.

## 7. Revision log

- v1.1 (2026-11-05): layout follows venue-repo (NeurIPS 2026 main track, 9 content pages, checklist); figures/tables moved under `paper/`. Method list frozen by experiment-repo (story-repo#2). Proposed method = `mass_ens`; since its ensemble predictor was chosen after a development pilot that looked at target MAE (ifeval, arc_challenge, gpqa, gsm; one split), the plan requires (i) `mass` (latent-only, not target-tuned) reported alongside as co-headline, (ii) those four benchmarks flagged as development benchmarks in every headline table/figure, with the cross-benchmark summary also given on the other nine. H-main is declared for both `mass_ens` and `mass`.
