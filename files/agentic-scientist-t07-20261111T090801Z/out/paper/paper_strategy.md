# Paper Strategy (paper_standalone, ICLR 2026, double-blind)

**Status: ready.** Not in edit mode (no previous paper, no edit-context files): prior-story status = rejected/not applicable; framing chosen fresh.

## Title (provisional)
Source-Validated Latent-Ability Stacking for Few-Item Benchmark Score Prediction: Small Gains Over Random Subsets and a Persistent Extrapolation Gap

## Central question
With only source models' binary per-item results and k=100 items revealed for a new model, does Fisher D-optimal item selection on a source-fitted logistic latent model plus a source-validated stacked estimator predict full-benchmark accuracy and ranking better than a random subset mean, k-means anchor points and an IRT-style estimator, especially for targets stronger than every source model?

## Central thesis
On five held-out benchmarks (3 seeds), the selected estimator has lower point-estimate MAE than all three trusted baselines (0.0294 vs 0.0339 for the best baseline, a random subset mean) and passed every validity check and negative control. But the paired bootstrap interval for its gain over the best baseline includes zero (MAE delta CI [-0.0052, 0.0134]; utility delta CI [-0.0143, 0.0354]). Error and rank correlation are about twice as bad for targets stronger than all sources (MAE 0.0409, Spearman 0.730) as for random targets (MAE 0.0179, Spearman 0.956). The supported claim is a modest, statistically unresolved improvement plus a measured extrapolation limitation. It is not a decisive win.

## Why this framing
- `final.qualification.outcome = qualified`, status completed. In this task "qualified" means protocol validity (all 32 episodes, both controls, required baselines completed). It is not superiority. The paper must say so and must not turn it into a generalization or superiority claim. Evidence files mark `candidate_diagnostics_trust` as unverified; disclose that. No gate diagnostics exist, so no causal attribution of any criterion.
- No `downstream_study` / `study.*` sources exist. Search facts come from `result.*`: 3 of 3 variants scored, 0 unscored. Final facts come from `final.*` and stay separate from search.
- Rejected framings: (a) "new method beats SOTA" (CI crosses zero, no SOTA comparison); (b) chronology of three variants (run diary); (c) an ablation-centred paper (no single-factor ablations exist, `ablation_studies` is empty).

## Method groups
1. **Proposed**: selected stacked estimator (search variant c02): logistic latent model, greedy Fisher D-optimal design at upper-tail reference abilities, MAP target ability, NNLS stacking over source pseudo-target folds (strongest-holdout for the strong regime), fallback to simpler estimators.
2. **Supporting**: linear model-assisted D-optimal estimator (c01), the stack's fallback member; cumulative-change reference only.
3. **Negative extension**: bagged posterior-mean + tail calibration (c03): no gain (0.9445 vs 0.9452).
4. **Baselines**: random subset mean (best baseline by utility), anchor points (k-means), IRT-style. MAE deltas (positive favours candidate): +0.0045, +0.0134, +0.0398. A CI exists only for the best-baseline/random-mean comparison.
5. **Controls**: permuted and constant targets (Spearman drop 1.157, MAE increase 0.156, constant-target MAE delta 0.094).

## Results focus
1. Final held-out comparison with uncertainty (Fig. 2, Table 1).
2. Extrapolation gap, random vs strong targets, on development and held-out benchmark groups (Fig. 3). Per-regime baseline numbers are not in the artifacts, so no claim about where the gain concentrates.
3. Within-family variants on search (Table 2): utility 0.9381 / 0.9452 / 0.9445. The top-two gap (0.0006) is below within-variant seed spread (about 0.006), so selecting c02 is a frozen choice, not a demonstrated best.
4. Search→final shift (0.9452 → 0.9314): different benchmarks and seeds; report without a cause.
5. Scope: k=100 only, binary accuracy, 5+5 benchmarks. The k sweep, latent-rank/shrinkage ablations and temporal split in the idea files were not run; list as untested.

## Figures (ICLR single-column, text width ≈5.5 in; all at full width, PDF + 300-DPI PNG)
- **Fig. 1 overview** (`generate-concept-figure`, page 1–2, 1 panel): protocol and pipeline plus the two target regimes.
- **Fig. 2 main comparison** (matplotlib, 2 panels, ≤4 bars each): panel A overall MAE of candidate vs 3 baselines (baseline MAEs derived as candidate MAE + delta: 0.0339 / 0.0428 / 0.0692, labelled derived); panel B paired delta vs best baseline (MAE, utility) with 95% bootstrap intervals crossing zero.
- **Fig. 3 extrapolation gap** (matplotlib, 2 panels MAE/Spearman; 2 groups × 2 regimes, development vs held-out labelled separately).
- Tables: final metrics + per-seed utilities (0.9257, 0.9324, 0.9360) + controls; search variants with per-seed utilities.

## Page budget (8–9 pages body, last page ≥75% full)
Intro ≈1.0 (with Fig. 1), related work ≈0.7, setting+method ≈1.8, protocol ≈0.8, results ≈2.6, discussion/limitations ≈1.0. Extra space goes to mechanism motivation (explicitly not a proven mechanism, since there is no ablation), failure modes and limitations, not padding.

## Supplement
Protocol and metric definitions (incl. benchmark names and bootstrap); estimator/stacking details; full search-variant table; final details and controls; reproducibility, data provenance, seeds and the required LLM Usage section. The CI and the extrapolation gap stay in the main text.

## Avoid
Headings: search trajectory, progression, milestones, first valid result, campaign phases, Experiment A/B, attempt history. Phrases: correctness rate, eligible, combined_score, rubric, "state of the art", "significantly outperforms". Use "utility score", "model variants", "seeded runs", "configurations".

## Writer cautions
- `references.bib` is mostly unrelated; only Vivek2023AnchorPB is clearly relevant. Add the other starter-list works from the task brief's details; cite nothing unverifiable; do not touch the withheld paper beyond the permitted starter-list citation.
- Anonymize fully; no repository links.
