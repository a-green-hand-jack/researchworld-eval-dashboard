# Restricted-source reading notes

Study date: 2026-11-02. Research only; no method implementation or experiments.

## Scope and source policy

Seven allowed original works were read in full-text excerpts, not merely abstracts. Source PDFs, page-marked extracted text, arXiv landing-page snapshots and metadata are stored beside these notes. Section/page lists below describe what was actually read; they do **not** mean entire papers or all proofs were read. PDF page numbers refer to the saved PDF. Unversioned PDF retrievals were checked against their first-page arXiv version stamps and original-page revision metadata.

Only the user-specified original article URLs and their same-work arXiv PDF representations were retrieved. For the allowed DOI, the original publisher redirect and publisher PDF endpoint were attempted, but both returned access-block HTML. No scientific discovery queries, citation traversal, recommendations, mirrors, third-party summaries, repositories, or citing works were accessed. URLs printed inside original papers are availability statements only, not visited resources. See `access_audit.md` for the access-block and incidental bibliography-exposure record. The identity of the prohibited work was neither guessed nor investigated.

Bibliography policy: `references.bib` records the seven **arXiv originals**, with verified original-submission years, identifiers and actual version/revision notes. It does not invent proceedings details. Thus an arXiv entry's year can differ from its conference year or last revision. Conference designations below are included only where visible in the read PDF. Evidence quotes are at most 80 characters each; line whitespace and PDF typographic ligatures may be normalized, without paraphrasing.

## 1. MMLU-Pro — benchmark and score-extraction protocol [mmlupro2024]

**Verified bibliography.** Yubo Wang, Xueguang Ma, Ge Zhang, Yuansheng Ni, Abhranil Chandra, Shiguang Guo, Weiming Ren, Aaran Arulraj, Xuan He, Ziyan Jiang, Tianle Li, Max Ku, Kai Wang, Alex Zhuang, Rongqi Fan, Xiang Yue, and Wenhu Chen. *MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark*. arXiv:2406.01574, originally 2024-06-03; read v6, 2024-11-06. PDF identifies NeurIPS 2024 Datasets and Benchmarks track.

Original: https://arxiv.org/abs/2406.01574  
PDF: https://arxiv.org/pdf/2406.01574  
Local: `2406.01574.pdf`, `2406.01574.txt`, `2406.01574.abs.metadata.json`.

**Actually read.** Title/abstract; introduction and overview; §3.1–3.2 dataset composition/construction; §4 experimental setup; §6.2–6.3 reasoning and prompt robustness; §7 limitations; Appendix A.2 demonstration-source paragraph. Principal pages: 1–5, 8–9, 14. The initial p.1–5 excerpt also included §2 related work; no references were followed. A later excerpt inadvertently included the start of the bibliography on p.9 (logged separately).

**Verified contribution and actionable protocol.** The dataset has 12,032 questions across 14 disciplines. It combines cleaned original MMLU questions with additional STEM, TheoremQA and SciBench sources. Although described as increasing choices to ten, §3.2 specifies that 83% have ten options and 17% have fewer; mean option count is 9.47. Evaluation uses five discipline-specific CoT demonstrations, with Appendix A.2 identifying the validation subset as the demonstration source. Table 2 notes zero-shot exceptions for Gemini-1.5-Pro and Flash. Section 4 specifies sequential regex answer extraction and, when both extraction attempts fail, a **random-option fallback**. That is an important reproducibility/noise choice, not a neutral parser detail.

Section 6.3 evaluates 24 reasonable prompts and reports a typical accuracy range around two percentage points on MMLU-Pro, maximum 3.74 points, versus generally 4–5 points on MMLU. These are observed cross-prompt ranges, not confidence limits or bounds on selection bias. The precise prompt list and a standalone selection/inference split were not verified in the sections read. The fixed question count is not evidence of an iid population-sampling design.

**Evidence (≤80 characters each).**
- “we evaluated models using 24 different but reasonable prompts.” (§6.3, p.9)
- “a random option from the answer choices is selected.” (§4, p.5)

**Resources.** Dataset construction and evaluation protocols are present in the original. No dataset download, repository contents, license, current split sizes or executable evaluator were inspected. Do not treat the source-reported demonstrations as an independent inference holdout.

**Applicability/cautions.** Useful benchmark and format-family motivation, not selected-winner inference. Curated discipline mixtures, inherited question sources and filtering do not establish iid sampling. Define whether the target is the finite benchmark, a fixed weighted subject mixture or a broader question population. Freeze decoding, parser and fallback randomness before comparing prompts; record invalid-output rates. A low prompt range can coexist with selection-induced optimism.

## 2. DSPy — optimizing demonstrations/programs [dspy2023]

**Verified bibliography.** Omar Khattab, Arnav Singhvi, Paridhi Maheshwari, Zhiyuan Zhang, Keshav Santhanam, Sri Vardhamanan, Saiful Haq, Ashutosh Sharma, Thomas T. Joshi, Hanna Moazam, Heather Miller, Matei Zaharia, and Christopher Potts. *DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines*. arXiv:2310.03714v1, 2023-10-05. Read PDF is marked “Preprint”; no later publication metadata is inferred.

Original: https://arxiv.org/abs/2310.03714  
PDF: https://arxiv.org/pdf/2310.03714  
Local: `2310.03714.pdf`, `2310.03714.txt`, `2310.03714.abs.metadata.json`.

**Actually read.** Title/abstract; §4 compiler stages 1–3 on p.7; §5 goals; §6 GSM8K protocol and optimization; §7 HotPotQA setup/program/compilation and initial results discussion, pp.7–10. Appendices/pseudocode were not audited.

**Verified contribution and actionable protocol.** Parameterized LM modules are composed into programs; bootstrapped successful traces yield demonstration candidates, with random search or other hyperparameter selection over candidates. The text explicitly optimizes average metric quality using cross-validation on training data or a validation set. GSM8K: 200 training and 300 development question–answer pairs sampled from the official training set; final evaluation on approximately 1.3k official test examples; final numerical-answer accuracy. Randomly sampled few-shot baselines average 3–5 runs depending on setting. Compilation examples use roughly 10–20 trials over 150–300 validation examples.

HotPotQA: because official test answers are hidden, 1,000 examples from the official validation set are reserved for testing. Official training data are subdivided 70%/30% for training/validation, keeping “hard” examples; 200 training and 300 development examples are sampled. The task uses answer exact match and retrieval-aware programs. These labels must not be confused with the official split names.

**Evidence (≤80 characters each).**
- “metric with cross-validation over the training set or a validation set.” (§4)
- “comparisons on the development set to avoid overfitting on test.” (§6)

**Code availability, source-reported only.** https://github.com/stanfordnlp/dspy appears in the abstract; not visited. Current API behavior/version and repository documentation were not verified.

**Applicability/cautions.** A useful optimization baseline and example of separating tuning from final evaluation. Compilation can generate candidates using data, change multiple modules, add ensembles or finetune weights. It is not automatically an iid, fixed-prompt-family experiment. To study that setting, create/freeze the family using independent data before the inference sample is exposed, or explicitly analyze the adaptive process. Dev/test point scores here do not supply simultaneous or conditional-on-winner confidence intervals.

## 3. MIPRO — joint instruction/demonstration search [mipro2024]

**Verified bibliography.** Krista Opsahl-Ong, Michael J Ryan, Josh Purtell, David Broman, Christopher Potts, Matei Zaharia, and Omar Khattab. *Optimizing Instructions and Demonstrations for Multi-Stage Language Model Programs*. arXiv:2406.11695, originally 2024-06-17; read v2, 2024-10-06.

Original: https://arxiv.org/abs/2406.11695  
PDF: https://arxiv.org/pdf/2406.11695  
Local: `2406.11695.pdf`, `2406.11695.txt`, `2406.11695.abs.metadata.json`.

**Actually read.** Title/abstract; Figure 4 and §4.3 MIPRO procedure; §4.4 variants; §4.5 adjacent optimizer discussion; §5.1 setup/Table 1; §5.2 methods/models; beginning of §6 lessons; Appendix B.1–B.3 split/budget/hyperparameter details, pp.1, 5–8, 13–14. Not all task descriptions, result tables or appendices were read.

**Verified contribution.** Bootstrap demonstration sets and grounded instruction candidates; choose module-level combinations using a tree-structured Parzen-estimator Bayesian search; score configurations on random minibatches, periodically evaluate promising configurations on the full optimization training set, and return the best fully evaluated configuration. The abstract reports improvements on five of seven programs, “by as much as 13% accuracy”; this preserves the source's wording rather than reinterpreting its units. Do not treat it as a universal effect or calibrated winner correction.

**Verified evaluation protocol.** Table 1 tasks include HotPotQA exact match, conditional HotPotQA custom metric, Iris/Iris-Typo classification accuracy, Heart Disease ensemble accuracy, ScoNe exact match and HoVer Recall@21. Appendix B.1 is more precise than the generic 500/500/2,000 description:

| Dataset | Train | Dev | Test |
|---|---:|---:|---:|
| HotPotQA | 500 | 500 | 2,000 |
| HotPotQA Conditional | 500 | 200 | 200 |
| Iris | 75 | N/A | 75 |
| Heart Disease | 120 | N/A | 183 |
| ScoNe | 500 | 500 | 1,200 |
| HoVer | 500 | 500 | 1,520 |

Table 3 does not list Iris-Typo separately. Its caption distinguishes optimizer training from method-iteration development and final reporting test data; no dev split is made for the two small datasets. Section 5.2 reports five runs per method/task and Wilcoxon signed-rank tests applied to run-averaged, example-level test results. Appendix B.2 gives 50 full-evaluation-equivalent trials for HotPotQA/ScoNe (about 300 minibatch trials), 30 for Iris/Heart Disease/conditional HotPotQA and 20 for HoVer. Most experiments use GPT-3.5 proposer at default temperature 0.7 and Llama-3-8B task model; GPT-4o is used as demonstration teacher for the harder ScoNe and HoVer tasks.

**Evidence (≤80 characters each).**
- “We conduct 5 runs for each method on each task.” (§5.2)
- “Test was used for final evaluation” (Table 3 caption)

**Code availability, source-reported only.** Original says optimizers/benchmark are released in DSPy at http://dspy.ai; not visited.

**Applicability/cautions.** Optimize/evaluate budgets should be compared in example evaluations, not just iteration counts. Minibatch objective noise and adaptive configuration selection differ from evaluating every member of a predeclared prompt family on the same iid sample. Freezing proposal pools is necessary but not sufficient if proposals or demonstrations depend on the inference data. Neither Bayesian optimizer uncertainty nor the reported Wilcoxon tests establish a selected prompt's calibrated population-score interval.

## 4. Format sensitivity / FormatSpread [formatspread2023]

**Verified bibliography.** Melanie Sclar, Yejin Choi, Yulia Tsvetkov, and Alane Suhr. *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting*. arXiv:2310.11324, originally 2023-10-17; read v2, 2024-07-01. PDF identifies ICLR 2024.

Original: https://arxiv.org/abs/2310.11324  
PDF: https://arxiv.org/pdf/2310.11324  
Local: `2310.11324.pdf`, `2310.11324.txt`, `2310.11324.abs.metadata.json`.

**Actually read.** Title/abstract and introductory sensitivity discussion, p.1; end of §3.1 prompt construction, §3.2 sensitivity/Algorithm 1, §4.1 setup and opening §4.2 results, pp.4–5. Detailed grammar restrictions, prior choices, cost experiments and other appendices were not read.

**Verified contribution and protocol.** For a sampled family of plausible, semantically equivalent formats, defines the empirical performance interval as min/max format score and spread as max minus min. FormatSpread uses Bernoulli Thompson sampling, spending half its evaluation budget searching for a maximum and half for a minimum, reusing accumulated observations. It samples previously unevaluated data for each arm rather than automatically constructing a full balanced question-by-format matrix.

Experiments use 53 Super-NaturalInstructions tasks: 19 multiple-choice and 34 classification tasks. Data sets are treated as size 1,000 for fair evaluation. Few-shot examples are randomly chosen, excluded from evaluation, and their identities/order fixed across formats. Models include LLaMA-2 7B/13B/70B, Falcon-7B and its instruction version, and GPT-3.5-Turbo. Distinguishes normalized exact-prefix accuracy from probability-ranking accuracy; defaults to ranking unless specified. Initial sensitivity study samples ten plausible formats per task and reports a median spread of 7.5 accuracy points across model/shot choices; abstract reports extremes up to 76 points for LLaMA-2-13B. Paired model comparisons use one-sided McNemar tests on shared examples.

**Evidence (≤80 characters each).**
- “We define the performance spread” (§3.2)
- “Few-shot examples for each task are chosen randomly” (§4.1)

**Code availability, source-reported only.** https://github.com/msclar/formatspread is printed in the p.1 footnote; not visited.

**Applicability/cautions.** The “performance interval” is a range across prompts, **not** a confidence interval for any prompt or the selected winner. Bandit uncertainty used to allocate computation is not automatically post-selection inference. Observed format ranges have finite-sample estimation noise. Shared examples induce cross-format dependence. The family grammar and demonstration ordering are useful controls; preserve paired item information if studying covariance-aware calibration. Results for older models and classification/probability-ranking scores need not transfer to CoT regex extraction on MMLU-Pro.

## 5. Adaptive data analysis [adaptive2014]

**Verified bibliography.** Cynthia Dwork, Vitaly Feldman, Moritz Hardt, Toniann Pitassi, Omer Reingold, and Aaron Roth. *Preserving Statistical Validity in Adaptive Data Analysis*. arXiv:1411.2664, originally 2014-11-10; read v3, 2016-03-02. First-page footnote identifies a preliminary STOC 2015 version; BibTeX describes the read arXiv version.

Original: https://arxiv.org/abs/1411.2664  
PDF: https://arxiv.org/pdf/1411.2664  
Local: `1411.2664.pdf`, `1411.2664.txt`, `1411.2664.abs.metadata.json`.

**Actually read.** Title/abstract; §1 introduction, §1.1 problem, §1.2 informal results and opening §1.3 techniques, pp.1–5; end of §3.1 including Theorem 9 and proof, opening §3.2/Theorem 10, pp.11–12. Other formal results/proofs were not audited.

**Verified contribution and protocol.** Samples are iid from a distribution over a discrete universe; statistical queries are bounded functions from the universe to [0,1]. Separates fixed nonadaptive query families from queries selected using previous answers. Uses differential privacy to transfer empirical validity to population validity. Introductory bounds explicitly depend on tolerance, query count and, for the nearly exponential-query result, universe size; the paper warns that this mechanism is computationally inefficient.

Theorem 9: if an epsilon-DP algorithm outputs a bounded query, epsilon ≤ tau/2 and n ≥ 12 ln(4/beta)/tau² imply that empirical versus population query expectation differs by at most tau except with probability beta, over both data and algorithm randomness. This is a mechanism assumption, not a theorem for arbitrary maximization of public scores. No dataset, benchmark split or code artifact was assessed here; this is theoretical evidence.

**Evidence (≤80 characters each).**
- “samples drawn randomly and independently” (§1.1)
- “selected non-adaptively before the data are gathered” (abstract)

**Applicability/cautions.** Provides the essential boundary between predeclared finite-family selection and data-dependent candidate creation/repeated feedback. Ordinary prompt search is not thereby differentially private. Do not claim privacy-style guarantees after unprotected score access or raw-question inspection. The exponential-query headline is not a practical plug-in interval or a direct claim about a selected prompt. For a genuinely fixed family, a simultaneous finite-family analysis may suffice without invoking this broader adaptive mechanism theory.

## 6. Ladder — best-so-far feedback versus winner inference [ladder2015]

**Verified bibliography.** Avrim Blum and Moritz Hardt. *The Ladder: A Reliable Leaderboard for Machine Learning Competitions*. arXiv:1502.04585v1, submitted 2015-02-16; PDF title page is dated 2015-02-17. Both dates are preserved rather than silently conflated.

Original: https://arxiv.org/abs/1502.04585  
PDF: https://arxiv.org/pdf/1502.04585  
Local: `1502.04585.pdf`, `1502.04585.txt`, `1502.04585.abs.metadata.json`.

**Actually read.** Title/abstract and introduction/opening contributions, pp.1–2; bounded-loss/iid setup, §2 adaptive estimation, §2.1 leaderboard accuracy, §3 mechanism/Theorem 3.1 and proof, opening §3.1 lower-bound statement, pp.5–7. Empirical competition study and parameter-free mechanism were not read; their performance is not used here.

**Verified contribution and calibration.** Section 2 explicitly states Hoeffding-plus-union-bound control for a family fixed independently of the sample: probability that any empirical loss differs from population loss by more than epsilon is at most 2k exp(-2 epsilon² n). No independence between classifier losses is assumed; the sample rows are iid and loss is bounded. Adaptive reuse requires a different argument.

Ladder releases a new rounded empirical loss only after an improvement by more than a threshold eta; otherwise it repeats the prior release. Its leaderboard-error target compares each release with the **minimum population loss among all submitted classifiers so far**, not necessarily the true loss of the empirically best classifier. Theorem 3.1 obtains a high-probability order (log(kn)/n)^(1/3) leaderboard error for a suitable threshold choice. Thresholding and rounding are part of the mechanism, not optional postprocessing of an ordinary public leaderboard.

**Evidence (≤80 characters each).**
- “we do not need an accurate estimate for each” (§2.1)
- “the algorithm releases the previous best loss” (§3)

**Resources.** No code/repository was inspected or verified. This reading uses the formal protocol, not an empirical reproduction claim.

**Applicability/cautions.** Especially important estimand distinction: minimum true loss/best population prompt is not the true loss of an empirical winner. For a fixed prompt family, §2 supplies a simple conservative simultaneous baseline that remains valid at any data-selected coordinate. That is unconditional coverage, not conditional coverage given the winner identity. Ladder instead changes the released-score protocol and is not a retrospective correction for fully exposed prompt scores.

## 7. Gaussian maxima and multiplier bootstrap [gaussian2012]

**Verified bibliography.** Victor Chernozhukov, Denis Chetverikov, and Kengo Kato. *Gaussian approximations and multiplier bootstrap for maxima of sums of high-dimensional random vectors*. arXiv:1212.6906, originally 2012-12-31; read v6, 2018-01-23. DOI 10.1214/13-AOS1161 is verified in the original arXiv landing-page metadata. The saved PDF says “Submitted to the Annals of Statistics”; journal volume/pages/year were not inferred from the DOI.

Original: https://arxiv.org/abs/1212.6906  
PDF: https://arxiv.org/pdf/1212.6906  
Local: `1212.6906.pdf`, `1212.6906.txt`, `1212.6906.abs.metadata.json`.

**Actually read.** Title/abstract and introduction pp.1–4; §2 setup/moment quantities and smooth maximum through Theorem 2.2, anti-concentration lemma and variance caveat, pp.6–9; §3.1–3.3 including comparison lemma, multiplier construction, Theorems 3.1–3.2 and Corollary 3.1, pp.11–14. Main theorem proofs, supplement proofs and application sections were not audited.

**Verified contribution and calibration.** Approximates the distribution of the maximum of normalized sums of independent centered random vectors by Gaussian vectors with matching covariance. Coordinates may be highly dependent; no full covariance invertibility assumption is imposed. Marginal variance lower/upper bounds and moment/tail/growth conditions remain essential. For bounded coordinates the introductory sufficient growth condition is that (log p)^7/n tends to zero at a polynomial rate, not simply p < n.

Section 3 uses a common iid N(0,1) multiplier per row and takes the maximum across coordinates of the resulting multiplier sums; calibration is a conditional quantile over multipliers given the data. Theorems 3.1–3.2 quantify coverage/quantile error via Gaussian approximation error, covariance-estimation error, and any linearization/remainder errors. The constructions in the formal setup use centered vectors; a practical unknown-mean plug-in must explicitly estimate/center coordinates and verify the resulting approximation assumptions. A theorem about centered maxima does not justify an uncentered resampling maximum.

**Evidence (≤80 characters each).**
- “Our result does not limit the dependency structure.” (§1)
- “This is the Gaussian multiplier (or wild) bootstrap procedure.” (abstract)

**Resources.** No software implementation or repository was verified. The read original gives mathematical calibration, not a benchmark-ready package.

**Applicability/cautions.** For a **predeclared** family, per-item prompt scores form vector coordinates; iid items give independent rows while shared items yield dependent columns. This is an appropriate mathematical starting point, not a completed proof for any proposed benchmark procedure. To obtain two-sided simultaneous bands, one can consider an augmented vector with both signs and account for any standardization; this adaptation is our planning inference, not an experiment reported by this original. Near-zero Bernoulli variance, very small sample sizes, growing family size and non-iid subject clusters require separate attention. Simultaneous bands protect a selected coordinate unconditionally; they do not automatically give conditional-on-selection coverage, unbiased winner correction or a confidence interval for the population maximum.

## Cross-source synthesis for independent planning

The following are **planning deductions**, not claims that any read paper studies the exact target problem.

### Define the target before selecting a procedure

Let a finite prompt family P be fixed independently of inference examples. For example Z and a fully specified scoring/decoding rule, let s_p(Z) be the bounded score and mu_p its population mean. The same iid examples can be evaluated under all prompts, creating a paired item-by-prompt matrix. Let p-hat be the empirical-score maximizer, with tie-breaking fixed in advance.

Keep separate:
1. The realized finite-benchmark score of p-hat (observable; not itself unknown).
2. The population score mu_(p-hat) of the data-selected winner.
3. The best population score max_p mu_p.
4. Variation across prompts (a range, not a coverage statement).
5. Conditional-on-winner inference versus unconditional selected-coordinate coverage.

The fixed-family simultaneous event covers every coordinate at once, so it also covers a selected coordinate. This elementary implication does not provide conditional coverage given which prompt won. Ladder targets best-so-far population loss, FormatSpread targets score spread, and the optimizer papers target useful configurations; none of those targets should silently replace (2).

### Recommended next experiments — proposals only, not executed

- **Anchor design:** Freeze prompts, demonstrations, candidate-generation data, model version, parser, decoding distribution and tie-breaking before inference-data access. Declare the sampling population and subject weights. Treat a curated benchmark as an empirical stress test unless the sampling design supports iid population claims.
- **Independent holdout baseline:** Select using one set and estimate only that winner on a genuinely untouched iid set. State both sample sizes and the data spent on selection. Any prompt changes after observing the holdout invalidate its untouched status. DSPy/MIPRO illustrate split roles but do not by themselves establish repeated-use validity [dspy2023; mipro2024].
- **Finite-family conservative baseline:** For [0,1] scores under iid rows, use the fixed-family Hoeffding/union-bound relation in Ladder §2, e.g. radius sqrt(log(2K/alpha)/(2n)) for two-sided simultaneous mean coverage. This is a conservative baseline, not an optimizer-derived interval [ladder2015].
- **Covariance-aware candidate:** Study centered, paired Gaussian-multiplier max-statistic calibration after explicitly checking variance and growth conditions. Resample one common multiplier per example across all prompts; independent column resampling discards pairing. Separate one-sided/two-sided calibration and studentized/unstudentized choices [gaussian2012]. No finite-sample exactness is claimed.
- **Stress factors:** Family size; sample size; almost-tied versus separated prompt means; high versus weak inter-prompt correlation; rare errors/near-degenerate variance; parser fallback and model randomness. Start with predeclared families; adaptive prompt generation is a distinct protocol requiring different guarantees [adaptive2014].
- **Coverage assessment:** If future simulations use known population means, report repeated-sample coverage of mu_(p-hat), interval width and winner-selection frequencies, with Monte Carlo uncertainty. Conditional-by-winner coverage should be labeled separately. On real benchmark data with unknown population means, do not call agreement with a finite reference sample “true coverage.” Report accuracy units as percentage points when discussing differences.

### What is not verified

No original in this restricted reading is being claimed as prior work on the exact selected-prompt inference problem, and no novelty claim has been made. No current code API, dataset license/download, external repository, benchmark contamination audit or empirical implementation was verified. The allowed best-arm and Polo starters were not retrieved; the seven read works were sufficient for this bounded assignment. Berk's publisher content could not be read and is excluded from `references.bib` and substantive claims.
