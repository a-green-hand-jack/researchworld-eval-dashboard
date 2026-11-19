# Reference query plan

**Status: ready.** Nine queries; planning only. No reference retrieval, literature reading, or bibliography creation was performed in this stage. Proposed citation targets are not claims of having read those works.

## Central topic

Budgeted selection of benchmark columns and prediction of unmeasured new-model scores from incomplete historical score matrices, using masked low-rank factors and predictive-variance reduction on MTEB and Open LLM Leaderboard data.

## Grounding and scope

- `paper_data.json` records a retained baseline, three unscored proposed variants, no best scored search variant, and no ablation studies. Its completed final evaluation supplies usable evidence for the retained method. Search failures are not measured scientific losses; search and final scores are different evaluation scopes.
- `source_evidence/downstream/program/src/program.py` implements masked alternating ridge factorization; historical held-out-cell rank selection; greedy covariance-trace selection; and conditional ridge reconstruction. The acquisition depends on queried columns and availability, not purchased score values. Do not describe it as score-adaptive latent-mixture inference.
- The same source includes candidate columns in its current target sum. Prediction-oriented design is therefore a methodological neighborhood, not proof that this code exactly minimizes risk only on the post-purchase unqueried targets.
- Recorded final comparators are random-query low-rank prediction, selected-benchmark ridge, the evaluator's correlation-central order labeled `medoid_ridge`, historical means, and purchased-score mean-offset transfer. Do not reinterpret the correlation-central order as an implemented k-medoids clustering algorithm.
- Final cases cover both sources, model and heuristic-family holdouts, increasing budgets, and column-permutation controls. The recorded aggregate structure gap is positive, as is the paired family-clustered interval against random-query low-rank prediction. These support related-work themes, not a novel-method victory or a universal sufficient budget. The final plan identifies the interval's comparator and clustering scheme.
- `task/resources/final/audit.json` pins MTEB results to `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383` and Open LLM Leaderboard contents to `9c09a7cae43334062a82cb164f2ef255013dafa2`. MTEB uses default/English test main scores with task/revision/subset distinctions; Open LLM uses six Raw columns. The latter dataset license is undeclared.
- `global_memory_summary.md` is qualitative context only. The plan follows actual final evidence and retained source rather than promoting its unsuccessful proposals. No existing `references.bib` or `references_provenance.json` was present, and `figures/` was empty.

## Methods, comparators, and representation scope

Core families are masked low-rank completion, prediction-oriented experimental design, and conditional ridge inference. The two foundational queries cover the literature behind both the retained method and matched low-rank/ridge controls; trivial mean and offset controls do not warrant separate searches.

Two permitted starter papers cover item-level evaluation reduction, which is related but different from selecting whole benchmark columns. Observational scaling and latent-skill prediction are positioning comparators, not executed baselines. Benchmark agreement contextualizes the structure control but is not itself a score-prediction metric.

**Architectural shifts: none established.** Embedding models and generative language models are separately evaluated populations. No shared fitted representation, embedding-to-generation transfer, encoder/decoder transition, or architecture intervention is demonstrated. Heuristic naming-based family splits do not supply architecture labels. Accordingly, the JSON architectural-shift list is empty and there is no architecture query.

## Queries

The query strings and categories below mirror the JSON. Exact-title starter queries are restricted to papers explicitly permitted by the task, not invitations to expand their citation graphs.

1. **Core method:** `"matrix factorization" "alternating least squares" "collaborative filtering" -"language model" -benchmark`
   Grounded in masked alternating ridge factors and conditional reconstruction. Seek foundational collaborative-filtering methods, not broad LLM benchmark prediction. Do not import missing-at-random guarantees.
2. **Core method:** `"V-optimal design" "linear regression" "prediction variance" -"language model" -benchmark`
   Grounded in covariance-trace query acquisition. Seek classical target-prediction variance reduction; do not assert exact unqueried-only optimality for this implementation.
3. **Baseline comparator:** `"tinyBenchmarks: evaluating LLMs with fewer examples" "2402.14992"`
   Permitted item-reduction comparator. Explain the difference between examples within a benchmark and entire benchmark columns; no executed tinyBenchmarks comparison is claimed.
4. **Baseline comparator:** `"metabench" "A Sparse Benchmark of Reasoning and Knowledge in Large Language Models" "2407.12844"`
   Permitted sparse composite-evaluation comparator using model histories. Contrast sparse-item construction with column-level score reconstruction; not an executed baseline.
5. **Benchmark context:** `"MTEB: Massive Text Embedding Benchmark" "2210.07316"`
   Permitted primary-source context for the actual embedding-task matrix. Cite the pinned results repository separately; the original paper does not establish the later snapshot's population.
6. **Benchmark context:** `"Open LLM Leaderboard" "open-llm-leaderboard/contents"`
   Resolve only the official dataset record. Actual columns are IFEval, BBH, MATH Lvl 5, GPQA, MUSR, and MMLU-PRO. Preserve the pinned revision and undeclared-license caveat; do not search broadly for papers discussing this dataset.
7. **Baseline comparator:** `"Observational Scaling Laws and the Predictability of Language Model Performance" "2405.10938"`
   Permitted comparator for latent-performance predictability from public evaluations. Do not rename the implemented empirical factorization a demonstrated compute-scaling law.
8. **Result-driven theme:** `"Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families" "2412.06540"`
   Permitted cross-family skill-prediction context for actual model/family holdouts. Avoid architecture-transfer claims and do not imply Sloth was evaluated.
9. **Result-driven theme:** `"Do These LLM Benchmarks Agree? Fixing Benchmark Evaluation with BenchBench" "2407.13696"`
   Permitted benchmark-dependence context for the positive corruption gap. Distinguish benchmark agreement and rank consistency from calibrated prediction of individual scores.

## Result-driven priorities

Prioritize dependence exploited by prediction and informed querying versus random-query low-rank reconstruction. Discuss model/family holdout conditions and improving recorded budget curves separately for each source. The available evidence does not establish a universal sufficient budget, superior nonlinear mixture or saturation models, robustness to arbitrary missing-not-at-random sampling, or generalization to untested architectures.

## Exclusions and downstream safety

- Never try to identify or infer the prohibited paper, authors, title, or findings, and never access its mirrors, abstracts, reviews, slides, videos, blogs, repositories, or derivative discussions.
- Reject broad central-problem searches such as “predict all LLM benchmarks from a few benchmarks” and broad benchmark-selection surveys. Prefer exact permitted starter titles/identifiers and foundational non-LLM methods to reduce exposure risk.
- Do not follow cited-by, related-paper, recommendation, review, social-media, or repository links from permitted records. For the dataset query, resolve only its official record. These restrictions are operational requirements; keywords alone cannot guarantee exclusion of unknown prohibited material.
- If prohibited material is encountered incidentally, stop reading immediately and record what appeared, where, and how much was exposed for the later reproduction documentation. Do not use that material as evidence or a source of further queries.
- Exclude generic optimization, benchmarking, scientific-method, writing, chronology, and search-history queries: they add little discrimination for the retained factors, query design, actual controls, and two evaluated datasets.
- Exclude superiority searches for overlap-shrunk covariance, latent mixtures, or monotone saturation: their unscored attempts do not establish comparative findings. Exclude architecture-transition and embedding-to-generation transfer claims.
- Do not present HELM, LiveBench, BigCodeBench, AlpacaEval, or synthetic matrices as evaluated datasets. No prior provenance exists here to audit or repeat; keep future provenance narrowly tied to this plan.

**Handoff:** resolve only the scoped targets under the task's access restrictions, then verify source relevance before citation. No retrieval has occurred, and the protected bibliography, provenance, paper, and claim-grounding files remain unwritten in this stage.
