"""Closed-allowlist downloader. No search, discovery, reference, or external redirect access."""
import datetime
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path('/work')
LOG = ROOT / 'artifacts/access_events.jsonl'
PDFS = {f'https://arxiv.org/pdf/{x}' for x in ['1808.08683','2302.04997','1305.6156','1305.6979']}
OFFICIAL = {
    'https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles',
    'https://neurips.cc/Conferences/2026/CallForPapers',
    'https://neurips.cc/Conferences/2026/MainTrackHandbook',
    'https://neurips.cc/Conferences/2026/PaperInformation',
    'https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles',
}

def log(event):
    event['timestamp_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with LOG.open('a') as f:
        f.write(json.dumps(event, sort_keys=True) + '\n')

class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        log({'event':'redirect_blocked', 'url':req.full_url, 'target':newurl, 'status':code})
        raise RuntimeError('Redirect not followed: ' + newurl)

def fetch(url, destination, authorized_media=False):
    if url not in PDFS | OFFICIAL:
        if not (authorized_media and url.startswith('https://media.neurips.cc/') and '\n' not in url):
            raise ValueError('Not allowlisted: ' + url)
    target = ROOT / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    log({'event':'request', 'method':'GET', 'url':url, 'destination':str(target)})
    opener = urllib.request.build_opener(StrictRedirect())
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'AllowlistedResearchAcquisition/1.0'})
        with opener.open(req, timeout=50) as r:
            data = r.read(30_000_001)
            if len(data)>30_000_000:
                raise ValueError('Response exceeds 30MB cap')
            if url in PDFS and not data.startswith(b'%PDF-'):
                raise ValueError('Expected original PDF; refusing to interpret non-PDF response')
            target.write_bytes(data)
            event={'event':'success', 'url':url, 'final_url':r.url, 'status':r.status,
                   'content_type':r.headers.get('Content-Type'), 'bytes':len(data),
                   'sha256':hashlib.sha256(data).hexdigest(), 'destination':str(target)}
            log(event)
            print(json.dumps(event, sort_keys=True))
    except Exception as e:
        log({'event':'failure','url':url,'error':str(e)})
        print(json.dumps({'url':url,'error':str(e)}))

if __name__=='__main__':
    if sys.argv[1]=='pdfs':
        for x in ['1808.08683','2302.04997','1305.6156','1305.6979']:
            fetch('https://arxiv.org/pdf/'+x,'artifacts/sources/'+x+'.pdf')
    else:
        fetch(sys.argv[1],sys.argv[2],len(sys.argv)>3 and sys.argv[3]=='--authorized-media')
