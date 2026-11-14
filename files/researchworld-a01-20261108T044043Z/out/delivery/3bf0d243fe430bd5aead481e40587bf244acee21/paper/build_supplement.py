"""Package tracked manuscript sources, code and evidence for the separate supplement.
Run from any directory: python3 paper/build_supplement.py
The ZIP excludes its own output and the separately delivered PDF; its internal
SHA-256 manifest identifies every included file. Timestamps are fixed so identical
file contents produce identical archives.
"""
from pathlib import Path
import hashlib
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper' / 'reproducibility.zip'
names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
prefixes = ('code/', 'data/', 'results/', 'figures/', 'tables/', 'paper/', 'venue/')
names = sorted(n for n in names if n and (n.startswith(prefixes) or n in ('README.md', 'REPRODUCE.md'))
               and n not in ('paper/main.pdf', 'paper/reproducibility.zip'))
manifest = []
with zipfile.ZipFile(OUT, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name in names:
        content = (ROOT / name).read_bytes()
        info = zipfile.ZipInfo(name, date_time=(2026, 11, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (0o100755 if (ROOT / name).stat().st_mode & 0o111 else 0o100644) << 16
        archive.writestr(info, content)
        manifest.append(hashlib.sha256(content).hexdigest() + '  ' + name)
    info = zipfile.ZipInfo('ARCHIVE_MANIFEST.sha256', date_time=(2026, 11, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, '\n'.join(manifest) + '\n')
if OUT.stat().st_size > 100_000_000:
    raise RuntimeError('Supplement exceeds the venue 100 MB limit')
print(f'{OUT.relative_to(ROOT)}: {len(names)} files, {OUT.stat().st_size:,} bytes')
