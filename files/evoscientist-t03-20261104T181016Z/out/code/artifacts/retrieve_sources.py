"""Direct allowlisted source retrieval only; no search or experiment code."""
import urllib.request, urllib.error, urllib.parse, csv, pathlib, datetime, hashlib, sys
ROOT=pathlib.Path('/work')
LOG=ROOT/'artifacts/literature_access.tsv'
IDS={'1705.07874','2202.01602','2204.11351','2410.01917','2006.16234'}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None
opener=urllib.request.build_opener(NoRedirect())
def allowed(url):
    u=urllib.parse.urlsplit(url)
    if u.scheme!='https': return False
    if u.hostname in {'arxiv.org','export.arxiv.org'}:
        return any(u.path in {'/pdf/'+i,'/pdf/'+i+'.pdf','/abs/'+i} for i in IDS)
    if u.hostname=='jmlr.org': return u.path=='/papers/v18/17-514.html' or u.path.startswith('/papers/volume18/17-514/')
    if u.hostname in {'neurips.cc','media.neurips.cc'}: return True
    if u.hostname in {'icml.cc','media.icml.cc'}: return True
    return False

def fetch(url,dest,purpose):
    dest=ROOT/dest
    for attempt in range(6):
        if not allowed(url): raise ValueError('Blocked non-permitted redirect/source: '+url)
        row=[datetime.datetime.now(datetime.timezone.utc).isoformat(),url,purpose,'','','','',str(dest)]
        nxt=None
        try:
            r=opener.open(urllib.request.Request(url,headers={'User-Agent':'RestrictedSourceVerification/1.0'}),timeout=70)
            data=r.read(); row[3]=str(r.status); row[4]=r.headers.get('Content-Type',''); row[5]=str(len(data)); row[6]=hashlib.sha256(data).hexdigest()
            dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(data)
        except urllib.error.HTTPError as e:
            row[3]=str(e.code); row[4]=e.headers.get('Content-Type','')
            if e.code in (301,302,303,307,308):
                nxt=urllib.parse.urljoin(url,e.headers.get('Location','')); row[6]='redirect to '+nxt
            else: row[6]=str(e)
        except Exception as e: row[3]='ERROR';row[6]=repr(e)
        exists=LOG.exists()
        with LOG.open('a') as f:
            w=csv.writer(f,delimiter='\t');
            if not exists:w.writerow(['utc','url','purpose','status','content_type','bytes','sha256_or_error','local_path'])
            w.writerow(row)
        print('\t'.join(row),flush=True)
        if nxt: url=nxt; continue
        return row[3]
    raise RuntimeError('Too many redirects')
if __name__=='__main__':fetch(*sys.argv[1:])
