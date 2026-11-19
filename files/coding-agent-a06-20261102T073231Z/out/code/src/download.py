"""Fetch only pinned, official data/model files; record hashes and access URLs."""
import argparse, hashlib, json, pathlib, requests
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILES=[
 ('https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/resolve/b189ec765aa7ed75c8acfea42df31fdae71f97be/data/test-00000-of-00001.parquet','data/test.parquet'),
 ('https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/9217f5db79a29953eb74d5343926648285ec7e67/qwen2.5-0.5b-instruct-q8_0.gguf','data/model.gguf'),
]
def main():
    p=argparse.ArgumentParser();p.add_argument('--data-only',action='store_true');a=p.parse_args()
    manifest=[]
    for url,name in FILES:
        if a.data_only and name.endswith('gguf'):continue
        target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            r=requests.get(url,stream=True,timeout=300);r.raise_for_status()
            temp=target.with_suffix(target.suffix+'.partial')
            with temp.open('wb') as f:
                for b in r.iter_content(1024*1024):f.write(b)
            temp.rename(target)
        h=hashlib.sha256()
        with target.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        manifest.append(dict(url=url,path=name,bytes=target.stat().st_size,sha256=h.hexdigest()))
    (ROOT/'logs/download_manifest.json').write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
