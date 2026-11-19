"""Download only public data originals; no topic searches. Run from any directory."""
from pathlib import Path
import hashlib, json, requests, zipfile
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
URLS={'german.zip':'https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip',
'pima.arff':'https://www.openml.org/data/download/37/dataset_37_diabetes.arff'}
def main():
    for name,url in URLS.items():
        dest=DATA/name
        if not dest.exists():
            r=requests.get(url,timeout=120); r.raise_for_status(); dest.write_bytes(r.content)
    with zipfile.ZipFile(DATA/'german.zip') as z: z.extractall(DATA/'german')
    if not (DATA/'acs2018vt.pkl').exists():
        from folktables import ACSDataSource
        s=ACSDataSource(survey_year='2018',horizon='1-Year',survey='person',root_dir=str(DATA/'acs'))
        s.get_data(states=['VT'],download=True).to_pickle(DATA/'acs2018vt.pkl')
    files=[p for p in DATA.rglob('*') if p.is_file()]
    (DATA/'manifest.json').write_text(json.dumps({str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files if p.name!='manifest.json'},indent=2))
if __name__=='__main__': main()
