# Paper strategy (paper_standalone, ICLR 2026, single-column)

**Status: ready.** Edit mode is not active (no prior manuscript or staged inputs); `downstream_study` is absent from `paper_data.json`.

## Provisional title
Recalibrating the Control Variate in Prediction-Powered Mean Intervals: Small, Regime-Dependent Width Gains over PPI++ with Fixed Labels, Unlabeled Data, and Predictor

## Central question
With labeled set, unlabeled set and predictor all fixed, can a cross-fitted recalibration g(Yhat), added as an extra control variate nested around PPI++, shorten a valid mean interval? By how much, and where does it help or fail?

## Central thesis
Recalibration gives a small, regime-dependent narrowing over PPI++ (final aggregate mean log width ratio 0.022, about 2% in geometric-mean width; 0.070 vs PPI lambda=1; 0.358 vs classical). Gains are concentrated where the predictor is miscalibrated (census_income 0.029, plankton 0.036, synthetic 0.041) and near zero for census_healthcare (0.0018) and census_education (0.0023). Coverage passed the evaluator gate but its point estimates (pooled 0.934, minimum family 0.91) lie below 0.95.

## Qualification status (from `final.qualification.*`)
outcome = **qualified**, status = completed, correct = true, claim_status_code = 2 (narrower than PPI++, coverage not rejected), controls passed, 0 failed episodes. This supports a conditional-support paper. It does not support generalization, superiority beyond the measured pools, or "nominal coverage achieved". `candidate_diagnostics_trust` is "unverified". The bootstrap lower bound is not in the artifacts. No ablation artifacts exist.

## Why this framing
- A headline "beats PPI++" would overstate a ~2% gain with below-nominal point coverage.
- The label-free spline-basis route scored lowest in search (0.0046), and stacked calibration (0.0223) did not beat the simpler winner (0.0271). Neither is a paper contribution; both are a design-space contrast.
- The efficiency-bound reading (gain = Var(Y - lambda*Yhat) → residual variance of the best g, bounded by Var(Y - E[Y|Yhat])) explains both when gains are possible and when they are not.
- Search and final are kept separate. All 3 search attempts were scored (no unscored ones), each evaluated once on search pools disjoint from the final pools. The frozen winner was evaluated once on sealed pools.
- Rejected framings: method-wins headline; stacked or label-free variant as the contribution.

## Method groups
1. Baselines: classical, PPI (lambda=1), PPI++ (primary comparator and fallback).
2. Proposed: cross-fitted recalibrated PPI (isotonic and binned g; [Yhat, g] control variates; Student-t; adopt only if half-width ≥1% below PPI++).
3. Supporting: stratified PPI (implemented, no reported metrics; do not give numbers).
4. Design-contrast variants (single evaluation, search pools): label-free basis with PRESS, and NNLS-stacked calibration.

## Results focus
1. Sealed final per-family width reductions vs PPI++ and aggregate vs three comparators (derived percentages labeled as derived).
2. Validity: pooled 0.934, min family 0.91, controls, failed episodes. State the gate is non-rejection.
3. Where gain exists and where it does not. Mechanisms stay hypotheses without ablations.
4. Spread across the five evaluator partitions (scores 0.0203–0.0247). These are not independent confidence intervals.
5. Search-stage design contrast with per-family log ratios; single evaluations, no uncertainty.
6. Analytic headroom section with assumptions and no-gain conditions. No numeric theory-vs-observed check is available, so state that it was not performed.

## Figures (ICLR single-column, text width ≈5.5 in; all full-width; PDF + 300-DPI PNG from source)
- **Fig. 1** `overview_setting_and_method`: diagram, generate-concept-figure, early (page 1–2). Shows fixed inputs → classical / PPI++ / recalibrated PPI with fallback → coverage and width ratio evaluation, with a headroom annotation.
- **Fig. 2** `final_width_ratio`: matplotlib, 2 panels (per-family bars; aggregate vs 3 comparators). Coverage goes in Table 1.
- **Fig. 3** `search_variant_contrast`: matplotlib, 1 panel, 5 families × 3 variants, labeled single evaluation.
- **Tables:** Table 1 final summary; Table 2 estimator comparison and assumptions.
- No trajectory or progression views.

## Body-page use (8–9 pages)
Problem and fixed-input setting; related work (PPI, PPI++, cross-PPI, stratified PPI, plus a few genuinely related bib entries); nested estimator and analytic headroom; evaluation protocol; final results with Table 1 and Fig. 2; search-stage design contrast; no-gain regimes and limitations. The limitations cover below-nominal coverage point estimates, mean estimand only, n=500 on real pools, no ablations, no n sweep, single sealed run, unverified diagnostics, and the in-population truth definition.

## Supplementary plan
Estimator hyperparameters from the frozen source; evaluation protocol and gates; full final tables; search-variant details; variance derivation; reproducibility and LLM Usage (venue-required).

## Avoid
Headings: Search Campaign, Iteration History, Progression, Milestones, Cycle N, Experiment A/B. Phrases: pipeline-native metric names, "state of the art", "achieves nominal coverage", "significantly outperforms".

## Writer notes
- Cite only keys in `references.bib`. DML, isotonic and control-variate sources are absent, so no citation unless retrieved later.
- Anonymize the submission.
- Use the reader-facing names "recalibrated PPI" and "evaluation partitions".
