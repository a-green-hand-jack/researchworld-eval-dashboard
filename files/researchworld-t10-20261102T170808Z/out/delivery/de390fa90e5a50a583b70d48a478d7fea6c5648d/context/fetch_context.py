from pathlib import Path
import concurrent.futures, urllib.request, hashlib, json, subprocess
Path('sources').mkdir(parents=True, exist_ok=True)
items=[('ppi','2301.09633v1'),('ppiplus','2311.01453v1'),('crossppi','2309.16598v1'),('active','2403.03208v2'),('stratified','2406.04291v1'),('dml','1608.00060v1'),('folktables','2108.04884v1'),('galaxyzoo','1308.3496v1'),('empirical-bernstein','0907.3740v1')]
def fetch(item):
 name, aid=item; url='https://arxiv.org/pdf/'+aid
 try:
  data=urllib.request.urlopen(url,timeout=50).read(); path=Path('sources')/(name+'.pdf');path.write_bytes(data)
  subprocess.run(['pdftotext','-layout',str(path),str(path.with_suffix('.txt'))],check=True)
  return {'name':name,'arxiv':aid,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'status':'retrieved'}
 except Exception as e:return {'name':name,'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(fetch,items))
Path('sources/retrieval-rerun.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
