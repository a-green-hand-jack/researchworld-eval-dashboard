"""Experimental configuration (single source of truth for all scripts)."""
DATASETS = {
    # name: (n_sub for subsampling (None=all), n_instances, budget grid for coalition evaluations m)
    "pima":       dict(n_sub=None,  n_inst=30, grid=[128, 512, 2048, 8192]),
    "gmsc":       dict(n_sub=40000, n_inst=30, grid=[128, 512, 2048, 8192]),
    "acs":        dict(n_sub=40000, n_inst=30, grid=[128, 512, 2048, 8192]),
    "german":     dict(n_sub=None,  n_inst=30, grid=[128, 512, 2048, 8192]),
    "wdbc":       dict(n_sub=None,  n_inst=30, grid=[128, 512, 2048, 8192]),
    "spambase":   dict(n_sub=None,  n_inst=30, grid=[256, 1024, 4096, 16384]),
    "arrhythmia": dict(n_sub=None,  n_inst=20, grid=[1024, 4096, 16384, 32768]),
}
MODELS = ["lr", "mlp", "xgb", "rf"]
B = 100            # background size (rows) for every run unless stated otherwise
R_A = 10           # full reruns (new background + new coalition seed)
R_B = 6            # reruns with fixed background (estimator randomness only)
REF_COALITIONS = 131072   # coalition evaluations of the high-budget reference estimator
EXACT_MAX_D = 20
INSTANCE_SEED = 12345
