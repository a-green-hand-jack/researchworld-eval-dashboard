"""Capture local installed terms; no imports of the scientific implementation or network."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'package-terms'
PINS = {'numpy': '2.4.6', 'scipy': '1.17.1', 'pandas': '3.0.6',
        'python-dateutil': '3.0.0', 'six': '1.17.0', 'tzdata': '2026.6'}


def save(source, target):
    data = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {'installed_path': str(source), 'saved_path': target.relative_to(ROOT).as_posix(),
            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    assert platform.python_version() == '3.11.2', 'Capture the recorded execution environment'
    record = {'captured_utc': datetime.now(timezone.utc).isoformat(),
              'source': 'Local installed distributions and system Python documentation only; no network retrieval',
              'python': {'version': platform.python_version(), 'sys_version': sys.version, 'files': []},
              'packages': []}
    for source in [Path(sys.base_prefix) / 'lib/python3.11/LICENSE.txt',
                   Path('/usr/share/doc/python3.11/copyright')]:
        record['python']['files'].append(save(source, OUT / 'python-3.11.2' / source.name))
    for name, version in PINS.items():
        dist = metadata.distribution(name)
        assert dist.version == version, (name, dist.version, version)
        entry = {'name': name, 'version': version,
                 'license_field': dist.metadata.get('License'),
                 'license_expression': dist.metadata.get('License-Expression'),
                 'declared_license_files': dist.metadata.get_all('License-File', []),
                 'requires_dist': dist.requires or [], 'files': []}
        for relative in sorted(dist.files or [], key=str):
            parts = relative.parts
            if '..' in parts:
                continue
            lower = relative.name.lower()
            terms = any(word in lower for word in ('license', 'notice', 'copying', 'copyright', 'authors'))
            metainfo = lower == 'metadata' and any(p.endswith('.dist-info') for p in parts)
            if terms or metainfo:
                source = Path(dist.locate_file(relative))
                if source.is_file():
                    entry['files'].append(save(source, OUT / (name + '-' + version) / relative))
        assert entry['files'], name
        record['packages'].append(entry)
    (ROOT / 'dependency-terms.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Captured', len(record['packages']), 'pinned distributions and Python terms;',
          sum(len(p['files']) for p in record['packages']) + len(record['python']['files']), 'files')


if __name__ == '__main__':
    main()
