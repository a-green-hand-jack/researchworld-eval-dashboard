"""Download the HELM MMLU v1.13.0 release summary files (groups/json + top-level json) and record SHA-256.
Usage: python3 code/fetch_helm.py OUTDIR
"""
import hashlib, json, sys, urllib.parse, urllib.request, pathlib
BUCKET = "crfm-helm-public"
PREFIX = "mmlu/benchmark_output/releases/v1.13.0/"
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
def get(u):
    with urllib.request.urlopen(u, timeout=60) as r: return r.read()
items, tok = [], None
while True:
    u = f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o?prefix={PREFIX}&maxResults=1000&fields=items(name,size),nextPageToken"
    if tok: u += "&pageToken=" + urllib.parse.quote(tok)
    d = json.loads(get(u)); items += d["items"]; tok = d.get("nextPageToken")
    if not tok: break
man = {}
for it in items:
    rel = it["name"][len(PREFIX):]
    if not rel or rel.endswith("/"): continue
    p = out / rel; p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        b = get(f"https://storage.googleapis.com/{BUCKET}/" + urllib.parse.quote(it["name"]))
        p.write_bytes(b)
    man[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
(out / "MANIFEST.sha256.json").write_text(json.dumps(man, indent=1, sort_keys=True))
print(len(man), "files")
