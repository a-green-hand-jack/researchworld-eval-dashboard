"""Download open-llm-leaderboard/results (pinned commit) -> data/ollb_results/<path>.json (resumable)."""
import json, os, re, urllib.request, concurrent.futures as cf
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'data', 'ollb_results')
SHA = 'aa81ecc38fdc5708254b833923368970efdf5ef5'
import time, urllib.parse, urllib.error
def fetch(url, tries=60):
    for i in range(tries):
        try: return urllib.request.urlopen(url, timeout=120)
        except urllib.error.HTTPError as e:
            err = e
            if e.code == 429: time.sleep(min(float(e.headers.get('Retry-After') or 20), 120))   # rate limited: wait
            elif e.code == 404: raise
            else: time.sleep(5)
        except Exception as e:
            err = e; time.sleep(5)
    raise err
def list_all():
    url = f'https://huggingface.co/api/datasets/open-llm-leaderboard/results/tree/{SHA}?recursive=true&expand=false'
    files = []
    while url:
        r = fetch(url); files += json.loads(r.read())
        m = re.search(r'<([^>]+)>; rel="next"', r.headers.get('Link') or ''); url = m.group(1) if m else None
    return [f for f in files if f['type'] == 'file' and f['path'].endswith('.json')]
def dl(f):
    dest = os.path.join(OUT, f['path'])
    if os.path.exists(dest) and os.path.getsize(dest) == f['size']: return 0
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    data = fetch(f'https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/{SHA}/' + urllib.parse.quote(f['path'])).read()
    open(dest, 'wb').write(data); return 1
import urllib.parse, urllib.error
if __name__ == '__main__':
    fs = list_all(); print(len(fs), 'json files listed; bytes', sum(f['size'] for f in fs), flush=True)
    json.dump(fs, open(os.path.join(ROOT, 'data', 'ollb_results_filelist.json'), 'w'))
    # keep only the LATEST results file of every model directory (one evaluation per model)
    latest = {}
    for f in fs:
        d = os.path.dirname(f['path'])
        if d not in latest or f['path'] > latest[d]['path']: latest[d] = f
    fs = sorted(latest.values(), key=lambda f: f['path'])
    print(len(fs), 'model directories; bytes to fetch', sum(f['size'] for f in fs), flush=True)
    n = 0
    with cf.ThreadPoolExecutor(3) as ex:
        for i, r in enumerate(ex.map(dl, fs)):
            n += r
            if i % 1000 == 0: print(i, flush=True)
    print('downloaded', n)
