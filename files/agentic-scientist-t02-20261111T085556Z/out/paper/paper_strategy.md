# Paper strategy (paper_standalone, ICLR 2026 single-column, 8-9 body pages)

**Status:** ready.

## Provisional title
Is Grokking Delay Width-Dependent? A Censoring-Aware Seed-Cluster Slope Test on Modular Addition Finds No Resolvable Trend

## Central question
In a one-layer transformer trained with AdamW on modular addition (p=97, train fraction 0.4, weight decay 1.0, full batch, 10,000-step limit), does the delay between fitting the training set and generalizing decrease with width, as a pre-declared seed-cluster slope test can detect?

## Central thesis
The sealed final evaluation (outcome `qualified`, status completed, correct true; 4 seeds x 5 widths 16-256) measured a ln(delay)-vs-log2(width) slope of -0.020 with 95% seed-cluster bootstrap CI [-0.585, 0.354]. Under the pre-declared rule (CI entirely below zero = supported; at/above zero = refuted; straddling = inconclusive) the verdict is **inconclusive**. 40% of runs were censored at the step limit. The paper's contribution is a calibrated inconclusive measurement, a censoring-aware test design with explicit resolution limits, and an inventory of what the evidence cannot say.

"Qualified" means the evaluation ran validly. It does not mean the width hypothesis was supported. Gate diagnostics beyond `final.qualification.*` are unknown and must be stated as such.

## Why this framing (and not the others)
- Capacity-crossover story (t_mem vs t_gen, critical width vs train fraction): no such results exist in the artifacts. Rejected.
- Lazy-to-rich / effective-learning-rate confound explanation: the hidden-exponent sweep script was written but never executed, so no comparison across reparametrization strengths exists. The frozen model contains the reparametrization, but its effect is not isolated. Listed as untested.
- "Best search score" story: scores come from a different data plane, 2 seeds each, with an undisclosed score formula, and ordering is not monotone with censoring. Descriptive context only.
- No downstream_study block, no edit context: fresh framing; the prior-story status is `rejected` only in the sense that nothing is carried over.

## Method groups
1. Frozen evaluated model variant (proposed): one-layer transformer, last-position forward, init scale 0.5, reference width 128, output exponent 0.5, hidden reparametrization exponent 0.5.
2. Evaluator-owned reference trainer (baseline): single-seed slope -0.368, inside the CI; no significance claim, and no attribution of the gap to the reparametrization.
3. Control episodes (supporting): control max validation accuracy 0.0122; missing episodes 0.
4. Search-phase variants (descriptive ablation-like context): scores 0.798 / 0.828 / 0.850, censored fractions 0.667 / 1.0 / 0.667, 2 seeds each. Kept separate from final.

## Results focus
- Slope, CI and verdict, with the reference slope for cross-check.
- Resolution analysis (derived from manifest values): delay is floored at 250 and capped at 10,000 steps, so |slope| over 4 width doublings is at most ln(40)/4 ≈ 0.92. The CI (width ≈ 0.94) covers much of that range. With 4 seed clusters the bootstrap is coarse.
- Censoring (0.4) and validity checks.
- Seed-level spread of the evaluator summary score (0.607, 0.733, 0.717, 0.860), described as variability, not performance.
- Explicitly unavailable: per-width/per-seed delays, t_mem/t_gen, d*(f), train-fraction sweeps, hidden-exponent sweep, weight-decay control.

## Figures
1. `protocol_overview` (required, full width, early placement, concept figure via generate-concept-figure): delay definition, censoring, slope test, three-way verdict, this run's outcome marked.
2. `slope_interval_vs_decision_rule` (required, matplotlib, ~0.6 text width, 1 panel): CI, reference point, zero line, decision regions, attainable-slope bound.
3. `search_variants_descriptive` (optional, supplement-friendly, full width, 2 panels x 3 categories): labelled "search phase, 2 seeds, not final".
All figures: export PDF + 300 DPI PNG, reference the PDF in LaTeX, no upscaled rasters.

## Body-page use
Intro ~1.2 pp; related work ~0.8; protocol + frozen model ~2; results ~2 (including the resolution analysis); discussion of alternatives (censoring ceiling, 4 seeds, reparametrization confound, single operation/prime) ~1; limitations/scope ~0.7. No padding. If short, deepen the resolution analysis and move the seed-level table into the main text.

## Supplement
Full protocol/hyperparameters; frozen-model constants; seed-level episode table; descriptive search table; untested hypotheses and unexecuted analyses; LLM usage statement (required by venue).

## Avoid
Headings: search campaign, milestones, progression, cycles, first successful run, Experiment A/B, run log.
Phrases: correctness rate, correct and eligible, combined_score, rubric, winner, any directional width claim, "not qualified", "qualified therefore the hypothesis holds".

## Citations
Only keys in `references.bib` that are relevant: Power2022GrokkingGB, Nanda2023ProgressMF, Liu2022OmnigrokGB, Kumar2023GrokkingAT, Huang2024UnifiedVO; Lyle2024NormalizationAE and Nam2024DecouplingDR only if described accurately. Other starter references (circuit efficiency, double descent, AdamW, etc.) are not in the bib and must not be cited unless added. Unrelated bib entries must not be cited.
