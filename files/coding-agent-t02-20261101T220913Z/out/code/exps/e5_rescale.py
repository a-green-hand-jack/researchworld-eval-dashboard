"""E5: causal norm intervention. Rescale all parameters by c at first step with train acc>=0.99.  c=1 reused from E1."""
import sys, os, shutil; sys.path.insert(0, '/work/code')
import sweep
out = '/work/results/e5_rescale'
os.makedirs(out, exist_ok=True)
cfgs = []
for d in [24, 32, 64, 128]:
    for c in [0.6, 0.8, 1.2, 1.4]:
        for seed in range(4):
            cfgs.append(dict(arch='tf', p=59, frac=0.4, width=d, seed=seed, lr=1e-3, wd=1.0, steps=30000, rescale=c,
                             eval_every=50, stop_after_gen=300))
sweep.run_grid(cfgs, out, 4)
