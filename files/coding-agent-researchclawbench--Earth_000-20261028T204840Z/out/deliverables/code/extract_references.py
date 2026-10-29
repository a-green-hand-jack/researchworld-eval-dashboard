"""Extract supplied PDFs and the downloaded GlaMBIE article for traceable reading."""
from pathlib import Path
from html.parser import HTMLParser
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/literature'; OUT.mkdir(parents=True,exist_ok=True)
for p in sorted((ROOT/'related_work').glob('*.pdf')):
 target=OUT/(p.stem+'.txt')
 if not target.exists(): target.write_text('\n\n'.join(x.extract_text() for x in PdfReader(p).pages))
class Extract(HTMLParser):
 def __init__(self): super().__init__(); self.parts=[]; self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'): self.skip+=1
  if tag in ('p','h1','h2','h3','h4','li','tr'): self.parts.append('\n')
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.skip=max(0,self.skip-1)
  if tag in ('p','h1','h2','h3','h4','li','tr'): self.parts.append('\n')
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
p=OUT/'glambie_nature.html'
if p.exists():
 h=Extract();h.feed(p.read_text());(OUT/'glambie_nature.txt').write_text('\n'.join(s.strip() for s in ''.join(h.parts).splitlines() if s.strip()))
