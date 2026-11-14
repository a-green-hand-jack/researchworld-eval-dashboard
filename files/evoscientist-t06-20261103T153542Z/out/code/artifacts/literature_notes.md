# Authorized-only literature notes: ranking deletion robustness and influence

## Scope, access, and evidence policy

Only these six user-authorized arXiv papers were accessed. Each exact supplied abstract URL and its corresponding arXiv PDF returned HTTP 200. No search engine, recommendation endpoint, citation graph, reference link, repository, dataset page, or other paper was opened. No attempt was made to identify any unnamed excluded paper. These notes support positioning within this explicitly bounded corpus, not a comprehensive novelty or priority determination. No implementation or experiments were performed.

Abstracts were read from the `citation_abstract` metadata on the exact allowed abstract pages; fulltexts were extracted from the PDFs with pypdf and read selectively for methods, experiments, limitations, and relevant appendices. Quotations below are actual read passages, with PDF page numbers; line wrapping and PDF typographic ligatures are normalized where necessary. Bibliographies were not used for discovery or to obtain additional sources. Paper-reported code URLs are recorded only as availability statements and were NOT visited.

Raw fetched HTML, PDFs, extracted page-marked text, and the HTTP access log are saved under `/work/artifacts/sources/`. The access log records requested URLs/statuses, not request timestamps. Research session date: 2026-11-03 (runtime context).

| ID | Exact abstract access URL | Fulltext access URL | Fetched version identified inside PDF | Access result |
|---|---|---|---|---|
| [1] | https://arxiv.org/abs/2403.04132 | https://arxiv.org/pdf/2403.04132 | v1, 7 Mar 2024 | Both 200; PDF 29 pages |
| [2] | https://arxiv.org/abs/2306.05685 | https://arxiv.org/pdf/2306.05685 | v4, 24 Dec 2023 | Both 200; PDF 29 pages |
| [3] | https://arxiv.org/abs/1703.04730 | https://arxiv.org/pdf/1703.04730 | v3, 29 Dec 2020 | Both 200; PDF 12 pages |
| [4] | https://arxiv.org/abs/2011.14999 | https://arxiv.org/pdf/2011.14999 | v5, 19 Jul 2023 | Both 200; PDF 55 pages |
| [5] | https://arxiv.org/abs/2501.17858 | https://arxiv.org/pdf/2501.17858 | v2, 10 Aug 2025 | Both 200; PDF 20 pages |
| [6] | https://arxiv.org/abs/2508.11847v1 | https://arxiv.org/pdf/2508.11847v1 | v1, 16 Aug 2025 | Both 200; PDF 29 pages |

The first five URLs were supplied unversioned, so their returned revisions were read. For [6], the requested v1 was retained for BOTH abstract and PDF; its abstract metadata advertised an unversioned PDF link, which was not used.

## Verified bibliography and version caveats

`/work/artifacts/authorized_starters.bib` contains complete author lists, exact titles, and original arXiv submission years. These are arXiv `@misc` entries, deliberately not speculative journal/DOI records.

1. **Wei-Lin Chiang; Lianmin Zheng; Ying Sheng; Anastasios N. Angelopoulos; Tianle Li; Dacheng Li; Banghua Zhu; Hao Zhang; Michael I. Jordan; Joseph E. Gonzalez; Ion Stoica. (2024). _Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference._** Author order and displayed names here follow the PDF title page. IMPORTANT: the allowed abstract's citation metadata instead places Hao Zhang before Banghua Zhu, expands Angelopoulos to Anastasios Nikolas, and gives Michael Jordan without the middle initial. This source discrepancy is preserved here rather than silently claiming both records agree.
2. **Lianmin Zheng; Wei-Lin Chiang; Ying Sheng; Siyuan Zhuang; Zhanghao Wu; Yonghao Zhuang; Zi Lin; Zhuohan Li; Dacheng Li; Eric P. Xing; Hao Zhang; Joseph E. Gonzalez; Ion Stoica. (2023). _Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena._** Original submission 9 Jun 2023; read v4.
3. **Pang Wei Koh; Percy Liang. (2017). _Understanding Black-box Predictions via Influence Functions._** Original submission 14 Mar 2017; read v3 from 2020. Do not turn its original year into 2020 because the PDF is revised.
4. **Tamara Broderick; Ryan Giordano; Rachael Meager. (2020). _An Automatic Finite-Sample Robustness Metric: When Can Dropping a Little Data Make a Big Difference?_** Original submission 30 Nov 2020; read v5 from 2023. PDF cover says 20 Jul 2023 while its arXiv footer says 19 Jul 2023. BibTeX uses original arXiv year 2020, not an inferred publication year.
5. **Rui Min; Tianyu Pang; Chao Du; Qian Liu; Minhao Cheng; Min Lin. (2025). _Improving Your Model Ranking on Chatbot Arena by Vote Rigging._** Original submission 29 Jan 2025; read v2.
6. **Jenny Y. Huang; Yunyi Shen; Dennis Wei; Tamara Broderick. (2025). _Dropping Just a Handful of Preferences Can Change Top Large Language Model Rankings._** Exact authorized v1 submitted 16 Aug 2025; PDF cover says 19 Aug 2025. Huang and Shen are marked equal contribution.

## [6] Huang et al.: direct overlap and important qualifications

Abstract URL: https://arxiv.org/abs/2508.11847v1

Fulltext URL: https://arxiv.org/pdf/2508.11847v1

### Actual read passages

- **Abstract, PDF p.1:** “We propose a method for evaluating the robustness of a widely used LLM ranking system—the Bradley–Terry ranking system—to dropping a worst-case very small fraction of evaluation data.”
- **Abstract, p.1:** “Our framework also identifies the specific evaluations most responsible for such ranking flips, allowing for inspections of these influential preferences.”
- **Section 2, p.5, Definition 2.1:** “Let Wα := {w ∈ {0, 1}N : ∑Nn=1(1 − wn) ≤ αN} be the set of all binary weight vectors indicating subsets where at most 100α% of the data has been dropped.” (Mathematical typesetting normalized.)
- **Section 3, p.8:** “This method approximates the maximal directional change in a statistic, e.g., [θ̂i(1N) − θ̂j(1N)], that can result from dropping a worst-case subset of data points (in our case, evaluations) of size at most ⌊αN⌋.”
- **Section 3, p.9:** “In other words, we refit the BT-model upon leaving out the subset of impactful evaluations identified by AMIP and check whether leaving out this subset induces a sign change in the difference of BT scores for the pair, (i, j).”
- **Section 3, p.9:** “Note that, when checking the robustness of a given pair (i, j), we allow matches between any two models (not only (i, j)) to be dropped.”
- **Section 3.1, p.10:** “The primary difference is that our analysis is conducted on tie-free data (we discard any matchups that were annotated as ties).”
- **Section 4.1, footnote 7, p.11:** “specifically, we use the arena-human-preference-55k dataset, the chatbot-arena-llm-judges dataset, and the mt-bench-human-judgments dataset.”
- **Section 4.1, p.12:** “We then run our method to check for top-k robustness, for k ∈ {1, 3, 5, 10, 20}”.
- **Section 4.3, p.14:** “Within both arenas (Chatbot Arena and MT-Bench), we find the sensitivity of the BT-based top-k rankings to worst-case data-dropping to be similar between human- and LLM-judged evaluations”.
- **Section 4.4, pp.14–15:** “For every instance where the top-k leaderboard changes due to dropped evaluations, we find that the affected matches always involve at least one of the models whose rank is altered”. Also: “we are unable to find instances where rankings were flipped by removing a small fraction of evaluations where neither of the affected models were involved.”
- **Appendix A, p.25:** “This final verification step ensures that our method does not return false positives.”
- **Appendix C, p.26:** “Figure 6 illustrates the relationship between the robustness of model rankings and the BT score gap between adjacent models, confirming that small score differences tend to coincide with greater sensitivity to worst-case data-dropping.”

### Method and protocol already established

- BT MLE cast as logistic regression; one reference score is fixed to zero for identification. The objective in Eq. (4) uses binary row weights to express deletion.
- Target is reversal of a pair's BT score difference; top-k **set membership** robustness is reduced to cross-boundary pair comparisons. This is not a new metric for the complete ordering within a top-k set.
- Candidate deletions use AMIP/influence scores; additive one-step Newton is also supported. Closest-score cross-boundary pairs are checked first, with early exit after a successful witness. Scores are computed using the full comparison graph, and deletion candidates are globally eligible.
- Refit the reduced BT data to verify successful flips. This proves existence of that non-robustness witness, assuming a valid converged fit. It does not prove that the found deletion set is minimal, nor does unsuccessful heuristic search certify robustness.
- Budget denominator is the total number of comparisons in the analyzed arena, not explicitly target-model exposure. Influential-match endpoint involvement is separately inspected.
- Human and LLM-judge analyses already appear for BOTH Arena and MT-Bench. The reported comparison must not be presented as a novel first human-versus-LLM deletion study.
- No independent predictive holdout is described for this finite-sample deletion audit; the question is sensitivity of rankings fitted to the analyzed comparison data.
- The text records named released datasets, but does not establish a strict common-support, identical-response, equal-weight human/GPT-4 analysis in the passages read. Different analyzed totals in Table 1 reinforce the need to verify matching rather than assume it. The table calls the evaluator “LLM”; do not silently relabel all of its rows as an exactly specified GPT-4 version/prompt.
- Author-reported code: https://github.com/JennyHuang19/IsRankingRobust (PDF p.3). Repository not accessed.

### Directly verified figures, with source inconsistencies retained

Table 1, PDF p.13, explicitly reports **sufficient deletions**, not certified optimal thresholds:

| Dataset | Evaluator as printed | Num Dropped | Frac Dropped as printed | Head-to-head Win Percent as printed |
|---|---|---|---|---|
| Chatbot Arena | Human | 9 out of 39716 | 0.000226 | 55.17% |
| Chatbot Arena | LLM | 4 out of 34297 | 0.000116 | 53.73% |
| MT-Bench | Human | 83 out of 2575 | 0.0322 | 62.75% |
| MT-Bench | LLM | 27 out of 2180 | 0.0124 | 51.72% |

These are table transcriptions, not reproduced experiments. No new empirical values are asserted here.

**Do not combine denominators carelessly:** Section 4.1 calls Arena 57,477 evaluations and MT-Bench 3,355 evaluations; Table 1 reports different, analyzed totals after the tie-free setup (39,716 and 2,575 for humans). The Section 4.2 Arena top-5 narrative says 20 deletions, whereas Figure 3 and Appendix B report 5. Figure 3 also has different counts for different k, and larger k is a different event, not a single cumulative rank-distance curve. The notes do not resolve those discrepancies by guessing which is correct.

**Numerical reproduction audit:** Before using Eqs. (11)/(14), verify the influence sign and scaling against the weighted likelihood in Eq. (4) and the general derivative in [3]/[4]; the printed logistic influence expression contains an extra variance factor relative to the usual score/Hessian presentation, and the nearby prose uses differing directional conventions. This is a flag for independent algebra/finite-perturbation checks, not a claim about what the uninspected code implements.

**Interpretation boundary:** Section 4.4 is an observation about the deletion witnesses found. It is not a theorem that off-target deletion cannot change a ranking. “At least one of the two flipped models” is also not identical to “the particular designated target appears.” Section 5's explanation attributing MT-Bench robustness to expert annotators and prompt quality is a hypothesis, not a controlled causal result.

## [4] Broderick, Giordano, Meager: AMIP foundations

Abstract URL: https://arxiv.org/abs/2011.14999

Fulltext URL: https://arxiv.org/pdf/2011.14999

### Actual read passages

- **Abstract, p.1:** “Our metric, the ‘Approximate Maximum Influence Perturbation,’ is based on the classical influence function, and is automatically computable for common methods including (but not limited to) OLS, IV, MLE, GMM, and variational Bayes.”
- **Introduction, p.3:** “for the cost of a single additional data analysis, we can provide an exact lower bound on the worst-case change in an analysis upon removing 100α% of the data”.
- **Introduction, p.4:** “this ‘noise’ is large when we have a high ratio of residual variance to regressor variance”. Also: “This noise can be large even when standard errors are small, because it does not disappear as N grows.”
- **Introduction, p.4:** “since our approximation is fundamentally local due to the Taylor expansion, practitioners may also consider global sensitivity checks”.
- **Section 2.2, p.8:** “our approximation to the Maximum Influence Perturbation ... centers on a first-order Taylor expansion ... around w⃗ = 1⃗.” (Ellipsis removes the list of related quantities; mathematical notation normalized.)
- **Section 2.2.1, p.9:** “we can use the Approximate Most Influential Set to conclusively demonstrate non-robustness.”

### Actionable notes

The smooth quantity of interest can be a parameter, its sign, a standard-error-adjusted significance quantity, or another differentiable functional. Sort directional influence scores to select a subset under the linearized budget. The general “find a small influential deletion subset, refit, demonstrate fragility” recipe is already established; extending it to score gaps does not independently establish method novelty. Refit gives a lower bound on the worst-case **effect**, hence a successful deletion count gives an upper bound on the true minimum flip **cost**. These are opposite bound directions on different quantities.

Sensitivity and sampling uncertainty are distinct. A small standard error, large dataset, or absence of gross outliers does not by itself rule out deletion sensitivity. Finite-sample approximation bounds have assumptions; they are not blanket certification for arbitrary BT graphs near separation or singularity. Author-reported R package: https://github.com/rgiordan/zaminfluence (PDF pp.3,6); not visited.

## [3] Koh and Liang: influence mechanics, not a ranking-deletion novelty claim

Abstract URL: https://arxiv.org/abs/1703.04730

Fulltext URL: https://arxiv.org/pdf/1703.04730

### Actual read passages

- **Abstract, p.1:** “we develop a simple, efficient implementation that requires only oracle access to gradients and Hessian-vector products.”
- **Section 2, p.2:** “Assume that the empirical risk is twice-differentiable and strictly convex in θ”.
- **Section 2.1, p.2:** “Since removing a point z is the same as upweighting it by ε = −1/n, we can linearly approximate the parameter change due to removing z without retraining the model”.
- **Section 3, p.3:** “avoid explicitly computing H−1 ... instead, we use implicit Hessian-vector products”. (Subscripts/line wrapping elided.)
- **Section 4, p.4:** “influence functions are asymptotic approximations of leave-one-out retraining under the assumptions that (i) the model parameters θ̂ minimize the empirical risk, and that (ii) the empirical risk is twice-differentiable and strictly convex.”

### Actionable notes

The core parameter derivative is minus inverse-Hessian times example gradient; a smooth target functional uses the chain rule. For ranking, use a smooth score gap rather than differentiate a discontinuous rank indicator. Sum-versus-average likelihood conventions and the deletion weight change must agree. The full-data Hessian captures indirect coupling through other comparisons, so influence need not be a head-to-head count or simple win/loss heuristic. Check approximation versus actual leave-out refits; non-convergence, curvature problems, nonsmoothness, and damping change the interpretation. This paper is general ML influence attribution, not itself the authorized corpus's direct Arena deletion study. No repository availability was independently verified.

## [5] Min et al.: target-only versus omnipresent manipulation precedent

Abstract URL: https://arxiv.org/abs/2501.17858

Fulltext URL: https://arxiv.org/pdf/2501.17858

### Actual read passages

- **Abstract, p.1:** “we propose omnipresent rigging strategies, exploiting the Elo rating mechanism of Chatbot Arena that any new vote on a battle can influence the ranking of the target model ... even if ... not directly involved in the battle.” (Target symbol elided.)
- **Section 2.2, p.2:** “This is achieved by submitting new votes, where each voting option is strategically selected to promote the target model’s ranking.”
- **Section 2.2, p.3:** “we divide 90% of the complete historical vote records as VH and the remainder as VO throughout all simulations.”
- **Section 3.2, footnote 2, p.3:** “Our measure of ‘votes’ corresponds to the ‘interactions’ ... where they use ‘votes’ to count only the battles predicted to involve mt.” (The cited author's identity is deliberately omitted here; no cited source was accessed.)
- **Section 3.2, p.4:** “we adopt the relative rating increase between mt and ... [the model] that ranks one position ahead of it ... as our rigging objective.” (Symbols and intervening formula elided.)
- **Section 5.2, p.5:** “When β = 0, it indicates that no mt will be sampled for new battles.”

### Actionable notes

This is an **addition/injection** threat model, not deletion of fixed historical evaluations. It already contrasts target-only opportunities with globally available manipulation, and explicitly discusses the difference between all interactions and target-involving votes. Merely observing that target exposure changes the meaning of a global budget has conceptual precedent even when the proposed deletion protocol differs.

Threat models vary access to historical votes, model identity, sampling distribution, and concurrent honest votes. The 90/10 split is historical/concurrent simulation data, NOT a standard ranking generalization train/test split. Its BT-based objective uses a target-versus-neighbor score gap. Do not transfer its attack magnitudes to deletion or conflate online Elo updates with a full BT refit.

The exact allowed abstract states author-reported code at https://github.com/sail-sg/Rigging-ChatbotArena; not visited. No empirical vote-rigging numbers are needed for the proposed study's positioning.

## [2] Zheng et al.: matched human/GPT-4 protocol and judge pitfalls

Abstract URL: https://arxiv.org/abs/2306.05685

Fulltext URL: https://arxiv.org/pdf/2306.05685

### Actual read passages

- **Section 2.2, pp.3–4:** “We create MT-bench, a benchmark consisting of 80 high-quality multi-turn questions.” The paper enumerates writing, roleplay, extraction, reasoning, math, coding, STEM knowledge, and humanities/social-science knowledge.
- **Section 3.4, p.6:** “call a judge twice by swapping the order of two answers and only declare a win when an answer is preferred in both orders. If the results are inconsistent after swapping, we can call it a tie.”
- **Section 3.5, p.6:** “the necessity of displaying a complete conversation to enable the LLM judge to better grasp the context.”
- **Section 4.1, p.7:** “We generate answers for all 80 questions with 6 models ... We then use 2 kinds of judges: LLM judges and 58 expert-level human labelers.”
- **Section 4.1, p.7:** “We let LLM judges evaluate all pairs and let each human evaluate at least 20 random multi-turn questions.”
- **Section 4.1, p.7:** “We define the agreement between two types of judges as the probability of randomly selected individuals (but not identical) of each type agreeing on a randomly selected question.”
- **Table 5 caption, p.8:** “S1 includes non-tie, tie, and inconsistent (due to position bias) votes and counts inconsistent as tie; S2 only includes non-tie votes.”
- **Appendix C.1, p.23:** “When human’s vote differs from GPT-4, we additionally show GPT-4’s judgment ... and ask the user ... whether GPT-4’s judgment is reasonable.”

### Actionable notes

The paper supplies controlled human and LLM judgments on generated responses and already compares judge agreement. Strictly matched deletion analysis should freeze question ID, full response pair, turn, and unordered model pair, then specify how repeated human labels are aggregated or weighted. Do not copy one GPT-4 judgment into multiple statistically independent rows just because multiple humans rated that comparison.

Record GPT-4 judge/version, prompt, pairwise-versus-single-score setup, reference guidance, answer-order swapping, inconsistent-order handling, and ties. The paper diagnoses position bias, verbosity bias, limited reasoning/grading ability, and possible self-enhancement; it explicitly says its evidence does not settle self-enhancement causally. Agreement is not probability calibration, deletion robustness, or a proof of truth.

Human-versus-GPT-4 matching is not just the same benchmark name. Restricting to comparisons where both give decisive labels changes the population; report common support, exclusions, tie rates, and a tie-preserving sensitivity analysis. Preserve original independent human choices rather than post-GPT-feedback revisions if those are available; the paper documents the feedback interface, but the actual released schema was not inspected here.

For uncertainty, prompt/conversation grouping matters because turns and model pairs share prompts. The human collection allows repeats and some skipped questions; judge missingness should not be silently treated as random. Author-reported questions/votes/code: https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge (abstract and PDF p.1); not accessed.

## [1] Chiang et al.: ranking estimand and uncertainty context

Abstract URL: https://arxiv.org/abs/2403.04132

Fulltext URL: https://arxiv.org/pdf/2403.04132

### Actual read passages

- **Section 3.2, p.3:** “we employ non-uniform sampling to concentrate votes on model pairs that have similar performance due to higher uncertainty.”
- **Section 4, p.4:** “the BT coefficients are better for the purpose of statistical estimation.”
- **Section 5, p.5:** “We perform the inverse weighting by P(At) because this allows us to target a score with a uniform distribution over A.”
- **Section 5, p.5:** “we choose to deploy the sandwich intervals due to their smaller size in large samples.”
- **Section 5, p.5:** “we report an approximate ranking for each model that accounts for the uncertainty in the estimation of the score.”

### Actionable notes

Arena is adaptively/nonuniformly sampled, so per-model exposure is not uniform. Its statistical target and sampling weights matter. The paper distinguishes BT scoring from earlier online Elo and gives uncertainty-aware rankings, not just a sorted point estimate. It discusses both bootstrap and robust sandwich uncertainty methods.

A deletion audit should state whether it uses unweighted tie-free BT (as in Huang) or a weighted/tie-aware platform-like estimator; these need not give the same baseline ordering. A point-estimate flip is not equivalent to changing a statistically separated conclusion. Frozen snapshots, model/version names, sampling/filtering, weights, ties, baseline margins, and uncertainty must be reported. Affine display transformations do not change score ordering, but likelihood weights and tie treatment can. The abstract/platform promise of open code/data was read; no live leaderboard, notebook, or repository was accessed.

## Positioning: known, overlapping, and only potentially incremental

### Already known within the authorized corpus

1. First-order influence approximates deletion effects on smooth fitted quantities [3].
2. Adversarial subset dropping under a global fraction budget, AMIP selection, minimum-inducing proportion concepts, and refit-based non-robustness witnesses are established [4].
3. BT score-gap/top-k deletion fragility on Arena and MT-Bench, human/LLM comparisons, affected-model involvement, and score-gap relationships are already central to Huang [6].
4. Target-only versus omnipresent ranking manipulation and all-interactions versus target-votes accounting have precedent in an injection setting [5].
5. Controlled human/GPT-4 comparison, order swapping, tie-conditioned agreement, and judge failure modes are already studied [2]; Arena weighting and uncertainty are established [1].

### Key distinction: normalization is not a new feasible deletion set

Let N be the number of original retained comparison events, Et the set involving target t, Nt = |Et|, and D a deleted set. Specify these counts before any deletion.

- **Global fraction:** |D|/N.
- **Exposure-normalized total deletion cost:** |D|/Nt. If D is still globally eligible, this merely rescales the same successful set. It is NOT necessarily the fraction of target events removed, and can exceed one.
- **Actual fraction of target exposure removed:** |D ∩ Et|/Nt.
- **Target-incident feasible deletions:** constrain D to be a subset of Et.
- **Off-target feasible deletions:** constrain D to the complement of Et. For a pair (i,j), distinguish “neither endpoint” from “not involving designated target t.”

At integer budget b, global feasible sets and target-incident feasible sets differ; relabeling b/N as b/Nt does not change the optimizer. For a pairwise target, report Ni, Nj, union exposure |Ei ∪ Ej|, and head-to-head count where relevant rather than choosing a convenient denominator after seeing results. For global top-k membership events, specify which endpoint/target supplies any exposure denominator. Count original comparison events, not duplicated likelihood rows introduced for symmetric/tie encoding.

### Defensible but modest proposed contribution

An **exposure-aware, budget-controlled robustness audit**: hold the ranking objective, attack search effort, data support, and fitting protocol fixed; distinguish global versus target-incident versus off-target action sets; report both absolute and normalized budgets; compare human and GPT-4 labels on exactly matched MT-Bench responses; then test whether any resulting pattern transfers to a specified NBA comparison graph.

This is a possible extension of Huang, NOT evidence of a novel influence method or a first deletion-fragility result. Adding NBA alone is domain breadth. A stronger contribution would be a replicated explanation of when exposure normalization changes cross-dataset conclusions after score margins, sample size, graph structure, and judge filtering are controlled. The result is not known from this reading and must not be predicted as an empirical fact.

No 'NBA' occurrence was found by local literal inspection of the six authorized extracted fulltexts. This is not a comprehensive literature claim. No NBA dataset URL, season, split, availability, or numerical result was verified; none was fetched. Nothing here establishes priority outside the authorized corpus.

## Recommended next experiments (planning only; not executed)

1. **Reproduce before comparing.** Freeze exact Arena snapshot/model versions and Huang v1's tie-free BT protocol. Reconcile raw versus retained totals and the top-5 narrative/figure discrepancy before using reported percentages. Every claimed flip needs an actual reduced-data refit and convergence check.
2. **Separate two research questions.** First hold deletion set fixed and report b, b/N, b/Nt, and |D∩Et|/Nt to expose pure normalization effects. Then change feasible sets (global, target-incident, neither target, neither endpoint) at equal integer b and equal search effort. Compute effects relative to the same full ranking, not separate target-subgraph fits. Global search should not appear weaker merely because an incident-only search happened to find a better witness; include feasible restricted candidates in the global candidate pool.
3. **Use strong explicit comparators.** Random deletions, exposure/edge-stratified random deletions, directional outcome heuristics, Huang-style one-shot AMIP, additive one-step Newton, and a refit-updated greedy search are useful comparisons. On small reduced graphs, exact enumeration can reveal missed flips and bound optimality gaps. Baseline search effort and refit budgets must be reported.
4. **Match human/GPT-4 labels tightly.** Same prompt, response texts, turn, model pair, support, and weighting. Report repeated-rater aggregation, missingness, original-versus-post-feedback human labels, position-swap consistency, tie policy, and decisive-only selection effects. Compare paired budgets/curves with prompt-clustered uncertainty, not just two unrelated percentages. Separate rank margin effects from evaluator effects.
5. **Metrics and honest bounds.** Primary: smallest refit-verified deletion count FOUND to reverse a preregistered pairwise margin or change a specified top-k set. Report absolute count, full-data fraction, exposure normalization, eligible-pool size, target-hit fraction, original score gap, and success at fixed budgets. Secondary: margin-change curves, search cost, and approximation-versus-refit discrepancies. A successful count upper-bounds the true minimum cost. “No flip found” is not “certified robust.” Distinguish point-rank flips, top-k membership changes, and confidence-qualified ordering changes.
6. **Numerical and statistical calibration.** Verify score gauge, objective scaling, IF sign, optimizer tolerances, and finite-MLE existence. Deletion can disconnect the graph or cause separation even when an undirected comparison graph remains connected. Do not count solver failure or unidentified scores as a valid flip. If regularization is used, fix its convention so deletion does not accidentally change penalty strength. Report uncertainty separately from adversarial robustness. Random controls should preserve relevant exposure/edge structure; resampling should respect shared prompts/users where the available data permit.
7. **NBA as a specified external-validity check, not a novelty assertion.** Before any future data acquisition, choose and document an authorized data source, seasons, regular-season/playoff policy, team identities, game as the deletion unit, home advantage treatment, and temporal nonstationarity. Keep season-specific rankings distinct unless a pooling model is declared. Match margins/exposures/graph density when comparing with LLM graphs; empirical competitiveness and schedule structure can otherwise dominate apparent domain differences. No particular NBA protocol or result is claimed to be present in these six papers.
8. **Splits and generalization claims.** A frozen finite-sample ranking sensitivity audit does not inherently require a train/test split. If search rules or budgets are tuned using outcomes, use separate development snapshots and held-out snapshots/seasons for the claimed transferable findings. If predictive validity or judge probability calibration is claimed, add an explicit held-out protocol; neither rank flips nor pairwise agreement alone establishes it.

## Fetch failures and limitations

- Network fetch failures: **none** (six exact abstract pages and six PDFs, all HTTP 200).
- No external code/data schema, NBA source, or live leaderboard was checked because the authorization excludes those accesses.
- The full PDFs were fetched, but reading was targeted rather than an exhaustive analysis of every appendix/reference.
- This report cannot rule out additional already-published related work and makes no claim to identify an excluded paper.

## Verbatim abstracts and retrieved metadata

The following section is populated directly from the exact allowed abstract pages' citation metadata, preserving what was retrieved rather than reconstructing abstracts from memory.

### 2403.04132

Access URL: https://arxiv.org/abs/2403.04132

Title: Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference

Authors (verbatim citation metadata order): Chiang, Wei-Lin; Zheng, Lianmin; Sheng, Ying; Angelopoulos, Anastasios Nikolas; Li, Tianle; Li, Dacheng; Zhang, Hao; Zhu, Banghua; Jordan, Michael; Gonzalez, Joseph E.; Stoica, Ion

Original date: 2024/03/07; online date: 2024/03/07

> Large Language Models (LLMs) have unlocked new capabilities and applications; however, evaluating the alignment with human preferences still poses significant challenges. To address this issue, we introduce Chatbot Arena, an open platform for evaluating LLMs based on human preferences. Our methodology employs a pairwise comparison approach and leverages input from a diverse user base through crowdsourcing. The platform has been operational for several months, amassing over 240K votes. This paper describes the platform, analyzes the data we have collected so far, and explains the tried-and-true statistical methods we are using for efficient and accurate evaluation and ranking of models. We confirm that the crowdsourced questions are sufficiently diverse and discriminating and that the crowdsourced human votes are in good agreement with those of expert raters. These analyses collectively establish a robust foundation for the credibility of Chatbot Arena. Because of its unique value and openness, Chatbot Arena has emerged as one of the most referenced LLM leaderboards, widely cited by leading LLM developers and companies. Our demo is publicly available at \url{https://chat.lmsys.org}.

### 2306.05685

Access URL: https://arxiv.org/abs/2306.05685

Title: Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena

Authors (verbatim citation metadata order): Zheng, Lianmin; Chiang, Wei-Lin; Sheng, Ying; Zhuang, Siyuan; Wu, Zhanghao; Zhuang, Yonghao; Lin, Zi; Li, Zhuohan; Li, Dacheng; Xing, Eric P.; Zhang, Hao; Gonzalez, Joseph E.; Stoica, Ion

Original date: 2023/06/09; online date: 2023/12/24

> Evaluating large language model (LLM) based chat assistants is challenging due to their broad capabilities and the inadequacy of existing benchmarks in measuring human preferences. To address this, we explore using strong LLMs as judges to evaluate these models on more open-ended questions. We examine the usage and limitations of LLM-as-a-judge, including position, verbosity, and self-enhancement biases, as well as limited reasoning ability, and propose solutions to mitigate some of them. We then verify the agreement between LLM judges and human preferences by introducing two benchmarks: MT-bench, a multi-turn question set; and Chatbot Arena, a crowdsourced battle platform. Our results reveal that strong LLM judges like GPT-4 can match both controlled and crowdsourced human preferences well, achieving over 80% agreement, the same level of agreement between humans. Hence, LLM-as-a-judge is a scalable and explainable way to approximate human preferences, which are otherwise very expensive to obtain. Additionally, we show our benchmark and traditional benchmarks complement each other by evaluating several variants of LLaMA and Vicuna. The MT-bench questions, 3K expert votes, and 30K conversations with human preferences are publicly available at https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge.

### 1703.04730

Access URL: https://arxiv.org/abs/1703.04730

Title: Understanding Black-box Predictions via Influence Functions

Authors (verbatim citation metadata order): Koh, Pang Wei; Liang, Percy

Original date: 2017/03/14; online date: 2020/12/29

> How can we explain the predictions of a black-box model? In this paper, we use influence functions -- a classic technique from robust statistics -- to trace a model's prediction through the learning algorithm and back to its training data, thereby identifying training points most responsible for a given prediction. To scale up influence functions to modern machine learning settings, we develop a simple, efficient implementation that requires only oracle access to gradients and Hessian-vector products. We show that even on non-convex and non-differentiable models where the theory breaks down, approximations to influence functions can still provide valuable information. On linear models and convolutional neural networks, we demonstrate that influence functions are useful for multiple purposes: understanding model behavior, debugging models, detecting dataset errors, and even creating visually-indistinguishable training-set attacks.

### 2011.14999

Access URL: https://arxiv.org/abs/2011.14999

Title: An Automatic Finite-Sample Robustness Metric: When Can Dropping a Little Data Make a Big Difference?

Authors (verbatim citation metadata order): Broderick, Tamara; Giordano, Ryan; Meager, Rachael

Original date: 2020/11/30; online date: 2023/07/19

> Study samples often differ from the target populations of inference and policy decisions in non-random ways. Researchers typically believe that such departures from random sampling -- due to changes in the population over time and space, or difficulties in sampling truly randomly -- are small, and their corresponding impact on the inference should be small as well. We might therefore be concerned if the conclusions of our studies are excessively sensitive to a very small proportion of our sample data. We propose a method to assess the sensitivity of applied econometric conclusions to the removal of a small fraction of the sample. Manually checking the influence of all possible small subsets is computationally infeasible, so we use an approximation to find the most influential subset. Our metric, the "Approximate Maximum Influence Perturbation," is based on the classical influence function, and is automatically computable for common methods including (but not limited to) OLS, IV, MLE, GMM, and variational Bayes. We provide finite-sample error bounds on approximation performance. At minimal extra cost, we provide an exact finite-sample lower bound on sensitivity. We find that sensitivity is driven by a signal-to-noise ratio in the inference problem, is not reflected in standard errors, does not disappear asymptotically, and is not due to misspecification. While some empirical applications are robust, results of several influential economics papers can be overturned by removing less than 1% of the sample.

### 2501.17858

Access URL: https://arxiv.org/abs/2501.17858

Title: Improving Your Model Ranking on Chatbot Arena by Vote Rigging

Authors (verbatim citation metadata order): Min, Rui; Pang, Tianyu; Du, Chao; Liu, Qian; Cheng, Minhao; Lin, Min

Original date: 2025/01/29; online date: 2025/08/10

> Chatbot Arena is a popular platform for evaluating LLMs by pairwise battles, where users vote for their preferred response from two randomly sampled anonymous models. While Chatbot Arena is widely regarded as a reliable LLM ranking leaderboard, we show that crowdsourced voting can be rigged to improve (or decrease) the ranking of a target model $m_{t}$. We first introduce a straightforward target-only rigging strategy that focuses on new battles involving $m_{t}$, identifying it via watermarking or a binary classifier, and exclusively voting for $m_{t}$ wins. However, this strategy is practically inefficient because there are over $190$ models on Chatbot Arena and on average only about $1\%$ of new battles will involve $m_{t}$. To overcome this, we propose omnipresent rigging strategies, exploiting the Elo rating mechanism of Chatbot Arena that any new vote on a battle can influence the ranking of the target model $m_{t}$, even if $m_{t}$ is not directly involved in the battle. We conduct experiments on around $1.7$ million historical votes from the Chatbot Arena Notebook, showing that omnipresent rigging strategies can improve model rankings by rigging only hundreds of new votes. While we have evaluated several defense mechanisms, our findings highlight the importance of continued efforts to prevent vote rigging. Our code is available at https://github.com/sail-sg/Rigging-ChatbotArena.

### 2508.11847v1

Access URL: https://arxiv.org/abs/2508.11847v1

Title: Dropping Just a Handful of Preferences Can Change Top Large Language Model Rankings

Authors (verbatim citation metadata order): Huang, Jenny Y.; Shen, Yunyi; Wei, Dennis; Broderick, Tamara

Original date: 2025/08/16; online date: 2025/08/16

> We propose a method for evaluating the robustness of a widely used LLM ranking system -- the Bradley--Terry ranking system -- to dropping a worst-case very small fraction of evaluation data. Our approach is computationally fast and easy to adopt. When we apply our method to matchups from two popular human-preference platforms, Chatbot Arena and MT-Bench, we find that the Bradley--Terry rankings of top-performing models are remarkably sensitive to the removal of a small fraction of evaluations. Our framework also identifies the specific evaluations most responsible for such ranking flips, allowing for inspections of these influential preferences. We observe that the rankings derived from MT-Bench preferences are notably more robust than those from Chatbot Arena, likely due to MT-bench's use of expert annotators and carefully constructed prompts. Finally, we find that rankings based on crowdsourced human-evaluated systems are just as sensitive as those based on LLM-as-a-judge evaluations, where in both, dropping as little as 0.02% of the total evaluations in the dataset can change the top-ranked model.
