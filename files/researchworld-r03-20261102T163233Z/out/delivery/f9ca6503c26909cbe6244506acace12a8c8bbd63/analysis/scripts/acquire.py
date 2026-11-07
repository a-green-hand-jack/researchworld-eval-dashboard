"""Fetch only the explicitly supplied public data sources, with pinned revisions."""
import argparse, hashlib, json, pathlib, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCES={
 'mteb':('https://api.github.com/repos/embeddings-benchmark/results/tarball/6dabbcc68c28ea5f180ce7df79347b3ca9cc6383','mteb.tar.gz'),
 'open_llm':('https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet','open_llm.parquet')}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('dataset',choices=SOURCES);a=p.parse_args()
 url,name=SOURCES[a.dataset];dest=ROOT/'data/raw'/name;dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():
  temporary=dest.with_suffix(dest.suffix+'.partial')
  with urllib.request.urlopen(url,timeout=180) as src,temporary.open('wb') as out:
   while chunk:=src.read(1024*1024):out.write(chunk)
  temporary.replace(dest)
 h=hashlib.sha256(dest.read_bytes()).hexdigest()
 info={'url':url,'filename':name,'bytes':dest.stat().st_size,'sha256':h}
 (ROOT/'data'/f'{a.dataset}_source.json').write_text(json.dumps(info,indent=2)+'\n');print(info)
