"""Download HELM-MMLU release v1.13.0 summary files (groups/json + a few top-level jsons).
Writes data/helm_v1.13.0/... and data/helm_v1.13.0.sha256 (checksums of every file).
Usage: python code/fetch_helm.py
"""
import hashlib, os, re, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

BUCKET = "https://storage.googleapis.com/crfm-helm-public/"
PREFIX = "mmlu/benchmark_output/releases/v1.13.0/"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "helm_v1.13.0")


def listing():
    url = BUCKET + "?prefix=" + urllib.parse.quote(PREFIX) + "&max-keys=1000"
    t = urllib.request.urlopen(url, timeout=60).read().decode()
    return re.findall(r"<Key>([^<]+)</Key>", t)


def get(key):
    dst = os.path.join(OUT, key[len(PREFIX):])
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    url = BUCKET + urllib.parse.quote(key)
    for _ in range(4):
        try:
            data = urllib.request.urlopen(url, timeout=60).read()
            open(dst, "wb").write(data)
            return dst
        except Exception as e:  # retry
            err = e
    raise err


if __name__ == "__main__":
    keys = [k for k in listing() if not k.endswith("/")]
    print(len(keys), "files")
    with ThreadPoolExecutor(16) as ex:
        paths = list(ex.map(get, keys))
    with open(os.path.join(OUT, "..", "helm_v1.13.0.sha256"), "w") as f:
        for p in sorted(paths):
            f.write(hashlib.sha256(open(p, "rb").read()).hexdigest() + "  " + os.path.relpath(p, OUT) + "\n")
    print("done")
