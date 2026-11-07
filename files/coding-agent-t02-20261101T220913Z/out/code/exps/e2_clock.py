"""E2: optimiser 'weight-decay clock' + hyper-parameter confound.  tf, p=59, frac=0.4, widths {32,64,128}, 3 seeds.
(lr, wd) = (1e-3,1) baseline is copied from E1 (seeds 0-2)."""
import sys, os, shutil; sys.path.insert(0, '/work/code')
import sweep
out = '/work/results/e2_clock'
os.makedirs(out, exist_ok=True)
grid = [(1e-3, 0.5), (1e-3, 2.0), (1e-3, 4.0), (2e-3, 1.0), (4e-3, 1.0), (5e-4, 1.0), (2e-3, 2.0)]
cfgs = []
for d in [32, 64, 128]:
    for lr, wd in grid:
        for seed in range(3):
            cfgs.append(dict(arch='tf', p=59, frac=0.4, width=d, seed=seed, lr=lr, wd=wd, steps=30000,
                             eval_every=50, stop_after_gen=300))
    for seed in range(3):
        base = dict(arch='tf', p=59, frac=0.4, width=d, seed=seed, lr=1e-3, wd=1.0, steps=30000)
        fn = sweep.name_of(base) + '.json'
        if not os.path.exists(os.path.join(out, fn)):
            shutil.copy(os.path.join('/work/results/e1_width', fn), os.path.join(out, fn))
sweep.run_grid(cfgs, out, 4)
