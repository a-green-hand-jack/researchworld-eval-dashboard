"""Fetch only whitelisted starter literature and official conference material."""
import urllib.request, json, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URLS={
'literature/ppi.pdf':'https://arxiv.org/pdf/2301.09633v4',
'literature/ppiplus.pdf':'https://arxiv.org/pdf/2311.01453v2',
'literature/crossppi.pdf':'https://arxiv.org/pdf/2309.16598v3',
'literature/active.pdf':'https://arxiv.org/pdf/2403.03208v2',
'literature/stratified.pdf':'https://arxiv.org/pdf/2406.04291v2',
'literature/dml.pdf':'https://arxiv.org/pdf/1608.00060v7',
 'template/neurips2026.html':'https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles',
 'template/iclr2027.html':'https://iclr.cc/Conferences/2027/AuthorGuide',
 'literature/loader.py':'https://raw.githubusercontent.com/aangelopoulos/ppi_py/v0.2.3/ppi_py/datasets/datasets.py'}
def fetch(kv):
 p,u=kv
 try:
  with urllib.request.urlopen(u,timeout=60) as r:
   b=r.read(); (ROOT/p).write_bytes(b)
   z=dict(path=p,url=u,status=r.status,bytes=len(b))
 except Exception as e: z=dict(path=p,url=u,error=str(e))
 print(z,flush=True); return z
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=5) as ex: out=list(ex.map(fetch,URLS.items()))
 (ROOT/'logs/source_fetch.json').write_text(json.dumps(out,indent=2))
