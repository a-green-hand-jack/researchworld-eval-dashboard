import os,importlib.util,sys
from html.parser import HTMLParser
from pathlib import Path
for base in ['/opt/venv/lib','/usr/local/lib/python3.11/site-packages','/usr/local/lib/python3.13/site-packages']:
 if os.path.isdir(base):
  print('LOCAL',base,[x for x in os.listdir(base) if any(k in x.lower() for k in ['pdf','fitz','python','pymu'])])
for p in Path('/opt/venv/lib').glob('python*/site-packages'):
 print('VENV',p,[x for x in os.listdir(p) if any(k in x.lower() for k in ['pdf','fitz','pymu'])])
class Text(HTMLParser):
 def __init__(self): super().__init__(); self.parts=[];self.skip=False
 def handle_starttag(self,tag,attrs):
  if tag in ['script','style']:self.skip=True
  if tag=='a':
   for k,v in attrs:
    if k=='href':self.parts.append(' [LINK '+v+'] ')
  if tag in ['p','h1','h2','h3','li','div','br']:self.parts.append('\n')
 def handle_endtag(self,tag):
  if tag in ['script','style']:self.skip=False
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
for p in Path('/work/paper/template').glob('*.html'):
 q=Text();q.feed(p.read_text());p.with_suffix('.txt').write_text(''.join(q.parts))
