# Reference Query Plan

**Status: ready.** Nine queries; planning only. No literature was retrieved, verified, or read in this stage. Titles and identifiers below come from the permitted task starters, not a new search. Existing `references.bib` and `references_provenance.json` are absent, so there is no prior query provenance to reuse or correct.

## Scientific Focus

The paper concerns conditional task-support investment needed for a fixed target model to become strictly first on public multi-task score matrices under mean, median, and trimmed-mean aggregation. Investment is the number or fraction of selected task coordinates. Selected scores follow `x_j + alpha*(1-x_j)` with `alpha` equal to 0.25, 0.5, or 1; rival scores remain fixed. This is a score-space counterfactual, not an observed training response, monetary cost, or causal estimate of contamination.

## Grounding and Evidence Limits

- `paper_data.json`, fields `downstream_study` and `final_evaluation`: the search found no qualifying winner, selected the baseline, and completed a qualified final evaluation. The final aggregate feasible rate is 0.6072530864197531 and mean verified gap fraction is 0.046025557721464154. These motivate attainability and certificate-gap themes, not an ordering of aggregation rules. Search and final scores have different evaluation scopes and are not evidence of improvement over one another.
- `source_evidence/downstream/program/src/program.py`: selected-method evidence is exact sorted-headroom selection for the mean, exhaustive support enumeration on at most six coordinates, and deterministic marginal-aggregate greedy selection on larger median/trimmed panels. The conventional even median averages two middle scores; trimming removes `floor(0.2*m)` values at each end. Strict first requires exceeding all rivals by more than `1e-10`.
- `global_memory/task/evaluate.py` and the final solution structure in `paper_data.json`: actual comparison controls are no intervention, random-order support selection, and marginal greedy. The workload includes ordinary, constant-score, zero-uplift copy, and joint-permutation cases. These integrity checks do not constitute an architecture comparison. Candidate-supplied diagnostics are explicitly marked unverified; they are not independent scientific evidence.
- `task/resources/final/manifest.json` and `task/resources/final/records.json`: locally recorded acquisition time is `2026-11-17T11:35:39.193972+00:00`; the records SHA-256 is `d80abb1b13c6962e15f04d9794fc18fcf39e91cf7c79c679e233d3031f934398`. The manifest retains individual source hashes and limitations. These are inspected local provenance, not a fresh network verification.
- `figures/` is empty and `paper_data.json` contains no ablation studies. No figures, matched ablations, universal robustness order, or successful rank-window/clipped-bound improvement can ground additional queries.

## Methods and Expected Comparators

The central methodological neighborhood is finite-sample sensitivity of means and order-statistic aggregators to sparse, bounded, one-sided coordinate changes. Distinguish exact minimum support from a feasible witness, a conservative lower bound, and proven infeasibility. Classical replacement breakdown is related context, not an interchangeable definition of the run's investment metric. The elementary mean sorting argument and exhaustive audit do not warrant a generic optimization citation search.

Reviewer-facing comparators are social-choice evaluation, strategic post-training incentives, benchmark task-selection sensitivity, and evaluation-data contamination. Social-choice or equilibrium models are related work, not executed baselines. Borda and multi-developer equilibria were not tested. The selected run does not support proposed coupled-clipped or rank-window methods as improvements.

## Benchmark Scope and Architecture

- **HELM/MMLU:** release `v1.13.0`, with 57 subject coordinates. Cite MMLU for task construction and HELM for the evaluation framework; neither paper replaces snapshot provenance. The manifest warns that evaluation conditions need not be identical across model rows.
- **Open LLM contents:** revision `9c09a7cae43334062a82cb164f2ef255013dafa2`; six raw-score coordinates are IFEval, BBH, MATH Lvl 5, GPQA, MUSR, and MMLU-PRO. Dataset citation metadata should come directly from the pinned official record; do not invent a paper or data license.
- **BBH sensitivity:** results revision `aa81ecc38fdc5708254b833923368970efdf5ef5`, with complete 24-subtask panels and exact model-revision matching. The manifest says this sensitivity is separately reported and not scored or merged into the primary six-task contents scores. Contents and results are distinct runs; revision matching does not prove equivalent evaluation settings.
- **Architectural shifts:** none supported; the JSON field is empty. Subject-level versus task-level panels are a granularity distinction, not a representation or architecture transition. BBH's source-paper title does not imply a chain-of-thought experiment here.

## Query Set

1. **Core method:** `median trimmed mean finite-sample replacement breakdown order statistics` — foundational context for the actual robust aggregators and sparse-coordinate sensitivity; screen independently for foundational statistics sources, not leaderboard-specific discoveries.
2. **Comparator:** `"Evaluating Agents using Social Choice Theory" 2312.03121` — cardinal aggregation versus social-choice evaluation; no suggestion that ordinal aggregation was implemented.
3. **Comparator:** `"Leaderboard Incentives: Model Rankings under Strategic Post-Training" 2603.08371` — compare incentive-model assumptions with a single target, fixed rivals, and externally assumed response ceilings. Read before asserting details.
4. **Result-driven theme:** `"The Benchmark Lottery" 2107.07002` — task-panel sensitivity and the distinction between panel selection and aggregation; no presumed rule-order reversal.
5. **Benchmark:** `"Measuring Massive Multitask Language Understanding" 2009.03300` — the 57-subject MMLU structure, not the later HELM snapshot settings.
6. **Benchmark:** `"Holistic Evaluation of Language Models" 2211.09110` — the framework supplying HELM results, paired with the pinned local provenance.
7. **Benchmark:** `"Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them" 2210.09261` — identity of the separate BBH sensitivity panel, not a prompting or architecture comparison.
8. **Benchmark:** `"open-llm-leaderboard/contents" "9c09a7cae43334062a82cb164f2ef255013dafa2"` — citation metadata for the actual six-task snapshot; resolve directly at the official dataset revision if indexing is insufficient. Preserve the separate results revision for BBH provenance.
9. **Comparator:** `"Don't Make Your LLM an Evaluation Benchmark Cheater" 2311.01964` — contamination motivation and the boundary between assumed score improvements and measured training effects.

## Result-Driven Priorities

Prioritize response-ceiling-dependent attainability, support cardinality, and exact versus bounded certificates. Treat panel granularity as a scope variable rather than a demonstrated transfer effect. The selected baseline is the supported configuration; no search candidate has an established improvement. Do not search as though one aggregation rule is universally most robust or actual training costs were measured.

## Exclusions and Retrieval Safety

The prohibited prior study is intentionally unidentified. Do not infer its title, authors, or results. The later retrieval stage must prefer direct canonical records for the explicitly permitted starter identifiers and pinned dataset metadata. Do not expand citation graphs, references, cited-by lists, related-paper recommendations, surveys, discussion pages, mirrors, or repositories. Exact-title lookup is not permission to read arbitrary surrounding pages. If source isolation cannot be ensured, skip the unsafe query rather than broaden it.

The only topical query without a supplied identifier is foundational robust statistics; do not combine it with leaderboard manipulation or targeted-investment terms. If prohibited material is accidentally encountered, stop reading immediately and record the location and amount exposed in the reproducibility record. No such external encounter occurred during this local-only stage.

Avoid broad searches paraphrasing the research question; fabricated established names for local proposals; unsupported Borda, equilibrium, training, architecture, and chain-of-thought claims; presumed universal robustness or rule reversals; unpinned latest leaderboards; Arena-specific detours; and standalone searches for every component benchmark without an actual comparison. Generic optimization, generic benchmarking, scientific-method, writing-process, citation-volume, and campaign-chronology searches would dilute the actual score-intervention and order-statistic story. Exact permitted identifiers and the pinned dataset record provide more precise, safer coverage. The lm-evaluation-harness starter need not become a separate query merely because public score files were produced by an evaluation stack; this run does not evaluate models anew.

## Handoff

The JSON mirrors this memo with nine nonduplicate queries and no architecture query. Planning readiness means the literature neighborhood is grounded, not that references or scientific claims have been verified. Future retrieval must establish existence, metadata, substantive relevance, and actual reading before citation. This stage does not write bibliography, provenance, LaTeX, or claims-grounding artifacts and does not run any retrieval service.
