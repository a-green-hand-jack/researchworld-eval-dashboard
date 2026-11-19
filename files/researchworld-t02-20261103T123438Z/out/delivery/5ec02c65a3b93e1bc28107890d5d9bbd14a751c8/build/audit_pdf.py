#!/usr/bin/env python3
"""Audit the actual integrated PDF using Poppler; never infer scientific validity."""
import argparse
import json
import re
import subprocess
from pathlib import Path


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, default=Path('paper.pdf'))
    parser.add_argument('--output', type=Path, default=Path('build/pdf-audit.json'))
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error(f'Missing actual PDF: {args.pdf}')
    info = run('pdfinfo', str(args.pdf))
    fonts = run('pdffonts', str(args.pdf))
    text = run('pdftotext', '-layout', str(args.pdf), '-')
    pages = text.split('\f')
    if pages and not pages[-1].strip():
        pages.pop()
    problems = []
    page_size = re.search(r'^Page size:\s+([\d.]+) x ([\d.]+) pts', info, re.M)
    if not page_size or tuple(map(float, page_size.groups())) != (612.0, 792.0):
        problems.append('PDF is not US Letter (612 x 792 points).')
    font_rows = [row for row in fonts.splitlines()[2:] if row.strip()]
    if not font_rows:
        problems.append('No fonts were reported.')
    if any('Type 3' in row for row in font_rows):
        problems.append('PDF contains a Type 3 font.')
    # pdffonts rightmost fields are emb/sub/uni/object-ID/generation.
    for row in font_rows:
        fields = row.split()
        if len(fields) < 6 or fields[-5] != 'yes':
            problems.append(f'Font embedding cannot be confirmed: {row}')
    references = [i + 1 for i, page in enumerate(pages)
                  if re.search(r'^\s*(?:\d+\s+)?References\s*$', page, re.M)]
    references_page = references[0] if references else None
    if references_page is None:
        problems.append('Cannot find a standalone References heading.')
    elif references_page - 1 > 9:
        problems.append('Content before the references exceeds nine pages.')
    if not re.search(r'NeurIPS Paper Checklist', text, re.I):
        problems.append('Cannot find the mandatory NeurIPS Paper Checklist.')
    for token in ('TODO', 'TBD', '??'):
        if token in text:
            problems.append(f'Unresolved text marker: {token}')
    source_files = sorted(Path('manuscript').rglob('*.tex'))
    for source in source_files:
        body = source.read_text()
        if re.search(r'\\answerTODO\b', body):
            problems.append(f'Unanswered checklist macro in {source}.')
    result = {
        'pdf': str(args.pdf),
        'total_pages': len(pages),
        'references_start_page': references_page,
        'content_pages_before_references': references_page - 1 if references_page else None,
        'font_count': len(font_rows),
        'problems': problems,
        'technical_checks_passed': not problems,
        'scope': 'Technical checks only. Visual inspection, scientific review, source/provenance verification, checklist wording and exact content-boundary inspection remain required.',
        'pdfinfo': info,
        'pdffonts': fonts,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('pdf', 'total_pages', 'technical_checks_passed', 'problems')}, indent=2))
    raise SystemExit(1 if problems else 0)


if __name__ == '__main__':
    main()
