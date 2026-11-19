"""Software fixture for lost attempt ends and checkpoint rollback; no research run."""
import argparse
import contextlib
import hashlib
import io
import json
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import torch

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / 'code/src'))
from train import run


def same(a, b):
    if isinstance(a, torch.Tensor):
        return torch.equal(a, b)
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
start = time.perf_counter()
cpu_start = time.process_time()
child_start = resource.getrusage(resource.RUSAGE_CHILDREN)
report = dict(kind='software fixture only; not a scientific observation or launch authorization',
              started_utc=datetime.now(timezone.utc).isoformat(),
              source_train_sha256=hashlib.sha256((repo / 'code/src/train.py').read_bytes()).hexdigest())
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    uninterrupted, recovered = root / 'full', root / 'recovered'
    config = dict(p=7, fraction=.5, split_seed=98765, init_seed=87654, task='add',
                  width=13, activation='relu', lr=.001, weight_decay=1., steps=40,
                  onset_horizon=40, eval_every=5, checkpoint_every=20, report_every=100, threads=1)
    with contextlib.redirect_stdout(io.StringIO()):
        run(config, uninterrupted)
        run(config, recovered, stop_after=20)
        checkpoint20 = (recovered / 'checkpoint.pt').read_bytes()
        run(config, recovered, resume=True, stop_after=30)
    # Simulate a process killed at30 with only step20 durable: edits affect this fixture only.
    rows_before = [json.loads(line) for line in (recovered / 'curve.jsonl').read_text().splitlines()]
    events = [json.loads(line) for line in (recovered / 'attempts.jsonl').read_text().splitlines()]
    lost_id = events[-1]['attempt_id']
    assert events[-1]['event'] == 'ended'
    events.pop()
    original_event_bytes = ''.join(json.dumps(e)+'\n' for e in events).encode()
    (recovered / 'attempts.jsonl').write_bytes(original_event_bytes)
    (recovered / 'checkpoint.pt').write_bytes(checkpoint20)
    with contextlib.redirect_stdout(io.StringIO()):
        run(config, recovered, resume=True)
    full = torch.load(uninterrupted / 'final.pt', weights_only=False, map_location='cpu')
    final = torch.load(recovered / 'final.pt', weights_only=False, map_location='cpu')
    for key in ['model', 'optimizer', 'torch_rng_state', 'initial_vector', 'step']:
        assert same(full[key], final[key]), key
    timing = {'cpu_s', 'elapsed_s', 'training_s'}
    strip = lambda rows: [{k:v for k,v in row.items() if k not in timing} for row in rows]
    read_rows = lambda directory: [json.loads(line) for line in (directory / 'curve.jsonl').read_text().splitlines()]
    rows_after = read_rows(recovered)
    assert strip(read_rows(uninterrupted)) == strip(rows_after)
    archives = list(recovered.glob('curve.discarded-after-20.*.jsonl'))
    assert len(archives) == 1
    assert [json.loads(line) for line in archives[0].read_text().splitlines()] == [r for r in rows_before if r['step'] > 20]
    final_events = [json.loads(line) for line in (recovered / 'attempts.jsonl').read_text().splitlines()]
    assert (recovered / 'attempts.jsonl').read_bytes().startswith(original_event_bytes)
    assert not any(e['event']=='ended' and e['attempt_id']==lost_id for e in final_events)
    assert final_events[-2]['start_step']==20 and final_events[-2]['resume']
    assert json.loads((recovered / 'metadata.json').read_text())['cpu_accounting_incomplete']
    assert json.loads((recovered / 'summary.json').read_text())['cpu_accounting_incomplete']
    assert next(r for r in rows_after if r['step'] > 20)['cpu_s'] >= max(r['cpu_s'] for r in rows_before)
    # Analyze only this fixture and confirm the real reporting path suppresses CPU100.
    inputs = root / 'inputs'; inputs.mkdir()
    shutil.move(str(recovered), str(inputs / 'recovered'))
    subprocess.run([sys.executable, str(repo/'code/scripts/analyze.py'), str(inputs),
                    '--output', str(root/'analysis')], check=True, capture_output=True, text=True)
    record = json.loads((root/'analysis/runs.json').read_text())[0]
    assert record['cpu_accounting_incomplete']
    assert all(record[k] is None for k in ['cpu100_step', 'cpu100_acc', 'cpu100_recorded_s'])
    report.update(passed=True, assertions=['bitwise model,AdamW,RNG,initial-vector and final-step equality',
        'all nonclock metrics equal uninterrupted fixture', 'rolled-back rows retained exactly',
        'unmatched attempt start preserved without invented end', 'resume restarts at durable checkpoint',
        'known measured CPU prefix retained as lower bound', 'incomplete accounting propagates to metadata and summary',
        'actual analysis excludes CPU100'], fixture_steps=40, durable_checkpoint=20, last_preresume_row=30)
child_end = resource.getrusage(resource.RUSAGE_CHILDREN)
report.update(ended_utc=datetime.now(timezone.utc).isoformat(), wall_s=time.perf_counter()-start,
              process_cpu_s=time.process_time()-cpu_start,
              child_cpu_s=child_end.ru_utime+child_end.ru_stime-child_start.ru_utime-child_start.ru_stime,
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2)+'\n')
print('PASS: abrupt rollback preserves exact science/state and raw history; incomplete CPU excludes CPU100. Software fixture only.', flush=True)
