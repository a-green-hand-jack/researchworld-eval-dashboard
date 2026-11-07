"""Download the latest results_*.json per model from open-llm-leaderboard/results (pinned sha),
keeping only per-subtask scores + n-samples. Output: data/olmb/results_compact.jsonl"""
import json, sys, os, requests, urllib.parse
from concurrent.futures import ThreadPoolExecutor
SHA = 'aa81ecc38fdc5708254b833923368970efdf5ef5'
tree = json.load(open(sys.argv[1]))
out = sys.argv[2]
latest = {}
for s in tree['siblings']:
    f = s['rfilename']
    if not f.endswith('.json') or '/results_' not in f: continue
    model = f.rsplit('/', 1)[0]
    ts = f.rsplit('results_', 1)[1]
    if model not in latest or ts > latest[model].rsplit('results_', 1)[1]:
        latest[model] = f
print(len(latest), 'models with results files', flush=True)
def get(f):
    u = f'https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/{SHA}/' + urllib.parse.quote(f)
    for _ in range(4):
        try:
            r = requests.get(u, timeout=120); r.raise_for_status()
            d = r.json()
            res = {k: {a: b for a, b in v.items() if 'stderr' not in a and a != 'alias'} for k, v in d['results'].items()}
            return dict(model=f.rsplit('/', 1)[0] if False else f.split('/results_')[0], file=f, results=res,
                        n_samples={k: v.get('effective') for k, v in d.get('n-samples', {}).items()}, date=d.get('date'))
        except Exception as e:
            err = str(e)
    return dict(model=f.split('/results_')[0], file=f, error=err)
with ThreadPoolExecutor(24) as ex, open(out, 'w') as fo:
    for i, r in enumerate(ex.map(get, sorted(latest.values()))):
        fo.write(json.dumps(r) + '\n')
        if i % 500 == 0: print(i, flush=True)
