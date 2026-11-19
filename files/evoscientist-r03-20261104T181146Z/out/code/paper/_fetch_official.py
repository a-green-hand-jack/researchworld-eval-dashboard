"""Audited direct acquisition of official conference resources only; no discovery search."""
import urllib.request, urllib.error, hashlib, datetime, sys
from pathlib import Path
from urllib.parse import urlsplit
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None
opener=urllib.request.build_opener(NoRedirect)
url,dest=sys.argv[1:]
u=urlsplit(url)
if u.scheme!='https' or u.hostname not in {'neurips.cc','media.neurips.cc'}:
    raise ValueError('Not an approved official conference host')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
log=Path('literature/access_log.md')
try:
    with opener.open(urllib.request.Request(url,headers={'User-Agent':'Research-safe-acquisition/1.0'}),timeout=40) as response:
        data=response.read(); status=response.status; ct=response.headers.get('Content-Type','')
    Path(dest).parent.mkdir(parents=True,exist_ok=True); Path(dest).write_bytes(data)
    entry=f'- {now} GET {url} — HTTP {status}; {ct}; {len(data)} bytes. Saved `/work/{dest}`; SHA256 `{hashlib.sha256(data).hexdigest()}`.\n'
    print(entry)
except urllib.error.HTTPError as e:
    entry=f'- {now} GET {url} — HTTP {e.code}; not saved. Redirect Location: `{e.headers.get("Location", "none")}`; no redirect followed.\n'; print(entry)
except Exception as e:
    entry=f'- {now} GET {url} — failed: {type(e).__name__}: {e}; not saved.\n'; print(entry)
with log.open('a') as f:f.write(entry)
