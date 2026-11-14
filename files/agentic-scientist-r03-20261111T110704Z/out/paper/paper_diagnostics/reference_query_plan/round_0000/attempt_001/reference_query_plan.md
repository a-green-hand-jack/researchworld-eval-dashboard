# Reference Query Plan

## Central topic
Choosing a small subset of k benchmarks to run on a new model and imputing its scores on the remaining benchmarks from a historical model-by-benchmark score matrix (MTEB, HELM Lite, Open LLM Leaderboard), evaluated by held-out-model normalized RMSE against random selection, ridge and permuted-control baselines.

## Core methods
- greedy conditional-variance (Gaussian/low-rank) benchmark subset selection
- EM-estimated Gaussian covariance with conditional-mean imputation of missing scores
- wrapper cross-validated forward selection of benchmarks
- rank-Gauss (quantile) transform with range clipping
- per-target NNLS stacked ensemble of imputers
- monotone-link latent-skill model with Huber MAP and Laplace posterior
- A-optimal experimental-design selection

## Comparators
- random benchmark selection
- greedy ridge regression on selected benchmarks
- permuted-control baseline
- low-rank matrix completion / probabilistic matrix factorization
- item-response-theory style latent ability models for LLM evaluation
- benchmark-sparsification work (metabench, tinyBenchmarks)
- observational scaling laws and Sloth skill scaling laws

## Benchmarks
- MTEB (embedding models x tasks)
- HELM Lite (core scenarios)
- Open LLM Leaderboard (IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO)

## Method shifts visible in the run
- from pure conditional-variance Gaussian imputation (nRMSE 1.067 in search) to quantile-transformed wrapper-selected NNLS-stacked imputation (nRMSE 1.028)
- adding a monotone latent-skill member and A-optimal selector to the stack gave identical search score to the stacked incumbent (no measurable gain)
- final sealed evaluation nRMSE 0.562 overall, with MTEB error decreasing as k grows (0.787 at k=2 to 0.638 at k=20)

## Result-driven themes
- few benchmarks recover the rest only modestly: skill over random selection is small (final 0.016) while gain over greedy ridge is larger (0.099)
- prediction difficulty varies by leaderboard (HELM 0.50, Open LLM 0.48, MTEB 0.70)
- diminishing returns in k on MTEB
- permuted-control gap shows that cross-benchmark structure is real
- low-rank / latent-skill structure in model-by-benchmark matrices

## Queries
1. `predicting language model benchmark performance from a subset of benchmarks low-rank` (core_method): Central problem: infer a new model's scores on unrun benchmarks from k observed ones using a historical score matrix.
2. `greedy subset selection conditional variance Gaussian process sensor placement submodular` (core_method): Theory-side literature behind greedy conditional-variance selection and its near-optimality guarantees.
3. `EM algorithm multivariate Gaussian missing data covariance estimation conditional mean imputation` (core_method): The incumbent imputer estimates a Gaussian covariance by EM from a partially observed matrix and imputes by conditional mean.
4. `stacked generalization non-negative least squares ensemble` (baseline_comparator): Per-target NNLS stack of imputers is the best-scoring configuration; need the stacking/NNLS-combining reference.
5. `matrix completion low-rank probabilistic matrix factorization missing entries` (baseline_comparator): Expected comparator family for score-matrix imputation with a low-rank/latent structure.
6. `item response theory efficient evaluation of language models few examples` (baseline_comparator): Latent-ability models (monotone-link latent skill) and benchmark-sparsification comparators such as metabench/tinyBenchmarks.
7. `observational scaling laws low-dimensional capability space language models` (result_driven_theme): Supports the low-dimensional latent skill explanation and the starter-list work on cross-benchmark predictability (including Sloth).
8. `A-optimal Bayesian experimental design active feature selection` (architectural_shift): A-optimal latent selector was added in the third variant and gave no gain; need experimental-design background.
9. `cross-benchmark agreement of LLM benchmarks correlation of model rankings` (result_driven_theme): Variation in predictability across leaderboards and the permuted-control gap relate to benchmark-agreement analysis.
10. `MTEB massive text embedding benchmark leaderboard` (benchmark_context): MTEB is the primary data source and the setting with the highest error across k.

## Forbidden patterns
- generic 'benchmarking' or 'optimization' phrasing
- scientific method / paper-writing phrasing
- chronology of campaign cycles, ideas, or attempts
- internal terms such as combined_score, rubric, program_1, eligible
- queries naming or hinting at the prior published paper on this exact task (do not search for its title, authors, or results)
- unsupported claims about generative-LLM benchmark transfer beyond MTEB/HELM Lite/Open LLM Leaderboard

## Why these over generic alternatives
Queries are tied to methods and numbers in the run (Gaussian conditional-variance selection, wrapper CV selection, NNLS stacking, latent skill, A-optimal design; MTEB/HELM Lite/Open LLM Leaderboard). Generic 'benchmarking' or 'optimization' queries were rejected as unlikely to return citable, relevant work.
