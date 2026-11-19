# Reference Query Plan

**Status:** ready

## Central topic
Quantifying and correcting the winner's-curse bias of reporting the best searched LLM prompt/pipeline configuration's score on the same benchmark questions used to select it, via searcher-agnostic debiased interval reporting evaluated on synthetic worlds and replayed MMLU-Pro outcomes.

## Core methods
- empirical-Bayes hierarchical logistic item-response (latent difficulty) posterior-quantile interval
- parametric-bootstrap pivot calibration of the EB-IRT interval
- config-by-subject interaction random effects
- naive Wilson interval, Bonferroni and question-resampling reporting baselines

## Comparator literatures
- adaptive data analysis / holdout reuse
- Ladder leaderboard mechanism
- inference on winners and post-selection inference
- best-arm-identification / successive-halving prompt selection
- DSPy/MIPRO auto-tuners
- efficient multi-prompt evaluation and prompt-format sensitivity

## Benchmarks / data
- MMLU-Pro (replayed outcomes, 24 configs, subject codes)
- synthetic latent-difficulty worlds (varying N questions, K configs; equal-config null worlds)

## Representation shifts
- from per-config binomial/Wilson score to hierarchical latent-difficulty IRT posterior using all logged (question, config, outcome) triples
- from 1-D difficulty to config-by-subject interaction (did not beat the simpler variant)
- from analytic posterior to parametric-bootstrap pivot calibration (under-covered: 0.77)

## Result-driven themes
- naive reporting is upward biased (signed bias ~0.037) and under-covers; EB-IRT cuts bias to ~0.014 and interval score from -0.232 to -0.148 at ~0.915 coverage
- Bonferroni is valid but wide (-0.196); resampling worst (-0.273)
- bootstrap pivot calibration under-covers (0.77) and interaction model did not improve on the simple EB-IRT
- selection is ignorable for likelihood under searchers that use only observed outcomes

## Queries
1. `winner's curse selection bias reported score after selecting best configuration among many` (core_method) — Central problem: the best-of-K searched config scored on the same questions is upward biased (naive signed bias +0.037 in the run).
2. `adaptive data analysis statistical validity reuse of holdout` (baseline_comparator) — Adaptive reuse of one question set for selection and scoring; grounds the validity argument (Dwork et al. line).
3. `Ladder mechanism reliable leaderboard adaptive submissions` (baseline_comparator) — Reporting-mechanism comparator for repeated adaptive evaluation on a shared test set.
4. `inference on winners selected parameter confidence intervals` (baseline_comparator) — Econometric post-selection inference for selected best candidates; the run's Bonferroni/resample baselines belong to this neighborhood.
5. `valid post-selection inference confidence intervals` (baseline_comparator) — Classical post-selection inference literature; context for simultaneous/Bonferroni-style intervals compared against.
6. `empirical Bayes shrinkage for selected maximum item response theory LLM benchmark evaluation` (core_method) — Run's best method is an empirical-Bayes hierarchical logistic IRT posterior interval (a_config - b_question, Laplace draws, quantile intervals); needs IRT and shrinkage references.
7. `item response theory efficient LLM evaluation question difficulty` (architectural_shift) — Representation shift from per-config binomial/Wilson score to latent-difficulty IRT model of (question, config) outcomes; IRT for LLM benchmarks.
8. `prompt optimization best arm identification successive halving limited evaluation budget` (benchmark_context) — Searchers in the evaluation (exhaustive and successive halving, sparse outcome logs) are the prompt-selection setting; selection via observed outcomes is ignorable for the likelihood.
9. `automatic prompt and pipeline optimization DSPy MIPRO few-shot instruction search` (benchmark_context) — Auto-tuning tools whose reported best-config scores motivate the problem.
10. `multi-prompt evaluation performance distribution across prompt templates sensitivity` (result_driven_theme) — Config-to-config variability across prompts/formats determines tau and the size of selection bias; Polo/Sclar neighborhood.

## Forbidden patterns
- generic 'hyperparameter optimization' or 'AutoML survey' queries
- generic 'benchmarking LLMs' or 'scientific method' queries
- queries naming campaign order, cycles, attempts or search history
- any attempt to locate the withheld published paper on this exact research question, its title, authors, mirrors, or papers citing/discussing it
- queries on LLM-agent paper-writing or research automation

## Why these over generic alternatives
Generic queries (hyperparameter optimization, LLM benchmarking) would return high-citation but off-target work. Each query here maps to a concrete element of the run: the naive-vs-debiased interval comparison, the Bonferroni/resample baselines, the EB-IRT model, the searchers, and the MMLU-Pro replay. No references provenance existed beforehand, and no retrieval was run in this stage.
