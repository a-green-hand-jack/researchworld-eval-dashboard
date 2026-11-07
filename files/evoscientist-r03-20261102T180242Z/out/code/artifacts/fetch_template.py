import urllib.request, pathlib, zipfile, io, hashlib, json, re
from html.parser import HTMLParser
ROOT=pathlib.Path('/work/artifacts/sources'); PAPER=pathlib.Path('/work/paper')
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**kw): return None
opener=urllib.request.build_opener(NoRedirect)
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,t,a):
        if t in ['script','style']:self.skip+=1
        if t in ['p','div','h1','h2','h3','li','br']:self.parts.append('\n')
    def handle_endtag(self,t):
        if t in ['script','style']:self.skip-=1
    def handle_data(self,d):
        if not self.skip:self.parts.append(d)
url='https://icml.cc/Conferences/2026/CallForPapers'
with opener.open(url,timeout=60) as r:data=r.read().decode(); print('CFP',r.status)
(ROOT/'icml2026_call_for_papers.html').write_text(data)
p=Text();p.feed(data);(ROOT/'icml2026_call_for_papers.txt').write_text('\n'.join(x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
url='https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip'
with opener.open(url,timeout=60) as r:data=r.read();print('ZIP',r.status,len(data))
(PAPER/'icml2026.zip').write_bytes(data)
manifest={'source_url':url,'archive_sha256':hashlib.sha256(data).hexdigest(),'members':[]}
z=zipfile.ZipFile(io.BytesIO(data))
for member in z.infolist():
    path=pathlib.PurePosixPath(member.filename)
    if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe zip path')
    if member.is_dir():continue
    payload=z.read(member);dest=PAPER.joinpath(*path.parts);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(payload)
    manifest['members'].append({'path':str(dest),'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()})
    print(member.filename,len(payload))
(PAPER/'template_manifest.json').write_text(json.dumps(manifest,indent=2))
