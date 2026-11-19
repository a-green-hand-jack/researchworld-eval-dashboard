# figures/ and tables/ — outputs, generators, inputs, claims

Run from the repository root; `R` = `results/` of the analysis (this repository's `results/`). All scripts are in `figures/src/`
(`style.py` shared). Every figure has a `.json` sidecar with its arguments, the SHA-256 of each input file and the cell counts it
plots; `tables/MANIFEST.json` does the same for the tables. Nothing is computed beyond display statistics: bin medians with
bootstrap-over-targets intervals (B=1000, seed 0), Wilson intervals for fractions. Infeasible cases are never dropped silently: every
conditional cost panel is paired with a feasibility fraction, and captions must say "among feasible targets".

| output | command | inputs (under `R`) | what it shows / claim supported (plan id) |
|---|---|---|---|
| `F_ollb_primary` (F1) | `python3 figures/src/fig_rank_rules.py R ollb figures/F_ollb_primary --caps primary` | `core_ollb.csv` (cap `emp99`) | OLLB, primary cap: feasibility, K/n and L1/n vs the target's rank, 5 rules. Borda/Condorcet exist only for the 50 best targets under the mean. (F1, H1/H2) |
| `F_helm_primary` (F2) | `... fig_rank_rules.py R helm figures/F_helm_primary --caps primary` | `core_helm.csv` (cap `emp99T`, a transfer assumption) | same for HELM (n=57). (F2) |
| `F_ollb_oracle`, `F_helm_oracle` | `... --caps ceil` | `core_*.csv` (cap `ceil`) | the oracle (score <= 100) version: lower bound on any needed investment; feasibility is 1 everywhere, so it isolates the rule effect from the cap. Appendix. |
| `F_ollb_capgrid`, `F_helm_capgrid` (F3) | `python3 figures/src/fig_cap_grid.py R ollb figures/F_ollb_capgrid` (and `helm`) | `core_ollb.csv` (7 caps), `core_helm.csv` (8 caps) | how cap choice moves feasibility and cost, per rank stratum. Mean-rule L1 does not depend on the cap among feasible targets (P1). (F3, Q3) |
| `F_helm_scaling` (F4) | `python3 figures/src/fig_scaling.py R figures/F_helm_scaling` | `summary/summary_rob_helm_tasksub_emp99T.csv` | K/n and L1/n vs number of tasks n (random HELM subsets), by rule. Bands are the spread over 60 subset draws. (F4, H3) |
| `F_robust` (F5) | `python3 figures/src/fig_robust.py R figures/F_robust` | `summary/summary_rob_{ollb_noise_closed,ollb_noise_ord,ollb_taskboot_closed,ollb_taskboot_ord}_emp99.csv`, `summary_rob_helm_{noise,taskboot}_emp99T.csv`, `core_*.csv` | per-target stability of L1 under evaluation noise and task bootstrap, with the share of infeasible draws. Four panels: OLLB/HELM x evaluation noise/task bootstrap. (F5, Q5) |
| `tables/T2_theory_check.tex` | `python3 figures/src/tables.py R tables` | `theory_check.csv` | closed forms P1-P3 vs exact solvers and generic LP/MILP: max deviation, feasibility mismatches (aggregated over caps). OLLB median is solver only (n even). (T2, Q1) |
| `tables/T3_rules_{ollb,helm}_{emp99,emp99T,ceil}.tex` | same | `core_*.csv` | per rule and rank stratum: feasible count, median K and L1 among feasible targets with 95% bootstrap CIs, and median L1 ratio to the mean rule over targets feasible under both. Caveat for captions: the feasible set differs by rule, so costs and ratios are conditional on feasibility (e.g. HELM primary, rank 11-50: mean 6/40 feasible). (T3, Q2) |
| `tables/T4_frontier_{ollb,helm}.tex` | same | `core_*.csv`, `summary/frontier_*.csv` | feasibility frontier: Wilson share, r\* and all-feasible-up-to with the analysis' bootstrap CIs (asserted equal to our recomputation). (T4, Q2/Q3) |
| `tables/T5_variants_{ollb,helm}.tex` | same | `summary/summary_variants.csv` | sensitivity variants (margin, no-merge, raw, top-500, weights, sigma-unit cost) at the primary cap. Appendix. (T5, Q5) |
| `tables/T6_paired_{ollb,helm}_{emp99,emp99T,ceil}.tex` | same | `summary/paired_*.csv` | each rule vs the mean on targets feasible under both, by rank stratum, with n_both/n_either. (T6, Q2) |

Open items: provenance table T1 (the paper's data section typesets it from the analysis manifest). Everything regenerates with the commands above when `core_*.csv` or the summaries change.

Suggested caption stubs: state N targets, the cap and its role (primary / oracle), that bands are 95% bootstrap CIs over targets
within rank bins (bins double from rank 2; bins with fewer than 3 targets omitted), that the x position of a point is the geometric
mean rank of the targets in the bin, and that cost panels are conditional on feasibility.
