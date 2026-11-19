"""Direct, exact-URL retrieval only; no redirects, link following, or discovery."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from html.parser import HTMLParser
import requests

ROOT = Path('/work')
OUT = ROOT / 'literature'
ART = ROOT / 'artifacts'
SOURCES = [
 ('https://arxiv.org/pdf/2108.04884', '2108.04884', 'pdf', 'Supplied folktables task/data starter; bounded reading'),
 ('https://neurips.cc/public/EthicsGuidelines', 'neurips_ethics_guidelines', 'html', 'Supplied official ethics requirements; direct verification'),
 ('https://www.census.gov/about/policies/privacy/data_stewardship.html', 'census_data_stewardship', 'html', 'Supplied official Census privacy/data stewardship policy'),
 ('https://www.census.gov/about/policies/copyright.html', 'census_copyright', 'html', 'Supplied official Census copyright/reuse policy'),
 ('https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data', 'uci_german_credit_144', 'html', 'Supplied UCI German source; license verification'),
 ('https://www.openml.org/api/v1/json/data/37', 'openml37_metadata', 'json', 'Supplied OpenML37 metadata; license verification'),
]

def sha(p):
 return hashlib.sha256(p.read_bytes()).hexdigest()

class TextOnly(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True); self.hidden=0; self.parts=[]
 def handle_starttag(self, tag, attrs):
  if tag in ('script','style'): self.hidden+=1
  if tag in ('p','div','section','h1','h2','h3','h4','li','br','tr'): self.parts.append('\n')
 def handle_endtag(self, tag):
  if tag in ('script','style') and self.hidden: self.hidden-=1
  if tag in ('p','div','section','h1','h2','h3','h4','li','tr'): self.parts.append('\n')
 def handle_data(self, data):
  if not self.hidden: self.parts.append(data)
 def text(self):
  return '\n'.join(' '.join(line.split()) for line in ''.join(self.parts).splitlines() if line.strip())+'\n'

before = {'source_notes_sha256': sha(ART/'source_notes.md'),
          'access_log_bytes': (ART/'literature_access.tsv').stat().st_size,
          'access_log_prefix_sha256': sha(ART/'literature_access.tsv')}
manifest={'boundary':'Six supplied exact URLs only; redirects disabled; no linked resources fetched.', 'before':before, 'sources':[]}
for url, stem, ext, purpose in SOURCES:
 rec={'original_url':url,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'purpose':purpose}
 try:
  resp=requests.get(url, timeout=55, allow_redirects=False, headers={'User-Agent':'Direct-source-research-verification/1.0'})
  path=OUT/(stem+'.'+ext); path.write_bytes(resp.content)
  rec.update(status=resp.status_code, content_type=resp.headers.get('content-type',''), bytes=len(resp.content),sha256=sha(path),local_path=str(path),response_url=resp.url,redirect_location=resp.headers.get('location'))
  (OUT/(stem+'.provenance.json')).write_text(json.dumps(rec,indent=2)+'\n')
  if ext=='html':
   parser=TextOnly(); parser.feed(resp.text)
   textpath=OUT/(stem+'.txt'); textpath.write_text(parser.text()); rec['extracted_text_path']=str(textpath)
  elif ext=='json' and resp.status_code==200:
   textpath=OUT/(stem+'.pretty.json'); textpath.write_text(json.dumps(resp.json(),indent=2,ensure_ascii=False)+'\n'); rec['extracted_text_path']=str(textpath)
  elif ext=='pdf' and resp.status_code==200 and shutil.which('pdftotext'):
   textpath=OUT/(stem+'.pages1-6.txt')
   proc=subprocess.run(['pdftotext','-f','1','-l','6','-layout',str(path),str(textpath)],capture_output=True,text=True)
   rec['text_extraction_exit']=proc.returncode; rec['extracted_text_path']=str(textpath)
  print(json.dumps({k:rec.get(k) for k in ('original_url','status','content_type','bytes','sha256','local_path','redirect_location')}))
 except Exception as exc:
  rec.update(status='ERROR',content_type='',bytes=0,sha256_or_error=str(exc),local_path='')
  print(json.dumps(rec))
 with (ART/'literature_access.tsv').open('a',newline='') as f:
  csv.writer(f,delimiter='\t',lineterminator='\n').writerow([rec['utc'],url,purpose,rec['status'],rec.get('content_type',''),rec.get('bytes',0),rec.get('sha256',rec.get('sha256_or_error','')),rec.get('local_path','')])
 manifest['sources'].append(rec)
manifest['source_notes_unchanged']=sha(ART/'source_notes.md')==before['source_notes_sha256']
prefix=(ART/'literature_access.tsv').read_bytes()[:before['access_log_bytes']]
manifest['prior_access_rows_unchanged']=hashlib.sha256(prefix).hexdigest()==before['access_log_prefix_sha256']
(ART/'direct_source_verification_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'source_notes_unchanged':manifest['source_notes_unchanged'],'prior_access_rows_unchanged':manifest['prior_access_rows_unchanged']}))
