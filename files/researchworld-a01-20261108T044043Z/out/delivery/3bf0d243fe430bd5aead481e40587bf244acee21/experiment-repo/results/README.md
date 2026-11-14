# results/ — what each file is

Produced by `code/` (command per file in `REPRODUCE.md` and `code/run_all.sh`). **Infeasibility** is encoded as `L1 = K = Linf = inf`
(no raise within the cap makes the target strictly first); `NaN` means the exact solver hit its time limit (censored, never
counted as infeasible). `status` in the core tables says which: `ok | infeasible | censored | already_first`.

## Core tables (use these; one row per cap x rule x target)
`core_ollb.csv` (4496 models, 6 tasks) and `core_helm.csv` (79 models, 57 subjects). Columns:
`dataset, cap, cap_role, rule, target, target_idx, rank_mean, rank_rule, gap, L1, K, Linf, L2, status`.
- `cap`: `emp99` (OLLB primary: per-task 99th percentile of fine-tune-minus-base gains, 540 OLLB pairs), `emp95`, `emp99T`
  (HELM primary: the OLLB MMLU-PRO 99th-percentile gain applied to all 57 subjects, **a transfer assumption**), `emp95T`, `emp99P`
  (pooled six-task percentile applied to every task, a loose cap), `ceil` (score <= 100, oracle), `front0` (cap at the best other
  model on each task), `gain5/10/20` (+5/10/20 points on every task). `cap_role` = primary | oracle | sensitivity.
- `rule`: `mean`, `median`, `min`, `borda` (mean rank), `condorcet` (target must beat every rival in a strict task majority; a
  sufficient condition for Copeland/Schulze/Kemeny), `plurality`, `copeland`, `geomean`, `harmonic`, `pow-<p>`/`pow<p>`. OLLB
  ordinal rules (`borda, condorcet, plurality`) exist for the 50 best targets under the mean only (exact MILP, M = 4496).
- `rank_mean`: rank of the target under the unweighted mean (ties share the best rank); `rank_rule`: its rank under its own rule.
- `L1` total points raised, `K` number of tasks raised, `Linf` the largest single-task raise (minimum over all ways to become first;
  each measure is minimised on its own, so the three need not come from one solution), `L2` sum of squared raises (mean, min, median only).
  `gap` = rival level minus target value under the score rules.
- first = strictly ahead by a margin `eps = 1e-3` point (sensitivity: 1 and 2 points in `variants/`).

## Summaries (`summary/`)
- `summary_{ollb,helm}_groups.csv` — median L1/K/Linf/L2 per cap x rule x rank stratum (rank under the mean) with bootstrap 95% CIs over
  targets; `*_infeasible` = share proven infeasible, `*_feas_med` = median among feasible targets (always read together). `_own_groups`:
  strata by the target's rank under the rule itself. `summary_*_relL1_vs_mean.csv`: median per-target L1 ratio to the mean rule.
- `frontier_{ollb,helm}.csv` — feasibility frontier per dataset x cap x rule. Rows per rank stratum: `n`, `n_feasible`, `feas_frac` with
  bootstrap CI (`feas_lo/hi`). Rows `group = frontier`: `max_feasible_rank` (largest rank_mean of a feasible target), `prefix_rank`
  (largest r with every target of rank <= r feasible), `r50` (lower end of the first stratum with feasible share < 0.5), CIs by
  bootstrap over targets. OLLB ordinal rules cover only the 50 best targets, so their frontier is a lower bound.
- `paired_{ollb,helm}.csv` — ordered rule pairs (`rule_a`, `rule_b`) per cap x stratum: `n_both` (targets feasible under both, positive
  cost in both), `n_either`, median ratio cost(a)/cost(b) for L1 and K with bootstrap CI, `*_a_cheaper` share. Selective by construction:
  read with `n_both / n_either`.
- `summary_variants.csv` — (weights runs use the stratified targets, ranks 2,3,5,10,20,50,100 on OLLB and 2,3,5,10,20,40 on HELM, x 500 weight draws each, so `n` counts draws) margin (eps 1 or 2 points), OLLB slices/raw scores, Dirichlet weights, sigma-unit cost against the baseline.
- `summary_rob_*.csv` — percentile intervals of the Monte Carlo runs (see below).

## Other files
- `theory_check.csv` — closed forms P1-P3 (mean, min, odd-n median) vs the exact solvers (all targets) and vs a generic LP/MILP
  (sample of 60 targets): max abs deviation of L1 and K and number of feasibility mismatches per dataset x cap x rule.
  OLLB median (n = 6, even) is solver-only.
- `official_rules_check.csv` — published aggregate vs the mean of the components we use (OLLB `Average`; HELM `MMLU All Subjects`).
- `robust/rob_*.csv` — one row per Monte Carlo draw x rule x target: `noise` = evaluation noise (binomial SE of each cell from the item
  counts, Gaussian draw), `taskboot` = bootstrap over tasks (same caps, per-task caps follow their task), `tasksub` = random subsets of
  `n` HELM subjects (target = the rank-2 and rank-5 model of each subset under its own rule). `summary/summary_rob_*.csv` — percentile
  intervals (2.5/50/97.5) over feasible draws, share infeasible/censored, median rank under the rule.
- `variants/` — dataset slices (`var_ollb_*`), margin sensitivity (`margin{1,2}_*`), weighted means (`weights_*`), cost in sigma units
  (`zcost_*`). `runs/` — the raw run files that `core_*.csv` are assembled from.
- `logs/` — the log of every step that wrote a shipped file (stale, empty or failed logs are listed in `REPRODUCE.md`); `runtime_*.csv` — measured run times.
- `cap_evidence/` — pair bootstrap of the empirical caps, leave-one-task-allowance-out, joint-gain description and HELM allowance sensitivity (`README.md` inside).
- `ordinal_sample/` — Borda and Condorcet on a rank-stratified sample of 60 OLLB targets beyond rank 50 on the full board (`README.md` inside).
- `leaf/` — OLLB 39-score-component run with its gate, caps, source manifest and digests (`README.md` inside).
- `variants/var_ollb_top500.csv` holds the mean, median, min, Borda, Condorcet-winner and plurality rules at `emp99` and `ceil` and Copeland at `emp99` only, on the 500 best OLLB models (499 with rank >= 2; the geometric, harmonic and power means are not in this slice).
  Feasibility and the minimum L1 cost are different outcomes: the L1, K and Linf programs are solved separately under a 120 s limit, and a censored L1 solve (NaN) does not make a target infeasible.
  Copeland, L1 outcomes: 329 solved, 121 proved infeasible, 50 censored. `variants/copeland_top500_screen.csv` settles feasibility per target (columns `l1_status`, `K_status`, `Linf_status`, `wins_at_saturation`, `feasibility`, `feasibility_basis`):
  375 of 500 feasible and 125 infeasible (374 of 499 excluding the mean leader); of the 50 L1-censored targets 46 are feasible (finite K and Linf; only the minimum L1 is unresolved) and 4 are infeasible. Per-stratum counts: `variants/copeland_top500_feasibility.csv`.
  In `summary/summary_variants.csv` `feas_frac` is the share with a finite **L1** cost over all targets of the group and `n_censored` counts censored L1 (plus censored K among finite L1) solves: for Copeland `feas_frac` is therefore a lower bound on the feasible share
  (upper bound `feas_frac + n_censored / n`; the settled value is `n_feasible/n` of `copeland_top500_feasibility.csv`), and `L1_med_feas` / `K_med_feas` are medians over the targets with a solved cost.
