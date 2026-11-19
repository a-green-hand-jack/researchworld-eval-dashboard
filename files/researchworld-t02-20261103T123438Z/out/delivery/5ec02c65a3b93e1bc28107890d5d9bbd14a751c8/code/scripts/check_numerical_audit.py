"""Audit regression on a copied measured endpoint; never new training/science."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

repo=Path(__file__).resolve().parents[2]
source=repo/'results/confirmatory/decay_w512_b04'
if not (source/'summary.json').exists():
    raise SystemExit('Requires the supplied completed large-logit control endpoint')
with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary);run=root/source.name
    shutil.copytree(source,run)
    report=root/'audit.json'
    command=[sys.executable,str(repo/'code/scripts/audit_registered.py'),str(root),
        '--registry',str(repo/'configs/confirmatory.json'),'--output',str(report)]
    original=subprocess.run(command,cwd=repo,capture_output=True,text=True)
    assert original.returncode==0,original.stderr
    state=json.loads(report.read_text())
    precision=state['split_diagnostics'][0]['numerical_precision']
    assert precision['total_prediction_differences']==1,precision
    assert precision['roundoff_ambiguous_prediction_count']>=1
    assert precision['max_error_fraction_of_bound']<1
    # Preserve summary/curve mutual identity while corrupting the actual stored
    # terminal loss. Only independent replay can detect this mutation.
    summary=json.loads((run/'summary.json').read_text())
    summary['final']['valid_loss']+=0.1
    (run/'summary.json').write_text(json.dumps(summary))
    curve=(run/'curve.jsonl').read_text().splitlines()
    curve[-1]=json.dumps(summary['final'])
    (run/'curve.jsonl').write_text('\n'.join(curve)+'\n')
    corrupted=subprocess.run(command,cwd=repo,capture_output=True,text=True)
    assert corrupted.returncode!=0
    assert "'valid', 'loss'" in corrupted.stderr,corrupted.stderr
print('PASS: strict terminal replay, recorded float64 near-tie disagreement, roundoff envelope and independent corrupted-loss rejection; raw inputs untouched')
