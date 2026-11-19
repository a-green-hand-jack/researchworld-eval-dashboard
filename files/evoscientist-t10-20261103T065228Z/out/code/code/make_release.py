"""Build a portable submission archive without redistributing source PDFs/data.
Raw measured result CSVs are included. Data reacquisition is via fetch_data.py.
"""
from pathlib import Path
import zipfile,hashlib,json
ROOT=Path(__file__).resolve().parents[1]


def main():
    files=[]
    for pattern in ['*.md','paper.pdf','paper.tex','references.bib','requirements*','icml2026.sty',
        'icml2026.bst','algorithm.sty','algorithmic.sty','fancyhdr.sty']:
        files.extend(ROOT.glob(pattern))
    for sub in ['code','tests','figures','math_audit']:
        files.extend(p for p in (ROOT/sub).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for sub in ['main','ablation','exact','tables']:
        files.extend(p for p in (ROOT/'artifacts'/sub).rglob('*') if p.is_file())
    files.extend(p for p in (ROOT/'artifacts').glob('*.json') if p.is_file())
    files.extend([ROOT/'artifacts'/'final_tests.log',ROOT/'artifacts'/'build_stdout.log',
                  ROOT/'template'/'icml2026.zip',ROOT/'template'/'source.txt'])
    for name in ['allowed_methods.md','scope_notes.md','access.tsv','pdf_versions.tsv']:
        files.append(ROOT/'literature'/name)
    files=sorted(set(p for p in files if p.is_file()))
    dest=ROOT/'submission.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,str(p.relative_to(ROOT)))
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None
    info={'file':dest.name,'bytes':dest.stat().st_size,'files':len(files),
          'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
          'excluded':'Original data and literature PDFs excluded; fetch data using supplied direct-ID script. Historical redundant replays excluded.'}
    (ROOT/'submission_manifest.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))

if __name__=='__main__':main()
