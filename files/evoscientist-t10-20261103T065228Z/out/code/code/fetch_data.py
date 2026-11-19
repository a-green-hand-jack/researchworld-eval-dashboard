"""Download only direct allowlisted data files; no repository browsing."""
from pathlib import Path
import hashlib,json
import numpy as np
import gdown
ROOT=Path(__file__).resolve().parents[1]
IDS={'galaxies':'1pDLQesPhbH5fSZW1m4aWC-wnJWnp1rGV','forest':'1Vqi1wSmVnWh_2lLQuDwrhkGcipvoWBc0'}

def main():
    out=ROOT/'data';out.mkdir(exist_ok=True)
    records=[]
    for name,id in IDS.items():
        p=out/(name+'.npz')
        if not p.exists():gdown.download(id=id,output=str(p),quiet=False)
        with np.load(p) as d:
            y,z=d['Y'],d['Yhat']
            assert y.ndim==z.ndim==1 and len(y)==len(z)
            assert np.all(np.isfinite(y)) and np.all(np.isfinite(z))
            assert np.all((y==0)|(y==1)) and np.all((z>=0)&(z<=1))
            r={'dataset':name,'ppi_python':'0.2.3','source_id':id,'source_url':'https://drive.google.com/uc?id='+id,
              'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
              'n':len(y),'theta':float(y.mean()),'score_min':float(z.min()),'score_max':float(z.max()),
              'score_distinct':len(np.unique(z)),'missing':0,'label_values':[0,1],
              'score_label_correlation':float(np.corrcoef(y,z)[0,1]),
              'fraction_score_duplicates':float(1-len(np.unique(z))/len(z)),
              'fraction_duplicate_pairs':float(1-len(np.unique(np.c_[y,z],axis=0))/len(y)),
              'independent_data_license':'not specified in pinned package; no independent license asserted'}
            records.append(r)
    (ROOT/'artifacts'/'data_provenance.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))

if __name__=='__main__':main()
