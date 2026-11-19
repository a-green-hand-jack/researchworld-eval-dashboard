import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    root = Path('source_evidence')
    selected = Path('results/ideas/02_offset_invariant_risk_adaptive_control_variates/program_1')
    origins = {name: str(selected/'src'/name) for name in ['program.py', 'METHOD.md', 'test_controls.py']}
    origins.update({'program_spec.toml': str(selected/'program_spec.toml'),
                    'evaluate_final.py': 'task/evaluate_final.py', 'requirements.txt': 'task/requirements.txt',
                    'resource_manifest.json': 'task/resources/final/manifest.json',
                    'final_manifest.json': '/workspace/final_evaluation/final_manifest.json'})
    records = {}
    for name, origin in origins.items():
        payload = (root/name).read_bytes()
        assert payload == Path(origin).read_bytes(), name
        records[name] = {'original_path': origin, 'sha256': hashlib.sha256(payload).hexdigest(),
                         'association': 'result.top_program_01 identifies selected source location; final source-tree digest is not independently reconstructed.' if name in ['program.py', 'METHOD.md', 'test_controls.py', 'program_spec.toml'] else 'Readable evaluator or resource provenance.'}
    url = 'https://pypi.org/pypi/ppi-python/0.2.3/json'
    metadata = json.load(urllib.request.urlopen(url))
    wheel = next(Path('/tmp/paper-tools').glob('ppi_python-0.2.3-*.whl'))
    expected = next(record for record in metadata['urls'] if record['filename'] == wheel.name)
    actual = hashlib.sha256(wheel.read_bytes()).hexdigest()
    assert actual == expected['digests']['sha256']
    baseline = {'version': metadata['info']['version'], 'metadata_url': url, 'wheel_url': expected['url'], 'wheel_sha256': actual,
                'extracted_files': {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['ppi.py', 'statistics_utils.py']}}
    (root/'baseline_source_provenance.json').write_text(json.dumps(baseline, indent=2))
    for name in ['ppi.py', 'statistics_utils.py']:
        records[name] = {'original_path': expected['url']+'#ppi_py/'+('utils/' if name == 'statistics_utils.py' else '')+name,
                         'sha256': baseline['extracted_files'][name], 'association': 'Extracted from the fixed reference release; compared call path is in evaluate_final.py.'}
    (root/'index.json').write_text(json.dumps(records, indent=2))
    print('Verified copied sources and pinned reference wheel provenance.')


if __name__ == '__main__':
    main()
