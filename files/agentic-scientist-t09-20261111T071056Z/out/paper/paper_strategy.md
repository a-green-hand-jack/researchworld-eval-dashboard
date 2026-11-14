# Paper Strategy (paper_standalone, ICLR 2026)

**Status:** ready. **Provisional title:** How Accurate Is Regression-Based GATE Estimation Under Network Interference? Exposure-Mapping Fidelity Governs Error in an Eight-Case Grid.

## Central question
In a single randomized experiment on a network, how accurately can a regression-based GATE estimator recover the truth, and which features of the interference mechanism, graph and assignment design decide when it works and when it fails?

## Central thesis
On the eight-case synthetic grid (n=3000; SBM / Barabasi-Albert / Watts-Strogatz; additive, strong, saturating, degree-dependent and two-hop interference; Bernoulli and cluster assignment), regression-GATE error is small (about 3-5% relative RMSE per case) when the fitted exposure mapping matches the mechanism, and large when it does not (saturating 0.198, count x degree 0.151, two-hop 0.452). Graph family, interference strength and cluster vs Bernoulli assignment did not degrade accuracy within the tested range. Nominal 95% intervals undercover (0.839). The frozen BIC-gated parametric exposure regression lowers mean relative RMSE to 0.126 vs 0.180 for plain linear exposure regression, but leaves the two-hop case unresolved.

## Why this framing
- Final evaluation: completed, outcome `qualified`, 24 unseen seeds x 8 cases, 0 missing/failed episodes. No `downstream_study` block, so no downstream claims. Qualification supports reporting the measured results only, not generality or superiority.
- Rejected: "new estimator wins" (only 3 scored variants, same case specs in search and final, no gate ablation, no per-case baselines); search-chronology (diary). Chosen: thesis-first characterization with the frozen estimator as the studied method. Not edit mode, so prior-paper status is "rejected" (nothing to preserve).

## Method groups
1. Frozen BIC-gated parametric exposure-regression estimator (proposed/studied).
2. Plain linear exposure regression (baseline, 0.180).
3. Difference-in-means (0.622) and neighbourhood Horvitz-Thompson (0.994) (baselines).
4. Correctly specified oracle regression (supporting reference, 0.045).
5. Search-plane estimator-class alternatives: flexible ridge ensemble (0.232), linear + residual correction (0.185), vs BIC-gated library (0.140) and linear (0.184) on that plane. Ablation-style, labelled search plane.
6. Negative controls and replay (supporting): constant 9.0e-15, permuted outcome 0.0588, permuted graph RMSE 0.627, 0 vacuity violations, 0 replay diff.

## Results focus
Aggregate method comparison; per-case profile with single-factor contrasts (explicitly case pairs, no per-case intervals); aggregate bias 0.074 vs RMSE 0.126; interval undercoverage (0.839, width 0.379); seed-level variability from the 24 per-seed scores (two outliers, seeds 9001 and 9015); search-plane estimator-class table, kept separate from final.

## Figures (ICLR is single-column; text width about 5.5 in)
- **Fig. 1 overview_schematic** (generate-concept-figure, full width, page 1-2): pipeline and eight-case factor grid, with the corner-extrapolation vs misspecification error sources.
- **Fig. 2 main_accuracy** (matplotlib, full width, 2 panels): (a) five methods aggregate relative RMSE, log/broken axis; (b) per-case frozen-estimator error across 8 cases (budget relaxed to 8 categories, 1 series, because the grid has exactly eight cases).
- **Fig. 3 reliability** (matplotlib, 0.85 width, 2 panels): per-seed scores with bootstrap interval; coverage vs 0.95 nominal.
- Tables: case-factor table with final per-case error; search-plane estimator-class table.
- PDF + 300 DPI PNG from one source script; LaTeX references the PDF; no shrinking of dense figures.

## Body-page use (8-9 pages, no padding)
Framing + Fig. 1 (~1), related work (~0.75), setup/estimator/metric (~1.5), results (~3-3.5), discussion and limitations (~1).

## Supplement
Case specifications; exact estimator and baseline definitions; per-seed table and bootstrap; negative controls; search-plane comparison; LLM Usage section (required by venue).

## Must-disclose limitations
Search and final share case specifications and the library was designed after seeing search-plane per-case errors (no transfer-to-new-mechanism claim); one n, one p; case-pair contrasts, not factorial; no per-case baselines, bias or intervals; two-hop failure cause unknown (gate diagnostics unverified, so unknown); undercoverage cause not established; no public-graph or real-data experiments, no gate ablation (ablation_studies empty), no learned-graph methods.

## Avoid
Headings: Experiment A/B, search trajectory, iteration history, progression, campaign summary, lessons learned. Phrases: combined_score, correctness rate, eligible, rubric, program_1, "we first tried", state-of-the-art claims. Use "model variant", "configuration", "seeded run".

## Writer notes
Cite only relevant bib entries (Chin, Aronow-Samii, Ugander, Karrer, Han-Ugander, Chen et al., Eichhorn et al., Forastiere et al., etc.) after checking provenance; many bib entries are irrelevant noise. Starter-list papers missing from the bib must not be cited without provenance. Anonymize everything. Full machine-readable plan in `paper_strategy.json`.
