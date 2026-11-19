"""Download only frozen public score summaries; never mirror model runs."""
from __future__ import annotations
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
HELM = "https://storage.googleapis.com/crfm-helm-public"
PREFIX = "mmlu/benchmark_output/releases/v1.13.0/"
CONTENTS_SHA = "9c09a7cae43334062a82cb164f2ef255013dafa2"

def download(url, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=90)
            r.raise_for_status()
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(r.content)
            tmp.replace(path)
            return path
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "data/manifest.json"
    old = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    entries = []
    def get(url, rel):
        path = download(url, ROOT / rel)
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        previous = next((e for e in old.get("files", []) if e["path"] == rel), None)
        if previous and previous["sha256"] != sha:
            raise RuntimeError(f"Checksum mismatch: {rel}")
        item = dict(path=rel, url=url, sha256=sha, bytes=path.stat().st_size)
        entries.append(item)
        return path
    listing = get(f"{HELM}?prefix={PREFIX}&max-keys=500", "data/raw/helm_listing.xml")
    tree = ET.fromstring(listing.read_bytes())
    ns = {"g": "http://doc.s3.amazonaws.com/2006-03-01"}
    keys = [e.text for e in tree.findall(".//g:Key", ns)]
    subject_keys = sorted(k for k in keys if re.fullmatch(
        re.escape(PREFIX) + r"groups/json/mmlu_mmlu_subject:[a-z_]+\.json", k))
    assert len(subject_keys) == 57, len(subject_keys)
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda k: get(f"{HELM}/{k}", "data/raw/helm/" + k.split(":")[-1]), subject_keys))
    get(f"{HELM}/{PREFIX}summary.json", "data/raw/helm_summary.json")
    get(f"https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/{CONTENTS_SHA}/data/train-00000-of-00001.parquet",
        "data/raw/open_llm_contents.parquet")
    get(f"https://huggingface.co/datasets/open-llm-leaderboard/contents/raw/{CONTENTS_SHA}/README.md",
        "data/raw/open_llm_README.md")
    entries.sort(key=lambda e: e["path"])
    result = dict(retrieved_utc=old.get("retrieved_utc", dt.datetime.now(dt.timezone.utc).isoformat()),
                  helm_release="v1.13.0", helm_release_date="2025-01-10",
                  contents_sha=CONTENTS_SHA, contents_last_update="2025-03-20", files=entries)
    manifest_path.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Verified {len(entries)} raw files, {sum(e['bytes'] for e in entries):,} bytes")

if __name__ == "__main__":
    main()
