"""Create a portable paper+code+evidence archive; omit duplicate clean tree/web downloads."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parent
NAME='composition_conformal_research.zip'

def main():
    dirs={'artifacts','figures','template','preregistration'}
    excluded={'delivery_manifest.json','packaging.log',NAME,NAME+'.sha256'}
    paths=[]
    for p in ROOT.iterdir():
        if p.is_file() and p.name not in excluded and p.suffix in {'.py','.md','.json','.tex','.bib','.pdf','.txt','.log','.aux','.bbl','.blg','.out'}:
            paths.append(p)
        if p.is_dir() and p.name in dirs:
            paths.extend(q for q in p.rglob('*') if q.is_file() and '__pycache__' not in q.parts)
    paths=sorted(set(paths))
    manifest={'archive':NAME,'purpose':'Complete paper, source code, original results, fresh replay evidence, and offline reproducibility materials.','excluded_from_archive':['duplicate clean_reproduction tree (remains in workspace; numeric equivalence checked)','raw public web downloads in sources (URLs/read scope retained)','tool backend and background-process internals','Python bytecode caches'],
              'file_count_without_manifest':len(paths),'uncompressed_bytes_without_manifest':sum(p.stat().st_size for p in paths),
              'files':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths}}
    assert manifest['uncompressed_bytes_without_manifest']<10_000_000_000
    m=ROOT/'delivery_manifest.json'; m.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    with zipfile.ZipFile(ROOT/NAME,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths+[m]: z.write(p,str(p.relative_to(ROOT)))
    with zipfile.ZipFile(ROOT/NAME) as z:
        assert z.testzip() is None
        required=['paper.pdf','paper.tex','README.md','reproduce.py','artifacts/main/metrics.csv','artifacts/analysis/contrasts.csv']
        for n in required: assert n in z.namelist()
    sha=hashlib.sha256((ROOT/NAME).read_bytes()).hexdigest()
    (ROOT/(NAME+'.sha256')).write_text(sha+'  '+NAME+'\n')
    print(json.dumps({'archive':NAME,'file_count_including_manifest':len(paths)+1,'uncompressed_bytes':sum(p.stat().st_size for p in paths+[m]),'archive_bytes':(ROOT/NAME).stat().st_size,'sha256':sha,'zip_integrity':'PASS'},indent=2))

if __name__=='__main__': main()
