"""E4: other scale axes.  (a) depth of the transformer, (b) MLP width at two weight decays, (c) d_model vs d_mlp scaled separately."""
import sys; sys.path.insert(0, '/work/code')
import sweep
base = dict(p=59, frac=0.4, lr=1e-3, steps=30000, eval_every=50, stop_after_gen=300)
cfgs = []
for L in [2, 3]:                                   # (a) depth
    for d in [32, 64]:
        for seed in range(4):
            cfgs.append(dict(base, arch='tf', width=d, layers=L, wd=1.0, seed=seed))
for wd in [1.0, 5.0]:                              # (b) MLP width
    for d in [16, 32, 64, 128, 256, 512]:
        for seed in range(4):
            cfgs.append(dict(base, arch='mlp', width=d, layers=2, wd=wd, seed=seed, eval_every=100))
for d, mm in [(64, 1), (64, 16), (16, 16)]:        # (c) d_mlp = mm*d_model decoupled from d_model
    for seed in range(4):
        cfgs.append(dict(base, arch='tf', width=d, mlp_mult=mm, wd=1.0, seed=seed))
sweep.run_grid(cfgs, '/work/results/e4_arch', 4)
