#!/usr/bin/env python3
"""Compute JNMF importance factors from the supplied matrix columns.

Requires NumPy. Run with /workspace/.venv/bin/python in this environment.
"""

import json
from pathlib import Path

import numpy as np


DATA_DIR = Path('/benchmark/datasets/jnmf_visualization')
OUTPUT_PATH = Path('/workspace/pred_results/jnmf_h_importances.json')


def main():
    matrices = {}
    for name in ('W_high', 'W_low', 'H_high', 'H_low'):
        matrix = np.load(
            DATA_DIR / f'fit_result_conscientiousness_{name}.npy',
            allow_pickle=False,
        )
        if matrix.ndim != 2 or matrix.shape[1] < 2:
            raise ValueError(f'{name} must be a matrix with at least two columns')
        if not np.isfinite(matrix).all():
            raise ValueError(f'{name} contains non-finite entries')
        matrices[name] = matrix

    w_high, w_low = matrices['W_high'], matrices['W_low']
    h_high, h_low = matrices['H_high'], matrices['H_low']
    if w_high.shape[0] != w_low.shape[0]:
        raise ValueError('W_high and W_low must have the same number of rows')

    high_total = float(h_high.sum())
    low_total = float(h_low.sum())
    combined_total = high_total + low_total
    if any(total == 0 for total in (high_total, low_total, combined_total)):
        raise ValueError('Importance denominators must be nonzero')

    scores = {
        'common error': float(1.0 - np.dot(w_high[:, 0], w_low[:, 0])),
        'common importance': float(
            (h_high[:, 0].sum() + h_low[:, 0].sum()) / combined_total
        ),
        'high importance': float(h_high[:, 1].sum() / high_total),
        'low importance': float(h_low[:, 1].sum() / low_total),
        'distinct error': float(np.dot(w_high[:, 1], w_low[:, 1])),
        'distinct importance': float(
            (h_high[:, 1].sum() + h_low[:, 1].sum()) / combined_total
        ),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(scores, indent=2, allow_nan=False) + '\n')
    print(json.dumps(scores, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
