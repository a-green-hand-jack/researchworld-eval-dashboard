"""E3: critical width for memorise-first vs number of training pairs N (varied via p and frac)."""
import sys; sys.path.insert(0, '/work/code')
import sweep
cfgs = []
for p, frac in [(31, 0.45), (31, 0.7), (59, 0.25), (59, 0.6), (97, 0.3)]:
    for d in [8, 12, 16, 24, 32, 48]:
        for seed in range(3):
            cfgs.append(dict(arch='tf', p=p, frac=frac, width=d, seed=seed, lr=1e-3, wd=1.0, steps=20000,
                             eval_every=50, stop_after_fit=300))
big = [c for c in cfgs if c['width'] > 16]
small = [c for c in cfgs if c['width'] <= 16]
sweep.run_grid(big, '/work/results/e3_capacity', 4)
sweep.run_grid_ens(small, '/work/results/e3_capacity', 4)
