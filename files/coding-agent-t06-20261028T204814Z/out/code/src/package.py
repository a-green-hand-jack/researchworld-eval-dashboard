"""Create a data-free submission bundle with a file-integrity manifest."""
from pathlib import Path
import tarfile,hashlib,json
R=Path(__file__).resolve().parents[1]
def main():
 fixed=['README.md','PLAIN_LANGUAGE_SUMMARY.md','RESEARCH_LOG.md','LICENSE','requirements.txt','requirements-lock.txt','run_all.sh','DATA_MANIFEST.json','TEMPLATE_MANIFEST.json','ENVIRONMENT.json','.gitignore']
 files=[R/f for f in fixed]
 files+=sorted((R/'src').glob('*.py'))
 files+=sorted((R/'results').glob('*.csv'))+sorted((R/'results').glob('*.json'))
 files+=sorted((R/'figures').glob('*.pdf'))
 files+=sorted((R/'paper').glob('*.tex'))+sorted((R/'paper').glob('*.bib'))+sorted((R/'paper').glob('*.sty'))+sorted((R/'paper').glob('*.bst'))
 files+=[R/'paper/paper.pdf',R/'paper/paper.bbl']+sorted((R/'paper/generated').glob('*.tex'))
 # Include the actual main/supplement/verification stdout as small audited text files.
 for name in ['experiment_initial.log','experiment.log','matched.log','supplement.log','verification.log','tests.log','pdf-audit.log','end_to_end.log']:
  p=R/'logs'/name
  if p.exists():files.append(p)
 files=sorted(set(files))
 assert all(p.exists() for p in files)
 hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 (R/'SUBMISSION_MANIFEST.json').write_text(json.dumps(hashes,indent=2)+'\n')
 files.append(R/'SUBMISSION_MANIFEST.json')
 with tarfile.open(R/'submission.tar.gz','w:gz') as out:
  for p in files:out.add(p,arcname='leaderboard_stability/'+str(p.relative_to(R)),recursive=False)
 with tarfile.open(R/'submission.tar.gz') as archive:
  names=archive.getnames();assert not any('/data/' in n or '/literature/' in n or '/.venv/' in n or 'conversation' in n for n in names)
 print(json.dumps({'archive':'submission.tar.gz','files':len(files),'bytes':(R/'submission.tar.gz').stat().st_size,'raw_data_included':False},indent=2))
if __name__=='__main__':main()
