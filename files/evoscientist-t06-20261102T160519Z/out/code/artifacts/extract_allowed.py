from pathlib import Path
from pypdf import PdfReader
from html.parser import HTMLParser
import re, json

class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta' and a.get('name','').startswith('citation_'):
            self.meta.append(a)

p=Path('/work/artifacts/sources')
for f in sorted(p.glob('*.pdf')):
    aid=f.stem
    meta=Meta()
    meta.feed((p/(aid+'.html')).read_text())
    (p/(aid+'.metadata.json')).write_text(json.dumps(meta.meta,indent=2))
    print('METADATA',aid,json.dumps(meta.meta))
    reader=PdfReader(f)
    pages=[]
    for i,page in enumerate(reader.pages):
        text=page.extract_text()
        # Do not expose bibliography. Retain later appendix pages for selective reading.
        text=re.split(r'(?m)^\s*(?:References|REFERENCES)\s*$',text,maxsplit=1)[0]
        pages.append(f'\n=== PDF PAGE {i+1} ===\n'+text)
    (p/(aid+'.body.txt')).write_text('\n'.join(pages))
    print('PAGES',len(reader.pages),'TEXT LINES',sum(x.count('\n') for x in pages))
