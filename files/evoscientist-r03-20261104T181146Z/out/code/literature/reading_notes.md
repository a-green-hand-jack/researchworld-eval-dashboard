# Reading notes: five permitted papers

References [1]–[8] and verified metadata are in `sources.md`. All empirical numbers below are **paper-reported**, not reproduced. Page references are physical PDF pages. No bibliographies, post-bibliography appendices, external repositories or dataset sites were read. Automatically extracted body text contains additional unread sections; extraction alone is not claimed as reading. No novelty/completeness claim about the wider literature is possible under the source restriction.

## [1] MTEB — task diversity is essential

**Actually inspected:** p.1 title/authors/abstract; pp.3–5 task definitions, dataset structure, Table 1 and evaluation-split statement; pp.7–9 analysis, efficiency, multilinguality and conclusion; p.10 only pre-bibliography acknowledgments. Did not read pp.2,6 or appendices. No separate limitations section was encountered in these inspected pages.

**Evidence anchor:** “No model claims the state-of-the-art in all seven English tasks.” (p.7).

### Method, data and baselines

The paper introduces 58 datasets across 8 task types and 112 languages, benchmarking 33 embedding models (abstract). The English Table 1 summarizes **56 datasets across seven task columns**, not all 58 datasets/all eight types. Bitext mining adds a distinct multilingual task. Do not conflate the English table with the whole benchmark or assume these historical counts describe the current leaderboard.

Model families inspected include GloVe/BERT/SimCSE, MPNet/MiniLM, LaBSE/LASER2, SGPT, GTR, ST5, and the historical OpenAI Ada endpoint. There is no universal task winner: retrieval-oriented and similarity-oriented embeddings differ substantially. MPNet/MiniLM are useful historical speed/performance baselines, not a claim about today's strongest models.

### Evaluation protocol

- Evaluate dataset **test splits**, except **MSMARCO dev** (p.5).
- Bitext mining: cosine nearest matches; main metric **F1**.
- Classification: embed train/test; logistic regression with maximum 100 iterations; **accuracy**.
- Clustering: mini-batch k-means, batch size 32, number of clusters equals number of labels; **v-measure**.
- Pair classification: multiple distance/threshold diagnostics; main metric **cosine average precision**, which is not a fixed-threshold accuracy.
- Reranking: cosine ranking; **MAP**.
- Retrieval: cosine retrieval; **nDCG@10**.
- STS and summarization: **Spearman correlation using cosine similarity**; for summaries, use the closest human-reference summary embedding.
- Efficiency plot caption: STS15, one NVIDIA A100 80GB, CUDA 11.6 (p.7). No new timing was performed here.

### Failure modes and planning implications

The authors explicitly do not control model-training overlap in the MTEB scores and discuss possible SciDocsRR overlap (p.8). Their belief that averaging many datasets reduces this problem should not be treated as a demonstrated contamination correction. Shared corpora and similar dataset variants also make datasets dependent (p.5). Long inputs may be truncated by the model; MTEB itself imposes no input-length limit. Language coverage matters: models perform poorly on unseen pretraining languages.

**Actionable implication:** retain task/language/domain breakdowns and each task's native metric. Freeze dataset revision, split, prompts/pooling, truncation and software version. Do not treat a single STS score or a mixed-metric average as evidence of broad embedding quality. These are planning recommendations, not additional experiments in the paper.

**Availability reported in PDF, not visited:** https://github.com/embeddings-benchmark/mteb (p.1). Current code, datasets, licensing and compatibility were not verified.

## [2] tinyBenchmarks — combine representative items and IRT correction

**Actually inspected:** p.1 title/authors/abstract and availability footnote; pp.3–9 Sections 3–6, evaluation protocol, results, extensions and explicit limitations. Did not read p.2, bibliography, proofs or appendices.

**Evidence anchor:** “We consider two train-test model split scenarios” (p.6).

### Method and baselines

Learn from an item-by-model correctness matrix of previously fully evaluated LLMs. Compare stratified random selection, k-means in correctness space, and k-means in **multidimensional two-parameter IRT item-parameter space**. Cluster-nearest anchor items receive weights proportional to cluster size. IRT item parameters include discrimination/loading and difficulty; fit the new LLM's ability from its observed responses.

The p-IRT estimator combines observed responses with IRT predictions on unobserved items. The **gp-IRT** estimator mixes the weighted subset estimate and p-IRT to balance sampling variance against IRT bias; this is the “++” variant. Its mixture weight is estimated using training-model splits and a bias/variance heuristic, not tuned on final test-model full scores. Six strategies cross the three selection methods with vanilla/++ estimation. IRT is fit using variational inference; latent dimension is selected inside training data from {2,5,10,15} (p.6). Nonbinary scores in [0,1] are thresholded using a scenario-specific training-data rule to approximately preserve average correctness (pp.5–6).

### Data, splits and metrics

- Open LLM Leaderboard: six scenarios, about 29K items; 395 LLMs, **75/25 model split**, either random or chronological.
- MMLU: about 14K items, 57 subjects; same 395 LLMs/splits. Respect the paper's subscenario weighting rather than assuming item micro-average.
- HELM Lite v1.0.0: 10 core scenarios, about 10K items, 30 fully evaluated LLMs. Random split uses **11-fold CV**; the challenging alternative holds out organizations because model dates are unavailable. Aggregate benchmark metric is **mean win rate**, not plain accuracy.
- AlpacaEval 2.0: 805 prompts, 100 LLMs; **4-fold random CV**, or most recent 25% held out. Continuous preferences are used in the experiments (p.7 footnote).
- Results averaged over **five restarts**. Evaluate estimated full-benchmark/scenario scores against actual full evaluation, primarily absolute score-estimation error; the inspected text points to rank correlations in an unread appendix.

The reported headline is approximately **2 percentage points average score-estimation error** using **100 examples per scenario**, not a universal per-model error guarantee. Budgets are 100 MMLU items, 600 across the six leaderboard scenarios, 1000 HELM items, and 100 AlpacaEval prompts (p.7). Do not call all four settings “100 total examples.”

### Limitations and calibration

Correctness-space anchors deteriorate on 40 specialized MMLU models; IRT anchors are less affected in the reported test (p.8). Severe changes in easy/hard response patterns, architecture, pretraining data or capabilities can still break IRT extrapolation. Authors recommend periodically updating anchors and IRT parameters (p.9). The adaptive-testing extension improves estimates but their implementation takes over five minutes, unlike the seconds-scale fixed-anchor correction.

The mixture correction is not a validated coverage guarantee. No calibrated predictive-interval protocol was established in the sections read. The reported average 2-point error must not be used as a 95% confidence interval or a worst-case bound.

**Availability reported, not visited:** https://github.com/felipemaiapolo/tinyBenchmarks ; datasets at `huggingface.co/tinyBenchmarks` (p.1).

## [3] metabench — information filtering plus cross-benchmark reconstruction

**Actually inspected:** p.1 title/authors/abstract; p.2 availability and figure description (plus surrounding text); pp.4–10 Sections 2–4.2, Tables 1–3 and limitations; p.11 only pre-bibliography ethics/reproducibility text. Did not read p.3 or appendices.

**Evidence anchor:** “used it to create a stratified 10% split as the global test set.” (p.5).

### Method and data

Six Open LLM Leaderboard benchmarks: ARC, GSM8K, HellaSwag, MMLU, TruthfulQA, WinoGrande; original combined size **28,632 items**. After excluding flagged/merged models, data contain **6,875 LLMs from 1,355 users** and over 152M responses; **5,055** models have all six benchmarks. Per-benchmark analyses use all available models when possible.

Preprocessing removes the lowest 0.1% scoring subjects per benchmark, items with SD below 1%, mean accuracy above 95%, and near-zero item/total-score point-biserial correlation. Then: (1) repeated random subsets with **GAM score calibration**, (2) preselect 350 items per benchmark, (3) fit unidimensional 2PL/3PL/4PL IRT and infer ability via MAP/EAPsum, (4) select high-Fisher-information items across ability quantiles, (5) reconstruct original scores with GAMs. Selection hyperparameters are optimized on validation data, including a size penalty. The joint model uses information across **all six** reduced benchmarks, not just a single 96-question MMLU subset.

### Splits, calibration and results

Global test set: stratified **10% of models**, using grand-average scores among models with all six benchmarks. Each benchmark also has a local validation subset described as a “further 10% subset” stratified by its own score; the inspected text does not unambiguously specify that percentage's denominator. Fit IRT/GAM on training models and select on validation, not test RMSE. Random-subset comparator uses **10,000 draws** with matching budgets and GAM calibration.

Final sizes from Table 2: ARC 145; GSM8K 237; HellaSwag 93; MMLU 96; TruthfulQA 154; WinoGrande 133 — **858 total**, just under 3% of the original item pool. Scores are on a **0–100 scale**. Joint reconstruction reports **1.24 percentage points mean per-benchmark RMSE**, **0.582 points overall-average RMSE**, and overall-score Spearman **0.998** (p.8). These numbers are not directly comparable to tinyBenchmarks' absolute-error headline without aligning losses, cohorts, splits and budgets. The lower 0.582 overall error also benefits from aggregation.

The repository's `reconstruct.R` is described as producing nonparametric confidence intervals using local test RMSE for similar predictions (p.9). This is not independently verified coverage under time/family shift, and it uses a reference error set described as a test set. For a new evaluation, reserve a distinct calibration split before final testing. Also note an internal reporting inconsistency: prose on p.6 says all Table 1 correlations exceed 0.98, but MMLU entries in the displayed table are approximately 0.961–0.967. Do not repeat the stronger blanket claim.

### Limitations and safeguards

Two disjoint forms plus answer-choice permutations aim to reduce repeated-evaluation overadaptation; GSM8K has no choice permutation. A three-model LoRA fine-tuning experiment supports partial mitigation, not proof of contamination immunity (p.9). Authors cannot check contamination for all source models. Shared base models, users and fine-tuning data violate subject-independence assumptions and may distort IRT parameters (p.10). Random score-stratified model splits alone do not demonstrate unseen-family or future-model robustness. Preprocessing scope relative to held-out models also deserves auditing before reproduction; the inspected narrative does not fully resolve whether all filtering statistics were training-only.

**Availability reported, not visited:** https://github.com/adkipnis/metabench ; https://huggingface.co/datasets/HCAI/metabench (p.2). Paper reports R 4.4.0, `mgcv`, `mirt`, `caret`, and integration into `lm-evaluation-harness`.

## [4] Observational scaling — predict from measured capabilities, not FLOPs alone

**Actually inspected:** p.1 title/authors/abstract; pp.4–13 Sections 3–7, protocol, results prose and readable table/captions; p.14 only pre-bibliography limitations/changelog. Did not read pp.2–3, bibliography or appendices. No visual inspection of plots or numerical extraction from their curves.

**Evidence anchor:** “all preprocessing steps ... were fitted on the train set only” (p.7; ellipsis omits the parenthetical example).

### Method, data and baselines

Extract PCA capabilities from standard benchmark scores, then fit a scaled sigmoid of a linear combination of capability coordinates to a downstream target. Model families have different compute-to-capability efficiencies. **Target-model benchmark measurements are needed** to place that model in capability space; this is not pure prediction from a proposed model's parameter/token budget.

Base-model analysis: **77 models, 21 families**, with eight metrics (MMLU, ARC-C, HellaSwag, Winogrande, GSM8K, HumanEval, TruthfulQA, XWinograd). Under 1% missing data are PCA-imputed. The top **3 PCs explain about 97%** of variance in this cohort; PC1 nearly 80%. Those directions are interpreted as general, reasoning and programming capabilities. This is cohort-dependent empirical structure, not a universal dimensionality theorem. Training FLOPs are approximated by **6ND** where information is available; within-family PC1/log-FLOPs fits report R² > 0.9 (p.6).

Baselines use training FLOPs or parameter count. AgentBench/AgentBoard use instruction-tuned and proprietary models with seven measured base metrics (without XWinograd in the listed set). AgentBench target is its weighted overall score; AgentBoard uses average success rate.

### Holdouts and evaluation

Default weak-to-strong split: training FLOPs at most **Llama-2-7B's 8.4e22**, yielding **47 train / 30 test** base models (pp.7–8). Preprocessing, including imputation, is fitted on training models only. The main metric is held-out **MSE on [0,1]-normalized targets**. For arithmetic tasks, cutoff is quartered and GSM8K is removed from the capability features. Agent tasks hold out the **top 10% performers**. The paper also reports 20 future-model tests collected by September 1, 2024, following initial prediction preregistration; this is reported, not independently audited here.

For CoT/SC GSM8K experiments, exclude GSM8K from input metrics. CoT uses eight reasoning examples; SC samples five CoT paths at temperature 0.7. These details matter when comparing intervention curves.

For low-cost model selection, the paper minimizes a **V-optimality** prediction-variance criterion in capability space, searching over whole-family subsets rather than individual items. In the 47-model post-training setting, **12 selected models** reportedly retain scaling-trend accuracy and outperform random model selection (pp.11–12). No exact plot MSE is asserted here.

### Limitations

The authors limit the main applicability to post-training scaling analyses, not replacement of pretraining compute laws. Contamination, heterogeneous efficiencies within a nominal family, more intensive test-time computation and fine-tuning remain limitations. Missing training-data generation compute can distort apparent efficiency (Phi discussion). Capability correlations and regression weights are not causal intervention evidence. The inspected text does not establish calibrated predictive intervals or reliable far-out-of-distribution extrapolation.

**Availability reported, not visited:** https://github.com/ryoungj/ObsScaling (p.7), described as including implementation and collected data.

## [5] Sloth — forecast skills from size/tokens with family offsets

**Actually inspected:** p.1 title/authors/abstract/version stamp; pp.3–10 Sections 2–5, protocols, results descriptions and explicit limitations. Did not read p.2, proofs or appendices.

**Evidence anchor:** “only the smallest model of the test family is observed” (p.6).

### Method and prediction setting

Sloth jointly models benchmark logits as a low-dimensional loading matrix times latent skills. Each skill depends on **log(parameter count), log(training tokens), and their interaction**, with **family-specific intercepts** and shared skill slopes. A benchmark-specific fixed sigmoid or learned monotone neural link maps skills to scores, optionally with a lower asymptote. The principal distinction from [4] is that it can forecast a hypothetical larger model's skills from resource inputs, **provided the family is anchored by observed smaller models**.

Fit with **Huber loss δ=0.01**, Adam and learning-rate decay. Fitting is nonconvex; multiple initializations can help. Basic fixed-link models admit identifiability analysis up to transformations, whereas flexible-link models have weaker interpretability guarantees. Skill labels are subjective post-rotation interpretations, not directly observed cognitive faculties.

### Data, splits and baselines

Twelve benchmarks from Open LLM Leaderboard v1/v2: GSM8K, MATH level 5, MMLU, MMLU-PRO, BBH, GPQA, MuSR, TruthfulQA, HellaSwag, Winogrande, ARC, IFEval. Data cover **30 families** (28 on v1, 17 on v2, 15 in their intersection); **53** if base/instruction variants are counted separately (p.5).

The test protocol leaves out a family except for its **smallest observed model**, training on other families plus that calibration anchor and predicting larger members. Paired base/instruct counterpart families are excluded from training when the corresponding family is tested. A second setting observes the **two smallest** family members. Report **within-family MAE**, averaged across tested families, in percentage points. The paper also reports MAPE in an unread appendix.

Baselines: shared-intercept/slope FLOPs, family-intercept/shared-slope FLOPs, adapted PCA+FLOPs, and unconstrained “Size and Tokens” with identity loadings. With only one family anchor, a free family-specific slope cannot be estimated fairly. The paper reports competitive or lower errors than the unrestricted Size-and-Tokens variant; no exact error values are inferred from plots in these notes.

For basic models, lower asymptotes are set from choice counts (0 for non-choice benchmarks), except TruthfulQA uses a **first percentile from the full leaderboard** (p.6). This deserves a training-only sensitivity check in a strictly held-out protocol, rather than silently treating the published setup as leakage-free.

### Downstream and test-time extensions

The HumanEval/EQ-Bench example holds out Llama-3-70B base/instruct while fitting skills and downstream logistic regressions. The MATH test-time extension uses **7 observed models / 3 held-out largest models** across Llama-3-Instruct, Gemma and Pythia; per-item logistic correctness predictions yield mean **1−(1−p)^k** for pass@k. This assumes the repeated-sampling success model and is not a general result about majority voting or agent scaffolds.

### Limitations

Usually needs at least one model from the target family. Flexible learned links have **no extrapolation guarantee** for very different hypothetical models. Interpretability/identification results apply only to simpler fixed-link instances. The inspected sections do not establish predictive-interval calibration. A novel family with no anchor is a separate harder task; do not equate one-anchor extrapolation with zero-shot unseen-family generalization.

**Availability reported, not visited:** https://github.com/felipemaiapolo/sloth (p.1).

## Recommended next experiments (planning only; nothing implemented)

1. **Separate information regimes before comparing methods.** Distinguish item-response compression ([2],[3]), downstream prediction from measured target-model benchmark scores ([4]), and resource-based forecasting with one/two target-family anchors ([5]). Match available information and evaluation cost; these methods do not solve identical prediction problems. Use [1] as a heterogeneous embedding evaluation setting only if item-level response/metric assumptions can be justified; retrieval nDCG and clustering v-measure are not binary independent item correctness.
2. **Stress-test generalization using locked cohorts.** Include chronological holdout, grouped base-family/derivative holdout, and specialist models, alongside random-model splits. Prevent related checkpoints and base/instruct variants from straddling groups. Fit item filtering, clustering, PCA/imputation, IRT, lower asymptotes, link selection and hyperparameters using training/validation only. Document the permitted target-family anchor explicitly. Expected outcome: a more credible estimate of deployment error, potentially worse than random-split headlines.
3. **Run matched-budget baselines and ablations.** Compare stratified random items, correctness anchors, IRT anchors, vanilla versus gp-IRT, GAM-calibrated random subsets, and joint versus marginal reconstruction. Separately ablate PCA rank, family offsets, interaction term and fixed/learned links. Sweep item budgets and family-anchor counts. Count reference-matrix collection/training cost as well as target-model inference and calibration overhead. Expected outcome: identify which structure improves accuracy per unit cost instead of comparing headline reductions from different setups.
4. **Report errors, rankings and uncertainty separately.** Align score scales and benchmark weighting; report per-task MAE/RMSE, Spearman/Kendall, pairwise ranking error and high-quantile/worst-group error. Keep aggregate and per-benchmark errors separate. Use a distinct held-out calibration cohort for predictive intervals; measure 90%/95% coverage and interval width on final time/family-shifted tests. Use family-grouped resampling for uncertainty when models are related. Expected outcome: detect when good mean error hides subgroup failures or miscalibrated confidence.
5. **Audit overadaptation and contamination without new literature access.** Rotate disjoint item forms/choice ordering, compare frozen versus refreshed anchors as model cohorts evolve, and avoid reusing the final full-evaluation cohort for repeated tuning. Report that source-model pretraining contamination cannot be ruled out from leaderboard responses alone. No additional source visit is authorized by these suggestions.
