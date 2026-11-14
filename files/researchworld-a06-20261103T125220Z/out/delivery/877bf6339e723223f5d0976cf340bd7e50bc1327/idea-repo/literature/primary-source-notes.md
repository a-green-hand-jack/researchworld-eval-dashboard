# Permitted primary-source evidence and implications

Read on 2026-11-03. These are context notes, not results of this study. All five frozen inputs were read in full. The primary sources below were downloaded and consulted directly at the exact URLs and byte hashes in `provenance/primary-sources.json`. Reading was focused on the identified sections; this record does **not** claim a line-by-line audit of every appendix or independent verification of every proof. Numerical findings mentioned here are attributed prior results; they must not be mixed into this study's measured tables. The eleven starter works are permitted explicitly by `deliverable.md`. One additional classic paper was accessed directly by its known JMLR URL; no topical discovery search was used.

## 1. MMLU-Pro: benchmark and scoring conventions

**Read source:** Wang et al., *MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark*, arXiv:2406.01574v1 (3 June 2024). Main §§1–8, especially §3 construction, §4 scoring, §6 comparisons; pinned dataset card in full.

**Establishes:** MMLU-Pro merges/filter questions from MMLU and adds reasoning-oriented sources, expands distractors, and uses expert review. It covers 14 disciplines and 12,032 test questions. §4 uses 5-shot chain-of-thought (with stated model exceptions), generated answer extraction, and accuracy. §6 distinguishes benchmark difficulty, CoT versus direct answering, and sensitivity across 24 prompt styles. The reported reduction in spread across prompt styles is a benchmark robustness finding in those evaluated models; it is not a guarantee of unbiased reporting after choosing a prompt on the evaluated items.

**Scoring details that matter here:** The original §4 extractor first searches an `answer is ...` pattern, then an `Answer: ...` pattern, then randomly chooses an option if both fail. Its fallback must not silently become part of a deterministic new scoring rule. Counting unparseable answers as wrong is a possible explicit protocol change, not reproduction of the original scorer. Preserve the actual response and extracted option, invalid rate, truncation status, and the exact parser version. The original's percentage differences are accuracy percentage points when subtracting accuracies, not relative percent improvements.

**Pinned card:** `https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/raw/b189ec765aa7ed75c8acfea42df31fdae71f97be/README.md` declares MIT, 12,032 test and 70 validation examples, and fields `question_id`, `question`, `options`, `answer`, `answer_index`, `cot_content`, `category`, `src`. The card says items *typically* have ten options, with some reduced during review. The study must inspect loaded option counts rather than assume every item's chance rate is exactly 0.1. Test `cot_content`, `answer`, and `answer_index` are gold information; they must not enter the prompt construction or generation path for an audit item. Evaluation code of course needs labels for scoring after generation.

**Version caution:** The pinned card records corrections after the v1 paper (answers, categories, and leading option spaces). Its static per-category summary should be treated as documentation to check against the pinned loaded parquet, not an independently verified item audit. Its download-size metadata differs from the supplied approximate parquet size; report actual downloaded bytes. No leaderboard or discussion link in that card was followed.

**Implication/comparison:** Show accuracy and uncertainty for the realized model + decoding + prompt + parser combination. Report pooled question weighting versus macro-category weighting. Small or subject-restricted studies are allowed by the objective, but must say exactly which subset they study and cannot claim the full benchmark leaderboard score or all models' prompt sensitivity. CoT versus short direct output is a meaningful protocol difference, not a nuisance to hide.

## 2. DSPy: what optimization means

**Read source:** Khattab et al., *DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines*, arXiv:2310.03714v1 (5 October 2023). Main programming/compilation §§3–4 and evaluation §§5–8.

**Establishes:** DSPy separates signatures, parameterized modules, composed programs, and optimizers (“teleprompters” in this version). Compilation can generate demonstrations, select discrete instructions/demonstrations by random search or other hyperparameter optimization, and construct program-level changes such as ensembles. Candidate generation can use filtered successful traces; it is not merely selecting from templates that existed before data were seen. The compiler optimizes a user metric and generally uses training/validation data. The GSM8K case study distinguishes training, development, and official test; the HotPotQA study reserves official validation for final testing because the official test is hidden.

**Implication/comparison:** A prompt or pipeline is the evaluated system together with its compilation procedure. Do not call a manually frozen single-call bank a test of DSPy end-to-end compilation. The paper supplies motivation for automatic selection and a useful convention of explicit train/dev/test roles; it is not evidence that DSPy users necessarily report training performance as final performance. Attribute the risk to a specified reuse protocol, not to all optimizers.

## 3. MIPRO: generated candidates and feedback

**Read source:** Opsahl-Ong, Ryan, Purtell, Broman, Potts, Zaharia, and Khattab, *Optimizing Instructions and Demonstrations for Multi-Stage Language Model Programs*, arXiv:2406.11695v1 (17 June 2024). Main §§2–6 and limitations; Appendix B.1/B.2 data-split and budget description; Appendix H's stated failure mode.

**Establishes:** Optimizing a multi-stage program entails both proposing instructions/demonstrations and assigning credit from a downstream metric. MIPRO combines grounded proposal generation with a Tree-structured Parzen Estimator surrogate over instruction/demonstration combinations, minibatch evaluations, and periodic full evaluation to return a best configuration. Other variants adapt proposer hyperparameters using feedback. The paper evaluates six task/program combinations, with repeated optimizer runs and separated train/dev/test roles; Appendix B.1 explicitly says dev was used for internal iteration on methods and test for final reporting. Appendix H observes that instructions can overfit examples shown to the proposer.

**Implication/comparison:** A complete adaptive optimizer may reveal labels, individual examples, summaries, or aggregate scores to future proposals. A fixed-bank experiment isolates selection over a restricted family; it does not characterize arbitrary proposal adaptivity. The supplied objective permits a custom search and does not require implementing DSPy/MIPRO. Describe what is actually tested. The v1 main text and abstract make slightly different broad superiority phrasings, so avoid borrowing an unqualified “wins five of six” numerical claim; the table and statistical comparison must be read for any exact comparison.

## 4. PromptEval: distributions across prompts are a different target

**Read source:** Felipe Maia Polo et al., *Efficient multi-prompt evaluation of LLMs*, arXiv:2405.17202v1 (27 May 2024). Main §§1–7, especially §§2–4 model/estimands/assumptions and §§5–6 evaluation.

**Establishes:** The target is the distribution and quantiles of prompt performances on a specified prompt × example matrix under sparse observations. An extended performance-IRT estimator combines observed correctness with model-based predictions for unobserved entries, using prompt and item covariates. A two-way balanced sampling scheme distributes evaluation budget across prompts and items. The proposed logistic/Rasch-type correctness model is fitted by maximum likelihood. Consistency results require bounded covariates, enough unobserved items, correct specification, and consistent fitted parameters; they are not assumption-free guarantees.

**Prior evaluation conventions:** Compare the full estimated performance distribution by Wasserstein-1 distance and individual quantiles by absolute error, over evaluation budgets and sampling seeds. The paper also assesses best-prompt identification by regret and studies per-subject versus pooled prompt sensitivity. Those errors/quantiles are across prompts on the evaluation matrix. A 95th performance quantile is not a 95% confidence interval, and a max–min range is not an interval coverage guarantee.

**Implication/comparison:** This paper helps motivate cost-aware multi-prompt evaluation and the importance of paired prompt–item outcomes. It is not by itself a calibrated estimator or interval for the fresh-question performance of a prompt selected by reusing those questions. Its §7 explicitly distinguishes fixed candidates from dynamically evolving candidates. Implementing PromptEval is optional; if not implemented, cite it as related work and explain the different target rather than imply it was empirically defeated.

## 5. Best-arm identification: selecting well versus reporting honestly

**Read source:** Chengshuai Shi, Kun Yang, Jing Yang, and Cong Shen, *Best Arm Identification for Prompt Learning under a Limited Budget*, arXiv:2402.09723v1 (15 February 2024). Main §§1–5 and discussion. The supplied starter list gives a later title, *Efficient Prompt Optimization Through the Lens of Best Arm Identification*. The bibliography here uses the v1 title actually read, not unverified final-version text.

**Establishes:** A prompt's value is expected task score over new inputs and model-generation randomness. Candidate prompts are arms and evaluations are noisy pulls. TRIPLE adapts fixed-budget best-arm identification, with sequential halving/continuous rejection and embedding-based clustering/function approximation variants, to allocate evaluations efficiently. The study compares uniform evaluation and UCB and considers both fixed pools and integration into generation/selection pipelines.

**Prior conventions:** Hold total evaluation budget fixed when comparing allocation methods; report true-quality selection performance/regret or probability of finding a good arm, over repeated runs. Comparing search breadth at fixed questions per candidate increases total evaluations; comparing it at fixed total evaluations changes evaluations per candidate. These answer different questions and should have separate budget labels.

**Implication/comparison:** A better selection rule need not give an unbiased reused estimate of the selected arm, and a conservative reporting rule need not improve selected-arm utility. Keep selection regret separate from reporting bias and decision error. A fixed-bank search is an authentic restricted automatic search; it is not a substitute for claims about arbitrary adaptive candidate generation.

## 6. FormatSpread: a performance range is not statistical uncertainty

**Read source:** Sclar, Choi, Tsvetkov, and Suhr, *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting*, arXiv:2310.11324v1 (17 October 2023). Main §§1–7.

**Establishes:** Semantically equivalent prompt formats can yield materially different task accuracies and can change model comparisons. A manually defined grammar controls plausible formatting perturbations. FormatSpread samples formats and uses bandit allocation (Thompson sampling in the proposed method) to find high- and low-performing formats within a budget. The analysis fixes demonstrations/order to isolate formatting and uses both probability ranking and generated exact-prefix matching; paired McNemar tests are used for comparisons on shared items.

**Prior conventions:** The “performance interval” is explicitly `[min_i m(p_i,D), max_i m(p_i,D)]` over formats on a fixed task dataset. It describes format sensitivity, with spread defined as its width. It is not a frequentist confidence interval for the selected format's population accuracy. Figures compare spreads, model-pair reversals, atomic formatting changes, and budget against error in estimated spread. Outcome extraction/answer ranking can change measured sensitivity.

**Implication/comparison:** Distinguish genuine quality variation across configurations from sampling-driven optimism in choosing an empirical maximum. Never use the format range, across-run SD, or prompt-performance quantile as if it were a calibrated interval for a chosen deployed system.

## 7. Adaptive data analysis: a broader feedback problem

**Read source:** Dwork, Feldman, Hardt, Pitassi, Reingold, and Roth, *Preserving Statistical Validity in Adaptive Data Analysis*, arXiv:1411.2664v1. Abstract and §§1–2 problem/techniques, §1.2 result statements and the stated efficiency qualifications. The downloaded PDF has a 2014 arXiv stamp and a later typeset title-page date; hash identifies the consulted bytes.

**Establishes:** Reusing data adaptively to choose statistical queries breaks the usual fixed-query validity argument. Differentially private/stable interactions can yield generalization and valid estimates under specified sample/tolerance/composition conditions. Exponentially many adaptive queries are possible in some information-theoretic regimes, but efficient algorithms have distinct limits. The analyst's access must be mediated by the protected mechanism; freely revealing labels is not the same setting.

**Implication/comparison:** Do not claim a fixed-bank multiplicity correction handles arbitrary feedback-based candidate generation. Conversely, adaptive data reuse is not automatically invalid: the mechanism and accessible information determine what can be guaranteed. This source gives broader context, not an implemented baseline unless the study actually builds and tests a specific mechanism. Avoid “DP solves all reuse for free.”

## 8. Ladder: controlled release of feedback

**Read source:** Blum and Hardt, *The Ladder: A Reliable Leaderboard for Machine Learning Competitions*, arXiv:1502.04585v1 (16 February 2015). §§1–3 definitions/algorithm/bounds, §4 practical mechanism, §§5–6 experimental descriptions.

**Establishes:** In an adaptive leaderboard, only sufficiently improved and rounded empirical scores are released, otherwise the previous best reported value is retained. Leaderboard error concerns tracking the minimum population loss among submissions so far, rather than accurately reporting every submitted classifier. §2 contrasts independent fixed functions (Hoeffding + union bound) with functions chosen from prior feedback. §3 gives a theoretical Ladder mechanism with a step size. The paper also proposes a practical parameter-free variant and studies adversarial attacks and real competition submissions. §4.1 explicitly calls the repeated significance-test guide heuristic under adaptivity; do not transfer the theoretical step-size guarantee automatically to the practical variant.

**Implication/comparison:** Ladder changes the feedback supplied to the search, not merely the final standard error printed after unrestricted reuse. Its target is a leaderboard sequence and should not be treated as an interchangeable selected-configuration CI. A rounded score alone is not a faithful implementation of Ladder. Real-data absence of a large gap in a particular competition is compatible with a severe constructed attack, so show conditions and utility as well as worst cases.

## 9. Inference on Winners: selected target and coverage distinctions

**Read source:** Isaiah Andrews, Toru Kitagawa, and Adam McCloskey, *Inference on Winners*, NBER Working Paper 25456, downloaded revision September 2021 (title page: January 2019, initial version May 2018). Introduction and §§2–4 problem/conditional/projection/hybrid procedure descriptions. The supplied record also points to a 2024 QJE article, whose final text has not been substituted for this consulted revision.

**Establishes:** The parameter of interest can be the true quality of the unit selected as best **in the sample**, as distinct from the true maximum in the population. Conventional inference can suffer winner's-curse bias and undercoverage. The paper distinguishes validity conditional on selected identity from validity averaged over selected identities. Conditional/truncated-normal inference, projection of simultaneous intervals, and hybrid methods have different properties and tradeoffs. Its main exact setup is a normal vector with known covariance, with feasible asymptotic extensions under conditions. Sample splitting preserves inference independence but can select a different, more variable target and use less data for inference.

**Implication/comparison:** This is a close classical antecedent for the study's central estimand. Do not call the discovery of winner's curse, conditional selection inference, hybridization, or simultaneous correction new. Marginal coverage over repeated selections is weaker than identity-conditional coverage; neither is a posterior probability given the full realized dataset. A chosen fresh-question target must not silently become `max_j p_j`.

## 10. High-dimensional Gaussian maxima and multiplier bootstrap

**Read source:** Chernozhukov, Chetverikov, and Kato, arXiv:1212.6906v1 (31 December 2012), whose consulted title is *Central Limit Theorems and Multiplier Bootstrap When p Is Much Larger Than n*. Introduction, §§3.2–4.2 multiplier definitions, conditions and approximation-error statements. The supplied record uses the later journal title *Gaussian approximations and multiplier bootstrap for maxima of sums of high-dimensional random vectors*.

**Establishes:** Under assumptions on independent observation vectors, moments/tails, nondegenerate variances, covariance estimation and growth of dimension with sample size, maxima of vector sums can be approximated by Gaussian maxima with the same covariance. A shared Gaussian multiplier per observation preserves dependence across coordinates and estimates maximum quantiles. Theorems quantify approximation error; bounded outcomes alone do not establish that a finite sample satisfies a small-error regime. The original sufficient dimension-rate conditions can be restrictive.

**Implication/comparison:** For prompt-by-item correctness, the observation unit is the item row, not each prompt entry independently. A covariance-aware max correction can use shared multipliers across prompts. It must be labeled approximate and empirically calibrated, with care for nearly zero variance and small samples. It is not an exact binomial theorem and does not by itself permit data-dependent new candidates.

## 11. PoSI: simultaneous protection over a specified family

**Read source:** Berk, Brown, Buja, Zhang, and Zhao, *Valid post-selection inference*, Annals of Statistics 41(2), 802–837 (2013), DOI `10.1214/12-AOS1077`, accessed as arXiv:1306.1059v1. §§1–2 targets/assumptions and §§4.2–4.5 coverage/selection universe.

**Establishes:** In linear regression, valid post-selection inference can be obtained by simultaneous protection for all coefficients across an a priori specified family of submodels. Selection may be arbitrary within that family; the guarantee is generally conservative for particular selectors. Submodel parameters have model-specific meanings. The paper's exact construction assumes fixed regressors, Gaussian homoscedastic errors and an appropriate independent variance estimate; “wrong models” refers to allowing misspecified means, not absence of distributional assumptions.

**Implication/comparison:** This provides the conceptual precedent for simultaneous protection before selection. The general implication “simultaneous coverage implies coverage for a selected member” transfers; its regression-specific constants and exact guarantees do not transfer automatically to Bernoulli prompt accuracies. Family membership must be specified independently of the evaluation outcomes or protected by a larger valid argument. An unrestricted within-family selection rule is different from an unrestricted data-dependent family.

## 12. Classical model-selection bias and nested evaluation

**Read source:** Cawley and Talbot, *On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation*, JMLR 11, 2079–2107 (2010), direct known URL `https://www.jmlr.org/papers/volume11/cawley10a/cawley10a.pdf`. Abstract, §§1–4 mechanism/variance, §5 evaluation protocols, §6 conclusions.

**Establishes:** Optimizing a noisy model-selection criterion can overfit that criterion; this can degrade selected-model generalization and bias evaluation. The size of the resulting bias can be comparable to algorithm differences, and the bias need not affect compared algorithms equally. Selection must be repeated **inside** the evaluation resampling procedure; fixing hyperparameters selected using the full dataset and then repartitioning that dataset does not recreate independent evaluation.

**Implication/comparison:** Nested evaluation is longstanding. The study can investigate its cost, target and performance for LLM configuration search, but cannot present nested resampling or the basic reuse warning as novel. A bootstrap or CV of a fixed already-selected candidate is not a rerun of the full search. An outer evaluation estimates the trained selection procedure at its inner sample size; it is not automatically an interval for the exact final configuration selected using all items.

## Cross-source comparison map

| Line of work | Quantity/goal established | What it does not automatically establish for this study |
| --- | --- | --- |
| DSPy/MIPRO | Optimize a composed LM program against a task metric | Validity of any arbitrary reused final score |
| TRIPLE / best-arm identification | Identify a good/best prompt under an evaluation budget | Unbiased or calibrated reported score of selected prompt |
| FormatSpread | Range over plausible formats on specified task data | Sampling confidence interval for selected deployment quality |
| PromptEval | Distribution/quantiles of prompt performance under sparse evaluation and model assumptions | Post-selection fresh-question coverage |
| Dwork et al. | Valid adaptive interaction using controlled mechanisms | Protection after unrestricted label/feedback exposure |
| Ladder | Accurate sequence of best-so-far leaderboard values under controlled releases | An accurate interval for every submitted system |
| Andrews et al. | Inference for true quality of data-selected winners, with conditional/marginal distinctions | Distribution-free Bernoulli validity without adaptation |
| PoSI | Simultaneous protection across a specified regression family | A free guarantee for a data-generated prompt universe |
| CCK | Approximate Gaussian/multiplier inference for high-dimensional maxima under conditions | Exact small-sample coverage from a citation alone |
| Cawley–Talbot | Selection-aware outer evaluation and consequences of noisy optimization | A guarantee for the exact final full-data-selected configuration |

## Defensible positioning

The basic phenomenon, independent holdout, simultaneous protection, selected-target inference, and nested evaluation have substantial prior foundations. A defensible study-specific contribution would be a precise measurement of score reuse and decision consequences in a clearly specified LLM search setting, linked to controlled mechanisms and a calibrated, useful reporting protocol. Such a contribution is conditional on the experiments actually delivered; it is not a current finding or a claim of priority over inaccessible work. The objective explicitly withholds a related paper. Do not claim exhaustive related-work coverage, speculate about that paper, or try to prove novelty by looking for it.
