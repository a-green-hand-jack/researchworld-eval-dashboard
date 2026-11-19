# Figure/table map (figtab-repo)

All inputs are copies of committed `experiment-repo` results in `data_in/` (revision in `data_in/PROVENANCE_experiment_repo_commit.txt`). Run from the repo root with matplotlib 3.11.2. Delivered copies live in `paper-repo` `paper/figures/`, `paper/tables/`. Caption facts: `figures/CAPTIONS.md`.

| Output | Claim | Script | Input |
|---|---|---|---|
| `fig_headroom_population.{pdf,png}` | C1, C5 | `code/fig_headroom_population.py` | `data_in/headroom_population.csv`, `datasets.csv` |
| `fig_validity.{pdf,png}` | C0 | `code/fig_validity.py` | `data_in/summary_validity_real.csv` |
| `tables/tab_datasets.tex` | context | `code/tab_datasets.py` | `data_in/datasets.csv` |
| `tables/tab_headroom.tex` | C1, C5 | `code/tab_headroom.py` | `data_in/headroom_population.csv` |
| `fig_c2_real.{pdf,png}` | C2 (+C0) | `code/fig_c2_real.py` (uses `code/widthcov.py`) | `data_in/summary_mean_real.csv` |
| `fig_c2_real_app_a.{pdf,png}` | C2 appendix | same | `summary_mean_real.csv`, `summary_plankton_noshift.csv` |
| `fig_c3_synth.{pdf,png}` | C3 (knob, rho=0.1) | `code/fig_c3_synth.py` | `data_in/summary_synth.csv`, `theory_synth.csv` |
| `fig_c3_synth_app_knob_rho1`, `fig_c3_synth_app_named_{a,b}_rho{0.1,1}` | C3 appendix | same | same |
| `tables/tab_ols.tex` | C4 | `code/tab_ols.py` | `data_in/headline_ols_real.csv` |

Final-grid versions delivered from experiment-repo 2a7e4c588a74b4d63edb1268e1456196a92a5f0d. Still to build: ablation table (C6).
Pitfall handled: scenario name `null` must be read with `keep_default_na=False`.
