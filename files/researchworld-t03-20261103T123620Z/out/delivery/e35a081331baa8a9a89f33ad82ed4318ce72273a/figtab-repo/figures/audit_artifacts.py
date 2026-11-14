"""Verify delivered artifact/source hashes and physical PDF properties."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pymupdf
ROOT=Path(__file__).resolve().parents[1]

def check_record(rec):
    p=ROOT/rec['path']
    if len(p.read_bytes())!=rec['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=rec['sha256']:
        raise ValueError(f'Stale/missing artifact record: {p}')

def main():
    checked=[]
    for folder in ['figures','tables']:
        for path in sorted((ROOT/folder).glob('*.manifest.json')):
            if 'pilot' in path.name:continue
            m=json.loads(path.read_text())
            records=[]
            for k in ['inputs','outputs','supporting_code']:records.extend(m.get(k,[]))
            for k in ['generator','caption']:
                if k in m:records.append(m[k])
            for rec in records:check_record(rec)
            checked.append(path.relative_to(ROOT).as_posix())
    pdfs=[]
    for path in sorted((ROOT/'figures').glob('*.pdf')):
        if 'pilot' in path.name:continue
        doc=pymupdf.open(path)
        if len(doc)!=1 or abs(doc[0].rect.width-396)>.01:
            raise ValueError(f'Incorrect official-width output {path}')
        fonts=subprocess.check_output(['pdffonts',str(path)],text=True)
        if 'Type 3' in fonts:raise ValueError(f'Type 3 font in {path}')
        for row in fonts.splitlines()[2:]:
            if row and row.split()[-5]!='yes':raise ValueError(f'Unembedded font: {row}')
        # A text-bounds check supplements opening every output; this does not
        # replace visual checks for overlaps or incorrect visual encodings.
        for block in doc[0].get_text('dict')['blocks']:
            if block['type']!=0:continue
            for line in block['lines']:
                for span in line['spans']:
                    r=pymupdf.Rect(span['bbox'])
                    if not doc[0].rect.contains(r):raise ValueError(f'Text outside PDF in {path}: {span["text"]}')
        pdfs.append(path.name)
    print(json.dumps({'checked_main_manifests':len(checked),'one_page_5p5_inch_pdfs':len(pdfs),
        'hashes':'all matched','font_check':'embedded; no Type3',
        'pdf_text_bounds':'within page','visual_inspection':'recorded separately'},indent=2))

if __name__=='__main__':main()
