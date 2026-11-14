"""E6: other modular operations (a-b and a^2+b^2 mod p), same setting as E1, widths {16,32,64,128}, 4 seeds."""
import sys; sys.path.insert(0, '/work/code')
import sweep
cfgs = []
for op in ['sub', 'x2y2']:
    for d in [16, 32, 64, 128]:
        for seed in range(4):
            cfgs.append(dict(arch='tf', p=59, frac=0.4, width=d, seed=seed, lr=1e-3, wd=1.0, steps=30000, op=op,
                             eval_every=50, stop_after_gen=300))
sweep.run_grid(cfgs, '/work/results/e6_ops', 4)
