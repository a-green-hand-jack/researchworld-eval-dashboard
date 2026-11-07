#!/usr/bin/env python3
"""Record local TeX build assets and embedded font notices without network access."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'manuscript/provenance/build'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lines=(ROOT/'manuscript/.build/main.fls').read_text().splitlines()
    used=sorted({x[6:] for x in lines if x.startswith('INPUT ') and x.endswith('.pfb')})
    record={'scope':'Local recorded TeX font files/notices and build tools; no network or binaries redistributed','fonts':[], 'notices':[]}
    for path in used:
        data=Path(path).read_bytes()
        # PFB type1 segment header is followed by the ASCII font program.
        assert data[:2]==b'\x80\x01',path
        length=int.from_bytes(data[2:6],'little'); ascii_segment=data[6:6+length]
        # Preserve the initial comments, which contain the actual declared copyright/license.
        header=ascii_segment.split(b'%%EndComments',1)[0] if b'%%EndComments' in ascii_segment else ascii_segment.split(b'12 dict begin',1)[0]
        out=OUT/'font-notices'/(Path(path).stem+'.txt');out.parent.mkdir(exist_ok=True);out.write_bytes(header)
        record['fonts'].append({'installed_path':path,'file_sha256':sha(data),'bytes':len(data),'notice_path':str(out.relative_to(ROOT)),'notice_sha256':sha(header)})
    for path in ['/usr/share/doc/texlive-base/copyright','/usr/share/doc/texlive-fonts-recommended/copyright','/usr/share/common-licenses/GPL-2','/usr/share/common-licenses/GPL-3']:
        src=Path(path); name=src.parent.name+'-'+src.name if src.name=='copyright' else src.name
        dst=OUT/name;shutil.copyfile(src,dst);record['notices'].append({'installed_path':path,'saved_path':str(dst.relative_to(ROOT)),'sha256':sha(src.read_bytes())})
    record['versions']={cmd:subprocess.check_output(args,text=True).splitlines()[0] for cmd,args in [('pdfTeX',['pdflatex','--version']),('latexmk',['latexmk','--version']),('BibTeX',['bibtex','--version'])]}
    record['pdf_fonts']=subprocess.check_output(['pdffonts',str(ROOT/'paper.pdf')],text=True)
    (OUT/'installed-assets.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Captured',len(used),'actual TeX font files with original header notices.')
if __name__=='__main__':main()
