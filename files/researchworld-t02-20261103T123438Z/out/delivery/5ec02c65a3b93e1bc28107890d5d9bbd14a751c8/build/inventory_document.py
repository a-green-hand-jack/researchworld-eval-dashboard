#!/usr/bin/env python3
"""Map actual compiled display labels to source, pages and supplied artifact hashes."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--entry', type=Path, default=Path('manuscript/main.tex'))
    p.add_argument('--pdf', type=Path, default=Path('paper.pdf'))
    p.add_argument('--aux', type=Path, default=Path('build/latex/main.aux'))
    p.add_argument('--output', type=Path, default=Path('manuscript/display-inventory.json'))
    p.add_argument('--reading-copy', action='store_true')
    a = p.parse_args()
    root = Path.cwd().resolve()
    manifest = json.loads(Path('presentation/manifest.json').read_text())
    artifacts = {r['output']['path']: r['output']['sha256'] for r in manifest['artifacts']}
    if not a.reading_copy:
        metadata = json.loads(Path('presentation/artifact-metadata.json').read_text())
        if not metadata['evidence_scope']['full_study_complete']:
            raise ValueError('A final inventory needs full-study presentation metadata')
    aux = a.aux.read_text()
    labels = {label: (number, int(page)) for label, number, page in re.findall(
        r'\\newlabel\{([^}]+)\}\{\{([^}]+)\}\{(\d+)\}', aux)}
    visited, displays = set(), []
    base = a.entry.resolve().parent

    def visit(path):
        path = path.resolve()
        if path in visited:
            return
        visited.add(path)
        body = path.read_text()
        for match in re.finditer(r'\\begin\{(figure|table)\}(.*?)\\end\{\1\}', body, re.S):
            kind, content = match.groups()
            label = re.findall(r'\\label\{([^}]+)\}', content)
            if len(label) != 1 or label[0] not in labels:
                raise ValueError(f'Missing/duplicate compiled display label in {path}')
            figure = re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', content)
            table = re.findall(r'\\input\{([^}]+)\}', content)
            if kind == 'figure' and len(figure) == 1 and not table:
                artifact = Path('figures') / figure[0]
                if not artifact.suffix:
                    artifact = artifact.with_suffix('.pdf')
            elif kind == 'table' and len(table) == 1 and not figure:
                artifact = (base / table[0]).with_suffix('.tex').resolve().relative_to(root)
            else:
                raise ValueError(f'Need one supplied artifact per display: {label}')
            artifact = artifact.as_posix()
            if artifact not in artifacts or sha(root / artifact) != artifacts[artifact]:
                raise ValueError('Display artifact absent/changed in manifest: ' + artifact)
            number, page = labels[label[0]]
            displays.append(dict(label=label[0], kind=kind, number=int(number), page=page,
                                 source=path.relative_to(root).as_posix(), artifact=artifact,
                                 sha256=artifacts[artifact]))
        for item in re.findall(r'\\input\{([^}]+)\}', body):
            child = (base / item).with_suffix('.tex').resolve()
            if child.is_relative_to(root / 'manuscript'):
                visit(child)

    visit(a.entry)
    if len({d['label'] for d in displays}) != len(displays):
        raise ValueError('Repeated display label')
    displays.sort(key=lambda d: (d['page'], d['kind'], d['number']))
    out = dict(status=('Marked reading copy; not a completed/reviewed paper' if a.reading_copy
                       else 'Complete204 manuscript candidate; independent exact-version approval is separate'),
               document=a.pdf.as_posix(), document_sha256=sha(a.pdf),
               manifest='presentation/manifest.json', manifest_sha256=sha(Path('presentation/manifest.json')),
               entry=a.entry.as_posix(), entry_sha256=sha(a.entry), aux=a.aux.as_posix(),
               generator='build/inventory_document.py', generator_sha256=sha(Path(__file__)), displays=displays)
    a.output.write_text(json.dumps(out, indent=2) + '\n')
    print(f'Mapped {len(displays)} actual compiled displays; no visual/scientific approval inferred.')


if __name__ == '__main__':
    main()
