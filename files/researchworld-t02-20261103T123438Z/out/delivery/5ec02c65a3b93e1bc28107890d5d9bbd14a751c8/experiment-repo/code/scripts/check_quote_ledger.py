"""Regression: regenerating a quote never replaces an existing live ledger."""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as temporary:
    fixture=Path(temporary)
    (fixture/'configs').mkdir()
    (fixture/'reproduction').mkdir()
    shutil.copy2(root/'configs/confirmatory.json',fixture/'configs/confirmatory.json')
    shutil.copytree(root/'results/gate-benchmarks',fixture/'results/gate-benchmarks')
    shutil.copytree(root/'results/pilot',fixture/'results/pilot')
    ledger=copy.deepcopy(json.loads((root/'reproduction/deadline_ledger.json').read_text()))
    ledger['production_launched_utc']='2026-11-03T15:00:00+00:00'  # test fixture only
    ledger['production_status']='test representative live status'
    ledger['job_refs']+=['test-appended-job-ref']
    ledger_path=fixture/'reproduction/deadline_ledger.json'
    ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
    before=ledger_path.read_bytes()
    subprocess.run([sys.executable,str(root/'code/scripts/resource_quote.py'),'--root',str(fixture)],check=True,stdout=subprocess.DEVNULL)
    assert ledger_path.read_bytes()==before
    after=json.loads(ledger_path.read_text())
    assert after['production_launched_utc']==ledger['production_launched_utc']
    assert after['job_refs']==ledger['job_refs']
    assert after['absolute_one_week_deadline_utc']==ledger['absolute_one_week_deadline_utc']
    result=dict(status='PASS',existing_ledger_byte_identical=True,
        preserves=['non-null launch','appended job refs','status','immutable start/deadlines'],
        behavior='quote regeneration writes no existing ledger; only absent ledger gets initial template',
        fixture='isolated temporary copy; actual production ledger untouched')
(root/'results/quote-ledger-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
