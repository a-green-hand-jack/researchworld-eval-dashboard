"""Offline inspection of already-downloaded PDF streams; no network."""
from pathlib import Path
import re, zlib, sys
for name in sys.argv[1:]:
    data = Path(name).read_bytes()
    print(name, data[:40])
    for m in re.finditer(rb'(\d+)\s+(\d+)\s+obj\b(.*?)endobj', data, re.S):
        body = m[3]
        stream = re.search(rb'stream\r?\n(.*?)\r?\n?endstream', body, re.S)
        if not stream:
            continue
        s = stream[1]
        if b'/FlateDecode' in body[:stream.start()]:
            try:
                s = zlib.decompress(s)
            except zlib.error:
                continue
        if b'BT' in s:
            print('OBJECT', m[1], s[:8000])
            break
