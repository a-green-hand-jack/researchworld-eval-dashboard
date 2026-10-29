"""Download only the explicitly permitted frozen datasets; verify supplied hashes."""
import hashlib, json, pathlib, urllib.request, concurrent.futures
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/'data/raw'
SOURCES=[
 ('arena.csv','https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv','0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2'),
 ('nba.csv','https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv','d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc')]
def fetch(item):
 name,url,expected=item; p=DATA/name
 if not p.exists():
  with urllib.request.urlopen(url,timeout=180) as r, open(str(p)+'.part','wb') as f:
   while b:=r.read(1024*1024): f.write(b)
  pathlib.Path(str(p)+'.part').rename(p)
 sha=hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
 if expected and sha!=expected: raise ValueError((name,sha,expected))
 return dict(file=name,url=url,sha256=sha,bytes=p.stat().st_size)
def main():
 DATA.mkdir(parents=True,exist_ok=True)
 api='https://huggingface.co/api/datasets/lmsys/mt_bench_human_judgments/tree/f7d2896d2cc5d80f8b55c2bbc722613555233c25?recursive=true'
 entries=json.load(urllib.request.urlopen(api))
 items=list(SOURCES)
 for e in entries:
  if e['path'].endswith('.parquet'):
   typ='human' if 'human' in e['path'] else 'gpt4'
   url='https://huggingface.co/datasets/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/'+e['path']
   sha='4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769' if typ=='human' else None
   items.append((f'mt_{typ}.parquet',url,sha))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  results=list(ex.map(fetch,items))
 (ROOT/'data/manifest.json').write_text(json.dumps(results,indent=2)+'\n')
 print(json.dumps(results,indent=2))
if __name__=='__main__': main()
