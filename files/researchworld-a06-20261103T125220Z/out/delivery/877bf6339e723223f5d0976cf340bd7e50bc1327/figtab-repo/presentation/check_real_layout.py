#!/usr/bin/env python3
"""Optional PDF/font/layout inspection aid; never substitutes for visual review."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import pymupdf
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--style-directory',type=Path,default=ROOT/'venue/official/iclr2027')
p.add_argument('--output-directory',type=Path,required=True)
a=p.parse_args();out=a.output_directory.resolve();out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ);env['TEXINPUTS']=str(a.style_directory.resolve())+os.pathsep+env.get('TEXINPUTS','')
r=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(out),str(ROOT/'presentation/real-layout-check.tex')],cwd=ROOT,env=env,capture_output=True,text=True)
(out/'build.txt').write_text(r.stdout+r.stderr)
assert r.returncode==0,r.stdout[-3000:]
assert 'Overfull' not in r.stdout
records=[];tiles=[]
paths=sorted((ROOT/'figures').glob('real-*.pdf'))+sorted((ROOT/'tables').glob('real-*-preview.pdf'))
assert len(paths)==11
for path in paths:
    doc=pymupdf.open(path);assert len(doc)==1
    page=doc[0];spans=[s for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
    size=min(s['size'] for s in spans)
    bad=[s['text'] for s in spans if s['bbox'][0]<-.6 or s['bbox'][1]<-.6 or s['bbox'][2]>page.rect.width+.6 or s['bbox'][3]>page.rect.height+.6]
    assert not bad,(str(path),bad)
    assert size>=7.9,(str(path),size)
    if path.parent.name=='figures':assert page.rect.width==396
    assert all(len(doc.extract_font(f[0])[-1])>0 for f in page.get_fonts())
    records.append({'path':str(path.relative_to(ROOT)),'width_pdf_points':page.rect.width,'minimum_text_points':size,'embedded_fonts':True,'text_within_page':True})
    pix=page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4),alpha=False);pix.save(out/(path.stem+'.png'))
    im=Image.open(out/(path.stem+'.png'));im.thumbnail((600,650));tile=Image.new('RGB',(620,680),'#eeeeee');tile.paste(im,((620-im.width)//2,25));ImageDraw.Draw(tile).text((5,5),path.name,fill='black');tiles.append(tile)
contact=Image.new('RGB',(1240,680*((len(tiles)+1)//2)),'white')
for i,t in enumerate(tiles):contact.paste(t,((i%2)*620,(i//2)*680))
contact.save(out/'pdf-exports-contact.png')
layout=pymupdf.open(out/'real-layout-check.pdf');assert len(layout)==8
pages=[]
for i,page in enumerate(layout):
    pix=page.get_pixmap(matrix=pymupdf.Matrix(1,1),alpha=False);im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
    tile=Image.new('RGB',(632,812),'#eeeeee');tile.paste(im,((632-im.width)//2,10));ImageDraw.Draw(tile).text((5,795),f'Official style diagnostic page {i+1}',fill='black');pages.append(tile)
contact=Image.new('RGB',(1264,812*4),'white')
for i,t in enumerate(pages):contact.paste(t,((i%2)*632,(i//2)*812))
contact.save(out/'official-layout-contact.png')
record={'analysis_source_revision':json.loads((ROOT/'presentation/real-provenance.json').read_text())['source_revision'],'artwork':records,'official_style_diagnostic_pages':len(layout),'official_style_overfull_boxes':False,'visual_inspection':'See real-acceptance.md for manual inspection; this script checks geometry/fonts, not scientific validity.'}
(ROOT/'presentation/real-render-check.json').write_text(json.dumps(record,indent=2)+'\n')
print('Checked eleven PDF exports and eight-page official-style layout; no clipped text, small type or overfull boxes.')
