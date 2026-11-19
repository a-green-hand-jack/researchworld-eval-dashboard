# Figure/table plan (figtab-repo) — answers figtab-repo#3

Format: NeurIPS 2026, main text <= 9 pages incl. figures (venue-repo#4). Column width 5.5 in; figures are vector PDF, fonts >= 7 pt at final size, colour-blind-safe palette, design identity (crowd / expert / LLM judge / sports) encoded by the same colour in every figure. Every figure caption states: claim, size scale, what the band/interval is (seeds, bootstrap, percentile level), n of claims/seeds.

| Id | Claim | Display (main text unless noted) | Reads (tidy CSV from `results/`, see contract) |
| --- | --- | --- | --- |
| T1 | E1 descriptive | Table: design, K, N, tie share, min/median/max pair count, share of pairs with zero comparisons, claim set used (top-20 restriction for Arena) | `summary_datasets.csv` |
| F1 | E1 | Forest plot, small multiples: BT score +- bootstrap CI, rank interval annotated; Arena top-20, MT-Bench human, MT-Bench GPT-4 in main; NBA seasons/full and Arena-all in appendix | `base_scores.csv` |
| F2 | E2 | Claim-survival curves: P(claim unchanged) vs fraction f removed (log x), one panel per dataset, lines = C1/C2/C3, solid = random removal, dashed = label flips, band = seed percentile interval; marks where the verified adversarial budget lies on the same axis (vertical ticks) | `random_survival.csv`, `adv_budgets.csv` |
| F3 | E3 | Verified adversarial budget (upper bound) for adjacent-pair claim as a function of rank r, per dataset; left: fraction of N (log y); right: noise-equivalent units; C1 and C3 shown as separate markers | `adv_budgets.csv` |
| F4 | E4 | Scatter log budget vs log z-gap, coloured by design, pooled fit with cluster-bootstrap band; coefficient table (T2) alongside | `adv_budgets.csv` (z_gap, pair counts), `regression_coef.csv` |
| F5 | E5 | Paired (slope) plot: same MT-Bench claim under human vs GPT-4 labels, budget and z-gap shown | `adv_budgets.csv` filtered, `matched_labeller.csv` |
| T3 | E6 | Table: budget by method (influence-only guess, greedy+verify, heuristics, exhaustive where feasible), ratio to best; appendix scatter guess vs exact | `method_validity.csv` |
| T3b | E6 | Table: exhaustive enumeration (budgets <= 5) vs greedy+polish, greedy, one-shot; censored claims shown separately | `method_validity_exhaustive.csv` |
| F6 | E4 controls | Synthetic vs real budget; N-matched subsamples vs N (size vs design); synthetic rows flagged | `controls.csv`, `adv_budgets.csv` |
| T4 | E7 | One compact table: ablation x dataset, median budget (fraction of N) with CI; synthetic rows marked "SYNTHETIC" | `ablations.csv` |
| T5 | E8 | Addition vs removal budgets (one table; main or appendix depending on space) | `additions.csv` |

Page economy suggestion: main = T1, F1 (3 panels), F2, F3, F4+T2, F5, T3/T4 merged if needed; everything else appendix. Final split is decided with paper-repo after seeing the results.

## Input contract (asked of experiment-repo; tidy long-format CSV, one row per observation)
Every file carries the columns `dataset, design, code_rev, data_version, seed` where applicable.
- `summary_datasets.csv`: dataset, design, K, N, n_tie, min/median/max pair count, frac_pairs_unobserved.
- `base_scores.csv`: dataset, participant, n_comparisons, score, ci_lo, ci_hi (bootstrap B, level stated), rank, rank_lo, rank_hi.
- `random_survival.csv`: dataset, claim_type (C1/C2/C3), claim_id (e.g. rank r, k), perturbation (remove/flip), f, seed, survived (0/1) — or aggregated with n_seeds and Wilson/percentile interval.
- `adv_budgets.csv`: dataset, claim_type, claim_id, rank, budget (integer, verified), budget_frac_N, budget_frac_pair, budget_noise_units, z_gap, n_pair_comparisons, method, verified (bool), search_status (found / not found within cap), and interval over dataset bootstrap if run. Claims where no flip was found need an explicit censored row, not omission.
- `regression_coef.csv`, `matched_labeller.csv`, `method_validity.csv`, `ablations.csv`, `additions.csv`: columns self-explanatory from the table above; synthetic rows carry `synthetic=True`.
Stage-0 outputs (`summary_datasets.csv`, `base_scores.csv`) let me start T1/F1 immediately; I need nothing else before that.

## Working rules
- Generators in `code/figs/` of this repo (delivered as `figures/`, `tables/` with scripts alongside); `make_all.py` regenerates from a given `results/` path and writes `figures/MANIFEST.json` (input file sha256 + experiment-repo commit).
- Nothing is plotted from numbers not in a committed result file.

Update (interim 2): F3b and T0 no longer use the noise-equivalent leverage (a near-identity of z and k/N, declared by experiment-repo); they show k as a share of the pair's own comparisons. Added T3b, T4, F6.

## Update (interim 3, request paper-repo#5)
- F4 gets panel (b): first-order k_hat against the verified budget (s5_khat.csv); T8 gives the out-of-sample bias (s5_oos_summary.csv).
- F6 panel (b): the one-run N=1,367 point is replaced by the 40-draw medians with 95% intervals (s5_control_summary.csv).
- T0: median z (iid / cluster); T4: window-of-10 and old-claim-set rows; T5: random-removal (noise-equivalent) columns.
- New: F8 window sweep (fig8_window.pdf; F7 stays the noise-equivalence figure), T7 estimator sensitivity (table7_estimator), T8 out-of-sample, T9 restarts; T6 gets the C1-prime columns.
