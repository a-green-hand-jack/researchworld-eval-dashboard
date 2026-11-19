# Caption stubs (paste verbatim; numbers here come from the sidecar `.json` of each figure / `results/core_*.csv`)

Common to F1/F2/F3 (state once, or in each caption): *A target is a model other than the current leader under the mean rule (OLLB: 4,495 models;
HELM: 78 models). Investment = the minimum raise of the target's own scores, task by task, within the per-task cap, that makes it strictly first
(margin 0.001 points) with all other models fixed; K = number of tasks raised, L1 = total points raised, n = number of tasks. "Feasible" =
some raise within the cap makes the target first; targets already first under the rule cost 0 and count as feasible.*

**F1 `F_ollb_primary` (Open LLM Leaderboard, n = 6; cap `emp99`, per-task 99th percentile of fine-tune-minus-base gains).** Left: fraction of targets for which
first place is reachable (Wilson 95% CI), by the target's rank under the mean rule (log scale; bins double from rank 2; point at the geometric mean rank of the
targets in the bin; bins with fewer than 3 targets omitted). Middle/right: median K/n and L1/n *among feasible targets only* with 95% bootstrap CIs over targets
(B = 1000); the curves stop where fewer than 3 targets in a bin are feasible. Borda and Condorcet winner were solved exactly for the 50 best targets under the mean
only (ranks 2-50), so their curves end there and their feasibility fractions are not comparable with the score rules' overall fractions.

**F2 `F_helm_primary` (HELM MMLU, n = 57; cap `emp99T`).** As F1. The cap is the OLLB MMLU-PRO 99th-percentile gain applied to every one of the 57 subjects:
a transfer assumption, not a measured HELM quantity. 78 targets, so most bins hold fewer than 10 targets and the CIs are wide.

**F1b/F2b `F_ollb_oracle`, `F_helm_oracle` (appendix).** As F1/F2 with the oracle cap (scores may rise to 100). Every target is feasible, so these panels show what the rule
alone does; the values are lower bounds on the investment under any realistic cap.

**F3 `F_ollb_capgrid`, `F_helm_capgrid` (appendix).** Feasibility (left) and median L1/n among feasible targets (right) for three rank strata (OLLB 2-5, 6-20, 21-100; HELM 2-5, 6-20, 21-78; the number of
targets is in the axis label) under the cap scenarios, ordered by their size in points: +h = the target may gain at most h points on every task; emp95/emp99 = empirical 95th/99th percentile of fine-tune-minus-base gains
(OLLB: one value per task, from 3.2/7.1 points on MMLU-PRO to 46/63 on IFEval, placed at their average 14.8/21.4 and joined to nothing because their shape differs from the uniform caps; HELM: the MMLU-PRO value 3.2/7.1 used on every subject, `emp95T`/`emp99T`,
a transfer assumption); pooled = percentile of all six tasks' gains pooled (44.9 points); front = best rival score on each task; 100 = score ceiling. Markers are bin values, bars 95% intervals (Wilson for the fraction, bootstrap over targets for the median;
horizontal offsets only separate the rules). Under the mean rule the cost among feasible targets is the same at every cap (L1 = n times the gap to the best rival, Proposition 1), so that line is flat; the cap changes only *whether*
the target can get there. Borda and Condorcet on OLLB (top 50 only) were solved at `emp99` and the oracle cap and appear as isolated markers.

**F4 `F_helm_scaling`.** K/n and L1/n against the number n of randomly drawn HELM subjects (60 random subsets per n, cap `emp99T`); the target is the model ranked 2 (left) or 5
(right) under the subset's own rule. Lines: median over feasible draws; bands: 2.5-97.5 percentile over subset draws (spread across subsets, not a CI of the median).
The share of infeasible draws per rule is in `F_helm_scaling.json` (`max_infeasible_share_by_rule`).

**F5 `F_robust` (evaluation noise) and F5b `F_robust_boot` (bootstrap over tasks).** Stability of the minimum L1 for seven (OLLB) / six (HELM) targets chosen by rank under the mean (2, 3, 5, 10, 20, 50, 100; HELM 2, 3, 5, 10, 20, 40), cap `emp99` (OLLB) / `emp99T` (HELM).
Noise: Gaussian draws with the binomial standard error of each score from the item counts (300 draws OLLB score rules, 60 OLLB Borda/Condorcet, 200 HELM). Bootstrap: tasks resampled with replacement, per-task caps following their task (same numbers of draws).
Dot = median over feasible draws, bar = 2.5-97.5 percentile of the draws (not a CI of the median), open diamond = value on the observed data (absent where the target is infeasible on the observed data); bottom strip = percentage of draws in which first place is unreachable within the cap.
The HELM panel has its own, larger scale. Reading (counts from the sidecar `cells`, targets feasible on the observed data and with at least one feasible draw): the observed L1 lies inside the 2.5-97.5 interval in every such case (noise: 51 of 51; bootstrap: 51 of 51), and below the draw median in 44 and 41 of them, i.e. a small
downward offset; at ranks 2-3 the lower end of the interval is 0 because some draws already make the target first. Feasibility close to the frontier is not stable under noise (HELM, rank-20 target): infeasible on the observed data but feasible in 4.5% (mean) and 11.5% (median) of the draws, while under the minimum and the Condorcet requirement, feasible on the observed data, it is infeasible in 70.5% and 19.5% of the draws.
