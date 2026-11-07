from html.parser import HTMLParser
from pathlib import Path
import json,re
R=Path('/work')
class Abs(HTMLParser):
    def __init__(self):
        super().__init__(); self.meta={}; self.level=0; self.abstract=[]; self.history=False; self.hist=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='meta' and a.get('name','').startswith('citation_'):
            self.meta.setdefault(a['name'],[]).append(a.get('content',''))
        if tag=='blockquote' and 'abstract' in a.get('class',''):
            self.level=1
        elif self.level: self.level+=1
        if tag=='div' and 'submission-history' in a.get('class',''): self.history=True
    def handle_endtag(self,tag):
        if self.level: self.level-=1
        if self.history and tag=='div': self.history=False
    def handle_data(self,d):
        if self.level: self.abstract.append(d)
        if self.history: self.hist.append(d)
meta={}
for aid in ['2406.01574','2310.03714','2406.11695','1411.2664','1502.04585','1212.6906']:
    p=Abs(); p.feed((R/f'literature_arxiv_{aid}_abs.html').read_text())
    meta[aid]=p.meta
    text=json.dumps(p.meta,indent=2,ensure_ascii=False)+'\n\nABSTRACT\n'+p.meta['citation_abstract'][0]+'\n\nSUBMISSION HISTORY (not citations)\n'+re.sub(r'\s+',' ',' '.join(p.hist)).strip()+'\n'
    (R/f'literature_arxiv_{aid}_abstract_metadata.txt').write_text(text)
    print(aid+'\n'+text)
(R/'literature_original_metadata.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
