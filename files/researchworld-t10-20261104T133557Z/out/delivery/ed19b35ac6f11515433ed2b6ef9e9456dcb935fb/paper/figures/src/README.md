# Generators of the delivered figures and tables

`sh run_all.sh ../../../results OUT` rebuilds `OUT/figures/*.{pdf,png}` and `OUT/tables/*.tex` from `results/*.csv` (the scripts read them as `data_in/`, a symlink made by `run_all.sh`). Needs numpy, pandas, matplotlib 3.11.2.

| Output (paper/figures, paper/tables) | Script | Reads (results/) |
|---|---|---|
| `fig_headroom_population` | `fig_headroom_population.py` | `headroom_population.csv`, `datasets.csv` |
| `fig_validity` | `fig_validity.py` | `summary_validity_real.csv` |
| `fig_c2_real`, `fig_c2_real_app_a` | `fig_c2_real.py` | `summary_mean_real.csv`, `summary_plankton_noshift.csv` |
| `fig_c3_synth`, `fig_c3_synth_app_knob_rho1`, `fig_c3_synth_app_named_{a,b}_rho{0.1,1}` | `fig_c3_synth.py` | `summary_synth.csv`, `theory_synth.csv` |
| `tab_datasets.tex` | `tab_datasets.py` | `datasets.csv` |
| `tab_headroom.tex` | `tab_headroom.py` | `headroom_population.csv` |
| `tab_ols.tex` | `tab_ols.py` | `headline_ols_real.csv` |

`style.py` (palette, fixed colour/marker per method, rcParams) and `widthcov.py` (shared width-ratio/coverage panels) are imported by the figure scripts. Source repository: figtab-repo `code/`.
