"""Acquire ONLY the two original ppi-python0.2.3 dataset files. No web search.
Original dataset-specific license was not stated; do not assume redistribution.
"""
from pathlib import Path
import hashlib,json
import gdown
import numpy as np
ROOT=Path(__file__).resolve().parent
DATA={
 'galaxies':('1pDLQesPhbH5fSZW1m4aWC-wnJWnp1rGV','7be1d40a049f524fc51e150281541359a47c5eca80343dfac5b1c457fd7eae99'),
 'forest':('1Vqi1wSmVnWh_2lLQuDwrhkGcipvoWBc0','9708f3be14850a55d03f88dad235c87b4a3b6c6e8cb81173cc580de8f7386ade')}

def main():
    (ROOT/'data').mkdir(exist_ok=True); meta={}
    for name,(gid,expected) in DATA.items():
        path=ROOT/'data'/f'{name}.npz'
        if not path.exists():
            gdown.download(id=gid,output=str(path),quiet=False)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=expected:
            raise RuntimeError(f'{name}: file hash changed. Expected {expected}, got {digest}; investigate, do not silently proceed.')
        data=np.load(path); y=data['Y']; score=data['Yhat']
        assert len(y)==len(score) and np.all((y==0)|(y==1))
        assert np.all(np.isfinite(score)) and np.all((score>=0)&(score<=1))
        meta[name]={'source_package':'ppi-python==0.2.3','url':f'https://drive.google.com/uc?id={gid}',
                    'sha256':digest,'n':len(y),'label_mean':float(y.mean()),
                    'label_support':np.unique(y).tolist(),'score_min':float(score.min()),'score_max':float(score.max()),
                    'score_unique':len(np.unique(score)),'missing_values':int(np.isnan(score).sum()+np.isnan(y).sum()),
                    'target':'mean of empirical joint distribution; with-replacement iid sampling',
                    'license':'separate npz license not stated in inspected package; code MIT'}
        print(name,meta[name])
    (ROOT/'data'/'manifest.json').write_text(json.dumps(meta,indent=2))
if __name__=='__main__':main()
