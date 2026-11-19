import datetime, hashlib, json, pathlib, urllib.request, urllib.error
from pypdf import PdfReader
r=pathlib.Path('/work')
u='https://projecteuclid.org/journals/annals-of-statistics/volume-41/issue-2/Valid-post-selection-inference/10.1214/12-AOS1077.pdf'
e={'requested_url':u,'accessed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'Direct original PDF matching DOI redirect; no publisher links followed'}
try:
    with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Independent-background-reading/1.0'}),timeout=60) as f:
        data=f.read()
        e.update(status=f.status,final_url=f.url,content_type=f.headers.get('Content-Type'),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    if data.startswith(b'%PDF'):
        p=r/'literature_berk_12-AOS1077.pdf'
        p.write_bytes(data)
        pages=PdfReader(p).pages
        (r/'literature_berk_12-AOS1077.txt').write_text('\n'.join(f'\n===== PDF PAGE {i+1} =====\n'+(x.extract_text() or '') for i,x in enumerate(pages)))
        e.update(saved_as=p.name,extracted_text='literature_berk_12-AOS1077.txt',pages=len(pages),extraction_tool='pypdf 6.21.4')
    else:
        p=r/'literature_berk_pdf_unavailable_response.html'
        p.write_bytes(data)
        e.update(saved_as=p.name,error='Not a PDF; not consulted')
except Exception as x:
    e['error']=str(x)
    if isinstance(x,urllib.error.HTTPError): e['status']=x.code
p=r/'literature_access_manifest.json'
m=json.loads(p.read_text())
m['accesses'].append(e)
p.write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps(e))
