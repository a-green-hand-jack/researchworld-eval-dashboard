"""Experiment definitions (lists of configs). See README for which paper figure uses which."""

WIDTHS_TF = [8, 16, 32, 64, 128, 256]


def pilot():
    """Exploratory pilot (seeds 0-2). Used ONLY to choose budgets/hypotheses; not in confirmatory claims."""
    return [dict(arch="tf", p=53, width=w, seed=s, max_steps=30000) for w in WIDTHS_TF for s in range(3)]


def pilot_mlp():
    return [dict(arch="mlp", p=53, width=w, layers=2, seed=s, max_steps=30000)
            for w in [16, 32, 64, 128, 256, 512, 1024] for s in range(3)]


# ============================== confirmatory experiments (fresh seeds 100+) ==============================
SEEDS_C = list(range(100, 106))
W_MLP = [24, 32, 48, 64, 96, 128, 192, 256, 384, 512]


def e1_mlp_width():
    """Core: MLP width sweep, p=53, add, train frac 0.3, lr 1e-3, wd 1."""
    return [dict(arch="mlp", p=53, layers=2, width=w, seed=s, max_steps=100000) for w in W_MLP for s in SEEDS_C]


def e2_random():
    """Memorisation probe: random labels on the same train sets (steps to 99% train acc)."""
    return [dict(arch="mlp", p=53, layers=2, width=w, seed=s, max_steps=100000, shuffle_labels=True)
            for w in W_MLP for s in range(100, 103)]


def e3_frac():
    ws = [24, 32, 48, 64, 96, 128, 192, 256]
    real = [dict(arch="mlp", p=53, layers=2, width=w, seed=s, train_frac=f, max_steps=60000)
            for f in (0.2, 0.5) for w in ws for s in range(100, 103)]
    rnd = [dict(arch="mlp", p=53, layers=2, width=w, seed=s, train_frac=f, max_steps=100000, shuffle_labels=True)
           for f in (0.2, 0.5) for w in ws for s in range(100, 103)]
    return real + rnd


def e4_timescale():
    grid = [(1e-3, 0.3), (1e-3, 1.0), (1e-3, 3.0), (5e-4, 2.0), (2e-3, 0.5), (5e-4, 1.0), (2e-3, 1.0)]
    return [dict(arch="mlp", p=53, layers=2, width=w, seed=s, lr=lr, wd=wd, max_steps=80000)
            for w in (128,) for (lr, wd) in grid for s in range(100, 104)]


def e6_generality():
    out = [dict(arch="mlp", p=53, layers=2, width=w, seed=s, op=op, max_steps=100000)
           for op in ("sub", "mul", "sq") for w in (64, 128, 256) for s in range(100, 104)]
    out += [dict(arch="mlp", p=97, layers=2, width=w, seed=s, op="add", max_steps=100000)
            for w in (64, 128, 256) for s in range(100, 103)]
    return out


REF_W = 128


def e7_param():
    """Width-dependent lr: (a) lr ~ 1/w, decay-rate lr*wd fixed; (b) lr ~ 1/w, wd fixed. ref width 128."""
    out = []
    for w in (64, 128, 256, 512):
        lr = 1e-3 * REF_W / w
        for tag, wd in (("a", 1.0 * w / REF_W), ("b", 1.0)):
            for s in range(100, 104 if w < 512 else 102):
                out.append(dict(arch="mlp", p=53, layers=2, width=w, seed=s, lr=lr, wd=wd,
                                max_steps=100000, tag=tag))
    return out


def e8_small():
    """Added after seeing that all e2 widths >= 24 fit random labels: search the capacity threshold
    at very small widths, for 3 train fractions, real and random labels."""
    out = []
    for f in (0.2, 0.3, 0.5):
        for w in (8, 12, 16, 20):
            for s in range(100, 104):
                out.append(dict(arch="mlp", p=53, layers=2, width=w, seed=s, train_frac=f, max_steps=60000))
                out.append(dict(arch="mlp", p=53, layers=2, width=w, seed=s, train_frac=f, max_steps=60000,
                                shuffle_labels=True))
    return out


def e5_tf():
    """Transformer replication (1 layer, d_model=width, 4 heads, d_mlp=4d), p=53 add, frac 0.3."""
    return [dict(arch="tf", p=53, layers=1, width=w, seed=s, max_steps=40000)
            for w in (16, 32, 64, 128) for s in range(100, 104)]


def e9_long():
    """Do stuck small models (no generalisation within 100k steps) ever generalise? 400k-step budget."""
    return [dict(arch="mlp", p=53, layers=2, width=w, seed=s, max_steps=400000, record_curve=True)
            for w in (48, 64) for s in range(100, 103)]


def e10_threshold():
    """Refine the generalisation-threshold width at train_frac=0.3 (widths between 64 and 96)."""
    return [dict(arch="mlp", p=53, layers=2, width=w, seed=s, max_steps=100000)
            for w in (72, 80, 88) for s in range(100, 106)]


def e11_saturation():
    """Post-hoc (exploratory) test of the saturation reading of the large-width regime: at w=384 does t_val
    still move with the optimiser time scale?  Baseline (lr 1e-3, wd 1) is in e1_mlp_width."""
    return [dict(arch="mlp", p=53, layers=2, width=384, seed=s, lr=lr, wd=wd, max_steps=60000)
            for (lr, wd) in ((2e-3, 1.0), (1e-3, 3.0)) for s in range(100, 104)]


def e5b_tf_small():
    """Same configs as e5_tf for the cheaper widths; run in a second process to use idle CPU
    (results are merged with e5_tf.jsonl by analysis.py; duplicates by key are dropped)."""
    return [c for c in e5_tf() if c["width"] < 128]


def e12_tf128_long():
    """Transformer d_model=128 did not reach 99% validation accuracy within 4e4 steps in e5 (val acc 0.06-0.98); longer budget."""
    return [dict(arch="tf", p=53, layers=1, width=128, seed=s, max_steps=100000) for s in range(100, 103)]
