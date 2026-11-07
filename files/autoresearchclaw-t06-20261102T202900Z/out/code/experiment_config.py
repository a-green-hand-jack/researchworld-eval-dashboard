"""Configuration, hyperparameters and pre-registered hypothesis thresholds."""

HYPERPARAMETERS = {
    'seeds': [0, 1, 2],
    'time_budget_sec': 3600,
    'time_guard_frac': 0.80,
    'top_m': 8,                     # adjacent pairs among top-m ranked participants
    'bt_l2': 1e-4,
    'bt_max_iter': 50,
    'bt_tol': 1e-6,
    'n_bootstrap': 40,              # iid bootstrap replicates
    'random_flip_reps': 3,          # reps for random-flip budget
    'random_grid_points': 12,
    'max_budget_frac': 0.40,        # never edit more than this fraction of N
    'adv_batch_small': 1,
    'adv_k_exact_max': 15,
    'adv_batch_large': 10,
    'subsample_fracs': [0.5, 1.0],
    'tost_margin_log': 0.35,
    'rho_threshold_h2': 0.7,
    'mag_miscal_threshold_h2': 5.0,
    'adv_vs_rand_ratio_threshold_h2': 10.0,
    'h3_ratio_A_over_B': 3.0,
    'h3_ratio_C_over_B': 5.0,
    'h3_design_effect': 3.0,
    'h3_cluster_ci_ratio': 1.3,
    'min_pairs': 12,
    'min_comparisons_per_model': 20,
    'use_real_data': True,
    'data_dir': './data',
    'h3_reps': 12,
    'tie_handling': 'half',
    'nba_year_min': 2005,
    'nba_year_max': 2015,
    'nba_home_advantage': True,
    # per-(condition, dataset, seed) wall-clock cap (seconds)
    'per_run_cap_sec': 25,
    # cap on records per dataset used in the flip-budget search (CPU budget)
    'max_records_search': 5000,
}

CONDITIONS = [
    'DARTS',
    'Random Search',
    'bootstrap_ci_overlap_and_flip_probability',
    'wald_se_bt_fisher_information',
    'random_flip_budget_baseline',
    'dropping_data_amip_influence_baseline',
]

# Synthetic stand-in generators (used ONLY when real files are absent).
# Harder than before: more participants, smaller latent spread (small adjacent
# gaps), larger cluster noise, higher tie rates, sparser comparison graphs.
SYNTH_SPECS = {
    'arena_synth':   dict(kind='crowd',  M=40, N=14000, spread=0.55, n_clusters=3000, cluster_sd=0.45, tie_rate=0.20, density=0.6),
    'mtbench_human': dict(kind='expert', M=12, N=2400,  spread=0.45, n_clusters=90,   cluster_sd=0.30, tie_rate=0.15, density=1.0),
    'nba_synth':     dict(kind='sports', M=50, N=9000,  spread=0.35, n_clusters=400,  cluster_sd=0.10, tie_rate=0.0,  density=1.0),
}
JUDGE_SPEC = dict(bias_sd=0.5, flip_rate=0.22)