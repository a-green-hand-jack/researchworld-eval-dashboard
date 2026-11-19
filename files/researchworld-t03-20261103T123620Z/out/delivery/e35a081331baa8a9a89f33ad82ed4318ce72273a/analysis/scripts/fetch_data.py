"""Acquire only prespecified public data; retain exact raw bytes and checksums."""
from pathlib import Path
from urllib.request import urlopen
import hashlib, json, sys, time, zipfile
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; RAW.mkdir(parents=True,exist_ok=True)
MAN=ROOT/'data/manifest.json'; MAN.parent.mkdir(exist_ok=True)
manifest=json.loads(MAN.read_text()) if MAN.exists() else {}
def fetch(key,url,name):
    dest=RAW/name
    existed=dest.exists();previous=manifest.get(key)
    if not existed:
        for attempt in range(3):
            try:
                with urlopen(url,timeout=120) as response, dest.with_suffix(dest.suffix+'.part').open('wb') as out:
                    while block:=response.read(1024*1024): out.write(block)
                dest.with_suffix(dest.suffix+'.part').replace(dest); break
            except Exception:
                if attempt==2: raise
                time.sleep(2)
    sha=hashlib.sha256(dest.read_bytes()).hexdigest()
    if previous and key in ['german','diabetes','acs'] and sha!=previous['sha256']:
        raise ValueError(f'{key}: downloaded/cached bytes differ from recorded dataset version')
    retrieved=previous['retrieved_utc'] if existed and previous and sha==previous['sha256'] else time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    manifest[key]={'url':url,'file':str(dest.relative_to(ROOT)),'sha256':sha,'bytes':dest.stat().st_size,'retrieved_utc':retrieved}
    MAN.write_text(json.dumps(manifest,indent=2)+'\n')
    print(key,manifest[key],flush=True)
    return dest

def main():
    selected=sys.argv[1:] or ['german','diabetes','acs']
    if 'german' in selected:
        fetch('german','https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip','german.zip')
    if 'diabetes' in selected:
        desc=fetch('diabetes_openml_metadata','https://www.openml.org/api/v1/json/data/37','diabetes_metadata.json')
        metadata=json.loads(desc.read_text())['data_set_description']
        fetch('diabetes',metadata['url'],'diabetes.arff')
    if 'acs' in selected:
        fetch('acs','https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_pca.zip','acs2018_ca.zip')
if __name__=='__main__': main()
