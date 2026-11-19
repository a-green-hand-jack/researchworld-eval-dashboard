"""Create a portable, checksummed source/results archive, excluding environments."""
from pathlib import Path
import hashlib,zipfile

ROOT=Path(__file__).resolve().parents[1]
files=[]
for p in ROOT.iterdir():
    if p.is_file() and p.suffix in ['.md','.txt','.json','.sh','.pdf']:
        if p.name!='MANIFEST.sha256':files.append(p)
for folder in ['src','results','figures','vendor','logs']:
    for p in (ROOT/folder).rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.pyc','.png']:
            continue
        files.append(p)
for p in (ROOT/'paper').rglob('*'):
    if p.is_file() and p.suffix in ['.tex','.bib','.sty','.pdf','.bbl']:
        files.append(p)
for name in ['READING_NOTES.md','provenance.json']:
    files.append(ROOT/'literature'/name)
files.append(ROOT/'LICENSE')
files=sorted(set(files),key=lambda p:str(p.relative_to(ROOT)))
manifest=ROOT/'MANIFEST.sha256'
manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+
                           str(p.relative_to(ROOT))+'\n' for p in files))
files.append(manifest)
archive=ROOT/'research_deliverables.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:z.write(p,p.relative_to(ROOT))
print(f'{archive}: {archive.stat().st_size} bytes; {len(files)} files')
