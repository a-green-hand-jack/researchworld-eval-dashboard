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

**F3 `F_ollb_capgrid`, `F_helm_capgrid` (appendix).** Feasibility (left) and median L1/n among feasible targets (right) for three rank strata (the number of targets is in the axis label) under the caps of the sweep, ordered from tight to loose by the share of targets feasible under the mean rule (the order is empirical: +h is a uniform cap, emp95/emp99 are per-task percentile caps, `T` = percentile transferred from OLLB MMLU-PRO to HELM). Under the mean rule the cost among feasible targets does not depend on the cap (L1 = n times the gap to the best rival, Proposition 1), so any variation of the mean line comes from *which* targets are feasible, not from the cost of a given target. Borda and Condorcet on OLLB (top 50 only) were solved at `emp99` and the oracle cap and are drawn as unconnected markers. Axis order (identical to the x-axis, from tight to loose): OLLB `+5`, `+10`, `emp95`, `emp99`, `+20`, `front` (best rival score), `100`; HELM `emp95T`, `+5`, `emp99T`, `+10`, `+20`, pooled `emp99`, `front`, `100`. Curves stop where fewer than 3 targets in the stratum are feasible.

**F4 `F_helm_scaling`.** K/n and L1/n against the number n of randomly drawn HELM subjects (60 random subsets per n, cap `emp99T`); the target is the model ranked 2 (left) or 5
(right) under the subset's own rule. Lines: median over feasible draws; bands: 2.5-97.5 percentile over subset draws (spread across subsets, not a CI of the median).
The share of infeasible draws per rule is in `F_helm_scaling.json` (`max_infeasible_share_by_rule`).

**F5 `F_robust` (appendix).** Stability of the minimum L1 for seven (OLLB) / six (HELM) targets chosen by rank under the mean, under evaluation noise (binomial standard error of each score from the item counts; 300 OLLB draws closed rules, 60 ordinal; 200 HELM draws) and under a bootstrap over tasks (same caps). Dot (left of the bar) = median over feasible draws, bar = 2.5-97.5 percentile of draws, open diamond (right of the bar) = value on the observed data; the two are offset so they never overlap, and the y axis has headroom so no marker touches the frame; bottom rows = percentage of draws in which first place is unreachable within the cap. Reading (from the analysis, `experiment-repo`#5): wherever the observed target is feasible its cost lies inside the noise interval and mostly slightly below the draw median (a few percent); feasibility at the frontier is noise-sensitive (a target infeasible on the observed data can be feasible in a few percent of noise draws, and far-from-frontier targets are infeasible in every draw). Ordinal rules on OLLB are shown for the strata targets only.
