#!/usr/bin/env python3
"""Optional reference download; all files remain under the workspace."""
from pathlib import Path
from datetime import datetime,timezone
import urllib.request,hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/literature';OUT.mkdir(parents=True,exist_ok=True)
URLS={
 'glambie_nature.html':'https://www.nature.com/articles/s41586-024-08545-z',
 'glambie_supplement.pdf':'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-08545-z/MediaObjects/41586_2024_8545_MOESM1_ESM.pdf',
 'glambie_constants.py':'https://raw.githubusercontent.com/earthwave/glambie/main/glambie/const/constants.py'}
rows=[]
for name,url in URLS.items():
 p=OUT/name
 if not p.exists():
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=60) as res:p.write_bytes(res.read())
 rows.append({'file':str(p.relative_to(ROOT)),'url':url,'archive_file_modified_utc':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
(OUT/'provenance.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Reference cache verified; provenance written.')
