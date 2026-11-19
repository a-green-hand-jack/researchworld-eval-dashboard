# experiment-repo — minimum targeted investment to top a multi-task leaderboard

Analysis code and results for: *how much targeted investment (raising a target model's scores on chosen sub-datasets) is needed to make it rank
first, and how does this depend on the aggregation rule?* Definitions follow `PLAN.md` of `story-repo` (§1). Reproduction: `REPRODUCE.md`
(environment, data versions + SHA-256, seeds, commands, runtimes, script → result map). In `paper-repo` this repository is delivered under `analysis/`.

## Layout
- `src/fetch_helm.py`, `src/fetch_ollb.py`, `src/ollb_items.py`, `src/build_data.py` — pinned downloads (SHA-256) and the cleaned score matrices `data/processed/`.
- `src/mti/scorerules.py` — exact solvers for score rules (mean, geometric/harmonic/power mean, median, min, trimmed mean).
- `src/mti/ordinal.py` — exact MILP solvers for rank rules (Borda, Condorcet-winner requirement, plurality, Copeland) with lazily generated rival constraints.
- `src/mti/data.py` — matrices, dataset variants and the cap scenarios.  `tests/` — solvers vs brute force on random small instances (`./reproduce.sh test`).
- `src/run_*.py` — experiment drivers; `src/summarize*.py`, `src/theory_*.py`, `src/check_consistency.py` — summaries, theory checks, cross-checks.
- `results/` — CSVs (tidy, one row per dataset × cap × rule × target); `results/tables/` — summary tables with uncertainty; `logs/` — old run logs (not needed).

## Setting (one paragraph)
Score matrix X (models × tasks, 0–100). One *target* model raises its scores on a task subset to y_t ∈ [x_t, c_t] (cap c_t), all other models fixed.
"First" = strictly above every rival under the rule with margin ε = 1e-3 points (ε = 0.1 as a check). Costs: **K** tasks touched, **L1** total points,
**Linf** largest single-task jump, plus **L2** (convex, mean/geometric only). *Infeasible* = no plan within the caps makes the target first.

## Conventions of the result files (answers to figtab-repo#3 item 5)
- Key columns: `dataset` (`helm`, `ollb`, variants `ollb_raw|ollb_nomerge|ollb_top500`), `cap`, `rule`, `target` (model name), `target_idx` (row of the dataset's matrix as returned by `mti.data.load`).
- `rank_mean` — rank of the target under the *mean* rule on that dataset's own scores (rank 1 = best, ties get the minimum rank). Used to group targets in every summary.
  `rank_rule` — rank under the row's own rule (ties = min); `NaN` for `condorcet` on OLLB (the Copeland-score ranking is only computed for M ≤ 400 models) and for rules without a value (none else).
- `rank_rule == 1` means first *or tied for first*; investment is 0 iff the target is *strictly* first. `rank_mean == 1` rows exist and can have L1 > 0 under the other rules.
- **Infeasible ⇔ `L1 = inf`, and then `K = inf`, `Linf = inf`, `u_star = inf`** (verified over every row by `src/check_consistency.py` → `results/consistency_checks.csv`).
  `NaN` in `L1/K/Linf` would mean a MILP stopped at its time limit (neither optimum nor infeasibility proven); the column `unproven` counts such solves per cell.
- `gap` — best rival's rule value minus the target's, in score points, only for score rules (absent/`NaN` for rank rules). `ollb_trim.csv` (trimmed mean, MILP) has no `K` column.
- **Linf is the uniform-gain benchmark**: the min-max plan raises every task by the same amount, so `Linf == u_star` for every row (checked). What is new in `ustar_*.csv` is the
  *volume* of the uniform plan (`u_L1`) and its breadth (`u_K`); `L1 ≤ u_L1` holds by optimality, so claim C6 is the ratio `L1 / u_L1` (`results/tables/targeted_vs_uniform.csv`), not a sign.
- Target sets: score rules on every model (OLLB: all 4496 non-flagged models = 4497 after de-duplication minus 1 flagged, rank 1 included; HELM: 79); rank rules and trimmed mean on a sample of 57 OLLB targets (ranks 2–21 plus a log-uniform sample of the rest; seed 0).
  Cross-rule comparisons therefore use the paired ratios on the same targets (`paired_vs_mean.csv`) or the complete top-20 set (`head20_rule_comparison.csv`), not group medians of different samples.
- Caps: `ceil` 100; `front0|front2` best rival score on the task (+0/+2); `gain5|10|20` own score + h; `emp95|emp99` own score + the per-task 95th/99th percentile of
  (fine-tune − its base model) gains over the 540 base/fine-tune pairs in the OLLB (normalised scores; `Flagged` models excluded), floored at 0.
  **HELM has no base/fine-tune pairs**: `hemp95|hemp99` transfer the OLLB *MMLU-PRO* gain quantile (converted to raw accuracy points with the task's normalisation floor, ≈ 2.9 / 6.4 points) as a uniform per-subject cap. This is a transfer assumption and is labelled as such.
- Tie convention for rank rules: ties count ½; a raise counts at level (rival score) + ε (strict pass) or equal to it (tie).
- Time limit per MILP solve: 120 s; solves that hit it are flagged (`unproven`) and never recorded as infeasible.

## Result files
| file | content | script |
|---|---|---|
| `helm_main.csv`, `helm_emp.csv` | HELM, 8 rules × (6 caps; hemp95/99) × 79 targets | `run_core.py` (`core_helm`, `core_helm_emp`) |
| `ollb_closed.csv` | OLLB mean/geomean/harmonic/median/min × 8 caps × all targets | `core_ollb_closed` |
| `ollb_trim.csv`, `ollb_ord_{a,b,c}.csv` | OLLB trimmed mean, Borda/Condorcet/plurality on the 57-target sample | `core_ollb_trim`, `core_ollb_ord_*` |
| `var_ollb_{raw,nomerge,top500}_{closed,ord}.csv` | C5 variants (raw scores, no merged models, top-500) × caps ceil/front0/gain10 | `variants` |
| `ustar_*.csv` | `u_star`, `u_L1`, `u_K` of the uniform plan, same keys | `run_uniform.py` |
| `l2_cost.csv` | convex-cost plan (mean, geomean): `L2`, `K_L2`, `L1_atL2`, `Linf_atL2` | `run_l2.py` |
| `weighted_{helm,ollb}.csv` | weighted-mean sensitivity, 200 Dirichlet draws (`draw = -1`: equal weights) | `run_weighted.py` |
| `copeland_helm.csv` | exact Copeland optimum on HELM (with `proven_*` flags) | `run_copeland.py` |
| `eps01_*.csv` | tie margin 0.1 | `run_core.py --eps 0.1` |
| `theory_checks.csv`, `theory_pred.csv` | propositions checked against live solvers; tidy prediction-vs-solver table | `theory_checks.py`, `theory_table.py` |
| `helm_noise_gain10.csv`, `ollb_noise_gain10.csv`, `helm_taskboot_gain10.csv`, `helm_tasksub_gain10.csv`, `loto_*.csv` | robustness draws (evaluation noise, task bootstrap, task-subset size n, leave-one-task-out) | `run_robust.py`, `run_loto.py` |
| `tables/*.csv` | summaries with bootstrap CIs (see headers of `summarize*.py`) | `summaries.sh` |
| `consistency_checks.csv` | cross-checks between independently computed columns | `check_consistency.py` |
