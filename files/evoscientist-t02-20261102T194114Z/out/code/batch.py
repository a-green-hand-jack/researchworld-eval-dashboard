"""Run an explicit JSON manifest with bounded CPU concurrency; preserve failures."""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def one(item):
    command = [sys.executable, 'train.py']
    for key, value in item.items():
        if isinstance(value, bool):
            if value:
                command.append('--' + key.replace('_', '-'))
        else:
            command.extend(['--' + key.replace('_', '-'), str(value)])
    log = Path(item['out']) / (item['name'] + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    with log.open('w') as f:
        result = subprocess.run(command, stdout=f, stderr=subprocess.STDOUT, env=env)
    record = dict(name=item['name'], command=command, returncode=result.returncode,
                  start_unix=start, elapsed=time.time()-start, log=str(log))
    print(json.dumps(record), flush=True)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--status', default='batch_status.json')
    args = parser.parse_args()
    jobs = json.loads(Path(args.manifest).read_text())
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(one, jobs):
            records.append(result)
            Path(args.status).write_text(json.dumps(records, indent=2))
    if any(r['returncode'] for r in records):
        raise SystemExit('Some runs failed; inspect logs. No failed run removed.')


if __name__ == '__main__':
    main()
