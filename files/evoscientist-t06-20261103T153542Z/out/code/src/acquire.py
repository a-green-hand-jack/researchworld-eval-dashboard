"""Download only fixed authorized datasets and the official NeurIPS 2026 kit."""
from pathlib import Path
import hashlib, json, requests, time
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data'; D.mkdir(exist_ok=True)
MAN=[]
def get(url,path,expected=None):
    path=Path(path)
    if not path.exists():
        r=requests.get(url,timeout=180);r.raise_for_status();path.write_bytes(r.content)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    if expected and sha!=expected: raise ValueError(f'hash mismatch {path}: {sha}')
    MAN.append(dict(url=url,path=str(path.relative_to(ROOT)),sha256=sha,bytes=path.stat().st_size))
    print(path.name,path.stat().st_size,sha,flush=True)
get('https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv',D/'arena.csv','0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2')
base='https://huggingface.co/api/datasets/lmsys/mt_bench_human_judgments/tree/f7d2896d2cc5d80f8b55c2bbc722613555233c25?recursive=true'
r=requests.get(base,timeout=90);r.raise_for_status(); meta=r.json();(D/'mt_manifest.json').write_text(json.dumps(meta,indent=2))
for x in meta:
    p=x['path']
    if p.endswith('.parquet'):
        name='mt_human.parquet' if 'human-' in p else 'mt_gpt4.parquet'
        get('https://huggingface.co/datasets/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/'+p,D/name,'4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769' if name=='mt_human.parquet' else None)
get('https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv',D/'nba.csv','d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc')
(ROOT/'data_manifest.json').write_text(json.dumps(MAN,indent=2))
# Exact official template endpoints only, no topical search.
for url in ['https://media.neurips.cc/Conferences/NeurIPS2026/Styles/neurips_2026.zip','https://media.neurips.cc/Conferences/NeurIPS2026/Styles/neurips_2026.sty']:
    try:
        r=requests.get(url,timeout=60)
        print('template',url,r.status_code,len(r.content),flush=True)
        if r.ok:
            target=ROOT/'paper'/url.rsplit('/',1)[-1];target.write_bytes(r.content)
            MAN.append(dict(url=url,path=str(target.relative_to(ROOT)),sha256=hashlib.sha256(r.content).hexdigest()))
    except Exception as e: print('template fail',str(e),flush=True)
(ROOT/'data_manifest.json').write_text(json.dumps(MAN,indent=2))
