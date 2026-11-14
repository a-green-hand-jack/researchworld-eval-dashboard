# Paper strategy (paper_standalone, ICLR 2026 single-column, 8–9 body pages)

**Status:** ready (bounded claim). **Prior paper story:** rejected (not edit mode; fresh framing).

## Title (provisional)
When Is One Kernel SHAP Run Enough? Predicting Top-3 Attribution Reproducibility from a Single Budgeted Run

## Central question
For a trained tabular classifier explained by a budget-limited Kernel SHAP run, how often does the single run's top-3 feature set agree with independent reruns, and can that agreement be predicted from the run's own coalition data better than trivial and split-half baselines?

## Central thesis
Single-run top-3 reproducibility is conditional: mean agreement is 0.807 at a 4d coalition budget and 0.932 at 16d (final evaluation). A diagnostic computed only from the assessed run beats always-reliable, constant-0.5 and split-half-gap baselines on squared error, but only modestly beats a pairing-permuted control (0.9838 vs 0.9701), so most of its skill is budget-level calibration. Per-instance resolution is limited (Spearman 0.58).

## Why this framing
- The final evaluation completed with outcome **qualified**. Lower bounds are positive against all three baselines and against the permuted control.
- The artifacts do **not** support the broad brief. There is no per-dataset or per-model breakdown, no background-size or retraining-noise study, no deep tabular models and no ablations. These are stated as not done.
- The honest story is therefore narrow: define reproducibility operationally, show it depends on budget, evaluate a single-run self-diagnostic against baselines and a control, and say plainly that the gain over the control is small.
- Search chronology is not the story. Three configurations were scored on the search datasets (3 of 3 scored, none unscored). Scores are 0.9760, 0.9837 and 0.9854, and the per-seed ranges overlap. With no component ablations, no mechanism is attributed. This goes in the supplement.

## Method groups
1. **Reproducibility label (protocol):** mean top-3 Jaccard between the assessed run and 8 reruns; budgets 4d and 16d; 32-row background; logistic regression, random forest and MLP.
2. **Single-run self-diagnostic (frozen selected configuration, proposed):** delete-one-group jackknife over complement-pair folds, 4 partitions, antithetic common-random-number draws, shrinkage toward a budget prior, small margin gate. Constants are hand-set and untuned.
3. **Evaluator baselines:** always-reliable, constant 0.5, split-half-gap heuristic.
4. **Permuted-pairing control:** 20 derangements; isolates instance-specific information.
5. **Search-plane variants (supplement only).**

The original search-time baseline program has no grounded score in `paper_data.json`, so that comparison is omitted.

## Results focus (all from `final.*`, search kept separate)
- Label means 0.8065 (4d) vs 0.9315 (16d).
- Score 0.9838 (= 1 − MSE, so MSE ≈ 0.0162, derived). Seed scores are 0.9850 (seed 9001) and 0.9826 (seed 9002).
- Skill over always-reliable is +0.0353 (lower bound 0.0171).
- Skill over constant 0.5 is +0.1543 (lower bound 0.1245).
- Skill over the split-half gap heuristic is +0.0122 (lower bound 0.0081).
- Diagnostic minus control is 0.0137 (derived), lower bound 0.0101.
- RMSE is about 0.127 vs about 0.227 for always-reliable (derived).
- Only one-sided 2.5th-percentile bootstrap lower bounds exist; no upper bounds.

## Figures (single-column template, text width ≈ 5.5 in; both full width)
- **Fig. 1 `protocol_overview`:** concept figure (generate-concept-figure), page 1–2: model and instance → one run at 4d or 16d → r_hat; evaluator reruns ×8 → Jaccard label; scoring against baselines and control. 1 panel.
- **Fig. 2 `main_comparison`:** matplotlib, 2 panels. (a) Skill over the three baselines and over the permuted control, with lower-bound markers (4 categories). (b) Mean agreement at 4d vs 16d (2 categories). PDF in LaTeX plus 300-DPI PNG.
- **Table 1:** native LaTeX, final metrics, lower bounds, seed scores, derived columns marked.
- The supplement has a small table or figure of the three search-plane scores.

## Supplement
- Protocol and reproducibility details: datasets, models, 20 instances, 8 reruns, 20 derangements, 200 bootstrap replicates, seeds 9001/9002, software versions, disjointness.
- Full metric table and derivations.
- Search-plane configurations, with no mechanism claims.
- Diagnostic constants and provenance, including that the budget prior came from search-plane label means (0.840/0.958) that differ from the final ones.

## Body-page use
No padding. Space goes to framing, formal definitions, an implementable method section, protocol rationale, results and Table 1, a sharp limitations section, and related work. If the evidence cannot honestly fill the 8-page minimum, flag the shortfall rather than padding.

## Forbidden headings and phrases
- **Headings:** search progression, milestones, first valid result, campaign phases, cycle-based headings, Experiment A/B, run log.
- **Phrases:** "correctness rate", "correct and eligible", "combined_score", "eligible", "rubric", "state of the art", "incumbent", and blanket claims that SHAP is or is not reliable.

## Writer cautions
- Per-dataset and per-family claims are not grounded.
- Diagnostics trust is marked unverified, and the constants are untuned.
- `references.bib` is mostly off-topic. Usable entries: Covert2020ImprovingKP, Gupte2025UnderstandingTB and Mitchell2021SamplingPF, possibly Petrosian2024ExplainableAE. The starter references (Lundberg and Lee, Krishna, Nogueira, Webber, Musco and Witter, Chen, Ding) are missing, so re-run retrieve-references for them or do not cite.
- Anonymize the paper, include the LLM Usage section, and fill the checklist.
