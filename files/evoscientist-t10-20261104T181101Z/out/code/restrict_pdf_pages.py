"""Local PDF page restriction for allowlisted source reading; standard library only.
Not a general-purpose PDF parser. Fails on unsupported/compressed page trees.
Retains only objects reachable from selected pages; strips their annotations.
Never prints page contents, metadata, references, or extracted source text.
"""
import pathlib
import re
import sys

src, dst = map(pathlib.Path, sys.argv[1:3])
first, last = map(int, sys.argv[3:5])
data = src.read_bytes()
objects = {}
for m in re.finditer(rb"(?m)^(\d+)\s+(\d+)\s+obj\b(.*?)^endobj\b", data, re.S):
    assert int(m[2]) == 0, "Nonzero generation unsupported"
    objects[int(m[1])] = m[3].strip()
trailer = re.findall(rb"trailer\s*<<(.*?)>>", data, re.S)[-1]
root = int(re.search(rb"/Root\s+(\d+)\s+0\s+R", trailer)[1])
root_pages = int(re.search(rb"/Pages\s+(\d+)\s+0\s+R", objects[root])[1])
refs = lambda value: [int(v) for v in re.findall(rb"\b(\d+)\s+0\s+R\b", value)]

def pages(k):
    value = objects[k].split(b"stream", 1)[0]
    if re.search(rb"/Type\s*/Pages\b", value):
        kids = re.search(rb"/Kids\s*\[(.*?)\]", value, re.S)[1]
        return [p for child in refs(kids) for p in pages(child)]
    assert re.search(rb"/Type\s*/Page\b", value)
    return [k]

ordered = pages(root_pages)
assert 1 <= first <= last <= len(ordered)
selected = ordered[first-1:last]
new_catalog = max(objects) + 1
new_pages = new_catalog + 1
for k in selected:
    value = objects[k]
    assert b"stream" not in value
    value = re.sub(rb"/Parent\s+\d+\s+0\s+R", f"/Parent {new_pages} 0 R".encode(), value)
    value = re.sub(rb"/Annots\s*\[.*?\]", b"", value, flags=re.S)
    value = re.sub(rb"/Annots\s+\d+\s+0\s+R", b"", value)
    objects[k] = value
keep = {new_catalog: f"<< /Type /Catalog /Pages {new_pages} 0 R >>".encode(),
        new_pages: (f"<< /Type /Pages /Count {len(selected)} /Kids [ " +
                    " ".join(f"{k} 0 R" for k in selected) + " ] >>").encode()}
stack = list(selected)
while stack:
    k = stack.pop()
    if k in keep:
        continue
    value = objects[k]
    # Do not follow the original page tree or accidentally include another page.
    if re.search(rb"/Type\s*/Page(?:s)?\b", value.split(b"stream", 1)[0]):
        assert k in selected, "Unselected page referenced; refusing"
    keep[k] = value
    stack.extend(refs(value.split(b"stream", 1)[0]))
out = bytearray(b"%PDF-1.5\n%\xe2\xe3\xcf\xd3\n")
offsets = {}
for k, value in sorted(keep.items()):
    offsets[k] = len(out)
    out.extend(f"{k} 0 obj\n".encode() + value + b"\nendobj\n")
xref = len(out)
out.extend(b"xref\n0 1\n0000000000 65535 f \n")
for k, offset in sorted(offsets.items()):
    out.extend(f"{k} 1\n{offset:010d} 00000 n \n".encode())
out.extend(f"trailer\n<< /Size {new_pages+1} /Root {new_catalog} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
dst.write_bytes(out)
print(f"Wrote restricted copy: original pages {first}-{last}; {len(keep)} reachable objects; {len(out)} bytes")
