"""Download pinned benchmark; no model outputs or topical searches are fetched."""
import hashlib,json,platform,time,os
from pathlib import Path
import requests,pandas as pd
ROOT=Path(__file__).resolve().parent
REPO='TIGER-Lab/MMLU-Pro'
REV='b189ec765aa7ed75c8acfea42df31fdae71f97be'
def main():
    meta=requests.get(f'https://huggingface.co/api/datasets/{REPO}/tree/{REV}?recursive=true',timeout=60);meta.raise_for_status()
    (ROOT/'dataset_tree.json').write_text(meta.text)
    manifest={'repository':REPO,'revision':REV,'files':[]}
    for ent in meta.json():
        name=ent['path']
        if name.endswith('.parquet'):
            url=f'https://huggingface.co/datasets/{REPO}/resolve/{REV}/{name}'
            dst=ROOT/('mmlu_'+Path(name).name)
            if not dst.exists():
                r=requests.get(url,timeout=120);r.raise_for_status();dst.write_bytes(r.content)
            manifest['files'].append({'source_path':name,'local_path':dst.name,'url':url,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'rows':len(pd.read_parquet(dst))})
    (ROOT/'data_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
