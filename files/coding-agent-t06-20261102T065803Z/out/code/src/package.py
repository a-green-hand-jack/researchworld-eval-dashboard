"""Create a reviewable submission without raw data, env, or downloaded papers."""
from pathlib import Path
import hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    paths=[]
    for name in ['README.md','Makefile','requirements.txt','LICENSE','THIRD_PARTY.md','.gitignore','deliverable.md']:
        paths.append(ROOT/name)
    for name in ['src','results']:
        paths += [p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += list((ROOT/'paper').glob('*.tex'))+list((ROOT/'paper').glob('*.sty'))+list((ROOT/'paper').glob('*.bib'))
    paths += [ROOT/'paper/main.pdf']
    for name in ['figures','tables','vendor']:
        paths += [p for p in (ROOT/'paper'/name).rglob('*') if p.is_file()]
    paths += [p for p in (ROOT/'data').glob('*') if p.is_file()]
    paths += [p for p in (ROOT/'logs').glob('*') if p.suffix in ['.md','.json'] or p.name in [
        'experiment.log','winner.log','verification.log','audit.log','pdf_check.log',
        'report.log','hardware.txt','latex_version.txt','download.log']]
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
    with zipfile.ZipFile(ROOT/'submission.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(paths)):z.write(p,str(p.relative_to(ROOT)))
        z.writestr('MANIFEST_SHA256.json',json.dumps(manifest,indent=2)+'\n')
    print(f'Wrote submission.zip: {len(manifest)} files, {(ROOT/"submission.zip").stat().st_size:,} bytes')

if __name__=='__main__':main()
