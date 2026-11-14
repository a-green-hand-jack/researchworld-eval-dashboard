# Reference Query Plan

**Status:** ready

## Central topic
How network width (model size) relates to the onset delay of grokking on modular-addition tasks in small transformers, tested via a memorization-capacity crossover hypothesis with a width-by-train-fraction sweep, right-censored delay metrics, bootstrap slope CIs, and muP-style parametrization controls.

## Grounded evidence driving the plan
- Three model variants were evaluated: a memorization-capacity crossover sweep (width x train fraction), a width-aware output-scaling (muP-like) variant, and a hidden-layer W=m*V reparametrization targeting an effective-learning-rate confound.
- Sealed final evaluation: log-delay-vs-width slope -0.020, bootstrap CI [-0.58, 0.35] (spans zero), reference slope -0.37; censored fraction 0.4; shuffled-label control max val acc ~0.012. The width effect is therefore conditional/inconclusive rather than a clean monotone law.
- Setting: small transformer, modular addition mod prime p, exhaustive p^2 pairs, weight decay (AdamW).

## Queries
1. `grokking generalization beyond overfitting small algorithmic datasets modular arithmetic` (core_method) — Anchors the delayed-generalization phenomenon and the modular-arithmetic task family used in every run.
2. `progress measures for grokking mechanistic interpretability modular addition transformer` (benchmark_context) — Defines the small one-block transformer / modular-addition setting and Fourier-circuit view that the width sweeps build on.
3. `grokking circuit efficiency memorization versus generalization circuits` (baseline_comparator) — Circuit-efficiency explanation is the main competing account to the memorization-capacity crossover hypothesis (idea 1).
4. `grokking transition from lazy to rich training dynamics` (baseline_comparator) — Lazy-to-rich account is the comparator behind the width-aware output-scaling variant (idea 2).
5. `Omnigrok loss landscape weight norm grokking` (baseline_comparator) — Weight-norm / loss-landscape explanation and initialization-scale dependence relevant to init-scale and weight-decay choices.
6. `unifying grokking and double descent model size` (baseline_comparator) — Connects grokking to double descent in model size and data fraction; relevant to the width-by-train-fraction sweep.
7. `maximal update parametrization width-independent feature learning hyperparameter transfer` (architectural_shift) — Idea 2 introduced muP-like width-aware output scaling and idea 3 a W=m*V hidden-layer reparametrization; muP is the literature behind both.
8. `effective learning rate width scaling normalization weight decay AdamW` (result_driven_theme) — Idea 3 tests an effective-learning-rate confound in width; decoupled weight decay (AdamW) and effective-LR dynamics are needed to interpret it.
9. `memorization capacity of models bits per parameter` (result_driven_theme) — Memorization-capacity crossover hypothesis (t_mem falls with width, critical width scales with train fraction) needs capacity-estimation and memorization-dynamics work.

## Comparators expected by reviewers
Circuit efficiency, lazy-to-rich dynamics, weight-norm/Omnigrok, double descent, memorization capacity.

## Forbidden / avoided patterns
- generic 'optimization', 'benchmarking', 'scientific method', 'paper writing' phrasing
- chronology/search-history queries (cycle order, idea numbering, combined score)
- queries phrased as 'effect of model size/width on grokking delay' or 'scaling of grokking with model size' (risk of surfacing the excluded prior paper; the starter literature plus component literatures suffice)
- internal harness terms: eligible, rubric, worker, program_1
- LLM scaling-law or large-language-model pretraining queries not tied to memorization capacity

## Why these over generic alternatives
Each query maps to a specific hypothesis or control actually run (capacity crossover, muP-style scaling, effective-LR confound, censored delay under weight decay). Generic queries ("model scaling", "optimization", "benchmarking") were rejected as low-precision. Direct "model size vs grokking delay" queries were deliberately avoided to respect the task's exclusion of the prior paper; the width question is covered through component literatures instead. No retrieval was performed in this stage.
