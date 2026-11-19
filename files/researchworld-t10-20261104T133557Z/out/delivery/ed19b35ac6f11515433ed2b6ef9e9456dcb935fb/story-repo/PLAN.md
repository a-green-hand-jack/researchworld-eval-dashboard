# Study plan (story-repo)

Objective: `Research objective` issue (#1). This plan fixes the question, the claims the paper may make, the analyses that decide each, and who delivers which path. It does not fix conclusions; every claim below is conditional on what `experiment-repo` measures.

## Question
With labeled set (n pairs), unlabeled set (N) and predictor f fixed, and nominal coverage required: **can a confidence interval for a population parameter be shorter than power-tuned PPI++ (Angelopoulos–Duchi–Zrnic 2023), at valid coverage, and under which conditions?**

Primary estimand: the population mean E[Y] (the setting where every compared method is defined and the pools give a known truth). Secondary estimand: OLS coefficient of Y on X (`census_*` data), to show the finding is not specific to the mean. Rationale: a mean has a clean control-variate view, so a theory statement can be checked exactly.

## Framing (the route we test, not a presumed result)
PPI++ = classical-labeled estimator minus lambda·(labeled mean of f − unlabeled mean of f), i.e. a control variate affine in f. Route: **richer control variates built post hoc from the fixed (f, X)** — nonlinear/isotonic/GBM adjusters g(f, X) fitted on the labeled set with cross-fitting (the unlabeled mean of g is free) — plus **finite-sample-corrected intervals** (studentised bootstrap) so that narrowness is not bought by undercoverage.
Theory to state with assumptions and check numerically: asymptotic variance with control variate g is Var(Y − g)/n + Var(g)/N (λ-tuned form); the best g within a class is the L2 projection of Y on the class; so the width ratio vs PPI++ is sqrt(resid. variance of class / resid. variance of best affine-in-f), bounded below by the oracle E[Y | f, X]. Hence gain exists iff E[Y|f,X] is far from affine in f (non-monotone/miscalibrated f, or X carries signal beyond f), and is eaten by estimation cost of g when n is small. Also: nothing built from (f, X, labeled/unlabeled data) can beat the oracle bound; wider-than-PPI++ is expected at small n for flexible g.

## Claims and the evidence each needs
| id | claim (to be confirmed, refuted or conditioned) | analysis | owner |
|---|---|---|---|
| C0 | Validity baseline: coverage of Wald PPI/PPI++/classical vs n, rho=n/N, outcome skewness/rarity | Monte-Carlo coverage grid on real pools (truth = pool mean) and synthetic; Monte-Carlo CI for coverage | experiment |
| C1 | Population headroom: asymptotic width ratio of best (f,X)-control variate to PPI++ on each real dataset | `headroom_population.csv` (done in pilot; finalise with uncertainty over fold splits) | experiment |
| C2 | Finite-sample: width ratio and coverage of refined intervals vs PPI++ at n in {50,100,200,500,1000}, one rho sweep; where does the break-even n lie | real-pool resampling grid, **R ≥ 2000 reps for every coverage cell**, paired comparisons (same draws) | experiment |
| C3 | Conditions: synthetic scenarios with known truth and oracle (calibrated, miscalibrated-monotone, non-monotone, X-signal, uninformative f, heavy tails) show when gain exists, matching the theory | synthetic grid; theory-vs-measured width plot | experiment |
| C4 | Same conclusion for OLS coefficients | OLS grid, vector control variates, check vs ppi_py PPI++ | experiment |
| C5 | Negative/boundary results: gain ≈ 0 for real data where PPI++ already near the bound; narrower-but-invalid cases flagged | from C1–C3, no extra runs | experiment |
| C6 | Ablation: what carries a gain (adjuster class, cross-fitting, bootstrap vs Wald, using X) | extra columns in grids | experiment |

Rules for the paper: report width only together with coverage; all comparisons paired; uncertainty = Monte-Carlo SE/CI of mean width ratio and of coverage; data sets with no pool truth (`ballots`) and with distribution shift (`plankton`) are width/diagnostic-only, stated as such; no number enters the paper unless produced by a delivered script.

## Division of work and delivered paths (see `.forgejo/CODEOWNERS` proposal)
- `experiment-repo`: `code/` (methods, grids, drivers), `results/` (final CSVs with seeds, versions, input provenance), `REPRODUCE.md` (environment, data steps, seeds, commands, runtimes, table/figure → script map, incl. the log of any forbidden-content encounter — none by this plan).
- `figtab-repo`: `figures/`, `tables/` (rendered from `results/`; each must carry its claim id above).
- `venue-repo`: `venue/` (chosen conference — one of ICML/ICLR/NeurIPS — latest official template, page limit, checklist form requirements).
- `paper-repo`: `paper/` and the built `paper.pdf`.
- `story-repo`: this plan and CODEOWNERS.

## Constraints to honour
CPU only; ≤ 1 week; do not search for/read the paper that studied this exact question or anything discussing it (objective, `deliverable.md`); starter literature and unrelated work are fine.

## Decisions (answering idea-repo, story-repo#5)
1. **Recalibration is inside the setting.** A post-hoc adjuster g(Yhat) or g(X, Yhat) fitted on the labeled set only (cross-fitted, so its unlabeled mean is free) adds no labels, no unlabeled units and leaves the predictor f untouched. The paper must say this explicitly as an interpretation of "predictor fixed", and report what changes if one insists on affine-in-f only (that is PPI++, the baseline).
2. **Estimands.** Primary: mean of Y on every dataset. Secondary: OLS coefficient on `census_*` (done in the pilot). Quantiles are optional and only if time remains; not required for any claim.
3. **Data protocol.** For the seven pools with paired (Y, Yhat): each repetition draws the n labeled units and the N unlabeled units **i.i.d. with replacement from the pool** (the pool's empirical distribution is the population, so the truth = pool mean is exact and the iid target is met), N = min(pool size, 10 000) by default (so rho = n/N), Y hidden for the unlabeled; the same draw is shared by all methods. The paper's protocol sentence must say this (not 'without replacement'); the N cap and the rho sweep are stated with it. `plankton`: (a) within-2013 pool as a no-shift validity case with truth = 2013 mean; (b) 2013 labeled + 2014 unlabeled with truth = 2014 mean, labelled a shift stress test (H5). `ballots`: subsample inside the 1027 labeled (truth = their mean, N the rest) as a width/validity check; the 78,150 unlabeled Yhat have no Y and are used for width demonstration only, never for coverage. Binary-Yhat sets (`plankton`, `ballots`) are expected to show no asymptotic gain (E[Y|Yhat] is a two-point function, hence affine); that is a prediction to check.

## Hypotheses to be tested (from idea-repo Brief §4, kept as questions)
H1 no gain when PPI++ is near the bound; H2 cross-fitted recalibration shortens when E[Y|Yhat] is non-affine, with coverage kept; H3 more with informative X; H4 small n removes the gain or breaks coverage; H5 shift breaks all methods. Positioning note: the efficiency bound itself is already in the PPI++ paper; the paper's contribution is the realisable gain and its finite-sample cost, the conditions where it is zero, and the coverage check.

## Decision: ratio baseline (figtab-repo#3)
Headline narrowing statements compare each refined interval with PPI++ **calibrated the same way** (Wald vs Wald, t vs t, bootstrap vs bootstrap), paired on the same draws, so that a gain from the calibration of the interval is not credited to the control variate. The practitioner baseline (PPI++ Wald, the published default) is reported alongside, flagged where it undercovers; a width comparison against an undercovering interval is never read as a saving. Also report the best valid PPI++ variant at each cell. Main figure: like-for-like ratio; the Wald-baseline ratio goes to the appendix or a second panel.

## Sizing and bounds (answering idea-review-repo, story-repo#6) — supersedes the grids in the claims table where they differ
The measured real-data headroom for the mean is ≤ ~1.2 % in width, so the plan does not presume a real-data gain: the study is conditional ("when does headroom exist and is it realisable at finite n"), and a null on the real-data mean is an accepted, expected result (C5).
1. **Conditional core = synthetic family with a headroom knob.** One family with known truth in which a single parameter dials E[Y|f,X]'s departure from affine in f (and, separately, X signal / heteroscedasticity). For each knob value: closed-form asymptotic width ratio vs PPI++ (assumptions stated: iid, labeled MCAR, large n and N, fixed f, g in a class with L2 projection), and a numerical check that measured ratios follow it, at several n.
2. **Bounds.** Primary estimand mean; one secondary (OLS coefficient on `census_income`, chosen because X may carry headroom there). Baselines: classical, PPI, PPI++ (calibrated the same way as the refined interval); stratified PPI optional if time. Cross-PPI and active inference are out of the comparison (they retrain the predictor / choose which labels to buy, i.e. change the fixed inputs) and appear in related work only. Real datasets in the main text (≤5), with roles: `census_income` (X present, skewed; headroom-present), `gene_expression` (continuous, high correlation; ~1 % headroom), `galaxies` (calibration near-affine; absent), `forest` (small pool; small-n), `plankton` (binary Yhat: zero headroom; within-2013 plus 2013→2014 shift stress test). `alphafold`, `census_healthcare`, `census_education`, `ballots` go to the appendix (population headroom and a reduced grid). n ∈ {50, 100, 200, 500, 1000}; one N (rho) sweep, on `census_income`.
3. **Pre-decided reporting.** R ≥ 2000 replications for any coverage claim (MC s.e. ≈ 0.5 pp); coverage with Wilson/binomial interval; paired width ratios with CI; a width "gain" counts only when the interval's coverage is not below nominal by more than its MC interval; undercovering cells are reported, not dropped.
4. **Protocol caveats stated.** Finite-population truth = pool mean (pool-split protocol above); `ballots` unlabeled set has no Y (width only); `plankton` 2013→2014 shift violates exchangeability.

## Decisions on consistency (story-repo#7)
- Coverage cells: R ≥ 2000 (the claims table now says so); n ∈ {50,100,200,500,1000}. Protocol = i.i.d. with replacement from the pool, N = min(pool, 10 000) (as above); the earlier 'without replacement, N = pool − n' wording is withdrawn.
- **Main text vs appendix.** Main text: C2 (width ratio + coverage vs n for the five roled datasets, like-for-like baseline, one figure), C3 (synthetic knob: measured vs predicted ratio, one figure + the theory statement), C5 (null/boundary summary: population headroom table across all pools), C0 (validity baseline folded into the C2 coverage panels), C4 (one table, OLS on census_income), C6 (one small ablation table). Appendix: remaining real pools, `ballots` width demonstration, rho sweep details beyond census_income, extra learners and heavy-tail scenarios, all full-grid tables. Figtab/paper effort goes first to C2, C3, C5.
