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

**F3 `F_ollb_capgrid`, `F_helm_capgrid` (appendix).** Feasibility (left; vertical bars are Wilson 95% intervals) and median L1/n among feasible targets (right; 95% bootstrap CI over targets, B = 1000) for three rank strata (OLLB: 2-5, 6-20, 21-100; HELM: 2-5, 6-20, 21-78; the number of
targets is in the axis label) under the caps of the x axis, ordered roughly from tight to loose (the order is approximate: +h is a uniform cap, emp95/emp99 are per-task
percentile caps; in HELM, emp95$^T$/emp99$^T$ are the OLLB MMLU-PRO percentiles transferred to all 57 subjects, a transfer assumption). Rules are offset horizontally within a cap. Under the mean rule the cost among feasible targets is the same at every cap (L1 = n times the gap to the best rival, Proposition 1), so that line is
flat; the cap changes only *whether* the target can get there. Cost points appear only where at least 3 targets of the stratum are feasible, so the feasible set (and the targets behind a point) changes along a line; read right panels with the left ones. The 2-5 stratum has 4 targets: its intervals are wide. OLLB Borda and Condorcet (top 50 only) were solved at `emp99` and the oracle cap and are drawn as unconnected markers.

**F4 `F_helm_scaling`.** K/n and L1/n against the number n of randomly drawn HELM subjects (60 random subsets per n, cap `emp99T`); the target is the model ranked 2 (left) or 5
(right) under the subset's own rule. Lines: median over feasible draws; bands: 2.5-97.5 percentile over subset draws (spread across subsets, not a CI of the median).
The share of infeasible draws per rule is in `F_helm_scaling.json` (`max_infeasible_share_by_rule`).

**F5 `F_robust` (appendix).** Stability of the minimum L1 for seven (OLLB) / six (HELM) targets chosen by rank under the mean (x axis), under evaluation noise (top; binomial standard error of each score from the item counts; OLLB closed-form rules 300 draws, OLLB Borda/Condorcet 60 draws, HELM 200 draws) and a bootstrap over tasks (bottom; same caps). Dot = median over feasible draws, bar = 2.5-97.5 percentile of draws (a spread of draws, not a CI of the median), open diamond = value on the observed data;
lower strip = percentage of draws in which first place is unreachable within the cap (primary caps `emp99`, `emp99T`). The observed value lies inside the interval wherever it is feasible and is mostly slightly below the draw median (counts in `experiment-repo#5`: 24/24, 26/26 and 16/16 inside; below the median in 23/24, 18/26 and 14/16); at ranks 2-3 the lower end is 0 because some draws already make the target first. Feasibility at the frontier is noise-sensitive: e.g. a target infeasible on the observed data can be feasible in some draws. OLLB Borda/Condorcet cover the stratum targets within the top 50 under the mean only (ranks 2-50 observed; the rank-100 points are noise/bootstrap draws without an observed-data diamond).
