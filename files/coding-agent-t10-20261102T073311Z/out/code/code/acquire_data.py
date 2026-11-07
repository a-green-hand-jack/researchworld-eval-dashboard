"""Download only the three selected version-pinned PPI example artifacts."""
import json,hashlib
from pathlib import Path
import gdown
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
IDS={'galaxies':'1pDLQesPhbH5fSZW1m4aWC-wnJWnp1rGV','forest':'1Vqi1wSmVnWh_2lLQuDwrhkGcipvoWBc0','alphafold':'1lOhdSJEcFbZmcIoqmlLxo3LgLG1KqPho'}
expected={Path(x['file']).stem:x['sha256'] for x in json.loads((ROOT/'data/manifest.json').read_text())}
for name,id in IDS.items():
    path=ROOT/'data'/f'{name}.npz'
    if not path.exists():gdown.download(id=id,output=str(path),quiet=False)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    if sha!=expected[name]:raise ValueError(f'{name}: SHA256 mismatch; do not silently replace version-pinned data')
    z=np.load(path)
    assert z['Y'].shape==z['Yhat'].shape
    print(name,dict(records=len(z['Y']),sha256=sha,score_range=[float(z['Yhat'].min()),float(z['Yhat'].max())]))
