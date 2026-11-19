# Analysis protocol, fixed before outcome experiments

Written 2026-11-02. This is a local design record, not an external preregistration.

## Questions
1. Can a small subset predict *individual unmeasured scores*, rather than just a leaderboard average?
2. How much does selecting that subset help when the predictor is held constant?
3. Do benefits survive publisher-disjoint evaluation, incomplete history, and fixed target tasks?
4. Is there a universal sufficient k? We expect dependence on tolerance, task residuals, and distribution shift.

## Data and preprocessing
Use only the pinned MTEB commit and pinned Open LLM Leaderboard parquet in the task. Do not merge incompatible model identifiers. For MTEB use the original English 56-task suite, retaining CQADupstack as one aggregate; English main_score only, official test split except MSMARCO dev. Prefer explicit aggregate over average of all 12 CQADupstack subtasks. Per model choose the revision with most available suite tasks, lexicographic tie break. At least 10 observed suite tasks for historical models. Fully observed models are eligible test/validation cases; partial models remain useful history. No outcome-based task filtering. Deduplicate identical complete/partial score profiles (including missingness), keeping lexicographically first name. OLL: unflagged, one row per fullname, prefer bfloat16, then float16, then other precision; use six Raw scores on [0,1]. Deduplicate exact profiles. Check all units and ranges.

## Models and selection
Training-only means and standard deviations. Pairwise covariance on standardized observed entries; project to PSD and correlation-normalize; shrink towards identity. Tune alpha in {0.02,0.1,0.3,0.6,0.9} on inner validation random-prefix prediction loss. Gaussian conditional mean uses the same fitted covariance for all selection comparisons. Primary selector greedily minimizes trace of conditional covariance on the complement after each query. Fixed-target audit minimizes covariance trace on disjoint targets. Baselines: training mean; random subsets (10 orders); marginal squared-correlation centrality; D-optimal maximum conditional variance; inner-validation greedy; low-rank EM-PCA ridge reconstruction with random and D-optimal queries. Also alpha=0.02 ablation for covariance-greedy.

## Evaluation
Outer 5-fold model splits, seeds 17,29,43, repeated for random-row and publisher-disjoint splits. Publisher is a provenance proxy, not a verified model family. Inner validation: 20% outer training rows/groups, with complete cases used for validation loss; all other eligible history used in fitting. Refit on all outer training data after tuning, including inner validation. No test score is used for fitting, standardization, selection or hyperparameters. MTEB k in {0,1,2,4,8,12,16,24,32}; OLL k in {0,1,2,3,4,5}. Test loss excludes selected queries. Primary metric root of mean model-level standardized MSE, plus raw score-point RMSE (100 times raw [0,1] scores) and MAE. Average repeated predictions/losses per model before inference. Publisher cluster bootstrap, 2000 draws, seed 20261102; paired CIs for comparisons. These intervals condition on fitted cross-validation runs and do not capture all refitting uncertainty.

## Audits
Fixed disjoint target sets: one third of tasks, seed per repetition, identical for all methods. Report target-only error. Historical independent missingness stress: retain {100%,75%,50%,25%} of *originally observed* training cells, maintain complete test cases; seeds 17,29,43, random-row splits. OLL temporal split sorted by Submission Date: first 60% train, next 20% validation, last 20% test, tie dates kept together. Gaussian synthetic simulation checks analytic risk and a residual error floor. Report no universal sufficient k; show tolerance crossings only on tested budget grid, and percentile model errors.

## Integrity
All paper numbers and graphics are generated from saved outputs. Log failed or changed analyses. No topical literature searches: read only starter references and necessary official template/method/data documentation. Do not search for or infer the prohibited work.
