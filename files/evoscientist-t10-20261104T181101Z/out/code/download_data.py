"""Download only the two pinned PPI v0.2.3 example arrays; validate SHA256.
No paper searches, repository crawling, predictor training, or gdown dependency.
Dataset licensing is unresolved; do not interpret MIT code license as data license.
"""
from pathlib import Path
import hashlib
import urllib.request
import numpy as np

ROOT=Path(__file__).resolve().parent
DATA={
    'forest':('1Vqi1wSmVnWh_2lLQuDwrhkGcipvoWBc0','9708f3be14850a55d03f88dad235c87b4a3b6c6e8cb81173cc580de8f7386ade'),
    'galaxies':('1pDLQesPhbH5fSZW1m4aWC-wnJWnp1rGV','7be1d40a049f524fc51e150281541359a47c5eca80343dfac5b1c457fd7eae99')}


def main():
    (ROOT/'data').mkdir(exist_ok=True)
    for name,(identifier,expected) in DATA.items():
        path=ROOT/'data'/f'{name}.npz'
        if not path.exists():
            url=f'https://drive.google.com/uc?export=download&id={identifier}'
            request=urllib.request.Request(url,headers={'User-Agent':'fixed-score-audit/1.0'})
            content=urllib.request.urlopen(request,timeout=120).read()
            if hashlib.sha256(content).hexdigest()!=expected:
                raise RuntimeError(f'{name}: unexpected download hash; no changed data accepted')
            path.write_bytes(content)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,f'{name}: file hash changed'
        with np.load(path,allow_pickle=False) as d:
            assert d['Y'].shape==d['Yhat'].shape
            assert np.isin(d['Y'],[0,1]).all()
            assert np.isfinite(d['Yhat']).all()
            assert ((d['Yhat']>=0)&(d['Yhat']<=1)).all()
        print(name,'verified',expected)


if __name__=='__main__':main()
