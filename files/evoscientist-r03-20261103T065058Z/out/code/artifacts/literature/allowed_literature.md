# Restricted literature notes: selecting complete benchmarks versus selecting examples or models

## Scope and provenance

Research only; no model experiments, dataset downloads, or implementations of proposed prediction methods were performed. Read `/work/research_request.md`, but the present user's **six-ID allowlist overrides its longer starter list**. Literature access was limited to these exact papers: 2210.07316, 2402.14992, 2407.12844, 2407.13696, 2405.10938, 2412.06540. No topic search, discovery API, citation traversal, recommendations, code-site visits, or attempt to identify the excluded exact-problem work was made. No priority or exhaustive novelty claim is supported or intended.

All six papers were fetched explicitly as **v1** (not a moving latest version). Verify against those versions, not later revisions. The PDF first-page arXiv stamps confirm v1 for every paper. Titles and authors were checked against their own metadata and PDF; in particular, the supplied starter shorthand for metabench and BenchBench differs from the fetched titles below. BibTeX uses the arXiv preprints, without inferring conference publication details.

Primary artifacts:
- `sources/<ID>/paper_v1.pdf`: complete fetched PDF.
- `sources/<ID>/abstract_v1.html`: own arXiv abstract/metadata page.
- `sources/<ID>/metadata.json`: exact URLs and parsed citation metadata.
- `sources/<ID>/plain_text_v1.txt` and `full_text_v1.txt`: plain and layout text extractions; complete archival sources, **including bibliographies**. Do not treat the bibliography as permission to read additional works.
- `sources/<ID>/body_before_references_v1.txt`: reference-free main-body reading copy (ends before the first References heading; appendices after references are absent).
- `access_log.jsonl`: request UTC timestamps, exact URLs, status, byte counts, and SHA-256; also records the local incidental-exposure note.
- `manifest.json`: file integrity and version verification; `fetch_allowed.py`: allowlisted direct acquisition script; `ACCESS_README.md`: access and extraction caveats.

Reading concentrated on each paper's own method/evaluation/limitations and selected methodological appendices; it was not an exhaustive reading of every appendix. No bibliography entry was followed. A local keyword-location command inadvertently displayed a few bibliography-line snippets from allowed PDFs; that pattern was stopped and the exposure logged. No excluded work was identified and no incidental snippet was used as evidence. Extraction warns about rotated text: numerical claims below use readable prose/captions/tables, not corrupted plot glyphs. All numerical results below are **paper-reported**, not reproduced here.

## 1. Units of selection: the critical distinction

The project observes historical aggregate scores `S[m,j]`, then evaluates a **new model** on `k` entire benchmark columns and predicts the other `N-k` scores. Here an entire benchmark means one specified aggregate-score column, with its dataset, language/subset, split, metric, and evaluation version fixed. The papers use “benchmark,” “scenario,” “task,” and “item” at different levels; compare operational units, not terminology.

| Allowed paper | What is reduced/selected? | Observations needed for a new target | What is predicted/evaluated? | Relation to choosing k complete benchmark columns |
|---|---|---|---|---|
| [1] MTEB | No learned sparse selector in the benchmark construction/evaluation described | Embeddings evaluated under each task's evaluator | Heterogeneous task/dataset scores | Supplies a diverse score-matrix setting and metric cautions, not a tested column-selection policy |
| [2] tinyBenchmarks | Individual examples, usually **within each scenario** | Responses on a small item subset; historical item-by-model correctness for fitting | Full scenario scores, then the benchmark aggregate | “100 examples per scenario” does not mean 100 or k entire benchmarks; it generally still touches every source scenario |
| [3] metabench | 739 individual items spread across **all six** source benchmarks | Item responses yielding six benchmark-specific latent abilities | Six original scores and their mean, using abilities jointly | Cross-benchmark information sharing is real, but all six components are administered; whole benchmarks are not omitted in that experiment |
| [4] BenchBench | Models/overlap sets used for benchmark agreement testing | Scores of several shared models on a target benchmark and reference benchmarks | Agreement of rankings/scores, not missing-score regression | Sampling model rows for benchmark validation is not selecting benchmark columns for a new model |
| [5] Observational Scaling Laws | Low-dimensional representation of observed base-benchmark scores; §5 selects **model rows/families** | Target model's base-benchmark profile; target-task labels on historical models | Downstream performance through a sigmoid of principal capabilities | Relevant low-rank predictor and experimental-design ideas, but §5's budget counts models, not target-model benchmark columns |
| [6] Sloth | Low-dimensional skill model; small-model observations anchor family efficiency | Size, training tokens, family identity, and usually at least one evaluated smaller same-family model | Performance of a larger, potentially untrained model on many benchmarks | A resource-to-performance scaling setting, not a learned choice of k benchmarks to run on the larger target |

**Consequences.** An aggregate model–benchmark matrix is not an item-response matrix. The item-selection methods in [2,3] cannot be reproduced from aggregate scores alone. Conversely, a column-level low-rank method is not a reproduction of their IRT procedures. Cross-task prediction, example reduction, model-row experimental design, and complete-column selection should be separate experimental labels. None of the cited item-budget results establishes a sufficient k for this project's complete-column budget.

## 2. Verified paper notes

### [1] MTEB: Massive Text Embedding Benchmark — 2210.07316v1

**Own sources:** https://arxiv.org/abs/2210.07316v1 ; https://arxiv.org/pdf/2210.07316v1

**Verified method/data.** The abstract describes 56 datasets, eight task types, 112 languages, and 33 embedding models. §3.1 exposes a common API mapping texts to fixed-shape vectors, dataset/software versioning, and released JSON results. §3.2 defines task-specific evaluation rather than a common correctness likelihood:

| Task type | Main metric in this v1 text | Evaluation detail |
|---|---|---|
| Bitext mining | F1 | Match cross-language sentence embeddings using cosine similarity |
| Classification | Accuracy | Embed train/test sets; this **v1 says kNN classifier**, not an assumed later evaluator |
| Clustering | V-measure | k-means over embeddings |
| Pair classification | Cosine-based average precision | Distances between embedded pairs; other threshold-based metrics also computed |
| Reranking | MAP | Rank query/reference similarities and average over queries |
| Retrieval | nDCG@10 | Embed queries and corpus; rank documents |
| STS | Spearman correlation of cosine similarity with labels | Continuous similarity judgments |
| Summarization | Spearman correlation with human judgments | Match generated-summary embeddings to closest human summary |

These are **task-internal train/test splits**, not held-out-model splits for predicting missing benchmark scores. Figure 2's use of 100 embedded texts per dataset is for a dataset-similarity visualization, not an item-selection accuracy experiment or a sparse benchmark selector. Table 1 reports English-subset task averages; multilingual analysis is separate (§4.4).

**Findings/limitations.** §4.2 reports substantial task-dependent model strengths, including retrieval-versus-STS specialization and different rankings even for superficially similar tasks. It explicitly acknowledges training/evaluation overlap and does not remove it from MTEB scores. Its suggestion that averaging many datasets reduces contamination effects is the authors' belief, **not an established guarantee**. Language coverage and model pretraining languages affect results (§4.4). MTEB concerns embedding models; do not generalize its matrix results directly to generative LLMs. A later pinned results repository may have different models, tasks, and evaluators from this 2022 v1; its stated directory count is not verified by this literature reading.

**Actionable use.** Preserve task/metric/language/split identities and normalize using training models only. Test whether a model specialized for retrieval or one language violates a global latent-factor predictor. Cost of one “benchmark” is heterogeneous: full-corpus retrieval and sentence similarity are not equal-cost operations.

**Code/data availability reported in paper, not visited:** https://github.com/embeddings-benchmark/mteb ; https://huggingface.co/spaces/mteb/leaderboard ; https://huggingface.co/datasets/mteb/results . Do not substitute these moving endpoints for the fixed dataset commit in the request.

**Evidence anchors:** §3.1–3.3, PDF pp.2–4; Table 1 p.5; §4.2–4.4 pp.6–8. Short supporting spans: “kNN-classifier”; “nDCG@10 serves as the main metric”; “model performance on different tasks to vary strongly” (§5).

### [2] tinyBenchmarks: evaluating LLMs with fewer examples — 2402.14992v1

**Own sources:** https://arxiv.org/abs/2402.14992v1 ; https://arxiv.org/pdf/2402.14992v1

**Verified methods.** §2 distinguishes scenarios, subscenarios, and individual examples. It estimates complete scenario scores from selected examples, then aggregates scores. §3 compares (i) subscenario-stratified random sampling, (ii) k-means of historical correctness vectors, selecting the nearest actual item to each centroid, and (iii) k-means of fitted IRT item parameters. Anchor weights are cluster population fractions. §4 fits a multidimensional 2PL IRT model,
`P(correct item i | model m) = sigmoid(alpha_i^T theta_m - beta_i)`.
Item parameters are trained on historical models; new-model ability is estimated with fixed item parameters from observed responses. The p-IRT estimator combines observed responses with predicted correctness of unobserved items. gp-IRT combines an anchor-weighted estimate with p-IRT to trade sampling variance against IRT misspecification bias. Ability can be estimated jointly from responses across scenarios; this is information sharing, not proof that a whole scenario can be omitted without cost.

**Calibration/fitting.** §4.4 uses hierarchical Bayesian variational inference, posterior means as point estimates, and validation to choose latent dimensions from `{2,5,10,15}`. §4.2 estimates the gp-IRT bias term by splitting training models, fitting IRT on one subset, and predicting held-out item responses on the other. Its anchor-variance correction divides the estimated variance by 4 **heuristically**. For bounded nonbinary item scores, §4.3 binarizes at a scenario-specific threshold preserving the training-set average approximately; it does not establish a likelihood for arbitrary continuous aggregate metrics.

**Evaluation protocol (§5).**
- Open LLM Leaderboard: 395 models, six scenarios, about 29K examples; 75%/25% model split, randomly or by submission date. This is the older six-scenario suite, not the v2 six-benchmark matrix in the request.
- MMLU: same models/splits; 57 subject areas and about 14K examples; equal-weight subject averaging matters.
- HELM Lite **v1.0.0**: 30 models with all ten core scenarios; about 10K examples. Random 11-fold CV, and organization-grouped splits in lieu of dates. Do not confuse this with the request's HELM Lite v1.13.0.
- AlpacaEval 2.0: 100 models, 805 examples, continuous preference scores; random four-fold CV or 25% latest-model holdout. Its judge-based evaluation cost is separate from statistical inference cost.
- Six combinations: three item selectors with vanilla versus gp-IRT (`++`) estimation; five restarts. Figure 3 studies average performance-estimation error; Appendix D.2 adds Spearman rank correlations. Account for subscenario weighting rather than pooling all items indiscriminately (§2, Appendix A).

**Reported results and unit warning.** Figure 3 reports roughly 2% average estimation error with 100 examples **per scenario**: 600/29K examples for the old Open LLM Leaderboard, 100/14K for MMLU treated alone, 1,000/10K for HELM, and 100/~800 for AlpacaEval. Do not compare this average-error claim to metabench RMSE as if they were identical metrics. A separate 40-specialized-model MMLU test finds correctness-vector anchors degrade more than IRT anchors. Figure 6 finds some larger individual errors despite a small average; the 2% figure is not a uniform bound or a coverage guarantee. Released IRT inference is described as taking seconds on CPU (§6), **not** an assertion that training IRT or running the language model costs seconds.

**Limitations for this project.** Requires historical item-level outcomes, low-dimensional IRT adequacy and stable item parameters. Distribution shift/specialization can invalidate representative anchors; p-IRT bias can persist with more observations under misspecification. Binarization loses score information. Model-level random splits do not by themselves exclude base/fine-tune relatives across train/test. No validated minimal complete-benchmark k or predictive-interval coverage protocol is supplied by these experiments.

**Availability reported, not visited:** https://github.com/felipemaiapolo/tinyBenchmarks ; https://huggingface.co/tinyBenchmarks . Paper reports pretrained IRT parameters, tiny datasets, evaluation tools, and tutorials.

**Evidence anchors:** §2–4, PDF pp.2–6; §5/Figures 3–6 pp.6–8; §6 p.8. Short spans: “choose a small fraction of examples”; “100 examples per scenario”; “fit the ability parameter”; “model misspecification”.

### [3] metabench — A Sparse Benchmark to Measure General Ability in Large Language Models — 2407.12844v1

**Own sources:** https://arxiv.org/abs/2407.12844v1 ; https://arxiv.org/pdf/2407.12844v1

**Data/preprocessing (§2.1).** ARC, GSM8K, HellaSwag, MMLU, TruthfulQA, WinoGrande: 28,632 original items (abstract), 6,875 unique LLMs after excluding flagged/merged submissions, 5,055 with all six benchmarks, and 152,261,495 recorded responses. Scores are put on a percent scale. Per benchmark it removes the lowest-scoring 0.1% of models, items with <1% standard deviation or >95% mean accuracy, and near-zero part-whole-correlation items (threshold ±0.05, or ±0.02 for WinoGrande).

**Verified method (§2.2–2.5).** First screen random item subsets via regression to original scores: 10,000 repetitions and validation-based selection. Preselect 350 items per benchmark for IRT model fitting. Fit one-dimensional 2PL/3PL/4PL models using `mirt`; estimate abilities using MAP or EAPsum; use GAMs to map abilities to original normalized scores. Information filtering selects high-Fisher-information items across ability quantiles. Bayesian optimization chooses IRT/ability-estimator/quantile/information-threshold settings with a validation objective combining reconstruction RMSE and subset size. Finally, the “Going Meta” variant uses **all six inferred benchmark abilities jointly** as GAM inputs to each original benchmark score.

**Split/metrics.** A score-stratified 10% global model test set is drawn among models with all six scores. A further 10% local validation split is formed per benchmark, stratified by that benchmark's score (§2.1); do not silently describe this as an exact 80/10/10 split, since populations and conditioning differ. Score reconstruction uses RMSE and rank correlation; footnote 2 provides MAE for comparison with tinyBenchmarks. Table 2 scores are on a 0–100 scale: an RMSE of 1.508 is about **1.508 percentage points**, not 1.508 relative percent.

**Reported results (Table 2, §2.5).** Final item counts are ARC 100, GSM8K 237, HellaSwag 58, MMLU 102, TruthfulQA 136, WinoGrande 106: **739 items total**. Mean per-benchmark RMSE is 1.856 points using only each benchmark's own ability, versus 1.508 points using all six abilities. Grand-average-score RMSE is 0.814 points. These are different targets and cannot be interchanged. The body reports Spearman 0.996 for reconstructed grand-average scores, and **Pearson** 0.928 for the meta-ability versus grand average; the abstract calls its ~0.93 meta-factor association Spearman. Preserve that within-version discrepancy rather than silently assigning one correlation type to both claims.

**Adaptive extension (§2.6).** CAT repeatedly picks the item with maximum Fisher information given current ability, stopping when estimated ability SE <0.1 or the item pool is exhausted. Table 3 evaluates re-estimation of abilities **on the training set**, not held-out benchmark-score error. Its ability RMSE and median item count are not substitutes for Table 2's score reconstruction results or new-model generalization.

**Limitations.** §3.1 explicitly flags dependent base/fine-tune/related submissions, biased item-parameter estimates, low subject/item ratios, and limited out-of-distribution validation. Screening is narrated before the split in §2.1; without inspecting implementation, it is **not verified** that every response-dependent preprocessing decision was fit on training models only. Reproduce with nested train-only screening rather than assuming leakage safety. Validation used to optimize item subsets must remain separate from final testing. Narrow ability ranges and new specialized model families can change information functions. All six source components are still administered: the paper's joint predictor does not by itself validate choosing only k complete components for a new model.

**Availability reported, not visited:** https://github.com/adkipnis/metabench . Analysis uses R 4.4.0, `mgcv`, `mirt`, `rBayesianOptimization`, `psych`, `catR`; code/data link appears on PDF p.1.

**Evidence anchors:** §2.1–2.2 pp.4–5; §2.3–2.5/Tables 1–2 pp.5–7; CAT/Table 3 p.8; §3.1 p.9. Short spans: “jointly using all six latent ability estimates”; “totalling 739 items”; “on the training set”; “potentially violating the IRT model assumption”.

### [4] Benchmark Agreement Testing Done Right: A Guide for LLM Benchmark Evaluation — 2407.13696v1

**Own sources:** https://arxiv.org/abs/2407.13696v1 ; https://arxiv.org/pdf/2407.13696v1

**Verified method/data.** Uses over 40 benchmarks with results cutoff January 2024 (§2) to study benchmark agreement testing (BAT). Computes Kendall rank correlation or Pearson score correlation on models shared by reference and target benchmarks. Analysis admits intersections of at least five models; the **recommendation is at least ten, preferably more**, not that five models suffice for reliable validation. BenchBench implements configurable reference sets, model recommendation, multi-granularity reports, and a benchmark-level leaderboard (§5).

**Best practices (§4).** Aggregate appropriate references via mean win rate; sample more, diverse models randomly; also report agreement on contiguous rank groups (e.g. 5/10/20 models); interpret correlations relative to an empirical reference distribution. Their suggested agreement threshold is a Z-score above −1 relative to that distribution, **not** an absolute error tolerance or a statistically calibrated confidence interval. References should match the construct of interest, rather than indiscriminately including every benchmark.

**Findings.** Agreement depends on which reference benchmarks, which models, model count, model granularity, and which correlation metric are used. Global agreement can be much higher than agreement among similarly strong models. Pearson and Kendall cannot use the same numerical “high agreement” threshold. Table 1 reports BAT standard deviation decreasing from 0.31 to 0.10 with the combined recommendations (about 67%); despite the table's variance terminology, these entries are labeled σ, not variance estimates.

**Limitations (§8) and relevance.** Low agreement can reflect either construct mismatch or unreliable evaluation; novel valid abilities need not agree with old tests. Reference selection remains consequential. These are benchmark-validation diagnostics, not a new-model score-imputation algorithm, a benchmark-column selector, or a held-out-model accuracy evaluation. Even perfect ranking can coexist with large absolute score errors. A correlation-based feature selector should therefore be validated with unobserved-column MAE/RMSE as the primary project endpoint, not BAT alone.

**Availability reported, not visited:** https://github.com/IBM/BenchBench ; https://huggingface.co/spaces/per/BenchBench . Only the paper was read, not repository/leaderboard content.

**Evidence anchors:** §2–4 pp.3–7; §5 p.8; §8 p.9. Short spans: “at least 10 models”; “Report Multiple Granularities”; “data-driven Threshold”; “just not reliable”.

### [5] Observational Scaling Laws and the Predictability of Language Model Performance — 2405.10938v1

**Own sources:** https://arxiv.org/abs/2405.10938v1 ; https://arxiv.org/pdf/2405.10938v1

**Verified method (§3).** Construct low-dimensional principal capabilities from observed standard benchmark scores. A model's target downstream error/accuracy is fit with a scaled sigmoid of a linear combination of capabilities. Within families, capabilities are approximately linear in log training compute. This yields a capability-equivalent-FLOP axis for interpretation, with Llama-2 as reference. The prediction from observed capabilities does not require disclosing the target model's training compute. The target model must already exist and have its base-benchmark profile evaluated; this is distinct from forecasting an untrained model using resource metadata.

**Data/fitting.** §3.2 analyzes 77 pretrained base models from 21 families and eight input benchmarks: MMLU, ARC-C, HellaSwag, Winogrande, GSM8K, HumanEval, TruthfulQA, XWinograd. Less than 1% of entries are missing. Three PCs explain about 97% of variation **in that collected matrix**, not a universal rank bound. Appendix B.3: iterative PCA imputation, initialized by column means, uses PC-1 by default and at most 1,000 iterations; PCA then uses three PCs. Data are mean-centered without additional scaling because scores are already normalized to [0,1]. Both imputation and PCA are fitted on training models only and applied to test models. §3.4 fits the scaled sigmoid by least squares; scale h is restricted to [0.8,1.0].

**Validation (§4).** Primary extrapolation split uses models with training compute ≤ Llama-2-7B (8.4×10^22 FLOPs) for training: 47 train and 30 test models. Stronger models are held out. Evaluation uses normalized target-score MSE, with model size and training FLOPs as baselines. Experiments concern emergent-capability tasks, agentic benchmarks, and changes associated with chain-of-thought/self-consistency, with application-specific model sets/splits. Do not apply the 47/30 count to every application. The v1 text preregisters functional forms for future-model checks; it does **not** report completion of those future checks.

**The selection result is model-row selection (§5).** Uses V-optimal design over the principal-capability matrix, minimizing a trace prediction-variance criterion under a **number-of-models** budget, with structured exhaustive search over model-family combinations. Validation compares downstream scaling fits from selected models to random model subsets; its application fits can use only a small subset of historical models. It is not a procedure for choosing which base benchmarks to evaluate on a new target. A transpose-based adaptation to benchmark columns would be an independently specified adaptation with different observations and validation requirements.

**Limitations for this project (inference from stated setup, not a separate authors' limitation list).** Few missing entries in a dense, curated matrix do not validate high or nonrandom missingness. Near-saturation or specialization may undermine transfer; PCA variance explained does not establish low prediction error on omitted columns. Good extrapolation requires stable capability-to-target relations and suitable base evaluations; pretraining-data overlap and differing evaluation protocols remain concerns. Scores on [0,1] need not have equal variance or utility. The V-optimal formula presumes an informative design and invertible selected information matrix; score-curve extrapolation and predictive-interval coverage are not guaranteed by its design criterion.

**Availability reported, not visited:** https://github.com/ryoungj/ObsScaling . Paper reports implementation and collected data (§4).

**Evidence anchors:** §3 pp.4–7; §4 pp.7–10; §5 pp.11–12; Appendix B.3 p.24. Short spans: “77 models”; “less than 1% of all data”; “fitted on the train set only”; “optimal set of models”; “without additional scaling”.

### [6] Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families — 2412.06540v1

**Own sources:** https://arxiv.org/abs/2412.06540v1 ; https://arxiv.org/pdf/2412.06540v1

**Verified method (§3).** Model benchmark expectations using a low-dimensional latent skill vector and benchmark loadings. Skills depend on a family-specific intercept and shared slopes for `log(size)`, `log(training tokens)`, and their interaction. Benchmark scores are lower-asymptote-adjusted sigmoids or learned monotone links of those skills. The general link is a two-hidden-layer monotone neural network with nonnegative weights and final sigmoid. Training uses Huber loss (δ=0.01), Adam, and decaying learning rate. Optimization is nonconvex. Basic Sloth fixes sigmoid links and lower asymptotes; the general version can learn them.

**Data (§4.1–4.2).** Twelve benchmarks across Open LLM Leaderboard v1/v2. Thirty model families total: 28 represented in v1, 17 in v2, intersection 15. Separating base/instruction variants yields 53 families. These are **family counts, not model counts**. V2 includes IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO, matching names in the request but not verifying its fixed snapshot or licenses.

**Held-family extrapolation protocol.** Leave out a family as the target while retaining its **smallest model**, or in a second experiment the **two smallest models**, as training anchors. Larger members are predicted. Base and corresponding instruction-tuned families are not split across train/test; the tested-family eligibility rule also avoids testing an older family version when a newer version is in training. Thus this is not zero-shot leave-entire-family-out validation. Target larger models need not be trained/evaluated in the intended use case; smaller-family benchmark observations and resource metadata identify their family efficiency.

**Metrics/baselines/calibration.** Average within-family MAE, then average across families, in percentage points (§4.2). Baselines include shared-intercept/slope FLOP scaling, family-intercept shared-slope FLOP scaling, PCA+FLOPs, and a full-dimensional Size-and-Tokens variant; these are descriptions of this allowed paper's experiments, not permission to access additional cited works. With two small-model anchors, FLOP baselines can also fit family-specific slopes. Basic-link lower asymptotes use multiple-choice chance levels (weighted across subsections when necessary), zero otherwise, and the first percentile of full-leaderboard TruthfulQA scores. That last choice is a source-specific calibration heuristic; a leakage-safe project reproduction should estimate any empirical floor on training data only. Do not silently describe it as a train-only estimate. The discussed three-skill solution is an interpretation selected for that analysis, not a general identification of the number of abilities.

**Downstream experiment (§4.4).** Fit skill-to-task logistic regressions, excluding Llama-3-70B base/instruct from Sloth fitting, then use resource-predicted skills for coding/emotional-intelligence predictions. This is different from requiring observed large-target base-benchmark scores as in [5]. AgentBench extension drops family-specific intercepts to avoid overfitting.

**Limitations explicitly stated (Appendix A).** Usually requires data from at least one model in the target family. Flexible learned links have no extrapolation guarantee for distant hypothetical targets. Identifiability is understood only for the simple version. Theorem 3.2 assumes fixed invertible links, fixed lower asymptotes, full-rank design/loadings and standardized full-rank skills; it identifies parameters only up to transformations, not uniquely named causal skills. It is **not** a benchmark-budget sample-complexity theorem. Missing or unreliable token counts and family labels restrict its direct use on arbitrary leaderboard matrices (project implication).

**Availability reported, not visited:** https://github.com/felipemaiapolo/sloth (PDF p.1).

**Evidence anchors:** §3 pp.3–5; §4.1–4.2 pp.6–8; §4.4 pp.9–10; Appendix A p.14. Short spans: “only the smallest model of the test family”; “two smallest models”; “no guarantee of extrapolation”; “rank(X) = p”.

## 3. Recommended next experiments — proposals only, not run

These recommendations are independently specified experimental controls, not findings or attributed algorithms beyond the six sources. They do not assert novelty or exhaustiveness.

1. **Pin the estimand and budget.** Define each column as a fixed task/language/split/main-metric/version score. For each k, observe complete selected columns and evaluate only the genuinely unobserved `N-k` columns. Keep aggregate-score prediction separate from ranking and from predicting the grand average. Report both unit-cost k and measured/estimated evaluation cost; at k=N there are no unobserved columns, so do not record zero prediction error as evidence of success.
2. **CPU-cheap controls.** Compare training-column means; random k columns plus regularized multi-output linear regression; correlation/diversity-based column selection with the same predictor; and a small-rank factor model with regularized estimation of new-model coordinates from selected columns. Fit means/scales, selectors, rank, penalties and imputation within training/validation folds. Vary selector and predictor separately. A benchmark-column experimental-design variant motivated by [5] should be labeled an adaptation, not its published row-selection method.
3. **Separate available information.** Use aggregate-score methods on the pinned MTEB matrix. Only include [2,3] as executable controls if historical item-level responses and identical evaluation protocols are actually available; otherwise they are conceptual unit-of-selection comparisons. Add resource-based Sloth-style controls only when size/tokens/family information is sufficiently verified; missing metadata must not be silently imputed from inaccessible sources.
4. **Hold out model identities and relatives.** Use random held-out-model splits for an easy reference; add grouped base/fine-tune/family splits and temporal splits where trustworthy metadata exist, plus specialist holdouts motivated by [1,2,3]. Fit every selection rule using historical training models only. At inference, a sequential selector may use newly observed selected-column scores, never true unobserved scores. Describe family/date availability rather than inventing labels.
5. **Quantify error rather than agreement alone.** Primary endpoints: per-column and macro-averaged held-out MAE/RMSE in native/percentage-point units, plus train-standardized errors for heterogeneous metrics. Secondary: Spearman/Kendall across held-out models per target, reported at multiple capability granularities [4]. Report model-level error quantiles and failures, not just a grand mean. Bootstrap by model/family as appropriate; simple cell bootstraps ignore shared-model dependence.
6. **Define what “k is enough” means before testing.** Choose a validation tolerance ε and required success fraction q; select the smallest k meeting that target on validation, then report locked test error and uncertainty. If prediction intervals are added, calibrate residuals on a disjoint model-level calibration set and report test coverage and width separately under random and shifted splits. The literature results above do not supply calibrated interval coverage for this project. Under family/temporal shift, calibration may fail and must be measured rather than promised.
7. **Stress-test missingness and scale.** Compare an honest common-observed submatrix with training-only missing-data handling; audit whether missingness tracks model quality/task difficulty. Treat specialist and nonrandomly missing rows as potential negative results. Low PCA rank on [5]'s nearly complete generative-model matrix is motivation, not evidence that the different MTEB matrix or six-column v2 leaderboard admits accurate tiny-k extrapolation.

**Expected diagnostic outcomes, not measured results:** grouped/specialist splits may increase errors; correlation can remain high while native-score errors grow; benchmark selection gains can disappear after holding the inference model fixed; heterogeneous metric scaling may change selected columns. Report such outcomes even if unfavorable.

## Sources — only the six permitted papers

[1] Niklas Muennighoff, Nouamane Tazi, Loïc Magne, and Nils Reimers. *MTEB: Massive Text Embedding Benchmark*. 2022. https://arxiv.org/abs/2210.07316v1 ; PDF https://arxiv.org/pdf/2210.07316v1

[2] Felipe Maia Polo, Lucas Weber, Leshem Choshen, Yuekai Sun, Gongjun Xu, and Mikhail Yurochkin. *tinyBenchmarks: evaluating LLMs with fewer examples*. 2024. https://arxiv.org/abs/2402.14992v1 ; PDF https://arxiv.org/pdf/2402.14992v1

[3] Alex Kipnis, Konstantinos Voudouris, Luca M. Schulze Buschoff, and Eric Schulz. *metabench — A Sparse Benchmark to Measure General Ability in Large Language Models*. 2024. https://arxiv.org/abs/2407.12844v1 ; PDF https://arxiv.org/pdf/2407.12844v1

[4] Yotam Perlitz, Ariel Gera, Ofir Arviv, Asaf Yehudai, Elron Bandel, Eyal Shnarch, Michal Shmueli-Scheuer, and Leshem Choshen. *Benchmark Agreement Testing Done Right: A Guide for LLM Benchmark Evaluation*. 2024. https://arxiv.org/abs/2407.13696v1 ; PDF https://arxiv.org/pdf/2407.13696v1

[5] Yangjun Ruan, Chris J. Maddison, and Tatsunori Hashimoto. *Observational Scaling Laws and the Predictability of Language Model Performance*. 2024. https://arxiv.org/abs/2405.10938v1 ; PDF https://arxiv.org/pdf/2405.10938v1

[6] Felipe Maia Polo, Seamus Somerstep, Leshem Choshen, Yuekai Sun, and Mikhail Yurochkin. *Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families*. 2024. https://arxiv.org/abs/2412.06540v1 ; PDF https://arxiv.org/pdf/2412.06540v1
