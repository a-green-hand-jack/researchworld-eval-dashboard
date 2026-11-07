# Reference query plan

**Status: ready.** Eight targeted queries; no reference retrieval performed. Readiness concerns the scientific query plan, not blanket permission to access search results.

## Central topic

Finite-budget sensitivity of fixed-ridge Bradley-Terry rankings to nested binary-outcome flips, using influence-screened exact-refit path search on Chatbot Arena preferences and season-specific NBA games.

## Grounding and scope

- `paper_data.json` is the primary run evidence. Its strongest recorded search configuration is **Checkpoint Weighted Flip Path Exchange**; the final evidence contains `arena` and NBA 2011-2015 season cases. Earlier evaluated configurations use Arena and NBA 2006-2008. The original exposure-matched block-deletion title does not describe the executed intervention.
- `task/task_contract.json`, particularly its public method description, specifies 14,272 usable Arena search comparisons and 43,205 final comparisons; unique NBA games within season-specific panels; and flips at floored fractions 0.001, 0.005, and 0.01 of all usable rows. Ties enter fitting as half-wins but cannot be flipped. These are controlled outcome edits, not evidence of real vote fraud.
- `results/ideas/03_checkpoint_weighted_flip_path_exchange/program_1/src/IMPLEMENTATION.md` documents centered fixed-ridge Bradley-Terry fitting, optional home advantage, aggregated sufficient statistics, influence screening, exact refits, adaptive checkpoint paths, and whole-path exchanges with affected-prefix caching and fallback. This is bounded heuristic search, not an optimality certificate.
- The final aggregate perturbation statistic is 0.055641534391534395, versus 0.00935242200328407 for uniform random flips, 0.011150133225384662 for degree-stratified flips, and 0.007573891625615763 for the fitted-margin heuristic. These internal aggregates select the literature neighborhood; they do not by themselves establish significance or universal superiority. Several NBA paired intervals include zero.
- Final Arena influence-discrepancy values are approximately 0.2235-0.3350, compared with approximately 0.00036-0.02274 across final NBA cases and budgets. These reported normalized discrepancies motivate the local-derivative versus finite-refit distinction, not a causal explanation of the domain difference.
- The public contract defines grouped paired bootstrap resampling of **fixed** candidate and baseline interventions: Arena raw-document connected components and NBA unique games are the respective units. This is conditional uncertainty, not attack reoptimization in every resample; algorithmic seeds are not independent datasets.
- `global_memory_summary.md` supplies private planning context only. It does not establish an executed matched human/GPT-4 study. `figures/` is empty. No `references.bib` or `references_provenance.json` exists, so there is no prior retrieval-query provenance to reuse or correct.

## Core methods and comparator expectations

The main methodological neighborhood is paired-comparison estimation, influence diagnostics, finite perturbations verified by exact refitting, and discrete local rank search. Actual comparator families are uniform random flips, degree-sum-quartile-stratified random flips, and smallest-absolute-margin flips. Degree matching is approximate exposure matching, not exact endpoint matching.

Fixed-influence and adaptive exact-refit paths occur inside the candidate procedure, but the final evidence does not provide isolated ablations for every component. Exchange-based rank-aggregation methods are neighboring methodological context, not an additional evaluated baseline. Preference-vote manipulation and finite-sample deletion sensitivity are relevant related-work contrasts, with intervention differences stated explicitly.

## Benchmark context and architectural shifts

The scientifically relevant comparison is crowd preferences versus sports outcomes on unequal comparison graphs and fixed season panels. NBA outcomes are refitted with Bradley-Terry; an Elo-named data source does not imply use of Elo ratings or an Elo baseline. No neural architecture or learned-representation transition is supported: `architectural_shifts` is intentionally empty, and there are no architecture queries. Sufficient-statistic aggregation is an implementation representation, not an experimentally established architectural shift. There is no causal attribution of cross-design differences and no executed MT-Bench human-versus-model-judge comparison.

## Selected queries

1. **Core method:** `"Rank Analysis of Incomplete Block Designs" "The Method of Paired Comparisons" Bradley Terry 1952`
   - Explicitly permitted original model foundation. Separate it from this run’s ridge, tie handling, and optional home coefficient.
2. **Core method:** `"Understanding Black-box Predictions via Influence Functions" Koh Liang 2017`
   - Explicitly permitted influence foundation. The observed finite-change errors make approximation limits and exact-refit validation central.
3. **Core method:** `"rank aggregation" "local search" "exchange" before:2017`
   - Older methodological context for the strongest configuration’s swap/replacement search over nested rank-perturbation paths. Do not claim a tested Kemeny solver, isolated component gains, or global optimality.
4. **Baseline comparator:** `"Improving Your Model Ranking on Chatbot Arena by Vote Rigging" Min 2025`
   - Explicitly permitted manipulation comparator. Contrast interventions without assuming vote-rigging experiments were reproduced or interpreting controlled flips as misconduct.
5. **Result-driven theme:** `"An Automatic Finite-Sample Robustness Metric" Broderick Giordano Meager 2020`
   - Explicitly permitted finite-sample sensitivity context. Distinguish dropping observations from flipping outcomes and avoid importing deletion guarantees.
6. **Benchmark context:** `"Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference" Chiang 2024`
   - Explicitly permitted platform context for the actual crowd-preference panel, not architecture evaluation or judge comparisons.
7. **Benchmark context:** `"Bradley-Terry" "home advantage" basketball before:2017`
   - Older sports-model context for the actual NBA season panels and home nuisance term, not Elo benchmarking or pooled cross-season stationarity.
8. **Result-driven theme:** `"paired comparisons" bootstrap ranking before:2017`
   - Older uncertainty context for rank intervals and paired fixed-plan effects; some NBA intervals include zero, making conditional and nonuniform conclusions important.

## Retrieval safeguards for the next stage

No search, Semantic Scholar call, scholarly call, download, or external reference reading occurs in this stage. The supplied permitted starting works are **candidate seeds**, not newly verified citations or works claimed to have been read here.

For the five exact-title seed queries, restrict subsequent lookup to the matched original permitted work and its direct original publication record. Do not request citing papers, related works, recommendation lists, reviews, reproductions, discussion pages, or citation-graph expansion. The remaining three queries are supplemental pre-2017 methodological searches, not permission for broad current-topic discovery. Enforce their date restriction at the retrieval layer; query syntax alone does not guarantee enforcement. An older publication date is a scope restriction, not proof that a candidate or hosting page is admissible. If unrelatedness to the prohibited material cannot be established without potentially accessing it, skip the candidate or query rather than broadening it or trying to identify the forbidden work. Fewer admissible references are preferable to violating the exclusion.

Do not investigate the identity, title, authors, or findings of the unnamed prohibited study. If prohibited content is encountered accidentally in a later stage, stop reading immediately and record the location and extent of exposure in the reproduction notes; do not use that content. No such literature encounter occurred during this local-artifact planning stage.

## Rejected alternatives

- Broad leaderboard-instability, vote-attack, adversarial-deletion, and preference-removal discovery risks the prohibited study and its discussion network. Exact permitted seed lookups plus bounded older methods provide higher signal with less exposure risk.
- Generic optimization, benchmarking, scientific-method, and paper-writing queries add no precise scientific comparator. The exchange-search query is tied specifically to the strongest observed method and ranking objective.
- MT-Bench, matched human/GPT-4 coverage, question-block deletion, WebDev Arena, and other optional datasets lack executed evidence here. Dataset availability and prospective plans are insufficient grounds for queries framed as completed comparisons.
- Architecture transitions, cross-architecture transfer, exact endpoint-matching controls, Elo baselines, globally minimal attacks, and deletion certificates are unsupported and excluded.
- Campaign chronology and internal evaluation labels are not scientific literature neighborhoods. Final artifacts and method families, rather than milestones, determine the query set.

This plan mirrors `reference_query_plan.json`. It writes neither bibliography/provenance files nor paper/claims artifacts.
