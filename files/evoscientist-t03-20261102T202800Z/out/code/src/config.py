"""Central experiment configuration (all numbers used by the paper come from here)."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "artifacts")      # trained models, instances, backgrounds
RES = os.path.join(ROOT, "results")        # raw attribution arrays (.npz)

DATASETS = ["german", "pima", "gmsc", "acs"]       # main (low/medium d)
MODELS = ["lr", "rf", "xgb", "mlp"]
ESTIMATORS = ["kernel", "perm"]
BUDGETS = [32, 64, 128, 256, 512, 1024, 2048]  # coalition evaluations per explained instance
N_INST = 60          # explained test instances per dataset (random, fixed seed)
R = 16               # independent repeated runs of the explainer per instance/budget
M_BG = 50            # background rows
SEED_DATA = 0
SEED_INST = 7
SEED_BG = 0

# E2 background resampling
E2_M = [10, 50, 200]; E2_B = 2048; E2_N = 30; E2_R = 12
# E3 retraining replicates
E3_K = 8; E3_SUB = 0.8
# E5 high-dimensional stress test
E5_DS = "arrhythmia"; E5_MODELS = ["lr", "rf", "xgb"]; E5_BUDGETS = [512, 2048, 8192]; E5_N = 16; E5_R = 8
REF_B = 8192   # budget of the high-budget KernelSHAP reference for d > 12 (non-tree models)
