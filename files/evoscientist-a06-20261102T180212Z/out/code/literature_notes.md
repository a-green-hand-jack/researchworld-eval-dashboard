# Bounded background notes: accuracy reporting after selecting fixed prompts

## Scope and access boundary

Access date: **2026-11-02 UTC**. This is a bounded reading of the six specified arXiv originals, not a literature search, review of later work, or novelty assessment. No search engines, citation/recommendation pages, metadata APIs, mirrors, related-paper links, or code/data sites were accessed. Citations appearing inside an allowed paper were not followed or treated as independently verified sources. No attempt was made to identify or infer the forbidden paper.

**Berk / DOI 10.1214/12-AOS1077: unavailable.** The DOI redirected to an original Project Euclid article URL. Both that article's `.full` and `.pdf` URLs returned HTTP 200 **Incapsula challenge HTML**, not an abstract, article, or PDF. No challenge scripts/iframes were fetched. Consequently, no substantive Berk claims are made and no Berk entry is included in `references.bib`. Its title/metadata are not reconstructed from memory, other papers, or third-party sources.

All outputs are in `/work` root. Existing template assets and manuscript files were not edited. `literature_access_manifest.json` records requested/final URLs, access times, HTTP outcomes, hashes, saved filenames, unavailable content, resolved versions, and exact consulted text windows. Six original PDFs, their complete page-delimited text extractions, six abstract/metadata extracts, and six `*_consulted_extracts.txt` files preserve the material used. Raw abstract HTML was saved for provenance; only citation metadata, abstract, and submission history were extracted for reading. `pdftotext` was unavailable; PDF text was extracted with **pypdf 6.21.4**, so equations/tables can have extraction artifacts. PDF page numbers below refer to the saved originals.

Unversioned direct arXiv URLs resolved to these revisions of the original works:

| Ref. / BibTeX key | Initial arXiv year | Revision actually read |
|---|---:|---|
| [1] `wang2024mmlupro` | 2024 | 2406.01574v6, 2024-11-06 |
| [2] `khattab2023dspy` | 2023 | 2310.03714v1, 2023-10-05 |
| [3] `opsahlong2024mipro` | 2024 | 2406.11695v2, 2024-10-06 |
| [4] `dwork2014adaptive` | 2014 | 1411.2664v3, 2016-03-02 |
| [5] `blum2015ladder` | 2015 | 1502.04585v1, 2015-02-16 |
| [6] `chernozhukov2012maxima` | 2012 | 1212.6906v6, 2018-01-23 |

The bibliography deliberately uses verified **arXiv-preprint metadata** rather than guessing publication venues/years. Initial-submission year and consulted-revision date are distinguished.

## Key Findings

### First separate the estimands and the selection mechanisms

These distinctions are an experimental synthesis, not a claim that a starter paper already studies this exact prompt-reporting task.

For a fixed model, scoring rule, and decoding protocol, let `Y_ij` be correctness on item `i` using prompt `j`, `a_hat_j = mean_i Y_ij`, and `j_hat = argmax_j a_hat_j`, with a prespecified tie rule.

1. **Observed finite-benchmark accuracy** is an arithmetic property of the generated responses. Selecting a prompt does not make that count incorrect. A confidence interval instead requires a stated random sampling or generation target.
2. **Population accuracy of the selected prompt**, `a_j_hat = E_D[Y_j_hat]`, concerns new items from a specified distribution. Selection can invalidate treating the winner as an independently fixed prompt. A realized train/test gap need not be positive [4,5].
3. **Independent audit-split accuracy** estimates performance on a disjoint, untouched portion of the available benchmark under the chosen split design. It is not literally newly authored data and does not by itself solve pretraining contamination, duplicate questions, or distribution shift.
4. **Best attainable population accuracy**, `max_j a_j`, is not necessarily the population accuracy of the empirically selected prompt. Report winner performance, selection regret, and model-ranking changes as different quantities where measurable.
5. **Fixed family, selected winner:** all candidate prompts and their construction are fixed independently of the evaluation rows, though the winning index is selected on them. Simultaneous fixed-family inference is relevant [5,6]. Freezing prompts only *after* inspecting these rows does not establish this condition.
6. **Adaptively generated family:** score feedback, item errors, labels, demonstrations, or dataset summaries from those rows influence new prompts. The realized list is not automatically a fixed-family problem just because it is frozen at reporting time. This is closer to adaptive-query analysis or restricted-feedback leaderboard mechanisms [3–5].

### [1] MMLU-Pro: benchmark and prompt-variation context

**Consulted:** abstract/title metadata; PDF pp. 1–6 and portions of pp. 7–9, especially §§3–4 and §6.3. Evidence anchor: “24 different but reasonable prompts” (p. 9).

**Supports.** MMLU-Pro has **12,032 questions across 14 discipline subsets** (§3.1). It expands options toward ten and filters/reviews questions. Do not assume ten options for every question: §3.2 reports 83% with ten, 17% with fewer, mean 9.47. The original protocol uses **5-shot chain-of-thought**, with five representative demonstrations per discipline (§4); Table 2 notes the Gemini models use zero shots. The metric is answer accuracy, with explicit answer extraction rather than a confidence/probability score.

For prompt sensitivity, the authors evaluate **24 prompts** and report score ranges generally around **2 percentage points**, maximum **3.74**, for MMLU-Pro versus generally 4–5 and maximum 10.98 on MMLU (§6.3/Fig. 5). These are the paper's prior results, not results from this project. A score range across prompts is **not** a standard error, confidence interval, or winner's optimism estimate.

**Protocol pitfall.** §4 specifies primary and secondary regular expressions and then **randomly selects an option if both fail**. Parser/fallback changes can alter measured accuracy and create or obscure differences between prompts. Preserve raw completions, parsing status, and any fallback RNG; report invalid-response rates. A strict-invalid-as-wrong analysis is a useful separate sensitivity analysis, not an unannounced reproduction of their metric.

**Does NOT support.** Reduced variability in this particular 24-prompt experiment does not establish absence of selection bias, robustness to arbitrarily large/adaptive searches, or post-selection interval coverage. It does not provide a same-item-selected winner versus untouched-item audit study in the consulted sections. Nor does it establish the superpopulation sampling model required by the statistical papers.

**Artifacts / verification boundary.** The paper establishes the benchmark and describes its evaluation. No dataset repository or code site was opened. The requested dataset revision `b189ec765aa7ed75c8acfea42df31fdae71f97be` and the requested `test=12032 / validation=70` are project requirements, **not independently verified by this reading**. The 12,032 total appears in the original; this alone does not verify repository split labels or contents.

### [2] DSPy: concrete prompt/program selection baseline

**Consulted:** abstract/title metadata; PDF pp. 1–11, especially §§4, 6–7. Evidence anchor: “10–20 trials over 150–300 validation examples” (p. 9).

**Supports.** DSPy parameterizes LM modules and optimizes demonstrations and other pipeline parameters against a supplied metric. The compiler separates candidate generation, parameter optimization, and higher-order program optimization. `BootstrapFewShotWithRandomSearch` supplies an actionable baseline: generate successful demonstrations from training examples, evaluate candidate programs, select by validation metric (§4/§6). A selected program can then be frozen for auditing; demonstrations, program logic, and inference settings are part of the configuration, not merely an instruction string.

**Evaluation protocol.** GSM8K: **200 training and 300 development examples** sampled from the official training set, final evaluation on the **approximately 1.3k official test examples**; correctness is the final numerical value (§6). Random few-shot sampling settings average 3–5 runs. HotPotQA: official validation becomes the testing source because the official test is hidden; **1,000 testing examples** are sampled. The training source is partitioned 70/30, restricted to “hard” examples, and **200 training / 300 development** examples are sampled (§7). Metrics include answer exact match and pair-retrieval accuracy. Table 2 specifically says the **training set, not development, is used directly for cross-validation** on HotPotQA. One marked ensemble test result uses only 50% of their test sample for cost.

**Does NOT support.** Optimization gains or a displayed development/test gap are not estimates of pure selection optimism: source composition, program differences, generation noise, and different samples also matter. The work is not a post-selection confidence-interval theorem, and its multi-call/ensemble settings do not transfer unchanged to a single-call fixed-prompt study.

**Code availability as announced, not checked:** its own abstract gives `https://github.com/stanfordnlp/dspy`. The URL was not visited; current API compatibility was not verified.

### [3] MIPRO: adaptive prompt optimization, budgets, and data flow

**Consulted:** abstract/title metadata; PDF pp. 1–9 (selected windows), Appendix B on pp. 13–14, and a short adjoining portion of p. 15. Evidence anchors: “randomly selected mini-batch” and “highest scoring fully evaluated” (§4.3).

**Supports.** MIPRO proposes grounded instructions, bootstraps demonstrations, and uses a tree-structured Parzen surrogate to choose combinations. It evaluates on stochastic mini-batches, periodically evaluates promising configurations on the full training set, and returns the highest-scoring fully evaluated configuration (§4.3). Grounding may use dataset summaries and prior evaluated prompts/scores (§3.1). These are distinct information channels to log when distinguishing a fixed family from adaptive search.

**Evaluation protocol and split exceptions.** Appendix B.1/Table 3 explicitly assigns **training to optimizer fitting**, **development to internal method iteration**, and **test to final reporting**:

| Task | Train | Dev | Test |
|---|---:|---:|---:|
| HotPotQA | 500 | 500 | 2,000 |
| HotPotQA Conditional | 500 | 200 | 200 |
| Iris, including the typo setting | 75 | none | 75 |
| Heart Disease | 120 | none | 183 |
| ScoNe | 500 | 500 | 1,200 |
| HoVer | 500 | 500 | 1,520 |

Thus “500/500/2,000 for all tasks” would be wrong. Task metrics include exact match, accuracy, a custom conditional-answer metric, and HoVer retrieval recall; these are not interchangeable. The authors conduct **five optimizer runs** per method/task. They report Wilcoxon signed-rank comparisons using per-test-example averages across runs (§5.2/Table 2), not simultaneous intervals for a prompt selected on those test examples.

**Budget details.** Appendix B.2 gives 50 full-evaluation-equivalent trials for HotPotQA/ScoNe (about 300 minibatch trials), 30 for Iris/Heart Disease/HotPotQA Conditional, and 20 for HoVer. Log candidate proposals, mini-batch observations, full-set evaluations, and actual LM calls separately; “number of trials” alone obscures exposure and cost.

**Reproducibility pitfalls.** Appendix B.4 uses Llama-3-8B with temperature 0.7 and top-p 1.0 outside noted optimization exceptions, task-specific output limits, and **no chat template**. A chat-template or decoding change is a protocol change. Their parallel A100 setup is not a measured one-week/24-GB runtime guarantee. Dataset summaries/demonstrations must not be constructed from audit rows.

**Does NOT support.** Bayesian-optimization uncertainty is not calibrated uncertainty for the selected prompt's population accuracy. Five runs or significance tests do not automatically repair reusing evaluation items for selection/reporting. MIPRO's results on seven programs do not establish the magnitude of selection effects on MMLU-Pro.

**Code availability as announced, not checked:** the abstract states optimizers and benchmark are released in DSPy at `http://dspy.ai`; no site or repository was opened. Reproducing a full optimizer is optional for an initial fixed-family study; random search is a simpler exposure-controlled baseline [2,3].

### [4] Adaptive analysis: why generating new analyses from feedback is different

**Consulted:** abstract/title metadata; PDF pp. 1–8 and beginning of p. 9, relying on §§1.1–1.3 and the statistical-query definition, not on cited later developments. Evidence anchors: “randomly and independently” and “the only access ... through a differentially private algorithm” (§§1.1, 1.3; extraction spacing varies).

**Supports.** The setup uses i.i.d. draws from an unknown distribution and bounded statistical queries `psi: X -> [0,1]`, whose **population expectations** are the targets. Query choice may depend on prior answers. The paper develops privacy-based mechanisms and transfer results for coordinated/perturbed answers that generalize. A fixed prompt's correctness indicator is a natural bounded-query analogy; a score-informed sequence of new prompts is an adaptive-query analogy. The ordinary fixed-query concentration argument is not automatically valid for the adaptively selected query.

**Assumptions / calibration.** The guarantees are over random sample draws and mechanism randomness under stated privacy/sample-complexity conditions. The paper's exponentially-many-query existence result has computational qualifications; it is not a free computationally efficient method for unrestricted benchmark reuse (§1.2). The feedback mechanism must actually satisfy the required conditions. A fully public benchmark with access to all labels/item errors is not restricted access through such a mechanism.

**Does NOT support.** It is not a drop-in estimator that retrospectively corrects an arbitrary nonprivate selected accuracy. Small ad hoc noise, a query cap, or labeling a set “holdout” does not instantiate its guarantees. It does not quantify the bias of this project's prompts or establish that all prompt variation is adaptive overfitting.

**Artifacts:** theoretical work; no implementation artifact was verified in the consulted sections.

### [5] Ladder: restricted reporting, not ordinary per-prompt confidence intervals

**Consulted:** abstract/title metadata; PDF pp. 1–13 (partial last page), emphasizing §§2–6. Evidence anchor: “only for those that made a significant improvement” (p. 4).

**Supports.** Leaderboard accuracy targets the **best population loss so far**, uniformly over the submission sequence, not accurate loss estimates for every submission. With bounded loss and i.i.d. examples, fixed-step Ladder releases a rounded new empirical loss only when it beats the previous released value by a prescribed margin; otherwise it repeats the previous value (§3/Fig. 1). Its proved rate is of order **`(log(kn)/n)^(1/3)`** with the specified step-size choice (Theorem 3.1). The mechanism is prospective: reduced feedback is how it limits adaptation.

For a **family of k classifiers fixed independently of the sample**, §2, Eq. (2), gives the Hoeffding/union-bound benchmark `P(any |R_hat_j-R_j| > epsilon) <= 2 k exp(-2 n epsilon^2)`. This is an immediately useful conservative comparator for simultaneous fixed-prompt reporting. Cross-prompt independence is not required; independence of the family from the sampled evaluation data is.

**Critical distinction.** The parameter-free variant uses a paired-loss-difference threshold and roughly a 0.15-level one-sided test. **§4.1 explicitly calls this test heuristic** under adaptivity and notes that repeated comparisons are not controlled. Do not attribute the fixed-step theorem to this variant or interpret its per-step tests as valid adaptive p-values.

**Empirical protocol / failure modes.** The boosting-attack experiment uses 12,000 binary labels, 4,000 for feedback and 8,000 untouched, averaging five independent repetitions (§5.1). The real Photo Quality competition uses **3,600 public / 8,400 private** examples and **1,785 successfully processed submissions** (§6). There, little overfitting occurred, and common hard examples induced strongly correlated score shifts. This cautions against reading every same/audit difference as selection bias or treating prompts as independent samples.

**Does NOT support.** A rounded/thresholded best-so-far score is not necessarily the raw accuracy of the latest submitted prompt or a confidence interval for the ultimately selected prompt. Ladder cannot retroactively undo information already disclosed through full score/item access. Its adversarial attack magnitude is not a prediction of LLM prompt-search effects. Historical competition files are described, but their present availability was not verified.

### [6] Maxima bootstrap: simultaneous inference for dependent fixed coordinates

**Consulted:** abstract/title metadata; PDF pp. 1–10 and selected pp. 11–17, particularly Theorem 2.2, §3.2/Theorem 3.1, Corollary 3.1, and the signed-coordinate construction on p. 16. Evidence anchors: “independent centered random vectors” (§3.2) and “without restricting correlations” (abstract).

**Supports.** Chernozhukov–Chetverikov–Kato approximate the maximum of sums of **independent random vectors**, allowing dependence across coordinates. Gaussian multiplier bootstrap estimates maximum-statistic quantiles using common row multipliers; the result is useful for simultaneous high-dimensional mean inference. The coordinates need not have a nonsingular covariance matrix, but marginal variance, moment/tail, dimension/sample-size, and approximation conditions still matter. The basic theorem assumes variances bounded away from zero. Bounded binary correctness does not, by itself, ensure this if a prompt is almost always correct/incorrect.

**Proposed experimental adaptation—not a turnkey theorem for this project.** For a genuinely precommitted family of `m` prompts and independent evaluation-item rows, form centered row vectors `Y_ij - a_hat_j`. Draw independent `g_i ~ N(0,1)` and compute

`T* = max_j [ n^(-1/2) sum_i g_i (Y_ij - a_hat_j) ]`.

Use the conditional `(1-alpha)` quantile `q*` to form candidate simultaneous **lower bounds** `L_j = a_hat_j - q*/sqrt(n)` (optionally clip below at zero). Use **the same `g_i` across all prompts** to preserve their observed covariance. A two-sided band uses a maximum over absolute values, equivalently positive and negative coordinates. Centering with estimated means is a practical plug-in step whose covariance/approximation error must be controlled and tested; it is not licensed by only quoting the oracle-centered formula in the introduction. Studentized or pairwise-difference variants require their own variance and approximation checks.

If valid simultaneous coverage holds, reading out `L_j_hat` after selecting the winning index is protected by that simultaneous event. This targets a bound for **the selected prompt's population accuracy**, not an estimate of its optimism and not proof it is the population-best prompt. The crucial requirement concerns how the *entire coordinate family* was constructed, not whether its winner was selected later.

**Calibration / failure modes.** The original gives nonasymptotic approximation-error bounds and sufficient growth conditions, not an exact finite-sample 95% guarantee for arbitrary `m,n`; a displayed bounded-variable sufficient condition involves `(log p)^7/n`. Do not turn it into a practical numerical coverage guarantee without checking constants/conditions. Extreme accuracies, small samples, item clusters, domain-stratified sampling, and missing/error responses need explicit treatment. Resampling prompts independently discards useful dependence; reusing a single multiplier per prompt rather than per item is also wrong for this construction.

**Does NOT support.** Conditional bootstrapping of the realized output matrix does not automatically cover prompts generated from those same rows, unrestricted MIPRO-style search, or arbitrary stopping. Simultaneous coverage is not unbiased point estimation. Fixed-domain benchmark composition is not automatically i.i.d. population sampling. The term “adaptive specification testing” in the original does not establish a theorem for arbitrary adaptive prompt creation.

**Artifacts:** theory and simulation descriptions are available in the original; no external implementation was checked. The DOI `10.1214/13-AOS1161` is present in the allowed arXiv page's metadata; it was not visited.

## Recommended Next Experiments

These are proposals, **not completed experiments or predicted numerical results**.

1. **Start with a precommitted prompt-pool experiment.** Freeze a modest list before inspecting scoring/audit rows. Fix model revision, complete rendered prompts/demonstrations, ordering, chat template, decoder, parsing, metric, tie-breaking, and all seeds. Generate a question-by-prompt correctness matrix using one real LM. This isolates selection among fixed configurations from candidate generation [1–3,6]. Treat any later prompt editing as a separate adaptive condition.
2. **Use an untouched audit set.** Partition by question ID before prompt work, with a justified subject allocation and duplicate/group handling. Select only on the selection rows; audit the frozen winner once. Reserve audit access from both optimizers and human iteration. Report the selected same-item score, audit score, their signed difference, and ranking changes separately. Distinguish micro accuracy from equal-subject macro accuracy; neither weighting should be chosen after seeing which tells the better story [1–5]. A random benchmark split probes reuse on that benchmark, not unseen source distributions.
3. **Compare reporting procedures on exactly the same selection matrices:** naive selected-score intervals; a prespecified no-selection prompt; simultaneous Hoeffding bounds from [5]; and covariance-aware multiplier lower bounds motivated by [6]. At level `1-alpha`, the two-sided fixed-family Hoeffding radius is `sqrt(log(2*m/alpha)/(2*n))`. Label it a sufficient conservative radius under its assumptions, not a model of typical bias. Do not use a pointwise selected-prompt bootstrap as the unquestioned calibration oracle.
4. **Validate statistical calibration before claiming reliability.** In controlled simulations with known prompt accuracies and tunable within-item dependence, estimate selected-prompt lower-bound coverage `P(L_j_hat <= a_j_hat)`, simultaneous coverage, and average bound width. Separately sweep selection-item count, pool size, true accuracy heterogeneity, prompt similarity, and near-zero variance. Report Monte Carlo uncertainty for coverage. Audit-set accuracy is itself noisy, so checking whether an interval contains one audit estimate is not a direct test of population coverage [5,6].
5. **Measure selection, not just search volume.** Use nested subfamilies and repeated selection/audit partitions of the saved matrix to examine sample-size/pool-size effects at low additional LM cost. Repeated partitions are dependent; they do not create new independent questions or justify a naive standard error over split replicates. Report correlation/error-overlap summaries rather than presuming `m` independent trials. Keep item-sampling uncertainty separate from decoding randomness; repeat generation on a planned subset if needed [1,3,5,6].
6. **Only then add adaptive search.** A budget-matched random-search baseline [2] and, if resources permit, a small MIPRO-style condition [3] can vary feedback granularity and new-candidate construction. Record every feedback channel, proposal, mini-batch/full evaluation, and stop decision. Use the same untouched audit protocol for these conditions. Treat fixed-family bootstrap guarantees as unestablished there unless additional analysis justifies them. If testing a Ladder-inspired restricted-feedback condition, restrict information *during search* and distinguish proved fixed-step from heuristic parameter-free versions [4–6].

**Reporting checklist:** dataset revision/split IDs; domain weights; complete candidate provenance; selection/audit exposure; raw completions and parser failures; full LM configuration; prompt/model-call/token budgets; tie/stop rules; confidence target and resampling unit; bootstrap replication count/quantile convention/RNG; interval clipping; selected versus population-best estimand; and limitations of finite benchmark reuse. Model confidence calibration (for example probability calibration) is a different question from coverage of reported accuracy intervals; none of these readings validates it for this experiment.

## Claims this bounded reading does not justify

- “No previous work studies this problem” or any other novelty/priority certification.
- “MMLU-Pro prompt robustness eliminates winner's optimism.”
- “DSPy/MIPRO gains are artifacts of benchmark reuse,” or their reported gaps measure only selection bias.
- “All same-item-selected accuracies overestimate new-item accuracy on every split.”
- “The multiplier bootstrap is exactly calibrated for arbitrary adaptive searches.”
- “The Ladder's parameter-free paired tests control adaptive type-I error.”
- Any substantive claim attributed to the unavailable Berk original.

### Sources

Only these six successfully accessed originals enter `references.bib`. No citations were followed.

[1] Wang et al. **MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark.** https://arxiv.org/abs/2406.01574 ; consulted PDF: https://arxiv.org/pdf/2406.01574

[2] Khattab et al. **DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines.** https://arxiv.org/abs/2310.03714 ; consulted PDF: https://arxiv.org/pdf/2310.03714

[3] Opsahl-Ong et al. **Optimizing Instructions and Demonstrations for Multi-Stage Language Model Programs.** https://arxiv.org/abs/2406.11695 ; consulted PDF: https://arxiv.org/pdf/2406.11695

[4] Dwork et al. **Preserving Statistical Validity in Adaptive Data Analysis.** https://arxiv.org/abs/1411.2664 ; consulted PDF: https://arxiv.org/pdf/1411.2664

[5] Blum and Hardt. **The Ladder: A Reliable Leaderboard for Machine Learning Competitions.** https://arxiv.org/abs/1502.04585 ; consulted PDF: https://arxiv.org/pdf/1502.04585

[6] Chernozhukov, Chetverikov, and Kato. **Gaussian Approximations and Multiplier Bootstrap for Maxima of Sums of High-Dimensional Random Vectors.** https://arxiv.org/abs/1212.6906 ; consulted PDF: https://arxiv.org/pdf/1212.6906
