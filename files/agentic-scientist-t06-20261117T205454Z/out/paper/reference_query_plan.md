# Reference query plan

**Status:** ready. Six queries; planning only, with no reference retrieval.

## Scientific scope and evidence

The paper concerns sensitivity of ridge-regularized Bradley–Terry rankings to small, influence-selected row deletions. The actual comparison is crowdsourced Chatbot Arena preferences versus historical NBA game outcomes—not MT-Bench human versus GPT-4 judgments.

Grounding takes precedence over the proposed study and private planning memory:

- `paper_data.json`: `all_programs`, `best_correct`, `top_programs`, and especially `final_evaluation.metrics` and `final_evaluation.evaluation_evidence.episodes`.
- `results/ideas/02_exact_refit_contender_screening/program_1/src/IMPLEMENTATION.md` and its `program.py`: clean-Hessian influence orders, fixed prefixes, mean-loss ridge correction, at most six contenders and converged retained-data refits. Its implementation-time statements that evaluation was unmeasured are superseded only where recorded evaluations supply evidence.
- `results/ideas/03_retained_curvature_shortlist_expansion/program_1/src/IMPLEMENTATION.md`: retained-Hessian one-step proxy, at most 24 screened contenders and 12 exact finalists. This is an algorithmic variant, not a neural-architecture change.
- `task/evaluate_final.py`: deletion fractions 0.001, 0.005 and 0.01; ridge 0.001; normalized inversion fraction and original-leader rank displacement; random and descending clean-log-loss deletion; fixed-mask conditional group-bootstrap refits.
- `task/resources/final/arena_manifest.json` and `task/resources/final/nba_manifest.json`: normalized/group-separated source partitions, connected-component restrictions, and historical-team/era limitations. Final retained data contain 38,192 Arena comparisons and 41,418 NBA games; final clean score vectors contain 64 and 74 participants, respectively.

No existing `references.bib`, `references_provenance.json` or figure files were present. There are no prior retrieval queries to reuse or correct.

## Methods and expected comparators

The core methods are centered Bradley–Terry estimation with half-win ties and a fixed mean-loss ridge penalty; clean-Hessian inverse influence for leader–contender contrasts; frozen nested row-deletion prefixes; bounded exact retained-data refitting using aggregated pair statistics; and a retained-curvature Newton screening variant. The uncertainty analysis resamples provenance groups while holding selected deletion masks fixed. It neither deletes whole groups as the attack unit nor reruns selection within bootstrap samples.

The measured controls are random row deletion, high-log-loss/disagreement deletion, unchanged-data copies and row permutations. Reviewer-facing literature should cover paired-comparison estimation, influence-function approximations, finite-sample data-removal robustness, and preference-vote manipulation as a related but distinct threat model. Do not invent a formal named literature for the run-specific high-loss heuristic or present published manipulation algorithms as executed baselines.

## Result-driven emphasis

- The bounded exact-refit selector improved the recorded search aggregate over the clean-Hessian-only selector. Retained-curvature shortlist expansion tied the exact-refit selector on that aggregate; this is not evidence of an additional improvement or a formal ablation.
- The selected method has greater final aggregate inversion disruption than random and disagreement deletion, but that aggregation hides dataset and budget differences. In the final conditional group-bootstrap records, mean disagreement-relative gains are negative for Arena and positive for NBA.
- All five final candidate scores are identical. Repeated seeds and permuted-row cases do not supply five independent dataset replications; seed-based uncertainty is not population uncertainty. Fixed-mask bootstrap results describe conditional sensitivity, not the robustness of a newly optimized deletion strategy on each sample.
- The candidate internally prioritizes original-leader displacement, whereas the aggregate evaluator measures ranking inversions. Distinguish these objectives and do not infer universal ranking fragility or global optimality from the local selector.
- **Architectural shifts: none supported.** Different named Arena participants are observations, not an architecture experiment. The method transition from first-order screening to bounded exact refits belongs under core methods, not architecture transfer.
- Cross-design differences are descriptive: source populations, comparison graphs, participant counts, historical eras and partitions differ. The evidence does not identify a causal effect of crowdsourcing versus sports evaluation design.

## Six queries

1. **Core method:** `"Rank Analysis of Incomplete Block Designs: I. The Method of Paired Comparisons"`
   Resolve the supplied Bradley and Terry (1952) work, DOI `10.2307/2334029`. It grounds the common estimator, not the additional ridge/tie conventions.
2. **Core method:** `"Understanding Black-box Predictions via Influence Functions"`
   Resolve the supplied Koh and Liang (2017) work, `arXiv:1703.04730`. It motivates clean-Hessian influence calculations without validating the finite-deletion shortlist.
3. **Result-driven theme:** `"An Automatic Finite-Sample Robustness Metric: When Can Dropping a Little Data Make a Big Difference?"`
   Resolve the supplied Broderick, Giordano and Meager (2020) work, `arXiv:2011.14999`. It connects finite-sample removal robustness to the need for refitting and qualified, condition-dependent conclusions; no globally minimal deletion claim follows.
4. **Benchmark context:** `"Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference"`
   Resolve the supplied Chiang et al. (2024) work, `arXiv:2403.04132`. Cite the actual 55k snapshot separately: `lmarena-ai/arena-human-preference-55k`, commit `18c298340948c0e7f7727399fd459cca6ce0ca6f`.
5. **Benchmark context:** `FiveThirtyEight nba-elo nbaallelo.csv`
   Resolve only the supplied source at `https://github.com/fivethirtyeight/data/tree/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo` and its original documentation. Cite the dataset/repository rather than inventing a journal article. The run uses deduplicated game outcomes and historical team codes, not a time-varying Elo estimator.
6. **Baseline/comparator context:** `"Improving Your Model Ranking on Chatbot Arena by Vote Rigging"`
   Resolve the explicitly supplied Min et al. (2025) work, `arXiv:2501.17858`. Use it only to position manipulation threat models; the run does not benchmark its algorithms or perform vote insertion/flipping.

## Retrieval boundaries and rejected alternatives

These are identity-resolution targets, not permission for broad discovery. The five paper titles are explicitly allowed starter works; the sixth target is the supplied NBA dataset source. Exact known identities provide better scientific precision and reduce prohibited-content exposure compared with broad leaderboard-deletion searches. No target is a claim that its contents have already been read or verified in this stage.

For the later retrieval stage, match only the supplied title/identifier or pinned dataset source before opening content. Do not inspect unrelated search hits, abstracts or snippets, follow citations/cited-by links, request related-paper recommendations, or traverse derivative discussions. Prefer direct known-identifier resolution where the retrieval implementation supports it. If retrieval cannot enforce these boundaries, stop that query rather than broaden it. If prohibited material is encountered accidentally, stop reading immediately and record what, where and how much was exposed in the reproduction record; do not investigate its identity. No such external encounter occurred during this planning stage.

Excluded queries include the prohibited work or any attempt to identify it; broad ranking-deletion/fragility discovery; generic optimization, benchmarking, scientific-method or writing terms; unexecuted MT-Bench, expert/GPT-4, WebDev or 140k Arena comparisons; and architecture-transfer narratives inferred from model names. Also excluded are unsupported global-optimality, adaptive-reordering, whole-group-deletion, causal-design and full-bootstrap-reoptimization claims. These alternatives would either overstate the actual experiments, dilute citation relevance, or violate independence constraints. A separate generic bootstrap search is not necessary for this small initial plan; the current results need careful conditional interpretation, not a new ungrounded methodological storyline.
