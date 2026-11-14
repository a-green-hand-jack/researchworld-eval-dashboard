"""Audit endpoints, MC summaries, regenerated inputs, and source/template integrity."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from experiment import sample
from methods import all_intervals,dictionary
ROOT=Path(__file__).resolve().parents[1]
report=[]
for p in sorted((ROOT/'results/raw').glob('*.json')):
    m=json.loads(p.read_text());d=pd.read_csv(p.with_suffix('.csv.gz'))
    assert np.isfinite(d[['lo','hi','width']]).all().all()
    np.testing.assert_allclose(d.hi-d.lo,d.width,rtol=1e-9,atol=2e-12)
    assert (d.lo<=d.hi).all()
    np.testing.assert_array_equal(((d.lo<=m['theta'])&(d.hi>=m['theta'])).astype(int),d.covered)
    assert (d.groupby('method').rep.nunique()==m['reps']).all()
    assert not d.duplicated(['rep','method']).any()
    pop=None
    if m['kind']=='real':
        z=np.load(ROOT/'data'/f"{m['case']}.npz");pop=(z['Y'],z['Yhat'])
    rng=np.random.default_rng(m['seed']);y,sl,su=sample(m['case'],m['n'],m['N'],rng,pop)
    if m['kind']=='ablation':intervals={f'CV{k}':dictionary(y,sl,su,k) for k in [1,2,3,7,15]}
    else:intervals=all_intervals(y,sl,su,binary=(pop is not None or not m['case'].endswith('_cont')))
    first=d[d.rep==0].set_index('method')
    assert set(first.index)==set(intervals)
    for meth,endpoints in intervals.items():
        np.testing.assert_allclose(first.loc[meth,['lo','hi']].to_numpy(dtype=float),endpoints,atol=7e-12,rtol=1e-10)
    hashes={k:hashlib.sha256(x.tobytes()).hexdigest() for k,x in [('y',y),('sl',sl),('su',su)]}
    report.append(dict(cell=p.stem,repetitions=m['reps'],methods=len(intervals),first_input_sha256=hashes))
# The official style must remain byte-identical.
assert (ROOT/'paper/neurips_2026.sty').read_bytes()==(ROOT/'template/neurips2026/neurips_2026.sty').read_bytes()
assert len(report)==49
s=pd.read_csv(ROOT/'results/summary.csv')
assert len(s)==sum(z['methods'] for z in report)
(ROOT/'logs/output_audit.json').write_text(json.dumps(dict(passed=True,cells=report),indent=2))
print(f'PASS: {len(report)} conditions, {sum(z["repetitions"] for z in report)} repetitions, {len(s)} method summaries; first-draw endpoints regenerated; all stored widths/coverage audited; official style unchanged.')
