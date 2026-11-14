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
a transfer assumption, not a measured HELM quantity. 78 targets, so most bins hold fewer than 10 targets and the CIs are wide. Copeland winner (dashed, open markers, no band) is drawn over the Condorcet-winner curve, which it nearly coincides with; both were solved exactly for all 78 targets.

**F1b/F2b `F_ollb_oracle`, `F_helm_oracle` (appendix).** (HELM includes Copeland, as F2.) As F1/F2 with the oracle cap (scores may rise to 100). Every target is feasible, so these panels show what the rule
alone does; the values are lower bounds on the investment under any realistic cap.

**F3 `F_ollb_capgrid`, `F_helm_capgrid` (appendix).** Feasibility (left) and median L1/n among feasible targets (right) for three rank strata (OLLB: 2-5, 6-20, 21-100; HELM: 2-5, 6-20, 21-78; the number of
targets is in the axis label) under the caps the analysis ran (OLLB 7, HELM 8 incl. the transferred `emp95T`/`emp99T` and the pooled cap; +h: at most h points per task; emp: per-task empirical fine-tune gain percentile; front: best rival's score; 100: score ceiling). The caps are
ordered by the share of targets feasible averaged over mean, median and min (a data-derived order, not a cap size), so the curves rise from left to right by construction; the order differs between the datasets. Points: median (left: fraction); bars: 95% bootstrap CI over targets
(Wilson for fractions), rules offset horizontally; with 4 targets in the lowest stratum the intervals are wide. Under the mean rule the cost among feasible targets is the same at every cap (L1 = n times the gap to the best rival, Proposition 1), so that line is
flat; the cap changes only *whether* the target can get there. Median cost is omitted where fewer than 3 targets are feasible. OLLB Borda and Condorcet (top 50 only) were solved at `emp99` and the oracle cap and appear as unconnected markers; on HELM all rules are connected except Copeland, which was solved at six of the eight caps (not `emp95T`, `emp99P`) and is drawn as unconnected markers. HELM caps other than `ceil`/`emp99T` are sensitivity caps with no empirical HELM basis.

**F4 `F_helm_scaling`.** K/n and L1/n against the number n of randomly drawn HELM subjects (60 random subsets per n, cap `emp99T`); the target is the model ranked 2 (left) or 5
(right) under the subset's own rule. Lines: median over feasible draws; bands: 2.5-97.5 percentile over subset draws (spread across subsets, not a CI of the median).
The share of infeasible draws per rule is in `F_helm_scaling.json` (`max_infeasible_share_by_rule`).

**F5 `F_robust` (appendix).** Stability of the minimum L1 for targets at mean-rule ranks 2, 3, 5, 10, 20, 50, 100 (OLLB, cap `emp99`) and 2, 3, 5, 10, 20, 40 (HELM, cap `emp99T`), for mean, median, min, Borda and Condorcet winner (plurality and the squared-mean rule are in the summaries, not drawn).
Left column: evaluation noise (binomial standard error of each score from the item counts); right column: bootstrap over tasks (same caps). Draws: 300 for OLLB score rules, 60 for OLLB Borda/Condorcet (exact MILP, strata targets only), 200 on HELM. Dot = median over feasible draws, bar = 2.5-97.5 percentile of the draws (a spread of the draws, not a CI of the median), open diamond = value on the observed data;
strip below each panel = percentage of draws in which first place is unreachable within the cap. Reading (counts from `F_robust.json`): in every case where the observed target is feasible and has a draw interval, the observed L1 lies inside the interval (OLLB noise 30/30, OLLB bootstrap 30/30, HELM noise 21/21, HELM bootstrap 21/21 target x rule cases)
and mostly slightly below the draw median (29/30, 23/30, 15/21, 18/21): the observed cost is not a departure from the noise interval. Feasibility at the frontier is noise-sensitive: e.g. the HELM rank-20 target is infeasible on the observed data under the mean rule, yet finite in a minority of draws (strip), and the rank-40 target is infeasible in every draw. At ranks 2-3 the lower end of the interval is 0 because some draws already make the target first.
(Wording agreed with `experiment-repo`#5: do not write "observed cost lies below the interval".)

**Target set (all figures/tables, HELM median).** A target is any model that is not the unique strict leader under the rule at hand, strict by a margin of 0.001 points. Under the HELM median two models tie exactly at the top, so the median has 79 targets (the tied leader costs 0.001 points); our figures and tables restrict to targets other than the mean-rule leader, i.e. 78 for every rule (`experiment-repo` REPRODUCE.md, "Target sets and the first convention").
