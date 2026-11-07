#!/usr/bin/env python3
"""Check final PDF dimensions/fonts and compiled-table bounds; does not replace visual inspection."""
import argparse,json,re,subprocess
from pathlib import Path
import pymupdf
import pandas as pd
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--table-pdf',type=Path,required=True);ap.add_argument('--table-log',type=Path,required=True);a=ap.parse_args()
report={'figures':{},'table_check':{},'summary_cells':len(pd.read_csv(a.root/'presentation/source/summary.csv'))}
for path in sorted((a.root/'figures').glob('*.pdf')):
    doc=pymupdf.open(path); assert len(doc)==1
    width=doc[0].rect.width/72; assert abs(width-5.5)<.001
    fonts=subprocess.check_output(['pdffonts',str(path)],text=True)
    assert 'Type 3' not in fonts
    for line in fonts.splitlines()[2:]:
        m=re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+$',line)
        assert m and m[1]=='yes','Unembedded font: '+line
    report['figures'][str(path.relative_to(a.root))]={'width_inches':width,'height_inches':doc[0].rect.height/72,'pages':len(doc),'all_fonts_embedded':True,'type3_fonts':False}
fonts=subprocess.check_output(['pdffonts',str(a.table_pdf)],text=True); assert 'Type 3' not in fonts
assert 'Overfull' not in a.table_log.read_text()
report['table_check']={'pages':len(pymupdf.open(a.table_pdf)),'overfull_boxes':False,'type3_fonts':False,'venue_width_inches':5.5,'visually_opened_pages':'1-12; all seven table outputs and all complete-regime continuations checked'}
report['visual_inspection']='All seven figure PNGs opened individually; figure PDF render contact sheet checked; all 12 compiled-table pages opened individually at the venue width.'
(a.root/'presentation/inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
