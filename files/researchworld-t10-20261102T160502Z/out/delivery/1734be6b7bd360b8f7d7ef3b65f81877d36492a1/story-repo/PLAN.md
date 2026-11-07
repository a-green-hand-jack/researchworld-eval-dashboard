# Study plan (story-repo) — fixed-input CI width

Objective: `Research objective` issue (#1). Context: `idea-repo` wiki `Brief`. Feasibility: `idea-review-repo`#2.
Settled by the owner of this plan; the other positions may open an issue here to dispute any item.

## 1. Specific questions
Labeled set (n), unlabeled set (N) and predictor f are fixed. Can a valid 95% interval for the target be shorter than the best available one (PPI++), by how much, and when?
- **Q1 efficiency (asymptotic).** Inside the information set, the efficient variance is E[Var(Y|f)]/n + Var(E[Y|f])/(n+N); PPI++ attains it iff E[Y|f] is affine in f. Predict the gain per dataset from the population (floor) and check it by simulation.
- **Q2 finite-sample calibration.** PPI++ in `ppi-python` plugs in λ̂ with a z-interval; at small n this may under-cover. Does a variance/critical-value correction restore coverage, and at what width cost? (Any "shortening" that costs coverage does not count.)
- **Q3 conservativeness.** Quantify how much wider conservative/non-CLT valid intervals (conformal baseline in `ppi_py.baselines`) are than the CLT ones (context only, not a proposal).
- **Q4 where it cannot help / breaks.** f already affinely sufficient; weak f; N ≪ n; label–unlabeled distribution shift (plankton 2013→2014).
Expected answer is conditional or null; a null result on the real datasets with a quantified synthetic "when" map is a complete answer.

## 2. Fixed design choices
- **Estimand:** population mean E[Y] (prevalence for binary Y), level 95% (alpha=0.05). Quantile / regression coefficients are not studied (stated as extension).
- **Information set:** labeled (Y, f), unlabeled f only. Covariates X (census sets) are **not used** by any method; this is stated in the paper. Learning a map g(f)≈E[Y|f] from the labels is allowed *only* when cross-fitted inside the replicate (the labels are used once for the map and once for the rectifier through K-fold).
- **Methods (frozen before the final runs; ≤5 + ablations):**
  M1 classical (labeled Y only, z); M2 PPI (λ=1); M3 PPI++ (`ppi_py` λ̂, z) = **reference**;
  M4 cross-fitted calibrated-score PPI++ (one calibrator class, chosen on development seeds / synthetic data only, never on the final replicates);
  M5 PPI++ with small-n correction (t critical value and/or variance inflation for λ̂; applied to M3, and to M4 if M4 passes coverage).
  Ablations (secondary, synthetic + two real sets): other calibrators (isotonic/binned/spline), K, conformal baseline for Q3, bootstrap baseline.
- **Sampling model (finite-population caveat stated):** the pool of each dataset is the population; truth = pool mean. Labeled and unlabeled records are iid draws from the pool (with replacement), so n/pool does not matter; n is capped so that n ≤ pool/5 (forest, ballots). Report this convention. Unlabeled N: N=20n (primary), plus N∈{n, 5n, large (≥ 20 000 where the pool allows)} on a subset for the n/N sweep.
- **Datasets:** primary real (mean target, no X): galaxies, forest, alphafold, gene_expression, census_income (Y=income, continuous), ballots (pool = the 1027 labeled records; no unlabeled-Y truth, so the real unlabeled split is demonstration only). Stress test: plankton (real shift, truth = mean of 2014 labels) and a within-2013 no-shift control. census_healthcare / census_education: appendix if time. Optional external data (wine, housing, folktables) are not used.
- **n grid:** {50, 100, 200, 400, 1000} (capped as above). **Replicates:** ≥2000 per cell for the primary grid (1000 only in explicit secondary sweeps, marked as such). Seeds derived from (dataset, n, N, method-independent) so all methods see the same draws.
- **Uncertainty:** coverage with Wilson interval (and MC SE); width mean and median; **paired** width ratio vs M3 on the same draws with a CI (bootstrap over replicates or delta method); also the fraction of replicates in which M4 is narrower. Nominal coverage is "met" if the Wilson CI of coverage contains ≥0.95 or MC-consistent; below-nominal cells are reported, not hidden. No selection of a method by test-replicate outcome.
- **Synthetic grid (carries the "when" answer, known truth):** E[Y|f]: affine → increasingly non-linear (parameter κ); calibrated vs biased f; noise (SNR); binary and heavy-tailed Y; n∈{50,100,400}, N/n∈{1,5,20,large}. For each cell: measured width ratio vs the theoretical ratio from Q1 (population floor), with theory formulas derived and checked in `experiment-repo`.

## 3. Division of work (who delivers what)
| Position | Delivers |
|---|---|
| idea-repo | context/Brief, related-work facts for starter list; no forbidden content |
| experiment-repo | estimators, simulation code, derivation + checks of the Q1 floor, all result CSVs, reproduction notes (`code/`) |
| figtab-repo | every figure and table in the paper, one generating script each, from experiment CSVs (`figures/`); claims in §4 |
| venue-repo | venue/edition/page-limit/template/checklist (`venue/`) — decide early |
| paper-repo | the paper (`paper/`), README, build; claims no stronger than the evidence |
| internal-review / external-review | independent checks |
Delivered paths are in `.forgejo/CODEOWNERS` of `paper-repo` (changed by pull request from here).

## 4. Claims and the evidence each needs (for figtab/paper)
- C1 "PPI++ is already near the efficiency floor on the real datasets" — floor table (theory) + paired width ratio of M4 vs M3 with CI per dataset/n.
- C2 "Gain appears only when E[Y|f] is non-linear / f miscalibrated, and is bounded by the floor" — synthetic κ-sweep, measured vs theoretical ratio.
- C3 "Plug-in PPI++ under-covers at small n for some settings; the correction restores coverage at a quantified width cost" — coverage vs n with Wilson CIs, M3 vs M5.
- C4 "Under distribution shift all PPI-type intervals fail" — plankton shift vs no-shift control.
- C5 "Conservative valid intervals are much wider" — conformal baseline width (ablation).
Figures/tables (planned): F1 floor vs measured ratio; F2 coverage vs n per dataset; F3 paired width ratio vs n; F4 synthetic κ / n/N / noise panels; F5 shift; T1 methods and information set; T2 main real-data table (n=100,400); T3 no-gain / failure regimes.

## 5. Milestones and budget rules
1. Plan + CODEOWNERS (now). 2. Pilot: galaxies + forest, n∈{50,200}, 2000 reps (minutes) — checks harness, coverage, M4/M5 behaviour. 3. Freeze method list → full real grid and synthetic grid (jobs on `local-compute`; no network in jobs, fetch data in the sandbox first). 4. Figures/tables. 5. Paper draft → internal review → `final` (one reviewed delivery; an interim `release` only if time is short). 
Shared model time is 7200 s: no position re-derives work already pushed; if time runs short **cut datasets (alphafold, census_income, then ballots), not replicates**; keep a null/conditional paper complete at every stage.
Forbidden content: do not search "PPI + tighter/optimal interval"; only starter_literature.md and generic statistics (control variates, semiparametric efficiency, AIPW, isotonic regression, t-intervals). Accidental encounters are logged in the reproduction notes.

## 6. Adjustments after feasibility re-judgement (story-repo#5)
- **C1 is the headline real-data result, not a hoped-for gain.** Measured by idea-review (cross-fitted isotonic E[Y|f] vs PPI++ SE ratio, N=20n): galaxies 1.002, forest 1.001, alphafold 1.000, gene_expression 0.993, census_income 0.998, ballots 1.001 (ballots Yhat has 2 values, so no calibrator can help). The study's positive content comes from the synthetic "when" map (C2) and small-n coverage (C3). Paired CIs must resolve 0.2–1% width differences (same draws for all methods).
- **Floor from the pool** must use a cross-fitted or bounded-complexity E[Y|f]; an in-sample nonparametric g gives a spurious floor.
- **Duplicates sensitivity:** one ablation on forest with without-replacement labeled draws; confirm M4/M5 coverage and width are unchanged.
- **Synthetic grid:** one-factor-at-a-time around a base cell (~60–100 cells), full 2000 reps; no full factorial.
- **Multiplicity:** "met" is per cell as before; claim a coverage failure only for a pattern consistent across neighbouring n/datasets or after a Holm/pooled test; say so in the paper.
- **Seeds:** disjoint development and final seed ranges; a committed file records which seeds chose the calibrator and the M5 correction, frozen before the final run.
- **Page budget:** venue limit decides main vs appendix; suggested main text F1, F2+F3 merged, F4, T2; the rest in the appendix.

## 7. Corrections from final results
- **C4 restated.** The final plankton-shift runs do not show all PPI-type intervals failing. Classical (bias), unclipped PPI++ and calibrated variants collapse because λ̂≈1.4>1 under shift; PPI and the clipped package PPI++ (M3) and the jackknife variant stay near 0.95, protected by the λ̂≤1 clip (experiment-repo `results/shift_lambda_check.csv`, `FINDINGS.md`). Captions and text must name which methods fail and why. Original C4 wording in §4 is superseded.
- **C1 qualification:** the only narrower cells (gene_expression n≥400) come from removing the λ̂ clip, not from calibration; the clip is a separate source of shortening that fails under shift.
