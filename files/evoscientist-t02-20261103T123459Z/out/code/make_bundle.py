"""Package the completed artifact; exclude runtime internals and environments."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SUFFIXES={'.py','.sh','.tex','.bib','.sty','.bst','.json','.md','.txt','.log','.pdf','.aux','.bbl','.blg','.fls','.fdb_latexmk','.out'}
EXCLUDE={'artifact_manifest.json','bundle_info.json'}
DIRS=['analysis','figures','results','source_history','template','literature']


def main():
    files=[p for p in ROOT.iterdir() if p.is_file() and not p.name.startswith('.') and p.suffix in SUFFIXES and p.name not in EXCLUDE]
    for dirname in DIRS:
        files.extend(p for p in (ROOT/dirname).rglob('*') if p.is_file() and not any(x.startswith('.') or x=='__pycache__' for x in p.relative_to(ROOT).parts))
    files=sorted(set(files))
    manifest={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files}
    (ROOT/'artifact_manifest.json').write_text(json.dumps(dict(schema=1,files=manifest),indent=2))
    archive=ROOT/'grokking_study.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files+[ROOT/'artifact_manifest.json']:z.write(p,p.relative_to(ROOT))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    sha=hashlib.sha256(archive.read_bytes()).hexdigest()
    info=dict(archive=archive.name,archive_bytes=archive.stat().st_size,sha256=sha,
              files=len(files)+1,uncompressed_bytes=sum(p.stat().st_size for p in files),
              zip_crc_verified=True,excluded='hidden runtime folders, environments, caches, archive self-reference')
    (ROOT/'bundle_info.json').write_text(json.dumps(info,indent=2))
    (ROOT/'grokking_study.zip.sha256').write_text(sha+'  grokking_study.zip\n')
    print(json.dumps(info,indent=2))

if __name__=='__main__':main()
