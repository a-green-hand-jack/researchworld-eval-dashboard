# Restricted-source literature notes

Access date: 2026-11-02 (UTC). This is a literature/evaluation-planning artifact, **not a paper draft**.

## 1. Scope, access, and exposure accounting

Only the five user-allowlisted research papers below were retrieved. No web search, citation graph, recommendation service, research-paper repository, dataset page, or linked research paper was opened. Paper links to code/data were extracted from the allowed papers themselves but **not followed**. Separate official ICML 2026 instructions and the official template archive were accessed solely for template provenance.

The supplied `/abs/` URLs were used as identifiers; the actually retrieved research endpoints were the corresponding direct arXiv `/html/` endpoints. Unversioned HTML disclosed the versions below; the same versioned HTML endpoints were subsequently accessed to verify resource links. These are the current versions served during this session, not necessarily their original 2022/2024 submissions.

| ID | Title verified on the paper | Authors verified on the paper | Version banner actually accessed |
|---|---|---|---|
| [1] 2210.07316 | MTEB: Massive Text Embedding Benchmark | Niklas Muennighoff; Nouamane Tazi; Loïc Magne; Nils Reimers | v3, 19 March 2023 |
| [2] 2402.14992 | tinyBenchmarks: evaluating LLMs with fewer examples | Felipe Maia Polo; Lucas Weber; Leshem Choshen; Yuekai Sun; Gongjun Xu; Mikhail Yurochkin | v2, 26 May 2024 |
| [3] 2407.12844 | metabench: A Sparse Benchmark of Reasoning and Knowledge in Large Language Models | Alex Kipnis; Konstantinos Voudouris; Luca M. Schulze Buschoff; Eric Schulz | v2, 20 February 2025 |
| [4] 2405.10938 | Observational Scaling Laws and the Predictability of Language Model Performance | Yangjun Ruan; Chris J. Maddison; Tatsunori Hashimoto | v3, 1 October 2024 |
| [5] 2412.06540 | Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families | Felipe Maia Polo; Seamus Somerstep; Leshem Choshen; Yuekai Sun; Mikhail Yurochkin | v5, 1 December 2025 |

The colon separating metabench's displayed name and subtitle in this table is editorial: its HTML presents them on separate lines. Author affiliations and title capitalization were not inferred from outside records.

### What was actually read

- HTML title/author/version banners, abstracts, introduction, methods, main results tables and captions, conclusions, and limitations for all five papers. MTEB Table 1 was additionally reorganized locally into rows for readable verification.
- Full HTML responses necessarily contained bibliography markup. A local parser stopped producing readable text at the `ltx_bibliography`/`bib` section boundary, **before any bibliography entry reached the reading output**. Raw research HTML was not retained. Appendices after the bibliography were not read.
- Citation-link text, footnotes, navigation, and scripts were generally removed from readable extracts. This loses internal cross-reference numbers and can remove methodological footnotes. Link verification was limited to extracting code/data addresses from the same allowed paper main bodies.
- Initial MTEB and tinyBenchmarks excerpts included their dedicated related-work prose, which is within the allowed papers' main text. No cited identity was resolved and no cited link was followed. As an additional precaution, dedicated related-work sections were then omitted from the reading copies of all papers; metabench, Observational Scaling Laws, and Sloth were read from those copies. Sloth §2.2, part of its methodological setup/comparison, was read.
- No PDF, figure-image inspection, source archive, appendix, supplementary experiment, proof appendix, or executable research code was accessed or run. Main-text numerical claims are author-reported, not independently reproduced. Plot-only values were not guessed.

**Exposure status:** No non-allowlisted research paper or external page discussing the unnamed prohibited work was accessed, and no prohibited-paper identity was sought. No identifiable restricted exposure was detected that triggered the requested stop condition. Allowed main text contains incidental prior-work discussion; this is not a certification that the unnamed work is never alluded to there. The exposure accounting above explicitly records the related-work prose that was read rather than claiming it was all excluded.

## 2. Essential distinctions

Let a response matrix have **models as rows** and **individual benchmark items as columns**, with columns grouped into tasks/datasets. These are different experimental problems:

| Problem | Selection/input unit | Target | What the allowed papers establish |
|---|---|---|---|
| Item-level subsampling/distillation | Individual questions/examples, usually within each scenario | Reconstruct that model's full-benchmark score from a few item responses | tinyBenchmarks [2]; metabench [3] |
| Whole-task selection | Entire datasets/tasks, preserving their evaluation protocols | Infer an aggregate or omitted task scores from a subset of fully evaluated tasks | **No end-to-end method for this problem was verified in these five papers.** Cross-task correlations are motivation, not a demonstrated selector. |
| Observational scaling prediction | Already measured standard benchmark scores of a target model | Predict its harder downstream performance through a low-dimensional capability representation | Observational Scaling Laws [4] |
| Resource-to-performance scaling prediction | Parameter count, training tokens, family identity, calibrated family data | Predict benchmark scores of a larger/hypothetical model | Sloth [5] |
| Model/family selection for fitting a scaling analysis | Model rows or entire model families | Reduce the number of models requiring downstream evaluation | V-optimal design in [4] §5; **not task selection** |
| Benchmark construction/evaluation | A heterogeneous suite of embedding datasets | Measure strengths and tradeoffs across embedding applications | MTEB [1]; not itself a subset-prediction algorithm |

In particular, metabench uses cross-benchmark information but still administers **selected items from all six benchmarks**. Sloth's low-rank sharing is not an item or task selector. MTEB's discussion of size/performance is not a fitted predictive scaling-law method comparable to [4–5].

## 3. Verified paper summaries

### [1] MTEB: Massive Text Embedding Benchmark

**Evidence anchors:** abstract; §§3.1–3.3, 4.1–4.4; Table 1. Short anchor: “no particular text embedding method dominates across all tasks”.

**Contribution and data.** A common embedding evaluation interface spanning 58 datasets, eight task types, and 112 languages. Ten datasets are multilingual. The abstract reports evaluation of 33 models. The English Table 1 covers **56 datasets across seven types**, not all 58 datasets/eight types; bitext mining is evaluated separately. Table 1's dataset counts are classification 12, clustering 11, pair classification 3, reranking 4, retrieval 15, STS 10, summarization 1.

**Evaluation protocol verified in main text:**

| Task type | Main metric and evaluator |
|---|---|
| Bitext mining | F1 from cosine-nearest sentence-pair matching |
| Classification | Accuracy; logistic regression on train embeddings, maximum 100 iterations, scored on test embeddings |
| Clustering | V-measure; mini-batch k-means, batch size 32, number of clusters equal to number of labels |
| Pair classification | Average precision from cosine similarity; other threshold-based metrics also returned |
| Reranking | MAP; query/reference cosine ranking, metrics averaged over queries |
| Retrieval | nDCG@10; cosine ranking over the document corpus |
| STS | Spearman correlation using cosine similarity |
| Summarization | Spearman correlation with human assessment; score generated summary using its closest human-reference embedding |

The paper uses **test splits except MSMARCO, which uses dev** (§4.1). It places no benchmark-level input-length cap; truncation is model-dependent (§3.3). Its pair-classification discussion mentions best binary thresholds, but does not establish a separate held-out calibration split in the accessed main text; do not invent one.

**Verified result examples.** In English Table 1, ST5-XXL scores 73.42 on classification and 82.63 on STS; SGPT-5.8B-msmarco scores 50.25 on retrieval. The absence of one winner across task types is the more relevant finding than any single historical average. These are historical main-metric scores, not current leaderboard rankings.

**Failure modes and limits.** STS success does not imply retrieval/clustering success; symmetric similarity and asymmetric query/document tasks behave differently. Model size is insufficient to explain all differences. §4.2 explicitly acknowledges training/evaluation overlap and leaves it in reported scores; averaging many datasets is an author justification, **not a demonstrated contamination correction**. Dataset version, language, truncation, retrieval corpus, metric, and aggregation must be fixed before comparing subsets.

**Code/data availability claimed and linked by main text:** https://github.com/embeddings-benchmark/mteb ; https://huggingface.co/spaces/mteb/leaderboard ; https://huggingface.co/datasets/mteb/results . Addresses extracted only; contents and present availability unverified.

### [2] tinyBenchmarks: evaluating LLMs with fewer examples

**Evidence anchors:** §§2–5, 6.1–6.2; Eqs. 3.1, 4.1, 4.3–4.4. Short anchor: “100 examples per scenario”.

**Problem and method.** Use full item-response histories of training LLMs to select a few examples **within scenarios**, then estimate full scores for unseen LLMs. Baselines/variants are stratified random sampling, k-means on historical correctness vectors, and k-means on multidimensional two-parameter IRT item representations (discrimination vector plus difficulty). Anchor weights equal cluster fractions. Each selector is evaluated with a raw weighted estimator and a “++” IRT-enhanced estimator, for six strategies overall.

IRT assumes `P(correct) = sigmoid(alpha_i^T theta_model - beta_i)`. p-IRT retains observed responses and imputes unobserved items using fitted probabilities. gp-IRT mixes the weighted subset estimator and p-IRT to trade sampling variance against model bias. The mixing rule is a **heuristic**, not a universally optimal guarantee. For anchor estimators, the described variance heuristic divides estimated variance by four. Item parameters use variational inference; latent dimensions are selected from {2, 5, 10, 15} using validation within training data. Nonbinary scores in [0,1] are binarized at a training-data/scenario-specific threshold approximately preserving the aggregate mean (§4.3).

**Data, splits, aggregation.**

- Original Open LLM Leaderboard: six scenarios, approximately 29K items, 395 LLMs, 75/25 train/test **model** split, either random or temporal. Overall score is the average of scenario accuracies.
- Standalone MMLU: approximately 14K questions, 57 subjects, same 395 LLMs/splits; subject accuracies are averaged rather than allowing larger subjects to dominate.
- HELM Lite v1.0.0: ten scenarios, approximately 10K examples, 30 complete models. Random evaluation uses 11-fold model cross-validation; organization-grouped splits supply a more challenging alternative because dates were unavailable. Overall metric is mean win rate.
- AlpacaEval 2.0: 805 examples, 100 LLMs; random four-fold model cross-validation or newest 25% held out. Performance is judge-based win rate, not ordinary classification accuracy.
- Results are averaged over five restarts. Anchor selection and IRT fitting use training models only; test models expose only their selected-item responses at prediction time.

**Verified results.** The main text reports approximately two-percentage-point average estimation errors with 100 examples **per scenario**, not 100 examples for every entire benchmark. Figure 3's caption identifies budgets of 600/29K for the six-scenario leaderboard, 100/14K for standalone MMLU, 1000/10K for HELM, and 100/805 for AlpacaEval. Figure 1 reports 1.9% error on the illustrated recent-model MMLU setting. These are empirical score-estimation errors, **not confidence coverage or uniform worst-case guarantees**. The main MMLU error analysis reports errors at most about four points for nearly all examined models, with an extremely low-performing exception.

**Shift and calibration pitfalls.** A separate 40-model specialized-LLM MMLU test degrades correctness-vector anchors more than IRT anchors. Severe architectural/training-data shifts and unusual easy/hard response patterns remain limitations; periodically refresh anchors and IRT parameters. The p-IRT consistency proposition assumes known true item parameters and consistent ability estimates; it does not validate finite-sample uncertainty under misspecification. gp-IRT's bias calibration must remain inside training data. No general calibrated confidence-interval result was verified.

**Code/resources linked:** https://github.com/felipemaiapolo/tinyBenchmarks . The paper claims release of subsets, pretrained IRT parameters, and CPU estimation tools; repository contents were not accessed.

### [3] metabench: A Sparse Benchmark of Reasoning and Knowledge in Large Language Models

**Evidence anchors:** §§2.1–2.5, 3.1–3.2, 4.1; Tables 1–3. Short anchor: “858” items in the main score-reconstruction caption/table.

**Data and preprocessing.** Six original Open LLM Leaderboard benchmarks: ARC, GSM8K, HellaSwag, MMLU, TruthfulQA, WinoGrande; 28,632 original items. After excluding flagged/merged models, the paper reports 6,875 LLMs from 1,355 users, over 152 million responses, and 5,055 LLMs evaluated on all six benchmarks. It discards the lowest-scoring 0.1% of subjects per benchmark, near-constant items (SD below 1%), very easy items (mean above 95%), and items with approximately zero item/total-score correlation.

**Method.** First select 350 items per benchmark using repeated random subsampling with GAM score reconstruction. Then fit **one-dimensional** 2PL/3PL/4PL IRT models, estimate abilities with MAP or EAPsum, and retain informative items using Fisher information over ability quantiles. Bayesian hyperparameter optimization on the validation set trades reconstruction RMSE against retained item count. Final GAMs can use each benchmark's information separately or jointly exploit all six reduced benchmarks. This is **item-level distillation plus cross-benchmark calibration**, not choosing a subset of whole benchmarks.

**Splits and metrics.** A 10% global test-model split is stratified on the grand average of the complete models' original scores. A further 10% local validation subset per benchmark is stratified on that benchmark's score; the main text does not make the denominator of this second 10% completely explicit. Item/model parameters and GAMs are described as fitted on training data, and selection/hyperparameters on validation. Reported test metrics are RMSE on normalized 0–100 scores and Spearman rank correlation. It compares against 10,000 random item subsets of matching size. The ordering of all initial preprocessing relative to holdout creation is **not established by the accessed main text**; it should be audited before reproduction.

**Final budget/results (Table 2).**

| Benchmark | Selected items | Marginal-model RMSE, points | Joint-model RMSE, points |
|---|---:|---:|---:|
| ARC | 145 | 1.303 | 1.166 |
| GSM8K | 237 | 1.778 | 1.555 |
| HellaSwag | 93 | 1.542 | 0.999 |
| MMLU | 96 | 1.743 | 1.430 |
| TruthfulQA | 154 | 1.562 | 1.104 |
| WinoGrande | 133 | 1.656 | 1.195 |
| Combined | **858** | — | **0.582** for grand-average reconstruction |

The mean per-benchmark joint RMSE is approximately **1.24 points**. Grand-average reconstruction has Spearman `r = 0.998` (§2.5), which is different from the correlation of the latent common factor with the average score. The common factor explains 79.3% of estimated-ability variation. **Reporting discrepancy:** the abstract calls its approximately 0.94 correlation with total score Spearman; §2.5 explicitly calls the 0.938 value Pearson. Do not collapse these into one verified correlation type. Also, §2.3's prose says all correlations exceed 0.98, but Table 1 includes MMLU correlations below 0.98; use the table for numerical reporting.

**Uncertainty and limits.** §3.1 describes nonparametric confidence intervals based on local test RMSE for similar predictions. Their construction/nominal coverage was not verified from the unread appendix or code. A test set used to build such intervals must not simultaneously be called untouched final evaluation data. Model-family/submitter dependence can distort IRT fitting and make random-model splits optimistic. Temporal validation is proposed as future work, not a demonstrated main protocol. Contamination cannot be determined from the response histories. Two disjoint sets and answer-choice permutations mitigate, but do not eliminate, memorization; evidence is a small three-model fine-tuning study.

**Code/data links:** https://www.github.com/adkipnis/metabench ; https://www.huggingface.co/datasets/HCAI/metabench . Main text describes lm-evaluation-harness integration, `reconstruct.R`, pretrained GAM/IRT models, and separately hosted data. None of those destinations were opened.

### [4] Observational Scaling Laws and the Predictability of Language Model Performance

**Evidence anchors:** §§3.1–3.4, 4, 4.1–4.3, 5, 7. Short anchor: “top 3 PCs explaining” approximately 97% of variance.

**Method/input distinction.** PCA maps a model's **observed standard benchmark scores** into low-dimensional capabilities. A sigmoid of a fitted linear combination predicts downstream normalized error/accuracy. Within a model family, capabilities are approximately linear in log training FLOPs; across families, measured capabilities put models on a common scale. The plots' Llama-2-equivalent FLOPs are a fitted capability-equivalence transformation, **not the actual training compute of every model**. Central downstream predictions require standard benchmark measurements of the target model; they are not automatically forecasts from a parameter/token budget for an untrained model.

**Data.** The base-model analysis uses 77 models from 21 families and eight benchmarks: MMLU, ARC-C, HellaSwag, WinoGrande, GSM8K, HumanEval, TruthfulQA, XWinograd. Approximately 97% of variation is explained by three PCs, with nearly 80% by the first. Missing benchmark entries are below 1% and handled with PCA imputation. A separate instruction-tuned/proprietary-model analysis supports agent experiments. The revision reports an additional 20 newly released models for checking preregistered predictions.

**Protocol.** Default weak/strong split uses training FLOPs at or below Llama-2-7B, `8.4 x 10^22`: 47 train models, 30 held-out models. Preprocessing, including imputation, is fitted on training data only. The primary metric is **held-out MSE on [0,1] targets**. Three PCs are used. The downstream link includes a fitted sigmoid amplitude constrained to [0.8,1.0].

- Arithmetic emergence tasks use one quarter of the default FLOPs cutoff and exclude GSM8K from predictor benchmarks to avoid an almost trivial overlap.
- AgentBench/AgentBoard hold out the top-performing 10% of models on each target benchmark; the default FLOPs cutoff is inapplicable to proprietary models. Standard benchmark scores are still inputs for those held-out target models.
- CoT/SC experiments on GSM8K exclude GSM8K from base predictors. CoT uses eight reasoning exemplars; SC samples five reasoning paths at temperature 0.7.
- Baselines include training FLOPs and model size. Main plots qualitatively support the capability-based predictor and updated future-model checks; numerical plot MSEs were **not extracted or invented**.

**Important selection distinction.** §5 minimizes a V-optimal design criterion over **model/family subsets**. Search includes/excludes complete model families to reduce the models requiring expensive downstream tests. Twelve selected models can preserve the illustrated post-training scaling trends relative to the 47-model fitting set. This does not select benchmark tasks or evaluation items.

**Limits.** The authors explicitly distinguish post-training observational analysis from ordinary pretraining resource optimization. Benchmark contamination and heterogeneous recipes within a nominal family are not modeled. Explained variance is not held-out prediction accuracy or a task-selection guarantee. No formal calibrated predictive coverage was verified.

**Code/data link verified in the allowed main HTML:** https://github.com/ryoungj/ObsScaling . Not opened.

### [5] Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families

**Evidence anchors:** §§2.1, 3.1–3.3, 4.1–4.6, 5. Short anchor: “only the smallest model of the test family”.

**Method and distinction from [4].** Sloth predicts latent skills from parameter count `s`, training-token count `t`, and family `f`:

`theta_fk(s,t) = alpha_fk + beta_k^T [log(s), log(t), log(s)log(t)]`.

Shared benchmark loadings map skills to benchmark predictors, followed by chance-adjusted links. Family-specific intercepts encode efficiency, while resource slopes are shared across families. Links may be fixed sigmoids (“basic”) or learned monotone neural networks. Thus it can predict **larger/hypothetical model scores without measuring that large model's base benchmark scores**, but normally requires benchmark observations of at least one smaller model of its family. This is not zero-shot prediction for an entirely uncalibrated family and not a task selector.

**Fitting and data.** Huber loss with delta 0.01, Adam with decaying learning rate; learned increasing links use nonnegative network weights. Fitting is nonconvex. The dataset spans 30 families: 28 represented on leaderboard v1, 17 on v2, 15 in their intersection. The 12 benchmarks are GSM8K, MATH level 5, MMLU, MMLU-PRO, BBH, GPQA, MuSR, TruthfulQA, HellaSwag, WinoGrande, ARC, and IFEval.

**Evaluation protocol.** Family-wise leave-one-out-style evaluation retains either the smallest or the two smallest target-family models for calibration and predicts larger ones. Base/instruct variants have distinct intercepts, but the corresponding sibling base/instruct family is excluded when testing the other. Additional controls avoid testing an older family version with a newer version in training. Main metric: MAE in percentage points, averaged across families after within-family errors; appendix MAPE analyses were not read. This protocol is **few-shot family calibration**, not a pure unseen-family holdout.

Baselines include pooled-intercept FLOPs, family-intercept/shared-slope FLOPs, PCA + FLOPs, and a full-dimensional size/token model. The accessible main text/figure captions support competitive or lower errors than the full-dimensional variant, but provide no safely transcribed universal numerical MAE improvement. Do not claim one.

**Calibration/interpretability caveats.** Basic links use multiple-choice chance floors, zero where appropriate, and a TruthfulQA floor based on the first percentile of the full leaderboard's scores. Because “full” is stated in the main text, a leakage-free implementation must explicitly decide whether to recompute that floor within training folds. The three skill labels are subjective post-rotation interpretations, not directly observed ground truth. Identification claims are restricted to the fixed-link/fixed-floor version, not established for every learned-link variant.

**Additional verified application.** §4.5 fits question-wise logistic regressions for MATH using skills of seven training models out of ten, holding out the largest models from three families. It predicts pass@k using the average of `1 - (1-p_i)^k`. This concerns repeated-sampling success probabilities, not arbitrary inference algorithms; plots were not numerically digitized. Main conclusion warns that learned links have no guarantee when extrapolating far outside training support and that target-family observations are usually still needed.

**Code link:** https://github.com/felipemaiapolo/sloth . Not opened; claimed quick laptop fitting was not independently timed.

## 4. Recommended next experiments — planning only

1. **Choose the actual prediction unit first.** For an embedding-benchmark project, specify whether the budget buys individual examples, complete datasets, or model evaluations. Do not label item distillation or model-family design a whole-task-selection baseline. The allowed reading supports motivation from correlations, not a literature-backed novelty claim for whole-task selection.
2. **Establish simple matched-budget baselines.** For item selection: stratified random, historical-correctness anchors, IRT anchors, and raw versus IRT/calibrated estimators [2–3]. For a separately defined whole-task experiment: random whole-task selection and a train-only mean/ridge predictor are proposed controls here, **not methods attributed to these papers**. Charge actual evaluation cost rather than assuming all tasks/items have equal cost.
3. **Hold out models rigorously.** Use random, family/base-model-grouped, temporal, and specialized-model tests. Perform every data-dependent filtering, PCA/imputation, IRT fit, task/item selection, link calibration, and hyperparameter search using training/validation data only. Keep a separate calibration set if constructing intervals, then measure interval coverage on untouched test models.
4. **Match metrics and aggregation.** Preserve each MTEB task's evaluator and original dataset weighting [1]. Report full-score MAE/RMSE, per-task residuals, Spearman/Kendall rank preservation, top-model reversals, worst-case/tail error, and wall time/token/GPU cost. These additional proposed metrics are planning recommendations, not all reported metrics in every source.
5. **Separate prediction regimes.** Evaluate observed-score downstream prediction [4] separately from resource-based larger-model prediction with one/two family calibration points [5]. A predictor given the target's observed benchmark scores has more information than one given only size/tokens; do not compare the two as if their test-time inputs were identical.
6. **Test robustness rather than assuming correlation transfers.** Freeze software/dataset versions; investigate contamination, near-clone models, multilingual shifts, saturating tasks, and specialized models [1–5]. Rerun the full benchmark on a small audit sample to detect systematic errors masked by aggregate score reconstruction.

## 5. Sources and local evidence

Only these five research sources support the literature claims:

[1] **MTEB: Massive Text Embedding Benchmark** — https://arxiv.org/abs/2210.07316 ; actual versioned HTML https://arxiv.org/html/2210.07316v3 .

[2] **tinyBenchmarks: evaluating LLMs with fewer examples** — https://arxiv.org/abs/2402.14992 ; actual versioned HTML https://arxiv.org/html/2402.14992v2 .

[3] **metabench: A Sparse Benchmark of Reasoning and Knowledge in Large Language Models** — https://arxiv.org/abs/2407.12844 ; actual versioned HTML https://arxiv.org/html/2407.12844v2 .

[4] **Observational Scaling Laws and the Predictability of Language Model Performance** — https://arxiv.org/abs/2405.10938 ; actual versioned HTML https://arxiv.org/html/2405.10938v3 .

[5] **Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families** — https://arxiv.org/abs/2412.06540 ; actual versioned HTML https://arxiv.org/html/2412.06540v5 .

Local audit material is under `/work/artifacts/sources/`: `paper_access.json`, `<id>.main.txt` (bibliography-truncated text), `<id>.main.reading.txt` (additional related-work omission), omission JSONs, resource-link JSONs, and `mteb_table1_compact.txt`. These are working evidence extracts, not complete faithful reproductions of the papers. Mathematical HTML extraction duplicates some rendered/TeX notation; equations above were manually normalized from visible expressions. Template-only evidence is documented separately in `/work/artifacts/template_provenance.md`.
