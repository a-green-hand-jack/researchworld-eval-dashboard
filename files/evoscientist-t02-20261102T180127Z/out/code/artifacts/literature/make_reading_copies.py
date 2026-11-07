import re
from pathlib import Path
from pypdf import PdfReader
root=Path('/work/artifacts/literature')
for pdf in sorted(root.glob('*.pdf')):
    reader=PdfReader(pdf)
    parts=[]
    bibliography=False
    omissions=[]
    for idx,page in enumerate(reader.pages):
        text=page.extract_text()
        lines=text.splitlines()
        safe=[]
        for line in lines:
            compact=re.sub(r'\s+','',line).lower()
            if compact in ('references','bibliography'):
                bibliography=True
                safe.append('[BIBLIOGRAPHY OMITTED: independence guard]')
                omissions.append(idx+1)
                continue
            # Appendix section heading, not bibliographic initials.
            if bibliography and (re.match(r'^A\. Experimental details',line) or re.match(r'^8\s+A\s+PPENDIX',line) or (pdf.stem == '2303.06173' and idx+1 >= 8 and re.match(r'^A\s+An alternative intuition',line)) or re.match(r'^(?:[A-Z]\s{1,3})?(?:APPENDIX|Appendix|SUPPLEMENTARY|Supplementary)\b',line) or re.match(r'^A\s+(?:[A-Z][A-Z\s]{3,}|Experimental|Additional|Details|Proof|Implementation|Hyperparameters|Experiment|Experiments|Training|Model|Further|Formal|Deferred|Grokking)',line)):
                bibliography=False
            if not bibliography:
                safe.append(line)
        if safe:
            parts.append(f'===== PAGE {idx+1} =====\n'+'\n'.join(safe))
    path=pdf.with_suffix('.reading.txt')
    path.write_text('\n\n'.join(parts))
    print(pdf.stem, 'pages',len(reader.pages),'bibliography_starts',omissions,'reading_lines',len(path.read_text().splitlines()),'still_omitting_at_end',bibliography)
