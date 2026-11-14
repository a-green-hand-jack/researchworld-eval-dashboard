"""Build and verify a compact, self-contained code/results/paper archive."""
import hashlib,json,pathlib,tarfile,time
ROOT=pathlib.Path(__file__).resolve().parents[1]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    files=[]
    for name in ['README.md','LICENSE','PROTOCOL.md','PROTOCOL_AMENDMENTS.md','requirements-lock.txt','paper.pdf']:
        files.append(ROOT/name)
    for directory in ['src','paper','data','results','logs','refs']:
        for p in (ROOT/directory).rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(ROOT)
            if '__pycache__' in p.parts or 'engineering_tests' in p.parts:continue
            if directory=='src' and p.suffix not in ['.py','.sh']:continue
            if directory=='paper' and p.suffix not in ['.tex','.bib','.sty','.bst','.pdf','.png','.json']:continue
            if directory=='data' and p.suffix=='.gguf':continue
            if directory=='refs' and p.suffix in ['.pdf','.txt']:continue
            if rel.as_posix() in ['logs/package.json','logs/package_build.log']:continue
            if directory=='logs' and p.suffix=='.png':continue
            files.append(p)
    files.append(ROOT/'vendor/icml2026.zip')
    files=sorted(set(files))
    entries=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    manifest=ROOT/'ARTIFACT_MANIFEST.json'
    manifest.write_text(json.dumps(dict(files=entries,excluded='Model weights, virtual environment, backend checkout/build, downloaded literature PDFs; pinned retrieval instructions are supplied.'),indent=2)+'\n')
    entries_for_check=entries+[dict(path=manifest.name,sha256=sha(manifest))]
    sums=ROOT/'CHECKSUMS.sha256'
    sums.write_text('\n'.join(x['sha256']+'  '+x['path'] for x in entries_for_check)+'\n')
    archive=ROOT/'research_artifact.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=6) as tar:
        for p in files+[manifest,sums]:tar.add(p,arcname='research_artifact/'+p.relative_to(ROOT).as_posix(),recursive=False)
    with tarfile.open(archive,'r:gz') as tar:
        names={m.name for m in tar.getmembers()}
        assert len(names)==len(files)+2
        for entry in entries_for_check:
            stream=tar.extractfile('research_artifact/'+entry['path']);h=hashlib.sha256()
            for b in iter(lambda:stream.read(1024*1024),b''):h.update(b)
            assert h.hexdigest()==entry['sha256'],entry['path']
    info=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=sha(archive),
              archived_files=len(files)+2,all_member_checksums_verified=True,created_unix=time.time())
    (ROOT/'logs/package.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))

if __name__=='__main__':main()
