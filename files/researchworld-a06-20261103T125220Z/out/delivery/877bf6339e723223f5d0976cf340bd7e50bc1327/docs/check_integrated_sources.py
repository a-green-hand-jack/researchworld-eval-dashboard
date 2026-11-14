"""Verify delivered evidence lineage and local manuscript/reproduction references.

This checks integration integrity only; it neither reruns experiments nor
certifies the scientific completeness of the report.
"""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text())


def local_file(base, name):
    path = (base / name).resolve()
    assert path.is_relative_to(ROOT), f'Path leaves delivery root: {name}'
    assert path.is_file(), f'Missing delivered file: {path.relative_to(ROOT)}'
    return path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


analysis = read_json('analysis/source-manifest.json')
for item in analysis['files']:
    path = local_file(ROOT / 'analysis', item['path'])
    assert path.stat().st_size == item['bytes'], f'Size mismatch: {path}'
    assert digest(path) == item['sha256'], f'Analysis hash mismatch: {path}'

presentation = read_json('presentation/provenance.json')
for name, expected in presentation['sha256'].items():
    path = local_file(ROOT / 'presentation/inputs', name)
    assert digest(path) == expected, f'Plotting-input hash mismatch: {path}'
    source = local_file(ROOT / 'analysis', presentation['source_paths'][name])
    assert path.read_bytes() == source.read_bytes(), f'Plot/analysis mismatch: {name}'

real_presentation = read_json('presentation/real-provenance.json')
assert real_presentation['source_revision'] == analysis['source_revision']
for name, item in real_presentation['inputs'].items():
    path = local_file(ROOT / 'presentation/inputs/real', name)
    assert digest(path) == item['sha256'], f'Real plotting-input hash mismatch: {name}'
    source = local_file(ROOT / 'analysis', item['source_path'])
    assert path.read_bytes() == source.read_bytes(), f'Real plot/analysis mismatch: {name}'

real_map = read_json('presentation/real-output-map.json')
assert real_map['source_revision'] == analysis['source_revision']
for record in real_map['records']:
    for name in [record['generator'], record['caption_file'], *record['inputs'], *record['outputs']]:
        local_file(ROOT, name)

# Follow the manuscript's literal local inclusions, including table sources.
# Dynamic TeX macros and external URLs are outside this integration check.
seen = set()
figures = set()


def check_tex(path):
    if path in seen:
        return
    seen.add(path)
    text = path.read_text()
    for command, name in re.findall(
        r'\\(input|includegraphics|bibliography)(?:\[[^\]]*\])?\{([^}]+)\}', text
    ):
        suffix = {'input': '.tex', 'bibliography': '.bib'}.get(command)
        if suffix and not Path(name).suffix:
            name += suffix
        target = local_file(ROOT, name)
        if command == 'input':
            check_tex(target)
        elif command == 'includegraphics':
            figures.add(target)


check_tex(ROOT / 'paper.tex')
readme_links = 0
for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', (ROOT / 'README.md').read_text()):
    parsed = urlsplit(target)
    if parsed.scheme or not parsed.path:
        continue
    local_file(ROOT, unquote(parsed.path))
    readme_links += 1

print(json.dumps({
    'analysis_source_revision': analysis['source_revision'],
    'analysis_files_verified': len(analysis['files']),
    'plot_inputs_equal_to_analysis': len(presentation['sha256']) + len(real_presentation['inputs']),
    'real_output_routes_checked': len(real_map['records']),
    'manuscript_tex_files_checked': len(seen),
    'included_figures_present': len(figures),
    'readme_local_file_links_checked': readme_links,
    'scope': 'integration integrity only; no scientific-completeness certification',
}, indent=2))
