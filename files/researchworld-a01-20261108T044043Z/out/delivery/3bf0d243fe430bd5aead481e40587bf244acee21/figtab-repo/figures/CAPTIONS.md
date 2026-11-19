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

**F3 `F_ollb_capgrid`, `F_helm_capgrid` (appendix).** Feasibility (left) and median L1/n among feasible targets (right) for three rank strata under the per-task caps of the
sensitivity grid (OLLB strata 2-5, 6-20, 21-100 with 4, 15, 80 targets; HELM strata 2-5, 6-20, 21-78 with 4, 15, 58 targets; counts are in the axis labels). The caps form three families that
are *not* ordered against each other: uniform +h points (h = 5, 10, 20), empirical fine-tune gain percentiles (p95, p99; on HELM the OLLB percentiles transferred, marked T, and a pooled six-task percentile), and the
references (front = best rival score on each task, 100 = score ceiling); within a family caps run from tight to loose and lines connect only within a family. Bars/whiskers: Wilson 95% interval (left),
95% bootstrap CI over targets (right, omitted where fewer than 3 targets are feasible). For a fixed target the mean-rule cost does not depend on the cap whenever the target is feasible (L1 = n times the gap to the best rival, Proposition 1), so the cap changes only *whether* a target can get there. The plotted median over feasible targets can nevertheless move with the cap, because the set of feasible targets changes (a looser cap adds targets, typically farther from first place); where the mean line looks flat the added targets have similar gaps. OLLB Borda and Condorcet (top 50 only, so only strata 2-5, 6-20 and part of 21-100) were solved at p99 and the oracle cap only and are drawn as unconnected markers; the stratum 2-5 holds 4 targets, so its intervals are wide.

**F4 `F_helm_scaling`.** K/n and L1/n against the number n of randomly drawn HELM subjects (60 random subsets per n, cap `emp99T`); the target is the model ranked 2 (left) or 5
(right) under the subset's own rule. Lines: median over feasible draws; bands: 2.5-97.5 percentile over subset draws (spread across subsets, not a CI of the median).
The share of infeasible draws per rule is in `F_helm_scaling.json` (`max_infeasible_share_by_rule`).

**F5 `F_robust` (score rules + Borda) and F5b `F_robust_rank` (rank rules).** Stability of the minimum L1 for seven (OLLB) / six (HELM) targets chosen by rank under the mean (x axis), under evaluation noise
(binomial standard error of each score from the item counts; 300 draws OLLB, 200 HELM) and under a bootstrap over tasks (same caps; 300 draws OLLB score rules, 200 HELM; the OLLB ordinal-rule panels of F5b use 60 draws
and the HELM noise panel of F5b 200). Dot = median over feasible draws, bar = 2.5-97.5 percentile of the draws (a spread, not a CI of the median), open diamond = value on the observed data;
bottom strips = percentage of draws in which first place is unreachable within the cap. Reading (recounted from the summaries and `core_*.csv` of the final analysis, over every stratum target and rule whose observed value is feasible): the observed L1 lies *inside* the 2.5-97.5 interval in every case (evaluation noise: OLLB closed forms 24/24, OLLB ordinal 16/16, HELM 26/26; OLLB ordinal task bootstrap 16/16) and below the draw median in 23/24, 14/16, 18/26 and 15/16 of those cases, i.e. a small downward offset, not a departure from the interval; at ranks 2-3 the lower end of the interval is 0 because some draws already make the target first. Feasibility at the frontier is noise-sensitive: under the mean rule the HELM rank-20 target is infeasible on the observed data but feasible in 4.5% of the noise draws (median 385 points), while the rank-40 target is infeasible in every draw. The OLLB ordinal panels cover only the targets at ranks 2, 3, 5, 10, 20, 50, 100 under the mean.
