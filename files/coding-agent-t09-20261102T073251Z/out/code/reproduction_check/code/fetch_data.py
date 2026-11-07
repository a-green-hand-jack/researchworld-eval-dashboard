"""Acquire only the explicitly allowed public SNAP topology; verify exact bytes."""
from pathlib import Path
import hashlib,requests
from study import ROOT

URL='https://snap.stanford.edu/data/facebook_combined.txt.gz'
SHA='125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7'
target=ROOT/'data/raw/facebook_combined.txt.gz'
target.parent.mkdir(parents=True,exist_ok=True)
if not target.exists():
    response=requests.get(URL,timeout=60)
    response.raise_for_status()
    payload=response.content
    assert hashlib.sha256(payload).hexdigest()==SHA,'Unexpected data version; stop rather than silently change graph.'
    target.write_bytes(payload)
assert hashlib.sha256(target.read_bytes()).hexdigest()==SHA
print(f'Verified {target.name}: {target.stat().st_size} bytes; SHA-256 {SHA}')
