"""Exact-ID acquisition only; no discovery, link following, or reference extraction."""
import urllib.request, urllib.error, urllib.parse
import pathlib, json, hashlib, time, datetime, re
from html.parser import HTMLParser

ROOT = pathlib.Path('/work/artifacts/literature')
IDS = ['2210.07316','2402.14992','2407.12844','2407.13696','2405.10938','2412.06540']

def log(x):
    x['utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (ROOT/'access_log.jsonl').open('a') as f: f.write(json.dumps(x, ensure_ascii=False)+'\n')

class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urllib.parse.urlparse(newurl)
        ok = p.hostname in ['arxiv.org','www.arxiv.org'] and any(re.fullmatch('/(?:abs|pdf|html)/'+re.escape(i)+r'(?:v\d+)?(?:\.pdf)?', p.path) for i in IDS)
        log({'event':'redirect','from':req.full_url,'to':newurl,'status':code,'allowed':ok})
        if not ok: raise RuntimeError('Blocked redirect outside allowlist; destination NOT requested: '+newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class Metadata(HTMLParser):
    def __init__(self): super().__init__(); self.meta={}
    def handle_starttag(self,t,attrs):
        a=dict(attrs)
        if t=='meta' and a.get('name','').startswith('citation_'):
            self.meta.setdefault(a['name'],[]).append(a.get('content',''))

class Body(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.stack=[]; self.out=[]; self.active=False; self.done=False; self.suppressed=0
    def handle_starttag(self,t,attrs):
        a=dict(attrs); c=a.get('class',''); ident=a.get('id','')
        if t=='article': self.active=True
        if self.active and ('ltx_bibliography' in c or ident in ['bib','bibliography','references']): self.done=True
        if t in ['script','style','nav','footer']: self.suppressed+=1
        if self.active and not self.done and t in ['p','div','section','h1','h2','h3','h4','li','tr','br']: self.out.append('\n')
    def handle_endtag(self,t):
        if t in ['script','style','nav','footer'] and self.suppressed: self.suppressed-=1
        if t=='article': self.active=False
        if self.active and not self.done and t in ['p','div','section','h1','h2','h3','h4','li','tr']: self.out.append('\n')
    def handle_data(self,s):
        if self.active and not self.done and not self.suppressed: self.out.append(s)

opener=urllib.request.build_opener(StrictRedirect())
for ident in IDS:
    for kind,ext in [('abs','html'),('html','html'),('pdf','pdf')]:
        url=f'https://arxiv.org/{kind}/{ident}'
        path=ROOT/f'{ident}.{kind}.{ext}'
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'AllowedPaperReading/1.0 (exact arXiv IDs only)'})
            with opener.open(req,timeout=45) as r:
                body=r.read(); status=r.status; final=r.url; ctype=r.headers.get('Content-Type','')
            path.write_bytes(body)
            log({'event':'request','url':url,'final_url':final,'status':status,'content_type':ctype,'bytes':len(body),'path':str(path),'sha256':hashlib.sha256(body).hexdigest()})
            if kind=='abs':
                m=Metadata(); m.feed(body.decode('utf-8','replace'))
                (ROOT/f'{ident}.metadata.json').write_text(json.dumps(m.meta,ensure_ascii=False,indent=2))
            elif kind=='html':
                p=Body(); p.feed(body.decode('utf-8','replace'))
                text=re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+','\n\n',''.join(p.out))
                (ROOT/f'{ident}.body.txt').write_text(text)
                log({'event':'extraction','source':str(path),'path':str(ROOT/f'{ident}.body.txt'),'bibliography_excluded':True,'characters':len(text)})
            print(ident,kind,status,len(body),flush=True)
        except Exception as e:
            log({'event':'request_error','url':url,'error':str(e)})
            print(ident,kind,'ERROR',str(e),flush=True)
        time.sleep(3)
