#!/usr/bin/env python3
"""Download only explicitly allowlisted data and official style files; record hashes."""
from pathlib import Path
import argparse, concurrent.futures, hashlib, json, urllib.request, urllib.parse, datetime, zipfile
ROOT=Path(__file__).resolve().parents[1]
SHA='9c09a7cae43334062a82cb164f2ef255013dafa2'
BASE='https://storage.googleapis.com/crfm-helm-public/'
REFERENCE=ROOT/'data/reference_manifest.json'
EXPECTED={r['path']:r['sha256'] for r in json.loads(REFERENCE.read_text())['files']} if REFERENCE.exists() else {}

def fetch(url,path):
    path=ROOT/path;path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'IndependentLeaderboardAudit/1.0'})
        with urllib.request.urlopen(req,timeout=90) as f: b=f.read()
        path.write_bytes(b)
    b=path.read_bytes();relative=str(path.relative_to(ROOT));digest=hashlib.sha256(b).hexdigest()
    if relative in EXPECTED and (relative.startswith('data/raw/') or relative.endswith('icml2026.zip')):
        if digest!=EXPECTED[relative]:raise ValueError('Pinned checksum mismatch: '+relative)
    return dict(path=relative,url=url,bytes=len(b),sha256=digest,retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--template',action='store_true');args=ap.parse_args()
    records=[]
    records.append(fetch('https://storage.googleapis.com/storage/v1/b/crfm-helm-public/o?prefix=mmlu/benchmark_output/releases/v1.13.0/groups/json/&maxResults=1000','sources/helm_listing.json'))
    listing=json.loads((ROOT/'sources/helm_listing.json').read_text())
    names=[o['name'] for o in listing['items'] if o['name'].split('/')[-1].startswith('mmlu_mmlu_subject:')]
    assert len(names)==57,len(names)
    def one(name):return fetch(BASE+urllib.parse.quote(name,safe='/:'),'data/raw/helm/'+name.split('/')[-1])
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: records+=list(ex.map(one,names))
    records.append(fetch(BASE+'mmlu/benchmark_output/releases/v1.13.0/summary.json','data/raw/helm_summary.json'))
    records.append(fetch(f'https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/{SHA}/data/train-00000-of-00001.parquet','data/raw/contents.parquet'))
    if args.template:
        records.append(fetch('https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip','sources/icml2026.zip'))
        records.append(fetch('https://icml.cc/Conferences/2026/AuthorInstructions','sources/icml2026_page.html'))
        with zipfile.ZipFile(ROOT/'sources/icml2026.zip') as z:z.extractall(ROOT/'paper/template')
    (ROOT/'data/manifest.json').write_text(json.dumps({'helm_version':'v1.13.0','contents_commit':SHA,'files':records},indent=2))
    print('Downloaded/verified',len(records),'files;',sum(r['bytes'] for r in records),'bytes')
if __name__=='__main__':main()
