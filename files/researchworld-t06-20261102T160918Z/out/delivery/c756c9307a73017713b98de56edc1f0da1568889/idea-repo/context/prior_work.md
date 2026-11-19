# Permitted prior work and contribution boundaries

Authority: frozen `starter_literature.md` and `deliverable.md`. This dossier uses only the seven expressly permitted arXiv papers and metadata for the expressly permitted Bradley–Terry article. No search for the withheld study, citation traversal, related-paper recommendations, live-platform interaction or new data collection was performed. Original PDFs are reading copies outside version control; their retrieved versions/hashes are in `sources.json`. Section-specific reading scope and access failures are recorded in `reading_log.md`. Read-source findings below are not measurements from this study.

## Positioning that the evidence supports

The contribution can be a **reproducible, conditional empirical audit of decisive-outcome reversals**, with targeted versus random baselines, baseline score-gap uncertainty, a non-LLM season panel, matched human/model-judge schedules, and checks of modeling conventions. Influence-function machinery, preference-leaderboard sensitivity and Arena/MT comparisons already exist in the explicitly permitted literature. There is no basis for a priority claim about discovering fragile rankings or for claiming a new influence-function algorithm.

The current intervention is neither deletion nor injection. It changes an existing decisive label while retaining its comparison pair, schedule and all tie labels. Such a study can show that specific recorded rankings admit small successful interventions. It cannot infer an attacker's access, establish actual corruption, generalize to live-platform defenses, or attribute differences causally to evaluation design.

## Source-by-source findings

### Chiang et al. (2024): Chatbot Arena

Reviewed source: arXiv:2403.04132v1, especially §§3–5, §§6.3–8 and Figure 5.

- Anonymous models answer the same user prompt; identities are disclosed after preference voting. This is live, crowdsourced preference collection, not an expert-designed question set or an independent draw from all deployment users.
- §4 specifies BT score differences through a logistic win relationship; additive score shifts do not identify an absolute ability scale. Scores summarize performance under a specified comparison distribution.
- §§4–5 define a target uniform distribution over pairs and inverse-sampling-weighted estimation. This is consequential under model misspecification: an unweighted empirical-schedule fit need not target the same score. Our current static ridge BT audit must not be described as reproducing all official Arena leaderboard calculations.
- §5 distinguishes pivot bootstrap and sandwich uncertainty. Its approximate ranks use a simultaneous confidence set over scores; Figure 5 displays intervals with and without multiplicity correction. A percentile interval for one empirically selected gap is a different object.
- §6.3 validates a limited set of crowd preferences against experts. §8 acknowledges user-base and prompt-distribution biases and the focus on helpfulness over safety. Crowd votes are observations of preferences, not universal ground-truth answer quality.

Implication: define the estimand, sampling/weighting rule, score scale and uncertainty object. Cite this paper for platform construction and score/interval context, not for the current perturbation results or a guarantee that exported snapshots recreate a live board.

### Zheng et al. (2023): MT-Bench and LLM judges

Reviewed source: arXiv:2306.05685v4, main §§2–7, Appendix C and the setup of Appendix D.3.

- MT-Bench has 80 designed two-turn questions in eight categories; the reported human study uses six answer-generating models and 58 expert-level annotators, mostly graduate students. Turns, repeated questions, pairs and judgments are not independent benchmark questions.
- §§3.3–3.5 document position bias, verbosity bias and limitations in grading math/reasoning; self-enhancement is investigated but the paper explicitly declines a definite conclusion given its limited data.
- §3.4's conservative order-swap rule declares a win only when both answer orders agree; inconsistent orders become ties. A released GPT-4 tie can therefore encode an order inconsistency rather than equal substantive quality. The current analysis must disclose that and retain the inconsistent-tie exclusion check.
- The prominent >80% agreement finding is setup-dependent. Table 5's non-tie setup gives 85% GPT-4–human agreement; the setup retaining ties/inconsistencies gives 66% for GPT-4-pair versus humans. Agreement is not a universal accuracy claim and does not imply equality of ranking-sensitivity statistics.
- Appendix C.1 says annotators can skip questions, have reference answers for some tasks, and see GPT-4's judgment after a disagreement to assess its reasonableness. The reviewed paper alone does not establish whether the current release's recorded `winner` is an amended or initial vote. Do not invent that provenance. In particular do not call all human votes a causally isolated or independent ground-truth control.
- Appendix D.3 distinguishes expert human and author votes. The current data audit's full-human and expert-only analyses should remain separate.

Implication: canonical question–unordered pair–turn cells are an appropriate matching unit; shared question resampling captures some dependence. Matching support/N does not remove annotator heterogeneity, tie construction or question-selection limits. Report label-source differences on this collection without broad human-versus-LLM superiority claims.

### Koh and Liang (2017): influence functions

Reviewed source: arXiv:1703.04730v3, §§2–4, selected applications in §5 and derivation context.

- §2 derives parameter sensitivity to infinitesimal upweighting using an inverse Hessian times a sample gradient, then uses the chain rule for a target statistic. §2.2 explicitly permits replacing an observation, including a discrete label, by interpolating its loss contribution.
- Hessian-vector methods address expensive inverse solves in large models; a small BT parameter vector does not need a deep-network-scale approximation to be feasible.
- The paper checks approximations against actual retraining and explores departures from strict smoothness/convexity assumptions. Those applications do not certify the accuracy of any new BT subset search.

Implication: the current reversal influence score is a routine adaptation of smooth loss replacement. Credit the existing method; fit and refit validation supplies empirical evidence for its current use, not a global adversarial optimum.

### Broderick, Giordano and Meager (2020 preprint; retrieved v5 from 2023)

Reviewed source: arXiv:2011.14999v5, §§1–2, §3.2 and §3.3, including the exact-refit distinction in §2.2.1.

- Maximum Influence Perturbation maximizes a target statistic's change after deleting at most a prescribed data fraction. AMIP uses a first-order expansion in observation weights, selects the largest helpful influence scores, and evaluates sign/significance changes.
- §2.2.1 explains that refitting a candidate subset supplies a lower bound on maximum achievable **effect**. Equivalently, a successful witness supplies an upper bound on minimum **cost**. Those are consistent directions for different quantities; do not call the found edit count a lower bound on minimum attack cost.
- §3.2 separates data-deletion sensitivity from conventional standard errors. Small standard errors do not in general imply robustness to an adversarial fraction of data. Thus our observed overlap between tiny counts and unresolved gaps is descriptive evidence in these snapshots, not a theorem that sensitivity is just statistical uncertainty.
- §3.3 requires smoothness/invertibility and controls approximation error locally. The paper explicitly discusses limitations of linear approximation. A theoretical result for deletion does not automatically transfer unchanged to the current finite label reversals or prove a selected prefix globally optimal.

Implication: show gap uncertainty and perturbation sensitivity together as complementary diagnostics. Keep exact-refit witnesses distinct from influence predictions and from certification.

### Min et al. (2025): new-vote rigging

Reviewed source: arXiv:2501.17858v2, main §§1–8 and impact statement; particularly threat model §2.2, strategies §3, stress tests §§4–6 and defenses §7.

- The intervention submits **new** votes; historical data access, true versus inferred model identities, sampling information and simultaneous ordinary votes are distinct threat-model axes.
- Target-only strategies manipulate battles predicted to involve a target. Omnipresent strategies exploit BT's coupled fit to influence a target even through other models' battles. Their mechanisms include BT-based and online-score objectives; the paper compares rank improvement at specified interaction/vote budgets.
- The simulated setting uses historical votes and separate ordinary/new votes to avoid contaminating actual Arena voting. Classifier training and de-anonymization are part of that work's practical access story, not the current CPU-only audit's experiment.
- §7 tests partial defenses and reports limitations; the existence of a retrospective label-reversal witness does not evaluate those defenses.

Implication: cite this work as related manipulation research while explicitly contrasting injection with reversal. Neither a smaller fractional denominator nor fewer edited historical rows establishes that this study provides a stronger or cheaper executable attack.

### Singh et al. (2025): evaluation policy and sampling

Reviewed source: arXiv:2504.20879v2, abstract/introduction, §2 methodology and §9 conclusion; the dossier uses only those inspected claims.

- The paper examines private model testing/selective score disclosure, unequal sampling/data access, distribution-specific overfitting and model deprecation. It draws on several historical and collected data sources, not the present fixed 55k snapshot alone.
- These are policy/selection mechanisms distinct from modifying existing preferences under a frozen schedule. The authors' reported platform findings must be attributed as that paper's results rather than asserted as newly verified here.

Implication: use it to locate the current audit among different reliability questions. Our runs do not independently test private-test selection, provider fairness, overfitting or model-deprecation policy. Avoid importing stronger causal/policy claims into the present evidence.

### Huang et al. (2025): BT deletion sensitivity

Reviewed source: explicitly permitted arXiv:2508.11847v1, read through all main sections and appendices, including source-specific tables and figure captions.

- §§2–3 study adversarial data **deletion** in BT scores, reducing top-k set changes to pairwise score contrasts. AMIP/additive one-step Newton approximations propose influential subsets; actual refits check candidate failures of robustness.
- §3.1 explicitly discards ties and distinguishes raw BT fits from Arena's displayed score transformation. Positive affine transformations preserve ranks; removing ties can change them.
- §4 and Table 1 already compare Arena and MT-Bench, human and model judging. The study already reports tiny successful deletion sets and associates sensitivity with small score gaps. These ideas cannot be claimed as newly discovered here.
- Table 1's published sufficient top-1 deletion counts are 9/39,716 Arena-human, 4/34,297 Arena-model-judge, 83/2,575 MT-human and 27/2,180 MT-model-judge. These are **published source facts**, not this study's rerun results. The 57,477/3,355 raw dataset descriptions differ from the retained tie-free denominators. The current MT model-judge source is the supplied GPT-4 pairwise release; the Arena model-judge collection is an optional different dataset.
- Figure conventions include BT-score plots, fraction-dropped bars across top-k boundaries, match-involvement composition and score-gap versus sensitivity scatter. These contextual figures do not require copying their layout or representing every difference as an evaluation-design effect.
- The paper discusses higher-quality prompts/annotators as possible explanations of MT's measured robustness. Its observational contrast does not license a causal quality explanation for our changed threat model and fit.

Implication: the main contrast is **deletion versus outcome reversal plus additional controls/designs**, not a direct numerical replication. If any published threshold is compared, give source, operator, denominator, tie rule, fit and endpoint together. It should not be a numerical performance baseline absent a fresh comparable implementation/run.

### Bradley and Terry (1952): access limitation

The original DOI and exact Crossref metadata were checked. The DOI redirect and publisher PDF returned HTTP 403; the direct JSTOR PDF URL returned a bot/challenge HTML page instead of a paper. OpenAlex exposed no open PDF location. I did not read the original article, and it is intentionally **absent from the citation-ready bibliography**. BT definitions used here are supported by the actually read Chiang, Zheng/Huang context and the current study's explicit mathematical specification. If the manuscript cites the original as a consulted paper, an owner must first obtain and read it; do not silently equate metadata verification with full-paper reading.

## Supported language and language to avoid

| Supported wording | Unsupported escalation |
| --- | --- |
| A specified exact-refit witness reverses the initial selected score contrast | The minimum number of corrupt votes is k |
| Sensitivity differs across these snapshots and specifications | Evaluation design X inherently causes less robustness |
| Shared MT schedule/N yields a descriptive label-source contrast | Experts or LLM judges are causally more reliable in general |
| Very small counts coexist with unresolved baseline gaps here | Adversarial robustness is equivalent to statistical significance |
| Reproducible empirical extension of influence-based audits | First leaderboard sensitivity method or new influence theory |
| Conditional ridge-BT ranking of this public snapshot | Recreated current official Arena leaderboard |
| Historical decisive-label sensitivity intervention | Practical live vote-rigging exploit |

No withheld content was identified, sought or knowingly encountered in this literature workflow. This statement does not infer its identity; expressly permitted starter content is allowed regardless of topical similarity.
