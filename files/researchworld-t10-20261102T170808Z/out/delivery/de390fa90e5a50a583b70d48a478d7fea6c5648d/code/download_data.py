#!/usr/bin/env python3
"""Retrieve the frozen PPI v0.2.3 example files and verify their hashes."""
import hashlib,json,urllib.request
from pathlib import Path
manifest=json.loads(Path('provenance/manifest.json').read_text())
Path('data').mkdir(exist_ok=True)
for row in manifest['data']:
 p=Path('data')/(row['name']+'.npz')
 if not p.exists():
  with urllib.request.urlopen(row['source']) as response: p.write_bytes(response.read())
 if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']: raise ValueError('Hash mismatch: '+str(p))
 print('verified',p)
