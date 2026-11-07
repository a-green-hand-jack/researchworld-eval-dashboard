"""Build a portable deliverable without the environment or third-party data/papers."""
import hashlib,json,tarfile
from pathlib import Path
from study import ROOT

paths=[]
for name in ['README.md','SOURCE_ACCESS.md','RUN_LOG.md','EXPERIMENT_PLAN.md',
             'requirements-lock.txt','reproduce.sh','data/manifest.json','sources/format_provenance.json']:
    paths.append(ROOT/name)
paths+=sorted((ROOT/'code').glob('*.py'))
for pattern in ['*.tex','*.bib','*.bbl','*.sty','*.bst','*.pdf']:
    paths+=sorted((ROOT/'paper').glob(pattern))
paths+=sorted((ROOT/'paper/generated').glob('*.tex'))
paths+=sorted((ROOT/'figures').glob('*.pdf'))
paths+=sorted((ROOT/'figures').glob('*.png'))
paths+=sorted((ROOT/'results').glob('*'))
for pattern in ['*.json','*.log','*.txt']:
    paths+=sorted((ROOT/'logs').glob(pattern))
paths=sorted(set(p for p in paths if p.is_file()))
manifest={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths}
(ROOT/'ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
paths.append(ROOT/'ARTIFACT_MANIFEST.json')
with tarfile.open(ROOT/'deliverables.tar.gz','w:gz') as tar:
    for p in paths:tar.add(p,arcname='gate-research/'+str(p.relative_to(ROOT)),recursive=False)
print(f'Packaged {len(paths)} files, {(ROOT/"deliverables.tar.gz").stat().st_size:,} bytes')
