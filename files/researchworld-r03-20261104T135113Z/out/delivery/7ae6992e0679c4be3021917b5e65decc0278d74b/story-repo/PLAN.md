# Study plan (story-repo / plan)

Objective: `Research objective` (story-repo#1). Context: idea-repo wiki `Brief` (H1-H4). Feasibility bounds: story-repo#2. Written 2026-11-04; revised through commits here and the commitment issue.

## 1. Questions and hypotheses (answered by evidence; any outcome is reportable)

Setting: historical model x benchmark matrix (cells missing), a new model observed on k benchmarks (chosen from training matrix only, among benchmarks the model covers), infer its scores on the *other* benchmarks.

- **RQ1 structure (H1).** Is the matrix approximately low-rank (+ noise) on real leaderboards, and does the k-curve flatten near the effective rank?
- **RQ2 selection (H2).** At fixed inference rule, does an informed selector (greedy / D-optimal / leverage / pivoted-QR / coverage) beat random-k, and where (small k vs large k)?
- **RQ3 inference (H3).** Which inference rule (column mean, avg-regression, ridge, kNN over models, factor-analysis conditional Gaussian, kernel ridge) wins, and does selection matter less than inference? Selector x inference crossed table.
- **RQ4 how large k.** Smallest k reaching a tolerance, with CI, per dataset.
- **RQ5 data conditions (H3).** Dependence on missingness/density, number of models M, benchmark heterogeneity, score scale, effective rank, noise; and which conclusions hold only for the dense embedding block.
- **RQ6 shift (H4).** Leave-family-out / time-split (older -> newest models) versus random leave-one-model-out.
- **RQ7 theory.** Rank-r Gaussian factor model: Schur-complement/conditional-covariance error of the posterior-mean predictor as a function of (k, r, noise, subset); greedy log-det selection (submodular, (1-1/e)-type guarantee for the log-det objective only, not for MSE). Checked on labelled synthetic matrices with known truth, then compared to real curves; report where theory fails.

## 2. Data roles
- **Primary:** MTEB @ pinned SHA, dense blocks. Feasibility profile gave 56 tasks x 162 models and 357 x 135; as built by experiment-repo (README, `results/summary/datasets.csv`): dense56 = 152 models x 56 tasks (99.6% observed), dense = 133 x 275 (98.9%). Sensitivity axis: mid (156 x 357, 92%) and sparse (479 x 472, 30%) blocks (density falls). Claims are about embedding benchmarks.
- **Secondary, small-N cross-checks, each its own matrix, no cross-leaderboard merge:** Open LLM Leaderboard (N=6), HELM Lite (N=10, and HELM-MMLU subjects), LiveBench (N=7). k-curves are short; never pooled with MTEB; used to state which conclusions are MTEB-only.
- **Synthetic:** theory and controlled data-condition checks only; always labelled synthetic; never evidence about real leaderboards.

## 3. Protocol (fixed before looking at results)
1. Cold-start row: leave-one-model-out within grouped folds (near-duplicate/same-family models in the same fold). Selector and all hyper-parameters (rank, ridge strength) fit on training models only (inner CV); k benchmarks drawn from the held-out model's covered cells.
2. Protocol B: fixed held-out target benchmarks (never selected), same targets for every k, so curves are comparable across k. Protocol A (targets = all remaining observed cells) as robustness.
3. Scores standardised per benchmark with training statistics; outliers/non-quality tasks (speed tasks, scale outliers) removed by a documented rule.
4. Metrics: nMSE (z-scale, primary), RMSE/MAE in score points, within-model rank correlation over targets, model-ranking agreement on targets. Uncertainty: bootstrap over held-out models; paired bootstrap for selector-vs-random and method-vs-method; repetitions over selection draws; seeds fixed.
5. **"k is enough" (pre-fixed):** primary = gap-closed fraction G(k) = (E_mean - E_k)/(E_mean - E_floor), E_floor = full-information predictor (all non-target benchmarks observed); k*(g) = smallest k whose CI lower bound of G is >= g, for g in {0.8, 0.9}. Secondary = absolute tolerances already in experiment-repo's kstar tables (nMSE <= 0.5/0.25/0.15; RMSE <= 3/2 points). Where seed noise (`scores_per_experiment`) is available, report error against that noise floor and make no claim below it.
6. Baselines/bounds: column mean (k=0), random-k with the same inference, single-factor average regression, oracle best-k (upper bound on selection, flagged as using the held-out row), full-information floor, selection-vs-inference crossing.
7. Ablations: selection vs inference crossing; rank r; regularisation; scale normalisation; leakage check (selection on train only vs peeking); M subsampling; missingness injection; heterogeneity (task-type blocks).
8. Compute: grid as `ht-resource run` jobs; cut folds/reps before baselines if a pilot exceeds ~20 CPU-h; storage < 5 GB (raw MTEB tree deleted after matrix build; raw per-model tables not in git).

## 4. Claim -> evidence -> carrier map
| id | claim / question | source (experiment-repo) | carrier |
|---|---|---|---|
| C0 | data description: sizes, fill, spectrum / effective rank | data/, build_matrices summary | Table 1 + Fig. 2a (scree) |
| C1 | error vs k per selector x inference vs mean/random/floor (RQ2-3) | results/summary/curves_* | **Fig. 1 (main)** |
| C2 | informed vs random, paired difference with CI (RQ2) | paired_* | Fig. 3 |
| C3 | k needed, with CI (RQ4) | kstar_* (+ G(k) summary) | **Table 2** |
| C4 | selector x inference crossing at fixed k (RQ3) | curves_* at k in {2,4,8,16} | Table 3 |
| C5 | data conditions: density/M/rank/noise/heterogeneity, MTEB dense/mid/sparse, OLB/HELM/LiveBench (RQ5) | summaries per dataset/axis | Fig. 4 (+ appendix tables) |
| C6 | shift: family-out / time split (RQ6) | grouped & temporal runs | Fig. 5 / Table 4 |
| C7 | theory vs experiment (RQ7) | results/theory, synthetic truth | Fig. 6; derivation in appendix |
| C8 | leakage and noise-floor checks | leakage ablation, noise floor | appendix table |
Negative cases (selection not better than random, rank not low, failure on small-N / heterogeneous scales) are shown, not omitted.

## 5. Paper outline (venue per venue-repo; main-text page limit decides what moves to appendix)
Abstract; 1 Introduction (problem, RQs, contributions stated modestly); 2 Related work (efficient evaluation item-level: tinyBenchmarks, metabench; low-rank/scaling: observational scaling laws, Sloth; subset selection: CUR / D-optimal / pivoted QR; recommender cold-start; missing-data PCA); 3 Problem and methods (setting, selectors, inference rules, cost and applicability, proposition); 4 Evaluation protocol (why it answers RQ1-7, pre-fixed k criterion); 5 Experiments (5.1 data, 5.2 main curves C1, 5.3 selection vs random C2, 5.4 k needed C3, 5.5 data conditions C5/C6, 5.6 theory C7); 6 Discussion and limitations (embedding models are not generative LLMs, missingness not random, small-N secondaries, MTEB noise); references; appendix (derivations, protocol details, extra tables, leakage/noise, forbidden-content log); checklist.

## 6. Division (see `.forgejo/CODEOWNERS` in paper-repo)
- experiment-repo: `code/` (analysis code), `data/`, `results/` — computes everything in section 4, README of results stating which claim each table supports. Open asks to it: grouped/family and temporal splits (C6), G(k) summary, leakage ablation, noise floor, per-dataset summaries.
- figtab-repo: `figures/`, `tables/`, `code/figtab/` — one script per figure/table, provenance file.
- venue-repo: `venue/`; paper-repo: `paper/`, `README.md` (reproduction notes, script->artifact map, forbidden-content log).
- story-repo: this plan and CODEOWNERS.

## 7. Compliance
No search phrased as "predict performance on other benchmarks from a few benchmarks"; any encounter with the forbidden paper is logged by the finder in README repro notes (paper-repo collects).
