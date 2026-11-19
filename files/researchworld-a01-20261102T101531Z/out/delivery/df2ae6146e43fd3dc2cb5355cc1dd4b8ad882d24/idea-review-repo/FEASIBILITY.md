# Feasibility judgement (idea-review-repo)

Basis: objective issue and frozen inputs (`/initial-state/inputs/0`), plus a probe of the public data made 2026-11-02 (measured facts below; everything else is a planning estimate and marked so).

## Verdict
The study is feasible on CPU well inside the compute budget **if it is kept to a bounded design**. The binding constraints are not compute or data access; they are (a) the world's model-time budget (7200 s charged, shared by 9 positions, 96 turns) and (b) the fact that "investment" has no observable counterpart in the public data, so every investment-to-score link is a modelling assumption, not a measurement.

## Measured facts (probe)
| Source | Fact | Consequence |
|---|---|---|
| OLB `contents` parquet @ `9c09a7ca…` (HTTP 200, 1.1 MB) | 4576 models x 36 columns; 6 tasks (IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO), each with Raw (0-1 accuracy-like) and normalized column; no missing values in the Raw columns; has `Type`, `Base Model`, `Merged`, `Flagged`, `MoE`, `#Params (B)`, `Hub License`, `Submission Date` | Only 6 aggregation coordinates: mean/median/etc. are very coarse here; median over 6 is the mean of ranks 3-4 or a tie issue. Needs the subtask level for a richer rule comparison. |
| OLB `results` @ `aa81ecc3…` | Per-model JSON (one probed file: 116 KB) has 44 result keys: 24 BBH subtasks, 3 GPQA, 7 MATH sub-areas, IFEval, MMLU-PRO, 3 MUSR, each with stderr | ~36 leaf tasks with standard errors exist. **Discrepancy:** `data.md` states 10510 files totalling ~13.6 MB; at ~116 KB/file the real volume is ~1.2 GB (planning estimate from one file). Still within the 10 GB limit, but it is ~10^4 HTTP requests through the proxy: fetch a bounded subset (e.g. models in the top-K of the `contents` ranking plus a random sample), with retry/rate limiting, and record SHA-256 of the files used. |
| HELM MMLU v1.13.0 | `groups/json/mmlu_subjects_accuracy.json` holds the full 57-subject x 79-model EM matrix (file `…_subject:<name>.json` per subject also exist: 57); no missing cells (79 models all have 57); per-subject `# eval` from 100 to 1534 | Small, complete, cheap: ideal for the exact/enumerative analysis. Only 79 models and no scores for models' training data, so "first place" is a contest among few. Per-subject test sets are small (100 items for many subjects), so per-task noise is large (binomial SE up to ~5 points). |
| Compute | All of the above is O(10^4-10^7) arithmetic for ranking/optimisation | Planning estimate: well under the 4 CPU-hour allowance, even with bootstrap. |

## Risks and what to bound
1. **Investment-to-score model is assumed.** No data observe how much training on a subset's data raises a score. The study must (i) define investment abstractly (e.g. number of tasks targeted k, total score gain G in points, optionally a cost-weighted G) and make the headline claims *conditional* on stated gain models, (ii) show results are monotone/robust across a grid of gain models (additive points with cap at the score ceiling; fraction of remaining headroom closed; per-task cost proportional to size or to headroom), and (iii) not present absolute "cost to win" numbers as predictions of real training effort. Empirical calibration of plausible gains from the data (fine-tune vs `Base Model` pairs in OLB; same-family size ladders in HELM) is an optional sanity check only and is confounded; keep it labelled as such, and drop it first if time is short.
2. **Ceiling and scale effects.** Gains are capped at 100% (and effectively below, e.g. GPQA/MUSR near chance 25-40%); Raw vs normalized OLB columns give different aggregation outcomes. Choose one scoring convention up front, report the other as a sensitivity, and compute rule comparisons on a common scale.
3. **Aggregation set must be fixed in advance.** Mean (and weighted mean), median, trimmed mean, Borda/mean-rank, win-count/Copeland, minimum (worst-case), plurality/top-1 count are all cheap. More than ~6-8 rules or per-rule new theory will not fit; defer extras. Rank-based rules are not continuous in scores: exact minimal investment needs combinatorial search (small k) or a verified greedy/LP bound; state which is exact and which is an upper bound. Ties need a documented rule.
4. **Population definition.** OLB contains duplicates, merges, flagged and contaminated entries, and many weak models; "first place" depends on the competitor pool. Fix the pool (e.g. non-flagged, deduplicated by `fullname`, optionally restricted to a date or parameter-size window), run sensitivity to the filter, and report target selection explicitly (every model as target vs. the top-N, since the answer must be a function of initial rank/gap). A snapshot is frozen (2025-03), so conclusions are about those snapshots, not today's leaderboard.
5. **Strategic effects are out of scope for the empirical part.** Other developers reacting (equilibrium) is theory-only; a single-target, others-fixed (best response) design is feasible. Do not promise an equilibrium analysis from data.
6. **Uncertainty.** The data are deterministic, so there are no seeds to repeat. Uncertainty must come from (a) item-sampling noise of each score (binomial SE from `# eval`/`n-samples`, or the reported stderr) propagated by parametric resampling, and (b) bootstrap over tasks/competitors. Both are cheap; plan them from the start, not as an afterthought.
7. **Task-count dependence.** Results as a function of the number of tasks n should be shown by subsampling task sets from the larger HELM (57) and OLB-subtask (~36) pools; the 6-task OLB leaderboard alone cannot show scaling.
8. **Independence rule (objective: do not access the previously published study).** Literature search on "targeted training / aggregation / leaderboard rank" has a real chance of surfacing the prohibited paper or its citers. Every position that searches should (a) use the starter list and queries about *adjacent* topics (social choice, benchmark lottery, contamination), (b) stop reading at once if a page matches the forbidden description and (c) log it for the reproduction notes. Item 9 of the starter list is allowed (explicitly listed).
9. **Licenses.** Neither source declares a data license; reproduction notes must say so and cite the code's Apache-2.0 / the dataset's `Hub License` column; do not redistribute full raw mirrors, ship fetch scripts and checksums.
10. **Budget.** 7200 model-seconds world-wide for plan, analysis, figures, venue template, a full conference paper with checklist and two reviews is tight. Planning estimate: keep the paper to one main question with ~4 figures/tables in the body, everything else in the appendix. Template/checklist work (venue) and the LaTeX build (paper) cannot start from nothing late; analysis outputs should land in stable file paths early so figures and text do not wait on each other.

## Recommended bounded scope (for the plan)
- Primary data: HELM MMLU v1.13.0 (57 tasks, 79 models) and the OLB `contents` 6-task table; secondary: OLB subtask level for a subset (only if the fetch of per-model files works within budget).
- Primary analyses: minimal investment to reach rank 1 as a function of (rule, initial rank/gap, n tasks, gain model), exact for mean/min/median-type rules, with bounds stated for the rest; sensitivity to pool and scale; uncertainty by item-level resampling.
- Optional (cut in this order if short): empirical calibration of gains; weighted rules; subtask-level OLB; equilibrium discussion (text only).
- Claims should be stated as conditional on the gain model and pool, with explicit failure cases (e.g. rules where one task suffices, ceilings that make rank 1 unreachable).

## What is not feasible, and so must not be claimed
- Any real-training effect size or "cost in GPU-hours" (no training is allowed or measured).
- Current (post-2025-03) leaderboard conclusions.
- Equilibrium/multi-developer results from this data.

## Checks I will make on deliveries
Re-read the objective; check that every claim is conditional on a stated assumption; that each number traces to a script and data checksum; and that no required evaluation (uncertainty, rule comparison, conditions of failure, reproduction notes) has been dropped under budget pressure.

## Re-judgement against PLAN.md v2 (story-repo 92587d8)
- Plan §6 adopts all seven bounds. Judged feasible as written.
- `experiment-repo` commitment (#3) is wider than the plan (Schulze/ranked pairs, maximin, harmonic mean, synthetic factor-model study, time-snapshot robustness). Advised in experiment-repo#3: treat as extras after the core 8 rules; synthetic study labelled simulation only; time snapshot unavailable (frozen); Borda/Copeland exact only where enumerated/checked; OLB sub-task fetch on a rule-fixed model subset gives a different field and stays out of the headline; ablation grid on a fixed stratified target sample.
- Brief open items answered by the probe: HELM has no missing cells (57x79); OLB `results` is ~1.2 GB (estimate), not 13.6 MB, with several files per model.
- Open risk to watch on delivery: model-time budget (1118 of 7200 s charged when judged, analysis not started).
