# Reference Query Plan

**Status:** ready. Planning only: no references retrieved and no bibliography, provenance, paper, or claims-grounding files written.

## Central Topic

Predict an LLM's full binary benchmark score and ranking from **8, 16, or 32 items**, using source-only score-targeted selection and a ridge/Rasch-residual profile blend. The scientific story is a bounded evaluation of this estimator and its generalization limitations, not an established universally superior compression method.

## Grounding and Evidence Boundaries

- Primary grounding: `paper_data.json`, especially `/best_correct`, `/all_programs`, `/final_evaluation/metrics`, `/final_evaluation/limitations`, and `/final_evaluation/evaluation_evidence/episodes`. Method grounding: `results/ideas/03_rasch_residual_profile_mixtures_on_fixed_score_targeted_prefixes/program_1/src/METHOD.md` and its adjacent `program.py`. Dataset scope: `task/resources/search/manifest.json` and `task/resources/final/manifest.json`. Global memory supplies planning context only, not quantitative evidence.
- The selected search configuration combines fixed score-covariance prefixes, group-balanced Rasch-residual particles, and ridge predictions. Its retained search MAE is **0.031563431544012165**. Sealed final evaluation retains MAE **0.08801465854359276**, RMSE **0.09789336720441476**, Spearman **0.7328732236748521**, and Kendall tau-b **0.5943160224743321** across three recorded evaluation seeds. Final evaluation completed but did **not** qualify; the precise cause is not established. These aggregate values motivate literature selection, not validated superiority claims.
- Final retained comparator MAEs are **0.1186668212839868** for IRT, **0.22047382735923254** for anchors, and **0.1335974367939037** for the uniform baseline. Comparator labels do not establish official-method reproduction or independent statistical significance.
- The `no_diversity` mode substitutes uniform nested selection while retaining learned prediction. Its retained final MAE is **0.044910877034389785**, lower than the primary method; search MAE **0.05351873980080848** has the opposite ordering. This supports searching for validation/generalization context, not asserting why the ordering changed or comparing absolute performance across different benchmark pools as a paired effect.
- The `no_calibration` mode returns the raw observed mean. Final retained MAE **0.10836174574059959** must not be described as a clean ablation of an affine calibration layer. Missing episodes and a nonzero final control-failure rate further limit interpretation. The reported difference interval `[-1, 1]` does not support significance, and particle spread is not target-calibrated uncertainty.
- Source-only grouped tuning is implemented, but independent outer-source comparisons and matched standalone mixture/linear ablations are not established by the method document. Tuning alternatives are not independent ablation results. The final artifact's candidate diagnostics are marked unverified.

## Methods and Comparators

The core method families are conditional score-covariance acquisition with a low-rank pivoted factorization; equal-group source weighting; ridge regression and mean shrinkage; Rasch-shrunk empirical response profiles with discrete ability-offset particles; Bernoulli posterior inference; exact observed plus expected unobserved score decomposition; and source-only group-disjoint blend tuning. The ridge component itself is unweighted; group weighting applies to acquisition, Rasch fitting, particle priors, and grouped tuning objectives.

Expected comparator literature includes clustering anchors (**Anchor Points**), IRT-assisted compression (**tinyBenchmarks**, **metabench**), learned adaptive acquisition, and reference-instance prediction of unobserved performance. Adaptive acquisition is related work, not a description of this fixed-prefix implementation. Uniform sampling, sample means, uniform selection with learned prediction, source means, constant predictions, copy controls, and the recorded IRT control matter experimentally; they need not each consume a retrieval query. Classical scalar-target experimental design and mixture psychometrics provide more precise methodological context than broad optimization searches.

The earlier anchor/audit residual configuration is not the selected method. It does not justify expanding this small plan into a survey-sampling or residual-audit bibliography.

## Benchmark Context and Architectural Shifts

- Development/search: **ARC-Challenge, IFEval, MMLU-Pro**.
- Final Open LLM Leaderboard-derived case keys: **bbh, gpqa, musr, openllm_math**.
- Final HELM-derived case keys: **commonsense, gsm, legalbench, math, med_qa, mmlu**.
- Matrices derive from the pinned `benchmark-prediction` snapshot **55faff496947789f94e6b5908c77cbc3e84f81ad**, with staged filtering and fixed item universes. Use manifest case keys where a more specific benchmark edition has not been verified. The final seeds are **5003, 7001, 9001**. These are recorded evaluation seeds, not demonstrated independent training replications.

**Architectural shifts: none supported** (`architectural_shifts: []`). Moving from a ridge predictor to a Rasch-residual mixture is an estimator/representation change, not an LLM architecture intervention; its isolated benefit is not established. Model names or heuristic family metadata alone do not support Transformer/Mamba, dense/MoE, verified ancestry, or architecture-transfer claims. Groups exposed to the method are opaque; grouping metadata is explicitly heuristic. Final benchmark separation also does not itself demonstrate cross-benchmark parameter transfer: each case supplies its own source matrix for fitting.

The two dataset-context queries cover HELM and the leaderboard rather than spending the limited query budget on every benchmark. Benchmark-specific original citations may be needed during paper drafting, but should be chosen only for cases actually discussed in detail and independently verified. Do not assume ARC-Challenge is an official leaderboard-v2 component just because its matrix is staged alongside v2 benchmarks.

## Ten Queries

| # | Category | Query | Run-specific rationale |
|---|---|---|---|
| 1 | baseline_comparator | `Anchor Points: Benchmarking Models with Much Fewer Examples` | Permitted starter; response-clustering anchors and weighted score estimates contextualize the recorded anchor comparator, without asserting an audited reproduction. |
| 2 | baseline_comparator | `tinyBenchmarks: evaluating LLMs with fewer examples` | Permitted starter; anchors plus IRT directly contextualize the Rasch predictor and recorded IRT control. |
| 3 | baseline_comparator | `metabench A Sparse Benchmark of Reasoning and Knowledge in LLMs` | Permitted starter; information-based IRT selection and learned score prediction contrast with scalar score-covariance acquisition. |
| 4 | baseline_comparator | `Active Evaluation Acquisition for Efficient LLM Benchmarking` | Permitted starter; separates learned adaptive acquisition from this implementation's fixed source-only prefixes; not a completed comparison. |
| 5 | core_method | `c-optimal experimental design prediction linear functional` | Classical design for a scalar prediction target is the relevant neighborhood; no claim of exact c-optimality. |
| 6 | core_method | `latent class Rasch models local dependence item responses` | Mixture psychometrics contextualizes source-profile particles and conditional-independence limitations; no equivalence to a named model is presumed. |
| 7 | baseline_comparator | `100 instances is all you need: predicting the success of a new LLM on unseen data by testing on a few instances` | Permitted starter; reference-instance outcome prediction directly relates to the unobserved-score inference mechanism. |
| 8 | result_driven_theme | `grouped cross-validation hierarchical dependent data prediction assessment` | Classical dependent-data validation contextualizes source-group tuning and cautions prompted by the search/final control reversal; no causal shift diagnosis. |
| 9 | benchmark_context | `Holistic Evaluation of Language Models HELM` | Permitted starter; evaluation framework underlying six final matrices, with staged-universe limitations retained. |
| 10 | benchmark_context | `Open LLM Leaderboard v2 Fourrier Habib Lozovskaya Szafer Wolf` | Permitted starter; leaderboard context, subject to benchmark-specific provenance verification rather than blanket v2 membership claims. |

## Retrieval Boundaries and Rejected Alternatives

No existing `references.bib` or `references_provenance.json` is present, so there is no prior retrieval-query history to reuse or correct. All ten entries are future citation-oriented queries, not claims that those works have been consulted. The seven named-title/context seeds are explicitly permitted in the supplied starter literature; the other three are classical methodology neighborhoods. No network retrieval was performed at this stage.

Future retrieval must preserve the task's prohibition on the unnamed paper and all material citing, discussing, or reproducing it. **Do not try to discover its identity or construct title/author guesses.** Prefer the permitted named seeds and restrict the methodological searches to classical experimental-design, psychometric, and dependent-data validation sources. Do not expand citation graphs, follow citing/cited-by links or related-paper recommendations, or read unvetted surveys, aggregation pages, reviews, repositories, or social discussions. If prohibited material is accidentally encountered, stop reading immediately and record the location and exposure extent; do not use it. Exact-title seeds reduce exposure but do not certify that a destination is safe. Do not force the retrieval stage to fill a quota if these safeguards prevent safe sourcing.

Reject broad optimization, generic benchmarking, scientific-method, writing-process, campaign-history, and milestone queries: they neither explain the observed estimator nor distinguish its controls. Also reject unsupported architecture transitions, continuous-score evaluation, open-ended pooled benchmarks, multimodal methods, and neural-model training. The binary fixed-universe experiments do not justify those neighborhoods. Avoid claiming universal superiority, calibrated posterior intervals, significant gains, certified ancestry, exact comparator reproduction, or a known cause of final non-qualification.

This plan prioritizes the strongest selected configuration while preserving the final evaluation's limitations and the selection-control reversal. The result-driven themes are selection-versus-estimation separation, grouped validation, limited generalization, and descriptive score/ranking evidence—not a chronology of attempted methods.
