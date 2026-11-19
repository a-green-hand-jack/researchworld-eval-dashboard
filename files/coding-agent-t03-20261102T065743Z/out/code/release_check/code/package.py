"""Create the lightweight reproducible source/results package; omit large payoff/raw ACS caches."""
from common import ROOT
from pathlib import Path
import zipfile,hashlib,json
paths=[]
for name in ['README.md','PROTOCOL.md','RESEARCH_LOG.md','LICENSE','Makefile','requirements.txt','environment.json']:
 paths.append(ROOT/name)
for dirname in ['code','paper','results','logs','literature','data']:
 for p in (ROOT/dirname).rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(ROOT);s=str(rel)
  if '__pycache__' in s or '/render/' in s:continue
  if dirname=='paper' and p.suffix in ['.aux','.bbl','.blg','.log','.out']:continue
  if dirname=='paper' and '/vendor/icml2026/' in s:continue
  if dirname=='results' and s.startswith('results/games/'):continue
  if dirname=='data' and s.startswith('data/raw/acs'):continue
  if dirname=='literature' and p.name not in ['manifest.json','icml2026_author.html','census_api_terms.html','census_policies.html','census_privacy.html','uci_german_metadata.txt','openml_diabetes_metadata.txt']:continue
  paths.append(p)
checks=[]
for p in sorted(set(paths)):
 checks.append({'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
manifest=ROOT/'ARTIFACT_MANIFEST.json';manifest.write_text(json.dumps(checks,indent=2))
with zipfile.ZipFile(ROOT/'source_and_paper.zip','w') as z:
 for p in sorted(set(paths)):
  z.write(p,str(p.relative_to(ROOT)),compress_type=zipfile.ZIP_STORED if p.suffix in ['.npz','.zip','.pdf'] else zipfile.ZIP_DEFLATED)
 z.write(manifest,'ARTIFACT_MANIFEST.json',compress_type=zipfile.ZIP_DEFLATED)
print('files',len(paths)+1,'zip bytes',(ROOT/'source_and_paper.zip').stat().st_size)
