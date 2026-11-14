"""Direct official documents only. URLs are supplied explicitly, never discovered by search."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse

root=Path('/work/official_template')
manifest=root/'download_manifest.json'
records=json.loads(manifest.read_text()) if manifest.exists() else []
class OfficialOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        host=urlparse(newurl).hostname or ''
        if not any(host==h or host.endswith('.'+h) for h in ['neurips.cc','iclr.cc','icml.cc']):
            raise RuntimeError('Blocked nonofficial redirect: '+newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)
opener=urllib.request.build_opener(OfficialOnly)
for url,filename in zip(sys.argv[1::2],sys.argv[2::2]):
    record={'requested_url':url,'download_started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'path':str(root/filename)}
    try:
        with opener.open(urllib.request.Request(url,headers={'User-Agent':'IndependentResearchSupport/1.0'}),timeout=80) as response:
            data=response.read()
            record.update(status=response.status, final_url=response.url, headers=dict(response.headers))
        (root/filename).write_bytes(data)
        record.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),download_completed_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    except Exception as e:
        record['error']=repr(e)
        if isinstance(e,urllib.error.HTTPError):
            body=e.read()
            (root/(filename+'.error')).write_bytes(body)
            record.update(status=e.code,error_body_sha256=hashlib.sha256(body).hexdigest())
    records.append(record)
    print(json.dumps({k:v for k,v in record.items() if k!='headers'}))
manifest.write_text(json.dumps(records,indent=2))
