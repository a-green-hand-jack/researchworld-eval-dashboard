"""Experiment grids. Each function returns a list of cfg dicts for grok.run. data_seed = seed (so
run-to-run variance includes the random train/val split)."""
def _c(**k):
    k.setdefault("data_seed", k.get("seed", 0)); return k

def pilot():
    cs = []
    for arch, ws in [("mlp", [4, 8, 16, 32, 64, 128, 256, 512]), ("tf", [8, 16, 32, 64, 128])]:
        for w in ws:
            cs.append(dict(arch=arch, p=53, frac=0.5, width=w, lr=1e-3, wd=1.0, seed=0, steps=20000))
    return cs

MLP_W = [4, 6, 8, 12, 16, 24, 32, 48, 64, 128, 256, 512, 1024]
TF_W = [8, 12, 16, 24, 32, 48, 64, 128]

def e1_mlp_width():   # main width sweep, MLP, p=53, frac .5, add
    return [_c(arch="mlp", p=53, frac=0.5, width=w, seed=s, steps=40000, eval_every=25)
            for w in MLP_W for s in range(8)]

def e2_tf_width():    # same for 1-layer transformer
    return [_c(arch="tf", p=53, frac=0.5, width=w, seed=s, steps=30000, eval_every=50)
            for w in TF_W for s in range(5)]

def e3_frac():        # train-fraction x width (capacity threshold should move with n_train)
    return [_c(arch="mlp", p=53, frac=f, width=w, seed=s, steps=40000, eval_every=25)
            for f in (0.3, 0.4, 0.7) for w in MLP_W[:-1] for s in range(4)]

def e4_randlabel():   # memorisation capacity: random labels on the same training inputs
    return [_c(arch="mlp", p=53, frac=f, width=w, seed=s, steps=20000, eval_every=50, randlabel=True,
               wd=wd, thr=0.99, stop_extra=0)
            for f in (0.3, 0.5, 0.7) for w in MLP_W[:-1] for s in range(3) for wd in (0.0, 1.0)]

def e5_hparam():      # lr x wd grid at several widths
    return [_c(arch="mlp", p=53, frac=0.5, width=w, lr=lr, wd=wd, seed=s, steps=60000, eval_every=25)
            for w in (32, 128, 512) for lr in (3e-4, 1e-3, 3e-3) for wd in (0.3, 1.0, 3.0) for s in range(3)
            if not (lr == 1e-3 and wd == 1.0)]

def e6_tasks():       # other operations / prime
    out = []
    for op, p in (("mul", 53), ("sub", 53), ("sq", 53), ("add", 97)):
        for w in (16, 32, 64, 128, 512):
            for s in range(4):
                out.append(_c(arch="mlp", p=p, op=op, frac=0.5, width=w, seed=s, steps=40000, eval_every=25))
    return out

def e7_init():        # init scale (lazy vs rich) x width
    return [_c(arch="mlp", p=53, frac=0.5, width=w, init_scale=i, seed=s, steps=40000, eval_every=25)
            for w in (32, 128, 512) for i in (0.5, 2.0, 4.0) for s in range(3)]

def e8_depth():       # depth 2 MLP
    return [_c(arch="mlp", p=53, frac=0.5, width=w, depth=2, seed=s, steps=40000, eval_every=25)
            for w in (8, 16, 32, 64, 128, 256, 512) for s in range(4)]
