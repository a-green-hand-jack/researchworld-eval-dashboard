# Global Memory Summary

Use as qualitative context only; do not use as quantitative grounding source.

## Recent Entries

- 2026-11-11T07:48:54.655366Z | step=idea | scope=idea
  - summary: Selected idea: characterize regression-based GATE error as corner-exposure extrapolation bias vs variance across graphs, mechanisms, designs, models. gate=kept; trigger=none; reason=no prior evidence.
  - evidence: No prior attempts/histories; chosen from task context and starter literature (Chin 2019, Han&Ugander 2023, Ugander 2013).
- 2026-11-11T08:30:00Z | step=implement | scope=program
  - summary: Cloned program_0; rewrote program_1/src/program.py: ridge regression GATE family with extrapolation-aware model selection/averaging and design-resampling wild block bootstrap CI; DiM/Hajek fallbacks. Untested (no execution allowed).
  - evidence: (missing evidence)
- 2026-11-11T07:59:01.720937+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=-0.23241643926779176, correct=True; scientific acceptance passed; search metrics (data): {"baseline_dim_rmse_rel": 0.6232941898446912, "baseline_ht_rmse_rel": 0.9245644451443786, "baseline_linear_rmse_rel": 0.1841297578911339, "baseline_oracle_rmse_rel": 0.049784811226036924, "bias_rel_abs_mean": 0.18540408502273953, "ci_coverage": 0.6875, "ci_width_rel": 0.2974923683194412, "combined_score": -0.23241643926779176, "control_constant_max_abs_est": 0.0, "control_permuted_graph_rmse_rel": 0.6521964143923895, "control_permuted_outcome_mean_abs_rel_est": 0.14922187426340824, "control_vacuity_violations": 0.0, "correct": true, "missing_or_failed_episodes": 0.0, "ratio_to_dim_baseline": 0.3728840137683682, "ratio_to_linear_baseline": 1.2622426810836693, "replay_abs_diff": 0.0, "rmse_rel": 0.23241643926779176, "rmse_rel_case_1": 0.07010666532079847, "rmse_rel_case_2": 0.05460117882744864, "rmse_rel_case_3": 0.04991016153456786, "rmse_rel_case_4": 0.032724964060882496, "rmse_rel_case_5": 0.3139276510935619, "rmse_rel_case_6": 0.710166948078311, "rmse_rel_case_7": 0.2003235240644234, "rmse_rel_case_8": 0.42757042116234034}
- 2026-11-11T08:10:00+00:00 | step=idea | scope=idea
  - summary: Selected c02 linear base + design-weighted shrunk residual correction; gate=kept; trigger=none
  - evidence: cycle-1 flexible ensemble -0.232 worse than linear -0.184
- unknown_ts | step=unknown_step | scope=unknown_scope
  - summary: linear base + shrunk design-weighted HT corner residual correction; edited program_1/src/program.py only; not evaluated
  - evidence: (missing evidence)
- 2026-11-11T08:03:44.297349+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=-0.18478414847992633, correct=True; scientific acceptance passed; search metrics (data): {"baseline_dim_rmse_rel": 0.6232941898446912, "baseline_ht_rmse_rel": 0.9245644451443786, "baseline_linear_rmse_rel": 0.1841297578911339, "baseline_oracle_rmse_rel": 0.049784811226036924, "bias_rel_abs_mean": 0.1638917316048664, "ci_coverage": 0.671875, "ci_width_rel": 0.18375724330008636, "combined_score": -0.18478414847992633, "control_constant_max_abs_est": 0.0, "control_permuted_graph_rmse_rel": 0.629239856378698, "control_permuted_outcome_mean_abs_rel_est": 0.05959235008711256, "control_vacuity_violations": 0.0, "correct": true, "missing_or_failed_episodes": 0.0, "ratio_to_dim_baseline": 0.29646377503690474, "ratio_to_linear_baseline": 1.0035539643145532, "replay_abs_diff": 0.0, "rmse_rel": 0.18478414847992633, "rmse_rel_case_1": 0.08168649476225466, "rmse_rel_case_2": 0.03574948423561497, "rmse_rel_case_3": 0.058078787073602936, "rmse_rel_case_4": 0.028544986766936866, "rmse_rel_case_5": 0.02226344338626941, "rmse_rel_case_6": 0.7081851135577993, "rmse_rel_case_7": 0.09848510465410135, "rmse_rel_case_8": 0.44527977340283104}
- 2026-11-11T08:20:00+00:00 | step=idea | scope=idea
  - summary: Parametric exposure-mapping library with BIC-margin gate and linear fallback, targeting bias-dominated cases 6/8. gate=kept; trigger=none; reason=no new evidence yet.
  - evidence: c01 -0.232, c02 -0.185 vs incumbent -0.184; cases 6/8 ~0.71/~0.44 unchanged across both; bias_rel_abs_mean ~0.16 vs rmse 0.18.
- unknown_ts | step=unknown_step | scope=unknown_scope
  - summary: (missing summary)
  - evidence: (missing evidence)
- 2026-11-11T08:08:17.283052+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=-0.13957642911831114, correct=True; scientific acceptance passed; search metrics (data): {"baseline_dim_rmse_rel": 0.6232941898446912, "baseline_ht_rmse_rel": 0.9245644451443786, "baseline_linear_rmse_rel": 0.1841297578911339, "baseline_oracle_rmse_rel": 0.049784811226036924, "bias_rel_abs_mean": 0.09239311627989542, "ci_coverage": 0.8125, "ci_width_rel": 0.3663242485113022, "combined_score": -0.13957642911831114, "control_constant_max_abs_est": 5.435725080354051e-15, "control_permuted_graph_rmse_rel": 0.629239856378698, "control_permuted_outcome_mean_abs_rel_est": 0.05933818738657601, "control_vacuity_violations": 0.0, "correct": true, "missing_or_failed_episodes": 0.0, "ratio_to_dim_baseline": 0.22393346736168032, "ratio_to_linear_baseline": 0.7580329802032066, "replay_abs_diff": 0.0, "rmse_rel": 0.13957642911831114, "rmse_rel_case_1": 0.08168649476225466, "rmse_rel_case_2": 0.030514359525275876, "rmse_rel_case_3": 0.058078787073602936, "rmse_rel_case_4": 0.028544986766936866, "rmse_rel_case_5": 0.02226344338626941, "rmse_rel_case_6": 0.2670751636285935, "rmse_rel_case_7": 0.18316842440072476, "rmse_rel_case_8": 0.44527977340283104}
