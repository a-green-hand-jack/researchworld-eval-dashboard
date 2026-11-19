# Review of paper-repo#13 (main -> final), head 84e28c22c7df18c71e0862af15a7eb7466427b0c

Inspected: main.pdf (24 pp, main text 9 pp), all 9 figure PDFs (rendered), appendix tables, README/code README, results/*.csv.

Checks done
- tools/check_venue.py: RESULT OK (anonymous NeurIPS 2026 mode, checklist filled).
- Text numbers vs results/aggregate.csv, cells.csv, coverage.csv, ess_gain.csv, best_baseline.csv: Table 1 ratios (0.79 / 1.41 / 3.89), n=100 (0.78 / 1.65 / 5.63), coverage by n, ESS gain 1.62 (min 1.17) and source-CV choice counts all match.
- `bash paper/figures/make_all.sh` on a copy: all .tex tables regenerate byte-identical; figure PDFs regenerate (only binary metadata differs).
- Smoke reproduction: fetched ifeval.jbl at pinned commit, ran code/src/run.py (extrap, 20 reps, n=50): per-draw RMSE random 0.0587 / mass 0.0583 / ridge 0.122 vs cells.csv 0.0571 / 0.0579 / 0.1207 (same pipeline, difference is how reps/models are averaged; same ordering and magnitude).
- Claims are scoped to the evidence (effective under conditions; no ranking gain; not separable from source-CV baseline; under-coverage at small n); development-pilot, not-run methods, forbidden-content contact disclosed; citations are real and in the starter list or standard references.

Open findings (requested changes)
1. Figure 3 (paper/figures/extrap_scatter.pdf, fig_extrap.py): the "RMSE" annotated per panel is the RMSE of seed-averaged predictions (predictions averaged over 20 selection seeds), so it is ~sqrt(20) smaller than the per-draw RMSE of the tables (e.g. random mean on MMLU-Pro 0.011 in the figure vs 6.4 points in Table 6; ridge 0.100 vs 10.3). The caption says "average over 20 seeds" but the annotation reads as the method's error and contradicts Tables 1/6. Annotate it as RMSE of the seed-averaged prediction (or report the per-draw RMSE), and say in the text that the panels show the systematic (bias) part, not the error of one run.
2. Section 4.2 (H-main paragraph): "picks ridge on GPQA and MuSR although ridge degrades under extrapolation" is contradicted by the appendix tables: on GPQA and MuSR ridge is below the random mean under extrapolation (Table 6, n=50: 6.0 vs 6.9 and 4.8 vs 5.8). Qualify it (ridge degrades on high-spread benchmarks, not on these two low-spread ones) or drop the clause.
3. Figure 1 / Section 4.2: at n=10-20 under extrapolation the best-source-CV baseline curve is visibly below MASS-Ens (aggregate.csv, ref best_cv: 1.08 [0.96,1.20] at n=10; interpolation 1.18 [0.99,1.47]); the text discusses only n=50,100. State that at small budgets the point estimate favours the baseline.
4. Appendix source (appendix.tex line 51): stray sentence "Headline tables at n=100:" before the tables; and appendix section D heading is followed directly by E in the PDF because floats are deferred. Remove the sentence / place float barriers.
5. Reproduction (minor): results/raw/ is not in the delivery (it is in the experiment-repo release `raw-predictions`); the README should say in the step list where to download it for merge_tables.py, or state that the CSVs are rebuilt only by re-running the sweeps (15+ h).

# Re-review at head 31e2173c50a666ffb3f84610ec6bb339ad59da3d (PR #13 head; includes #16, #17)

Findings 1-5 resolved: Fig. 3 now prints bias of the seed-averaged prediction and per-run RMSE from cells.csv (rendered, e.g. random mean on MMLU-Pro 0.064, matches Table 6), caption/text say the points show the systematic part; ridge-on-GPQA/MuSR clause now states ridge is below the random mean there; small-budget paragraph added (1.08 [0.96,1.21] at n=10 etc., matches aggregate/paired best_cv); stray sentence removed and FloatBarriers added; README says where raw/ comes from.
Re-checks: check_venue OK (main text 9 pp, 25 pp total); make_all.sh regenerates all .tex tables identically; new aggregate.csv/ranking_by_subset.csv headline values unchanged (mass_ens 0.7896, ridge 1.408 at n=50 extrap).
Non-blocking nit: Table 1 uses its own benchmark bootstrap (ridge [1.18,1.68]); aggregate.csv, drawn with another seed, gives [1.17,1.67]. Last-digit difference only.
Conclusion: supported; approved.
