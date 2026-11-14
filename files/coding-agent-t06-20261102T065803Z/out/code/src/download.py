"""Download only explicitly supplied data snapshots; verify every raw file."""
import hashlib,json,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MT='https://huggingface.co/datasets/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/'
FILES={
 'arena.csv':('https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv','0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2','Apache-2.0'),
 'mt_human.parquet':(MT+'data/human-00000-of-00001-25f4910818759289.parquet','4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769','CC-BY-4.0'),
 'mt_gpt4.parquet':(MT+'data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet','57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71','CC-BY-4.0'),
 'nba.csv':('https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv','d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc','CC-BY-4.0'),
}

def main():
    out=ROOT/'data/raw';out.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for name,(url,expected,license_) in FILES.items():
        path=out/name
        if not path.exists(): urllib.request.urlretrieve(url,path)
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=expected: raise ValueError(f'Checksum mismatch: {name}')
        manifest.append(dict(file=name,url=url,sha256=actual,bytes=path.stat().st_size,license=license_))
        print(name,actual,flush=True)
    (ROOT/'data/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__': main()
