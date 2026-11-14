"""Experiment grids. Each function returns a list of config dicts (see grok.run)."""


def heads(d):
    return max(1, min(4, d // 4))


def pilot():
    # exploratory pilot (NOT used for confirmatory claims): p=53, frac .5, widths x 2 seeds
    return [dict(p=53, train_frac=0.5, seed=s, d=d, n_heads=heads(d), lr=1e-3, wd=1.0, steps=12000,
                 eval_every=50) for d in (4, 8, 16, 32, 64, 128) for s in (0, 1)]
