"""E1: main width sweep, 1-layer transformer, p=59, frac=0.4, lr=1e-3, wd=1 (Nanda et al. settings), 8 seeds."""
import sys; sys.path.insert(0, '/work/code')
import sweep
cfgs = []
for d in [8, 16, 24, 32, 48, 64, 96, 128]:
    for seed in range(8):
        cfgs.append(dict(arch='tf', p=59, frac=0.4, width=d, seed=seed, lr=1e-3, wd=1.0, steps=30000,
                         eval_every=50, stop_after_gen=300))
sweep.run_grid(cfgs, '/work/results/e1_width', 4)
