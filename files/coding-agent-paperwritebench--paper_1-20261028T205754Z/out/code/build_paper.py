#!/usr/bin/env python3
"""Build from the immutable external references.bib; skip uncited broken entries.

Only cited entries are streamed into a temporary references.bib. Their contents,
keys and bibliographic metadata are unchanged. No workspace bibliography is edited.
"""
from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
BIB = ROOT / 'references.bib'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def run(command, cwd, logfile):
    result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    (ROOT / logfile).write_text(result.stdout)
    if result.returncode:
        print(result.stdout[-6000:])
        raise SystemExit(result.returncode)

before = digest(BIB)
run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'template.tex'],
    ROOT, 'build-latex.log')
aux = (ROOT / 'template.aux').read_text()
keys = {key for group in re.findall(r'\\citation\{([^}]+)\}', aux)
        for key in group.split(',')}
entries = {}
current_key, lines = None, []

def retain():
    if current_key in keys:
        if current_key in entries:
            raise RuntimeError('Duplicate bibliography key: ' + current_key)
        entries[current_key] = ''.join(lines)

# Stream the database: never load or print the full bibliography.
with BIB.open() as handle:
    for line in handle:
        start = re.match(r'\s*@\w+\s*\{\s*([^,]+),', line)
        if start:
            retain()
            current_key, lines = start.group(1), [line]
        elif current_key in keys:
            lines.append(line)
    retain()
missing = keys - entries.keys()
if missing:
    raise RuntimeError('Unknown citation keys: ' + ', '.join(sorted(missing)))
with tempfile.TemporaryDirectory(prefix='vl-rethinker-bib-') as directory:
    temp = Path(directory)
    (temp / 'references.bib').write_text('\n'.join(entries.values()))
    shutil.copy2(ROOT / 'template.aux', temp / 'template.aux')
    run(['bibtex', 'template'], temp, 'build-bibtex.log')
    shutil.copy2(temp / 'template.bbl', ROOT / 'template.bbl')
    shutil.copy2(temp / 'template.blg', ROOT / 'template.blg')
for _ in range(2):
    run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'template.tex'],
        ROOT, 'build-latex.log')
log = (ROOT / 'template.log').read_text()
if re.search(r'(?:Citation|Reference) .+ undefined|There were undefined references', log):
    raise RuntimeError('Unresolved citations or references; see template.log')
if before != digest(BIB):
    raise RuntimeError('The external bibliography changed during the build')
print(f'Validated {len(keys)} citation keys; references.bib unchanged.')
print(re.search(r'Output written on .+', log).group(0))
print('Official NeurIPS style available:', (ROOT / 'neurips_2025.sty').exists())
