"""Download only explicitly authorized, pinned public data. No dataset search."""
import hashlib, json, pathlib, requests, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; RAW.mkdir(parents=True, exist_ok=True)
SOURCES=[
 ('arena.csv','https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv','0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2','apache-2.0'),
 ('nba.csv','https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv','d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc','CC-BY-4.0')]
def download(name,url,expected,license):
 p=RAW/name
 if not p.exists():
  r=requests.get(url,stream=True,timeout=180); r.raise_for_status()
  with p.open('wb') as f:
   for b in r.iter_content(1024*1024): f.write(b)
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 if expected and digest!=expected: raise ValueError((name,digest,expected))
 return dict(file=str(p.relative_to(ROOT)),url=url,sha256=digest,bytes=p.stat().st_size,license=license)
def main():
 start=time.perf_counter(); out=[]
 for args in SOURCES: out.append(download(*args)); print(out[-1],flush=True)
 repo='lmsys/mt_bench_human_judgments'; rev='f7d2896d2cc5d80f8b55c2bbc722613555233c25'
 tree=requests.get(f'https://huggingface.co/api/datasets/{repo}/tree/{rev}?recursive=true',timeout=60);tree.raise_for_status()
 for item in tree.json():
  path=item['path']
  if path.endswith('.parquet') and ('human-' in path or 'gpt4_pair-' in path):
   name='mt_human.parquet' if 'human-' in path else 'mt_gpt4.parquet'
   expected='4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769' if name=='mt_human.parquet' else '57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71'
   out.append(download(name,f'https://huggingface.co/datasets/{repo}/resolve/{rev}/{path}',expected,'CC-BY-4.0'));print(out[-1],flush=True)
 assert (RAW/'mt_human.parquet').exists() and (RAW/'mt_gpt4.parquet').exists()
 (ROOT/'data/manifest.json').write_text(json.dumps(dict(files=out,download_seconds=time.perf_counter()-start),indent=2))
if __name__=='__main__': main()
