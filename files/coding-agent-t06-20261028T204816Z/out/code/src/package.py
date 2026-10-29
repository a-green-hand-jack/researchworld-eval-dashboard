"""Create a source/results distribution with no raw/processed data or papers."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]

def main():
 files=[]
 for fn in ['README.md','LICENSE','requirements.txt','reproduce.sh','paper.pdf','.gitignore','DELIVERABLES.md']:
  files.append(ROOT/fn)
 for folder,extensions in [('src',{'.py'}),('notes',{'.md','.json','.html','.txt'}),('figures',{'.pdf','.png'}),('results',{'.csv','.json','.log','.npz'})]:
  files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in extensions)
 for fn in ['manifest.json','PROVENANCE.md']:files.append(ROOT/'data'/fn)
 files.extend(p for p in (ROOT/'paper').rglob('*') if p.is_file() and p.suffix in {'.tex','.bib','.bst','.sty','.zip'})
 files=sorted(p for p in set(files) if p.name!='package.log')
 manifest=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()) for p in files]
 (ROOT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
 files.append(ROOT/'MANIFEST.json')
 target=ROOT/'submission.zip'
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in files:z.write(p,str(p.relative_to(ROOT)))
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  assert not any(x.startswith(('data/raw/','data/processed/','.venv/','literature/')) for x in z.namelist())
  assert all(x in z.namelist() for x in ['paper.pdf','paper/main.tex','src/bt.py','README.md','reproduce.sh'])
 print(json.dumps(dict(archive=str(target),files=len(files),bytes=target.stat().st_size,sha256=hashlib.file_digest(open(target,'rb'),'sha256').hexdigest()),indent=2))
if __name__=='__main__':main()
