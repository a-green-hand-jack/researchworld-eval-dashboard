from pathlib import Path
from html.parser import HTMLParser
import urllib.request, urllib.parse, json, datetime

ROOT=Path('/work/paper/template')
ROOT.mkdir(parents=True,exist_ok=True)
LOG=ROOT/'access_template.json'
class OfficialOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        host=urllib.parse.urlsplit(newurl).hostname or ''
        if not (host=='neurips.cc' or host.endswith('.neurips.cc')):
            raise ValueError('Blocked non-official redirect: '+newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)
class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out=[]; self.links=[]; self.a=None; self.label=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ['script','style']: self.skip+=1
        if tag=='a': self.a=a.get('href',''); self.label=[]
        if tag in ['p','div','h1','h2','h3','li','br']: self.out.append('\n')
    def handle_endtag(self,tag):
        if tag in ['script','style']: self.skip=max(0,self.skip-1)
        if tag=='a' and self.a is not None:
            self.links.append((''.join(self.label).strip(),self.a)); self.a=None
    def handle_data(self,s):
        if not self.skip:
            self.out.append(s)
            if self.a is not None: self.label.append(s)
def fetch(url,name):
    log=json.loads(LOG.read_text()) if LOG.exists() else []
    e={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':url}
    try:
        r=urllib.request.build_opener(OfficialOnly()).open(url,timeout=45)
        data=r.read(); dest=ROOT/name; dest.write_bytes(data)
        e.update(status=r.status,final_url=r.url,bytes=len(data),file=str(dest))
        if 'html' in r.headers.get('Content-Type',''):
            t=Text(); t.feed(data.decode()); (ROOT/(name+'.txt')).write_text(''.join(t.out)); (ROOT/(name+'.links.json')).write_text(json.dumps(t.links,indent=2))
            # Only show resource-related links; never accepted-paper listings.
            print('RELEVANT LINKS',[(a,b) for a,b in t.links if any(k in (a+' '+b).lower() for k in ['style','template','checklist','paper formatting','call for papers','author guide'])])
    except Exception as ex:
        e['error']=str(ex)
    log.append(e); LOG.write_text(json.dumps(log,indent=2)); print(json.dumps(e))
if __name__=='__main__':
    import sys
    fetch(sys.argv[1],sys.argv[2])
