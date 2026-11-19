# Grounded reference query plan

**Status:** ready. Planning only: no references retrieved, no external pages accessed, and no bibliography or provenance file created.

## Central topic

Finite-budget repeat-run reliability of grouped interventional Kernel SHAP for fixed tabular classifiers, distinguishing attribution agreement from reference fidelity and comparing four short explanations with one longer explanation.

## Grounding and limits

- Authoritative scope: `paper_data.json` (`downstream_study`, `final_evaluation`, and episode cells); copied sources under `source_evidence/downstream/`; evaluator definitions in `task/evaluate_final.py`; dataset source manifest in `task/resources/final/manifest.json`. Recent global memory was not used as empirical evidence.
- The selected stratified/complementary sampler has the strongest reported search reference fidelity among the three candidates, but the search outcome is `completed_no_winner`, the selection is `non_winner_candidate`, and all combined search scores tie. Conditioning and interaction-alias portfolios are search-stage alternatives, not final deployed improvements.
- Final artifacts report six repetitions at coalition budgets 64 and 256, backgrounds of 8 and 32, and two evaluation seeds. Replay is a reproducibility check, not an extra independent replicate. Original columns remain players before one-hot encoding; logistic regression, random forest, and gradient boosting are model-family comparisons, not architecture transitions.
- Final reported `repeat_agreement` is 0.9458719135802469, `reference_fidelity` is 0.9289530659189914, and `local_accuracy_quality` is 0.9999999999999954. These distinct metrics motivate literature on agreement, discrepancy, and efficiency without claiming that one certifies another.
- Final reported `matched_budget_gain` is -0.03883354541895445. The evaluator defines this as reference similarity of the mean of four 64-coalition candidate runs minus similarity of one 256-coalition candidate run. It is not a candidate-versus-baseline comparison; do not infer a universal averaging penalty or a causal explanation.
- ACS has exact enumeration of its 1,024 coalitions. German Credit uses two independently seeded package references with nominal budget 2,048; these are approximate, not ground truth. Background size and feature count change both the game/reference context and work required; dataset differences cannot isolate a dimensionality effect.
- Episode evidence explicitly labels candidate diagnostics `unverified`. The numbers above are reported artifact values, not newly independently validated estimates; metric formulas were checked against evaluator source, but this stage did not rerun experiments. Search and sealed final scopes must not be pooled.
- `figures/` is empty. Neither `references.bib` nor `references_provenance.json` exists, so there are no prior retrieval queries to recycle or correct. The starter titles below are retrieval targets supplied in the task, not claims that their full texts were read during this stage.

## Core methods

- Shapley-kernel coalition sampling with endpoint-constrained least-squares attribution on the positive-class probability scale
- Randomized size stratification, complementary coalition pairing with rank headroom, and finite-population coverage within complement strata
- Exploratory outcome-blind eight-design portfolios selected by contrast rank and inverse-spectrum conditioning or pairwise/three-way interaction alias energy; search-stage alternatives only
- Exact coalition-enumeration Shapley references for ten-feature ACSIncome and two independently seeded high-budget KernelExplainer references for twenty-feature German Credit
- Top-three absolute-attribution overlap, rank and sign agreement, normalized L1 reference discrepancy, local-accuracy residuals, and explained-input-cluster bootstrap intervals
- Equal-coalition-budget comparison of averaging four 64-coalition explanations against one 256-coalition explanation

## Expected comparator literature

- Independent Shapley-kernel size/subset sampling with the same endpoint-constrained regression, as implemented by the copied baseline
- Package KernelExplainer at deployment budgets and at higher reference budgets; not interchangeable with the copied independent-sampling baseline
- Stratified and antithetic Monte Carlo Shapley estimation as the methodological comparator for complementary coalition sampling
- Leverage-score Shapley estimation and finite-sample accuracy guarantees as literature comparators, not implemented baselines
- Chance-corrected feature-selection stability as a conceptual comparator for raw top-three overlap, not a metric implemented in the run
- Interventional versus conditional Shapley estimands and background-size sensitivity as semantic context, not experimentally compared estimands

## Benchmark context

- UCI Statlog (German Credit Data), twenty original feature groups; logistic regression, random forest, and gradient boosting
- folktables ACSIncome from California 2024 one-year ACS PUMS, ten original feature groups; logistic regression, random forest, and gradient boosting
- Synthetic constant, copied-feature and feature-permutation controls; validation controls rather than additional public benchmarks

## Architectural shifts

None supported (`architectural_shifts: []`). Fixed original-feature grouping and fitted preprocessing define the representation; no representation ablation, neural architecture transition, or transfer study is evidenced.

## Result-driven themes

- Near-exact efficiency does not certify attribution fidelity: final reported local_accuracy_quality is approximately one while reference_fidelity is below one.
- Repeat agreement and reference fidelity measure different properties; avoid treating top-three agreement as an accuracy or causal-validity certificate.
- Final reported matched_budget_gain is negative for four short runs averaged minus one longer run; this is not a candidate-versus-baseline improvement metric and is not evidence of universal averaging failure.
- ACS supports exhaustive finite-background game references, whereas German Credit uses approximate references whose disagreement limits reference resolution.
- Reported behavior varies across dataset/model/background/budget cells; the design does not isolate a causal model-family or dimensionality effect.
- No qualifying search winner or demonstrated architecture transition; candidate diagnostics are labeled unverified, and search and final evaluation scopes must remain separate.

## Queries

Nine nonduplicate queries; no architecture query is warranted. Seven target explicitly permitted starter works or the named dataset record; two target grounded estimator-method neighborhoods.

### 1. core_method

Query: `"A Unified Approach to Interpreting Model Predictions" Lundberg Lee`

Allowed starter source for additive SHAP, the Shapley kernel, and endpoint efficiency. Copied candidate and baseline sources both retain constrained sampled regression; efficiency must not be presented as proof of reference fidelity.

### 2. core_method

Query: `Shapley value estimation stratified sampling antithetic sampling`

The selected source stratifies coalition sizes, pairs complementary subsets with rank headroom, and covers complement strata before reuse. Search the specific variance-reduction families, without asserting unbiased regression coefficients or measured superiority.

### 3. baseline_comparator

Query: `"Provably Accurate Shapley Value Estimation via Leverage Score Sampling" Musco Witter`

Allowed starter comparator for regression-based Shapley estimation under limited samples and accuracy guarantees. It contextualizes the fixed-budget design and outcome-blind portfolios, but was not executed and supplies no guarantee for this candidate.

### 4. core_method

Query: `"True to the Model or True to the Data?" Chen Janizek Lundberg Lee`

Allowed starter source for distinguishing interventional and conditional value functions. The evaluator fixes background-averaged interventional games, masks original columns before fitted encoding, and does not estimate causal effects or test conditional SHAP.

### 5. result_driven_theme

Query: `"On the Stability of Feature Selection Algorithms" Nogueira Sechidis Brown`

Allowed starter source to interpret chance-sensitive overlap of selected feature sets. The evaluator measures raw top-three absolute-attribution overlap, supplemented by rank/sign agreement and reference discrepancy; it does not implement the cited adjusted stability measure.

### 6. result_driven_theme

Query: `"An empirical study of the effect of background data size on the stability of SHapley Additive exPlanations" Yuan`

Allowed starter study for the background-size axis actually present in the run: backgrounds of eight and thirty-two rows, fixed within repetitions. Its deep-learning setting is related-work context only; this run contains no neural model or evidence of neural-to-tree transfer.

### 7. result_driven_theme

Query: `Shapley value estimation Monte Carlo error confidence intervals`

Targets uncertainty in sampled Shapley estimates and approximate references: German Credit uses two high-budget references, ACS has exhaustive anchors, and the evaluator bootstraps explained-input clusters. Also contextualizes four-short-versus-one-long budget allocation without equating reference agreement with a formal error bound.

### 8. benchmark_context

Query: `"Retiring Adult: New Datasets for Fair Machine Learning" Ding Hardt Miller Schmidt`

Allowed starter source for folktables ACSIncome. The final data manifest identifies California 2024 one-year PUMS and ten original features; the benchmark citation does not imply a fairness experiment, cross-state transfer, or a citation-specific data vintage.

### 9. benchmark_context

Query: `"Statlog (German Credit Data)" "10.24432/C5NC77"`

Pins the actual UCI credit dataset rather than generic credit-risk literature. Its twenty original feature groups motivate reporting approximate, independently seeded references separately from the ten-feature exhaustive ACS game.

## Retrieval safeguards and rejected alternatives

Do not execute retrieval in this stage. At the later retrieval stage, prefer exact-title/identifier lookup of the explicitly allowed starter works and the UCI record. The two exploratory method queries require a safe-source gate before opening results; if safe eligibility cannot be established, skip them rather than broaden retrieval. Do not follow references, citations, recommendations, or discussion pages to discover the prohibited study. On accidental exposure, stop immediately and record what appeared, where, and how much was read in the reproduction log. The prohibited work remains unidentified; this plan does not attempt to guess it.

- Any attempt to infer, identify, retrieve, access, or use the prohibited prior paper, its title, authors, results, mirrors, preprints, abstract pages, proceedings/review pages, slides, posters, videos, blogs, or code.
- Citation-graph expansion, cited-by/related-paper recommendations, reviews, notes, aggregators, social discussions, or reproductions that cite or discuss the prohibited work; do not use starter papers as snowballing entry points.
- Broad searches phrased as the task itself, such as SHAP repeated-run reliability tabular models or single-run SHAP reliability, which risk identifying the prohibited study.
- Unrestricted exploratory retrieval for the two method-level queries without a safe-source gate; if potentially prohibited content appears, stop reading immediately and record the location, content encountered, and extent read.
- FT-Transformer, ResNet, deep tabular architecture transitions, neural-to-tree transfer, TreeSHAP speedups, or cross-architecture superiority claims: none is tested here. The named Yuan study is permitted context, not evidence of a neural experiment.
- Pima, Give Me Some Credit, Arrhythmia, or other unexecuted dataset benchmarks; ACS interstate/year transfer or fairness-performance studies not present in the run.
- Generic optimization, generic benchmarking, scientific method, paper writing, campaign chronology, milestone searches, or positive-result searches premised on a winning sampler.
- Predictive multiplicity across retrained models, causal SHAP validation, adaptive stopping certificates, conditional SHAP experiments, or implemented leverage-score baselines not supported by these artifacts.

These queries are preferable to generic optimization or benchmarking searches because each attaches to an implemented estimator component, an actual metric/reference limitation, or a dataset provenance requirement. Broad explanation-disagreement and predictive-multiplicity searches are omitted: this run repeats one estimator on each fixed model rather than comparing unrelated explainers or equally accurate retrained models. Rank-biased-overlap retrieval is omitted because the implemented rank score is not that measure. Dedicated architecture and portfolio-optimization queries would overemphasize unsupported transitions or non-winning search alternatives.

**Failure reason:** none; the estimator, benchmark, comparator, and uncertainty neighborhoods are coherent despite limited diagnostic trust and no winning improvement.
