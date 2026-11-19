import subprocess,json,hashlib
from pathlib import Path
repo='/hutian/paper-repo'
Path('artifacts/integration-check').mkdir(parents=True,exist_ok=True)
rev='8aa79e935dae75d9fdcc3be7b9f290d9c16692a1'
ls=subprocess.check_output(['git','-C',repo,'ls-tree','-r','--name-only',rev],text=True).splitlines(); paths=set(ls)
def blob(p):return subprocess.check_output(['git','-C',repo,'show',f'{rev}:{p}'])
own=[]; mismatch=[]
for p in ls:
 if not p.startswith(('analysis/','results/')):continue
 local=Path(p.removeprefix('analysis/'))
 if not local.is_file():continue
 same=hashlib.sha256(local.read_bytes()).digest()==hashlib.sha256(blob(p)).digest()
 (own if same else mismatch).append(p)
checks=[];missing=[]
def walk(v,manifest):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and 'sha256' in v:
   p=v['path']
   if p in paths:checks.append(dict(manifest=manifest,path=p,match=hashlib.sha256(blob(p)).hexdigest()==v['sha256']))
   else:missing.append(dict(manifest=manifest,path=p))
  for x in v.values():walk(x,manifest)
 elif isinstance(v,list):
  for x in v:walk(x,manifest)
for p in ls:
 if p.startswith(('figures/','tables/')) and p.endswith('.manifest.json'):walk(json.loads(blob(p)),p)
report=dict(paper_revision=rev,owned_matching_files=len(own),owned_different_files=mismatch,display_hash_records=len(checks),display_hash_mismatches=[x for x in checks if not x['match']],display_unresolved_paths=missing)
Path('artifacts/integration-check/hash_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
for p in ['main.pdf','figures/one_run_budget.pdf','figures/criterion_instance_contrast.pdf','figures/background_sensitivity_acs.pdf','figures/error_repeatability.pdf']:
 Path('artifacts/integration-check/'+Path(p).name).write_bytes(blob(p))
