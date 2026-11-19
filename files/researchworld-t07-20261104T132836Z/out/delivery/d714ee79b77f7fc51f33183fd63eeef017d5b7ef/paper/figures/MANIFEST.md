# Manifest: figures and tables -> generator -> inputs -> claim

Status: delivered against experiment-repo `results/` at commit 0b1df5aa53ef4a5544dad3189051780cc890252f (tidy tables; `sources_only` label). Outputs are in `paper/figures/*.pdf` and `paper/tables/*.tex`; the generator code is in `paper/figures/src` and `paper/tables/src`. Caption definitions: `paper/figures/CAPTIONS.md`.
Run all: `FIGTAB_RESULTS=<path to results/> bash paper/figures/make_all.sh` (default `<repo root>/results`; ~70 s on 1 CPU; seeds fixed, deterministic). Python: numpy, pandas, matplotlib 3.11.2.
Development benchmarks (ifeval, arc_challenge, gpqa, gsm; story-repo PLAN v1.1) carry an asterisk in every figure/table; headline tables give the 13-benchmark and the 9-non-dev summaries.

| output | script | input files (`results/`) | claim (story-repo#3) |
|---|---|---|---|
| `tables/headline_<proto>_n<n>.tex` (proto extrap/random, n 50/100) | `tables/src/tab_headline.py` | cells.csv | C1 cross-benchmark table |
| `tables/perbench_{rmse,kendall}_<proto>_n<n>.tex` | `tables/src/tab_headline.py` | cells.csv, paired.csv | C1 per-benchmark CIs, incl. low-spread gpqa/musr/openllm_math (C6) |
| `figures/paired_rmse_{mass_ens,mass}.pdf` | `figures/src/fig_paired.py` | cells.csv, paired.csv, best_baseline.csv, aggregate.csv | C2 pre-declared headline (vs random mean / ridge / best source-CV) |
| `figures/budget_relrmse.pdf` | `figures/src/fig_budget.py` | cells.csv, best_baseline.csv | C3 error vs budget |
| `figures/budget_grid_{random,extrap}.pdf` | `figures/src/fig_budget.py` | cells.csv, best_baseline.csv | C3 per benchmark (appendix) |
| `figures/ess_gain.pdf` | `figures/src/fig_ess.py` | ess_gain.csv | C3 ESS gain |
| `figures/extrap_scatter.pdf` | `figures/src/fig_extrap.py` | predictions_headline.csv | C4 true vs predicted |
| `figures/coverage.pdf` | `figures/src/fig_extrap.py` | coverage.csv | C4 interval coverage (MASS-Ens only: the only method with a reported SE) |
| `figures/sensitivity.pdf` | `figures/src/fig_sens.py` | cells.csv | C5 source count, extrap fraction |
| `tables/robustness_n100.tex` | `tables/src/tab_sens.py` | cells.csv | C5 dedup on/off, family-out |
| `tables/ablate_design_n100.tex`, `tables/ablate_rank_n100.tex` | `tables/src/tab_ablate.py` | cells.csv | C5 selection x predictor, latent rank |
| `tables/data_audit.tex` | `tables/src/tab_audit.py` | data_audit.csv | C6 |

Not produced (no data): bias-vs-position beyond the source range as a separate plot (positions are encoded by colour in `extrap_scatter.pdf`; `predictions_headline.csv` has `rank_pct_in_sources` if a separate plot is wanted).
