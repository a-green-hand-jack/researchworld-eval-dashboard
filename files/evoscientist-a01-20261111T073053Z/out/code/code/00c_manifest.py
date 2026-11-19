"""SHA-256 manifest of every downloaded raw file and processed table -> data/MANIFEST_full.json"""
import os, json, hashlib
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); D = os.path.join(ROOT, 'data')
man = {}
for dp, _, fs in os.walk(D):
    for f in fs:
        if f.startswith('MANIFEST'): continue
        p = os.path.join(dp, f); man[os.path.relpath(p, D)] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
json.dump(man, open(os.path.join(D, 'MANIFEST_full.json'), 'w'), indent=0, sort_keys=True); print(len(man), 'files')
