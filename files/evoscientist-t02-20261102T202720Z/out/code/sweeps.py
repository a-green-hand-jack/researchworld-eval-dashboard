"""Sweep definitions. Usage: python sweeps.py <stage> [workers]
Stages: main (width x train-fraction, p=53), pscan, mlp, robust.  Seeds 1-5 (pilot used seed 0)."""
import sys
from grok import *

WIDTHS = [8, 12, 16, 24, 32, 48, 64, 96, 128]


def stage(name):
    S = [1, 2, 3, 4, 5]
    if name == "main":
        return [base(d=d, frac=f, seed=s, max_steps=20000) for f in (0.4, 0.5, 0.6, 0.7) for d in WIDTHS for s in S]
    if name == "pscan":  # N varied through modulus at fixed fraction 0.5 (p=53 frac 0.5 comes from main)
        return [base(d=d, p=p, frac=0.5, seed=s, max_steps=12000) for p in (31, 43, 67) for d in (8, 16, 32, 64, 128) for s in S[:3]]
    if name == "mlp":
        return [base(arch="mlp", d=d, frac=f, seed=s, max_steps=12000) for f in (0.5, 0.7) for d in (4, 8, 16, 32, 64, 128) for s in S[:3]]
    if name == "robust":
        c = []
        for d in (16, 32, 64, 128):
            for s in S[:3]:
                c += [base(d=d, frac=0.5, seed=s, wd=w, max_steps=12000) for w in (0.3, 3.0)]
                c += [base(d=d, frac=0.5, seed=s, init_scale=i, max_steps=12000) for i in (0.5, 2.0)]
                c += [base(d=d, frac=0.5, seed=s, op=o, max_steps=12000) for o in ("sub", "mul")]
        return c
    raise ValueError(name)


if __name__ == "__main__":
    st = sys.argv[1]
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 36
    sweep(stage(st), f"results/{st}.jsonl", w)
