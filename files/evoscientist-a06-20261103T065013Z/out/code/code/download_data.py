"""Fetch the exact public benchmark revision, verifying content digests."""
import hashlib,json,pathlib,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
REV='b189ec765aa7ed75c8acfea42df31fdae71f97be'
def main():
    folder=ROOT/'data';folder.mkdir(exist_ok=True)
    u=f'https://huggingface.co/api/datasets/TIGER-Lab/MMLU-Pro/tree/{REV}?recursive=true'
    tree=json.load(urllib.request.urlopen(u,timeout=60));(folder/'tree.json').write_text(json.dumps(tree,indent=2))
    log=[]
    for r in tree:
      if r['path'].endswith('.parquet'):
        url=f'https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/resolve/{REV}/'+r['path'];p=folder/pathlib.Path(r['path']).name
        if not p.exists():p.write_bytes(urllib.request.urlopen(url,timeout=120).read())
        sha=hashlib.sha256(p.read_bytes()).hexdigest();expected=r.get('lfs',{}).get('oid')
        assert expected is None or sha==expected,(p,sha,expected)
        log.append({'file':str(p.relative_to(ROOT)),'url':url,'sha256':sha,'bytes':p.stat().st_size})
    # Dataset card records licensing and schema; never use solution fields in requests.
    card=f'https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/resolve/{REV}/README.md'
    p=folder/'DATASET_CARD.md'
    if not p.exists():p.write_bytes(urllib.request.urlopen(card,timeout=60).read())
    (folder/'download_manifest.json').write_text(json.dumps(log,indent=2));print(json.dumps(log,indent=2))
if __name__=='__main__':main()
