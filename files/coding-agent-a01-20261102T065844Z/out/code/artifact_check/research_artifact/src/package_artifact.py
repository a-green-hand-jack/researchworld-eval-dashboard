"""Create a self-contained deliverable, excluding the environment and TeX caches."""
from pathlib import Path
import hashlib
import tarfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    files=[]
    for dirname in ['src','tests','data','artifacts','paper','literature','logs']:
        for p in (ROOT/dirname).rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(ROOT)
            if '__pycache__' in rel.parts or '.pytest_cache' in rel.parts:continue
            if 'previews' in rel.parts:continue
            if rel.parts[0]=='paper' and len(rel.parts)==2 and p.suffix in {
                    '.aux','.log','.out','.fls','.fdb_latexmk','.blg','.synctex.gz'}:continue
            files.append(p)
    files += [ROOT/x for x in ['README.md','RESEARCH_LOG.md','Makefile','requirements-lock.txt']]
    files=sorted(set(files))
    lines=[hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(ROOT)) for p in files]
    (ROOT/'MANIFEST.sha256').write_text('\n'.join(lines)+'\n')
    target=ROOT/'research_artifact.tar.gz'
    with tarfile.open(target,'w:gz',compresslevel=6) as tar:
        for p in files+[ROOT/'MANIFEST.sha256']:
            tar.add(p,arcname='research_artifact/'+str(p.relative_to(ROOT)),recursive=False)
    sha=hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT/'research_artifact.tar.gz.sha256').write_text(sha+'  research_artifact.tar.gz\n')
    print(f'{len(files)} files; {target.stat().st_size:,} bytes; SHA-256 {sha}')

if __name__=='__main__':
    main()
