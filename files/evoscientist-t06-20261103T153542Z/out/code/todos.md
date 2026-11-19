# Locked analysis plan (before results)

Primary question: does a global deletion fraction hide dependence on the leading pair's exposure and score gap, and how accurately does a frozen influence approximation predict exact targeted-deletion reversals?

## Stage 1 data and checks
Acquire fixed Arena55k, MTBench human/GPT4, NBA snapshots. MTBench retain six common models and all valid outcomes, ties as half win. Arena retain models with >=500 appearances before inducing subset, no label-dependent filtering. NBA use 2015 regular season with one game row (_iscopy=0). No pooled eras. Audit graph connectivity, duplicate IDs, outcome counts, source hashes. No performance-tuned subsets.

## Stage 2 baseline
Ridge BT objective sum of logistic losses + lambda/2 ||theta||², lambda=0.1, zero-centering. Aggregate ordered edge outcomes for fast deterministic Newton fits. Validate gradients, row/aggregate equivalence, permutation invariance, influence signs, tiny exhaustive deletion cases. Main target original leader versus original runner-up (fixed after baseline). Also target every original adjacent top-five pair for a descriptive sensitivity distribution.

## Stage 3 perturbations
Deletion only primary; random deletions (100 seeds), frozen influence-ranked deletions (all records allowed), incident-leader-only influence ablation, direct-pair loss-removal heuristic. Exact refit at each budget. Budget fractions 0, .001, .002, .005, .01, .02, .05 (integer floor; nonzero budgets at least one). Primary outputs fixed-pair margin, reversal indicator, top-1 replacement, normalized Kendall distance, max rank movement. Denominators both all records and union of target incident records; also report each participant's exposure loss. Frozen influence predicts initial derivative, not certified minimum. Obtain first successful feasible budget via sorted-prefix search, explicitly not global optimum. No claims of malicious feasibility.

## Stage 4 uncertainty and controls
200 row bootstrap baseline fits; MTBench additionally cluster bootstrap by question_id; NBA season records conditional (not causal team quality). Matched MTBench human vs GPT4 common question/model-pair/turn cells if available. Ridge lambda .01, .1, 1; random vs targeted; removal vs flip secondary. Downsample Arena to manageable matched sizes with fixed seeds if needed; no causal ranking of designs. Three independent random seeds minimum, report empirical distribution/95% intervals, no uncorrected multiple p-values. Compute finite-prefix influence prediction error versus exact refit. Report all failures.

## Artifacts
src/acquire.py, src/analysis.py, tests/; results/*.csv and json; publication figures and tables generated from results; paper/main.tex + official 2026 NeurIPS template if available (otherwise latest officially released); paper/main.pdf; README.md, requirements.txt, final_report.md.

## Rejection risks
Existing influence/deletion ideas: frame as controlled empirical budget calibration, no algorithmic novelty claim. Cross-design confounding: matched MTBench and descriptive comparisons only. Optimistic attack: all-data oracle upper bound, not feasible threat model. Ridge/disconnected graph: sensitivity and graph audits. Uncertainty: row versus question clusters, conditional analysis, target-selection limits.

## Code policy
No code-agent delegation (higher-level mode question cannot be answered unattended); parent implements and runs code directly. Planner and independent analysis/review consults permitted. Expected fits: few thousand small dense Newton systems, minutes on CPU. Use BLAS thread limits and background main execution.
