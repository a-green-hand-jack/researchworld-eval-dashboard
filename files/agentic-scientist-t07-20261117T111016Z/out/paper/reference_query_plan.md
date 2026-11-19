# Reference Query Plan

**Status:** ready. **Scope:** planning only; no references retrieved or verified in this stage.

## Central topic

Predict full-benchmark binary accuracy and model rankings from a small shared item subset using historical source-model responses, score-directed acquisition, and source-trained score decoding.

## Grounding and priorities

Primary evidence is `paper_data.json`, especially `all_programs`, `best_correct`, and `final_evaluation`; recent memory is secondary. Method details are grounded in:

- `results/ideas/01_frozen_surrogate_random_audit/program_1/src/IMPLEMENTATION.md`
- `results/ideas/02_score_targeted_all_query_ridge/program_1/src/IMPLEMENTATION.md`
- `results/ideas/03_log_odds_shift_residual_decoder/program_1/src/DECODER.md`

Three successful variants are recorded. Development uses `arc_challenge`, `ifeval`, `commonsense`, and `gsm`, budgets 5, 10, and 25, and seeds 101 and 211:

| Implemented package | Development MAE |
| --- | ---: |
| Frozen surrogate with randomized audit correction | 0.0810613202961334 |
| Score-directed selection with all-query ridge | 0.055403088322603176 |
| Same selection with optional log-odds/residual-ridge decoder | 0.05464601737059244 |

The qualified final evaluation covers **nine other cases**, seeds 1009, 2003, and 3001, and the same budgets. Candidate MAE is 0.038991605535293065 versus recorded IRT 0.05911223215296765, uniform 0.10520541810011626, anchors 0.15674229873896958, and source prior 0.08335016635136305. Final Spearman is 0.8158480130897703 and Kendall is 0.6715966634525837.

Recorded paired lineage-block bootstrap intervals favor the final candidate over baselines. Candidate minus IRT MAE is -0.02012062661767458, with 95% interval [-0.02570984836073398, -0.014632649205711504]. The policy uses 200 draws, equal case weights, and inference conditional on fixed cases. Copies of the same interval in seed records are not independent analyses.

There are no recorded ablation studies, figures, existing BibTeX, or reference provenance. Candidate diagnostics are unverified. Prioritize **package-level score prediction**, not causal explanations for the small nonlinear-candidate difference. Nonlinear activation is not verified and the candidate permits linear fallback. Development/final scores are not a paired improvement estimate. Implementation-stage notes about unfinished experiments do not negate later recorded evaluations.

## Methods and comparator scope

- **Primary method:** source-weighted conditional full-score/item covariance, a fixed nested content-group-unique query path, and all-query ridge with an optional difficulty-centered offset blend.
- **Optional decoder:** prefix-only penalized scalar log-odds shifts, averaging shifted probabilities over original item columns, and prefix-matched residual ridge. Rasch/logistic latent-trait estimation is conceptual context, not a claim of full IRT fitting.
- **Earlier estimator:** frozen pilot-only predictions plus randomized audit residual correction. Model-assisted sampling/generalized difference estimation grounds conditional unbiasedness only without shrinkage/clipping; unequal content groups need size weighting. Score unbiasedness does not guarantee unbiased MAE or accurate rankings.
- **Comparators:** random averaging, source prior, clustering anchors, IRT/tinyBenchmarks, supervised reference-instance prediction, and adaptive acquisition. Only recorded baseline families are measured; exact published-method reproductions are not established. Random averaging/prior prediction need no standalone broad search.
- **Validation:** source-only lineage-held-out tuning, with nested refitting for the nonlinear candidate. Anonymous lineage groups do not establish complete ancestry separation.

The architecture story concerns **estimators**, not neural architectures: reconstruction-plus-audit versus direct score ridge, then an optional nonlinear-plus-residual decoder. Acquisition also changes between the first two packages, preventing an isolated decoder comparison. No named-model-family or neural architecture transition is established.

## Benchmark context

- Development: `arc_challenge`, `ifeval`, `commonsense`, `gsm`.
- Final evaluation: `bbh`, `gpqa`, `mmlu_pro`, `musr`, `openllm_math`, `legalbench`, `math`, `med_qa`, `mmlu`.
- Provenance: Open LLM Leaderboard and HELM binary model-by-item matrices in the supplied `benchmark-prediction` snapshot, commit `55faff496947789f94e6b5908c77cbc3e84f81ad`.

Use MMLU-Pro for a precise final-benchmark reference and HELM/Open LLM Leaderboard v2 for ecosystem coverage. Do not spend a separate query on every matrix. Both `mmlu` and `mmlu_pro` occur, but no transfer mechanism between them is established. The live leaderboard is not the frozen snapshot; neither gated item-text access nor new LLM evaluations is needed.

## Ten queries

1. **Result-driven theme:** `c-optimal experimental design regularized regression linear functional prediction`
   - Grounds conditional score-covariance acquisition and all-query ridge in prediction-directed design. Do not assert exact c-optimal equivalence or isolated selector gains.
2. **Estimator architecture:** `Rasch model fixed item difficulty penalized ability estimation`
   - Positions the optional log-odds curve; prefix-matched residual correction is an implementation distinction, not an independently established gain.
3. **Core method:** `model assisted survey sampling generalized difference estimator residual correction`
   - Grounds the earlier randomized audit correction, unequal-group weighting, and restricted unbiasedness argument, not empirical superiority or unbiased rankings.
4. **Comparator:** `"Anchor Points: Benchmarking Models with Much Fewer Examples"`
   - Required clustering-anchor context for a recorded baseline family. Resolve supplied arXiv:2309.08638; local exact reproduction is not established.
5. **Comparator:** `"tinyBenchmarks: evaluating LLMs with fewer examples"`
   - Required IRT/compact-benchmark context because IRT is the strongest recorded final baseline. Resolve arXiv:2402.14992; distinguish its full method from local IRT.
6. **Comparator:** `"100 instances is all you need" "predicting the success of a new LLM"`
   - Closest supplied supervised reference-instance prediction work. Resolve arXiv:2409.03563 and compare prediction targets/protocols, without claiming an experimental reproduction.
7. **Comparator:** `"Active Evaluation Acquisition for Efficient LLM Benchmarking"`
   - Distinguishes adaptive acquisition from the fixed shared path. Resolve arXiv:2410.05952; per-target adaptation is interface-incompatible and was not evaluated.
8. **Benchmark context:** `"MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark"`
   - Grounds a final benchmark and leaderboard component. Resolve arXiv:2406.01574 without inferring MMLU-to-MMLU-Pro transfer.
9. **Benchmark context:** `"Holistic Evaluation of Language Models"`
   - Grounds the HELM ecosystem for development/final matrices. Resolve arXiv:2211.09110; distinguish the binary snapshot from HELM's full multi-metric protocol.
10. **Benchmark context:** `"Open LLM Leaderboard v2" Fourrier Habib Lozovskaya Szafer Wolf`
    - Grounds the second data ecosystem using the supplied official source. Its live page is not snapshot provenance or ancestry evidence.

## Safeguards and rejected alternatives

No retrieval occurs now. Later retrieval should directly resolve supplied allowed titles/identifiers and official sources. Screen metadata before opening foundational-method sources and keep discovery narrow. The prohibited paper is unidentified: do not infer its identity or invent an exclusion title. A keyword denylist alone cannot guarantee safe retrieval. Do not expand forward citations, cited-by lists, related-paper feeds, surveys, reviews, discussions, or reproductions that may expose prohibited material. If encountered, stop reading immediately and log what, where, and how much was read.

Forbid attempts to identify or use the prohibited paper or associated materials; unrestricted searches restating the research question; generic optimization/benchmarking/scientific-method/paper-writing searches; campaign chronology; unsupported neural architecture or named-family transfer; continuous-score/adaptive-stopping experiments; unmeasured ablations; nonlinear-mechanism superiority; and design-unbiasedness of clipped/shrunken scores or rankings. Do not substitute the newest repository branch, live leaderboard, or gated details for the measured snapshot.

These queries outperform generic alternatives in relevance because each maps to implemented estimators, successful evaluated packages, expected comparator families, or actual data ecosystems. Conditional bootstrap results warrant careful baseline positioning, not a broad robustness search. Continuous-score ranking and open-ended sparse sample-pool aggregation are not central to complete binary matrices. No prior provenance exists to reuse or repair. No new reference is claimed read or verified.
