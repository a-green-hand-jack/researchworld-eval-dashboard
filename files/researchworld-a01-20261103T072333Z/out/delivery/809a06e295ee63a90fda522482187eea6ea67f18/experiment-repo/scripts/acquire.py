"""Fetch only frozen public score summaries; no model outputs or test questions."""
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
BASE = 'https://storage.googleapis.com/crfm-helm-public/'
PREFIX = 'mmlu/benchmark_output/releases/v1.13.0/'
HF_SHA = '9c09a7cae43334062a82cb164f2ef255013dafa2'

def fetch(item):
    name, url = item
    path = RAW / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(url, timeout=120) as response:
            path.write_bytes(response.read())
    content = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), url=url, bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest())

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    initial = [('helm_summary.json', BASE + PREFIX + 'summary.json'),
               ('helm_listing.xml', BASE + '?prefix=' + PREFIX + '&max-keys=1000'),
               ('open_llm.parquet', f'https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/{HF_SHA}/data/train-00000-of-00001.parquet')]
    records = [fetch(item) for item in initial]
    root = ET.fromstring((RAW / 'helm_listing.xml').read_bytes())
    keys = [el.text for el in root.iter() if el.tag.endswith('Key')]
    keys = [k for k in keys if '/groups/json/mmlu_mmlu_subject:' in k]
    assert len(keys) == 57, len(keys)
    items = [('helm/' + k.rsplit('/', 1)[1], BASE + urllib.parse.quote(k, safe='/')) for k in keys]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records.extend(pool.map(fetch, items))
    manifest = dict(acquired_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    helm_version='v1.13.0', helm_release_date='2025-01-10',
                    open_llm_commit=HF_SHA, files=records,
                    license_note='Score-data licenses not separately declared at supplied sources. Research use; no upstream license is asserted. Model Hub License metadata is not a license for the score table.')
    manifest_path = ROOT / 'data/manifest.json'
    if manifest_path.exists():
        expected = {r['path']: r['sha256'] for r in json.loads(manifest_path.read_text())['files']}
        actual = {r['path']: r['sha256'] for r in records}
        if expected != actual:
            raise RuntimeError('Frozen data checksum mismatch; preserve inputs and investigate source changes')
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Fetched/verified {len(records)} files ({sum(r["bytes"] for r in records)} bytes)', flush=True)

if __name__ == '__main__':
    main()
