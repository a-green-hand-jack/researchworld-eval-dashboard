# Study plan: stability of pairwise-comparison leaderboards (story-repo)

Status: v2 (2026-11-04; revised after idea-review-repo#3 feasibility judgement and venue choice NeurIPS 2026, 9 pages). Owner: story-repo. Authority: `Research objective` (#1) wins over this file.
Division of delivered paths: `.forgejo/CODEOWNERS` in paper-repo. Open questions are marked **[open]**.

## 1. Question

How much must the comparison data under a Bradley-Terry (BT) leaderboard change before a ranking *claim*
changes, when the change is (a) benign noise, (b) the worst case chosen by an adversary, and does this differ
between evaluation designs (crowd votes, expert labels, LLM-judge labels, sports)?

Operational sub-questions (each is answered, or reported unanswered, in the paper):

- **Q1 Magnitude.** For each dataset, how large is the smallest data change (the *flip budget*) that reverses a ranking claim?
  Claims: C1 identity of rank 1; C2 order of each adjacent pair (rank r vs r+1); C3 membership of the top-k set (k=3,5,10 where the dataset has that many participants); C4 whole-ranking agreement (Kendall tau) as a secondary, non-flip metric.
- **Q2 Noise vs. worst case.** How does the flip budget under adversarial removal compare with what random removal / label noise / bootstrap resampling does to the same claims? (Random-noise baseline is the reference scale, not only a foil.)
- **Q3 Explanation.** Is cross-claim and cross-dataset variation in flip budget explained by statistical margin alone (score gap divided by its standard error, comparison counts of the two participants, graph connectivity), or is there a residual dataset difference after z-gap, pair counts and N-matching? "Design" is confounded with dataset, N, K and graph (3-4 datasets), so it is read only as that residual dataset difference, never as a causal effect of crowd / expert / sports as a category; NBA seasons give within-sports variation only.
- **Q4 Matched designs.** Where the same items carry different label sources (MT-Bench human vs GPT-4 judgments on the same pairs; optionally Arena battles with LLM-judge labels), how does fragility change when only the labeller changes?
- **Q5 Modelling choices.** Does the answer depend on analysis choices (tie handling, regularisation, home/side effect, model-pair subsets, claim definition)? A "depends on conditions" or "small sensitivity" outcome is acceptable; the paper reports what the evidence supports.
- **Q6 Method validity.** Is the cheap influence-based search for adversarial removals a reliable guide? Judged against exact refits and against brute-force/exhaustive search on small instances.

No expected direction is assumed. Results contradicting prior expectations are reported as they are.

## 2. Data (from `data.md`; versions fixed there)

| Tier | Dataset | Design | Role |
| --- | --- | --- | --- |
| Primary | Arena human preference 55k (`train.csv`) | crowd votes, ~60 models, ties | main crowd dataset |
| Primary | MT-Bench human judgments | expert labels, 6 models | expert design |
| Primary | MT-Bench GPT-4 pair judgments (same file repo) | LLM judge on the *same* pairs/questions | Q4 matched labeller |
| Primary | NBA Elo history (`nbaallelo.csv`, use `_iscopy==0`, regular season only) | sports, per-season fits (~30 teams, ~70 seasons) | sports design; full history is a non-stationary mix of eras, so only an ablation |
| Optional | Arena 140k (needed columns only) | crowd, larger N | replication only, after stage 2; adds no new design |
| Cut | potsawee LLM-judge labels (no declared license), WebDev Arena (agreement terms) | - | Q4 already has a matched pair in MT-Bench; not used, not counted toward the two-design requirement |
| Control | Synthetic BT data matched to each real dataset's pair-count matrix and fitted scores | model-correct i.i.d. | **must be labelled synthetic everywhere**; separates "design = data generating process" from "design = comparison graph and N" |

Raw data stay in `data/` outside the repository; checksums/versions go into the reproduction notes. The fixed set of >=2 designs required by the objective is met by the four primary rows (crowd, expert, LLM judge, sports).

## 3. Method

### 3.1 Model and claims
BT fitted by (lightly L2-regularised, sum-to-zero or anchored) logistic regression on win/loss; ties: default = half a win for each side (equivalently duplicate rows with weight 0.5), ablation = drop ties. Same estimator across all datasets; check it against an independent implementation (e.g. scikit-learn / statsmodels) and against the Arena-style bootstrap rank intervals on Arena 55k. NBA: win/loss only (no ties, unlike the others); home advantage as an ablation (it is a modelling choice, not part of the plain leaderboard).

Ranking is by BT score. Claim set as in Q1; the claims are about the point ranking (public leaderboards also show bootstrap rank intervals; one CI-based claim, "the interval of model m contains rank r", is evaluated on final witness sets in an ablation and the limit is stated). Claim counts differ by dataset (MT-Bench K=6: C1, 5 adjacent pairs, top-3 only; no k=10 where K<~20); report per dataset first and weight pooled analyses by dataset. For Arena the leaderboard-relevant claims are restricted to the top ~20 participants by comparison count to avoid claims about thinly-compared models, with the all-participant version as an ablation. The set is fixed on the full data before any perturbation.

### 3.2 Perturbation families (each gives a size on a stated scale)
1. **Random (benign) removal** of a fraction f of comparisons, many seeds -> probability that each claim survives, as a function of f.
2. **Random label flips** of a fraction f (noise model), same readout.
3. **Bootstrap / subsample** over comparisons (the leaderboard's own uncertainty); gives the per-claim noise scale and the z-gap.
4. **Adversarial removal**: smallest set of comparisons whose deletion reverses a claim. Method route: first-order influence of each comparison on the score gap (Koh & Liang style influence for the BT MLE / Broderick et al. approximate maximum influence perturbation), greedy selection, then **exact refit to verify**; the reported budget is the verified upper bound. Cheap baseline heuristics for comparison: remove the wins of the higher-ranked over the lower-ranked in the pair; remove comparisons involving the pair ranked by naive count. Re-linearised greedy (recompute influences every batch) and a randomised/beam variant. Exhaustive search only on small subsampled instances (about 30-60 comparisons, budget <= 4-5) as the validity reference (Q6). A found set is a *witness*: the reported budget is an upper bound on the true minimum (it is a lower bound on sensitivity); no exact minimum is claimed, and the abstract says so. Exact refits are cheap (about 0.01-0.05 s per BT fit, measured in idea-review-repo notes on synthetic data), so every candidate is verified; influence-only numbers are never reported as results.
5. **Adversarial addition / relabelling** (vote rigging, cf. Min et al. 2025): smallest number of added or flipped comparisons that reverse a claim, restricted to the same participants. Secondary: a single clear table, not a family of analyses.

All the budgets are integers of comparisons, convertible to fraction of N.

### 3.3 Comparable size scale across datasets (to be fixed by experiment-repo, justified in the paper)
Raw count and raw fraction of N are not comparable across datasets with N from 3e3 to 6e4 and K from 6 to 126. Report at least:
- budget as a fraction of all N and as a fraction of the comparisons involving the two participants of the claim;
- a *random-reference scale*, fixed in stage 0 before stage-1 numbers exist: either the fraction f* at which random removal reverses the claim with probability p (may not be reached for large z), or the *leverage ratio* = adversarial budget / the number of random removals giving the same RMS shift of the score gap (random removal has mean-zero effect, so an "SE-sized" shift is not a usable unit). experiment-repo defines it and shows it in a pilot. Agreed refinement (experiment-repo, stage 0): the "one SE" unit is degenerate (random removal of fraction r shifts the gap by SD = SE*sqrt(r/(1-r)), so one SE is r=1/2 for every dataset); use leverage L = gap / SD of the shift that random removal of the same k comparisons produces, P(random removal of k flips the claim), and k/sqrt(N), alongside the raw fractions. The regressions carry both z-gap (gap/SE) and the influence-score signal-to-noise (gap / spread of per-comparison influences) as regressors (idea-repo Brief section 7);
- budget versus z-gap (gap / SE) per claim, which tests Q3 directly (regression of log budget on log z-gap and log pair counts with dataset-specific intercepts; uncertainty by bootstrap over claims within a dataset and, for NBA, over seasons; no cluster-level inference over the 3-4 datasets).
N-matched subsampling of the larger datasets (Arena down to MT-Bench / NBA-season sizes and the converse where possible) is required to separate dataset from size.

### 3.4 Uncertainty and controls
Seeds are fixed and listed; random-noise results use >=100 seeds with percentile intervals; bootstrap for the base fit uses >=1000 resamples; adversarial budgets get an interval from reruns on bootstrap resamples (about 100) of the dataset, with the 1000-resample bootstrap used only for the base fit and the final witness sets, not inside the greedy loop. Claims are not independent: see 3.3. Multiple comparison caveat stated, no p-value hunting. Synthetic matched controls (same pair counts and fitted scores, model-correct i.i.d. labels) are what separate "graph and N" from the data-generating process. Matched labeller (Q4): compare on the (question, turn, unordered pair) keys present in both MT-Bench files: 1,814 keys with outcomes put in a canonical orientation (main; experiment-repo's count), and the 1,232 keys whose presentation order also matches as the robustness variant (the human file has 3,355 rows but 2,396 unique keys; say whether multiple judges per key are separate comparisons, default yes as in the raw file); state how "tie (inconsistent)" (16% of GPT-4 rows) maps to a tie; GPT-4 labels skew to position B, so position bias is part of the labeller effect. With 6 participants and 15 pairs report budgets with bootstrap intervals and make no regression claims there.

## 4. Division of work (the split follows function)

| Position | Delivers | Path in paper-repo |
| --- | --- | --- |
| experiment-repo | Data loaders + checksums, BT fitter and its validation, all perturbation analyses, result tables as CSV/JSON with input provenance, all analysis code, run scripts, seeds and runtimes | `code/`, `results/` |
| figtab-repo | Figures and tables for the claims in section 5 with generator scripts, input manifest, captions | `figures/`, `tables/` |
| venue-repo | Chosen conference (ICML/ICLR/NeurIPS latest), its template/style files, page limit, checklist requirements | `venue/` |
| paper-repo | The paper (LaTeX + PDF), checklist filled, reproduction README, the release pull request | `paper/`, `README.md` |
| idea-repo | Related-work/brief: BT, Arena, influence-function and robustness literature, conventions to follow | wiki (no delivered path) |
| story-repo | This plan, the claim map (section 5), the `CODEOWNERS` | `.forgejo/CODEOWNERS` |
| review positions | feasibility, internal and external review | none |

Order of work: stage 0 (loaders, fitter and its validation, base leaderboards + bootstrap CIs, real fit timings, the scale definition piloted) -> stage 1 (random removal/flips, synthetic matched control, verified adversarial removal on all primary datasets, validity table, MT-Bench matched pair) -> stage 2 (regressions, N-matching, z-gap analysis) -> stage 3 (ablations limited to tie handling, regularisation strength, home advantage; adversarial additions; Arena 140k). Stage 0-1 alone is a coherent paper on >=2 designs; stage 2 supports the cross-dataset claims; stage 3 is added value, and E8 is dropped first if time is short. Independent work (venue choice, related work, template, figure code against stage-0 outputs) goes in parallel and does not wait.

Main text (9 pages, NeurIPS 2026): E1 (compact), E2, E3, E4, E5, E6; E7 and E8 in the appendix.

## 5. Claim map (what the paper's evidence must show; figure/table owner = figtab-repo)

| Id | Claim to be supported or refuted | Evidence | Display |
| --- | --- | --- | --- |
| E1 | Descriptive: each dataset's participants, comparisons, per-pair count distribution, scores with CIs and rank intervals | base fits | Table 1 + leaderboard-with-CI figure per dataset |
| E2 | Survival of claims under random removal/flips vs f | perturbation family 1,2 | survival curves per dataset, bands over seeds |
| E3 | Verified adversarial flip budgets per claim (C1-C3) per dataset on the common scales | family 4 | budget distributions (adjacent-pair claims as a function of rank), with and without the noise-equivalent scale |
| E4 | Budget explained by z-gap (or not) and residual design effect | regressions | scatter budget vs z-gap, coloured by design, with fit and intervals; coefficient table |
| E5 | Matched-labeller comparison (MT-Bench human vs GPT-4) | families 3-4 on same pairs | paired display |
| E6 | Method validity: influence guess vs exact refit; greedy vs exhaustive; vs heuristic baselines | Q6 | table/figure of budgets by method |
| E7 | Robustness to modelling choices (tie handling, regularisation, home advantage) and N-matching, synthetic controls | ablations | one compact appendix table; synthetic control in the main text (it is part of reading E3/E4) |
| E8 | Adversarial additions (rigging) vs removals | family 5 | one appendix table, optional |

The paper must also state: applicability (BT-fit leaderboards with this comparison design), the limitations (single estimator family, public snapshots, no user ids, ties, synthetic control is not real data), and which results are upper bounds (verified witnesses) rather than exact minima.

## 6. Constraints and guardrails

- Data details from idea-repo's Brief that bind the analysis: NBA rows are duplicated per game (`_iscopy`): de-duplicate before any count; NBA is non-stationary, so per-season (or window) fits are the main sports unit; Arena has A/B position effects and non-uniform pair sampling (report the comparison-graph sparsity); tie / "both bad" handling is a stated choice with an ablation.
- Reproduction notes must contain: LLM-use disclosure, a log of the forbidden-content rule (even if "none encountered"), data sources / versions / checksums. The paper discloses LLM assistance.

- CPU only; the whole analysis should fit in the one-week limit; a single BT fit is seconds. Long runs go through `ht-resource run`.
- Every number in the paper comes from a result file produced by code in `code/`.
- **Task independence rule.** The task forbids reading the earlier published paper that studied this question. Starter-literature entry 8 (Huang et al. 2025, "Dropping Just a Handful of Preferences ...") looks like that paper or closely related to it from its title. I recommend that no position opens it, its mirrors, or pages that discuss it, and that nobody searches for the title/authors. If it was seen by accident, record it in the reproduction notes as `deliverable.md` requires. Cite entries 1-7 as appropriate after actually reading them. Whether entry 8 can be listed as a reference without being read is for paper-repo with idea-repo; I advise against making any claim about its content.
