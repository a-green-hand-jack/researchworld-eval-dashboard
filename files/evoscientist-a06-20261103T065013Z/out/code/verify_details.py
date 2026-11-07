import sys,json,pathlib,urllib.request,datetime,hashlib
from html.parser import HTMLParser
sys.path.insert(0,'/work');from retrieve import fetch
root=pathlib.Path('/work')
class Text(HTMLParser):
 def __init__(self):super().__init__();self.skip=0;self.text=[];self.links=[]
 def handle_starttag(self,t,a):
  if t in ['script','style']:self.skip+=1
  if t=='a':self.links.append(dict(a).get('href',''))
 def handle_endtag(self,t):
  if t in ['script','style']:self.skip=max(0,self.skip-1)
 def handle_data(self,d):
  if not self.skip and d.strip():self.text.append(d.strip())
for name in ['iclr2027_call','iclr2026_call','iclr2026_authors']:
 p=Text();p.feed((root/'official'/f'{name}.html').read_text());(root/'official'/f'{name}.txt').write_text('\n'.join(p.text));(root/'official'/f'{name}_links.json').write_text(json.dumps(p.links,indent=2))
records=json.loads((root/'official_retrieval.json').read_text())
for url,name in [
 ('https://api.github.com/repos/ICLR/Master-Template/commits/master','template_commit.json'),
 ('https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027?ref=master','iclr2027_contents.json')]:
 r=fetch(url,root/'official'/name);records.append(r);print(json.dumps({k:v for k,v in r.items() if k not in ['metadata','abstract','history','headers']}))
(root/'official_retrieval.json').write_text(json.dumps(records,indent=2))
# Resolve the already-allowlisted DOI only, using DOI-native metadata negotiation.
url='https://doi.org/10.1214/12-AOS1077';rec={'requested_url':url,'accessed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'accept':'application/vnd.citationstyles.csl+json'}
try:
 req=urllib.request.Request(url,headers={'Accept':rec['accept'],'User-Agent':'SourceVerification/1.0'})
 with urllib.request.urlopen(req,timeout=45) as r:
  data=r.read();rec.update(status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'))
 path=root/'sources'/'12-AOS1077.negotiated';path.write_bytes(data);rec.update(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 print(json.dumps(rec));
 if 'json' in (rec['content_type'] or ''):print(data.decode())
except Exception as e:rec['error']=str(e);print(json.dumps(rec))
r=json.loads((root/'retrieval.json').read_text());r.append(rec);(root/'retrieval.json').write_text(json.dumps(r,indent=2))
