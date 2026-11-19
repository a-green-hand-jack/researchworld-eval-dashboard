# Source-bounded literature notes: BT leaderboard robustness

Date: **2026-11-02 UTC**. Purpose: experimental planning for a **cross-design, exposure-normalized, fixed-design label-flip audit of Bradley–Terry (BT) leaderboards with full numerical refits**, covering crowdsourced Arena, MT-Bench expert/model judges, and NBA.

## Independence boundary and reading method

Only these five user-authorized works were fetched/read: arXiv **2306.05685, 2403.04132, 2011.14999, 2501.17858, 2508.11847v1**. The other authorized IDs (1703.04730, 2504.20879) and DOI 10.2307/2334029 were **not accessed or read and are not in references.bib**. No broad literature search, citation following, recommendations, search engine, accepted-paper listing, external discussion, code repository or dataset site was opened. No attempt was made to identify an unspecified forbidden work.

Direct arXiv abstract HTML and PDFs were downloaded. Only citation metadata was exposed from abstract HTML; recommendation/navigation areas were not read. PDFs were converted locally using `pypdf`. Selected body sections and appendices were read, not bibliographies. Full downloaded PDFs/HTML naturally contain citations and ancillary links; downloading those bytes is not a claim to have read them. Incidental citation names and related-work text **within authorized papers** were not followed or treated as independent evidence. Repository/data URLs below are transcribed availability claims from authorized papers, **not accessed resources**.

**Forbidden-material incident log:** no separately forbidden source was fetched or opened; no forbidden identity was inferred. No contamination incident requiring a reading stop was identified. Only the specified works and official task-required NeurIPS pages/archive were accessed, plus the permitted `pypdf` dependency installation. The ordinary dependency installation is not a literature source.

## Key Findings

### The distinction must be narrow, not a priority claim

The most directly overlapping work, **Dropping Just a Handful of Preferences Can Change Top Large Language Model Rankings** [5], already studies small worst-case preference modifications, BT top-k sensitivity, Arena versus MT-Bench, human versus model judges, influential examples, and **full refits to confirm candidate ranking changes**. Its perturbation is **deletion**. **An Automatic Finite-Sample Robustness Metric** [3] already provides influence-based subset selection and an exact-refit lower bound on maximum sensitivity. **Improving Your Model Ranking on Chatbot Arena by Vote Rigging** [4] already changes selected vote outcomes on **new incoming battles**, including indirect effects through battles not involving the target. Accordingly, do not claim that label manipulation, exact refits, cross-judge comparisons, or discovery of small-data leaderboard sensitivity are by themselves new [3–5].

A defensible project description is:

> We audit BT ranking sensitivity to bounded binary outcome reversals on a fixed observed comparison design, report both whole-dataset and target/pair-exposure-normalized perturbation budgets, and compare multiple evaluation designs and an NBA outcome domain using refit-verified witnesses and matched controls. This differs from the deletion audit in [5] and new-vote injection in [4], while sharing their concern with finite-sample leaderboard sensitivity and their use of refitting for verification.

This is a **bounded contrast to the works actually read**, not an assertion of first-ever methodology, exhaustive novelty, or a demonstrated new empirical result. NBA is outside the experiments described in the read sections of these works; that alone does not establish novelty. Exposure-normalized accounting is not the same thing as Arena's inverse-probability weighting of the fitted population objective [2].

### Comparison at a glance

| Source | Main perturbation/question | Design and evaluation | What is already covered / remaining distinction |
|---|---|---|---|
| [1] MT-Bench / LLM-as-judge | Judge agreement and biases; not a worst-case BT flip-budget audit | Curated 80 two-turn questions, 58 expert labelers, crowd and model judges; tie-conditional agreement and average win rates | Defines evaluation designs and judge pitfalls, not a label-flip certificate |
| [2] Arena platform | Statistical ranking/uncertainty, adaptive sampling and anomalous-user detection | Crowdsourced comparisons; BT MLE, propensity reweighting, sandwich/bootstrap intervals, simultaneous ranking uncertainty | Exposure/design and ordinary uncertainty already matter; distinguish edit budgets from propensity weights |
| [3] AMIP | Worst-case deletion of a small sample fraction | Influence approximation for smooth estimators; exact refit witnesses; approximation theory | Selection plus refitting is established; local approximation is not a global certificate |
| [4] Vote rigging | Choose outcomes/ties/abstention for newly sampled votes and append them | 1.7M historical Arena votes, target-only/omnipresent strategies, simulated online threat models | Label-choice manipulation and indirect ranking effects are established; project holds original battles fixed |
| [5] BT deletion robustness | Delete influential existing evaluations to change top-k set | Arena/MT-Bench × human/model judges; influence/Newton candidate selection and BT refits | Already closest cross-design audit; project changes deletion to fixed-design reversal and makes exposure normalization/controls explicit |

## Actual-read source cards

### [1] Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena

- **Identity/version:** Lianmin Zheng et al.; arXiv:2306.05685 **v4**, 24 Dec 2023, initial submission 9 Jun 2023. PDF identifies NeurIPS 2023 Datasets and Benchmarks track.
- **Actual read:** abstract; §§1–4.2 and Tables 1–6 (PDF pp.1–8; text lines 1–545, with last page only partially read); Appendix C.1–C.3 (pp.23–24); D.1–D.3 and opening D.4 text (pp.25–26), opening caption of Table 13 (p.27). No claim to have read main §§5 onward, all prompt appendices, training appendices, or the rest of Table 13.
- **Evidence anchors:** “80 high-quality multi-turn questions” (§2.2); “58 expert-level human labelers” (§4.1); “S2 ... only includes non-tie votes” (Table 5).
- **Design/data:** 8 categories × 10 manually designed two-turn questions: writing, roleplay, extraction, reasoning, math, coding, STEM, humanities/social science. Six answering models in agreement study. Humans judge at least 20 random multi-turn questions; about 3K votes. Experts are mostly graduate students, not a representative sample of all users. Arena analysis samples about 3K single-turn votes from the earlier ~30K-vote release, with 2,114 unique crowd IPs (§4.1).
- **Metrics/protocol:** agreement is probability that randomly selected, distinct judges agree on a randomly selected question. Average win rate averages against other players. Table 5 S1 includes ties and treats order-inconsistent model verdicts as ties; S2 retains only non-ties. GPT-4 pairwise–human agreement is **66% in S1 vs 85% in S2** for the first turn (also 66%/85% second turn); first-turn human–human is **63%/81%**. Arena Table 6 GPT-4 pairwise–human is **64%/87%**. “Over 80% agreement” must not be described as unconditional accuracy. D.3 explains that a deterministic majority-aligned judge can exceed average human–human agreement without being infallible.
- **Judge calibration/failure modes:** position bias, verbosity bias, possible self-enhancement (not conclusively established), reasoning/math grading errors. Their conservative order-swap rule calls a win only if it wins in both orders; inconsistencies become ties. References improve math grading (Table 4 default failures 14/20 vs reference 3/20), not a general correctness guarantee. Near-equal answer pairs show more position bias. Two turns from one prompt, two order-swapped verdicts, and multiple judgments of a response pair are dependent units, not independent new battles.
- **Collection caveat:** C.1 says GPT-4 explanations are shown after disagreement and participants are asked about reasonableness; §4.2 reports willingness to change opinions. Verify which released field is the initial vs any revised judgment before using it as an independent expert label. This task did not inspect released files, so it does not assert that the headline agreement uses revised labels.
- **Split:** this is a judge-agreement evaluation, not a supervised train/test benchmark split for a leaderboard audit. Do not invent such a split. Their human collection allows limited skips and reference solutions on some questions.
- **Availability stated, not verified:** https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge (questions, expert votes and Arena preferences; printed in abstract). No repository or license review performed.
- **Audit implication:** compare expert/model labels on a shared prompt–answer–model-pair support where possible, separately from comparisons on all available rows. Preserve turn, annotator, judge and order provenance; report tie and inconsistent-judgment filters.

### [2] Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference

- **Identity/version:** Wei-Lin Chiang et al.; arXiv:2403.04132 **v1**, 7 Mar 2024.
- **Actual read:** abstract; §§1–5.1 (pp.1–5), §6 (pp.6–7), §7–7.2 (pp.7–8), opening §8 limitations. Text lines 1–340 and 371–915; skipped part of the dense win-matrix figure extraction. Appendices and bibliography not read.
- **Evidence anchors:** “we employ non-uniform sampling” (§3.2); “the ‘sandwich’ robust standard errors” (§5); “inverse weighting ... uniform distribution” (§5, Eq.7).
- **Data/design:** Table 1 snapshot 2024-01-21: **243,329** conversations/votes, **50** models, **90,051** users, **149** languages; approximately 77% English. User-authored prompts; model identities revealed after voting; tie and “both are bad” options. Keywords filter identity-revealing responses. The analysis snapshot is not automatically the same as a later public 55k release.
- **Estimator:** pairwise logistic BT coefficients with one reference coefficient fixed; switched from online Elo to BT for statistical estimation. Population target is a uniform distribution over model pairs by default. Eq.7 uses inverse sampling-probability weighting to target that objective. A plain unweighted fit on nonuniform observations may target a different pseudo-true ranking under misspecification. Do not call a plain audit a replica of their entire production pipeline.
- **Uncertainty/calibration:** evaluates pivot bootstrap and sandwich standard errors; chooses sandwich intervals based on simulation. Formal approximate rank bounds use simultaneous, multiplicity-corrected confidence sets; overlapping marginal intervals do not directly define a unique total order. Simulations draw BT coefficients from beta distributions (γ=2 main setting), synthesize outcomes and assess coverage/width over **20 trials**. This is sampling calibration, not certification against adversarial label edits.
- **Protocols/results:** replays **213,576 historical votes** for ranking; fits this reference distribution to simulate active versus random sampling. For win-matrix precision 0.2, random needs 6,800 samples vs adaptive 4,400; for score precision 0.3, 17,200 vs 16,400 (§7.1). These are the paper's simulations, not new audit results. Expert relabeling of **160 battles** in §6.3 compares two selected model-pair settings; crowd–expert agreement 72–83% does not establish universal vote correctness. Anomaly test uses per-user combined p-values at five random checkpoints with Bonferroni correction; experiment manually labels 25 anomalous + 25 normal users with ≥50 votes.
- **Availability:** paper commits to data/code releases; printed platform URL https://chat.lmsys.org is historical and was not visited. No public dataset bytes, current leaderboard implementation or filtering code were inspected.
- **Audit implication:** freeze date/model cohort, retain edge counts, language/time and annotator clustering. Separate statistical uncertainty from adversarial edit sensitivity. If propensities are unavailable, explicitly name the empirical-design estimand and do not reconstruct weights from unsupported guesses.

### [3] An Automatic Finite-Sample Robustness Metric: When Can Dropping a Little Data Make a Big Difference?

- **Identity/version:** Tamara Broderick, Ryan Giordano, Rachael Meager; arXiv:2011.14999 **v5**, posted 19 Jul 2023 (PDF cover 20 Jul); first submitted 30 Nov 2020. Bibliography uses initial arXiv year with an explicit v5 note.
- **Actual read:** abstract, §§1–2.3 (PDF pp.1–11), opening §2.4 (p.12); §3.3.1–3.3.2 (pp.24–27, including Assumptions 3–4 and Theorem 1). No detailed applications, full proofs, §3.4 related-work discussion or appendices read.
- **Evidence anchors:** “re-run our analysis” (§2.2.1); “lower bound on the exact Maximum Influence” (§2.2.1); “do not expect the constants to be useful in practice” (§3.3.1).
- **Method:** introduce binary row weights (0 deletes, 1 retains); linearize a smooth scalar analysis functional in row weights; sort harmful influence scores and select up to floor(αN) rows. Approximation is fast relative to enumerating all subsets and applies to smooth Z-estimators, including MLE. Consider effect sign, significance, or significant sign reversal, not only raw coefficient movement.
- **Exact-refit guarantee:** recompute on the selected subset (§2.2.1). Achieved change is a **lower bound on maximum attainable change**. Equivalently, a successful witness with k edits gives an **upper bound on the unknown minimum edit budget**. It does not make the selected subset globally optimal. Lack of a successful candidate is not a general proof of robustness.
- **Theory/failures:** finite-sample approximation-error bounds need smoothness, nonsingular derivatives, bounded averages and Lipschitz conditions. §3.3.1's bound is O(α) error versus O(sqrt(α)) change under assumptions; constants may be loose and the allowable α may theoretically be below 1/N (vacuous). Linearization can fail for large deletion fractions or near parameter boundaries. Standard errors do not substitute for this sensitivity measure, and sensitivity need not mean misspecification or gross outliers. Do not transfer deletion bounds to label flips without new assumptions/analysis.
- **Metrics/splits:** deterministic finite-sample sensitivity conditional on observed data; not a prediction train/test metric. Numerical checks and application results support the original method but were not reproduced here.
- **Availability stated, not verified:** https://github.com/rgiordan/zaminfluence (R package, paper footnote). Exact-refit checking is prior practice, not a new project contribution.

### [4] Improving Your Model Ranking on Chatbot Arena by Vote Rigging

- **Identity/version:** Rui Min, Tianyu Pang, Chao Du, Qian Liu, Minhao Cheng, Min Lin; arXiv:2501.17858 **v2**, 10 Aug 2025; initial submission 29 Jan 2025. PDF identifies ICML 2025, PMLR 267.
- **Actual read:** abstract, §§1–7 (PDF pp.1–8, text lines 1–715; includes the opening of §8 and Table 8 because of page layout). Remaining related-work/conclusion and appendices not read. Do not claim appendix classifier/defense details independently verified.
- **Evidence anchors:** “submitting new votes” (§2.2); “90% ... as VH” (§2.2 remark); “relative rating increase” (§3.2).
- **Threat model:** append malicious votes on newly sampled anonymous battles; choose A win, B win, tie or abstention. Target-only needs target identification; omnipresent strategies use all newly encountered pairs, potentially affecting a target even when it is absent. Omni-BT considers alternative outcomes using a BT-based objective (target minus model immediately ahead); Omni-On uses online Elo surrogates when only public ratings are available. This is not an audit which reverses arbitrary existing historical labels while preserving all original battles.
- **Data/split:** ~**1.7M historical votes across 129 models**, from Arena Notebook as of Jan 2025. **90% historical VH / 10% concurrent-other-user VO** in simulations, not a prediction training/test split. Main idealized tests include 20,000 new voting interactions with uniform pair sampling, six target models and no concurrent votes. Do not equate submitted interactions, target-involving battles and accepted rigged votes.
- **More realistic setting:** 25-model subset and ~23k English votes; de-anonymization classifiers trained using 4,000 prompts/model from HC3/Quora, 20 epochs, batch 64, 2×A100. Initial simulations reuse training prompts; unseen-prompt and unseen-model ablations are therefore important. The case-study threat model exposes only public ratings, while Omni-BT needs historical data; distinguish idealized reference performance from restricted-access strategies. The paper simulates rigging rather than corrupting the live platform.
- **Metrics/failures:** target rank improvement as new voting interactions accumulate, varying identity errors, nonuniform target sampling and concurrent votes. Defensive duplicate-vote checks, anomaly tests and unlikely-win filtering only partly mitigate attacks; normal-looking votes can trade attack efficiency for detectability. These findings are not evidence that a fixed historical-label-flip method will attain the same budgets or that such flips represent real annotation errors.
- **Availability stated, not verified:** https://github.com/sail-sg/Rigging-ChatbotArena (abstract metadata). No code/data download or independent rerun.

### [5] Dropping Just a Handful of Preferences Can Change Top Large Language Model Rankings

- **Identity/version:** Jenny Y. Huang, Yunyi Shen, Dennis Wei, Tamara Broderick; **arXiv:2508.11847v1 explicitly pinned**, 16 Aug 2025 (PDF cover 19 Aug). No later version consulted.
- **Actual read:** abstract, §§1–6 (PDF pp.1–18); Appendix A (pp.23–25); B (pp.25–26); C captions/supporting description and extracted figure text (pp.26–29). Figure images were not independently visually measured; conclusions use prose/tables/captions. Bibliography not read.
- **Evidence anchors:** “we refit the BT-model” (§3); “our analysis is conducted on tie-free data” (§3.1); “always performs a refitting” (Appendix A).
- **Setup:** binary comparisons, unregularized BT maximum likelihood with first model fixed at zero. Top-k robustness is **set membership**, not the exact ordering inside the set. Reduces top-k membership changes to crossing pairs inside/outside baseline top-k. Selects candidate deletions by influence or additive one-step Newton scores, checks nearby-score pairs first and stops on a successful witness. Permits deleting comparisons between any models, not only the affected pair. Appendix A allows optional refits even if the approximation did not predict a crossing; verified positives always get a full refit.
- **Critical guarantee interpretation:** successful refits witness non-robustness; the approximate/greedy candidate search does not exhaust all subsets and hence cannot in general certify robustness when it fails. “Exact refit” means refitting the estimator on a candidate, not an exact combinatorial solution. The target audit should explicitly distinguish these meanings.
- **Data:** §4.1 names Arena **arena-human-preference-55k**, **chatbot-arena-llm-judges**, and **mt-bench-human-judgments** releases hosted on Hugging Face. It reports 57,477 Arena evaluations and 3,355 MT-Bench evaluations before the smaller binary-analysis denominators reported in Table 1. Ties are discarded (§3.1); simple raw BT rankings need not reproduce platform ties/postprocessing choices. No dataset revision/hash or exact filtering implementation was verified here.
- **Refit-verified top-1 witnesses in Table 1:**

| Platform | Judge | Deleted / analyzed N | Fraction as percent (rounded) |
|---|---|---:|---:|
| Arena | Human | 9 / 39,716 | 0.0227% |
| Arena | LLM | 4 / 34,297 | 0.0117% |
| MT-Bench | Human | 83 / 2,575 | 3.22% |
| MT-Bench | LLM | 27 / 2,180 | 1.24% |

These are **sufficient deletion counts**, not established global minima, and are not label-flip results. Denominators must come from the actual filtered analysis set, not automatically the raw release size. §4.2 text mentions 20 deletions for an Arena top-5 change, whereas Fig.3/Appendix B describe a 5-deletion top-5 witness; this apparent reporting difference is not resolved by the read text. Do not silently merge these into one verified baseline. Reproduce the snapshot/filter and target definition before comparison.

- **Cross-design conclusion:** observes greater MT-Bench deletion robustness than Arena and compares human/model judges in both designs. Its attribution to expert raters/curated prompts is tentative, not randomized identification. Small score margins and different pair exposures/cohorts also matter. Appendix C explicitly examines model appearances and score-gap association, so it is wrong to claim the paper ignores exposure or margins altogether. The read method reports global deletion fractions, not the explicit matched exposure-normalized flip-budget protocol proposed below.
- **Influential-example result:** §4.4/B find observed deletion witnesses involve one or both affected models. This is an observation from their search/results, not a theorem excluding indirect paths. §4.5 inspects five response pairs and finds similarities; not a label-correctness audit. Claimed runtime: top-1/top-5 on ~50k evaluations in under 3 min on M1 Pro/16GB, not a measurement from this task.
- **Availability stated, not verified:** https://github.com/JennyHuang19/IsRankingRobust (§1). Source formula/implementation should be independently checked against the actual loss and finite differences; a deletion influence expression should not simply be copied into a label-flip implementation. Code was not inspected.

## Recommended Next Experiments (planning recommendations, not performed results)

### 1. Define perturbations and units before running the audit

Primary audit: fix each binary row's participant pair, prompt/game identity, covariates and row weight; choose a subset S and reverse **y → 1−y**, leaving all comparison exposures unchanged. Count **one original vote/game** as one edit. Never count two implementation rows for a tie as two independent votes. Use tie-free binary data for the clearest primary analysis; report removals and run a separately specified tie-aware sensitivity check (do not invent a binary “flip” for a tie).

For target contrast a vs b, measure the baseline gap and the refitted gap. Distinguish pair-order reversal, top-1 identity, top-k membership and complete ordering; k>1 is not interchangeable across these endpoints. Predeclare targets (e.g., adjacent pairs and top-k boundary pairs) and crossing/tie numerical tolerances. Report the smallest successful **searched** budget, not an unqualified minimum.

### 2. Report global and exposure-normalized budgets without disguising denominators

Let N be the eligible original comparisons and E_t = #{n: t appears in comparison n}. For a target pair define E_ab = #{n: a or b appears}, counting shared battles once, and H_ab = #{n: the battle is directly a vs b}. Keep these counts fixed under binary flips.

Report k/N, target-incident flips k_t/E_t, union-incident flips k_ab/E_ab, and direct-head-to-head flips k_h/H_ab where defined. Also report k and the counts themselves. For **target-only or union-only eligible edits**, k/E_t or k/E_ab has the natural interpretation of a fraction of eligible exposure. For **unrestricted** edits, total k/E_t is only a reference-normalized cost and can include off-target edits; label it accordingly and show incident/off-target composition. Do not call it a fraction of target labels corrupted. Never interchange E_a+E_b with E_ab, which would double-count direct encounters.

This makes global fractions interpretable across different graph sizes and exposure patterns. It is not a guarantee that exposure normalization removes confounding. Include raw score gap, standardized gap, direct win margin, edge counts, model cohort and connectedness diagnostics alongside it. Restrict eligible edges explicitly so denominators cannot be adjusted post hoc.

### 3. Use strong matched controls and verify all successes

Compare random flips, random flips matched to the candidate's affected model-pair/edge counts, simple target-incident adverse flips, a static influence-selected set, and sequential refit-and-reselect (if feasible). Add deletion using the same target definitions to connect to [3,5]; compare edits carefully because deleting one observation and reversing its outcome are different interventions. Treat new-vote injection [4] as a different threat-model comparison, not a directly commensurate baseline budget.

For every reported success, optimize the original BT objective to convergence on the modified labels, preserve identification/regularization/weights, and save row IDs, original/new outcomes, baseline/refit scores, gradient/convergence diagnostics and achieved endpoint. These are **full numerical refits**, not symbolic exact solutions. Validate candidate-score predictions with finite differences and exact small-instance calculations. Exhaustive tiny-graph tests can expose search failures and provide exact minima only on those tiny instances. Failed heuristics are “no witness found within tested budget/search,” not certified robust.

### 4. Separate design effects from judge and margin effects

Run at least Arena-crowd, MT-Bench-expert and MT-Bench-model-judge panels; include Arena model-judge panel if released matching support permits. Compare human/model judgments on **identical prompt/response-pair supports** before comparing the full releases; retain shared prompt/turn clusters. Add exposure/cohort/margin-matched subsamples and repeat over random seeds. Expected diagnostic: some apparent design gap may shrink after matching; its magnitude/direction is empirical, not assumed. Neither persistence nor disappearance establishes a causal effect of annotator expertise.

### 5. Use NBA only as a specified external outcome-domain check

No NBA dataset or NBA-specific paper was accessed; no season, game count, license, data URL or prior NBA robustness result is claimed here. Before experiments, record approved data provenance, season(s), regular-season vs playoffs, team-ID consistency, home advantage, schedule exposure and any time effects. Decide between plain BT (same estimand across domains) and an explicitly separate home-adjusted variant. Game outcome reversals are **counterfactual data perturbations**, not plausible human preference corrections or evidence of real game errors. Keep the observed schedule fixed; do not conflate a schedule change with a label flip.

### 6. Calibration, uncertainty and reporting

The primary robustness audit is conditional on the fitted dataset: no train/test split is inherently required. Freeze snapshots and preregister targets/budget grids/search rules. If tuning heuristics or making predictive-generalization claims, use separate development datasets or time-held-out games/prompts; do not optimize on an evaluation snapshot and label it out-of-sample robustness.

Report random-control success rates with seed counts and suitable intervals; distinguish variability over controls, sampled datasets, and annotator/prompt clusters. Cluster resampling by prompt/response pair or annotator where dependence exists; if annotator IDs are absent, state that limitation. Ordinary BT confidence intervals and adversarial witnesses answer different questions. If bootstrap is used to characterize a data-adaptive minimum searched budget, rerun the selection procedure within each replicate or clearly label fixed-witness-only uncertainty. For multiple selected targets, avoid treating the most vulnerable post-selected pair as a prespecified significance test. Report null/tiny-margin pairs rather than suppressing them.

Check graph connectivity and finite MLE existence/separation before and after perturbations. Label flips preserve the undirected exposure graph but can change the directed win graph and create separation. Fix gauge constraints and objective scaling; keep penalties fixed/explicit and report when regularization changes the estimand. Do not count optimizer failures, diverging coefficients or numerical ties as successful substantive reversals. Record runtime/full-refit counts and both successful and unsuccessful searches.

## Limitations of these notes

This was source-bounded reading, not a literature survey or a proof of novelty. No external paper, cited method, repository, dataset, license, NBA source, or live leaderboard implementation was verified. No experiments were executed. Actual-read extents are declared above; appendix proofs and implementation details not read are not being certified. The extracted PDF text can distort formulas and figures, so implement from the specified objective and test, not from OCR-like transcription alone. Causal claims about judge expertise/design cannot be inferred from these observational comparisons.

## Official template result

A real **NeurIPS 2026** official template exists and was downloaded directly from its official CFP-linked archive. **Main Track submission: 9 content pages including figures/tables; accepted camera-ready: 10 content pages.** References, technical appendices and mandatory checklist do not count toward content pages. See `/work/paper/template/PROVENANCE.md` for exact URLs, quotes, hashes, access dates and scope. No 2025 fallback, accepted-paper listing, external template mirror or search engine was used.

### Sources (only actually read works)

[1] Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena: https://arxiv.org/abs/2306.05685 (downloaded PDF v4).

[2] Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference: https://arxiv.org/abs/2403.04132 (downloaded PDF v1).

[3] An Automatic Finite-Sample Robustness Metric: When Can Dropping a Little Data Make a Big Difference?: https://arxiv.org/abs/2011.14999 (downloaded PDF v5).

[4] Improving Your Model Ranking on Chatbot Arena by Vote Rigging: https://arxiv.org/abs/2501.17858 (downloaded PDF v2).

[5] Dropping Just a Handful of Preferences Can Change Top Large Language Model Rankings: https://arxiv.org/abs/2508.11847v1 (v1 only).

## Access log and downloaded-source integrity

All HTTP accesses below were direct retrievals, not searches. Each source's reading extent is recorded in the cards above. The raw machine log is `/work/artifacts/sources/access_literature.json`. Official-resource requests are also reproduced below from `/work/paper/template/access_template.json`. `pypdf` was installed using the default package manager (`python -m pip install pypdf -q`); package-manager transport URLs were not emitted, so no per-URL dependency access trace is claimed. Local extraction/retrieval helper scripts are retained for provenance; no experiment or model code was written.

| UTC | Requested URL | Status or result | Final URL | Bytes |
|---|---|---|---|---:|
| 2026-11-02T16:08:21.238727+00:00 | https://arxiv.org/abs/2306.05685 | 200 | https://arxiv.org/abs/2306.05685 | 43641 |
| 2026-11-02T16:08:24.875757+00:00 | https://arxiv.org/pdf/2306.05685 | 200 | https://arxiv.org/pdf/2306.05685 | 1580141 |
| 2026-11-02T16:08:28.218097+00:00 | https://arxiv.org/abs/2403.04132 | 200 | https://arxiv.org/abs/2403.04132 | 42506 |
| 2026-11-02T16:08:31.815467+00:00 | https://arxiv.org/pdf/2403.04132 | 200 | https://arxiv.org/pdf/2403.04132 | 1081950 |
| 2026-11-02T16:08:35.122626+00:00 | https://arxiv.org/abs/2011.14999 | 200 | https://arxiv.org/abs/2011.14999 | 43574 |
| 2026-11-02T16:08:38.720256+00:00 | https://arxiv.org/pdf/2011.14999 | 200 | https://arxiv.org/pdf/2011.14999 | 1046828 |
| 2026-11-02T16:08:42.076306+00:00 | https://arxiv.org/abs/2501.17858 | 200 | https://arxiv.org/abs/2501.17858 | 42201 |
| 2026-11-02T16:08:45.666426+00:00 | https://arxiv.org/pdf/2501.17858 | 200 | https://arxiv.org/pdf/2501.17858 | 1267116 |
| 2026-11-02T16:08:49.054415+00:00 | https://arxiv.org/abs/2508.11847v1 | 200 | https://arxiv.org/abs/2508.11847v1 | 40951 |
| 2026-11-02T16:08:52.759179+00:00 | https://arxiv.org/pdf/2508.11847v1 | 200 | https://arxiv.org/pdf/2508.11847v1 | 1729289 |
| 2026-11-02T16:12:46.671574+00:00 | https://neurips.cc/Conferences/2026/CallForPapers | 200 | https://neurips.cc/Conferences/2026/CallForPapers | 53579 |
| 2026-11-02T16:12:48.420298+00:00 | https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles | HTTP Error 404: Not Found | — | — |
| 2026-11-02T16:13:03.584694+00:00 | https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip | 200 | https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip | 20259 |
| 2026-11-02T16:13:54.468973+00:00 | https://neurips.cc/Conferences/2026/MainTrackHandbook | 200 | https://neurips.cc/Conferences/2026/MainTrackHandbook | 167185 |

| Local file | SHA-256 |
|---|---|
| artifacts/sources/2011.14999.pdf | b25d1b808fd68bc283c69694dd069b13c95259a762af40e92f4300bb4183ed4a |
| artifacts/sources/2306.05685.pdf | 1574982845157569b85c1214bfa9987000384d7a5e3b5fbdcc5a29afec59cb81 |
| artifacts/sources/2403.04132.pdf | 039bccd60a7d49bfda80ce17ea627654736928eee9a7ee75767a38d04a01562f |
| artifacts/sources/2501.17858.pdf | 90d2df39bab4b94ddbd19633af368fdf265db6fd73e39c5fc88b10b08ae85ae6 |
| artifacts/sources/2508.11847v1.pdf | 3539869811b8dc60da3ebb0486127b5aca1a00b5e0bc468c0813ba1dd4a0f3ef |
| paper/template/Formatting_Instructions_For_NeurIPS_2026.zip | 82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9 |
| paper/template/neurips_2026.tex | cf4cee7991665306d1daaa3985be4feec7f8889d6d072ffa12f99a8e1537d797 |
| paper/template/neurips_2026.sty | c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a |
| paper/template/checklist.tex | 780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6 |
