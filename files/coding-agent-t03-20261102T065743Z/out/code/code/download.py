"""Fetch only explicitly approved sources; persist hashes and URLs."""
from pathlib import Path
import requests,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
'german.data':('https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip','zip'),
'diabetes.arff':('https://www.openml.org/data/v1/download/37/diabetes.arff','raw'),
}
def fetch(url,path):
 path=Path(path)
 if not path.exists():
  r=requests.get(url,timeout=180);r.raise_for_status();path.write_bytes(r.content)
 return {'url':url,'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
def main():
 records=[]
 for name,(url,typ) in SOURCES.items():
  path=ROOT/'data/raw'/(name+'.zip' if typ=='zip' else name)
  records.append(fetch(url,path))
  if typ=='zip':
   with zipfile.ZipFile(path) as z:
    for f in z.namelist():
     if f.endswith('german.data'): (ROOT/'data/raw/german.data').write_bytes(z.read(f))
 from folktables import ACSDataSource
 src=ACSDataSource(survey_year='2018',horizon='1-Year',survey='person',root_dir=str(ROOT/'data/raw/acs'))
 frame=src.get_data(states=['CA'],download=True)
 frame.to_pickle(ROOT/'data/raw/acs_ca2018.pkl')
 for path in (ROOT/'data/raw/acs').rglob('*'):
  if path.is_file(): records.append({'file':str(path.relative_to(ROOT)),'url':'https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_pca.zip','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
 records.append({'file':'data/raw/acs_ca2018.pkl','rows':len(frame),'source':'ACS PUMS 2018 California person, via folktables 0.0.12'})
 (ROOT/'data/manifest.json').write_text(json.dumps(records,indent=2))
 print(records,flush=True)
if __name__=='__main__':main()
