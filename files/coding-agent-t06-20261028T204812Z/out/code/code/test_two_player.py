"""Idealised 2-player BT check: for a small gap, K_remove ~ z sqrt(N), K_flip ~ z sqrt(N)/2, K_add ~ z sqrt(N)."""
import sys; sys.path.insert(0, '/work/code')
import numpy as np
from btlib import build_board
for N in (400, 4000, 40000):
    for p in (0.52, 0.55, 0.6):
        wins = int(round(p * N)); y = [1.0] * wins + [0.0] * (N - wins)
        b = build_board([0, 1], [0] * N, [1] * N, y, outcomes=(0.0, 1.0), lam=1e-9)
        th = b.base_fit(); c = b.contrast(0, 1); _, se = b.class_effects(th, b.W0, c); z = (c @ th) / se
        out = [N, p, round(z, 2)]
        for m in ('remove', 'flip', 'add'):
            out.append(round(b.attack(0, 1, m)['K'] / (z * np.sqrt(N)), 3))
        print(*out)
