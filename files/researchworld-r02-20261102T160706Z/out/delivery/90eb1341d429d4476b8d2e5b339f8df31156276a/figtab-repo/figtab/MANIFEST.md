# Figure / table manifest

Generator → input → claim. Inputs are `experiment-repo/results/**` at the commit printed by `figtab/common.py:save` (run in a checkout of experiment-repo next to this repo, or set `CPC_RESULTS`).

| Output | Generator | Input (experiment-repo `results/`) | Claim | Status |
|---|---|---|---|---|
| `figures/fig1_beta_law.pdf` | `figtab/fig1_beta.py` | `theory/t1_beta_law.csv` | C1 | delivered (real data) |
| `figures/fig4_ncal.pdf` | `figtab/fig4_ncal.py` | `e1/sens_ncal*_{dirichlet,lognormal}.csv`, `e1/main*_{fam}_D5_h1_linear.csv` | C4, C6 | delivered (100 reps; regenerated on the final grid and final sens_ncal files) |
| `figures/fig6_delta_method.pdf` | `figtab/fig6_delta.py` | `theory/t4_points_*.csv`, `theory/t4_cond_coverage.csv` | C6 | delivered |
| `tables/tab1_methods.tex` | `figtab/tab1_methods.py` | none (static; names from results/README.md) | Table 1 | delivered |
| `tables/tab3_e2_labelsets.tex` | `figtab/tab3_e2.py` | `e2_summary.csv`, `e2_ident_summary.csv` | C7 | delivered |
| `figures/fig5_null_spread.pdf` | `figtab/fig5_null.py` | `null/null_binned.csv` | C5 | delivered (real data); the same null band is drawn inside Fig 3 |
| `tables/tab4_e3_cifar10h.tex` | `figtab/tab4_e3.py` | `e3_summary.csv` | C8 | delivered (12-epoch CNN, n_cal=1000, T=1) |
| `figures/fig7_shift.pdf` | `figtab/fig7_shift.py` | `e4_summary.csv` | C10 (E4 covariate shift) | delivered |

Regenerate everything: `cd figtab && python3 <script>.py` with experiment-repo checked out at `../../experiment-repo` (or `CPC_RESULTS=<path>`); each output is stamped with the experiment-repo commit it was made from (stdout; table files in a first-line comment).
Captions' facts: `figtab/CAPTIONS.md`. For D=3 the L1 and L-infinity scores induce the same ordering (differences sum to zero), so their rows coincide.

| `figures/fig2_size.pdf` | `figtab/fig2_size.py main_dirichlet_D3_h1_linear main_dirichlet_D5_h1_linear main_dirichlet_D10_h1_linear main_rounded_D10_h1_linear` | `e1/main_*.csv` (`pool_frac`) | C2, C4 | delivered |
| `figures/fig2_size_volume.pdf` | `SIZE_METRIC=vol_med python3 figtab/fig2_size.py main_dirichlet_D3_h1_linear main_dirichlet_D5_h1_linear main_lognormal_D5_h1_linear main_rounded_D5_h1_linear` | `e1/main_*.csv` (`vol_med`, D<=5) | C2 (robustness of the size metric, appendix) | delivered |
| `figures/fig3_conditional.pdf` | `figtab/fig3_cond.py main_dirichlet_D5_h0_linear main_dirichlet_D5_h1_linear main_lognormal_D5_h1_linear main_multinomial_D5_h1_linear main_rounded_D5_h1_linear`; null band from `null/null_binned.csv` | `e1/main_*.csv` | C3, C5 | delivered |
| `tables/tab2_e1_headline.tex` | `figtab/tab2_e1_headline.py` (default: dirichlet and lognormal, D=5, het., linear) | `e1/main_*.csv` | C2, C3 | delivered |
| `tables/tabA_e1_grid_{dirichlet,lognormal,multinomial,rounded}.tex` | `figtab/tab_a_grid.py` | all 48 `e1/main_*.csv` | C2, C3 (whole grid, appendix) | delivered |
| `figures/fig8_eps_sensitivity.pdf` | `figtab/fig8_eps.py` | `e1/sens_eps*_{dirichlet,multinomial,rounded}.csv`, `e1/main_{fam}_D5_h1_linear.csv` | C5 (Aitchison eps) | delivered |
| `figtab/fig_e1_config.py` | per-config 4-panel prototype | `e1/main_*.csv` | - | working material only, not delivered (superseded by Fig 2/3 and the appendix grid tables) |