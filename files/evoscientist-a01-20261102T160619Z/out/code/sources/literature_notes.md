# Restricted original-source literature notes

Accessed: 2026-11-02 (UTC). Scope: exactly the seven user-permitted works, with no discovery searches, citation following, recommendations, citation graphs, derivative pages, or attempt to identify the unspecified forbidden work. No study implementation was performed.

**Purpose:** a modest, verified background basis for an independent counterfactual score-edit comparison of mean, median, and Borda. This is not a comprehensive literature review, an assessment of priority, or evidence for a first-of-kind claim.

**Evidence standard:** metadata checked against original arXiv citation metadata and PDF front matter, or the original Zenodo record. All locators below are 1-indexed PDF pages in the cached versions. Selected pages/sections were read, not entire papers. Cached full PDFs/HTML/page-text JSON include unread material; caching does not mean reading. `access_log.md` specifies exact scope, redirects, and incidental boundary exposures. No identifiable forbidden work was recognized; because its identity is unspecified, identity-based exclusion cannot be certified. No attempt was made to infer it.

## 1. Verified source register

| Ref / BibTeX key | Verified title and authors | Year and exact cached version | Reading level |
|---|---|---|---|
| [1] `hendrycks2021mmlu` | **Measuring Massive Multitask Language Understanding** — Dan Hendrycks; Collin Burns; Steven Basart; Andy Zou; Mantas Mazeika; Dawn Song; Jacob Steinhardt | Initially posted 2020-09-07; PDF says ICLR 2021; cached arXiv v3, 2021-01-12. Bibliography uses conference year 2021. | Abstract, benchmark-definition and evaluation excerpts; not full paper. |
| [2] `liang2023helm` | **Holistic Evaluation of Language Models** — Percy Liang and 49 additional authors; complete checked list in `references.bib` and cached citation metadata | Initially posted 2022-11-16; PDF says TMLR 08/2023; cached arXiv v2, 2023-10-01. Bibliography uses publication year 2023. | Abstract, accuracy/calibration sections, selected adaptation passages; not full paper. |
| [3] `dehghani2021benchmarklottery` | **The Benchmark Lottery** — Mostafa Dehghani; Yi Tay; Alexey A. Gritsenko; Zhe Zhao; Neil Houlsby; Fernando Diaz; Donald Metzler; Oriol Vinyals | 2021; cached arXiv v1, 2021-07-14 | Abstract; §3 and case studies/aggregation excerpts pp. 6–9. |
| [4] `lanctot2023evaluating` | **Evaluating Agents using Social Choice Theory** — Marc Lanctot; Kate Larson; Yoram Bachrach; Luke Marris; Zun Li; Avishkar Bhoopchand; Thomas Anthony; Brian Tanner; Anna Koop | Initially posted 2023-12-05; cached arXiv v4, 2025-06-28. PDF also displays 2023-12-11 near its title and a 2025 copyright. Bibliography uses initial preprint year 2023 and explicitly notes revision. | Abstract and body pp. 3–7; no full empirical reading, references, or appendices. |
| [5] `zhou2023benchmarkcheater` | **Don't Make Your LLM an Evaluation Benchmark Cheater** — Kun Zhou; Yutao Zhu; Zhipeng Chen; Wentong Chen; Wayne Xin Zhao; Xu Chen; Yankai Lin; Ji-Rong Wen; Jiawei Han | 2023; cached arXiv v1, 2023-11-03 | Abstract; experimental setup p. 3, continuation/Table 1/results excerpt p. 4. |
| [6] `chen2026leaderboard` | **Leaderboard Incentives: Model Rankings under Strategic Post-Training** — Yatong Chen; Guanhua Zhang; Moritz Hardt | 2026; cached arXiv v1, 2026-03-09 | **Abstract-only evidence.** First-page introduction also incidentally displayed, but no methods, theorem assumptions, proofs, or result sections read. |
| [7] `sutawika2023harness` | **EleutherAI/lm-evaluation-harness: Major refactor** — Lintang Sutawika and 29 additional credited contributors; full checked list in `references.bib` and original record metadata | Original Zenodo publication date 2023-12-04; software version **v0.4.0**; DOI **10.5281/zenodo.10256836** | **Original software-record metadata only**, not a paper or source-code review. |

Full author lists and title/date metadata were checked programmatically from the permitted originals. Unusual contributor handles in [7] are retained, not silently replaced with guessed real names. No venue was inferred for works lacking an explicit verified venue.

## 2. Source-specific evidence and permitted uses

### [1] MMLU — benchmark dimensions and evaluation provenance

Original: https://arxiv.org/abs/2009.03300 ; cached original PDF: `permitted_cache/2009.03300.pdf`.

**Actually read:** original metadata/abstract; p. 1 including incidental introduction; §3 general definition pp. 3–4 until §3.1; §4.1 pp. 5–6 including prompt details; §4.2 p. 6 excerpt, not the continuation. Related work and references were not intentionally read.

- **Supported claim:** MMLU is a 57-subject multiple-choice benchmark. §3, p. 3: “There are 57 tasks in total”. It is a plausible source of task coordinates, not itself evidence about score-edit robustness.
- **Splits:** §3, p. 3 reports 5 development examples per subject, 1,540 validation questions, and 14,079 test questions, with at least 100 test examples per subject. The validation set is described as usable for hyperparameter selection. The same passage reports 15,908 total questions; the stated split counts, including 57×5 development examples, sum to 15,904. Do not silently reconcile this paper-internal discrepancy; verify an actual pinned dataset release before analysis.
- **Metric/weighting:** §4.1, p. 5 describes classification accuracy “across all examples and tasks”; Table 1 explicitly says “Average weighted accuracy”. This does **not** justify calling an equal-subject mean an exact reproduction of that table. Keep sample weighting, task weighting, and broad-domain weighting distinct.
- **Prompting:** §4.1 continuation, p. 6 uses up to five demonstrations; the prediction is the highest-probability option among A/B/C/D; the development examples are fixed per subject. Changing prompting or scoring conventions changes the score matrix.
- **Availability:** the benchmark is described in the original text. No benchmark repository/dataset was opened in this task; an exact downloadable dataset revision or license was not independently verified.
- **Limit:** no claim here that one score-edit unit corresponds to a realizable model update, or that a different aggregation is benchmark-author endorsed.

### [2] HELM — standardized evaluation, heterogeneous metrics, uncertainty

Original: https://arxiv.org/abs/2211.09110 ; PDF: `permitted_cache/2211.09110.pdf`.

**Actually read:** p. 1 metadata/abstract; §4.3 p. 27; §4.4 pp. 27–28 through the next heading; §7 excerpts pp. 45–46; a short prompt-formatting continuation on p. 47 cut at its first §8.2 cross-reference. **No §8 experimental-results section was read.**

- **Supported claim:** the original HELM evaluation uses seven general metric categories across 16 core scenarios where possible (abstract, p. 1). This motivates retaining scenario/metric identities rather than treating every numerical entry as interchangeable.
- **Metric meanings:** §4.3, p. 27 uses “accuracy” as an umbrella: exact match for classification, word-overlap F1 for QA, MRR/NDCG for retrieval, and ROUGE for summarization. Scores need explicit direction and scale conventions before cardinal aggregation; that normalization recommendation is our planning implication, not a HELM theorem.
- **Calibration protocol:** §4.4 and Figure 17, p. 28: “we use 10 bins in practice”; default ECE bins contain equal numbers of predicted probabilities. Selective classification includes accuracy at coverage C=0.1 and area under the coverage–accuracy curve. Figure 17's two-bin illustration is not the actual default. Calibration of example-level predictive probabilities is distinct from leaderboard stability.
- **Prompting/repeats:** §7, pp. 45–46 uses five in-context examples when included, fixes them across evaluation instances, and repeats experiments three times varying in-context selection. Table 7, p. 46 lists a 1,000-instance evaluation cap and three runs for its three illustrative scenarios; this is **not** asserted here to specify every HELM scenario or a universal train/test split.
- **Availability:** abstract p. 1 states that raw prompts/completions and a modular toolkit are released. Links printed in the original were not visited; no live export/schema, current coverage, or exact matrix snapshot was checked.
- **Limit:** do not infer a complete model×task matrix from the existence of the benchmark, conflate metrics with incompatible meanings, or describe a score-edit test as ECE calibration.

### [3] The Benchmark Lottery — task-selection and aggregation sensitivity

Original: https://arxiv.org/abs/2107.07002 ; PDF: `permitted_cache/2107.07002.pdf`.

**Actually read:** metadata/abstract; §3 start and §3.1 case studies pp. 6–9; §3.2 p. 9 excerpt, not its continuation. The recommendations section (§7) was not read.

- **Supported claim:** leaderboard order can depend on the selected task subset. §3.1.1, p. 6 recomputes mean-aggregate rankings over subsets of eight SuperGLUE tasks. Among 70 four-task subsets, the authors report six distinct top-1 models. Evidence anchor: “6 different possible top models”. This is a task-subset intervention, not a target-row score-edit intervention.
- **Metrics:** their case studies report top-k ranking disagreement and Kendall rank correlations (§3.1, pp. 6–9). These are available templates for descriptive stability checks, not evidence for an exact minimal edit cost.
- **Mean versus median:** §3.1.4, p. 9 discusses Atari human-normalized scores, where a few games can dominate the mean; it reports disagreement between mean and median aggregations. Evidence anchor: “mean and median in this case do not agree”. Do not universalize this to all benchmarks or conclude median always resists targeted edits.
- **Rank aggregation:** §3.2, p. 9 explicitly describes averaging per-task ranks as an alternative to aggregating absolute score differences. It also discusses task scale, headroom, difficulty, and overrepresented domains. This is relevant motivation for comparing cardinal and ordinal aggregation.
- **Data/availability:** case studies include SuperGLUE, VTAB, LRA, and RL Unplugged. Only the permitted paper was read; its linked leaderboards/ancillary files and the papers it cites were not opened. No extracted leaderboard dataset is supplied by this research task.

### [4] Voting-as-Evaluation — an ordinal aggregation basis including Borda

Original: https://arxiv.org/abs/2312.03121 ; PDF: `permitted_cache/2312.03121.pdf`.

**Actually read:** original metadata/abstract and incidental first-page introduction; body pp. 3–7. The directly relevant evidence is on pp. 4–7; no reference list, full empirical section, or technical appendix was read.

- **Supported claim:** VasE maps agents to alternatives and tasks/environments to voters; tasks supply rankings or pairwise comparisons. “Voters are different tasks or environments” (VasE passage, p. 6). Cross-task numerical comparability is not assumed there.
- **Scoring rules/Borda:** “Social Choice Theory Basics”, p. 5 defines nonincreasing position-score vectors, sums scores across voters, and lists Borda among scoring rules. This is a narrow original-text basis for including Borda as an ordinal comparison, not a new Borda formulation.
- **Trade-offs:** the same p. 5 passage states that scoring rules satisfy population consistency but are not Condorcet consistent. Do not describe Borda as satisfying all desirable voting properties, or equate this axiomatic discussion with our proposed counterfactual robustness metric.
- **Concrete evaluation:** “Empirical Evaluation” / “General Reinforcement Learning Agents”, p. 7 uses eight agents and 54 Atari games, with one complete preference ranking per game. Table 2 includes Borda; the paper reports a shared top-ranked agent across its nine methods in this example. This is not evidence that aggregators always agree.
- **Unverified details:** the exact Borda treatment of tied task scores, normalization, missingness, and any source-code tie-breaking were not established by the sections read. A half-credit-for-ties convention in an independent study must be explicitly defined as that study's convention, not attributed to this source.
- **Availability:** source code and experimental files were not accessed. No code-availability claim is verified here.

### [5] Benchmark leakage — observed score changes are not general capability changes

Original: https://arxiv.org/abs/2311.01964 ; PDF: `permitted_cache/2311.01964.pdf`.

**Actually read:** original metadata/abstract; §2.1 p. 3 and continuation p. 4; Table 1 and §2.2 excerpt p. 4. The full analysis and suggestions section were not read.

- **Supported claim:** the paper experimentally distinguishes continued training on benchmark-related training sets, addition of evaluation prompts, and the extreme case of training on the test sets (§2.1, p. 3). “test set” leakage and benchmark-specific training are not identical interventions.
- **Protocol:** MMLU is evaluated 5-shot; seven QA tasks are evaluated zero-shot; selected reasoning tasks use chain-of-thought prompts; reading-comprehension procedures differ (§2.1, p. 3). Thus its table entries are not a homogeneous metric/protocol by default. Four backbones are listed across pp. 3–4: GPT-Neo-1.3B, phi-1.5, OpenLLaMA-3B, LLaMA-2-7B.
- **Observed example:** Table 1, p. 4 reports phi-1.5 MMLU accuracy 42.87 without the added leakage training and 75.05 under the extreme all-training/test-set-plus-prompt condition. The source explicitly warns that the extreme test-set-leakage case “should never occur” (§2.1, p. 3). These are controlled study results, not allegations about a live leaderboard.
- **Use in our framing:** distinguish sensitivity of an observed score matrix from claims about contamination, achievable resource costs, or improvements in latent/general capability. A mathematical score edit is not a demonstrated training procedure.
- **Unverified details:** no code link was followed, training settings were not reproduced, and the complete optimizer/training recipe was not read. Do not copy its leakage setup as a proposed experiment here.

### [6] Strategic post-training incentives — abstract-only conceptual background

Original: https://arxiv.org/abs/2603.08371 ; PDF: `permitted_cache/2603.08371.pdf`.

**Evidence level: abstract only**, PDF p. 1 and matching original arXiv abstract. Metadata and the first-page opening introduction were also displayed. No theorem assumptions or proofs were checked.

- **Supported claim:** the abstract frames benchmarking as a “Stackelberg game” between a benchmark designer and competing developers who can allocate resources to benchmark-specific score improvements. This motivates separating observed leaderboard movement from latent model quality.
- The abstract reports nonexistence of developer Nash equilibrium for the benchmark games it studies and a positive tune-before-test result under conditions. Since those conditions were not read, these are only **author-reported abstract claims**, not independently checked results or statements about all real leaderboards. They are not needed for the proposed score-edit study's validity.
- No task-specific score matrix, evaluation split, code availability, or implementable cost model was verified. Do not transfer its game-theoretic conclusions to mean/median/Borda edits.

### [7] Evaluation Harness — versioned software provenance only

Original DOI: https://doi.org/10.5281/zenodo.10256836 ; resolves to the same original record https://zenodo.org/records/10256836 . Cache: `permitted_cache/zenodo.10256836.landing.html` and `zenodo.10256836.verified_metadata.json`.

**Actually read:** original citation meta tags and JSON-LD metadata; no source archive, README, repository, PR, or other linked page was opened. A short change-log prefix was incidentally displayed but not used as evidence.

- **Supported claim:** the record identifies an archived software release titled “EleutherAI/lm-evaluation-harness: Major refactor”, version v0.4.0, published 2023-12-04. Locators: HTML `citation_title`, `citation_author`, `citation_doi`; JSON-LD `name`, `author`, `datePublished`, `version`, `@type=SoftwareSourceCode`.
- The JSON-LD record license field points to CC BY 4.0. This is **record metadata**, not a verified claim about the license of every code dependency or dataset.
- **Use:** a versioned software citation can anchor evaluation provenance if that release is actually used later. It does not establish the exact task definitions, prompt templates, aggregation weights, current task support, or equivalence of results across harness versions.
- No evaluation was run and no release archive was downloaded. Do not claim this task verified the harness implementation.

## 3. Conservative related-work wording

> Benchmark rankings can depend on which tasks are included and on how their scores are aggregated; The Benchmark Lottery documents task-subset sensitivity and disagreement between mean and median summaries [3, §3.1, pp. 6–9]. Voting-as-Evaluation provides an ordinal task-as-voter perspective and includes Borda among scoring-rule aggregators [4, pp. 5–7]. MMLU and HELM illustrate the importance of preserving evaluation units and protocol details [1, §3–4.1; 2, §4.3–4.4, §7]. Benchmark-leakage experiments and an abstract-level strategic-incentives formulation additionally caution against equating observed score movement with general capability gains [5, §2.1–2.2; 6, abstract]. Against this limited background, our study separately defines and measures counterfactual target-score-edit sensitivity under mean, median, and Borda.

The last sentence describes the intended independent study, **not** a novelty conclusion or a claim that the cited works omit a topic. Do not write “first”, “no previous work”, “comprehensive”, or “state of the art” based on these notes. The software citation [7] belongs with actual evaluation provenance, if used, rather than being treated as a theoretical result.

## 4. Recommended next experiments / protocol decisions (not source-established findings)

No implementation or experiment was performed. The following are prospective planning implications, clearly separated from the literature claims above.

1. **Pin one complete matrix before comparing aggregators.** Record benchmark/dataset revision, model roster, task IDs, metric directions/scales, prompt/scoring protocol, task/sample weighting, and missing-data policy. Use the same frozen entries for all three aggregators. Motivation: task-selection/scale effects [3], MMLU weighting and prompt details [1], HELM's heterogeneous metrics and repeat protocol [2]. Expected benefit: avoid attributing an input/protocol change to an aggregation rule.
2. **Declare the counterfactual, ties, and success criterion.** Specify whose coordinates may change, upward-only or signed edits, allowed bounds, strict-first versus shared-first success, and whether the objective is number of edited tasks, total magnitude, or a lexicographic combination. Define even-task median, Borda task ties, and final leaderboard ties. The exact optimization problem and tie conventions are independent study definitions, not claims supplied by these sources.
3. **Compare sensitivity, not alleged cheating or training feasibility.** Report support and magnitude separately; distinguish a mathematical edit from a realizable post-training action. Compare fixed-roster mean/median/Borda results, with task-ablation or leave-one-task-out diagnostics as a separately labeled intervention [3]. Expected outcome is diagnostic comparison; no winner among aggregators is presupposed.
4. **Treat uncertainty and calibration separately.** Where prediction-level data exist, preserve repeated evaluation runs and report uncertainty for score differences; preserve the original ECE convention if reporting calibration [2]. With an aggregate matrix only, do not claim prediction calibration or invent confidence intervals. A changed aggregate ranking is not by itself evidence of contamination or changed general capability [5–6].

## 5. Artifact map and limitations

- `literature_notes.md`: this source-bounded evidence register and protocol implications.
- `references.bib`: seven machine-readable, verified entries; complete author lists; preprint-versus-publication/revision dates documented.
- `access_log.md`: every network request and redirect outcome, exact reading scope, and bounded incidental exposures.
- `permitted_cache/*.pdf`: six original PDFs.
- `permitted_cache/*.landing.html`: seven original landing pages, including the original software record.
- `permitted_cache/*.metadata.json`: extracted original landing metadata. Zenodo's full metadata cache contains an unread long description; use its `verified_metadata.json` for the safe subset.
- `permitted_cache/*.pages.json`: complete mechanically extracted PDF text by page, **including unread references**. For restricted continuation, do not read these files wholesale.
- `permitted_cache/selected_reading_batch*.json`: specifically exposed reading excerpts (with source IDs and page numbers).
- `permitted_cache/manifest.json`: file sizes and SHA-256 hashes for reproducible cache identification.

All seven exact works were available. The first DOI attempt was blocked by a conservative redirect guard, then the exact same-work resolution succeeded. No citation rests on an unavailable or unverifiable work. No code repository, live leaderboard, dataset download, reference target, or forbidden-paper identification was accessed. The bounded incidental introduction/reference-like-line/change-log exposures are documented in the access log; they are not presented as a perfect zero-exposure guarantee.

### Sources

[1] Hendrycks et al., *Measuring Massive Multitask Language Understanding*: https://arxiv.org/abs/2009.03300

[2] Liang et al., *Holistic Evaluation of Language Models*: https://arxiv.org/abs/2211.09110

[3] Dehghani et al., *The Benchmark Lottery*: https://arxiv.org/abs/2107.07002

[4] Lanctot et al., *Evaluating Agents using Social Choice Theory*: https://arxiv.org/abs/2312.03121

[5] Zhou et al., *Don't Make Your LLM an Evaluation Benchmark Cheater*: https://arxiv.org/abs/2311.01964

[6] Chen et al., *Leaderboard Incentives: Model Rankings under Strategic Post-Training*: https://arxiv.org/abs/2603.08371

[7] Sutawika et al., *EleutherAI/lm-evaluation-harness: Major refactor*, v0.4.0: https://doi.org/10.5281/zenodo.10256836
