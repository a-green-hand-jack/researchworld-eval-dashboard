"""Download the HELM MMLU release v1.13.0 summary files (GCS bucket crfm-helm-public) and record md5/sizes.
usage: fetch_helm.py OUTDIR MANIFEST_JSON"""
import sys, json, os, urllib.request, urllib.parse, hashlib
out, man = sys.argv[1], sys.argv[2]
prefix = "mmlu/benchmark_output/releases/v1.13.0/"
api = "https://storage.googleapis.com/storage/v1/b/crfm-helm-public/o?prefix=%s&maxResults=1000"
items, tok = [], None
while True:
    u = api % urllib.parse.quote(prefix) + (("&pageToken=" + tok) if tok else "")
    d = json.load(urllib.request.urlopen(u))
    items += d.get("items", []); tok = d.get("nextPageToken")
    if not tok: break
rows = []
for it in items:
    rel = it["name"][len(prefix):]
    if rel.endswith("/"): continue
    dst = os.path.join(out, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
    url = "https://storage.googleapis.com/crfm-helm-public/" + urllib.parse.quote(it["name"])
    req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
    data = urllib.request.urlopen(req).read()
    open(dst, "wb").write(data)
    rows.append(dict(path=rel, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), gcs_md5=it["md5Hash"], gcs_generation=it["generation"]))
json.dump(rows, open(man, "w"), indent=1)
print(len(rows), "files", sum(r["bytes"] for r in rows), "bytes")
