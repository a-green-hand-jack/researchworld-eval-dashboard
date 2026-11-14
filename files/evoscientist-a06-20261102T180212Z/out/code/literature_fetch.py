"""Direct-original-only retrieval. No search/discovery/citation APIs.
Run: python /work/literature_fetch.py
"""
import datetime, hashlib, json, pathlib, time, urllib.request, urllib.error
from pypdf import PdfReader
ROOT = pathlib.Path('/work')
IDS = ['2406.01574','2310.03714','2406.11695','1411.2664','1502.04585','1212.6906']
manifest_path = ROOT / 'literature_access_manifest.json'
manifest = {'policy': 'Only six user-whitelisted arXiv originals and DOI 10.1214/12-AOS1077. No search engines, citation APIs, recommendation pages, later reviews, or related-paper links. HTML assets/scripts/links are not fetched. Bibliographies are not evidence sources.', 'accesses': []}
class ControlledRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed = ('https://arxiv.org/abs/','https://arxiv.org/pdf/','https://arxiv.org/html/')
        if not newurl.startswith(allowed):
            raise urllib.error.HTTPError(req.full_url, code, 'Redirect stopped for manual original-article verification', headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)
opener = urllib.request.build_opener(ControlledRedirect())
def fetch(url, filename, accept='*/*'):
    entry={'requested_url':url,'accessed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'Independent-background-reading/1.0','Accept':accept})
        with opener.open(request,timeout=60) as response:
            data=response.read()
            entry.update(status=response.status, final_url=response.url, content_type=response.headers.get('Content-Type'), bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), saved_as=filename)
        (ROOT/filename).write_bytes(data)
        if data.startswith(b'%PDF'):
            pages=PdfReader(ROOT/filename).pages
            text='\n'.join(f'\n===== PDF PAGE {i+1} =====\n'+(p.extract_text() or '') for i,p in enumerate(pages))
            txt=filename.rsplit('.',1)[0]+'.txt'
            (ROOT/txt).write_text(text)
            entry.update(extracted_text=txt,pages=len(pages),extraction_tool='pypdf 6.21.4; pdftotext unavailable')
    except Exception as error:
        entry.update(error=str(error))
        if isinstance(error,urllib.error.HTTPError):
            entry.update(status=error.code, redirect_location=error.headers.get('Location'))
    manifest['accesses'].append(entry)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(entry),flush=True)
for aid in IDS:
    fetch(f'https://arxiv.org/abs/{aid}',f'literature_arxiv_{aid}_abs.html')
    time.sleep(3)
    fetch(f'https://arxiv.org/pdf/{aid}',f'literature_arxiv_{aid}.pdf')
    time.sleep(3)
fetch('https://doi.org/10.1214/12-AOS1077','literature_berk_doi_response.html','application/pdf,text/html;q=0.9')
