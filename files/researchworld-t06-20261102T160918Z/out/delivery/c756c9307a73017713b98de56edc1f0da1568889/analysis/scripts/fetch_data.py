"""Download only the frozen public inputs; raw files are never committed."""
import hashlib,json,pathlib,urllib.request,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILES=[
('arena55.csv','https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv','0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2','apache-2.0'),
('mt_human.parquet','https://huggingface.co/datasets/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data/human-00000-of-00001-25f4910818759289.parquet','4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769','cc-by-4.0'),
('mt_gpt4.parquet','https://huggingface.co/datasets/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet',None,'cc-by-4.0'),
('nba.csv','https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv','d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc','cc-by-4.0')]
def main():
 (ROOT/'data/raw').mkdir(parents=True,exist_ok=True)
 manifest=[]
 for name,url,expected,license_ in FILES:
  p=ROOT/'data/raw'/name;t=time.perf_counter()
  if not p.exists():
   with urllib.request.urlopen(url,timeout=120) as src,p.open('wb') as dst:
    while chunk:=src.read(1024*1024):dst.write(chunk)
  sha=hashlib.sha256(p.read_bytes()).hexdigest()
  if expected and sha!=expected:raise ValueError((name,sha,expected))
  manifest.append(dict(file='data/raw/'+name,url=url,sha256=sha,bytes=p.stat().st_size,license=license_))
  print(name,p.stat().st_size,sha,'seconds',round(time.perf_counter()-t,2),flush=True)
 (ROOT/'results/provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
