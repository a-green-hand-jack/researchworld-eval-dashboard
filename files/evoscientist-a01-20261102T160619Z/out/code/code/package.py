#!/usr/bin/env python3
"""Create a deterministic local reviewer bundle; exclude raw third-party data/text."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]

def main():
    files=[]
    for name in ['README.md','LICENSE','requirements.txt','TASK.md','research_request.md','todos.md','theory.md','experiment_log.md','final_report.md','paper.tex','paper.pdf','icml2026.sty','fancyhdr.sty']:
        files.append(ROOT/name)
    for directory,extensions in [('code',{'.py'}),('tests',{'.py'}),('paper',{'.tex','.bib','.sty','.bst'})]:
        files += [p for p in (ROOT/directory).rglob('*') if p.is_file() and p.suffix in extensions and '__pycache__' not in p.parts]
    files += [ROOT/'data/manifest.json',ROOT/'data/reference_manifest.json']
    for name in ['literature_notes.md','access_log.md','references.bib','helm_listing.json','contents_meta.json','icml2026.zip','icml2026_page.html','template_latest_check.json']:
        files.append(ROOT/'sources'/name)
    files += [p for p in (ROOT/'artifacts').rglob('*') if p.is_file() and not any(x.startswith('reproduce_') for x in p.relative_to(ROOT/'artifacts').parts) and p.suffix not in ['.pyc'] and '__pycache__' not in p.parts]
    files=sorted(set(files));assert all(p.is_file() for p in files)
    manifest={'scope':'local reviewer bundle, not a public archival release; raw data and third-party full-text caches excluded, run download.py first','files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    (ROOT/'artifact_manifest.json').write_text(json.dumps(manifest,indent=2));files.append(ROOT/'artifact_manifest.json')
    with zipfile.ZipFile(ROOT/'submission.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:
            info=zipfile.ZipInfo(str(p.relative_to(ROOT)),date_time=(2026,11,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,p.read_bytes())
    b=(ROOT/'submission.zip').read_bytes();digest=hashlib.sha256(b).hexdigest();(ROOT/'submission.zip.sha256').write_text(digest+'  submission.zip\n');print('Bundle files',len(files),'bytes',len(b),'sha256',digest)
if __name__=='__main__':main()
