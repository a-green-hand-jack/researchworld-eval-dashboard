"""Download public leaderboard data and record sha256 checksums (manifest in data/MANIFEST.json)."""
import json, hashlib, os, sys, urllib.parse, urllib.request, concurrent.futures as cf
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
D = os.path.join(ROOT, 'data')
GCS = 'https://storage.googleapis.com/crfm-helm-public/'
PREFIX = 'mmlu/benchmark_output/releases/v1.13.0/'
OLLB = 'https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet'

def get(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 0: return
    for _ in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r, open(dest, 'wb') as f: f.write(r.read())
            return
        except Exception as e: err = e
    raise err

def sha(p):
    h = hashlib.sha256(); h.update(open(p, 'rb').read()); return h.hexdigest()

def main():
    lst = json.loads(urllib.request.urlopen('https://storage.googleapis.com/storage/v1/b/crfm-helm-public/o?prefix=%s&maxResults=1000&fields=items(name,size)' % PREFIX).read())['items']
    jobs = []
    for it in lst:
        rel = it['name'][len(PREFIX):]
        jobs.append((GCS + urllib.parse.quote(it['name']), os.path.join(D, 'helm_v1.13.0', rel)))
    with cf.ThreadPoolExecutor(8) as ex: list(ex.map(lambda a: get(*a), jobs))
    get(OLLB, os.path.join(D, 'ollb_contents', 'train-00000-of-00001.parquet'))
    man = {}
    for dp, _, fs in os.walk(D):
        for f in fs:
            p = os.path.join(dp, f)
            if f in ('MANIFEST.json', 'helm_list.json'): continue
            man[os.path.relpath(p, D)] = {'sha256': sha(p), 'bytes': os.path.getsize(p)}
    json.dump(man, open(os.path.join(D, 'MANIFEST.json'), 'w'), indent=1, sort_keys=True)
    print(len(man), 'files; total bytes', sum(v['bytes'] for v in man.values()))
main()
