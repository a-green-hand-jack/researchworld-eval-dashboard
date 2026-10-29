"""Download only explicitly allowed data and the official required template."""
import urllib.request, pathlib, hashlib, json, concurrent.futures, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE='https://huggingface.co/datasets/'
FILES={
'arena.csv':(BASE+'lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv','0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2'),
'mt_human.parquet':(BASE+'lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data/human-00000-of-00001-25f4910818759289.parquet','4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769'),
'mt_gpt4.parquet':(BASE+'lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet','57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71'),
'nba.csv':('https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv','d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc')}
def get(item):
 name,(url,expected)=item;p=ROOT/'data/raw'/name;p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  for attempt in range(4):
   try:
    urllib.request.urlretrieve(url,str(p)+'.tmp');pathlib.Path(str(p)+'.tmp').replace(p);break
   except Exception:
    if attempt==3:raise
    time.sleep(2)
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 if sha!=expected:raise ValueError((name,sha,expected))
 print(name,p.stat().st_size,sha,flush=True)
 return {'file':name,'url':url,'sha256':sha,'bytes':p.stat().st_size}
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:out=list(pool.map(get,FILES.items()))
 (ROOT/'data/manifest.json').write_text(json.dumps(out,indent=2)+'\n')
