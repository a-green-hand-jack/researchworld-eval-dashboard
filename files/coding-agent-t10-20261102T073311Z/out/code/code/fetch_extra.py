import urllib.request,json,hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
urls={
'literature/bernstein.pdf':'https://arxiv.org/pdf/0907.3740',
'literature/ppi_mean_source.py':'https://raw.githubusercontent.com/aangelopoulos/ppi_py/v0.2.3/ppi_py/ppi.py',
'literature/ppi_LICENSE':'https://raw.githubusercontent.com/aangelopoulos/ppi_py/v0.2.3/LICENSE',
'literature/galaxies_example.ipynb':'https://raw.githubusercontent.com/aangelopoulos/ppi_py/v0.2.3/examples/galaxies.ipynb',
'literature/forest_example.ipynb':'https://raw.githubusercontent.com/aangelopoulos/ppi_py/v0.2.3/examples/forest.ipynb',
'literature/alphafold_example.ipynb':'https://raw.githubusercontent.com/aangelopoulos/ppi_py/v0.2.3/examples/alphafold.ipynb',
'literature/ethics.html':'https://neurips.cc/public/EthicsGuidelines'}
def f(kv):
 p,u=kv
 try:
  with urllib.request.urlopen(u,timeout=45) as r:
   b=r.read();Path(p).write_bytes(b); z=dict(path=p,url=u,status=r.status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 except Exception as e: z=dict(path=p,url=u,error=str(e))
 print(z,flush=True);return z
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(f,urls.items()))
 Path('logs/extra_fetch.json').write_text(json.dumps(r,indent=2))
