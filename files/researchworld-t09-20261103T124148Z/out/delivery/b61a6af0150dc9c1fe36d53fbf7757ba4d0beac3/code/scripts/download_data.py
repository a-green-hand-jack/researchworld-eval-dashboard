"""Download only the explicitly permitted graph URL, enforcing frozen hash."""
import hashlib
import json
from pathlib import Path
import urllib.request

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/"data/manifest.json").read_text())
for name,spec in manifest.items():
    path=root/"data"/name
    if not path.exists():
        with urllib.request.urlopen(spec["url"],timeout=90) as response:
            payload=response.read()
        path.write_bytes(payload)
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual!=spec["sha256"]:
        raise ValueError(f"Hash mismatch for {name}: {actual}")
    print(name,actual)
