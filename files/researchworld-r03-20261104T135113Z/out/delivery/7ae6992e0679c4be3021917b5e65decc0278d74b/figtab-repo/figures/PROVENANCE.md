# Provenance of figures and tables

All numbers are read from the CSVs in `results/summary` and `results/theory` of this repository (delivered by experiment-repo); nothing is typed into a script.
Rebuild from the repository root: `bash code/figtab/make_all.sh` (matplotlib, pandas, numpy; no randomness).

| script | artifact(s) | input CSVs (experiment-repo `results/summary` unless `theory/`) |
|---|---|---|
| `code/figtab/fig1_main_curves.py` | figures/fig1_main_curves.pdf | curves_B_mteb_dense56/mteb_dense.csv, floor_B_mteb_dense56/mteb_dense.csv |
| `code/figtab/fig2_scree.py` | figures/fig2_scree.pdf | scree.csv, datasets.csv |
| `code/figtab/fig3_paired.py` | figures/fig3_paired_vs_random.pdf | cluster_paired_B_{mteb_dense56,mteb_dense,helm_mmlu}.csv, paired_B_mteb_dense56/mteb_dense/helm_mmlu.csv, paired_d56_group.csv, paired_d56_temporal.csv |
| `code/figtab/fig4_conditions.py` | figures/fig4_conditions.pdf | curves_{d56_miss*,d56_mtrain*,d56_rank*,B_mteb_dense56}.csv, conditions.csv (column-mean baseline) |
| `code/figtab/fig4b_datasets.py` | figures/fig4b_datasets.pdf | curves_B_<dataset>.csv, floor_B_<dataset>.csv for every real dataset present |
| `code/figtab/fig5_shift.py` | figures/fig5_shift.pdf | curves_{B_mteb_dense56,B_mteb_dense,d56_group,d275_group,d56_temporal,d275_temporal}.csv, floor_<same>.csv, conditions.csv |
| `code/figtab/fig6_theory.py` | figures/fig6_theory.pdf, figures/figA3_theory_vs_cv_all.pdf | theory/theory_A_random.csv, theory/theory_B_greedy.csv, theory/vs_real_<dataset>.csv, theory/vs_real_trainonly_<dataset>.csv, curves_B_<dataset>.csv |
| `code/figtab/figA1_all_selectors.py` | figures/figA1_all_selectors.pdf | curves_B_mteb_dense56/mteb_dense/helm_mmlu.csv |
| `code/figtab/figA2_oracle_leak_cost.py` | figures/figA2_oracle_leak_cost.pdf | oracle_mteb_dense56.csv, leak_mteb_dense56.csv, curves_C_d56.csv |
| `code/figtab/figA4_cluster.py` | figures/figA4_cluster_paired.pdf | cluster_paired_B_{mteb_dense56,mteb_dense,helm_mmlu}.csv |
| `code/figtab/figA5_extra_baselines.py` | figures/figA5_extra_baselines.pdf | xcurves_sel_B_{mteb_dense56,mteb_dense,helm_mmlu}.csv, xcurves_rules_{d56_group,d56_temporal,d275_temporal}.csv, xfloor_rules_<same>.csv, floor_B_<dataset>.csv |
| `code/figtab/tables.py` | tables/table1_datasets.tex, table2_kstar.tex, tableA1_kstar_best_and_absolute.tex, table3_crossing.tex, tableA2_crossing_all.tex, tableA3_oracle.tex, tableA4_leakage.tex, tableA5_synthetic.tex, tableA6_cluster_kstar.tex, tableA7_kstar_shift.tex, tableA8_ood_detector.tex, tableA9_kstar_split.tex, tableA10_extra_selectors.tex, tableA10c_extra_selectors_paired.tex, tableA10b_extra_rules.tex, tableA11_temporal_drift.tex | datasets.csv, kstar_table.csv, curves_B_mteb_dense56.csv, oracle_*.csv, leak_*.csv, curves_B_syn_*.csv, cluster_kstar_B_<dataset>.csv, group_counts.csv, ood_<run>.csv, cluster_kstar_B_{mteb_dense56,mteb_dense,helm_mmlu}.csv, kstar_gap_{d56,d275}_{group,famgroup,temporal}.csv, xcurves_sel_B_<dataset>.csv, xpaired_sel_B_<dataset>.csv, xcurves_rules_{d56,d275}_temporal.csv, extra_temporal_summary.csv |
