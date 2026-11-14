#!/usr/bin/env python3
"""Fetch only explicitly permitted, pinned starter PDFs; keep them out of git."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(Path(__file__).with_name('sources.json').read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    for source in manifest['pdf_sources']:
        target = args.output / (source['key'] + '.pdf')
        expected = source['sha256']
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
            print(source['key'], 'existing verified')
            continue
        with urllib.request.urlopen(source['pinned_url'], timeout=60) as response:
            payload = response.read()
        if not payload.startswith(b'%PDF'):
            raise ValueError(f"Non-PDF response for {source['key']}")
        actual = hashlib.sha256(payload).hexdigest()
        if actual != expected:
            raise ValueError(f"Checksum mismatch for {source['key']}: {actual}")
        target.write_bytes(payload)
        print(source['key'], 'downloaded verified')


if __name__ == '__main__':
    main()
