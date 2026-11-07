"""Hash final source, processed inputs and numerical evidence, excluding raw downloads."""
import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
files=[]
for folder in ['scripts','data','results','notes']:
 for p in sorted((ROOT/folder).rglob('*')):
  rel=p.relative_to(ROOT)
  if not p.is_file() or 'raw' in rel.parts or '__pycache__' in rel.parts or p.name=='manifest.json':continue
  files.append({'path':str(rel),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for name in ['README.md','requirements.txt','requirements.lock','.gitignore']:
 p=ROOT/name
 files.append({'path':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'results/manifest.json').write_text(json.dumps({'python':sys.version,'files':files},indent=2)+'\n')
print('Manifest records',len(files),'files')
