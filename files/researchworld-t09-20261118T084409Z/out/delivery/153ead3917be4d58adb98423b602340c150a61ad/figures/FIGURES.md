# Figure/table → script → input

Filled in as results arrive; nothing is listed before its script exists and runs on real result files.

| Item | Claim (Outline) | Script | Input |
|---|---|---|---|
| Fig. 1 corner picture | thesis | `figures/src/fig1_corner.py` | `results/fig1_corner.parquet` (one draw) |
| Fig. 2 error anatomy | C1 | `figures/src/fig2_anatomy.py` | `results/summary/e1.csv, e1b.csv, e9.csv` |
| Fig. 3 projection bias | C2 | `figures/src/fig3_projection_bias.py` | `results/summary/e2.csv, e2b.csv` |
| Fig. 4 crossover | C3 | `figures/src/fig4_crossover.py` | `results/summary/e3.csv` |
| Fig. 5 collapse in Z | C4 | `figures/src/fig5_collapse.py` | `results/summary/e4.csv, c4_bias_loo.csv, c4_bias_pred.csv` |
| Fig. 6a misspecification map | C5/H4 | `figures/src/fig6a_misspec_map.py` | `results/summary/c11_map.csv` |
| Fig. 6b GCR U-curve | C7 | `figures/src/fig6b_gcr_ucurve.py` | `results/summary/e5.csv` |
| Fig. 7 diagnostic (a) e7 ranks, (b) D4 on grid e12 with stress and control rows, (c) bound B | C6 | `figures/src/fig7_diagnostic.py` | `results/summary/c6_rank.csv, c6_B_vs_bias.csv, c12_rank.csv` |
| App. fig., D1 against abs. bias (was Fig. 7b) | C6 | `figures/src/fig7_d1_scatter.py` | `results/summary/c6_cover_cells.csv` |
| Table 1 mechanism × method | C5 | `tables/src/tab1_method_mechanism.py` | `results/summary/c5_table1.csv` |
| App. table, full C5 (median, worst) | C5 | `tables/src/app_tab_c5_full.py` | `results/summary/c5_table1.csv` |
| Table wins (REG-L vs each) | C3/C5 | `tables/src/tab_wins.py` | `results/summary/c3_pairs.csv` |
| App. table, staggered rollout | C7 | `tables/src/app_tab_stag.py` | `results/summary/e8.csv` |
| Table 2 coverage and width by class | C6 | `tables/src/tab2_coverage.py` | `results/summary/c6_cover.csv` |
| App. table, coverage and width by regime | C6 | `tables/src/tab2_coverage.py` | `results/summary/c6_cover.csv` |

Run from the repository root: `python3 -I figures/src/<script>.py`. Schema: `results/README.md`.

Placed size: every figure PDF is exactly 5.50 in wide (`figstyle.save`, no tight bounding box), so
`\includegraphics[width=\linewidth]` does not rescale it and text is 8 pt as printed. Heights (in):
Fig. 1 1.87, Fig. 2 1.93, Fig. 3 1.87, Fig. 4 1.93, Fig. 5 1.98, Fig. 7 2.09 (aspect 0.38; two legend rows), appendix D1 scatter 2.70 x 2.29 (6a, 6b 2.20, appendix).
