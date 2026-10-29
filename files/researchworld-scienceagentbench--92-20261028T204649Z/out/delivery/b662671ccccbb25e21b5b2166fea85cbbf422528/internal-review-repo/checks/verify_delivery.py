"""Foreground execution and independent scalar arithmetic for the requested scores."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

root = Path(sys.argv[1]).resolve()
data = Path('/benchmark/datasets/jnmf_visualization')
program = root / 'workspace/pred_programs/pred_h_importances.py'
output = root / 'workspace/pred_results/jnmf_h_importances.json'
delivered = json.loads(output.read_text())
matrices = {}
for name in ('W_high', 'W_low', 'H_high', 'H_low'):
    path = data / f'fit_result_conscientiousness_{name}.npy'
    a = np.load(path, allow_pickle=False)
    assert a.ndim == 2 and a.shape[1] == 2 and np.isfinite(a).all()
    matrices[name] = a.tolist()
    print(name, 'shape=', a.shape, 'sha256=', hashlib.sha256(path.read_bytes()).hexdigest())
wh, wl, hh, hl = (matrices[n] for n in ('W_high', 'W_low', 'H_high', 'H_low'))
assert len(wh) == len(wl)
high_total = math.fsum(x for row in hh for x in row)
low_total = math.fsum(x for row in hl for x in row)
total = high_total + low_total
ref = {
    'common error': 1.0 - math.fsum(a[0] * b[0] for a, b in zip(wh, wl)),
    'common importance': math.fsum(row[0] for row in hh + hl) / total,
    'high importance': math.fsum(row[1] for row in hh) / high_total,
    'low importance': math.fsum(row[1] for row in hl) / low_total,
    'distinct error': math.fsum(a[1] * b[1] for a, b in zip(wh, wl)),
    'distinct importance': math.fsum(row[1] for row in hh + hl) / total,
}
# A fresh cwd prevents a pre-existing output file from masquerading as execution.
with tempfile.TemporaryDirectory(prefix='jnmf-review-') as temp:
    result = subprocess.run([sys.executable, str(program)], cwd=temp, check=True,
                            text=True, capture_output=True)
    print('Foreground stdout:\n' + result.stdout)
    generated = json.loads((Path(temp) / 'pred_results/jnmf_h_importances.json').read_text())
assert set(delivered) == set(ref) == set(generated)
assert generated == delivered, 'Regenerated and delivered JSON differ'
for name, expected in ref.items():
    actual = delivered[name]
    assert type(actual) in (int, float) and math.isfinite(actual)
    error = abs(actual - expected)
    assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
    print(f'{name}: delivered={actual:.17g} independent={expected:.17g} abs_error={error:.3g}')
assert math.isclose(delivered['common importance'] + delivered['distinct importance'], 1.0, abs_tol=1e-12)
print('PASS: six scores, exact key set, finite numeric JSON, fresh foreground execution, and regenerated output agreement')
print('Python', sys.version.split()[0], 'NumPy', np.__version__)
