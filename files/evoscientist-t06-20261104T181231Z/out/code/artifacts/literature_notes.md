# Bounded literature evidence: stability of pairwise-comparison leaderboards

Prepared 2026-11-04 UTC. **Evidence-only assignment: no experiments, model fitting, dataset downloads, or code implementation were performed.** All numerical findings below are explicitly attributed to the papers; none are new computed research results.

## 1. Scope, access rules, and reading inventory

Read `/work/research_request.md` first. Fetched only the **six explicitly permitted arXiv PDFs** below, by the supplied IDs, and official NeurIPS template/policy resources. No keyword searches, citation/cited-by queries, related-paper services, forbidden-paper identity inference, or links to other works were used. Bradley–Terry 1952 and Singh 2504.20879 are permitted in the brief but **were not fetched or consulted** and are not independently summarized or added to the bibliography. This is not a comprehensive literature review or an unrestricted novelty clearance.

Each PDF and its `pdftotext -layout` extraction is saved under `/work/artifacts/literature/`. PDF page numbers below are physical PDF pages (matching the printed numbering for the principal passages). Reading was targeted, **not a claim of having read every page**. The extractor processes the complete document, including references; bibliography entries were not followed. A structural page-start locator also exposed short reference-page snippets inside permitted PDFs; those were not used as independent evidence or pursued. No recognized prohibited source was encountered outside the explicitly permitted source set. See `access_and_failure_log.md` for exposure and failures.

| Ref. | Actually fetched URL and observed version | Sections/passages actually read substantively |
|---|---|---|
| [1] | https://arxiv.org/pdf/2011.14999 — **v5**, arXiv stamp 19 July 2023, manuscript 20 July 2023 | Abstract; §1; §2 through §2.3, pp. 1–11; §3.2.1–3.2.2, pp. 18–21; §3.3, pp. 24–27. Extraction lines 1–701, 1060–1283, 1445–1616. Did not audit appendix proofs or reproduce §4 economics applications. |
| [2] | https://arxiv.org/pdf/1703.04730 — **v3**, 29 December 2020; printed ICML 2017 | Abstract; §1; §2.1–2.3; §3; §4.1 and beginning of §4.2, pp. 1–4; reproducibility paragraph on p. 9. Not the full downstream case studies. |
| [3] | https://arxiv.org/pdf/2501.17858 — **v2**, 10 August 2025; printed ICML 2025 | Abstract; §§1–7, pp. 1–8, with some adjacent §8/impact text exposed in the extraction; p. 16 appendix passages and Algorithm 1. Did not audit the full classifier-training appendix or regenerate attacks. |
| [4] | https://arxiv.org/pdf/2508.11847v1 — **v1 pinned**, arXiv stamp 16 August 2025, manuscript 19 August 2025 | Abstract; §§1–4.4, pp. 1–15; §4.5 and §5 discussion, pp. 17–18; Appendix A, pp. 23–25. Selected prompt-table text appeared, but no qualitative prompt audit was performed. Also visually inspected p. 9 to verify the printed Eq. (11); saved `huang_v1_page09.png`. |
| [5] | https://arxiv.org/pdf/2306.05685 — **v4**, 24 December 2023; printed NeurIPS 2023 Datasets and Benchmarks | Abstract; §§1–4, pp. 1–8; Appendix C, pp. 23–24. Some neighboring benchmark-result table text was exposed. No independent prompt-generation or judge runs. |
| [6] | https://arxiv.org/pdf/2403.04132 — **v1**, 7 March 2024 | Abstract; §§1–5, pp. 1–5; §6 through vote-quality passages on pp. 6–7; Appendix A, p. 15 (with beginning of B exposed). Did not audit the full nonparametric extension or annotation examples. |

The unversioned supplied IDs returned the versions above; they must not silently be described as their original 2020/2017/2025 submissions. Exact bytes and SHA256s are in `/work/artifacts/source_manifest.json`. The locally curated `/work/paper/permitted_literature.bib` contains only these six sources and records consulted-version dates.

## 2. Main finding: the core application already appears in permitted work

Huang et al., **“Dropping Just a Handful of Preferences Can Change Top Large Language Model Rankings”** [4], already applies Broderick-style AMIP to BT score differences; defines pairwise and top-k deletion robustness; checks a candidate deletion by exact refitting; and compares **Arena versus MT-Bench**, including human versus LLM judgments. Therefore none of these alone is a defensible new contribution relative to the permitted evidence:

- Showing that a few worst-case deletions can change the leading BT model.
- Adapting an inverse-Hessian influence score to BT margins and sorting influential preferences.
- Treating live/crowdsourced Arena and curated/expert MT-Bench as two evaluation designs.
- Comparing human and model-judge sensitivity on these datasets.

This conclusion uses only explicitly permitted [4], not any inference about the unspecified restricted paper. The restriction prevents a global originality claim. A useful follow-up must state a narrower, independently measured contribution and distinguish replication, methodological extension, and conditional interpretation.

## 3. Broderick, Giordano & Meager: the methodological baseline that must be credited

**“An Automatic Finite-Sample Robustness Metric: When Can Dropping a Little Data Make a Big Difference?”** [1]. Starter label is Broderick et al. (2020); the actually read file is v5 (2023).

### 3.1 Question and exact estimand

§2 (pp. 5–6), Definitions 1–2 and §2.2 (pp. 8–9), distinguish:

- **Maximum Influence Perturbation (MIP):** largest directional change in a scalar quantity of interest after deleting at most `floor(alpha*N)` observations.
- **Most Influential Set:** subset attaining that change.
- **Perturbation-Inducing Proportion:** smallest deletion fraction producing a specified change Delta.
- Their **approximate** counterparts, including AMIP, which solve a first-order surrogate rather than the original combinatorial problem.

Useful exact evidence span: “removing at most” is not necessary to assume an exactly saturated budget; §2.1 defines weights with “No more than” the allowed zeros. §2.2's Eq. (6) includes only beneficial signed scores. Do not force deletion of harmful-to-the-objective points simply to fill the budget.

Represent the analysis by estimating equations `sum_n w_n G(theta, d_n)=0`; all original weights are one and a deletion sets a weight to zero. The scalar target `phi(theta,w)` can depend directly on the data weights as well as on fitted parameters (§2.1, pp. 7–8). This permits sensitivity of a confidence bound, not merely a coefficient. Differentiability is essential; use a smooth **score margin**, not a discontinuous rank integer, as the local target.

### 3.2 Approximation and computational recipe

§2.2, Eqs. (5)–(6):

`phi(theta_hat(w),w) ≈ phi_hat + sum_n (w_n - 1)*psi_n`.

For increasing phi, delete up to `floor(alpha*N)` points with the most negative `psi_n`, stopping if no negative scores remain. For reducing a positive BT margin `m_ij = theta_i-theta_j`, use `phi=-m_ij` or consistently reverse the sorting direction. The procedure needs one original fit, influence calculations and a sort; it does not exhaustively optimize all subsets.

§2.2.2, Eqs. (7)–(10), derives the derivative by the chain rule and implicit differentiation. A direct weight dependence in the target contributes its own derivative. Omitting it is wrong for a target such as a CI endpoint. Full-rank estimating-equation Jacobians are assumed. Supporting span: “with full-rank Jacobian matrix” (p. 10).

### 3.3 Exact refitting: what it establishes and what it does not

§2.2.1, p. 9: refit after dropping the approximate most-influential subset. The achieved change is an **exact finite-sample lower bound on the maximum possible directional change**, because that particular subset is feasible. Supporting span: “conclusively demonstrate non-robustness”.

Consequently, a valid fitted ranking flip at `b` deletions gives:

- A witness that non-robustness occurs at that budget.
- An **upper bound** `b/N` on the *minimum* fraction needed to flip.
- Not a proof that the chosen subset is optimal, and not a robustness certificate when the candidate fails.

The linearized change itself is not generally a certified upper or lower bound on the true worst case. Do not call the AMIP-estimated threshold the exact minimum deletion budget. This distinction is central, not a minor caveat.

### 3.4 Sampling error and worst-case sensitivity are different questions

§3.2.1–3.2.2 (pp. 18–21) decomposes AMIP into a noise term and a tail-shape term. Under the paper's regularity/IID setting, the noise estimates the limiting standard deviation of the root-N-scaled target, whereas an ordinary standard error shrinks by an additional root-N factor. At fixed fraction alpha, sensitivity need not vanish as N grows; small standard errors do not rule it out. Supporting spans: “AMIP sensitivity does not vanish” and “standard errors are different”.

For the proposed leaderboard study this means: report both ordinary uncertainty in the **unperturbed target** and worst-case perturbation sensitivity. An ordering between nearly tied models can flip without contradicting valid conventional inference. Conversely, a point-estimate flip is not automatically a statistically significant reversal or evidence of platform misconduct.

§2.3 (p. 11) separately formulates changing sign, changing significance, and obtaining a significant opposite sign. That is a ready baseline for a study separating ordinal flips from scientifically meaningful changes. This distinction itself must be credited to [1], not claimed as a new generic sensitivity concept.

### 3.5 Assumptions and limits of the theory

§3.3, Theorem 1 (pp. 24–27), gives a uniform **finite-sample** error bound under compactness, smoothness, nonsingularity, boundedness and Lipschitz assumptions, plus smoothness of the target. For sufficiently small alpha, the displayed approximation-error bound is order alpha while the effect bound is order square-root-alpha. The constants are problem dependent.

The authors explicitly caution that the constants need not be practically useful and the sufficiently-small-alpha condition can in theory require alpha below `1/N`, making it vacuous for an actual deletion. Do not advertise a useful certified BT ranking radius from this theorem without verifying its assumptions and computing an applicable bound. Supporting spans: “do not expect the constants to be useful in practice” and “resulting in a vacuous statement” (p. 26).

§3.3.2 cautions against large deletion fractions and boundary parameters. It discusses a failed variance/hypervariance approximation and stresses actual refitting. An NA approximate perturbation-inducing proportion is not a proof of global robustness. These observations motivate explicit approximation-error diagnostics and invalid-fit reporting in the leaderboard setting.

**Code availability as stated, not inspected:** §§1–2 name the `zaminfluence` R package and print `https://github.com/rgiordan/zaminfluence`. No repository or dependency links were followed.

**Positioning difference:** applying this already-general subset-deletion machinery to a low-dimensional BT fit is an application/replication (and [4] already performs it). A more specific contribution could measure dependence-aware deletion units, tie-preserving stability or calibrated uncertainty-aware outcomes on pinned datasets; it would not constitute inventing AMIP or the refit lower-bound argument.

## 4. Koh & Liang: influence functions, not a new worst-case ranking objective

**“Understanding Black-box Predictions via Influence Functions”** [2], §§2–3 (pp. 2–4), derives upweighting influence

`d theta_hat_epsilon,z / d epsilon = -H_mean^{-1} grad ell_z`

and propagates it to a test loss. A leave-one-out change uses epsilon `-1/N`; changing an input or a discrete label can be approximated by a difference of upweighting influences (§2.2). Supporting span: “discrete label changes”. The mean-loss normalization here differs from unit record weights in a summed BT likelihood; mixing them can introduce a factor-N error.

§3 avoids explicit matrix inversion with inverse-Hessian-vector products, conjugate gradients or stochastic estimation. §4.1 compares predicted influence with actual leave-one-out retraining on MNIST; this is an approximation-validation protocol, not a ranking robustness certificate. §4.2 discusses lack of convexity/convergence and damping. For modest BT model counts a direct reduced-system solve is a simpler CPU baseline than reproducing the paper's large-neural-network machinery; this is a planning recommendation, not a reported experiment.

**Code availability as stated:** reproducibility paragraph, p. 9, gives GitHub and Codalab short links (`http://bit.ly/gt-influence`, `http://bit.ly/cl-influence`); neither was opened or resolved.

**Positioning difference:** [2] centers prediction attribution/training-data changes. Worst-case finite-fraction subset objectives, empirical leaderboard top-k outcomes and uncertainty-aware BT stability need separate formulation; [1] and [4] already supply much of that formulation. Label corruption is a different feasible operation from deletion even when both use local influence.

## 5. Min et al.: vote insertion and realistic attacker constraints

**“Improving Your Model Ranking on Chatbot Arena by Vote Rigging”** [3], §§2–3 (pp. 2–4), studies **submitting new manipulated votes**, not deleting a selected historical subset. Its threat model distinguishes historical-vote versus score-only access, real-name versus anonymous models, known versus unknown sampling and concurrent honest votes. Supporting span: “by submitting new votes”.

Target-only baselines act when a target is identified; passive options include tie, abstention, random or normal votes. Omnipresent strategies can act on battles that do not directly involve the target, exploiting coupling through the global BT fit. Omni-BT uses the fitted-score objective; Omni-On uses public scores and an online-Elo surrogate. Do not conflate a static adversarial deletion audit with a feasible online attack with unknown identities.

**Evaluation actually read:** §2.2 reports roughly 1.7M votes over 129 models and a **90% historical / 10% other-user vote split** for simulations. §4 has an idealized real-name setting; §5 changes identity accuracy, sampling and concurrent user votes; §6 narrows to 25 models and roughly 23K English votes, reporting target ranking improvements. Some classifier experiments initially reuse training prompts, then separately test unseen prompts/unrecognized models (§6.2). Its realistic classifier setup uses two A100 GPUs for fine-tuning (§6.1), outside this task's CPU-only reproduction budget. The paper says it avoided contaminating real platform records; no live attack is appropriate here.

§7 and Appendix E/Algorithm 1 discuss duplicate-vote detection, user anomaly testing and historical-win-probability vote filtering. Threshold filtering is not established as a universal defense and can preferentially remove genuine minority/upset judgments. The latter concern is our evaluation recommendation: measure clean-data effects as well as attack reduction before treating filtering as a robustness improvement.

**Code status:** the abstract says code is publicly available, but no code repository was inspected or independently verified in this assignment. The full 1.7M history and de-anonymization pipeline were not downloaded.

**Positioning difference:** a bounded **historical-label replacement** or session-level removal study with fixed model identities is a different threat model, not a reproduction of anonymous online vote insertion. Normalize budget by honest base records and distinguish interactions, submitted votes and actually altered records. “A few votes matter” alone is already a result in [3] and [4].

## 6. Huang et al. v1: closest permitted comparator and reproduction hazards

[4], §§2–3, defines binary/tie-free BT maximum likelihood with one score fixed to zero, then top-k **set membership** robustness. A within-top-k reorder need not change the top-k set. Boundary comparisons between members and nonmembers number `k*(M-k)`; the procedure tries close margins early and allows removal of matches between any models. Candidate sets come from AMIP or additive one-step Newton approximations; actual refits verify flips (§3 and Appendix A). Supporting span: “always performs a refitting”.

§3.1 explicitly **discards ties**. Its strictly increasing affine display-score transformation does not affect order, but tie removal can. This is an important distinction between a raw BT audit and a reproduction of an operational leaderboard.

### Reported results and exact denominators

Table 1, p. 13, reports the following **sufficient, found** top-1 deletion witnesses; these are paper results, not recomputed here:

| Data/judge | Deleted / analyzed comparisons | Fraction printed |
|---|---:|---:|
| Arena, human | 9 / 39,716 | 0.000226 |
| Arena, LLM | 4 / 34,297 | 0.000116 |
| MT-Bench, human | 83 / 2,575 | 0.0322 |
| MT-Bench, LLM | 27 / 2,180 | 0.0124 |

§4.1 instead describes **57,477 total Arena evaluations** and **3,355 total MT-Bench evaluations** before analysis-specific filtering. Never divide a found deletion count by the raw-release total while comparing it with a filtered-denominator result. The repository name “55k” is not a sufficient sample-size definition. No train/test split is needed for its descriptive full-historical-data deletion audit; no held-out robustness validation protocol was identified in the passages read.

**Internal inconsistency to resolve before reproduction claims:** §4.2 says **20 evaluations** change Arena top-5, while Figure 3's caption and §4.5 discuss **5** human Arena evaluations changing top-5. The same v1 gives the top-1 witness in Table 1 with its filtered denominator but approximate headline percentages elsewhere. Preserve table/caption provenance rather than selecting a convenient number or presenting one as an exact minimum. Do not silently “repair” the paper without a reproduction.

**Printed-equation audit:** p. 9 Eq. (11), repeated as Appendix A Eq. (14), includes an extra multiplicative `p_n*(1-p_n)` next to `x_n*(y_n-p_n)`, despite defining `V=diag(p_n*(1-p_n))` already. This is visually verified in saved `huang_v1_page09.png`, not just a text-extraction conjecture. Differentiating the stated unit-weight, summed logistic likelihood instead gives

`d theta_hat / d w_n = (X' V X)^{-1} x_n*(y_n-p_n)`

in the identified/reduced coordinates. This algebraic check follows the estimating-equation derivative in [1], Eq. (10), and the upweighting formula in [2]; it is **our consistency check**, not a measured software bug. Sorting/sign wording also differs between the main expression and nearby footnote/appendix prose. Independently fix the target direction and verify tiny positive/negative weight changes and exact refits before adopting any printed formula. The paper's code was not inspected, so **no claim is made that its implementation uses the discrepant expression or that its published results are invalid**.

§4.2/§5 attribute Arena–MT differences plausibly to experts and curated prompts, but datasets also differ in model sets, margins, graph support and denominators. These comparisons are observational; they do not identify an expert-annotation causal effect. §4.4's observation that selected deleted matches involve affected players is empirical, not a theorem ruling out indirect effects.

**Code availability as stated:** §1 prints `https://github.com/JennyHuang19/IsRankingRobust`; not opened. §3 reports under three minutes for roughly 50K evaluations for top-1/top-5 on an M1 Pro CPU with **16 GB RAM**. This is a source-reported feasibility hint, **not** evidence of meeting this workspace's 8 GB bound or a measured runtime here.

**Precise possible difference:** tie-preserving original-record budgets; prompt/session/judge-group deletion; fixed-size label corruption versus deletion under matched budgets; and uncertainty-aware effect thresholds are candidate narrower follow-ups. They must be tested, and none is asserted globally novel under the access restriction.

## 7. Zheng and Chiang: evaluation design, metrics and inference

### Zheng et al., “Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena” [5]

§2.2: MT-Bench has **80 two-turn questions**, eight categories with ten questions each. §4.1: six evaluated models and **58 expert-level human labelers**, mostly graduate students; each labels at least 20 random multi-turn questions, yielding roughly 3K votes. Appendix C says humans judge the first turn and then the second, can skip limited questions, and can see reference solutions for some tasks. Thus repeated turns/ratings of a shared prompt should not automatically be treated as independent prompts.

§2.3 contrasts unrestricted live Arena prompts and anonymous crowd votes. §4.1 samples **3K single-turn votes from 30K Arena data**, rather than using today's supplied 55k release. Source snapshot and study cohort must be distinguished.

§3 identifies position, verbosity and reasoning limitations; self-enhancement is discussed but the authors explicitly say their study **cannot determine** it due to confounding/limited data. §3.4 swaps answer order, accepts a win only when both orders agree, and otherwise calls a tie; reference-guided grading reduces some math failures. These are evaluation mechanisms that affect the tie distribution and hence deletion analysis.

§4's headline agreement requires its denominator: Table 5 MT-Bench GPT-4 pairwise versus human is **85% excluding ties (S2)** but **66% with ties/inconsistencies treated as ties (S1)** for first turn. Table 6 Arena is **87% S2 versus 64% S1**. Supporting span: “S2 only includes non-tie votes”. Agreement is not a certificate of identical leaderboard stability or calibrated uncertainty. Do not quote “over 80%” without its selected non-tie protocol.

**Code/data as stated:** abstract prints `https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge`; not followed. This assignment uses only the given pinned-data descriptions for future planning, not an audit of current repository files.

**Positioning difference:** [5] establishes datasets/judge agreement and failure modes; a stability study changes the estimand to sensitivity of the fitted ranking, not another unqualified assertion that GPT-4 matches humans.

### Chiang et al., “Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference” [6]

§3 describes self-selected user prompts, nonuniform pair sampling and anonymous comparisons; users can choose tie or both-bad. §4 frames ranking as a score functional of a comparison distribution, not an intrinsic model attribute independent of prompts/users. §5 Eq. (7) inverse-weights pairs to target a uniform pair distribution; unweighted BT fitted to a nonuniform public sample is therefore not automatically the same estimand. Historical sampling propensities may be unavailable in a release: do not fabricate them.

§5 compares pivot bootstrap and **sandwich robust covariance**, deploys sandwich intervals, and constructs a simultaneous score confidence set plus approximate ranks. **Marginal score CIs are not automatically simultaneous guarantees across all pairs/top-k.** Appendix A (p. 15) compares bootstrap and sandwich coverage in replay and synthetic studies and cautions that replay “coverage” relative to the full-data fitted coefficient is not ordinary true-parameter coverage. Supporting span: “not as meaningful as in the simulation”.

The model is only identified up to an additive constant; the paper fixes a reference score. Robust covariance addresses misspecified outcome probabilities under the relevant regularity assumptions; it is not a blanket correction for arbitrary shared-user/prompt dependence. Adaptive/nonuniform evaluation design, repeated users and source-specific filtering still require explicit assumptions.

**Code/data availability as stated:** §1 commits to making data and code available. No current platform implementation was inspected, and a paper's proposed estimator must not be conflated with every later platform version.

**Positioning difference:** estimating uncertainty/sample-efficient rankings is not the same as worst-case alteration robustness. A useful follow-up can jointly report both but should credit [6] for inference and [1]/[4] for deletion sensitivity.

## 8. Recommended next experiments — proposals, not results

These choices fit the brief's CPU-only, about-one-week, 8 GB, public-data constraints in intent; runtime/memory must still be measured. Use the supplied pinned Arena 55k and MT-Bench human/GPT-4 releases, not new model/API judging. License/hash statements in the request are supplied provenance, **not independently checked dataset evidence in this assignment**. Do not use optional unlicensed or agreement-bound assets before resolving terms.

1. **Faithful bounded replication before extension.** Reconstruct tie-free unit-record BT on the two pinned releases, record every filter and analyzed denominator, fit residual/convergence diagnostics and compare found top-1/top-k witnesses with [4]. Separate version/cohort mismatches from method failures. Expected value: determine whether published claims transfer to the supplied snapshots; no particular reproduction outcome is promised.
2. **Tie and deletion-unit ablation.** Compare dropping ties versus representing a tie as half-win/half-loss, while deleting both pseudo-rows jointly as one original comparison. Compare record-level with shared-prompt/session/judge-group budgets when identifiers exist. Expected diagnostic: whether preprocessing and pseudo-replication explain part of the apparent fragility. Group removals change the feasible optimization; a simple record-score sort is not an exact group-budget solution with unequal group costs.
3. **Operation-aware perturbations and baselines.** Hold a fixed honest record set and compare deletions with binary win/loss label reversals under explicit budgets. Baselines: random records, target-involving random records, margin-independent or local-pair heuristics, first-order AMIP selection, and exact refits of all candidate subsets selected. Use exhaustive subset checking only on genuinely tiny prespecified subproblems as a validation oracle, not as a large-data promise. No live manipulation, de-anonymization training or insertion of platform votes.
4. **Separate rank flips from consequential changes.** Report top-1 identity, top-k membership/Jaccard, Kendall-type order change with a declared tie convention, pairwise score/probability margin changes, and confidence-supported reversals. Treat min-found flip budgets as witness upper bounds; treat no-found-flip cases as censored/not found, not certified robustness. Prespecify an effect threshold rather than emphasizing only arbitrarily close ranks.
5. **Matched, conditional design comparison.** Report raw count `b`, fraction of analyzed original records `b/N`, changed target exposure `b/N_target`, base margins and graph support. Where possible restrict to common model sets and use matched record-count/support subsamples or stratification. Report unmatched whole-dataset comparisons separately. These controls can weaken or condition the Arena–MT contrast; they cannot prove that expert annotation causes stability without an appropriate intervention.

### Calibration/evaluation protocol to freeze before running

- **Descriptive versus predictive target:** all-data sensitivity needs no artificial train/test split; if evaluating robustness to independent future preferences, split by prompt/session/time as appropriate, freeze target models/thresholds and attack rule before the holdout, and do not tune to held-out flips. Do not reuse Min's 90/10 attacker simulation split as if it were a universal ranking protocol.
- **Sampling calibration:** distinguish pointwise margin CIs, simultaneous top-k/rank claims and bootstrap flip frequency. Document resampling units; cluster by shared prompts/users if identifiers justify it. If identifiers are absent, say dependence calibration cannot be fully checked. IID row bootstrap is at most a stated baseline.
- **Approximation calibration:** compare predicted versus exact-refit margin changes across budgets, track sign errors and missed witnesses, and test a few infinitesimal weight perturbations. Test the formula/sign/normalization discrepancies noted above before interpreting any robustness curve.
- **Numerical validity:** remove the score gauge; check fit gradients, score scale, separation, graph support and Hessian conditioning. A disconnected retained comparison graph or non-existent finite unregularized BT MLE is a distinct structural failure outcome, not an ordinary valid ranking flip. Undirected connectivity alone does not ensure finite unregularized BT estimates; directed win support matters. If ridge/damping is introduced, disclose that it changes the fitted estimator and repeat sensitivity checks for that estimator.
- **Record-level accounting:** duplicated rows, tie pseudo-observations and repeated judgments must have explicit atomic edit semantics. Cross-dataset fractions must use the same accounting rule. Preserve no-both-bad/tie mapping decisions and do not count a pseudo-row as a full independent vote.
- **Uncertainty in randomized baselines:** report seeds, repetitions, appropriate variability intervals and what randomness they cover. A deterministic adversarial witness does not need a fabricated standard error; uncertainty about its population generalization is a different analysis.
- **Compute and disclosure:** store runtimes/peak memory, failed fits and failed approximations; solve reduced linear systems rather than form an inverse unnecessarily. Do not claim 8 GB feasibility from [4]'s 16 GB machine alone. Disclose LLM assistance and do not distribute raw preference text in a code submission.

## 9. Limits of this evidence bundle

No source repositories, datasets, current leaderboards, paid APIs or experiments were accessed. Availability/license claims for paper code are source-reported only. Full appendix proofs and empirical claims were not independently reproduced. Some relevant distinctions above are analysis proposals and algebraic consistency checks, not prior-result attributions. No claim is made about the unspecified restricted work or about novelty beyond these six permitted papers. All recorded source/tool/dependency failures are in the companion log.

## Sources

[1] T. Broderick, R. Giordano and R. Meager, *An Automatic Finite-Sample Robustness Metric: When Can Dropping a Little Data Make a Big Difference?*, consulted arXiv v5 (2023), supplied as the 2020 starter. https://arxiv.org/pdf/2011.14999

[2] P. W. Koh and P. Liang, *Understanding Black-box Predictions via Influence Functions*, ICML 2017; consulted arXiv v3. https://arxiv.org/pdf/1703.04730

[3] R. Min et al., *Improving Your Model Ranking on Chatbot Arena by Vote Rigging*, ICML 2025; consulted arXiv v2. https://arxiv.org/pdf/2501.17858

[4] J. Y. Huang, Y. Shen, D. Wei and T. Broderick, *Dropping Just a Handful of Preferences Can Change Top Large Language Model Rankings*, arXiv, pinned v1 (2025). https://arxiv.org/pdf/2508.11847v1

[5] L. Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, NeurIPS 2023 Datasets and Benchmarks; consulted arXiv v4. https://arxiv.org/pdf/2306.05685

[6] W.-L. Chiang et al., *Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference*, consulted arXiv v1 (2024). https://arxiv.org/pdf/2403.04132
