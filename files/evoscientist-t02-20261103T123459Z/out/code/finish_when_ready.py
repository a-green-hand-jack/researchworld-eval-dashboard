"""Bounded release-build watcher; no new experiments or parameter changes."""
import json
import subprocess
import time
from pathlib import Path

root=Path(__file__).resolve().parent
start=time.monotonic()
while time.monotonic()-start<3600:
    manifest=root/'confirm_jobs.json.execution.json'
    record=json.loads(manifest.read_text()) if manifest.exists() else {}
    rows=record.get('records',[])
    if len(rows)==240 and all(r['status'] in ['ok','cached'] for r in rows):
        if len(list((root/'results/confirm').glob('*.pt')))==240:
            result=subprocess.run(['bash','reproduce.sh','--analysis-only'],cwd=root)
            raise SystemExit(result.returncode)
    if any(r['status']=='failed' for r in rows):raise RuntimeError('Training failure: inspect frozen manifest')
    print(f'Waiting for frozen ledger: {len(rows)}/240 launcher records',flush=True)
    time.sleep(20)
raise TimeoutError('Ledger not complete after bounded3600-second wait')
