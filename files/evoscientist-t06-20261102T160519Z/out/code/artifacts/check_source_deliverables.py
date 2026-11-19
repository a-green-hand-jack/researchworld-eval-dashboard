from pathlib import Path
import hashlib, json, re, zipfile
from pypdf import PdfReader
root=Path('/work')
t=root/'paper/template'
s=root/'artifacts/sources'
files=sorted(s.glob('*.pdf'))+[t/'Formatting_Instructions_For_NeurIPS_2026.zip',t/'neurips_2026.tex',t/'neurips_2026.sty',t/'checklist.tex']
rows=['| Local file | SHA-256 |','|---|---|']
for f in files:
    rows.append('| '+str(f.relative_to(root))+' | '+hashlib.sha256(f.read_bytes()).hexdigest()+' |')
for f in [root/'artifacts/literature_notes.md',t/'PROVENANCE.md']:
    txt=f.read_text()
    marker='| Local file | SHA-256 |'
    assert txt.count(marker)==1
    f.write_text(txt[:txt.index(marker)]+'\n'.join(rows)+'\n')
    assert all(hashlib.sha256(x.read_bytes()).hexdigest() in f.read_text() for x in files)
versions={}
for f in sorted(s.glob('*.pdf')):
    p1=PdfReader(f).pages[0].extract_text()
    versions[f.stem]=re.findall(r'arXiv:\s*([0-9.]+v\d+)',p1)
print('Downloaded PDF version markers:',json.dumps(versions))
assert versions=={'2011.14999':['2011.14999v5'],'2306.05685':['2306.05685v4'],'2403.04132':['2403.04132v1'],'2501.17858':['2501.17858v2'],'2508.11847v1':['2508.11847v1']}
z=zipfile.ZipFile(t/'Formatting_Instructions_For_NeurIPS_2026.zip')
assert set(z.namelist())=={'neurips_2026.tex','neurips_2026.sty','checklist.tex'}
assert all((t/n).read_bytes()==z.read(n) for n in z.namelist())
bib=(root/'paper/references.bib').read_text()
assert len(re.findall(r'@misc\{',bib))==5
assert bib.count('{')==bib.count('}')
assert set(re.findall(r'eprint\s*=\s*\{([^}]+)\}',bib))=={v[0] for v in versions.values()}
print('Verified all hashes, version pins, five BibTeX eprints, and pristine template/checklist extraction.')
